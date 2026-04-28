# Documentazione dei dati di log PX4 — ULG

**Formato:** ULog (`.ulg`) — formato binario nativo PX4  
**Log di riferimento:** `log/2026-04-28/10_28_38.ulg` (file più grande, ~166 MB, ~4 minuti di volo)  
**Libreria Python per la lettura:** `pyulog`

---

## Come leggere un file ULG in Python

```python
from pyulog import ULog

ulog = ULog("percorso/al/file.ulg")

# Elenco di tutti i topic disponibili
for d in ulog.data_list:
    print(d.name, list(d.data.keys()))

# Accedere a un topic specifico
topic = next(d for d in ulog.data_list if d.name == 'battery_status')
tempo_s = topic.data['timestamp'] / 1e6  # microsecondi → secondi
tensione = topic.data['voltage_v']
```

> Nota: alcuni topic hanno istanze multiple (es. 3 IMU). Si distinguono per indice nell'elenco `ulog.data_list`.

---

## Topic disponibili per categoria

---

### 1. Batteria

| Topic | Frequenza | Campioni |
|-------|-----------|---------|
| `battery_status` | ~5 Hz | 1229 |

**Campi principali:**

| Campo | Unità | Descrizione |
|-------|-------|-------------|
| `voltage_v` | V | Tensione totale del pacco |
| `current_a` | A | Corrente istantanea assorbita |
| `current_average_a` | A | Corrente media |
| `discharged_mah` | mAh | Capacità scaricata dall'armo |
| `remaining` | 0–1 | Stima SoC (State of Charge) |
| `time_remaining_s` | s | Stima tempo rimanente |
| `temperature` | °C | Temperatura batteria |
| `voltage_cell_v[0..N]` | V | Tensione per singola cella (se BMS smart) |
| `max_cell_voltage_delta` | V | Delta massimo tra celle |
| `internal_resistance_estimate` | Ω | Resistenza interna stimata |
| `state_of_health` | % | Stato di salute (cicli/degradazione) |
| `cycle_count` | — | Numero cicli di carica |
| `warning` | enum | Livello di allerta (0=ok, 1=low, 2=critical) |

**Utilità per manutenzione preventiva:**
- Monitorare la degradazione della batteria nel tempo (SoH, resistenza interna)
- Identificare sbilanciamento celle (`max_cell_voltage_delta`)
- Calcolare il consumo per volo
- Rilevare anomalie di corrente in hover

---

### 2. Motori / ESC

| Topic | Frequenza | Campioni |
|-------|-----------|---------|
| `actuator_motors` | ~889 Hz | 218772 |
| `esc_status` | ~71.5 Hz | 17601 |

**`actuator_motors` — campi principali:**

| Campo | Unità | Descrizione |
|-------|-------|-------------|
| `control[0..5]` | −1…+1 | Segnale di comando normalizzato ai 6 motori |

**`esc_status` — campi per ogni ESC (`esc[0]..esc[5]`):**

| Campo | Unità | Descrizione |
|-------|-------|-------------|
| `esc[i].esc_rpm` | RPM | Velocità di rotazione misurata |
| `esc[i].esc_voltage` | V | Tensione al motore |
| `esc[i].esc_current` | A | Corrente del motore |
| `esc[i].esc_temperature` | °C | Temperatura ESC |
| `esc[i].esc_power` | W | Potenza istantanea |
| `esc[i].esc_errorcount` | — | Contatore errori cumulativi |
| `esc[i].failures` | bitmask | Failure flags |
| `esc[i].esc_state` | enum | Stato operativo ESC |

**Utilità per manutenzione preventiva:**
- Confrontare RPM tra i 6 motori per rilevare squilibri
- Monitorare temperatura ESC (surriscaldamento)
- Corrente per motore: identificare motori che assorbono anomalamente
- `esc_errorcount`: tendenza crescente indica problemi

---

### 3. IMU — Accelerometro e Giroscopio

| Topic | Frequenza | Istanze | Campioni |
|-------|-----------|---------|---------|
| `sensor_combined` | ~144 Hz | 1 | 35377 |
| `sensor_accel` | ~10 Hz | 3 (IMU 0/1/2) | 2455 ciascuna |
| `sensor_gyro` | ~10 Hz | 3 (IMU 0/1/2) | 2455 ciascuna |
| `sensor_accel_fifo` | ~957 Hz | 1 | 235328 |
| `sensor_gyro_fifo` | ~983 Hz | 1 | 241901 |
| `vehicle_imu_status` | ~1 Hz | 3 | 246 ciascuna |
| `sensors_status_imu` | ~5 Hz | 1 | 1229 |

**`sensor_combined` — campi principali:**

| Campo | Unità | Descrizione |
|-------|-------|-------------|
| `gyro_rad[0/1/2]` | rad/s | Velocità angolare (roll/pitch/yaw) |
| `accelerometer_m_s2[0/1/2]` | m/s² | Accelerazione lineare (X/Y/Z) |
| `accelerometer_clipping` | bitmask | Saturazione accelerometro |
| `gyro_clipping` | bitmask | Saturazione giroscopio |

**`vehicle_imu_status` — campi principali:**

| Campo | Unità | Descrizione |
|-------|-------|-------------|
| `accel_vibration_metric` | m/s² | Metrica vibrazione accelerometro |
| `gyro_vibration_metric` | rad/s | Metrica vibrazione giroscopio |
| `accel_clipping[0/1/2]` | count | Saturazioni per asse |
| `temperature_accel` / `temperature_gyro` | °C | Temperature sensori |
| `accel_error_count` / `gyro_error_count` | — | Errori cumulativi |

**`sensors_status_imu` — campi principali:**

| Campo | Unità | Descrizione |
|-------|-------|-------------|
| `accel_inconsistency_m_s_s[0..2]` | m/s² | Discrepanza tra i 3 accelerometri |
| `gyro_inconsistency_rad_s[0..2]` | rad/s | Discrepanza tra i 3 giroscopi |
| `accel_healthy[0..2]` | bool | Stato salute accelerometri |
| `gyro_healthy[0..2]` | bool | Stato salute giroscopi |

**Utilità per manutenzione preventiva:**
- `accel_vibration_metric`: livello di vibrazione del drone (elica danneggiata → vibrazione alta)
- Inconsistenza tra le 3 IMU: rileva guasti sensoriali
- Clipping: segnala vibrazioni eccessive o impatti

---

### 4. Barometro

| Topic | Frequenza | Istanze | Campioni |
|-------|-----------|---------|---------|
| `sensor_baro` | ~10 Hz | 2 | 2455 ciascuna |
| `vehicle_air_data` | ~5 Hz | 1 | 1228 |

**Campi principali:**

| Campo | Unità | Descrizione |
|-------|-------|-------------|
| `pressure` | Pa | Pressione atmosferica grezza |
| `temperature` | °C | Temperatura barometro |
| `baro_alt_meter` | m | Quota barometrica stimata |
| `ambient_temperature` | °C | Temperatura ambiente stimata |

**Utilità:** Verifica coerenza quota tra i 2 barometri ridondanti; deriva termica del sensore.

---

### 5. Magnetometro

| Topic | Frequenza | Istanze | Campioni |
|-------|-----------|---------|---------|
| `sensor_mag` | ~10 Hz | 2 | 2455 ciascuna |
| `vehicle_magnetometer` | ~2 Hz | 1 | 490 |

**Campi principali:**

| Campo | Unità | Descrizione |
|-------|-------|-------------|
| `x`, `y`, `z` | Gauss | Campo magnetico per asse |
| `magnetometer_ga[0/1/2]` | Gauss | Lettura vettoriale calibrata |
| `temperature` | °C | Temperatura sensore |

**Utilità:** Interferenze EMI, verifica calibrazione, consistenza tra i 2 magnetometri.

---

### 6. GPS

| Topic | Frequenza | Campioni |
|-------|-----------|---------|
| `sensor_gps` | ~0.9 Hz | 227 |
| `vehicle_gps_position` | ~4.5 Hz | 1117 |
| `vehicle_global_position` | ~5 Hz | 1229 |

**Campi principali:**

| Campo | Unità | Descrizione |
|-------|-------|-------------|
| `latitude_deg` / `longitude_deg` | °deg | Posizione geografica |
| `altitude_msl_m` | m | Quota sul livello del mare |
| `s_variance_m_s` | m/s | Varianza velocità |
| `eph` | m | Precisione orizzontale (EPH) |
| `epv` | m | Precisione verticale (EPV) |
| `satellites_used` | — | Satelliti agganciati |
| `fix_type` | enum | Tipo di fix (0=no fix, 3=3D, 4=DGPS) |
| `hdop` / `vdop` | — | Dilution of precision |

**Utilità:** Traccia traiettoria volo; valuta qualità fix GPS; rileva anomalie posizionamento.

---

### 7. Attitude (Orientamento)

| Topic | Frequenza | Campioni |
|-------|-----------|---------|
| `vehicle_attitude` | ~144 Hz | 35375 |
| `vehicle_rates_setpoint` | ~144 Hz | 35375 |
| `vehicle_attitude_setpoint` | ~143 Hz | 35110 |

**Campi principali:**

| Campo | Unità | Descrizione |
|-------|-------|-------------|
| `q[0..3]` | quaternione | Orientamento stimato (roll/pitch/yaw) |
| `roll` / `pitch` / `yaw` | rad/s | Velocità angolari setpoint |
| `thrust_body[2]` | −1…0 | Setpoint spinta verticale |

**Utilità:** Analisi risposta del controllore, inseguimento setpoint, oscillazioni anomale.

---

### 8. Posizione locale e setpoint

| Topic | Frequenza | Campioni |
|-------|-----------|---------|
| `vehicle_local_position` | ~10 Hz | 2455 |
| `vehicle_local_position_setpoint` | ~2.3 Hz | 511 |
| `trajectory_setpoint` | ~1.2 Hz | 258 |

**Campi principali:**

| Campo | Unità | Descrizione |
|-------|-------|-------------|
| `x`, `y`, `z` | m | Posizione locale (NED frame) |
| `vx`, `vy`, `vz` | m/s | Velocità locale |
| `ax`, `ay`, `az` | m/s² | Accelerazione locale |
| `heading` | rad | Direzione di volo |

---

### 9. Controllo — Rate controller

| Topic | Frequenza | Campioni |
|-------|-----------|---------|
| `rate_ctrl_status` | ~49.8 Hz | 12257 |
| `vehicle_thrust_setpoint` | ~889 Hz | 218673 |
| `vehicle_torque_setpoint` | ~889 Hz | 218621 |

**`rate_ctrl_status` — campi:**

| Campo | Unità | Descrizione |
|-------|-------|-------------|
| `rollspeed_integ` | — | Integrale PID roll |
| `pitchspeed_integ` | — | Integrale PID pitch |
| `yawspeed_integ` | — | Integrale PID yaw |

**Utilità:** Saturazione dell'integratore → oscillazioni o tuning PID non ottimale.

---

### 10. Stima hover thrust

| Topic | Frequenza | Campioni |
|-------|-----------|---------|
| `hover_thrust_estimate` | ~10 Hz | 2372 |

| Campo | Unità | Descrizione |
|-------|-------|-------------|
| `hover_thrust` | 0–1 | Spinta normalizzata per mantenere il hover |
| `hover_thrust_var` | — | Varianza della stima |
| `accel_innov` | m/s² | Innovazione accelerometro |

**Utilità per manutenzione:** Variazioni nel tempo dell'hover thrust indicano cambio di peso o degradazione motori/eliche.

---

### 11. EKF2 — Stato filtro di Kalman

| Topic | Frequenza | Istanze | Campioni |
|-------|-----------|---------|---------|
| `estimator_status` | ~5 Hz | 3 | ~1229 ciascuna |
| `estimator_innovations` | ~2 Hz | 3 | 490 ciascuna |
| `estimator_sensor_bias` | ~1 Hz | 3 | 246 ciascuna |
| `estimator_baro_bias` | ~1.8 Hz | 3 | ~449 ciascuna |

**Campi principali `estimator_status`:**

| Campo | Unità | Descrizione |
|-------|-------|-------------|
| `pos_horiz_accuracy` | m | Accuratezza posizione orizzontale |
| `pos_vert_accuracy` | m | Accuratezza posizione verticale |
| `filter_fault_flags` | bitmask | Fault dell'EKF |
| `output_tracking_error[0..2]` | — | Errore tracking angolare/velocità/posizione |

**Utilità:** Qualità della stima di stato; fault dell'EKF indicano problemi sensoriali.

---

### 12. Rilevamento guasti

| Topic | Frequenza | Campioni |
|-------|-----------|---------|
| `failure_detector_status` | ~2 Hz | 494 |

| Campo | Unità | Descrizione |
|-------|-------|-------------|
| `imbalanced_prop_metric` | — | Metrica sbilanciamento elica |
| `motor_failure_mask` | bitmask | Motori in failure |
| `fd_roll` / `fd_pitch` | bool | Failure rilevato su roll/pitch |
| `fd_battery` | bool | Failure batteria |
| `fd_imbalanced_prop` | bool | Elica sbilanciata rilevata |
| `fd_motor` | bool | Motore in failure rilevato |

**Utilità per manutenzione:** Diretto — segnala eliche sbilanciate o motori con problemi.

---

### 13. Radio / Telecomando

| Topic | Frequenza | Campioni |
|-------|-----------|---------|
| `input_rc` | ~2 Hz | 490 |
| `radio_status` | ~1 Hz | 243 |
| `manual_control_setpoint` | ~42.8 Hz | 10531 |

| Campo | Unità | Descrizione |
|-------|-------|-------------|
| `rssi` | 0–255 | Qualità segnale RC |
| `rc_lost_frame_count` | — | Frame persi cumulativi |
| `rssi` (radio_status) | 0–255 | RSSI telemetria |
| `rxerrors` | — | Errori ricezione telemetria |
| `roll`, `pitch`, `yaw`, `throttle` | −1…+1 | Input pilota normalizzati |

---

### 14. Sistema — CPU e alimentazione

| Topic | Frequenza | Campioni |
|-------|-----------|---------|
| `cpuload` | ~2 Hz | 490 |
| `system_power` | ~2 Hz | 490 |

| Campo | Unità | Descrizione |
|-------|-------|-------------|
| `load` | 0–1 | Carico CPU Pixhawk |
| `ram_usage` | 0–1 | Utilizzo RAM |
| `voltage5v_v` | V | Bus 5V (alimentazione avionici) |
| `sensors3v3[0..3]` | V | Bus 3.3V sensori |

---

### 15. Stato generale drone

| Topic | Frequenza | Campioni |
|-------|-----------|---------|
| `vehicle_status` | ~2 Hz | 494 |
| `vehicle_land_detected` | ~1 Hz | 248 |
| `actuator_armed` | ~2 Hz | 495 |
| `vehicle_control_mode` | ~2 Hz | 494 |

| Campo | Unità | Descrizione |
|-------|-------|-------------|
| `arming_state` | enum | Stato armo (disarmed/armed) |
| `nav_state` | enum | Modalità volo attiva (Manual/Stabilized/Altctl/Posctl…) |
| `armed_time` | µs | Timestamp armo |
| `takeoff_time` | µs | Timestamp decollo |
| `landed` | bool | Rilevamento atterraggio |
| `failure_detector_status` | bitmask | Failure attivi |

---

## Riepilogo per priorità di manutenzione preventiva

| Priorità | Topic | Cosa cercare |
|----------|-------|-------------|
| **Alta** | `failure_detector_status` | `imbalanced_prop_metric`, `fd_motor` |
| **Alta** | `esc_status` | RPM squilibrati, temperatura alta, errorcount |
| **Alta** | `battery_status` | SoH, resistenza interna, delta celle |
| **Alta** | `vehicle_imu_status` | `accel_vibration_metric` elevata |
| **Media** | `hover_thrust_estimate` | Deriva del valore nel tempo tra voli |
| **Media** | `sensors_status_imu` | Inconsistenza tra IMU |
| **Media** | `estimator_status` | `filter_fault_flags` ≠ 0 |
| **Bassa** | `cpuload` | `load` > 0.8 prolungato |
| **Bassa** | `radio_status` | `rxerrors` crescenti |

---

## Note tecniche

- **Timestamp:** tutti i topic usano microsecondi (`µs`). Dividere per `1e6` per avere secondi.
- **Topic multipli con lo stesso nome:** corrispondono a istanze hardware diverse (es. 3 IMU del Pixhawk 6X). Si accede per indice nella lista `ulog.data_list`.
- **FIFO data** (`sensor_accel_fifo`, `sensor_gyro_fifo`): contengono burst di campioni per campione loggato — utili per analisi FFT delle vibrazioni ad alta risoluzione.
- **NaN nei campi:** valori non disponibili sono marcati `NaN` in numpy; filtrare con `np.isnan()` prima di plottare.
