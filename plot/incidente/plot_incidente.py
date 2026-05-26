#!/usr/bin/env python3
"""
Analisi forense dello schianto del 2026-05-26.

Legge il .ulg dalla cartella log_current/ (via utils.find_ulog).
Genera 5 figure dedicate alla ricostruzione dell'incidente:
  1. cronologia_volo.png   — assetto (roll/pitch/yaw) + quota + eventi
  2. dinamica_angolare.png — rate setpoint vs misurato sui 3 assi
  3. motori_rpm.png        — RPM 6 ESC + comandi normalizzati
  4. comandi_pilota.png    — stick RC roll/pitch/yaw/throttle
  5. vibrazioni_impatto.png — accel/gyro vibration metric + clipping
"""

import os
import sys

import matplotlib.pyplot as plt
import numpy as np
from pyulog import ULog

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import (COLORS_ESC, COLORS_XYZ, COLOR_SETPT, SCRIPT_DIR,
                   armed_intervals, armed_legend_patch, find_ulog,
                   save_fig, shade_armed)

OUT_DIR = os.path.dirname(os.path.abspath(__file__))

# Eventi chiave estratti da ulog.logged_messages
EVENTS = [
    (1064.81, 'armato',          '#1976D2'),
    (1066.88, 'takeoff',         '#388E3C'),
    (1075.94, 'pilota prende\nil controllo', '#F57C00'),
    (1079.15, 'attitude failure\n(roll>60°)', '#D32F2F'),
    (1079.16, 'failsafe',        '#7B1FA2'),
    (1079.85, 'impatto',         '#000000'),
]

# Finestra di interesse stretta sul crash
T_FOCUS = (1064.0, 1081.0)


def get(ulog, name, inst=0):
    for d in ulog.data_list:
        if d.name == name and d.multi_id == inst:
            return d
    return None


def quat_to_euler(q0, q1, q2, q3):
    roll = np.arctan2(2 * (q0 * q1 + q2 * q3), 1 - 2 * (q1 * q1 + q2 * q2))
    pitch = np.arcsin(np.clip(2 * (q0 * q2 - q3 * q1), -1, 1))
    yaw = np.arctan2(2 * (q0 * q3 + q1 * q2), 1 - 2 * (q2 * q2 + q3 * q3))
    return np.degrees(roll), np.degrees(pitch), np.degrees(yaw)


def annota_eventi(ax, ymin=None, ymax=None, etichette=True):
    for t, lbl, col in EVENTS:
        if T_FOCUS[0] <= t <= T_FOCUS[1]:
            ax.axvline(t, color=col, linestyle='--', linewidth=0.9, alpha=0.7, zorder=1)
            if etichette:
                yl = ax.get_ylim()
                y = yl[1] - (yl[1] - yl[0]) * 0.05
                ax.annotate(lbl, xy=(t, y), xytext=(2, 0), textcoords='offset points',
                            fontsize=6.5, color=col, va='top', ha='left', alpha=0.9)


def setup_ax(ax, xlim=T_FOCUS):
    ax.set_xlim(*xlim)


# ── Figura 1: cronologia ──────────────────────────────────────────────────────

def fig_cronologia(ulog, t0, armed):
    att = get(ulog, 'vehicle_attitude').data
    ta = att['timestamp'] / 1e6 - t0
    roll, pitch, yaw = quat_to_euler(att['q[0]'], att['q[1]'], att['q[2]'], att['q[3]'])

    lp = get(ulog, 'vehicle_local_position').data
    tlp = lp['timestamp'] / 1e6 - t0
    alt = -lp['z']  # NED → quota positiva verso l'alto

    fig, axes = plt.subplots(3, 1, figsize=(12, 8), sharex=True)
    shade_armed(axes, armed)

    ax = axes[0]
    ax.plot(ta, roll,  color=COLORS_XYZ[0], label='roll')
    ax.plot(ta, pitch, color=COLORS_XYZ[1], label='pitch')
    ax.axhline(+60, color='#D32F2F', linestyle=':', linewidth=0.8, alpha=0.6)
    ax.axhline(-60, color='#D32F2F', linestyle=':', linewidth=0.8, alpha=0.6,
               label='soglia failure ±60°')
    ax.set_ylabel('assetto [deg]')
    ax.set_ylim(-130, 130)
    ax.set_title('Cronologia del volo — assetto, yaw e quota')
    ax.legend(loc='lower left', ncol=4)
    annota_eventi(ax)

    ax = axes[1]
    ax.plot(ta, yaw, color=COLORS_XYZ[2], label='yaw')
    ax.set_ylabel('yaw [deg]')
    ax.legend(loc='lower left')

    ax = axes[2]
    ax.plot(tlp, alt, color='#37474F', label='quota (−z NED)')
    ax.fill_between(tlp, 0, alt, where=alt > 0, color='#90CAF9', alpha=0.3)
    ax.axhline(0, color='#5D4037', linewidth=0.9)
    ax.set_ylabel('quota [m]')
    ax.set_xlabel('tempo [s]')
    ax.legend(loc='upper left')

    for ax in axes:
        setup_ax(ax)
    fig.tight_layout()
    save_fig(fig, OUT_DIR, 'cronologia_volo.png')
    plt.close(fig)


# ── Figura 2: dinamica angolare ──────────────────────────────────────────────

def fig_dinamica_angolare(ulog, t0, armed):
    av = get(ulog, 'vehicle_angular_velocity').data
    tav = av['timestamp'] / 1e6 - t0
    rs = get(ulog, 'vehicle_rates_setpoint').data
    trs = rs['timestamp'] / 1e6 - t0

    fig, axes = plt.subplots(3, 1, figsize=(12, 8), sharex=True)
    shade_armed(axes, armed)
    nomi = ('roll', 'pitch', 'yaw')
    chiavi_av = ('xyz[0]', 'xyz[1]', 'xyz[2]')
    chiavi_rs = ('roll', 'pitch', 'yaw')

    for i, ax in enumerate(axes):
        ax.plot(trs, np.degrees(rs[chiavi_rs[i]]), color=COLOR_SETPT,
                linewidth=0.9, alpha=0.8, label='setpoint')
        ax.plot(tav, np.degrees(av[chiavi_av[i]]), color=COLORS_XYZ[i],
                label='misurato')
        ax.set_ylabel(f'{nomi[i]} rate [deg/s]')
        ax.legend(loc='upper left')
        setup_ax(ax)
        if i == 0:
            ax.set_title('Velocità angolari: setpoint vs misurato (saturazioni rivelano PIO)')
        annota_eventi(ax, etichette=(i == 0))

    axes[-1].set_xlabel('tempo [s]')
    fig.tight_layout()
    save_fig(fig, OUT_DIR, 'dinamica_angolare.png')
    plt.close(fig)


# ── Figura 3: motori RPM + comandi ───────────────────────────────────────────

def fig_motori(ulog, t0, armed):
    am = get(ulog, 'actuator_motors').data
    tam = am['timestamp'] / 1e6 - t0
    esc = get(ulog, 'esc_status')

    fig, axes = plt.subplots(2, 1, figsize=(12, 7.5), sharex=True)
    shade_armed(axes, armed)

    ax = axes[0]
    for k in range(6):
        ax.plot(tam, am[f'control[{k}]'], color=COLORS_ESC[k], linewidth=0.7,
                label=f'M{k+1}')
    ax.set_ylabel('comando motore [−1…+1]')
    ax.set_title('Comandi motori e RPM ESC')
    ax.set_ylim(-0.05, 1.05)
    ax.legend(loc='upper left', ncol=6)
    annota_eventi(ax)
    setup_ax(ax)

    ax = axes[1]
    if esc is not None:
        e = esc.data
        te = e['timestamp'] / 1e6 - t0
        for k in range(6):
            ax.plot(te, e[f'esc[{k}].esc_rpm'], color=COLORS_ESC[k], linewidth=0.9,
                    label=f'ESC{k+1}')
    ax.set_ylabel('RPM')
    ax.set_xlabel('tempo [s]')
    ax.legend(loc='upper left', ncol=6)
    setup_ax(ax)

    fig.tight_layout()
    save_fig(fig, OUT_DIR, 'motori_rpm.png')
    plt.close(fig)


# ── Figura 4: comandi pilota ─────────────────────────────────────────────────

def fig_pilota(ulog, t0, armed):
    mc = get(ulog, 'manual_control_setpoint')
    if mc is None:
        return
    d = mc.data
    tmc = d['timestamp'] / 1e6 - t0

    fig, axes = plt.subplots(2, 1, figsize=(12, 6.5), sharex=True)
    shade_armed(axes, armed)

    ax = axes[0]
    ax.plot(tmc, d['roll'],  color=COLORS_XYZ[0], label='roll stick')
    ax.plot(tmc, d['pitch'], color=COLORS_XYZ[1], label='pitch stick')
    ax.plot(tmc, d['yaw'],   color=COLORS_XYZ[2], label='yaw stick')
    ax.axhline(+1, color='#B71C1C', linestyle=':', linewidth=0.6, alpha=0.5)
    ax.axhline(-1, color='#B71C1C', linestyle=':', linewidth=0.6, alpha=0.5)
    ax.set_ylim(-1.15, 1.15)
    ax.set_ylabel('input pilota [−1…+1]')
    ax.set_title('Comandi pilota — cyclic e throttle')
    ax.legend(loc='upper left', ncol=3)
    annota_eventi(ax)
    setup_ax(ax)

    ax = axes[1]
    ax.plot(tmc, d['throttle'], color='#37474F', label='throttle stick')
    ax.axhline(0, color='#9E9E9E', linewidth=0.7)
    ax.set_ylim(-1.15, 1.15)
    ax.set_ylabel('throttle [−1…+1]')
    ax.set_xlabel('tempo [s]')
    ax.legend(loc='upper left')
    setup_ax(ax)

    fig.tight_layout()
    save_fig(fig, OUT_DIR, 'comandi_pilota.png')
    plt.close(fig)


# ── Figura 5: vibrazioni + impatto ───────────────────────────────────────────

def fig_vibrazioni(ulog, t0, armed):
    imu = get(ulog, 'vehicle_imu_status', 0)
    if imu is None:
        return
    d = imu.data
    ti = d['timestamp'] / 1e6 - t0

    fig, axes = plt.subplots(3, 1, figsize=(12, 7.5), sharex=True)
    shade_armed(axes, armed)

    ax = axes[0]
    ax.plot(ti, d['accel_vibration_metric'], color='#E53935', label='accel vibration')
    ax.set_ylabel('accel vib [m/s²]')
    ax.set_title('Vibrazioni IMU0 e clipping accelerometro')
    ax.legend(loc='upper left')
    annota_eventi(ax)
    setup_ax(ax)

    ax = axes[1]
    ax.plot(ti, d['gyro_vibration_metric'], color='#1E88E5', label='gyro vibration')
    ax.set_ylabel('gyro vib [rad/s]')
    ax.legend(loc='upper left')
    setup_ax(ax)

    ax = axes[2]
    for k, c in enumerate(COLORS_XYZ):
        ax.plot(ti, d[f'accel_clipping[{k}]'], color=c, label=f'clip asse {"XYZ"[k]}')
    ax.set_ylabel('clip count')
    ax.set_xlabel('tempo [s]')
    ax.legend(loc='upper left', ncol=3)
    setup_ax(ax)

    fig.tight_layout()
    save_fig(fig, OUT_DIR, 'vibrazioni_impatto.png')
    plt.close(fig)


def main():
    ulg_path = find_ulog()
    print(f"Caricamento: {os.path.basename(ulg_path)}")
    ulog = ULog(ulg_path)
    t0 = min(d.data['timestamp'][0] for d in ulog.data_list) / 1e6
    armed = armed_intervals(ulog, t0)

    fig_cronologia(ulog, t0, armed)
    fig_dinamica_angolare(ulog, t0, armed)
    fig_motori(ulog, t0, armed)
    fig_pilota(ulog, t0, armed)
    fig_vibrazioni(ulog, t0, armed)


if __name__ == "__main__":
    main()
