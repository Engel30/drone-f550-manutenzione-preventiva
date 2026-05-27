# Effetto pala danneggiata 5 % — Set A vs Set B

Confronto fra i 6 voli baseline (Set A, pale tutte sane) e i 6 voli con una
pala accorciata del 5 % montata a turno su ciascun motore M1…M6 (Set B).

Metodologia, layout motori e definizione delle metriche in
[`panoramica.md`](panoramica.md). Mappa file ↔ prova in
[`log/2026-05-27/README.md`](../log/2026-05-27/README.md).

---

## 1. Vibrazione

| Metrica | Set A (media) | Set B (media) | Δ |
|---|---:|---:|---:|
| accel `mean` (m/s²) | 2.14 | 2.14 | ≈ 0 |
| accel `p95` | 3.02 | 3.31 | **+9.5 %** |
| accel `max` | 3.45 | 4.03 | **+16.8 %** |
| gyro `mean` (rad/s) | 0.255 | 0.232 | −9 % |
| gyro `p95` | 0.351 | 0.352 | ≈ 0 |
| gyro `max` | 0.387 | 0.442 | **+14.2 %** |

→ **Le medie sono indistinguibili dal baseline**: il danno del 5 % è ai limiti
della sensibilità delle metriche aggregate. Il segnale vive solo nei **picchi**
(p95 e max), che crescono in modo sistematico ma modesto (+10–17 %).

### Vibrazione per singolo volo

| Volo | Motore con 5% | accel max (m/s²) | gyro max (rad/s) |
|---|---|---:|---:|
| B.1 | M1 | 4.14 | 0.45 |
| **B.2** | **M2** | **4.41** | **0.57** |
| B.3 | M3 | 3.81 | 0.45 |
| B.4 | M4 | 4.02 | 0.47 |
| B.5 | M5 | 4.33 | 0.37 |
| B.6 | M6 | 3.49 | 0.34 |

**B.2 (M2) è l'outlier** di tutta la sessione: vibrazione massima sia accel sia
gyro. Da replicare per capire se è ripetibile o artefatto di montaggio.

## 2. Imbalanced prop metric

| | Set A | Set B |
|---|---:|---:|
| mean | −0.53 | **−0.72** |
| p95  | −0.063 | **−0.134** |

→ La metrica è **sistematicamente più negativa** col danno (≈ ×2 sul p95).
Nessun volo ha mai superato la soglia interna PX4 di failure, ma il segnale è
chiaro e ben separato.

## 3. Hover thrust

Il Set A mostra una crescita monotona 0.513 → 0.549 nei 6 voli, **dovuta solo
alla scarica batteria** (a parità di peso, tensione minore ⇒ PWM più alto).
Il Set B varia 0.48–0.54 senza pattern interpretabile come "danno": è coerente
con `hover_thrust ≈ f(V_batt)`.

→ `hover_thrust` **non è un indicatore di danno utilizzabile** senza
normalizzazione con `battery_status.voltage_v`.

## 4. Bias di comando motore

Riferimento (media Set A): pattern strutturale del drone, M3/M6 sotto-comandati,
M4/M5 sopra-comandati. Vedi [`panoramica.md`](panoramica.md) §"Bias strutturale".

Set B — rapporto del motore *con pala 5 %* e variazione rispetto al baseline
dello stesso motore:

| Volo | Motore | rapporto cmd | Δ vs baseline | rapporto RPM | Δ vs baseline RPM |
|---|---|---:|---:|---:|---:|
| B.1 | M1 | 0.995 | **+0.022** | 1.008 | **+0.030** |
| B.2 | M2 | 1.068 | **+0.043** | 1.047 | +0.020 |
| B.3 | M3 | 0.992 | **+0.056** | 1.021 | **+0.055** |
| B.4 | M4 | 1.051 | −0.015 | 1.025 | −0.012 |
| B.5 | M5 | 1.036 | −0.016 | 1.016 | −0.014 |
| B.6 | M6 | 0.966 | **+0.016** | 0.993 | **+0.029** |

→ Su **4 motori su 6** (M1, M2, M3, M6) il motore con pala accorciata aumenta
sia comando che RPM rispetto al baseline (+1.6 % … +5.6 %): è il mixer che
compensa la minor spinta della pala più corta.

Su **M4 e M5** la firma è invertita o nulla. Due ipotesi non escludibili dai
dati:

1. M4/M5 erano già sopra-comandati di partenza (bias strutturale); i +5 % di
   danno cadono dentro la variabilità inter-volo.
2. Il bias baseline misurato col motore "sano" potrebbe non coincidere col bias
   misurato col motore "danneggiato" — la pala 5 % sostituisce una pala
   specifica che andava su quel motore di default.

## 5. Sforzo controllore yaw

| | Set A | Set B |
|---|---:|---:|
| `|yaw_integ|` mean | 0.0205 | 0.0176 |
| `|yaw_integ|` p95  | 0.0427 | 0.0534 |
| `|yaw_integ|` max  | 0.0568 | 0.0645 |

→ Mediamente simile, picchi leggermente più alti. **Outlier severo**: B.2 (5 %
su M2) con `|yaw_integ|` max = **0.156**, circa **3× il baseline**. Coerente con
B.2 outlier anche su vibrazione.

---

## Conclusioni del Set B

1. **Il 5 % è al limite della rilevabilità**: medie indistinguibili, segnale
   solo nei picchi e in `imbalanced_prop`.
2. La firma di compensazione del mixer è chiara su 4 motori su 6, ma è
   **mascherata dal bias strutturale** del drone su M4/M5.
3. **B.2 (5 % su M2) è un outlier diffuso** (vibrazione + yaw integrator): da
   replicare prima di trarre conclusioni sull'asimmetria del danno fra motori.
4. **`hover_thrust` non è utilizzabile** come indicatore di danno per volo
   singolo.

Per il quadro complessivo e la progressione vs danno 10 %, vedi
[`panoramica.md`](panoramica.md).
