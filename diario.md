# Diario di lavoro

Cronologia delle attività svolte sul progetto F550, in ordine cronologico
**inverso** (più recente in alto). Ogni voce riassume il lavoro di giornata e
rimanda al documento di dettaglio.

Per il piano voli ancora da eseguire vedi [`piano-voli.md`](piano-voli.md).
Per le azioni bloccanti prima del prossimo volo vedi
[`maintenance/azioni-pre-prossimo-volo.md`](maintenance/azioni-pre-prossimo-volo.md).

---

## 2026-05-27 — Diagnosi definitiva dropout GPS + prima sessione prove pale

**Mattina/pomeriggio — diagnosi cavo GPS**

- Sostituito Pixhawk 6X e cavo GPS (auto-costruito) prima della sessione.
- Abilitato `GPS_DUMP_COMM = 1` per registrare il flusso UART RX/TX nel topic `gps_dump`.
- Analizzati tutti gli 11 voli del mattino (`13_40_57.ulg` … `14_15_52.ulg`) con
  parsing UBX dei due bytestream. BER UART oscillante da 0.2 % (idle) a 49 %
  (regime di lift) → **causa radice: difetto di conduzione intermittente nel
  cavo GPS, attivato dalle vibrazioni dei motori**.
- Falsificate le ipotesi alternative (perdita portante, EMI motori, brownout 5 V,
  reset modulo, firmware u-blox, baud rate).
- Riconfigurato il failsafe perdita posizione (`EKF2_NOAID_TOUT`, `COM_POSCTL_NAVL`,
  limiti velocità/tilt). Aggiornata la checklist pre-volo con la sezione A0 (cavo).
- → [`maintenance/troubleshooting-gps-dropout-2026-05-27.md`](maintenance/troubleshooting-gps-dropout-2026-05-27.md)
- → [`maintenance/azioni-pre-prossimo-volo.md`](maintenance/azioni-pre-prossimo-volo.md) (sezione A0)

**Pomeriggio/sera — prove pale**

- 1ª sessione di prove con pale: 18 voli totali in Stabilize, ~1 min ciascuno.
  - **6 voli baseline** con tutte le pale sane, scambiando coppie di pale fra
    posizioni motore differenti (Set 1).
  - **6 voli con una pala accorciata del 5%**, ruotata su tutti e 6 i motori
    M1…M6 (Set 2).
  - **1 volo con pala accorciata del 10%** su M1 (Set 3, prima prova).
- → [`log/2026-05-27/README.md`](log/2026-05-27/README.md) (legenda completa
  file ↔ prova ↔ motore ↔ batteria)

## 2026-05-26 — Incidente in volo + dropout GPS

- Sessione voli RTK outdoor. Si sono verificati **due episodi di dropout
  `sensor_gps`** identici (gap 21.6 s) sui log `10_45_41.ulg` e `10_54_52.ulg`.
- Analisi forense del log `11_14_44.ulg` (decollo autonomo ~3 m, capovolgimento
  dopo ~13 s di volo): causa primaria identificata come **takeover POSCTL con
  throttle stick a −1.0** (comando discesa massima); PIO sul roll del pilota;
  commander auto-attiva `AUTO_LAND` capovolto; impatto in caduta libera
  (vz +4.95 m/s). Hardware nominalmente OK (batteria, RPM, vibrazioni, EKF).
- → [`plot/incidente/relazione_schianto.md`](plot/incidente/relazione_schianto.md)
- → [`maintenance/troubleshooting-rtk.md`](maintenance/troubleshooting-rtk.md)
  (sezione "Secondo modo di guasto" e ipotesi causa dropout — poi falsificate
  il 27/05).

## 2026-05-25 — Voli RTK preliminari

- Prime sessioni outdoor con RTK attivo. Diagnosi RTK Fixed non raggiunto
  (survey-in 3.6 m, insufficiente): proposta come soluzione la base con ground
  plane o "Use Specified Base Position" in QGC.
- → [`maintenance/troubleshooting-rtk.md`](maintenance/troubleshooting-rtk.md)

## 2026-04-28 — Voli outdoor di validazione

- 11 voli outdoor di validazione `vehicle_local_position` con GPS lock stabile.
- Log di riferimento: `10_28_38.ulg` (~166 MB, ~4 min) usato come base per
  documentare il formato ULog e l'elenco dei 147 topic uORB disponibili.
- → [`plot/DATI_LOG.md`](plot/DATI_LOG.md)

## 2026-04-27 — Primo volo outdoor + risoluzione GPS no-fix

- Migrazione GPS da CAN a UART su Pixhawk 6X. Problema iniziale: GPS non aggancia
  satelliti. Causa: `UAVCAN_ENABLE` residuo e `GPS_1_CONFIG` errato (su GPS1
  mentre il cavo era su GPS2). Risolto con `UAVCAN_ENABLE = 0`,
  `GPS_1_CONFIG = 202`, riavvio, cold start outdoor.
- 4 voli effettuati, primo GPS lock validato.
- BOM aggiornata a questa data come snapshot dello stato hardware.
- → [`maintenance/troubleshooting-gps-pixhawk6x.md`](maintenance/troubleshooting-gps-pixhawk6x.md)
- → [`docs/BOM.md`](docs/BOM.md)

## 2026-03-17 — Crash USB Cube Black → sostituzione hardware

- `IMU_GYRO_RATEMAX` impostato troppo aggressivo su Cube Black (STM32F427) →
  crash USB persistente. Tentati fix (reflash firmware, `rc.txt`, bootloader
  recovery) senza esito.
- Risoluzione finale: **sostituzione hardware con Pixhawk 6X**. Lezione: max
  ~2000 Hz su STM32F427; il Cube Orange/Pixhawk 6X (STM32H7) supporta 4000+ Hz.
- → [`maintenance/troubleshooting-cube-black-usb.md`](maintenance/troubleshooting-cube-black-usb.md)

## Commissioning iniziale (senza data esplicita)

Attività di setup completate prima dei primi voli outdoor:

- **Configurazione logging PX4**: `SDLOG_PROFILE = 849`, `IMU_GYRO_RATEMAX = 1000 Hz`,
  acquisizione FIFO ad alta frequenza.
  → [`maintenance/configurazione-logging.md`](maintenance/configurazione-logging.md)
- **Telemetria ESC su TELEM2**: `DSHOT_CONFIG = 600`, `DSHOT_TEL_CFG = 102`,
  `esc_status` popolato a ~65 Hz.
  → [`maintenance/configurazione-logging.md`](maintenance/configurazione-logging.md)
- **Bypass arming indoor**: `COM_ARM_WO_GPS = 1`, modalità Stabilized per test a
  banco. → [`maintenance/test-a-banco.md`](maintenance/test-a-banco.md)
- **Power module**: risolto `battery_status never published` con
  `BAT1_V_CHANNEL = 16` e `BAT1_I_CHANNEL = 17`; calibrazione tensione completa.
  → [`maintenance/calibrazione-batteria.md`](maintenance/calibrazione-batteria.md)
- **Primo log a banco**: `16_02_24.ulg` (28 s) acquisito e ispezionato.
- **Tooling Foxglove**: pipeline `ulog_to_mcap.py` operativa (147 topic uORB,
  transform NED→ENU, animazione eliche da RPM, overlay satellitare opzionale),
  modello URDF `f550.urdf` e layout pannelli `drone f550.json` definiti.
  → [`foxglove/README.md`](foxglove/README.md),
  [`foxglove/terreno-3d.md`](foxglove/terreno-3d.md)

---

## Lavori aperti non legati al volo

Per i task ancora pendenti che non sono prerequisito al prossimo volo
(tooling di analisi, BOM, profili parametri) vedi
[`maintenance/stato-lavori.md`](maintenance/stato-lavori.md).
