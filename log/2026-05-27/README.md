# Log di volo — sessione 27 maggio 2026

Questa cartella raccoglie i 18 log `.ulg` registrati il 27 maggio 2026 con
l'esacottero F550 (Pixhawk 6X, firmware PX4). La sessione è dedicata allo studio
dell'effetto delle pale (posizione e danneggiamento): tutti i voli sono in
hovering, in modalità *Stabilize*. Le tabelle riportano per ciascun volo il tipo,
la durata, la configurazione e una nota; in fondo è riportato l'elenco dei topic
registrati con le relative frequenze.

## Note pratiche

- **Orari**: il timestamp nel nome del file è l'ora locale del Pixhawk, **2 ore
  indietro** rispetto all'ora reale → `ora reale ≈ nome file + 2 h`
  (es. `13_56_40.ulg` ≈ 15:56). In caso di dubbio fa fede l'ora UTC del GPS nel log.
- **Sito di decollo**: Ancona (Università Politecnica delle Marche).
- **Come aprire i `.ulg`**: PX4 Flight Review (<https://review.px4.io>),
  QGroundControl, PlotJuggler, oppure `pyulog` (`ulog_info file.ulg`).
- Tutti i log contengono anche il **dump raw del GPS** (`gps_dump`).

---

## I voli

Tabelle in ordine temporale. Durata = tempo armato (motori attivi). Le pale sono
numerate 1…6 e i motori M1…M6; in configurazione "default" la pala `i` è sul
motore `Mi`.

### 1 · Voli preliminari e controlli a terra

Prova iniziale e armamenti brevi (verifiche / arming senza volo effettivo).

| File | ≈ ora | Durata | Nota |
|---|---|---:|---|
| `13_40_57` | 15:41 | 342 s | volo di prova iniziale (riscaldamento) |
| `13_50_41` | 15:50 | 11 s | check a terra |
| `13_50_52` | 15:51 | 11 s | check a terra |
| `13_51_13` | 15:51 | 18 s | hop molto breve |

### 2 · Hovering — pale sane (baseline)

Hover di circa 1 minuto a pale sane. Si parte dalla configurazione default e a
ogni volo si scambia una coppia di pale tra due motori, per valutare eventuali
accoppiamenti pala–motore.

| File | ≈ ora | Durata | Configurazione |
|---|---|---:|---|
| `13_51_37` | 15:51 | 95 s | default (nessuno scambio) |
| `13_56_40` | 15:56 | 80 s | scambio pala 2 ↔ 4 |
| `14_00_42` | 16:00 | 90 s | scambio pala 2 ↔ 5 |
| `14_05_57` | 16:05 | 91 s | scambio pala 4 ↔ 5 |
| `14_09_26` | 16:09 | 83 s | scambio pala 1 ↔ 3 |
| `14_12_24` | 16:12 | 86 s | scambio pala 3 ↔ 6 |
| `14_15_52` | 16:15 | 80 s | scambio pala 3 ↔ 6 (ripetizione) |

### 3 · Hovering — pala danneggiata 5 %

Una pala accorciata del 5 % (squilibrio statico) montata su un motore alla volta,
a turno su M1…M6.

| File | ≈ ora | Durata | Pala 5 % su |
|---|---|---:|---|
| `15_47_35` | 17:47 | 88 s | **M2** |
| `15_50_20` | 17:50 | 90 s | **M4** |
| `15_54_10` | 17:54 | 77 s | **M5** |
| `16_00_57` | 18:00 | 79 s | **M1** |
| `16_03_10` | 18:03 | 81 s | **M3** |
| `16_05_24` | 18:05 | 88 s | **M6** |

### 4 · Hovering — pala danneggiata 10 %

Stessa procedura con una pala accorciata del 10 %.

| File | ≈ ora | Durata | Pala 10 % su |
|---|---|---:|---|
| `16_07_29` | 18:07 | 82 s | **M1** |

> In questi voli si notano cali occasionali del segnale GPS sotto carico motore;
> trattandosi di voli in *Stabilize*, in cui il controllo non usa il GPS, la cosa
> non influisce sui dati delle pale.

---

## Topic registrati e frequenze

Tutti i log condividono la stessa configurazione, quindi i topic e le frequenze
sono praticamente identici tra i file (valori qui dal volo `13_56_40`).

> Alcuni topic compaiono in più copie perché i relativi sensori sono ridondanti
> (il Pixhawk ha 3 IMU e più magnetometri): è normale, vengono votati a bordo.
> In tutto ~80 topic; l'elenco esatto di un file si ottiene con `ulog_info`.

**Vibrazioni e dinamica ad alta frequenza** *(utili per l'effetto pala)*

| Topic | Hz | Contenuto |
|---|---:|---|
| `sensor_accel_fifo` | ~1000 | accelerometro ad alta frequenza |
| `sensor_gyro_fifo` | ~1000 | giroscopio ad alta frequenza |
| `vehicle_angular_velocity` | ~1000 | velocità angolare |
| `sensor_combined` | ~225 | IMU combinata (accel + gyro) |
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
| `vehicle_attitude` | ~225 | assetto stimato |
| `vehicle_attitude_setpoint` | ~225 | assetto desiderato |
| `vehicle_rates_setpoint` | ~225 | rateo angolare desiderato |
| `rate_ctrl_status` | ~50 | stato anelli di controllo |
| `vehicle_local_position` | ~10 | posizione/velocità locale |

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
| `gps_dump` | ~20 | dump raw del ricevitore u-blox |
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
