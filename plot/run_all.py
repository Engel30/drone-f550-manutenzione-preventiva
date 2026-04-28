#!/usr/bin/env python3
"""
Avvia tutti gli script di plot in sequenza.

Uso:
    python3 run_all.py

Il file .ulg deve trovarsi nella stessa cartella di questo script (plot/).
I PNG vengono salvati nella sottocartella del rispettivo script.
"""

import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.abspath(__file__))

SCRIPTS = [
    ("IMU",      os.path.join(ROOT, "imu",      "plot_imu.py")),
    ("Batteria", os.path.join(ROOT, "batteria", "plot_batteria.py")),
    ("ESC",      os.path.join(ROOT, "esc",      "plot_esc.py")),
]


def main():
    print("=" * 55)
    print("  PX4 Log Plotter")
    print("=" * 55)

    esiti = []
    for nome, script in SCRIPTS:
        print(f"\n[{nome}]  {os.path.relpath(script, ROOT)}")
        t_start = time.time()
        result = subprocess.run(
            [sys.executable, script],
            env={**os.environ, "MPLBACKEND": "Agg"},
        )
        elapsed = time.time() - t_start
        ok = result.returncode == 0
        stato = "OK" if ok else f"ERRORE (exit {result.returncode})"
        print(f"  {stato}  ({elapsed:.1f} s)")
        esiti.append((nome, ok))

    print("\n" + "=" * 55)
    print("  Riepilogo")
    print("=" * 55)
    for nome, ok in esiti:
        simbolo = "✓" if ok else "✗"
        print(f"  {simbolo}  {nome}")

    falliti = sum(1 for _, ok in esiti if not ok)
    if falliti == 0:
        print("\n  Tutti i plot completati.")
    else:
        print(f"\n  {falliti} script terminato/i con errore.")
        sys.exit(1)


if __name__ == "__main__":
    main()
