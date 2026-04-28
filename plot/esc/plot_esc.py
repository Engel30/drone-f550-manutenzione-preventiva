#!/usr/bin/env python3
"""
Plot velocità ESC (RPM) con setpoint dei motori dal log PX4.

Genera (in esc/):
  esc_velocita.png  — RPM + comando per i 6 motori + riepilogo con squilibrio
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import matplotlib.gridspec as gridspec
import matplotlib.pyplot as plt
import numpy as np

from utils import (
    COLOR_SETPT, COLORS_ESC,
    armed_intervals, armed_legend_patch,
    calc_freq, get_topic, load_ulog, log_t0,
    save_fig, shade_armed, t_sec,
)

MOSTRA_PLOT = True
N_MOTORI = 6
OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))


def main():
    ulog, fname = load_ulog()
    t0 = log_t0(ulog)
    intervals = armed_intervals(ulog, t0)

    esc    = get_topic(ulog, 'esc_status')
    motors = get_topic(ulog, 'actuator_motors')

    t_esc  = t_sec(esc.data, t0)
    t_mot  = t_sec(motors.data, t0)
    fs_esc = calc_freq(esc.data['timestamp'])
    fs_mot = calc_freq(motors.data['timestamp'])

    fig = plt.figure(figsize=(15, 14))
    fig.suptitle(
        f"ESC — Velocità motori e setpoint   |   {fname}\n"
        f"ESC: f_s = {fs_esc:.1f} Hz   |   Setpoint: f_s = {fs_mot:.1f} Hz",
        fontsize=11, fontweight='bold', y=0.995,
    )

    gs = gridspec.GridSpec(
        3, 3,
        figure=fig,
        hspace=0.50, wspace=0.35,
        height_ratios=[1, 1, 1.1],
    )

    # 6 subplot individuali (righe 0–1, colonne 0–2)
    ax_motors = []
    for i in range(N_MOTORI):
        ax = fig.add_subplot(gs[i // 3, i % 3])
        ax_motors.append(ax)

    # Subplot riepilogo (riga 2, tutte le colonne)
    ax_summary = fig.add_subplot(gs[2, :])

    # ── Singoli motori ────────────────────────────────────────────────────────
    for i in range(N_MOTORI):
        ax    = ax_motors[i]
        rpm   = esc.data[f'esc[{i}].esc_rpm']
        cmd   = motors.data[f'control[{i}]']
        color = COLORS_ESC[i]

        ax.plot(t_esc, rpm, color=color, linewidth=1.0, alpha=0.9,
                label=f'RPM  (f_s={fs_esc:.0f} Hz)')
        ax.set_ylabel("RPM", fontsize=8)
        ax.tick_params(axis='y', labelsize=7)

        ax_r = ax.twinx()
        ax_r.plot(t_mot, cmd, color=COLOR_SETPT, linewidth=0.8,
                  linestyle='--', alpha=0.75,
                  label=f'Setpoint  (f_s={fs_mot:.0f} Hz)')
        ax_r.set_ylabel("Cmd  [0–1]", fontsize=7, color=COLOR_SETPT)
        ax_r.tick_params(axis='y', labelcolor=COLOR_SETPT, labelsize=6)
        ax_r.spines['right'].set_visible(True)
        ax_r.set_ylim(-0.05, 1.15)

        shade_armed([ax], intervals)
        ax.set_title(f"Motore {i + 1}", fontsize=9, fontweight='bold', color=color)
        ax.set_xlabel("Tempo  [s]", fontsize=7)

        h1, l1 = ax.get_legend_handles_labels()
        h2, l2 = ax_r.get_legend_handles_labels()
        ax.legend(h1 + h2, l1 + l2, loc='upper left', ncol=1,
                  fontsize=6, framealpha=0.7)

    # ── Riepilogo ─────────────────────────────────────────────────────────────
    for i in range(N_MOTORI):
        ax_summary.plot(t_esc, esc.data[f'esc[{i}].esc_rpm'],
                        color=COLORS_ESC[i], linewidth=1.1, alpha=0.85,
                        label=f'M{i + 1}')

    shade_armed([ax_summary], intervals)
    ax_summary.set_ylabel("RPM")
    ax_summary.set_xlabel("Tempo  [s]")
    ax_summary.set_title(
        f"Confronto tutti i motori   (f_s = {fs_esc:.1f} Hz)",
        loc='left', fontsize=9,
    )

    # Metrica di squilibrio RPM (solo campioni in volo)
    rpm_matrix = np.column_stack(
        [esc.data[f'esc[{i}].esc_rpm'] for i in range(N_MOTORI)]
    )
    in_flight = np.sum(rpm_matrix > 100, axis=1) >= 5
    if in_flight.any():
        rpm_fl    = rpm_matrix[in_flight]
        mean_safe = np.where(rpm_fl.mean(axis=1, keepdims=True) > 0,
                             rpm_fl.mean(axis=1, keepdims=True), 1)
        imbalance = (rpm_fl.std(axis=1) / mean_safe.squeeze()) * 100
        ax_r_sum  = ax_summary.twinx()
        ax_r_sum.fill_between(t_esc[in_flight], imbalance,
                              color='#FFCDD2', alpha=0.4, label='Squilibrio  [%]')
        ax_r_sum.set_ylabel("Squilibrio  [%]", fontsize=8, color='#C62828')
        ax_r_sum.tick_params(axis='y', labelcolor='#C62828', labelsize=7)
        ax_r_sum.spines['right'].set_visible(True)
        ax_r_sum.set_ylim(0, max(float(imbalance.max()) * 2, 5))
        h_r, l_r = ax_r_sum.get_legend_handles_labels()
    else:
        h_r, l_r = [], []

    handles, labels = ax_summary.get_legend_handles_labels()
    handles += h_r
    labels  += l_r
    if intervals:
        handles.append(armed_legend_patch()); labels.append('Armato')
    ax_summary.legend(handles, labels, loc='upper right', ncol=8)

    save_fig(fig, OUTPUT_DIR, "esc_velocita.png")

    if MOSTRA_PLOT:
        plt.show()


if __name__ == "__main__":
    main()
