# Lavori aperti — tooling, BOM, analisi

Thread di lavoro **non bloccanti** per il prossimo volo. Tutto ciò che è
prerequisito al volo successivo sta in
[`azioni-pre-prossimo-volo.md`](azioni-pre-prossimo-volo.md); la cronologia di
ciò che è stato fatto sta in [`../diario.md`](../diario.md).

## Indagine RTK / RTCM (driver GPS) — APERTA

> **Decisione operativa (2026-06-04): per ora si vola SENZA RTK, solo in 3D lock.**
> Il GPS 3D (eph ~0.6 m) è sufficiente per le prove pala (basate su IMU/ESC/assetto,
> non sulla posizione assoluta) e **evita il modo di guasto**. Tenere l'RTK
> disattivato finché l'indagine sotto non è chiusa.

- [ ] **Indagare l'iniezione RTCM / interazione driver PX4 ↔ u-blox in modo RTK-rover.**
  Causa accertata del guasto GPS: in modo RTK (RTCM iniettato nell'**unico**
  ricevitore u-blox del drone — non esiste un secondo GPS) il link driver↔u-blox
  va in stallo/timeout e reinizializza → outage NAV → failsafe (atterraggio
  forzato). In 3D puro (niente RTCM) il link è stabile. **Non è il cavo, non è
  meccanico, non è una correzione RTCM corrotta**: è il *modo RTK* la
  precondizione. Prova più forte: A/B voli quadrati 04/06 (`14_07_19` RTK perde
  GPS vs `14_13_15` GPS-puro stessa missione, 0 perdita). Dettaglio, checklist e
  piano in [`indagine-rtk-attivo-2026-06-04.md`](indagine-rtk-attivo-2026-06-04.md).
  Direzione: **config/software RTK** (sorgente/instradamento RTCM, driver,
  baudrate), + log u-center lato ricevitore per vedere se stalla il rover o PX4.
  NON ri-tentare interventi su cavo/connettore/schermatura.

## Acquisizione dati di routine

- [ ] **Calibrazione corrente del power module** — richiede pinza amperometrica DC.
  Attualmente `BAT1_A_PER_V = 36.364` (default Holybro), sufficiente per trend
  ma non per misure assolute.
- [ ] **Aggiornamento parametri logging** prima del prossimo volo:
  `SDLOG_PROFILE = 857` (aggiunge bit System Identification →
  `actuator_controls_status_0` per analisi dell'effort PID).
- [ ] **Riduzione dropout di logging** (9 episodi in 28 s sul log a banco):
  leve possibili in ordine di costo — SD UHS-I U3/V30, profilo logging più
  snello, override buffer `-b` del modulo `logger` via
  `/fs/microsd/etc/extras.txt`.

## Tooling di analisi

### Consolidato (committato)

- `foxglove/ulog_to_mcap.py` — conversione `.ulg → .mcap` con `--auto-trim`
  e `--satellite` (overlay tile ESRI a partire dalle coordinate di decollo).
- `plot/info_log.py` — metadati log + elenco topic uORB con frequenza e completezza.
- `plot/gps_dump_ber.py` — diagnosi BER del link UART GPS (parsing UBX da
  topic `gps_dump`). Richiede `GPS_DUMP_COMM = 1`. Usato per validare il
  cavo schermato il 2026-06-04.
- `analisi/scripts/analizza_log.py` + `sintesi.py` — estrazione metriche
  vibrazioni / squilibrio elica / rapporti comando-RPM per ciascun volo,
  output in `analisi/dati/`.

### Da fare

- [ ] **Layout PlotJuggler salvato** — `maintenance/plotjuggler/dashboard-base.xml`:
  FFT giroscopio (3 assi, IMU principale), RPM dei 6 motori sovrapposti,
  correnti dei 6 ESC + corrente bus per cross-check, temperature ESC nel tempo,
  traiettoria XY (voli outdoor), roll/pitch/yaw vs setpoint.
- [ ] **Script Python di analisi automatica** (opzionale, complementare a
  PlotJuggler) — `maintenance/scripts/analisi_volo.py`: header (durata, dropout,
  configurazione IMU), health IMU comparativa (RMS vibrazioni, clip count),
  FFT giroscopio con identificazione picchi spettrali (squilibri), tabella
  RPM/corrente/temperatura medi e std per ESC, CSV riassuntivo per confronti
  longitudinali.

## Documentazione e BOM

- [ ] **Aggiornamento BOM** — sostituire/precisare `E-02` con il modello reale
  del power module (etichetta "PB01", da identificare via QR code).
- [ ] **Profili parametri esportati** — creare `maintenance/profili-parametri/`
  con due `.params` esportati da QGC: `banco.params` e `volo.params` (quando il
  profilo di volo sarà definitivo, dopo applicazione di
  [`azioni-pre-prossimo-volo.md`](azioni-pre-prossimo-volo.md)).
- [ ] **Stato di `telemetria-esc.md`** — il documento fa riferimento all'hardware
  Cube Black precedente. Da archiviare come "storico" o aggiornare per
  Pixhawk 6X (la configurazione corrente è già coperta da
  [`configurazione-logging.md`](configurazione-logging.md), sezione
  "Telemetria ESC su TELEM2").

## Punti aperti per la relazione

- Definizione formato e struttura della relazione finale (in attesa di
  indicazioni dal docente).
- Capitolo metodologia: descrizione del workflow
  "volo → SD → PlotJuggler/Python → trend longitudinale".
- Capitolo FMEA: tabella modi di guasto vs grandezze loggate
  - squilibrio elica → picco FFT a frequenza di rotazione,
  - cavo GPS intermittente sotto vibrazione → BER UART crescente → parser
    u-blox desync → driver auto-baud probe → gap `sensor_gps` 7–49 s → EKF
    dead-reckoning → failsafe blind-land (case study 2026-05-27),
  - survey-in base RTK non converge → degradazione posizione → abort missione
    in landing.
- Capitolo "case study": analisi forense incidente RTK 2026-05-26 + diagnosi
  cavo GPS 2026-05-27 + **validazione cavo schermato 2026-06-04** come esempio
  di ciclo diagnostico completo (osservazione → ipotesi → strumentazione del
  bus seriale via `GPS_DUMP_COMM` → causa radice → azione correttiva →
  verifica quantitativa con la stessa metrica).
- Appendice: configurazione completa parametri PX4 utilizzata, con diff
  rispetto al default.

## Indice file di manutenzione

- [`azioni-pre-prossimo-volo.md`](azioni-pre-prossimo-volo.md) — checklist
  bloccante prima del prossimo volo.
- [`configurazione-logging.md`](configurazione-logging.md) — logging PX4 e
  telemetria ESC.
- [`calibrazione-batteria.md`](calibrazione-batteria.md) — power module,
  troubleshooting, calibrazione.
- [`test-a-banco.md`](test-a-banco.md) — procedura di test indoor con bypass
  arming.
- [`troubleshooting-gps-pixhawk6x.md`](troubleshooting-gps-pixhawk6x.md) —
  problemi GPS preesistenti (riconoscimento modulo, no-fix iniziale).
- [`troubleshooting-rtk.md`](troubleshooting-rtk.md) — diagnosi RTK
  (survey-in + dropout `sensor_gps`); analisi forense incidente 2026-05-26.
- [`troubleshooting-gps-dropout-2026-05-27.md`](troubleshooting-gps-dropout-2026-05-27.md)
  — diagnosi definitiva dei dropout GPS via dump UART (causa: cavo).
- [`troubleshooting-cube-black-usb.md`](troubleshooting-cube-black-usb.md) —
  storico Cube Black (pre-Pixhawk 6X).
- [`telemetria-esc.md`](telemetria-esc.md) — storico telemetria ESC su Cube
  Black (da rivalutare).
