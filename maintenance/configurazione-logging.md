# Configurazione del logging — Pixhawk 6X / PX4 1.16.2

> Sistema di acquisizione dati di volo per le analisi di manutenzione preventiva (vibrazioni, salute motori, deriva sensori).

## Obiettivo

Loggare con frequenza adeguata:
- **Dati inerziali raw** (giroscopio e accelerometro a piena banda) per analisi vibrazionale FFT
- **Telemetria ESC** (RPM, tensione, corrente, temperatura per ognuno dei 6 motori)
- **Effort del controllore** (per evidenziare degrado meccanico tramite l'asimmetria di compenso PID)
- **Posizione e attitude** stimati dall'EKF (verifica del sistema di navigazione)

## Architettura del logging in PX4

PX4 utilizza il formato **ULog** (`.ulg`): file binario auto-descrittivo che contiene definizione dei topic, parametri del veicolo al momento dell'arming e stream dei messaggi timestamped. I file sono salvati su `/fs/microsd/log/<data>/<orario>.ulg`, un file per ciclo arming → disarming.

Il modulo `logger` non campiona: si limita a sottoscrivere i topic uORB pubblicati dai driver e a scriverli su SD. La frequenza di logging coincide quindi con la frequenza di pubblicazione del topic.

## Parametri di logging configurati

| Parametro | Valore | Significato |
|-----------|-------:|-------------|
| `SDLOG_MODE` | `0` | Logga da armato a disarmato |
| `SDLOG_PROFILE` | `849` | Bitmask: default + high rate + sensor comparison + raw gyro/accel |
| `SDLOG_UUID` | `1` | Aggiunge UUID veicolo al filename |
| `IMU_GYRO_RATEMAX` | `1000` | Hz, frequenza massima pubblicazione giroscopio |
| `IMU_INTEG_RATE` | `400` | Hz, rate del control loop |

### Decodifica `SDLOG_PROFILE = 849`

| Bit | Valore | Contenuto |
|-----|-------:|-----------|
| 0 | 1 | Default (stato veicolo, GPS, modalità, batteria) |
| 4 | 16 | High rate (IMU a piena frequenza) |
| 6 | 64 | Sensor comparison (3 IMU separate) |
| 8 | 256 | Raw gyro FIFO |
| 9 | 512 | Raw accel FIFO |

**Estensione consigliata:** `SDLOG_PROFILE = 857` (aggiunge bit 3 = System Identification, che logga `actuator_controls_status_0` — output PID rate/attitude, prezioso per intercettare degrado motore tramite compenso del controllore).

## Telemetria ESC su TELEM2

Gli ESC Tekko32 F4 (firmware AM32) trasmettono telemetria KISS-standard via filo dedicato. I 6 fili TLM sono uniti su un singolo UART (TELEM2) — il protocollo è request-driven dal flight controller, quindi non ci sono collisioni.

| Parametro | Valore | Significato |
|-----------|-------:|-------------|
| `DSHOT_CONFIG` | `600` | DShot600 come protocollo di comando agli ESC |
| `DSHOT_TEL_CFG` | `102` (TELEM2) | Porta UART su cui leggere la telemetria KISS |

Il driver `dshot` apre TELEM2 a 115200 baud hard-coded — non serve impostare `SER_TEL2_BAUD`.

Il topic risultante è `esc_status`, con campi `esc[i].esc_rpm`, `esc_voltage`, `esc_current`, `esc_temperature` per `i = 0..5`. Frequenza tipica con 6 ESC su un solo UART: **~65 Hz** (verificato sul log `16_02_24.ulg`).

## Topic loggati e loro utilità

| Topic | Frequenza misurata | Uso diagnostico |
|-------|-------------------:|-----------------|
| `sensor_gyro_fifo` | ~970 Hz | FFT vibrazioni, individuazione squilibri elica/cuscinetti |
| `sensor_accel_fifo` | ~920 Hz | FFT accelerazioni, squilibri strutturali |
| `vehicle_imu_status` ×3 | bassa | Clip count, RMS vibrazioni, salute IMU singole |
| `esc_status` | ~65 Hz | Trend RPM, correnti, temperature ESC |
| `actuator_motors` | ~780 Hz | Comandi normalizzati ai motori |
| `vehicle_attitude` | ~200 Hz | Roll/pitch/yaw, qualità del controllo |
| `vehicle_rates_setpoint` | ~200 Hz | Setpoint vs reale → tracking error |
| `battery_status` | ~10 Hz | Tensione/corrente bus (richiede power module calibrato) |
| `vehicle_local_position` | ~10 Hz | Posizione stimata (utile solo outdoor con GPS) |

## Lettura dei log

### Recupero file da SD

In Windows + WSL, la SD si monta automaticamente come `/mnt/<lettera>/`:

```bash
cp /mnt/d/log/<data>/<orario>.ulg ~/manutenzione-preventiva-freddi/logs/
```

I file `.ulg` sono **esclusi dal git** (`logs/` in `.gitignore`).

### Strumenti

1. **PX4 Flight Review** — https://review.px4.io — drag-and-drop del `.ulg`, report HTML automatico. Ispezione rapida.
2. **PlotJuggler** (Windows native, raccomandato) — visualizzazione interattiva multi-plot. https://github.com/facontidavide/PlotJuggler/releases
3. **pyulog** — riga di comando per ispezione e estrazione CSV:
   ```bash
   pip3 install pyulog
   ulog_info <volo>.ulg          # elenco topic e frequenze
   ulog_messages <volo>.ulg      # eventi e dropout
   ulog2csv -m sensor_gyro_fifo <volo>.ulg
   ```

## Dropout e qualità del logging

Il volo `16_02_24.ulg` (28 s, da banco) ha registrato 9 dropout per 0.4 s totali (max 157 ms). Accettabile ma non ideale: i dropout colpiscono soprattutto i FIFO ad alta frequenza.

**Mitigazioni** (in ordine di efficacia):
- **SD card più veloce:** classe **UHS-I U3 / V30** (≥30 MB/s sostenuti in scrittura sequenziale). È la leva più efficace.
- **`SDLOG_PROFILE` più snello:** rimuovere bit non utilizzati attivamente (es. Estimator Replay, Debug) per ridurre il flusso totale.
- **Override del buffer logger** (avanzato): la dimensione del buffer non è esposta come parametro PX4; va modificata negli argomenti `-b <KB>` dello start del modulo `logger` nello script di init, tramite override su `/fs/microsd/etc/extras.txt`. Da considerare solo se le prime due mitigazioni non bastano.
