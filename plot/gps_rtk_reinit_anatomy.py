#!/usr/bin/env python3
"""
Anatomizza i reinit del driver GPS (u-blox) in relazione al **modo RTK** e al
**movimento** del drone, sui log della sessione 2026-06-04.

Contesto (vedi log/2026-06-04/README.md): il guasto GPS NON è il cavo
(ispezione meccanica pulita, vibrazione anticorrelata). I dropout sono cicli di
reinit del driver PX4 ↔ u-blox che compaiono **solo sui voli in modo RTK**
(RTCM iniettato, fix_type=5), mentre i voli in 3D puro sono sempre sani.
L'RTCM però scorre liscio attraverso i dropout: è la *precondizione*, non il
grilletto del singolo evento. I reinit cadono a cadenza ~12-19 s → loop interno
del driver. Precisazione importante (dai dati di sessione): solo il **loop
sostenuto** (>=2 reinit, outage grosso) è esclusivo del modo RTK; un reinit
isolato è benigno e capita anche in 3D (es. 11_50_58). Il movimento NON
discrimina: 12_28_29 (7 reinit, 45% outage) volava quasi in hover come il volo
RTK sano 12_21_42. Il grilletto che tipped un dato volo RTK nel loop resta
aperto (sospetti: tempo/termico, stato RTK interno del ricevitore non loggato).

Questo tool, per ogni .ulg, stampa:
  1. PRECONDIZIONE RTK — RTCM iniettato (byte/s reali dal gps_dump, più
     affidabili di rtcm_injection_rate la cui mediana può essere 0 se bursty) +
     distribuzione fix_type → etichetta "RTK attivo" / "3D".
  2. ANATOMIA DEL LOOP — n. reinit, periodo, primo reinit vs ultimo NAV valido,
     outage NAV totale (gap sensor_gps > 2 s).
  3. MOVIMENTO — velocità orizzontale (vehicle_local_position) ai reinit vs
     fondo del volo, per testare l'ipotesi "serve RTK + movimento".

Con più file stampa una tabella di confronto finale (3D-sani vs RTK-problematici).

Uso:
    python3 plot/gps_rtk_reinit_anatomy.py log/2026-06-04/12_46_09.ulg
    python3 plot/gps_rtk_reinit_anatomy.py log/2026-06-04/*.ulg
"""

import sys
from pathlib import Path

import numpy as np
from pyulog import ULog

NAV_GAP = 2.0     # soglia gap sensor_gps per "stop-NAV" [s]
GUARD = 6.0       # esclusione attorno a ogni reinit per il fondo movimento [s]
RTK_BPS = 50.0    # soglia RTCM TX byte/s per considerare l'RTK attivo
REINIT_WIN = 2.0  # semi-finestra per campionare la velocità attorno a un reinit [s]


def armed_window(u: ULog) -> tuple[float, float]:
    d = u.get_dataset("vehicle_status")
    ts = d.data["timestamp"] / 1e6
    arm = d.data["arming_state"] == 2
    return float(ts[arm].min()), float(ts[arm].max())


def reinit_times(u: ULog, t0: float, t1: float) -> list[float]:
    """Istanti dei reboot driver. Ogni reboot logga 3 righe u-blox
    (firmware/protocol/module) ravvicinate: le collassiamo in un evento."""
    raw = sorted(m.timestamp / 1e6 for m in u.logged_messages
                 if t0 <= m.timestamp / 1e6 <= t1 and "u-blox" in m.message.lower())
    events: list[float] = []
    for t in raw:
        if not events or t - events[-1] > 1.0:
            events.append(t)
    return events


def rtcm_tx_bps(u: ULog, t0: float, t1: float) -> float:
    """Byte/s di RTCM (frame che iniziano con 0xD3) iniettati da PX4 verso il
    rover, ricostruiti dal topic gps_dump (bit 7 di len = direzione TX)."""
    try:
        d = u.get_dataset("gps_dump")
    except (KeyError, IndexError):
        return float("nan")
    ts = d.data["timestamp"] / 1e6
    ln = d.data["len"]
    istx = (ln & 0x80) != 0
    cols = np.array([d.data[f"data[{i}]"] for i in range(79)]).T
    rtcm = 0
    for i in np.where((ts >= t0) & (ts <= t1) & istx)[0]:
        n = int(ln[i] & 0x7F)
        buf = bytes(int(b) & 0xFF for b in cols[i][:n])
        j = 0
        while j < len(buf):
            if buf[j] == 0xD3 and j + 2 < len(buf):
                length = ((buf[j + 1] & 0x03) << 8) | buf[j + 2]
                tot = 3 + length + 3
                rtcm += tot
                j += tot
                continue
            j += 1
    return rtcm / max(t1 - t0, 1e-6)


def gps_series(u: ULog, t0: float, t1: float):
    d = u.get_dataset("sensor_gps")
    ts = d.data["timestamp"] / 1e6
    m = (ts >= t0) & (ts <= t1)
    return ts[m], d.data["fix_type"][m]


def nav_gaps(ts_gps) -> list[tuple[float, float]]:
    dt = np.diff(ts_gps)
    return [(float(ts_gps[i]), float(dt[i])) for i in range(len(dt)) if dt[i] > NAV_GAP]


def vh_series(u: ULog, t0: float, t1: float):
    d = u.get_dataset("vehicle_local_position")
    ts = d.data["timestamp"] / 1e6
    vh = np.hypot(d.data["vx"], d.data["vy"])
    m = (ts >= t0) & (ts <= t1)
    return ts[m], vh[m]


def vh_at(ts_v, vh, t) -> float:
    m = (ts_v >= t - REINIT_WIN) & (ts_v <= t + REINIT_WIN)
    return float(np.median(vh[m])) if m.any() else float("nan")


def vh_background(ts_v, vh, reinits):
    if not reinits:
        return vh
    keep = np.ones(len(ts_v), dtype=bool)
    for r in reinits:
        keep &= np.abs(ts_v - r) > GUARD
    return vh[keep]


def analyze(path: Path) -> dict:
    u = ULog(str(path), disable_str_exceptions=True)
    t0, t1 = armed_window(u)
    dur = t1 - t0
    reinits = reinit_times(u, t0, t1)
    rtcm = rtcm_tx_bps(u, t0, t1)
    rtk = (rtcm > RTK_BPS)
    ts_g, fix = gps_series(u, t0, t1)
    gaps = nav_gaps(ts_g)
    outage = sum(d for _, d in gaps)
    ts_v, vh = vh_series(u, t0, t1)

    print(f"\n══════ {path.name} — anatomia reinit modo RTK ──────")
    print(f"  Armato            : [{t0:.1f}, {t1:.1f}] s  ({dur:.1f} s)")

    fixvals = dict(zip(*[x.tolist() for x in np.unique(fix, return_counts=True)]))
    label = "RTK ATTIVO" if rtk else "3D (no RTCM)"
    print(f"  Precondizione RTK : RTCM TX {rtcm:.0f} B/s | fix_type {fixvals}  → {label}")

    if reinits:
        period = dur / len(reinits)
        print(f"  Reinit driver     : {len(reinits)}  → LOOP (1 ogni {period:.0f} s)")
        first = reinits[0]
        pre_gaps = [g for g in gaps if g[0] < first]
        if pre_gaps:
            last_nav = pre_gaps[-1][0]
            print(f"  Primo reinit      : @{first:.1f}s ({first-t0:.0f}s dopo armo) | "
                  f"ultimo NAV valido @{last_nav:.1f}s ({first-last_nav:.1f}s prima)")
        else:
            print(f"  Primo reinit      : @{first:.1f}s ({first-t0:.0f}s dopo armo)")
    else:
        print(f"  Reinit driver     : 0  → nessun loop (SANO)")

    print(f"  Stop-NAV (gap>{NAV_GAP:.0f}s): {len(gaps)}  outage tot {outage:.1f}s "
          f"({100*outage/dur:.0f}% del volo)")

    # ── movimento ──
    bg = vh_background(ts_v, vh, reinits)
    bg_med, bg_p90 = float(np.median(bg)), float(np.percentile(bg, 90))
    print(f"\n  Movimento (Vh orizzontale): fondo med={bg_med:.2f} p90={bg_p90:.2f} "
          f"max={float(vh.max()):.2f} m/s")
    if reinits:
        print(f"  {'reinit @s':>10} {'rel':>5} | {'Vh m/s':>7}")
        vh_re = []
        for r in reinits:
            v = vh_at(ts_v, vh, r)
            vh_re.append(v)
            print(f"  {r:10.1f} {r-t0:4.0f}s | {v:7.2f}")
        vh_re = np.array([v for v in vh_re if not np.isnan(v)])
        if len(vh_re):
            ratio = np.median(vh_re) / bg_med if bg_med else float("nan")
            n_hi = int((vh_re > bg_p90).sum())
            print(f"  Vh ai reinit med={np.median(vh_re):.2f} m/s  → ×{ratio:.2f} vs fondo  "
                  f"| reinit con Vh>p90 fondo: {n_hi}/{len(vh_re)}")

    return dict(name=path.name, dur=dur, rtk=rtk, rtcm=rtcm,
                n_reinit=len(reinits), outage=outage, vh_p90=bg_p90)


def comparison_table(rows: list[dict]) -> None:
    print(f"\n══════ Confronto sessione ──────")
    print(f"  {'volo':12s}{'armato':>7s}{'RTCM B/s':>9s}{'modo':>6s}"
          f"{'reinit':>7s}{'outage':>8s}{'Vh p90':>8s}  esito")
    for r in rows:
        modo = "RTK" if r["rtk"] else "3D"
        # GUASTO = loop sostenuto; un reinit isolato è benigno (re-probe), anche in 3D
        esito = "GUASTO" if r["n_reinit"] >= 2 else ("1 reinit" if r["n_reinit"] == 1 else "sano")
        print(f"  {r['name']:12s}{r['dur']:6.0f}s{r['rtcm']:9.0f}{modo:>6s}"
              f"{r['n_reinit']:7d}{r['outage']:7.1f}s{r['vh_p90']:8.2f}  {esito}")
    print("\n  Lettura: il LOOP sostenuto (>=2 reinit, outage grosso) compare solo in")
    print("  modo RTK; un reinit isolato è benigno e capita anche in 3D. Il movimento")
    print("  NON discrimina (12_28_29 peggiore ma in hover come il RTK sano 12_21_42).")
    print("  Grilletto residuo aperto: vedi docstring. Serve test A/B per chiuderlo.")


def main():
    paths = [Path(p) for p in sys.argv[1:]]
    if not paths:
        sys.exit("uso: gps_rtk_reinit_anatomy.py <file.ulg> [file2.ulg ...]")
    rows = []
    for p in sorted(paths):
        try:
            rows.append(analyze(p))
        except Exception as e:  # noqa: BLE001 — tool diagnostico, log e prosegui
            print(f"\n══════ {p.name} ──────\n  ERRORE: {e}")
    if len(rows) > 1:
        comparison_table(rows)


if __name__ == "__main__":
    main()
