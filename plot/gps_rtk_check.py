#!/usr/bin/env python3
"""
Classifica un log PX4 come **GPS puro** vs **RTK** e dice se l'RTK era davvero
attivo (correzioni applicate) o solo "inteso acceso".

Motivazione (2026-06-04): un volo può avere l'RTK acceso lato base/QGC ma NON
ricevere correzioni a bordo → il rover resta in fix 3D. QGC mostra "3D lock".
Non basta un campo per decidere: `rtcm_msg_used` su u-blox vale sempre 0=UNKNOWN
ed è ingannevole. La firma robusta di RTK attivo è la CONGIUNZIONE di:
  - fix_type >= 5  (5=RTK-float, 6=RTK-fixed)
  - rtcm_injection_rate > 0  (PX4 sta iniettando RTCM nel ricevitore)
  - eph che crolla sotto ~0.10 m  (precisione che solo l'RTK dà)
Se i tre non concordano c'è un'incoerenza da spiegare (es. RTCM iniettato ma
fix fermo a 3D = rover non aggancia → vedi maintenance/indagine-rtk-attivo-*).

Uso:
    python3 plot/gps_rtk_check.py log/2026-06-XX/*.ulg
"""

import sys
from pathlib import Path

import numpy as np
from pyulog import ULog

FIX = {0: "no-fix", 1: "no-fix", 2: "2D", 3: "3D",
       4: "3D-DGPS", 5: "RTK-float", 6: "RTK-fixed"}
EPH_RTK = 0.10  # [m] soglia sotto la quale eph è "da RTK"


def armed_window(u: ULog) -> tuple[float, float]:
    """Finestra armato (arming_state==2) in secondi; (0,inf) se assente."""
    try:
        d = u.get_dataset("vehicle_status")
        ts = d.data["timestamp"] / 1e6
        arm = d.data["arming_state"] == 2
        if arm.any():
            return float(ts[arm].min()), float(ts[arm].max())
    except Exception:
        pass
    return 0.0, float("inf")


def classify(path: Path) -> dict:
    u = ULog(str(path), disable_str_exceptions=True)
    t0, t1 = armed_window(u)
    d = u.get_dataset("sensor_gps")
    ts = d.data["timestamp"] / 1e6
    m = (ts >= t0) & (ts <= t1)
    if not m.any():           # nessun sample armato → usa tutto il log
        m = np.ones(len(ts), bool)

    fix = d.data["fix_type"][m]
    eph = d.data["eph"][m]
    sat = d.data["satellites_used"][m]
    inj = d.data["rtcm_injection_rate"][m]
    try:
        crc = d.data["rtcm_crc_failed"][m]
        crc_fail = int(crc.max())
    except KeyError:
        crc_fail = -1

    frac_rtk = float((fix >= 5).mean())
    frac_fixed = float((fix == 6).mean())
    inj_active = float((inj > 0).mean())   # frazione campioni con RTCM iniettato
    eph_med = float(np.median(eph))

    # ── Verdetto ────────────────────────────────────────────────────────────
    if frac_fixed > 0.5:
        verdict = "RTK-FIXED (cm) — correzioni applicate e ambiguità risolte"
    elif frac_rtk > 0.5:
        verdict = "RTK-FLOAT (dm/cm) — correzioni applicate, ambiguità NON risolte"
    elif inj_active > 0.2:
        verdict = ("⚠ INCOERENTE: RTCM iniettato ma fix resta 3D "
                   "→ il rover NON aggancia l'RTK")
    else:
        verdict = "GPS PURO (3D) — nessun RTCM iniettato, RTK non attivo"

    vals, cnts = np.unique(fix, return_counts=True)
    fixstr = " ".join(f"{FIX.get(int(v), v)}:{100*c/cnts.sum():.0f}%"
                      for v, c in zip(vals, cnts))

    return {
        "file": path.name,
        "armed_s": (t1 - t0) if np.isfinite(t1) else float("nan"),
        "fix_distrib": fixstr,
        "sat": (int(sat.min()), int(sat.max())),
        "eph_med": eph_med,
        "inj_active_pct": 100 * inj_active,
        "inj_mean": float(inj.mean()),
        "crc_fail": crc_fail,
        "verdict": verdict,
    }


def main() -> None:
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    rows = []
    for p in (Path(x) for x in sys.argv[1:]):
        try:
            r = classify(p)
        except Exception as e:
            print(f"\n══════ {p.name} ──────\n  ERRORE: {e}")
            continue
        rows.append(r)
        print(f"\n══════ {r['file']} ──────")
        print(f"  Armato        : {r['armed_s']:.0f} s")
        print(f"  fix_type      : {r['fix_distrib']}")
        print(f"  satelliti     : {r['sat'][0]}–{r['sat'][1]}")
        print(f"  eph mediana   : {r['eph_med']:.3f} m"
              f"  ({'< soglia RTK' if r['eph_med'] < EPH_RTK else 'livello GPS'})")
        print(f"  RTCM iniettato: {r['inj_active_pct']:.0f}% dei campioni "
              f"(rate medio {r['inj_mean']:.2f}/s)")
        if r["crc_fail"] >= 0:
            print(f"  RTCM CRC fail : {r['crc_fail']}")
        print(f"  → {r['verdict']}")

    if len(rows) > 1:
        print("\n══════ RIEPILOGO ──────")
        print(f"  {'file':<22} {'arm':>5} {'eph[m]':>7} {'RTCM%':>6}  verdetto")
        for r in rows:
            short = (r["verdict"].split(" —")[0].split(":")[0]
                     .replace("⚠ INCOERENTE", "INCOERENTE"))
            print(f"  {r['file']:<22} {r['armed_s']:4.0f}s "
                  f"{r['eph_med']:7.3f} {r['inj_active_pct']:5.0f}%  {short}")


if __name__ == "__main__":
    main()
