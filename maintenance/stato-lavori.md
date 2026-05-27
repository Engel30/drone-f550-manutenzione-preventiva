# Lavori aperti — tooling, BOM, analisi

Thread di lavoro **non bloccanti** per il prossimo volo. Tutto ciò che è
prerequisito al volo successivo sta in
[`azioni-pre-prossimo-volo.md`](azioni-pre-prossimo-volo.md); la cronologia di
ciò che è stato fatto sta in [`../diario.md`](../diario.md).

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
  cavo GPS 2026-05-27 come esempio di metodologia diagnostica basata su log e
  strumentazione del bus seriale (`GPS_DUMP_COMM`).
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
