# Log di volo — sessione 4 giugno 2026

Questa cartella raccoglie i 27 log `.ulg` registrati il 4 giugno 2026 con
l'esacottero F550 (Pixhawk 6X, firmware PX4). Le tabelle che seguono riportano
per ciascun volo il tipo, la durata, l'esito e una nota; in fondo è riportato
l'elenco dei topic registrati con le relative frequenze.

## Note pratiche

- **Orari**: il timestamp nel nome del file è l'ora locale del Pixhawk, **2 ore
  indietro** rispetto all'ora reale → `ora reale ≈ nome file + 2 h`
  (es. `13_15_11.ulg` ≈ 15:15). In caso di dubbio fa fede l'ora UTC del GPS nel log.
- **Sito di decollo**: lat 43.6008° N, lon 13.4821° E (Ancona).
- **Come aprire i `.ulg`**: PX4 Flight Review (<https://review.px4.io>),
  QGroundControl, PlotJuggler, oppure `pyulog` (`ulog_info file.ulg`).
- Tutti i log contengono anche il **dump raw del GPS** (`gps_dump`).

---

## I voli

La giornata comprende tre tipi di prova. Le tabelle sono in ordine temporale.
Durata = tempo armato (motori attivi).

### 1 · Test e controlli a terra

Armamenti brevi senza decollo effettivo (verifiche e decolli abortiti).

| File | ≈ ora | Durata | Nota |
|---|---|---:|---|
| `11_50_58` | 13:51 | 11 s | Check a terra dopo accensione |
| `11_51_42` | 13:52 | 11 s | Test motori al minimo |
| `13_13_29` | 15:13 | 11 s | Decollo non avvenuto |
| `14_38_41` | 16:38 | 11 s | Decollo abortito (auto-disarm pre-volo) |

### 2 · Voli in hovering (Stabilize)

Hover di circa 1 minuto in *Stabilize*. I primi due voli servono da riferimento
con pale sane; nei successivi è montata una pala accorciata del 10 %, a turno su
un motore, per osservarne l'effetto. Sono questi i voli usati per l'analisi delle
pale.

| File | ≈ ora | Durata | Configurazione | Nota |
|---|---|---:|---|---|
| `11_52_13` | 13:52 | 146 s | pale sane | baseline |
| `11_54_05` | 14:09 | 69 s | pale sane | baseline |
| `12_21_42` | 14:21 | 83 s | pala 10 % su **M3** | |
| `12_28_29` | 14:28 | 104 s | pala 10 % su **M6** | |
| `12_39_37` | 14:39 | 84 s | pala 10 % su **M2** | |
| `12_43_47` | 14:43 | 82 s | pala 10 % su **M4** | |
| `12_46_09` | 14:46 | 99 s | pala 10 % su **M5** | |

### 3 · Voli con traiettoria (position, missioni, quadrati)

Tutti a **pale sane**: brevi hop in *Position*, un volo lungo, missioni
automatiche (waypoint + rientro) e traiettorie quadrate.

| File | ≈ ora | Durata | Tipo | Nota |
|---|---|---:|---|---|
| `12_58_57` | 14:59 | 15 s | hop in position | |
| `12_59_16` | 14:59 | 10 s | hop in position | |
| `13_14_52` | 15:15 | 14 s | hop in position | |
| `13_15_11` | 15:15 | 398 s | volo lungo in position | volo più lungo della giornata |
| `13_34_40` | 15:34 | 182 s | missione automatica | |
| `14_06_22` | 16:06 | 21 s | quadrato | |
| `14_07_19` | 16:07 | 76 s | quadrato | atterraggio anticipato |
| `14_13_15` | 16:13 | 124 s | quadrato | |
| `14_30_03` | 16:30 | 110 s | quadrato + rientro | |
| `14_39_06` | 16:39 | 113 s | quadrato + rientro | |
| `14_42_14` | 16:42 | 96 s | quadrato | atterraggio anticipato |
| `14_47_52` | 16:47 | 49 s | missione/quadrato | |
| `14_48_51` | 16:48 | 30 s | hop breve | |
| `14_58_44` | 16:58 | 118 s | missione automatica | |
| `15_01_55` | 17:02 | 124 s | missione automatica | |
| `15_08_55` | 17:09 | 105 s | missione automatica | |

> In alcuni voli del pomeriggio si presentano due comportamenti, che abbiamo
> verificato e che non influiscono sull'analisi delle pale: in modalità RTK il GPS
> può perdere il fix per qualche secondo (sono i casi degli atterraggi anticipati),
> e in un paio di discese compare una segnalazione *motor failure* che si è
> rivelata un falso positivo, dato che i motori rispondevano correttamente.

---

## Topic registrati e frequenze

Tutti i log condividono la stessa configurazione, quindi i topic e le frequenze
sono praticamente identici tra i file (valori qui dal volo lungo `13_15_11`).

> Alcuni topic compaiono in più copie perché i relativi sensori sono ridondanti
> (il Pixhawk ha 3 IMU e più magnetometri): è normale, vengono votati a bordo.
> In tutto ~80 topic; l'elenco esatto di un file si ottiene con `ulog_info`.

**Vibrazioni e dinamica ad alta frequenza** *(utili per l'effetto pala)*

| Topic | Hz | Contenuto |
|---|---:|---|
| `sensor_accel_fifo` | ~1000 | accelerometro ad alta frequenza |
| `sensor_gyro_fifo` | ~1000 | giroscopio ad alta frequenza |
| `vehicle_angular_velocity` | ~1000 | velocità angolare |
| `sensor_combined` | ~200 | IMU combinata (accel + gyro) |
| `vehicle_acceleration` | ~200 | accelerazione lineare |

**Propulsione / motori**

| Topic | Hz | Contenuto |
|---|---:|---|
| `esc_status` | ~60 | RPM, corrente, tensione, temperatura per motore |
| `actuator_motors` | ~1000 | comando ai 6 motori |
| `actuator_outputs` | ~10 | uscite PWM |
| `control_allocator_status` | ~5 | ripartizione spinta/coppia ai motori |
| `vehicle_thrust_setpoint` / `vehicle_torque_setpoint` | ~1000 | spinta e coppia richieste |

**Assetto e controllo**

| Topic | Hz | Contenuto |
|---|---:|---|
| `vehicle_attitude` | ~120 | assetto stimato |
| `vehicle_attitude_setpoint` | ~100 | assetto desiderato |
| `vehicle_rates_setpoint` | ~120 | rateo angolare desiderato |
| `rate_ctrl_status` | ~50 | stato anelli di controllo |
| `vehicle_local_position` | ~10 | posizione/velocità locale |
| `trajectory_setpoint` | ~5 | setpoint di traiettoria |

**Sensori (IMU / mag / baro)**

| Topic | Hz | Contenuto |
|---|---:|---|
| `sensor_accel` / `sensor_gyro` | ~10 | accelerometro / giroscopio per sensore |
| `sensor_mag` | ~10 | magnetometro |
| `sensor_baro` | ~11 | barometro |
| `vehicle_imu` | ~2 | IMU integrata |
| `vehicle_air_data` | ~6 | quota barometrica |

**Navigazione e GPS**

| Topic | Hz | Contenuto |
|---|---:|---|
| `vehicle_global_position` | ~5 | posizione globale fusa |
| `sensor_gps` / `vehicle_gps_position` | ~1–5 | soluzione GPS (fix, satelliti, precisione) |
| `gps_dump` | ~12 | dump raw del ricevitore u-blox |
| `estimator_status` | ~5 | stato del filtro di navigazione (EKF) |

**Alimentazione**

| Topic | Hz | Contenuto |
|---|---:|---|
| `battery_status` | ~5 | tensione, corrente, carica residua |
| `system_power` | ~2 | tensioni di alimentazione interne |

**Comando RC e stato veicolo**

| Topic | Hz | Contenuto |
|---|---:|---|
| `manual_control_setpoint` | ~45 | comandi stick del pilota |
| `input_rc` | ~2 | canali RC |
| `vehicle_status` | ~2 | stato armamento e modalità di volo |
| `vehicle_land_detected` | ~1 | rilevamento atterraggio |
| `failsafe_flags` | ~2 | stato dei failsafe |

---

## Riepilogo dei topic per tipo di analisi

| Per analizzare… | Topic principali |
|---|---|
| vibrazioni / effetto pala | `sensor_accel_fifo`, `sensor_gyro_fifo`, `vehicle_angular_velocity` |
| sbilanciamento motori | `esc_status`, `actuator_motors`, `control_allocator_status` |
| stabilità di assetto | `vehicle_attitude` vs `vehicle_attitude_setpoint`, `rate_ctrl_status` |
| batteria | `battery_status`, `system_power` |
| GPS | `sensor_gps`, `vehicle_gps_position`, `gps_dump` |
| modalità ed eventi di volo | `vehicle_status`, `failsafe_flags`, `vehicle_land_detected` |
