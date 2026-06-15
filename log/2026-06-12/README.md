# Log di volo — sessione 12 giugno 2026

Questa cartella raccoglie i log `.ulg` registrati il 12 giugno 2026 con
l'esacottero F550 (Pixhawk 6X, firmware PX4). Le tabelle che seguono riportano
per ciascun volo l'orario, il file di log, la configurazione delle pale, la
tensione di batteria e una nota; in fondo è riportato l'elenco dei topic
registrati con le relative frequenze.

Vento durante la sessione: tra **15 e 25 km/h**.

## Note pratiche

- **Orari**: il timestamp nel nome del file è l'ora locale del Pixhawk, **2 ore
  indietro** rispetto all'ora reale → `ora reale ≈ nome file + 2 h`
  (es. `13_20_00.ulg` ≈ 15:20). In caso di dubbio fa fede l'ora UTC del GPS nel log.
- **Sito di decollo**: lat 43.6008° N, lon 13.4821° E (Ancona).
- **Come aprire i `.ulg`**: PX4 Flight Review (<https://review.px4.io>),
  QGroundControl, PlotJuggler, oppure `pyulog` (`ulog_info file.ulg`).
- Tutti i log contengono anche il **dump raw del GPS** (`gps_dump`).
- **Numerazione**: il libro di bordo salta il *Volo 9*; di seguito si segue la
  numerazione originale.
- **Log da ignorare**: dopo il Volo 17 sono presenti tre arm/disarm erronei
  (`14_47_04`, `14_47_16`, `14_47_21`) che non corrispondono a voli reali e
  vanno scartati nell'analisi.

---

## I voli

La giornata è organizzata in due blocchi: una prima parte di **voli su
traiettoria quadrata 3×3 m** con pala parzialmente accorciata a turno sui sei
motori (gli hover erano già stati eseguiti in sessioni precedenti — Set A–C il
27/05 e 04/06), e una seconda parte con payload montato (due voli liberi a pale
sane e tre voli su traiettoria quadrata con la pala accorciata sul motore 2).
Durata = tempo armato (motori attivi).

### 1 · Test e controlli a terra

Armamenti brevi senza decollo effettivo (verifiche pre-volo).

| File | ≈ ora | Durata | Nota |
|---|---|---:|---|
| `13_16_19` | 15:16 | 73 s | Verifica iniziale (hover breve di prova) |
| `13_17_58` | 15:17 | 32 s | Check a terra |
| `13_27_32` | 15:27 | 12 s | Check a terra prima del Volo 2 |
| `13_59_33` | 15:59 | 12 s | Check a terra dopo cambio batteria, prima del Volo 11 |

### 2 · Voli su traiettoria quadrata con pala accorciata (Volo 1–16)

Voli su **traiettoria quadrata 3×3 m** (~3 m di quota, con ~30 s di hovering
iniziale prima della traiettoria) di circa 2–2,5 minuti, con una pala accorciata
a turno su un singolo motore. La riduzione è del **10 %** in tutti i casi,
eccetto il **Volo 1** (pala del **5 %**). La sostituzione della batteria è
indicata in nota.

| # | ≈ ora | File | Durata | Pala accorciata | Tensione | Nota |
|---:|---|---|---:|---|---:|---|
| 1  | 15:19 | `13_20_00` | 147 s | M5, 5 %  | 15.4 V | tutto ok (quadrato 5 % su M5) |
| 2  | 15:28 | `13_27_52` | 146 s | M1, 10 % | 14.1 V | tutto ok |
| 3  | 15:33 | `13_33_16` | 148 s | M1, 10 % | 16.8 V | batteria nuova |
| 4  | 15:37 | `13_37_29` | 145 s | M3, 10 % | 15.8 V | tutto ok |
| 5  | 15:40 | `13_40_32` | 144 s | M3, 10 % | 15.4 V | tutto ok |
| 6  | 15:44 | `13_44_15` | 142 s | M6, 10 % | 15.2 V | tutto ok |
| 7  | 15:47 | `13_47_50` | 142 s | M6, 10 % | 15.1 V | tutto ok |
| 8  | 15:52 | `13_52_09` | 152 s | M2, 10 % | 14.8 V | segnalazione *motor failure* (falso positivo), volo regolare |
| 10 | 15:55 | `13_55_15` |  87 s | M2, 10 % | 13.6 V | batteria scarica, atterraggio di emergenza |
| 11 | 15:59 | `13_59_52` | 148 s | M2, 10 % | 16.8 V | batteria nuova |
| 12 | 16:03 | `14_03_52` |  77 s | M5, 10 % | 15.6 V | non si è alzato, magnetometro sbagliato |
| 13 | 16:06 | `14_06_38` | 149 s | M5, 10 % | 15.6 V | tutto ok |
| 14 | 16:09 | `14_09_45` | 157 s | M5, 10 % | 15.4 V | tutto ok |
| 15 | 16:15 | `14_15_24` | 153 s | M4, 10 % | 15.1 V | tutto ok |
| 16 | 16:18 | `14_18_32` | 150 s | M4, 10 % | 14.4 V | tutto ok |

### 3 · Voli con payload (Volo 17–21)

Test con payload montato. Prima due voli di riferimento a **pale sane**
(traiettoria **libera** del pilota), poi tre voli su **traiettoria quadrata
3×3 m** con la pala accorciata sul **motore 2**.

| # | ≈ ora | File | Durata | Configurazione | Tensione | Nota |
|---:|---|---|---:|---|---:|---|
| 17 | 16:44 | `14_44_38` | 135 s | pale sane | — | test libero |
| 18 | 16:50 | `14_50_12` | 149 s | pale sane | — | tutto ok, batteria scarica a fine volo |
| 19 | 17:29 | `15_29_08` | 145 s | M2, 10 % | 14.1 V | tutto ok (orario libro di bordo: 17:26) |
| 20 | 17:31 | `15_31_52` | 149 s | M2, 10 % | 14.1 V | tutto ok (orario libro di bordo: 17:29) |
| 21 | 17:35 | `15_35_21` | 146 s | M2, 5 %  | 13.8 V | atterraggio autonomo con batteria scarica |

> Tra il Volo 17 e il Volo 18 sono presenti tre arm/disarm erronei
> (`14_47_04`, `14_47_16`, `14_47_21`, durate 10/4/30 s) da ignorare
> nell'analisi.

---

## Topic registrati e frequenze

Tutti i log condividono la stessa configurazione, quindi i topic e le frequenze
sono praticamente identici tra i file.

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
