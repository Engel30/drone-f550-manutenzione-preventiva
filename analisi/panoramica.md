# Effetto del danneggiamento delle pale — panoramica

Vista d'insieme degli studi sull'effetto del danneggiamento delle pale sul
comportamento dell'esacottero F550. Questo documento contiene:

- la **metodologia** di estrazione delle metriche dai `.ulg`,
- il **confronto trasversale** fra tutti i livelli di danno provati,
- la **progressione 0 → 5 % → 10 %** su M1 (l'unica oggi completa).

I dettagli per ciascun livello di danno stanno nei file dedicati:

- [`pala-5pct.md`](pala-5pct.md) — Set A (baseline) vs Set B (pala 5 % su M1…M6)
- [`pala-10pct.md`](pala-10pct.md) — Set A vs Set C (pala 10 %; oggi solo M1)

Dati grezzi: [`dati/risultati.json`](dati/risultati.json) — tabelle leggibili:
[`dati/tabelle.txt`](dati/tabelle.txt).

---

## Metodologia (valida per tutti i set)

### Dataset

| Set | Configurazione | N. voli disponibili |
|---|---|---:|
| **A** | Hover, pale tutte sane (swap di posizione fra coppie) | 6 / 6 |
| **B** | Hover, pala accorciata **5 %** a turno su M1…M6 | 6 / 6 |
| **C** | Hover, pala accorciata **10 %** a turno su M1…M6 | 1 / 6 |

Tutti i voli in modalità **Stabilize**, ~1 min armato, hover stazionario. Mappa
file ↔ prova in [`log/2026-05-27/README.md`](../log/2026-05-27/README.md) e
[`piano-voli.md`](../piano-voli.md).

### Metriche estratte

Per ogni log, sull'intervallo armato più lungo:

| Metrica | Topic PX4 | Cosa misura |
|---|---|---|
| `accel_vib` | `vehicle_imu_status.accel_vibration_metric` | Vibrazione accelerometro (m/s²), media sulle 3 IMU |
| `gyro_vib`  | `vehicle_imu_status.gyro_vibration_metric`  | Vibrazione giroscopio (rad/s) |
| `hover_thrust` | `hover_thrust_estimate.hover_thrust` | Spinta normalizzata (0–1) per mantenere quota |
| `imbalanced_prop` | `failure_detector_status.imbalanced_prop_metric` | Metrica interna PX4 di squilibrio elica |
| RPM, corrente | `esc_status.esc[i].esc_rpm`, `.esc_current` | Per ogni motore |
| comando motore | `actuator_motors.control[i]` | Comando normalizzato −1…+1 |
| `|yaw_integ|` | `rate_ctrl_status.yawspeed_integ` (valore assoluto) | Sforzo dell'integratore PID yaw |

Per le metriche scalari riportiamo `mean`, `p95` e `max` calcolati sui campioni
nell'intervallo armato. Per le metriche per-motore (RPM, comando) usiamo il
**rapporto** fra il valore medio del motore *i* e la media degli altri 5: valore
> 1 ⇒ quel motore lavora di più del gruppo.

### Layout motori (PX4 hexa_x, vista dall'alto)

```
       fronte
        ▲
   M2 ─── M6
  ╱         ╲
 M3          M5
  ╲         ╱
   M4 ─── M1
```

Coppie diagonalmente opposte: **M1↔M2**, **M3↔M6**, **M4↔M5**.

### Riproduzione

```bash
python3 analisi/scripts/analizza_log.py > analisi/dati/risultati.json
python3 analisi/scripts/sintesi.py     > analisi/dati/tabelle.txt
```

---

## Confronto trasversale: baseline / 5 % / 10 %

Tutte le metriche aggregate (media intra-set per A e B, valore singolo per C.1).

| Metrica | A (media) | B (media) | C.1 (10 % su M1) |
|---|---:|---:|---:|
| `accel_vib` mean (m/s²) | 2.14 | 2.14 | **3.72** |
| `accel_vib` p95 | 3.02 | 3.31 | **6.65** |
| `accel_vib` max | 3.45 | 4.03 | **7.74** |
| `gyro_vib` mean (rad/s) | 0.255 | 0.232 | **0.393** |
| `gyro_vib` p95 | 0.351 | 0.352 | **0.640** |
| `gyro_vib` max | 0.387 | 0.442 | **0.836** |
| `imbalanced_prop` p95 | −0.063 | −0.134 | **−0.358** |
| `|yaw_integ|` p95 | 0.043 | 0.053 | **0.058** |
| `hover_thrust` mean | 0.525 | 0.513 | 0.555 |

Note di lettura:

- **Le medie di vibrazione del Set B sono indistinguibili dal baseline**: il danno
  del 5 % vive solo nei picchi.
- A **danno 10 %**, tutte le metriche di vibrazione **raddoppiano abbondantemente**
  (×1.7 sui mean, ×2.2 sui max).
- `imbalanced_prop` p95 cresce ×2 col 5 %, ×6 col 10 %: ha il miglior rapporto
  segnale/rumore.
- `hover_thrust` è **dominato dalla scarica batteria** (sale 0.51 → 0.55 nei soli
  6 voli baseline): da solo non è un indicatore di danno utilizzabile.

---

## Progressione su M1: sana → 5 % → 10 %

L'unico motore su cui abbiamo tutti e tre i livelli di danno. La firma è
**monotonica e pulita** sia per il comando sia per gli RPM:

| | baseline (media A) | 5 % (B.1) | 10 % (C.1) |
|---|---:|---:|---:|
| rapporto comando M1 | 0.975 | 0.995 | **1.014** |
| rapporto RPM M1 | 0.978 | 1.009 | **1.027** |

Il mixer porta M1 dal sotto-comando strutturale (0.975) al sopra-comando (1.014)
quando deve compensare il 10 % di pala mancante. La progressione è quasi lineare
nel range testato e suggerisce che lo stesso rapporto possa essere usato come
**indicatore proxy del livello di danno** (almeno nell'intervallo 0–10 %).

---

## Bias strutturale del drone

Pattern visibile **in tutti i 6 voli baseline**, quindi indipendente dal danno:

| | M1 | M2 | M3 | M4 | M5 | M6 |
|---|---:|---:|---:|---:|---:|---:|
| rapporto cmd, media Set A | 0.975 | 1.025 | 0.936 | 1.066 | 1.052 | 0.943 |

- **M3 e M6 sono sempre sotto-comandati** (~0.94)
- **M4 e M5 sono sempre sopra-comandati** (~1.05–1.07)
- M1, M2 vicini a 1.0

Cause possibili: CoM decentrato, braccio storto, ESC squilibrato. È importante
**caratterizzare/correggere questo bias prima dei Set D–G** (quadrato 3×3 m e
traiettorie casuali), altrimenti il segnale di danno si sovrappone al bias e
diventa impossibile separare le due cose.

---

## Metriche raccomandate per la relazione finale

In ordine di rapporto segnale/rumore osservato nel range 0–10 %:

1. **`imbalanced_prop_metric` p95** — ×2 a 5 %, ×6 a 10 %, baseline pulita.
2. **`accel_vib` max** — picchi della vibrazione accel, ×2.2 a 10 %.
3. **`gyro_vib` max** — picchi della vibrazione gyro, ×2.2 a 10 %.
4. **Rapporto comando/RPM** del motore con pala danneggiata — progressione
   monotona, ottimo per stimare il *livello* di danno (non solo presenza/assenza).

`hover_thrust` e le **medie** di vibrazione sono sconsigliate come metriche
primarie perché dominate da rumore (batteria, variabilità inter-volo).

## Azioni aperte

- Completare il **Set C** sui motori M2…M6.
- **Replicare B.2** (5 % su M2): outlier su quasi tutte le metriche, capire se
  ripetibile o artefatto di montaggio.
- **Caratterizzare/correggere il bias M3/M6 vs M4/M5** prima dei Set D–G.
- **Registrare V_batt** iniziale e finale di ogni volo (manca su molti voli
  Set B); serve per normalizzare `hover_thrust`.
