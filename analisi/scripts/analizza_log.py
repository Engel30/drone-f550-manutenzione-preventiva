"""
Estrazione metriche da log .ulg per confronto fra:
  - Set A: baseline, pale sane (6 voli, swap di posizione)
  - Set B: pala accorciata 5 %, montata a turno su M1…M6 (6 voli)
  - Set C: pala accorciata 10 % (al 2026-05-27 disponibile solo C.1 su M1)

Per ogni log, sull'intervallo armato più lungo, calcola:
  - vibrazione accel/gyro     (vehicle_imu_status)
  - hover thrust              (hover_thrust_estimate)
  - imbalanced_prop_metric    (failure_detector_status)
  - RPM e corrente per motore (esc_status)
  - comando motore            (actuator_motors.control[i])
  - integratori PID rate      (rate_ctrl_status)

Output: JSON su stdout (vedi analisi/dati/risultati.json).
"""
import os, sys, json
import numpy as np
from pyulog import ULog

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))
LOG_DIR = os.path.join(REPO_ROOT, "log", "2026-05-27")

SET_A = {
    "A.1 (2↔4)":   "13_56_40.ulg",
    "A.2 (2↔5)":   "14_00_42.ulg",
    "A.3 (4↔5)":   "14_05_57.ulg",
    "A.4 (1↔3)":   "14_09_26.ulg",
    "A.5 (3↔6)":   "14_12_24.ulg",
    "A.6 (3↔6r)":  "14_15_52.ulg",
}
SET_B = {
    "B.1 M1": "16_00_57.ulg",
    "B.2 M2": "15_47_35.ulg",
    "B.3 M3": "16_03_10.ulg",
    "B.4 M4": "15_50_20.ulg",
    "B.5 M5": "15_54_10.ulg",
    "B.6 M6": "16_05_24.ulg",
}
SET_C = {
    "C.1 M1": "16_07_29.ulg",
}

def get_topics(ulog, name):
    return [d for d in ulog.data_list if d.name == name]

def armed_window(ulog):
    arm = get_topics(ulog, 'actuator_armed')
    if not arm: return None
    d = arm[0]
    t = d.data['timestamp']; a = d.data['armed'].astype(bool)
    starts, ends, prev, s = [], [], False, None
    for ti, ai in zip(t, a):
        if ai and not prev: s = ti
        elif not ai and prev: starts.append(s); ends.append(ti)
        prev = ai
    if prev: starts.append(s); ends.append(t[-1])
    if not starts: return None
    durations = [e - s for s, e in zip(starts, ends)]
    idx = int(np.argmax(durations))
    return starts[idx], ends[idx]

def stats(arr):
    arr = arr[np.isfinite(arr)]
    if len(arr) == 0: return None
    return {"mean": float(np.mean(arr)), "median": float(np.median(arr)),
            "p95": float(np.percentile(arr, 95)), "max": float(np.max(arr)),
            "std": float(np.std(arr))}

def analyze(path):
    try: ulog = ULog(path)
    except Exception as e: return {"error": str(e)}
    win = armed_window(ulog)
    if win is None: return {"error": "non armato"}
    t0, t1 = win
    out = {"duration_armed_s": (t1 - t0) / 1e6}

    def mask(data):
        t = data['timestamp']; return (t >= t0) & (t <= t1)

    # vibration
    vib_a, vib_g = [], []
    for d in get_topics(ulog, 'vehicle_imu_status'):
        m = mask(d.data)
        if 'accel_vibration_metric' in d.data: vib_a.append(d.data['accel_vibration_metric'][m])
        if 'gyro_vibration_metric'  in d.data: vib_g.append(d.data['gyro_vibration_metric'][m])
    if vib_a: out['accel_vib'] = stats(np.concatenate(vib_a))
    if vib_g: out['gyro_vib']  = stats(np.concatenate(vib_g))

    # imbalanced prop
    fd = get_topics(ulog, 'failure_detector_status')
    if fd:
        d = fd[0]; m = mask(d.data)
        if 'imbalanced_prop_metric' in d.data:
            out['imbalanced_prop'] = stats(d.data['imbalanced_prop_metric'][m])

    # hover thrust
    ht = get_topics(ulog, 'hover_thrust_estimate')
    if ht:
        d = ht[0]; m = mask(d.data)
        if 'hover_thrust' in d.data:
            out['hover_thrust'] = stats(d.data['hover_thrust'][m])

    # esc rpm / current
    esc = get_topics(ulog, 'esc_status')
    if esc:
        d = esc[0]; m = mask(d.data)
        rpm, cur = {}, {}
        for i in range(6):
            for k in (f"esc[{i}].esc_rpm", f"esc_rpm[{i}]"):
                if k in d.data:
                    rpm[f"M{i+1}"] = stats(d.data[k][m].astype(float)); break
            for k in (f"esc[{i}].esc_current", f"esc_current[{i}]"):
                if k in d.data:
                    cur[f"M{i+1}"] = stats(d.data[k][m].astype(float)); break
        if rpm: out['rpm'] = rpm
        if cur: out['current'] = cur

    # motor commands
    am = get_topics(ulog, 'actuator_motors')
    if am:
        d = am[0]; m = mask(d.data); ctrl = {}
        for i in range(6):
            k = f"control[{i}]"
            if k in d.data:
                ctrl[f"M{i+1}"] = stats(d.data[k][m].astype(float))
        if ctrl: out['motor_cmd'] = ctrl

    # rate PID integrators
    rcs = get_topics(ulog, 'rate_ctrl_status')
    if rcs:
        d = rcs[0]; m = mask(d.data); rc = {}
        for ax in ('rollspeed_integ', 'pitchspeed_integ', 'yawspeed_integ'):
            if ax in d.data: rc[ax] = stats(np.abs(d.data[ax][m].astype(float)))
        if rc: out['rate_pid_integ'] = rc

    return out

def main():
    results = {"A": {}, "B": {}, "C": {}}
    for label, fname in SET_A.items():
        print(f"[A] {label}: {fname}", file=sys.stderr)
        results["A"][label] = analyze(os.path.join(LOG_DIR, fname))
    for label, fname in SET_B.items():
        print(f"[B] {label}: {fname}", file=sys.stderr)
        results["B"][label] = analyze(os.path.join(LOG_DIR, fname))
    for label, fname in SET_C.items():
        print(f"[C] {label}: {fname}", file=sys.stderr)
        results["C"][label] = analyze(os.path.join(LOG_DIR, fname))
    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    main()
