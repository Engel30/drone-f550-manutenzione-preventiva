#!/usr/bin/env python3
"""
Correla i reinit del driver GPS (u-blox) con i transitori di throttle e il
livello di vibrazione, per discriminare un guasto di **contatto meccanico
intermittente** da uno di integrità di segnale (EMI).

Logica: il messaggio "[gps] u-blox firmware version" viene loggato DOPO che il
driver è andato in timeout per perdita di link. Il trigger fisico (il
transitorio che apre il contatto) precede di qualche secondo la riga di log.
Per ogni reinit confrontiamo quindi una *pre-window* [t-PRE, t-LAG] con il
fondo del volo (finestre "quiete" lontane da ogni reinit).

Metriche per finestra:
  - throttle slew = max |Δ(sum-RPM)/Δt|  (esc_status)  → transitorio di spinta
  - vibrazione    = max accel_vibration_metric (vehicle_imu_status, m/s²)

Uso:
    python3 plot/gps_reinit_correlate.py log/2026-06-04/12_28_29.ulg
"""

import sys
from pathlib import Path

import numpy as np
from pyulog import ULog

PRE = 4.0    # inizio pre-window prima del reinit [s]
LAG = 0.5    # fine pre-window prima del reinit [s] (il log arriva dopo il drop)
GUARD = 6.0  # esclusione attorno a ogni reinit per definire le finestre quiete


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


def sum_rpm_series(u: ULog, t0: float, t1: float):
    d = u.get_dataset("esc_status")
    ts = d.data["timestamp"] / 1e6
    rpm = np.zeros(len(ts))
    for k in range(6):
        try:
            rpm += d.data[f"esc[{k}].esc_rpm"]
        except KeyError:
            pass
    m = (ts >= t0) & (ts <= t1)
    return ts[m], rpm[m]


def vib_series(u: ULog, t0: float, t1: float):
    ts_all, v_all = [], []
    for d in u.data_list:
        if d.name == "vehicle_imu_status":
            ts = d.data["timestamp"] / 1e6
            v = d.data["accel_vibration_metric"]
            ts_all.append(ts); v_all.append(v)
    ts = np.concatenate(ts_all); v = np.concatenate(v_all)
    order = np.argsort(ts)
    ts, v = ts[order], v[order]
    m = (ts >= t0) & (ts <= t1)
    return ts[m], v[m]


def peak_slew(ts, rpm, a, b) -> float:
    m = (ts >= a) & (ts <= b)
    if m.sum() < 2:
        return np.nan
    t, r = ts[m], rpm[m]
    dt = np.diff(t)
    dt[dt < 1e-3] = 1e-3
    return float(np.max(np.abs(np.diff(r) / dt)))


def peak_vib(ts, v, a, b) -> float:
    m = (ts >= a) & (ts <= b)
    return float(np.max(v[m])) if m.any() else np.nan


def quiet_windows(t0, t1, reinits, width):
    """Finestre di larghezza `width` che non cadono entro GUARD da un reinit."""
    out = []
    t = t0
    while t + width <= t1:
        c = t + width / 2
        if all(abs(c - r) > GUARD for r in reinits):
            out.append((t, t + width))
        t += width
    return out


def main():
    path = Path(sys.argv[1])
    u = ULog(str(path), disable_str_exceptions=True)
    t0, t1 = armed_window(u)
    reinits = reinit_times(u, t0, t1)
    ts_r, rpm = sum_rpm_series(u, t0, t1)
    ts_v, vib = vib_series(u, t0, t1)
    width = PRE - LAG

    print(f"\n══════ {path.name} — correlazione reinit ↔ throttle/vibrazione ──────")
    print(f"  Finestra armato : [{t0:.1f}, {t1:.1f}] s  ({t1-t0:.1f} s)")
    print(f"  Reinit driver   : {len(reinits)}  (1 ogni {(t1-t0)/max(len(reinits),1):.0f} s)")
    print(f"  Pre-window      : [t-{PRE}s, t-{LAG}s] prima di ogni reinit\n")

    print(f"  {'reinit @s':>10} {'rel':>6} | {'slew RPM/s':>11} {'vibr m/s²':>10}")
    slews, vibs = [], []
    for r in reinits:
        s = peak_slew(ts_r, rpm, r - PRE, r - LAG)
        vv = peak_vib(ts_v, vib, r - PRE, r - LAG)
        slews.append(s); vibs.append(vv)
        print(f"  {r:10.1f} {r-t0:5.0f}s | {s:11.0f} {vv:10.2f}")

    qw = quiet_windows(t0, t1, reinits, width)
    q_slew = np.array([peak_slew(ts_r, rpm, a, b) for a, b in qw])
    q_vib = np.array([peak_vib(ts_v, vib, a, b) for a, b in qw])
    q_slew = q_slew[~np.isnan(q_slew)]; q_vib = q_vib[~np.isnan(q_vib)]
    slews = np.array([s for s in slews if not np.isnan(s)])
    vibs = np.array([v for v in vibs if not np.isnan(v)])

    def line(name, pre, base, unit):
        pm, p90 = np.median(pre), np.percentile(base, 90)
        ratio = np.median(pre) / np.median(base) if np.median(base) else float("nan")
        print(f"  {name:<14} pre-reinit med={pm:8.1f}{unit}  "
              f"fondo med={np.median(base):8.1f} p90={p90:8.1f}{unit}  "
              f"→ ×{ratio:.2f} vs fondo")

    print(f"\n  ── Confronto pre-reinit vs fondo ({len(qw)} finestre quiete) ──")
    line("throttle slew", slews, q_slew, "")
    line("vibrazione", vibs, q_vib, "")

    # quanti reinit hanno pre-window sopra il 90° percentile del fondo
    s90, v90 = np.percentile(q_slew, 90), np.percentile(q_vib, 90)
    n_s = int((slews > s90).sum()); n_v = int((vibs > v90).sum())
    print(f"\n  Reinit con slew  > p90 fondo : {n_s}/{len(slews)}")
    print(f"  Reinit con vibr. > p90 fondo : {n_v}/{len(vibs)}")


if __name__ == "__main__":
    main()
