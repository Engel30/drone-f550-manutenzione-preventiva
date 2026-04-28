#!/usr/bin/env python3
"""
Plot IMU — accelerometro e giroscopio.

Genera (in imu/):
  imu_0.png, imu_1.png, imu_2.png  — un grafico per ogni IMU
  imu_confronto.png                 — confronto magnitudo tra le 3 IMU
  imu_vibrazione.png                — metrica di vibrazione (manutenzione)
"""

import os
import sys

# Rende importabile utils.py dalla root di plot/
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Patch

from utils import (
    COLORS_IMU, COLORS_XYZ,
    armed_intervals, armed_legend_patch,
    calc_freq, get_topic, load_ulog, log_t0,
    save_fig, shade_armed, t_sec,
)

MOSTRA_PLOT = True
NUM_IMU = 3
OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))


# ── Singola IMU ───────────────────────────────────────────────────────────────

def plot_imu(ulog, t0, intervals, idx):
    accel = get_topic(ulog, 'sensor_accel', idx)
    gyro  = get_topic(ulog, 'sensor_gyro',  idx)

    ta = t_sec(accel.data, t0)
    tg = t_sec(gyro.data, t0)
    fa = calc_freq(accel.data['timestamp'])
    fg = calc_freq(gyro.data['timestamp'])
    dev_id = int(accel.data['device_id'][0])

    fig, axes = plt.subplots(2, 1, figsize=(13, 7), sharex=True)
    fig.suptitle(
        f"IMU {idx}   |   Device ID: 0x{dev_id:08X}",
        fontsize=12, fontweight='bold', y=0.99,
    )

    ax = axes[0]
    for ch, label, color in zip(['x', 'y', 'z'], ['X', 'Y', 'Z'], COLORS_XYZ):
        ax.plot(ta, accel.data[ch], color=color, label=label, alpha=0.82)
    shade_armed([ax], intervals)
    ax.set_ylabel("Accelerazione  [m/s²]")
    ax.set_title(f"Accelerometro   (f_s = {fa:.1f} Hz)", loc='left', fontsize=9)
    handles, labels = ax.get_legend_handles_labels()
    if intervals:
        handles.append(armed_legend_patch()); labels.append('Armato')
    ax.legend(handles, labels, loc='upper right', ncol=4)

    ax = axes[1]
    for ch, label, color in zip(['x', 'y', 'z'], ['X', 'Y', 'Z'], COLORS_XYZ):
        ax.plot(tg, gyro.data[ch], color=color, label=label, alpha=0.82)
    shade_armed([ax], intervals)
    ax.set_ylabel("Velocità angolare  [rad/s]")
    ax.set_xlabel("Tempo  [s]")
    ax.set_title(f"Giroscopio   (f_s = {fg:.1f} Hz)", loc='left', fontsize=9)
    ax.legend(loc='upper right', ncol=3)

    fig.tight_layout()
    save_fig(fig, OUTPUT_DIR, f"imu_{idx}.png")
    return fig


# ── Confronto 3 IMU ───────────────────────────────────────────────────────────

def plot_confronto(ulog, t0, intervals):
    fig, axes = plt.subplots(2, 1, figsize=(13, 7), sharex=True)
    fig.suptitle(
        "Confronto IMU 0 / 1 / 2   —   Magnitudo segnali",
        fontsize=12, fontweight='bold', y=0.99,
    )

    for i in range(NUM_IMU):
        accel = get_topic(ulog, 'sensor_accel', i)
        gyro  = get_topic(ulog, 'sensor_gyro',  i)
        ta = t_sec(accel.data, t0)
        tg = t_sec(gyro.data, t0)
        fa = calc_freq(accel.data['timestamp'])
        fg = calc_freq(gyro.data['timestamp'])
        mag_a = np.sqrt(accel.data['x']**2 + accel.data['y']**2 + accel.data['z']**2)
        mag_g = np.sqrt(gyro.data['x']**2 + gyro.data['y']**2 + gyro.data['z']**2)
        axes[0].plot(ta, mag_a, color=COLORS_IMU[i], alpha=0.85,
                     label=f"IMU {i}   (f_s = {fa:.1f} Hz)")
        axes[1].plot(tg, mag_g, color=COLORS_IMU[i], alpha=0.85,
                     label=f"IMU {i}   (f_s = {fg:.1f} Hz)")

    for ax, ylabel, title in zip(
        axes,
        ["‖a‖   [m/s²]", "‖ω‖   [rad/s]"],
        ["Magnitudo accelerometro", "Magnitudo giroscopio"],
    ):
        shade_armed([ax], intervals)
        ax.set_ylabel(ylabel)
        ax.set_title(title, loc='left', fontsize=9)
        handles, labels = ax.get_legend_handles_labels()
        if intervals:
            handles.append(armed_legend_patch()); labels.append('Armato')
        ax.legend(handles, labels, loc='upper right', ncol=4)

    axes[1].set_xlabel("Tempo  [s]")
    fig.tight_layout()
    save_fig(fig, OUTPUT_DIR, "imu_confronto.png")
    return fig


# ── Vibrazione ────────────────────────────────────────────────────────────────

def plot_vibrazione(ulog, t0, intervals):
    """Metrica di vibrazione — alta → possibile elica/motore anomalo."""
    fig, axes = plt.subplots(2, 1, figsize=(13, 6), sharex=True)
    fig.suptitle(
        "Metrica di vibrazione IMU  —  (valori alti → elica/motore anomalo)",
        fontsize=11, fontweight='bold', y=0.99,
    )

    found = False
    for i in range(NUM_IMU):
        try:
            s = get_topic(ulog, 'vehicle_imu_status', i)
        except Exception:
            continue
        found = True
        tv = t_sec(s.data, t0)
        fv = calc_freq(s.data['timestamp'])
        axes[0].plot(tv, s.data['accel_vibration_metric'], color=COLORS_IMU[i],
                     alpha=0.85, label=f"IMU {i}   (f_s = {fv:.1f} Hz)")
        axes[1].plot(tv, s.data['gyro_vibration_metric'],  color=COLORS_IMU[i],
                     alpha=0.85, label=f"IMU {i}   (f_s = {fv:.1f} Hz)")

    if not found:
        plt.close(fig)
        return None

    for ax, ylabel, title in zip(
        axes,
        ["Metrica vibrazione accel  [m/s²]", "Metrica vibrazione gyro  [rad/s]"],
        ["Vibrazione accelerometro", "Vibrazione giroscopio"],
    ):
        shade_armed([ax], intervals)
        ax.set_ylabel(ylabel)
        ax.set_title(title, loc='left', fontsize=9)
        handles, labels = ax.get_legend_handles_labels()
        if intervals:
            handles.append(armed_legend_patch()); labels.append('Armato')
        ax.legend(handles, labels, loc='upper right', ncol=4)

    axes[1].set_xlabel("Tempo  [s]")
    fig.tight_layout()
    save_fig(fig, OUTPUT_DIR, "imu_vibrazione.png")
    return fig


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    ulog, fname = load_ulog()
    t0 = log_t0(ulog)
    intervals = armed_intervals(ulog, t0)
    dur = max(d.data['timestamp'][-1] for d in ulog.data_list) / 1e6 - t0
    print(f"  Durata log: {dur:.1f} s   | Intervalli armato: {len(intervals)}")

    for i in range(NUM_IMU):
        try:
            plot_imu(ulog, t0, intervals, i)
        except Exception as e:
            print(f"  [!] IMU {i}: {e}")

    try:
        plot_confronto(ulog, t0, intervals)
    except Exception as e:
        print(f"  [!] Confronto IMU: {e}")

    try:
        plot_vibrazione(ulog, t0, intervals)
    except Exception as e:
        print(f"  [!] Vibrazione IMU: {e}")

    if MOSTRA_PLOT:
        plt.show()


if __name__ == "__main__":
    main()
