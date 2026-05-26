#!/usr/bin/env python3
"""
Riporta tutte le informazioni generali di un log PX4 (.ulg):
- metadati (firmware, hardware, durata, parametri, dropout)
- elenco completo dei topic loggati con istanza, n. messaggi, frequenza, durata
- verifica di completezza rispetto a una lista di topic attesi per la
  manutenzione preventiva (modificabile sotto: EXPECTED_TOPICS)

Uso:
    python3 info_log.py                 # usa l'ultimo .ulg in plot/
    python3 info_log.py path/al/log.ulg # log specifico
    python3 info_log.py --md            # salva anche report markdown
"""

import argparse
import os
import sys
from datetime import datetime

import numpy as np
from pyulog import ULog

from utils import find_ulog


def safe_freq(ts_us: np.ndarray) -> float:
    """Frequenza mediana robusta: ignora diff nulli (timestamp ripetuti)."""
    if len(ts_us) < 2:
        return 0.0
    dt = np.diff(ts_us) / 1e6
    dt = dt[dt > 0]
    if dt.size == 0:
        return 0.0
    return 1.0 / float(np.median(dt))


# ── Topic attesi per manutenzione preventiva ──────────────────────────────────
# TODO (utente): rivedere/estendere questa lista in base a cosa vuoi verificare
# nella relazione. La presenza di questi topic indica che il log copre le aree
# critiche per la diagnostica di manutenzione (IMU, propulsione, alimentazione,
# navigazione, vibrazioni, errori). Vedi la richiesta sotto.
# Catalogo organizzato per categoria. Commenta le righe dei topic che non ti
# interessano: il check di completezza userà solo quelli rimasti attivi e la
# tabella in output li raggrupperà secondo queste categorie.
TOPIC_CATALOG = {
    "Sensori grezzi (IMU, mag, baro, GPS, power)": {
        "sensor_accel":          "IMU - accelerometro (atteso x3 istanze)",
        "sensor_gyro":           "IMU - giroscopio (atteso x3 istanze)",
        "sensor_accel_fifo":     "IMU - accelerometro FIFO ad alta freq. (vibrazioni/FFT)",
        "sensor_gyro_fifo":      "IMU - giroscopio FIFO ad alta freq. (vibrazioni/FFT)",
        "sensor_mag":            "Magnetometro grezzo",
        "sensor_baro":           "Barometro grezzo",
        "sensor_gps":            "GPS grezzo (driver)",
        "sensor_combined":       "IMU combinata filtrata (200 Hz)",
        "sensor_selection":      "IMU/mag selezionati dal voting",
        "sensors_status_imu":    "Stato/health sensori IMU",
        "system_power":          "Tensioni rail 5V / servo / periferiche",
    },
    "Stato veicolo / sensori fusi": {
        "vehicle_imu":               "IMU integrata (delta angle / delta velocity)",
        "vehicle_imu_status":        "Statistiche vibrazioni / clipping IMU",
        "vehicle_acceleration":      "Accelerazione veicolo filtrata",
        "vehicle_angular_velocity":  "Velocità angolare filtrata",
        "vehicle_attitude":          "Assetto (quaternione)",
        "vehicle_magnetometer":      "Magnetometro fuso",
        "vehicle_air_data":          "Dati barometrici fusi",
        "vehicle_gps_position":      "Posizione GPS fusa",
        "vehicle_local_position":    "Posizione locale (NED)",
        "vehicle_global_position":   "Posizione globale (lat/lon/alt)",
        "vehicle_land_detected":     "Rilevamento atterraggio",
        "vehicle_status":            "Stato di volo / nav_state / arming",
        "vehicle_control_mode":      "Modalità di controllo attive",
    },
    "Setpoint e controllo": {
        "vehicle_attitude_setpoint":       "Setpoint assetto",
        "vehicle_rates_setpoint":          "Setpoint rate angolari",
        "vehicle_thrust_setpoint":         "Setpoint spinta",
        "vehicle_torque_setpoint":         "Setpoint coppia",
        "vehicle_local_position_setpoint": "Setpoint posizione locale",
        "trajectory_setpoint":             "Setpoint traiettoria",
        "position_setpoint_triplet":       "Tripletta setpoint (prev/cur/next)",
        "vehicle_constraints":             "Vincoli di volo (vel max ecc.)",
        "rate_ctrl_status":                "Saturazioni controllore di rate",
        "control_allocator_status":        "Allocazione comandi sui motori",
        "hover_thrust_estimate":           "Stima spinta di hover",
    },
    "Attuatori / ESC / propulsione": {
        "actuator_armed":   "Stato armato/disarmato",
        "actuator_motors":  "Comandi motori normalizzati",
        "actuator_outputs": "PWM uscita verso ESC",
        "esc_status":       "Telemetria ESC (RPM, temp, corrente)",
        "landing_gear":     "Stato carrello",
    },
    "EKF2 (estimator) — x3 istanze per voting": {
        "estimator_status":                 "Stato EKF (test ratio, reset)",
        "estimator_status_flags":           "Flag di stato EKF",
        "estimator_states":                 "Stati EKF (24+)",
        "estimator_innovations":            "Innovazioni EKF",
        "estimator_innovation_variances":   "Varianze innovazioni EKF",
        "estimator_innovation_test_ratios": "Test ratio innovazioni",
        "estimator_sensor_bias":            "Bias stimati accel/gyro/mag",
        "estimator_attitude":               "Assetto stimato per istanza EKF",
        "estimator_local_position":         "Posizione locale per istanza EKF",
        "estimator_global_position":        "Posizione globale per istanza EKF",
        "estimator_odometry":               "Odometria EKF",
        "estimator_event_flags":            "Flag eventi EKF",
        "estimator_selector_status":        "Stato voting tra EKF",
        "estimator_gps_status":             "Controllo GPS EKF",
        "estimator_baro_bias":              "Bias barometro EKF",
        "estimator_aid_src_baro_hgt":       "Aiding EKF da barometro",
        "estimator_aid_src_gnss_hgt":       "Aiding EKF da GNSS altezza",
        "estimator_aid_src_gnss_pos":       "Aiding EKF da GNSS posizione",
        "estimator_aid_src_gnss_vel":       "Aiding EKF da GNSS velocità",
        "estimator_aid_src_mag":            "Aiding EKF da magnetometro",
        "estimator_aid_src_gravity":        "Aiding EKF da gravità",
        "estimator_aid_src_fake_pos":       "Aiding EKF fake position (no GPS)",
        "estimator_aid_src_fake_hgt":       "Aiding EKF fake height",
        "magnetometer_bias_estimate":       "Stima bias magnetometro",
        "yaw_estimator_status":             "Stato stima yaw",
    },
    "Radio / RC / comunicazione": {
        "input_rc":                "Canali RC ricevitore",
        "manual_control_setpoint": "Setpoint da pilota",
        "manual_control_switches": "Switch del radiocomando",
        "radio_status":            "RSSI / qualità link radio",
        "telemetry_status":        "Stato telemetria (MAVLink)",
        "transponder_report":      "ADS-B / transponder",
    },
    "Sistema / housekeeping": {
        "cpuload":          "Carico CPU del flight controller",
        "px4io_status":     "Stato coprocessore IO",
        "parameter_update": "Modifica parametri a runtime",
        "config_overrides": "Override di configurazione",
        "event":            "Eventi/log di sistema",
    },
    "Failsafe / sicurezza": {
        "failsafe_flags":          "Flag failsafe attivi",
        "failure_detector_status": "Stato failure detector",
        "vehicle_command":         "Comandi inviati al veicolo",
        "vehicle_command_ack":     "Ack comandi",
    },
    "Navigazione / missione": {
        "home_position":          "Posizione home",
        "navigator_status":       "Stato navigatore",
        "navigator_mission_item": "Waypoint corrente missione",
        "mission_result":         "Risultato esecuzione missione",
        "rtl_status":             "Stato Return-To-Launch",
        "rtl_time_estimate":      "Stima tempo RTL",
        "takeoff_status":         "Stato decollo",
        "action_request":         "Richieste azioni di volo",
    },
    "Alimentazione": {
        "battery_status": "Tensione/corrente/SOC batteria",
    },
    "Sensori opzionali": {
        "distance_sensor_mode_change_request": "Richiesta cambio modo distance sensor",
    },
}

# Vista flat per il check di completezza (categoria -> dict, dict -> flat)
EXPECTED_TOPICS = {t: desc for cat in TOPIC_CATALOG.values() for t, desc in cat.items()}

# Mappa inversa topic -> categoria (per il raggruppamento in stampa)
TOPIC_CATEGORY = {t: cat for cat, items in TOPIC_CATALOG.items() for t in items}


# ── Helpers ───────────────────────────────────────────────────────────────────

def fmt_duration(seconds: float) -> str:
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    if h:
        return f"{h}h {m:02d}m {s:02d}s"
    return f"{m}m {s:02d}s"


def fmt_bytes(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} TB"


def topic_stats(d) -> dict:
    ts = d.data["timestamp"]
    n = len(ts)
    field_names = [f.field_name for f in d.field_data if f.field_name != "timestamp"]
    duration = (ts[-1] - ts[0]) / 1e6 if n >= 2 else 0.0
    return {
        "name":     d.name,
        "instance": d.multi_id,
        "n":        n,
        "freq":     safe_freq(ts),
        "dur":      duration,
        "n_fields": len(field_names),
        "fields":   field_names,
    }


def wrap_fields(fields: list, indent: str, width: int = 78) -> list:
    """Avvolge una lista di nomi di campo separati da virgola in righe larghe `width`."""
    if not fields:
        return [indent + "(nessun campo)"]
    lines, cur = [], indent
    for i, name in enumerate(fields):
        sep = ", " if i < len(fields) - 1 else ""
        token = name + sep
        if len(cur) + len(token) > width and cur != indent:
            lines.append(cur.rstrip())
            cur = indent
        cur += token
    if cur.strip():
        lines.append(cur.rstrip(", "))
    return lines


# ── Report ────────────────────────────────────────────────────────────────────

def collect_report(ulog: ULog, path: str) -> dict:
    file_size = os.path.getsize(path)

    # Durata complessiva
    t_start_us = min(d.data["timestamp"][0] for d in ulog.data_list)
    t_end_us = max(d.data["timestamp"][-1] for d in ulog.data_list)
    duration = (t_end_us - t_start_us) / 1e6

    # Timestamp assoluto (UTC) se disponibile
    start_ts = ulog.start_timestamp  # µs unix
    start_dt = (datetime.utcfromtimestamp(start_ts / 1e6).isoformat() + " UTC"
                if start_ts else "n/d")

    # Metadati firmware/hardware
    info = ulog.msg_info_dict
    meta = {
        "sys_name":       info.get("sys_name", "n/d"),
        "ver_hw":         info.get("ver_hw", "n/d"),
        "ver_sw":         info.get("ver_sw", "n/d"),
        "ver_sw_release": info.get("ver_sw_release", "n/d"),
        "sys_os_name":    info.get("sys_os_name", "n/d"),
        "sys_os_ver":     info.get("sys_os_ver_release", "n/d"),
        "sys_toolchain":  info.get("sys_toolchain", "n/d"),
        "sys_mcu":        info.get("sys_mcu", "n/d"),
        "sys_uuid":       info.get("sys_uuid", "n/d"),
        "replay":         info.get("replay", ""),
    }

    # Dropout (perdite di log)
    dropouts = ulog.dropouts
    drop_total_ms = sum(d.duration for d in dropouts)

    # Topic stats
    topics = sorted(
        (topic_stats(d) for d in ulog.data_list),
        key=lambda x: (x["name"], x["instance"]),
    )

    # Completezza
    logged_names = {t["name"] for t in topics}
    missing = sorted(set(EXPECTED_TOPICS) - logged_names)
    present = sorted(set(EXPECTED_TOPICS) & logged_names)

    return {
        "path": path,
        "file_size": file_size,
        "start_dt": start_dt,
        "duration": duration,
        "meta": meta,
        "n_params": len(ulog.initial_parameters),
        "n_changed_params": len(ulog.changed_parameters),
        "dropouts": dropouts,
        "drop_total_ms": drop_total_ms,
        "topics": topics,
        "logged_names": logged_names,
        "missing": missing,
        "present": present,
    }


def section_header(title: str) -> None:
    bar = "═" * 78
    print()
    print(bar)
    print(f"  {title}")
    print(bar)


def subsection(title: str) -> None:
    print()
    print(f"── {title} " + "─" * (74 - len(title)))


def print_topic_block(t: dict, show_fields: bool = True) -> None:
    """Stampa un blocco compatto per un singolo topic+istanza."""
    print(f"  • {t['name']} [istanza {t['instance']}]")
    print(f"      messaggi : {t['n']}")
    print(f"      frequenza: {t['freq']:.1f} Hz")
    print(f"      durata   : {t['dur']:.2f} s")
    print(f"      campi    : {t['n_fields']}")
    if show_fields and t["fields"]:
        for line in wrap_fields(t["fields"], "        ", width=76):
            print(line)


def print_report(r: dict, show_fields: bool = True) -> None:
    # ── 1. Header
    section_header(f"PX4 ULog report — {os.path.basename(r['path'])}")

    # ── 2. File
    subsection("File")
    print(f"  Path        : {r['path']}")
    print(f"  Dimensione  : {fmt_bytes(r['file_size'])}")

    # ── 3. Tempo
    subsection("Tempo")
    print(f"  Inizio (UTC): {r['start_dt']}")
    print(f"  Durata      : {fmt_duration(r['duration'])}  ({r['duration']:.2f} s)")

    # ── 4. Firmware / Hardware
    m = r["meta"]
    subsection("Firmware / Hardware")
    print(f"  sys_name       : {m['sys_name']}")
    print(f"  ver_hw         : {m['ver_hw']}")
    print(f"  ver_sw         : {m['ver_sw']}")
    print(f"  ver_sw_release : {m['ver_sw_release']}")
    print(f"  sys_os         : {m['sys_os_name']} {m['sys_os_ver']}")
    print(f"  sys_mcu        : {m['sys_mcu']}")
    print(f"  sys_uuid       : {m['sys_uuid']}")
    if m["replay"]:
        print(f"  replay         : {m['replay']}")

    # ── 5. Parametri / dropout
    subsection("Parametri PX4")
    print(f"  Iniziali   : {r['n_params']}")
    print(f"  Modificati : {r['n_changed_params']} a runtime")

    subsection("Dropout (perdite di log)")
    print(f"  Eventi : {len(r['dropouts'])}")
    print(f"  Totale : {r['drop_total_ms']} ms persi")

    # ── 6. Topic raggruppati per categoria
    section_header(f"Topic loggati — {len(r['topics'])} istanze totali")

    # Raggruppamento topic per categoria
    by_cat: dict[str, list] = {}
    for t in r["topics"]:
        cat = TOPIC_CATEGORY.get(t["name"], "Altri (non catalogati)")
        by_cat.setdefault(cat, []).append(t)

    # Ordina: prima le categorie del catalogo nell'ordine, poi "Altri"
    cat_order = list(TOPIC_CATALOG.keys()) + ["Altri (non catalogati)"]
    for cat in cat_order:
        if cat not in by_cat:
            continue
        items = sorted(by_cat[cat], key=lambda x: (x["name"], x["instance"]))
        subsection(f"{cat}  ({len(items)} istanze)")
        for t in items:
            print_topic_block(t, show_fields=show_fields)

    # ── 7. Completezza
    if EXPECTED_TOPICS:
        section_header(f"Verifica completezza  ({len(r['present'])}/{len(EXPECTED_TOPICS)} topic attesi presenti)")
        # Raggruppa anche il check per categoria
        for cat, items in TOPIC_CATALOG.items():
            present_in_cat = [n for n in items if n in r["logged_names"]]
            missing_in_cat = [n for n in items if n not in r["logged_names"]]
            if not present_in_cat and not missing_in_cat:
                continue
            subsection(f"{cat}  ({len(present_in_cat)}/{len(items)})")
            for name in items:
                mark = "✓" if name in r["logged_names"] else "✗"
                print(f"  {mark} {name:<40} {items[name]}")
    print()


def write_markdown(r: dict, out_path: str) -> None:
    lines = []
    lines.append(f"# Report log `{os.path.basename(r['path'])}`")
    lines.append("")
    lines.append("## Informazioni generali")
    lines.append("")
    lines.append(f"- **File**: `{r['path']}`")
    lines.append(f"- **Dimensione**: {fmt_bytes(r['file_size'])}")
    lines.append(f"- **Inizio log (UTC)**: {r['start_dt']}")
    lines.append(f"- **Durata**: {fmt_duration(r['duration'])} ({r['duration']:.2f} s)")
    m = r["meta"]
    lines.append(f"- **Firmware**: {m['ver_sw_release']} (`{m['ver_sw']}`)")
    lines.append(f"- **Hardware**: {m['sys_name']} — {m['ver_hw']}")
    lines.append(f"- **MCU**: {m['sys_mcu']}")
    lines.append(f"- **UUID**: `{m['sys_uuid']}`")
    lines.append(f"- **Parametri**: {r['n_params']} iniziali, "
                 f"{r['n_changed_params']} modificati")
    lines.append(f"- **Dropout**: {len(r['dropouts'])} eventi, "
                 f"{r['drop_total_ms']} ms totali")
    lines.append("")
    lines.append(f"## Topic loggati ({len(r['topics'])})")
    lines.append("")
    lines.append("| Topic | Istanza | Messaggi | Hz | Durata [s] | #Campi |")
    lines.append("|---|---:|---:|---:|---:|---:|")
    for t in r["topics"]:
        lines.append(f"| `{t['name']}` | {t['instance']} | {t['n']} | "
                     f"{t['freq']:.1f} | {t['dur']:.2f} | {t['fields']} |")
    lines.append("")
    if EXPECTED_TOPICS:
        lines.append("## Verifica completezza")
        lines.append("")
        lines.append(f"Presenti: **{len(r['present'])}/{len(EXPECTED_TOPICS)}**")
        lines.append("")
        for name in r["present"]:
            lines.append(f"- ✓ `{name}` — {EXPECTED_TOPICS[name]}")
        for name in r["missing"]:
            lines.append(f"- ✗ `{name}` — {EXPECTED_TOPICS[name]} *(mancante)*")
        lines.append("")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"Report markdown salvato in: {out_path}")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(description="Report informativo di un log PX4 .ulg")
    ap.add_argument("ulog", nargs="?", help="Path al file .ulg (default: ultimo in plot/)")
    ap.add_argument("--md", action="store_true",
                    help="Salva anche un report markdown accanto al log")
    ap.add_argument("--no-fields", action="store_true",
                    help="Non stampare l'elenco dei campi di ciascun topic")
    args = ap.parse_args()

    path = args.ulog or find_ulog()
    if not os.path.isfile(path):
        print(f"File non trovato: {path}", file=sys.stderr)
        sys.exit(1)

    print(f"Caricamento: {path}")
    ulog = ULog(path)
    report = collect_report(ulog, path)
    print_report(report, show_fields=not args.no_fields)

    if args.md:
        out = os.path.splitext(path)[0] + "_info.md"
        write_markdown(report, out)


if __name__ == "__main__":
    main()
