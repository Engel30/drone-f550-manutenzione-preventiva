"""Utilità condivise per tutti gli script di plot PX4."""

import glob
import os

import matplotlib
import numpy as np
from pyulog import ULog

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT  = os.path.dirname(SCRIPT_DIR)
LOG_CURRENT_DIR = os.path.join(REPO_ROOT, "log_current")

# ── Stile globale ─────────────────────────────────────────────────────────────
matplotlib.rcParams.update({
    'figure.facecolor': 'white',
    'axes.facecolor': '#F7F9FC',
    'axes.edgecolor': '#C8CDD4',
    'axes.grid': True,
    'grid.color': '#E2E6EA',
    'grid.linestyle': '-',
    'grid.linewidth': 0.5,
    'axes.spines.top': False,
    'axes.spines.right': False,
    'axes.titlesize': 10,
    'axes.labelsize': 9,
    'legend.fontsize': 8,
    'legend.framealpha': 0.85,
    'xtick.labelsize': 8,
    'ytick.labelsize': 8,
    'lines.linewidth': 1.1,
    'figure.dpi': 120,
    'savefig.dpi': 150,
    'savefig.bbox': 'tight',
})

# Palette colori
COLORS_XYZ = ['#E53935', '#43A047', '#1E88E5']     # X=rosso, Y=verde, Z=blu
COLORS_IMU  = ['#E53935', '#FB8C00', '#8E24AA']    # IMU 0/1/2
COLORS_ESC  = ['#E53935', '#FB8C00', '#FDD835',
               '#43A047', '#1E88E5', '#8E24AA']    # 6 motori
COLOR_SETPT = '#455A64'                             # setpoint (grigio scuro)


# ── Caricamento log ───────────────────────────────────────────────────────────

def find_ulog() -> str:
    files = glob.glob(os.path.join(LOG_CURRENT_DIR, "*.ulg"))
    if not files:
        raise FileNotFoundError(
            f"Nessun file .ulg trovato in {LOG_CURRENT_DIR}\n"
            f"Copia il log corrente in log_current/ prima di eseguire lo script."
        )
    latest = max(files, key=os.path.getmtime)
    return latest


def load_ulog() -> tuple:
    path = find_ulog()
    name = os.path.basename(path)
    print(f"Caricamento: {name}")
    return ULog(path), name


def get_topic(ulog: ULog, name: str, instance: int = 0):
    matches = [d for d in ulog.data_list if d.name == name]
    if not matches:
        raise KeyError(f"Topic '{name}' non trovato nel log.")
    if instance >= len(matches):
        raise IndexError(f"Istanza {instance} non disponibile per '{name}' "
                         f"(trovate: {len(matches)}).")
    return matches[instance]


# ── Tempo ─────────────────────────────────────────────────────────────────────

def log_t0(ulog: ULog) -> float:
    """Timestamp di inizio log in secondi."""
    return min(d.data['timestamp'][0] for d in ulog.data_list) / 1e6


def t_sec(data_dict: dict, t0: float) -> np.ndarray:
    """Converte timestamp µs in secondi relativi all'inizio del log."""
    return data_dict['timestamp'] / 1e6 - t0


def calc_freq(timestamps_us: np.ndarray) -> float:
    """Frequenza di campionamento mediana in Hz."""
    if len(timestamps_us) < 2:
        return 0.0
    return 1.0 / float(np.median(np.diff(timestamps_us / 1e6)))


# ── Armamento ─────────────────────────────────────────────────────────────────

def armed_intervals(ulog: ULog, t0: float) -> list:
    """Restituisce lista di (t_start, t_end) in secondi in cui il drone è armato."""
    try:
        d = get_topic(ulog, 'actuator_armed')
        t = d.data['timestamp'] / 1e6 - t0
        armed = d.data['armed'].astype(bool)
        intervals, start, prev = [], None, False
        for ti, a in zip(t, armed):
            if a and not prev:
                start = ti
            elif not a and prev:
                intervals.append((start, ti))
            prev = a
        if prev:
            intervals.append((start, t[-1]))
        return intervals
    except Exception:
        return []


def shade_armed(axes, intervals: list) -> None:
    """Colora in verde chiaro i periodi in cui il drone è armato."""
    ax_list = axes if hasattr(axes, '__iter__') else [axes]
    for ax in ax_list:
        for s, e in intervals:
            ax.axvspan(s, e, color='#A5D6A7', alpha=0.20, zorder=0)


def armed_legend_patch():
    from matplotlib.patches import Patch
    return Patch(facecolor='#A5D6A7', alpha=0.5, label='Armato')


# ── Salvataggio ───────────────────────────────────────────────────────────────

def save_fig(fig, output_dir: str, filename: str) -> None:
    path = os.path.join(output_dir, filename)
    fig.savefig(path)
    print(f"  → Salvato: {path}")
