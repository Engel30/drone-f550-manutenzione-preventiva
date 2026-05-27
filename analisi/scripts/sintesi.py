"""Genera tabelle comparative leggibili da risultati.json.

Output: stampa su stdout (vedi analisi/dati/tabelle.txt)."""
import json, os, sys
import numpy as np

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATI_DIR = os.path.join(os.path.dirname(SCRIPT_DIR), "dati")
JSON_PATH = os.path.join(DATI_DIR, "risultati.json")

with open(JSON_PATH) as f: R = json.load(f)

def g(d, *p, default=None):
    for k in p:
        if d is None or k not in d: return default
        d = d[k]
    return d

def mean_across(setdict, *path):
    vals=[g(v,*path) for v in setdict.values()]
    vals=[x for x in vals if x is not None and np.isfinite(x)]
    return float(np.mean(vals)) if vals else float('nan')

def ratios(v, key):
    d=g(v,key)
    if not d: return None
    means={m:d[m]['mean'] for m in d}
    return {m:means[m]/np.mean([means[x] for x in means if x!=m]) for m in means}

print("="*80)
print("CONFRONTO COMPLETO — baseline (A) / pala 5% (B) / pala 10% (C)")
print("="*80)

for kind, label in [('accel_vib','accelerometro (m/s²)'), ('gyro_vib','giroscopio (rad/s)')]:
    print(f"\n--- VIBRAZIONE {label} ---")
    print(f"{'Volo':<18} {'mean':>8} {'p95':>8} {'max':>8}")
    for set_key in ('A','B','C'):
        for k,v in R[set_key].items():
            s=g(v,kind)
            if s: print(f"{k:<18} {s['mean']:>8.3f} {s['p95']:>8.3f} {s['max']:>8.3f}")
        if set_key in ('A','B'):
            print(f"  media {set_key:<11} "
                  f"{mean_across(R[set_key],kind,'mean'):>8.3f} "
                  f"{mean_across(R[set_key],kind,'p95'):>8.3f} "
                  f"{mean_across(R[set_key],kind,'max'):>8.3f}")

print("\n--- HOVER THRUST (0-1) ---")
for set_key in ('A','B','C'):
    for k,v in R[set_key].items():
        s=g(v,'hover_thrust')
        if s: print(f"{k:<18} mean={s['mean']:.4f}  std={s['std']:.4f}")

print("\n--- IMBALANCED PROP METRIC ---")
print(f"{'Volo':<18} {'mean':>9} {'p95':>9} {'max':>9}")
for set_key in ('A','B','C'):
    for k,v in R[set_key].items():
        s=g(v,'imbalanced_prop')
        if s: print(f"{k:<18} {s['mean']:>9.4f} {s['p95']:>9.4f} {s['max']:>9.4f}")
    if set_key in ('A','B'):
        print(f"  media {set_key:<11} "
              f"{mean_across(R[set_key],'imbalanced_prop','mean'):>9.4f} "
              f"{mean_across(R[set_key],'imbalanced_prop','p95'):>9.4f} "
              f"{mean_across(R[set_key],'imbalanced_prop','max'):>9.4f}")

for key, title in [('motor_cmd','BIAS COMANDO MOTORE'), ('rpm','BIAS RPM')]:
    print(f"\n--- {title} (motore/media altri 5) ---")
    print(f"{'Volo':<18} {'M1':>7} {'M2':>7} {'M3':>7} {'M4':>7} {'M5':>7} {'M6':>7}")
    for set_key in ('A','B','C'):
        for k,v in R[set_key].items():
            r=ratios(v,key)
            if r:
                row=" ".join(f"{r[f'M{i+1}']:>7.3f}" for i in range(6))
                print(f"{k:<18} {row}")

print("\n--- |yawspeed_integ| (sforzo controllore yaw) ---")
print(f"{'Volo':<18} {'mean':>9} {'p95':>9} {'max':>9}")
for set_key in ('A','B','C'):
    for k,v in R[set_key].items():
        s=g(v,'rate_pid_integ','yawspeed_integ')
        if s: print(f"{k:<18} {s['mean']:>9.4f} {s['p95']:>9.4f} {s['max']:>9.4f}")
    if set_key in ('A','B'):
        print(f"  media {set_key:<11} "
              f"{mean_across(R[set_key],'rate_pid_integ','yawspeed_integ','mean'):>9.4f} "
              f"{mean_across(R[set_key],'rate_pid_integ','yawspeed_integ','p95'):>9.4f} "
              f"{mean_across(R[set_key],'rate_pid_integ','yawspeed_integ','max'):>9.4f}")

print("\n" + "="*80)
print("FOCUS M1: progressione sana → 5 % → 10 %")
print("="*80)
print("\nMetrica                | baseline (media A) |  5% su M1 (B.1)  | 10% su M1 (C.1)")
def fmt(x): return f"{x:>8.4f}" if x is not None else "    n/a"
metrics = [
    ('accel_vib mean',     ('accel_vib','mean')),
    ('accel_vib p95',      ('accel_vib','p95')),
    ('accel_vib max',      ('accel_vib','max')),
    ('gyro_vib mean',      ('gyro_vib','mean')),
    ('gyro_vib p95',       ('gyro_vib','p95')),
    ('gyro_vib max',       ('gyro_vib','max')),
    ('hover_thrust mean',  ('hover_thrust','mean')),
    ('imbalanced_prop p95',('imbalanced_prop','p95')),
    ('|yaw_integ| p95',    ('rate_pid_integ','yawspeed_integ','p95')),
    ('|yaw_integ| max',    ('rate_pid_integ','yawspeed_integ','max')),
]
for name, path in metrics:
    a=mean_across(R['A'], *path)
    b=g(R['B']['B.1 M1'], *path)
    c=g(R['C']['C.1 M1'], *path)
    print(f"{name:<22} | {fmt(a)}          | {fmt(b)}        | {fmt(c)}")

print("\nRapporto motore M1 vs altri 5 (cmd e RPM):")
rA=[ratios(v,'motor_cmd')['M1'] for v in R['A'].values()]
rB=ratios(R['B']['B.1 M1'],'motor_cmd')['M1']
rC=ratios(R['C']['C.1 M1'],'motor_cmd')['M1']
print(f"  cmd M1 baseline (media A) = {np.mean(rA):.4f}   B.1 (5%) = {rB:.4f}   C.1 (10%) = {rC:.4f}")

rA=[ratios(v,'rpm')['M1'] for v in R['A'].values()]
rB=ratios(R['B']['B.1 M1'],'rpm')['M1']
rC=ratios(R['C']['C.1 M1'],'rpm')['M1']
print(f"  RPM M1 baseline (media A) = {np.mean(rA):.4f}   B.1 (5%) = {rB:.4f}   C.1 (10%) = {rC:.4f}")
