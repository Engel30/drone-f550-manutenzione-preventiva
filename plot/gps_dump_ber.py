#!/usr/bin/env python3
"""
Diagnostica BER del link UART GPS dal topic `gps_dump` di PX4.

Replica la metodologia usata il 2026-05-27 per diagnosticare il cavo GPS
auto-costruito (vedi maintenance/troubleshooting-gps-dropout-2026-05-27.md):

  1. Estrae `gps_dump` dal .ulg e ricostruisce lo stream RX (bit 7 di len = 0).
  2. Parsa frame UBX (sync B5 62, validazione checksum Fletcher-8), conta i
     byte "garbage" (fuori da qualunque frame valido) e i CRC fail.
  3. Estrae `sensor_gps`: gap > 2 s, reinit driver (heuristica sul rate).
  4. Estrae regime motori da `esc_status` per contestualizzare il carico
     vibrazionale durante la finestra armato.

Uso:
    python3 plot/gps_dump_ber.py log/2026-06-04/11_52_13.ulg
    python3 plot/gps_dump_ber.py log/2026-06-04/*.ulg
"""

import sys
from pathlib import Path

import numpy as np
from pyulog import ULog


# ── UBX parser ────────────────────────────────────────────────────────────────
UBX_SYNC1 = 0xB5
UBX_SYNC2 = 0x62


def ubx_checksum(buf: bytes) -> tuple[int, int]:
    """Fletcher-8 checksum su class+id+length+payload (esclude i 2 sync byte)."""
    ck_a = ck_b = 0
    for b in buf:
        ck_a = (ck_a + b) & 0xFF
        ck_b = (ck_b + ck_a) & 0xFF
    return ck_a, ck_b


def parse_ubx_stream(stream: bytes) -> dict:
    """Scansiona uno stream RX byte per byte e classifica:
       - byte dentro frame UBX validi (sync+header+payload+CRC OK)
       - byte garbage (tutti gli altri, inclusi CRC fail e desync)
       - conteggio frame per classe (NAV-PVT = 01 07, NAV-SAT = 01 35, ...)
       - CRC fail count
    """
    n = len(stream)
    i = 0
    in_frame_bytes = 0
    crc_fail = 0
    msg_counts: dict[tuple[int, int], int] = {}

    while i < n - 7:
        if stream[i] == UBX_SYNC1 and stream[i + 1] == UBX_SYNC2:
            cls = stream[i + 2]
            mid = stream[i + 3]
            length = stream[i + 4] | (stream[i + 5] << 8)
            frame_end = i + 6 + length + 2
            if length > 2048 or frame_end > n:
                # length implausibile o frame troncato → 1 byte spazzatura e avanti
                i += 1
                continue
            payload = stream[i + 2:i + 6 + length]  # cls+id+len+payload
            ck_a, ck_b = ubx_checksum(payload)
            if ck_a == stream[frame_end - 2] and ck_b == stream[frame_end - 1]:
                in_frame_bytes += frame_end - i
                msg_counts[(cls, mid)] = msg_counts.get((cls, mid), 0) + 1
                i = frame_end
                continue
            else:
                crc_fail += 1
                i += 1
                continue
        i += 1

    garbage_bytes = n - in_frame_bytes
    return {
        "total_rx_bytes": n,
        "in_frame_bytes": in_frame_bytes,
        "garbage_bytes": garbage_bytes,
        "garbage_pct": 100.0 * garbage_bytes / n if n else 0.0,
        "crc_fail": crc_fail,
        "msg_counts": msg_counts,
    }


# ── Estrazione ULog ───────────────────────────────────────────────────────────
def extract_rx_stream(ulog: ULog) -> tuple[bytes, float, float]:
    """Ricostruisce lo stream RX da `gps_dump`. Ritorna (bytes, t0_s, t1_s)."""
    try:
        d = ulog.get_dataset("gps_dump")
    except (KeyError, IndexError, Exception):
        return b"", 0.0, 0.0

    ts = d.data["timestamp"]  # μs
    lens = d.data["len"]
    # data è un campo array len=79 → in pyulog appare come data[0]..data[78]
    data_cols = np.stack([d.data[f"data[{k}]"] for k in range(79)], axis=1)

    rx_chunks = []
    rx_ts = []
    for row, (l, t) in enumerate(zip(lens, ts)):
        is_tx = (int(l) & 0x80) != 0
        n_valid = int(l) & 0x7F
        if is_tx or n_valid == 0:
            continue
        rx_chunks.append(bytes(data_cols[row, :n_valid].astype(np.uint8)))
        rx_ts.append(t)

    if not rx_chunks:
        return b"", 0.0, 0.0
    return b"".join(rx_chunks), rx_ts[0] / 1e6, rx_ts[-1] / 1e6


def armed_window(ulog: ULog) -> tuple[float, float]:
    """Finestra armato (arming_state==2) in secondi."""
    try:
        d = ulog.get_dataset("vehicle_status")
        ts = d.data["timestamp"] / 1e6
        arm = d.data["arming_state"]
    except Exception:
        return 0.0, 0.0
    mask = arm == 2
    if not mask.any():
        return 0.0, 0.0
    return float(ts[mask].min()), float(ts[mask].max())


def sensor_gps_gaps(ulog: ULog, t_start: float, t_end: float, threshold_s: float = 2.0):
    """Gap del timestamp di `sensor_gps` nella finestra armato."""
    try:
        d = ulog.get_dataset("sensor_gps")
    except Exception:
        return []
    ts = d.data["timestamp"] / 1e6
    mask = (ts >= t_start) & (ts <= t_end)
    ts = ts[mask]
    if len(ts) < 2:
        return []
    dt = np.diff(ts)
    gaps_idx = np.where(dt > threshold_s)[0]
    return [(float(ts[i]), float(dt[i])) for i in gaps_idx]


def motor_regime(ulog: ULog, t_start: float, t_end: float) -> dict:
    """Sum-RPM medio/massimo nella finestra armato e % tempo in 'lift'."""
    try:
        d = ulog.get_dataset("esc_status")
    except Exception:
        return {}
    ts = d.data["timestamp"] / 1e6
    mask = (ts >= t_start) & (ts <= t_end)
    if not mask.any():
        return {}
    rpm = np.zeros(mask.sum())
    for k in range(6):
        try:
            rpm += d.data[f"esc[{k}].esc_rpm"][mask]
        except KeyError:
            pass
    return {
        "sum_rpm_mean": float(rpm.mean()),
        "sum_rpm_max": float(rpm.max()),
        # "in lift" = sum-RPM > 20 000 (≈ 3300 RPM/motore, sopra idle ~700)
        "pct_in_lift": 100.0 * float((rpm > 20000).mean()),
    }


def driver_reinit_count(ulog: ULog, t_start: float, t_end: float) -> int:
    """Conta i log message 'u-blox firmware version' nella finestra (= boot driver)."""
    n = 0
    for m in ulog.logged_messages:
        t = m.timestamp / 1e6
        if t_start <= t <= t_end and "u-blox" in m.message.lower():
            n += 1
    return n


# ── Driver principale ────────────────────────────────────────────────────────
def analyze(path: Path) -> dict:
    ulog = ULog(str(path), disable_str_exceptions=True)

    t_arm0, t_arm1 = armed_window(ulog)
    rx_bytes, rx_t0, rx_t1 = extract_rx_stream(ulog)

    # Filtra lo stream RX alla finestra armato se possibile.
    # Per semplicità misuriamo il BER su tutto lo stream loggato — gps_dump è
    # tipicamente attivo solo durante il volo se GPS_DUMP_COMM è impostato.
    rx_stats = parse_ubx_stream(rx_bytes) if rx_bytes else {
        "total_rx_bytes": 0, "in_frame_bytes": 0, "garbage_bytes": 0,
        "garbage_pct": 0.0, "crc_fail": 0, "msg_counts": {},
    }

    nav_pvt = rx_stats["msg_counts"].get((0x01, 0x07), 0)
    rx_window = max(rx_t1 - rx_t0, 1e-3)
    nav_pvt_hz = nav_pvt / rx_window if rx_bytes else 0.0

    return {
        "file": path.name,
        "armed_window_s": t_arm1 - t_arm0,
        "rx_window_s": rx_window if rx_bytes else 0.0,
        "rx_bytes": rx_stats["total_rx_bytes"],
        "garbage_pct": rx_stats["garbage_pct"],
        "crc_fail": rx_stats["crc_fail"],
        "nav_pvt_count": nav_pvt,
        "nav_pvt_hz": nav_pvt_hz,
        "sensor_gps_gaps": sensor_gps_gaps(ulog, t_arm0, t_arm1),
        "driver_reinits": driver_reinit_count(ulog, t_arm0, t_arm1),
        "motor": motor_regime(ulog, t_arm0, t_arm1),
        "msg_counts": rx_stats["msg_counts"],
    }


def print_report(r: dict) -> None:
    print(f"\n══════ {r['file']} ──────")
    print(f"  Armato per : {r['armed_window_s']:6.1f} s")
    if r["rx_bytes"] == 0:
        print("  ⚠ gps_dump assente o vuoto in questo log "
              "(GPS_DUMP_COMM disabilitato?)")
        return
    print(f"  RX stream  : {r['rx_bytes']:8d} byte su {r['rx_window_s']:5.1f} s "
          f"({r['rx_bytes']/r['rx_window_s']:.0f} B/s)")
    print(f"  Garbage    : {r['garbage_pct']:5.2f} %   "
          f"({r['garbage_pct'] < 1.0 and 'OK ✓' or 'ALTO ✗'})")
    print(f"  CRC fail   : {r['crc_fail']:5d}")
    print(f"  NAV-PVT    : {r['nav_pvt_count']:5d}  ({r['nav_pvt_hz']:.2f} Hz)")
    print(f"  Reinit drv : {r['driver_reinits']}")
    print(f"  Gap >2s    : {len(r['sensor_gps_gaps'])}",
          r["sensor_gps_gaps"] and r["sensor_gps_gaps"][:5] or "")
    if r["motor"]:
        m = r["motor"]
        print(f"  Motori     : sum-RPM media {m['sum_rpm_mean']:.0f}, "
              f"max {m['sum_rpm_max']:.0f}, in lift {m['pct_in_lift']:.0f} %")
    top_msgs = sorted(r["msg_counts"].items(), key=lambda kv: -kv[1])[:5]
    print("  Top UBX    :", ", ".join(
        f"{cls:02X}-{mid:02X}×{n}" for (cls, mid), n in top_msgs))


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    paths = [Path(p) for p in sys.argv[1:]]
    results = []
    for p in paths:
        try:
            r = analyze(p)
            print_report(r)
            results.append(r)
        except Exception as e:
            print(f"\n══════ {p.name} ──────\n  ERROR: {e}")

    # Tabella riassuntiva finale
    if len(results) > 1:
        print("\n══════ RIEPILOGO ──────")
        print(f"  {'file':<22} {'armato':>7} {'rx B':>8} {'garb%':>7} "
              f"{'CRC':>4} {'PVT/s':>6} {'reinit':>7} {'gap>2s':>7} {'sumRPM':>7}")
        for r in results:
            m = r["motor"].get("sum_rpm_mean", 0) if r["motor"] else 0
            print(f"  {r['file']:<22} "
                  f"{r['armed_window_s']:6.1f}s {r['rx_bytes']:8d} "
                  f"{r['garbage_pct']:6.2f}% {r['crc_fail']:4d} "
                  f"{r['nav_pvt_hz']:5.2f} {r['driver_reinits']:7d} "
                  f"{len(r['sensor_gps_gaps']):7d} {m:7.0f}")


if __name__ == "__main__":
    main()
