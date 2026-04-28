#!/usr/bin/env python3
"""
Plot batteria dal log PX4.

Genera (in batteria/):
  batteria.png  — tensione, corrente, potenza, SoC, temperatura
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import matplotlib.pyplot as plt
import numpy as np

from utils import (
    armed_intervals, armed_legend_patch,
    calc_freq, get_topic, load_ulog, log_t0,
    save_fig, shade_armed, t_sec,
)

MOSTRA_PLOT = True
OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))


def main():
    ulog, fname = load_ulog()
    t0 = log_t0(ulog)
    intervals = armed_intervals(ulog, t0)

    batt = get_topic(ulog, 'battery_status')
    tb = t_sec(batt.data, t0)
    fs = calc_freq(batt.data['timestamp'])

    fig, axes = plt.subplots(5, 1, figsize=(13, 14), sharex=True)
    fig.suptitle(
        f"Batteria   |   f_s = {fs:.1f} Hz   |   {fname}",
        fontsize=12, fontweight='bold', y=0.995,
    )

    # 1 — Tensione totale + per cella
    ax = axes[0]
    ax.plot(tb, batt.data['voltage_v'], color='#1E88E5', label='Tensione totale')
    cell_count = int(batt.data['cell_count'][0]) if 'cell_count' in batt.data else 0
    if cell_count > 0:
        ax_r = ax.twinx()
        ax_r.plot(tb, batt.data['voltage_v'] / cell_count,
                  color='#90CAF9', linewidth=0.8, linestyle='--',
                  label=f'Per cella  ({cell_count}S)')
        ax_r.set_ylabel("Tensione per cella  [V]", fontsize=8, color='#90CAF9')
        ax_r.tick_params(axis='y', labelcolor='#90CAF9', labelsize=7)
        ax_r.spines['right'].set_visible(True)
    ax.set_ylabel("Tensione  [V]")
    shade_armed([ax], intervals)
    handles, labels = ax.get_legend_handles_labels()
    if intervals:
        handles.append(armed_legend_patch()); labels.append('Armato')
    ax.legend(handles, labels, loc='upper right', ncol=3)

    # 2 — Corrente
    ax = axes[1]
    ax.plot(tb, batt.data['current_a'], color='#E53935', alpha=0.7,
            linewidth=0.8, label='Corrente istantanea')
    ax.plot(tb, batt.data['current_average_a'], color='#B71C1C',
            linewidth=1.5, label='Corrente media')
    ax.set_ylabel("Corrente  [A]")
    shade_armed([ax], intervals)
    ax.legend(loc='upper right', ncol=2)

    # 3 — Potenza
    ax = axes[2]
    potenza = batt.data['voltage_v'] * batt.data['current_a']
    ax.plot(tb, potenza, color='#FB8C00', alpha=0.75, linewidth=0.8,
            label='Potenza istantanea')
    ax.plot(tb, batt.data['voltage_v'] * batt.data['current_average_a'],
            color='#E65100', linewidth=1.5, label='Potenza (corrente media)')
    ax.set_ylabel("Potenza  [W]")
    shade_armed([ax], intervals)
    ax.legend(loc='upper right', ncol=2)

    # 4 — SoC + capacità consumata
    ax = axes[3]
    ax.plot(tb, batt.data['remaining'] * 100, color='#43A047',
            linewidth=1.3, label='SoC  [%]')
    ax.set_ylabel("SoC  [%]")
    ax.set_ylim(0, 105)
    ax_r2 = ax.twinx()
    ax_r2.plot(tb, batt.data['discharged_mah'], color='#A5D6A7',
               linewidth=0.9, linestyle='--', label='Scaricato  [mAh]')
    ax_r2.set_ylabel("Capacità scaricata  [mAh]", fontsize=8, color='#388E3C')
    ax_r2.tick_params(axis='y', labelcolor='#388E3C', labelsize=7)
    ax_r2.spines['right'].set_visible(True)
    shade_armed([ax], intervals)
    h1, l1 = ax.get_legend_handles_labels()
    h2, l2 = ax_r2.get_legend_handles_labels()
    handles = h1 + h2
    labels  = l1 + l2
    if intervals:
        handles.append(armed_legend_patch()); labels.append('Armato')
    ax.legend(handles, labels, loc='upper right', ncol=3)

    # 5 — Temperatura
    ax = axes[4]
    temp  = batt.data['temperature']
    valid = ~np.isnan(temp)
    if valid.any():
        ax.plot(tb[valid], temp[valid], color='#8E24AA', label='Temperatura')
        ax.set_ylabel("Temperatura  [°C]")
    else:
        ax.text(0.5, 0.5, "Temperatura non disponibile\n(BMS non connesso)",
                ha='center', va='center', transform=ax.transAxes,
                fontsize=10, color='gray')
        ax.set_ylabel("Temperatura  [°C]")
    shade_armed([ax], intervals)
    ax.set_xlabel("Tempo  [s]")
    handles, labels = ax.get_legend_handles_labels()
    if intervals:
        handles.append(armed_legend_patch()); labels.append('Armato')
    if handles:
        ax.legend(handles, labels, loc='upper right', ncol=2)

    # Annotazione energia totale consumata
    mah_totali = float(batt.data['discharged_mah'][-1])
    wh_totali  = float(np.trapz(potenza, tb)) / 3600.0
    fig.text(
        0.98, 0.01,
        f"Totale consumato:  {mah_totali:.0f} mAh  |  {wh_totali:.1f} Wh",
        ha='right', va='bottom', fontsize=8, color='#455A64',
        bbox=dict(boxstyle='round,pad=0.3', facecolor='#ECEFF1', alpha=0.8),
    )

    fig.tight_layout(rect=[0, 0.02, 1, 1])
    save_fig(fig, OUTPUT_DIR, "batteria.png")

    if MOSTRA_PLOT:
        plt.show()


if __name__ == "__main__":
    main()
