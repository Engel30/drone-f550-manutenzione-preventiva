# Stato dei lavori e prossimi passi

> Indice delle attività di commissioning e dei thread aperti per la fase di acquisizione dati e analisi di manutenzione preventiva.

## Completato

- [x] **Configurazione logging PX4** — `SDLOG_PROFILE`, `IMU_GYRO_RATEMAX`, frequenze acquisizione FIFO. Documentato in `configurazione-logging.md`.
- [x] **Telemetria ESC su TELEM2** — `DSHOT_CONFIG = 600`, `DSHOT_TEL_CFG = 102`. Verificato `esc_status` popolato a ~65 Hz nel volo `16_02_24.ulg`.
- [x] **Bypass arming indoor** — `COM_ARM_WO_GPS = 1`, modalità Stabilized. Documentato in `test-a-banco.md`.
- [x] **Power module** — risolto problema `battery_status never published` impostando `BAT1_V_CHANNEL = 16` e `BAT1_I_CHANNEL = 17`. Calibrazione tensione completata. Documentato in `calibrazione-batteria.md`.
- [x] **Primo volo a banco** — log `16_02_24.ulg` (28 s) acquisito e ispezionato.

## In sospeso

### Acquisizione dati

- [ ] **Volo outdoor 2–3 minuti con GPS lock** — necessario per:
  - Validare la stima di posizione (`vehicle_local_position` con valori reali)
  - Triggerare `hover_thrust_estimate` (richiede hover effettivo)
  - Acquisire dati FFT con risoluzione frequenziale adeguata (più sample → migliore risoluzione)
  - Verificare `battery_status` con corrente reale di volo

- [ ] **Calibrazione corrente del power module** — richiede pinza amperometrica DC. Attualmente `BAT1_A_PER_V = 36.364` (default Holybro), sufficiente per trend ma non per misure assolute.

- [ ] **Aggiornamento parametri logging** prima del prossimo volo:
  - `SDLOG_PROFILE = 857` (aggiunge bit System Identification → `actuator_controls_status_0` per analisi dell'effort PID)

- [ ] **Riduzione dropout di logging** (9 episodi in 28 s sul log di prova): non esiste un parametro PX4 per il buffer del logger. Le leve disponibili sono SD più veloce (UHS-I U3/V30) e profilo di logging più snello. L'override del buffer (`-b` al modulo `logger` via `/fs/microsd/etc/extras.txt`) è opzione avanzata da valutare solo se le prime due non bastano.

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

- [ ] **Profili parametri esportati** — creare `maintenance/profili-parametri/` con due `.params` esportati da QGC: `banco.params` e `volo.params` (quando il profilo di volo sarà definitivo).

- [ ] **Stato del file `telemetria-esc.md`** — il documento esistente fa riferimento all'hardware **Cube Black** precedente. Verificare se va archiviato come "storico" o aggiornato per Pixhawk 6X (la configurazione corrente è già coperta da `configurazione-logging.md`, sezione "Telemetria ESC su TELEM2").

## Punti aperti per la relazione

- Definizione formato e struttura della relazione finale (in attesa di indicazioni dal docente)
- Capitolo metodologia: descrizione del workflow "volo → SD → PlotJuggler/Python → trend longitudinale"
- Capitolo FMEA: tabella modi di guasto vs grandezze loggate (es. squilibrio elica → picco FFT a frequenza di rotazione)
- Appendice: configurazione completa parametri PX4 utilizzata, con diff rispetto al default

## File documentazione attuali

- `configurazione-logging.md` — logging PX4 e telemetria ESC
- `calibrazione-batteria.md` — power module, troubleshooting, calibrazione
- `test-a-banco.md` — procedura di test indoor con bypass arming
- `troubleshooting-gps-pixhawk6x.md` — problemi GPS (preesistente)
- `troubleshooting-cube-black-usb.md` — storico Cube Black (preesistente)
- `telemetria-esc.md` — storico telemetria ESC su Cube Black (da rivalutare)
