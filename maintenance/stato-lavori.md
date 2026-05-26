# Stato dei lavori e prossimi passi

> Indice delle attività di commissioning e dei thread aperti per la fase di acquisizione dati e analisi di manutenzione preventiva.
>
> Ultimo aggiornamento: 2026-05-27 dopo incidente RTK del 2026-05-26.

## Completato

### Commissioning iniziale

- [x] **Configurazione logging PX4** — `SDLOG_PROFILE`, `IMU_GYRO_RATEMAX`, frequenze acquisizione FIFO. Documentato in `configurazione-logging.md`.
- [x] **Telemetria ESC su TELEM2** — `DSHOT_CONFIG = 600`, `DSHOT_TEL_CFG = 102`. Verificato `esc_status` popolato a ~65 Hz nel volo `16_02_24.ulg`.
- [x] **Bypass arming indoor** — `COM_ARM_WO_GPS = 1`, modalità Stabilized. Documentato in `test-a-banco.md`.
- [x] **Power module** — risolto problema `battery_status never published` impostando `BAT1_V_CHANNEL = 16` e `BAT1_I_CHANNEL = 17`. Calibrazione tensione completata. Documentato in `calibrazione-batteria.md`.
- [x] **Primo volo a banco** — log `16_02_24.ulg` (28 s) acquisito e ispezionato.

### Voli outdoor

- [x] **Voli outdoor 2026-04-27 / 2026-04-28** — prime sessioni con GPS lock, validazione `vehicle_local_position`.
- [x] **Voli outdoor 2026-05-25 / 2026-05-26** — sessioni con RTK attivo. Il 2026-05-26 si sono verificati due episodi di dropout GPS in volo (vedi sezione incidente).

### Tooling e visualizzazione

- [x] **Conversione `.ulg` → `.mcap`** — script `foxglove/ulog_to_mcap.py` operativo. Tutti i log 2026-05-26 sono già stati convertiti.
- [x] **URDF del drone per Foxglove** — `foxglove/f550.urdf` per visualizzazione 3D.
- [x] **Documentazione Foxglove** — `foxglove/README.md` e `foxglove/terreno-3d.md` (layer satellitare).

### Analisi incidente RTK 2026-05-26

- [x] **Diagnosi del dropout `sensor_gps`** — analisi forense dei log `10_45_41.ulg` e `10_54_52.ulg`. Documentato in `troubleshooting-rtk.md`, sezione "Secondo modo di guasto".
- [x] **Verifica delle ipotesi di causa** sui sorgenti PX4 ufficiali e sulle release notes u-blox: il "bug HPG 1.40 documentato" inizialmente assunto **non risulta** dalle fonti ufficiali (vedi `troubleshooting-rtk.md`).
- [x] **Checklist correttiva post-incidente** — `azioni-pre-prossimo-volo.md`, prerequisito per qualsiasi volo successivo.

## In sospeso

### 🔴 Bloccante: pre-prossimo volo

Tutti gli item in `azioni-pre-prossimo-volo.md` sezione 🔴 sono **bloccanti**. In sintesi:

- [ ] Riconfigurazione failsafe perdita posizione (`COM_POS_FS_*`, `COM_POSCTL_NAVL`)
- [ ] Abilitazione `GPS_DUMP_COMM = 3` per diagnostica del prossimo dropout
- [ ] Volo di test con RTCM disabilitato (diagnostico)

### Mitigazioni RTK (priorità 🟡)

- [ ] Aggiornamento firmware u-blox NEO-M8P: HPG 1.40 → **HPG 1.43** (ultima release ufficiale, gennaio 2022)
- [ ] Alzare baud-rate UART GPS da 38400 a 115200
- [ ] Aggiornamento PX4 alla release stable corrente
- [ ] Stress test 5 min motori armati a terra (replicare condizioni di volo senza eliche)

### Acquisizione dati di routine

- [ ] **Calibrazione corrente del power module** — richiede pinza amperometrica DC. Attualmente `BAT1_A_PER_V = 36.364` (default Holybro), sufficiente per trend ma non per misure assolute.

- [ ] **Aggiornamento parametri logging** prima del prossimo volo:
  - `SDLOG_PROFILE = 857` (aggiunge bit System Identification → `actuator_controls_status_0` per analisi dell'effort PID)

- [ ] **Riduzione dropout di logging** (9 episodi in 28 s sul log a banco): leve disponibili sono SD più veloce (UHS-I U3/V30) e profilo di logging più snello. L'override del buffer (`-b` al modulo `logger` via `/fs/microsd/etc/extras.txt`) è opzione avanzata da valutare solo se le prime due non bastano.

### Analisi

- [ ] **Layout PlotJuggler salvato** — file `.xml` con dashboard pre-impostato:
  - FFT giroscopio (3 assi, IMU principale)
  - RPM dei 6 motori sovrapposti
  - Correnti dei 6 ESC + corrente bus per cross-check
  - Temperature ESC nel tempo
  - Traiettoria XY (per voli outdoor)
  - Roll/pitch/yaw vs setpoint

  Da salvare in `maintenance/plotjuggler/dashboard-base.xml`.

- [ ] **Script Python di analisi automatica** (opzionale, complementare a PlotJuggler) — `maintenance/scripts/analisi_volo.py`:
  - Report header (durata, dropout, configurazione IMU)
  - Health IMU comparativa (RMS vibrazioni, clip count delle 3 IMU)
  - FFT giroscopio con identificazione frequenza di rotazione vs picchi spettrali (rilevamento squilibri)
  - Tabella RPM/corrente/temperatura medi e std per ESC
  - CSV riassuntivo per confronti longitudinali tra voli successivi

### Documentazione e BOM

- [ ] **Aggiornamento BOM** — sostituire/precisare `E-02` con il modello reale del power module (etichetta "PB01", da identificare via QR code).

- [ ] **Profili parametri esportati** — creare `maintenance/profili-parametri/` con due `.params` esportati da QGC: `banco.params` e `volo.params` (quando il profilo di volo sarà definitivo, dopo le modifiche di `azioni-pre-prossimo-volo.md`).

- [ ] **Stato del file `telemetria-esc.md`** — il documento esistente fa riferimento all'hardware **Cube Black** precedente. Verificare se va archiviato come "storico" o aggiornato per Pixhawk 6X (la configurazione corrente è già coperta da `configurazione-logging.md`, sezione "Telemetria ESC su TELEM2").

## Punti aperti per la relazione

- Definizione formato e struttura della relazione finale (in attesa di indicazioni dal docente)
- Capitolo metodologia: descrizione del workflow "volo → SD → PlotJuggler/Python → trend longitudinale"
- Capitolo FMEA: tabella modi di guasto vs grandezze loggate
  - Squilibrio elica → picco FFT a frequenza di rotazione
  - **Dropout UART GPS → EKF dead-reckoning → failsafe blind-land in ALTCTL → deriva orizzontale incontrollata** (nuovo dopo incidente 2026-05-26)
  - Survey-in base RTK non converge → degradazione posizione → abort missione in landing
- Capitolo "case study": analisi forense dell'incidente RTK 2026-05-26 come esempio di metodologia diagnostica basata su dati di log
- Appendice: configurazione completa parametri PX4 utilizzata, con diff rispetto al default

## File documentazione attuali

- `configurazione-logging.md` — logging PX4 e telemetria ESC
- `calibrazione-batteria.md` — power module, troubleshooting, calibrazione
- `test-a-banco.md` — procedura di test indoor con bypass arming
- `troubleshooting-gps-pixhawk6x.md` — problemi GPS preesistenti (riconoscimento modulo, no-fix iniziale)
- `troubleshooting-rtk.md` — diagnosi RTK (survey-in + dropout `sensor_gps`); analisi forense incidente 2026-05-26
- `azioni-pre-prossimo-volo.md` — checklist correttiva post-incidente, prerequisito per qualsiasi volo successivo
- `troubleshooting-cube-black-usb.md` — storico Cube Black (preesistente)
- `telemetria-esc.md` — storico telemetria ESC su Cube Black (da rivalutare)
