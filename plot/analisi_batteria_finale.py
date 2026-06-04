#!/usr/bin/env python3
"""
Analisi finale batteria — ricostruisce il calo di tensione e la caduta.

Uso: python3 plot/analisi_batteria_finale.py <file.ulg>
Stampa numeri chiave (no plot) per fare considerazioni sul crollo finale.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np
from pyulog import ULog

from utils import get_topic, log_t0

WARN = {0: "NONE", 1: "LOW", 2: "CRITICAL", 3: "EMERGENCY", 4: "FAILSAFE"}


def col(d, name):
    return np.asarray(d.data[name])


def main():
    path = sys.argv[1]
    ulog = ULog(path)
    t0 = log_t0(ulog)
    print(f"== {os.path.basename(path)} ==")

    # --- armato ---
    aa = get_topic(ulog, "actuator_armed")
    ta = col(aa, "timestamp") / 1e6 - t0
    armed = col(aa, "armed").astype(bool)
    intervals, start, prev = [], None, False
    for ti, a in zip(ta, armed):
        if a and not prev:
            start = ti
        elif not a and prev:
            intervals.append((start, ti))
        prev = a
    if prev:
        intervals.append((start, ta[-1]))
    print("\n-- Intervalli armato (s) --")
    for s, e in intervals:
        print(f"  {s:8.1f} -> {e:8.1f}   ({e - s:6.1f}s)")
    t_arm_end = intervals[-1][1] if intervals else ta[-1]

    # --- batteria ---
    b = get_topic(ulog, "battery_status")
    tb = col(b, "timestamp") / 1e6 - t0
    V = col(b, "voltage_v")
    I = col(b, "current_a")
    cells = int(np.median(col(b, "cell_count"))) if "cell_count" in b.data else 0
    warn = col(b, "warning").astype(int) if "warning" in b.data else np.zeros_like(tb)
    rem = col(b, "remaining") if "remaining" in b.data else None
    used = col(b, "discharged_mah") if "discharged_mah" in b.data else None
    rint = col(b, "internal_resistance_estimate") if "internal_resistance_estimate" in b.data else None
    Vf = V  # nessun filtrato separato in questa versione fw

    # tensioni per-cella effettivamente popolate
    cellcols = []
    for j in range(14):
        key = f"voltage_cell_v[{j}]"
        if key in b.data:
            c = col(b, key)
            if np.nanmax(c) > 0.5:
                cellcols.append((j, c))

    print(f"\n-- Batteria (celle stimate: {cells}) --")
    print(f"  V iniziale  : {V[0]:.2f} V  ({V[0]/cells:.2f} V/cella)" if cells else f"  V iniziale: {V[0]:.2f} V")
    print(f"  V minima    : {V.min():.2f} V  ({V.min()/cells:.2f} V/cella)  @ t={tb[np.argmin(V)]:.1f}s" if cells else f"  V min: {V.min():.2f}")
    print(f"  V finale    : {V[-1]:.2f} V  ({V[-1]/cells:.2f} V/cella)  @ t={tb[-1]:.1f}s" if cells else f"  V finale: {V[-1]:.2f}")
    print(f"  I max       : {I.max():.1f} A   media: {I.mean():.1f} A")
    if rem is not None:
        print(f"  remaining   : {rem[0]*100:.0f}% -> {rem[-1]*100:.0f}%")
    if used is not None:
        print(f"  scaricati   : {used[-1]:.0f} mAh")
    if rint is not None:
        print(f"  R interna   : {np.nanmedian(rint)*1000:.1f} mΩ (mediana)")
    if cellcols:
        vmin_per_cell = {j: c.min() for j, c in cellcols}
        worst = min(vmin_per_cell, key=vmin_per_cell.get)
        print(f"  celle lette : {[j for j, _ in cellcols]}")
        print(f"  cella peggiore: idx {worst} -> min {vmin_per_cell[worst]:.2f} V")

    # ── TENSIONE/CORRENTE DAGLI ESC (fonte indipendente dal power module) ──
    # ATTENZIONE 2026-06-04: il power module (battery_status) e' GUASTO e segna
    # tensione fissa (~15.7 V) e corrente 0. La verita' di bus arriva dagli ESC.
    try:
        esc = get_topic(ulog, "esc_status")
        teb = col(esc, "timestamp") / 1e6 - t0
        # solo gli ESC realmente connessi (i canali liberi loggano voltage=0)
        conn = [j for j in range(8)
                if f"esc[{j}].esc_voltage" in esc.data
                and np.nanmax(col(esc, f"esc[{j}].esc_voltage")) > 1.0]
        nmot = len(conn)
        Vesc = np.array([col(esc, f"esc[{j}].esc_voltage") for j in conn])
        Iesc = np.array([col(esc, f"esc[{j}].esc_current") for j in conn])
        Vbus = Vesc.mean(axis=0)
        print("\n-- Tensione di BUS dagli ESC (fonte affidabile, power module = GUASTO) --")
        s = max(0, np.searchsorted(teb, intervals[0][0]) if intervals else 0)
        e = np.searchsorted(teb, t_arm_end)
        vc = lambda v: f"{v/cells:.2f}V/c" if cells else ""
        print(f"  V decollo : {Vbus[s]:.2f} V ({vc(Vbus[s])})")
        print(f"  V finale  : {Vbus[e-1]:.2f} V ({vc(Vbus[e-1])})")
        print(f"  V minima  : {Vbus.min():.2f} V ({vc(Vbus.min())})  @ t={teb[np.argmin(Vbus)]:.1f}s")
        print(f"  I tot max : {Iesc.sum(axis=0).max():.1f} A   media: {Iesc.sum(axis=0)[s:e].mean():.1f} A")
        print("\n  Profilo (t : Vbus, Vmin_cella, Isum, RPM medio):")
        for tt in list(np.arange(intervals[0][0] + 5, t_arm_end, 15)) if intervals else []:
            k = np.argmin(np.abs(teb - tt))
            rpmmean = np.mean([col(esc, f"esc[{j}].esc_rpm")[k] for j in conn])
            print(f"    t={tt:7.1f}s  Vbus={Vbus[k]:5.2f} ({vc(Vbus[k])})  Isum={Iesc[:,k].sum():5.1f}A  RPM={rpmmean:5.0f}")
    except Exception as ex:
        print(f"  (esc voltage: {ex})")

    # transizioni di warning
    print("\n-- Transizioni warning batteria --")
    last = -1
    for ti, w in zip(tb, warn):
        if w != last:
            print(f"  t={ti:8.1f}s  ->  {WARN.get(w, w)}")
            last = w

    # --- finestra finale: ultimi 20s armato ---
    print("\n-- Finale: campioni batteria attorno alla fine del volo --")
    mask = tb >= (t_arm_end - 20)
    for ti, v, vf, i, w in zip(tb[mask], V[mask], Vf[mask], I[mask], warn[mask]):
        flag = WARN.get(int(w), w)
        vc = f"{v/cells:.2f}V/c" if cells else ""
        print(f"  t={ti:7.1f}s  V={v:5.2f} ({vc})  Vfilt={vf:5.2f}  I={i:6.1f}A  {flag}")

    # --- quota / discesa ---
    try:
        lp = get_topic(ulog, "vehicle_local_position")
        tl = col(lp, "timestamp") / 1e6 - t0
        z = col(lp, "z")            # NED: z negativo = in alto
        vz = col(lp, "vz")
        print("\n-- Quota e velocità verticale (ultimi 20s) --")
        m = tl >= (t_arm_end - 20)
        # campiona ~1 Hz
        idx = np.where(m)[0]
        step = max(1, len(idx) // 25)
        for k in idx[::step]:
            print(f"  t={tl[k]:7.1f}s  alt={-z[k]:6.2f}m  vz={vz[k]:6.2f}m/s")
    except Exception as e:
        print(f"  (local_position non disponibile: {e})")

    # --- land detected ---
    try:
        ld = get_topic(ulog, "vehicle_land_detected")
        tld = col(ld, "timestamp") / 1e6 - t0
        landed = col(ld, "landed").astype(int)
        print("\n-- Transizioni land_detected --")
        last = -1
        for ti, l in zip(tld, landed):
            if l != last:
                print(f"  t={ti:8.1f}s  landed={l}")
                last = l
    except Exception:
        pass

    # --- nav_state / arming changes ---
    try:
        vs = get_topic(ulog, "vehicle_status")
        tvs = col(vs, "timestamp") / 1e6 - t0
        nav = col(vs, "nav_state").astype(int)
        print("\n-- Transizioni nav_state --")
        last = -1
        for ti, n in zip(tvs, nav):
            if n != last:
                print(f"  t={ti:8.1f}s  nav_state={n}")
                last = n
    except Exception:
        pass

    # --- ESC: cala il regime nel finale? ---
    try:
        esc = get_topic(ulog, "esc_status")
        tе = col(esc, "timestamp") / 1e6 - t0
        # rpm fields
        nfields = sum(1 for k in esc.data if k.endswith("esc_rpm"))
        rpms = []
        for j in range(8):
            key = f"esc[{j}].esc_rpm"
            if key in esc.data:
                rpms.append(col(esc, key))
        if rpms:
            rpm = np.array(rpms)  # shape (n_esc, n_samples)
            mean_rpm = rpm.mean(axis=0)
            print("\n-- RPM medio ESC (ultimi 20s) --")
            m = tе >= (t_arm_end - 20)
            idx = np.where(m)[0]
            step = max(1, len(idx) // 25)
            for k in idx[::step]:
                vals = "  ".join(f"{rpm[j][k]:5.0f}" for j in range(len(rpms)))
                print(f"  t={tе[k]:7.1f}s  medio={mean_rpm[k]:5.0f}  [{vals}]")
    except Exception as e:
        print(f"  (esc_status: {e})")


if __name__ == "__main__":
    main()
