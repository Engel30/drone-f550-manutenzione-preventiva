# Troubleshooting: Cube Black — Crash USB dopo modifica parametro IMU

**Data**: 2026-03-17
**Stato**: NON RISOLTO — Cube Black e carrier board sostituiti
**Componente**: CubePilot Cube Black (FMUv3, STM32F427)

---

## Descrizione del problema

Dopo aver aumentato il parametro `IMU_GYRO_RATEMAX` a un valore troppo alto (superiore a quanto supportato dal processore STM32F427), il Cube Black ha smesso di connettersi via USB.

### Sintomi

- La porta COM appare in **Gestione Dispositivi** (Windows) per pochi secondi, poi scompare
- **QGroundControl** non rileva il dispositivo (la finestra di connessione e troppo breve)
- Il comportamento e identico con o senza batteria collegata
- Il LED del Cube lampeggia brevemente all'accensione

### Causa probabile

Il valore di `IMU_GYRO_RATEMAX` impostato era troppo alto per il Cube Black (FMUv3). Il processore STM32F427 supporta al massimo ~2000 Hz; valori di 4 kHz+ sono solo per processori STM32H7 (Cube Orange). Il valore troppo alto causa un crash del firmware durante l'inizializzazione degli IMU, prima che la connessione USB MAVLink venga stabilita.

Il parametro corrotto resta salvato nella **flash interna (FRAM)** del Cube, non sulla SD card. Reflashare il firmware non resetta i parametri, perche l'area dati nella flash e separata dall'area codice.

---

## Soluzioni tentate

### 1. Cambio cavo USB e porta USB
- **Risultato**: Nessun effetto
- Il cavo e la porta funzionavano correttamente

### 2. Reflash firmware PX4 via QGroundControl
- **Risultato**: Firmware installato con successo (metodo automatico), ma il problema persiste
- **Motivo**: Il reflash sovrascrive solo il codice firmware, non l'area parametri nella flash interna

### 3. Rimozione/sostituzione SD card
- Provato senza SD card → stesso crash
- Provato con SD card funzionante (con parametri corretti del giorno prima) → stesso crash
- Cancellati i file `parameters_backup.bson` e `param_import_fail.bson` dalla SD → stesso crash
- **Conclusione**: I parametri corrotti sono nella flash interna, non sulla SD

### 4. File `etc/extras.txt` sulla SD con `param reset_all`
- **Risultato**: Nessun effetto
- **Motivo**: `extras.txt` viene eseguito **dopo** l'inizializzazione dei sensori, che e il punto in cui avviene il crash

### 5. File `etc/rc.txt` sulla SD con `param reset_all`
- `rc.txt` **sostituisce** l'intero script di boot (`rcS`) di PX4
- Con `param reset_all` + `reboot` → **boot loop confermato** (la porta COM appare/scompare ciclicamente), dimostrando che lo script viene eseguito
- Con `param reset_all` + `param save` (senza reboot) → porta COM scompare una volta sola
- Con `param set IMU_GYRO_RATEMAX 400` + `param save` → stesso risultato
- Con `param reset_all` + `param save` + `sleep 3` + `reboot` → boot loop, ma dopo rimozione di `rc.txt` il problema persiste
- **Motivo probabile**: `rc.txt` sostituisce l'intero boot, quindi il driver MTD (che gestisce la flash interna) non viene inizializzato. `param save` non riesce a scrivere nella flash

### 6. Tentativo di accesso al bootloader
- Il Cube Black **non ha un pulsante boot** accessibile dall'esterno
- Il pin **BOOT0 non e esposto** sul connettore a 80 pin
- Il metodo "connessione/disconnessione rapida 3 volte" per forzare il bootloader non ha funzionato
- QGC nella schermata Firmware non riesce a catturare il dispositivo in tempo

### 7. Firmware custom / px_uploader.py
- **Non tentato** — lo script `px_uploader.py` con `--force-erase` avrebbe lo stesso problema di timing di QGC

---

## Soluzioni non tentate (per riferimento futuro)

### A. Programmatore SWD (ST-Link / J-Link)
Il Cube Black ha **2 connettori SWD bianchi** sul fondo del modulo (visibili rimuovendo il Cube dalla carrier):
- Connettore FMU SWD (processore principale)
- Connettore IO MCU SWD

Con un ST-Link (~10-15 EUR) e **STM32CubeProgrammer** si puo:
1. Collegare al connettore SWD del FMU
2. Eseguire un **full chip erase** (cancella tutto: firmware + parametri)
3. Riflashare bootloader e firmware

Questa soluzione bypassa completamente il bootloader USB e funziona sempre.

### B. Mission Planner (ArduPilot)
Alcuni utenti riportano che Mission Planner e piu aggressivo di QGC nel catturare il bootloader nei 5 secondi di finestra all'accensione. Si potrebbe flashare temporaneamente ArduPilot e poi tornare a PX4.

---

## Note tecniche

| Concetto | Dettaglio |
|----------|-----------|
| Processore Cube Black | STM32F427 (FMUv3) |
| IMU_GYRO_RATEMAX sicuro | 400 Hz (default), max ~2000 Hz per STM32F427 |
| IMU_GYRO_RATEMAX per STM32H7 | Fino a 4000 Hz+ (Cube Orange) |
| Storage parametri | Flash interna (FRAM/MTD), NON sulla SD card |
| Reflash firmware | Sovrascrive solo il codice, non i parametri |
| Bootloader PX4 | Attivo ~5 secondi all'accensione, area protetta della flash |
| BOOT0 pin Cube Black | Non esposto sul connettore a 80 pin |
| File `rc.txt` su SD | Sostituisce completamente lo script di boot |
| File `extras.txt` su SD | Eseguito dopo l'init dei sensori (troppo tardi) |

---

## Fonti

- [IMU_GYRO_RATEMAX — PX4 Forum](https://discuss.px4.io/t/imu-gyro-ratemax/19473)
- [MC Filter Tuning & Control Latency — PX4 Guide](https://docs.px4.io/main/en/config_mc/filter_tuning)
- [Parameters & Configurations — PX4 Guide](https://docs.px4.io/main/en/advanced/parameters_and_configurations)
- [Parameters not updating when reflashing firmware — PX4 Forum](https://discuss.px4.io/t/parameters-not-updating-when-reflashing-firmware/48063)
- [Bootloader Update — PX4 Guide](https://docs.px4.io/main/en/advanced_config/bootloader_update.html)
- [BOOT0 pin not exposed on Cube — CubePilot Forum](https://discuss.cubepilot.org/t/where-is-the-boot0-pin-on-the-i-o-carrier-board-of-a-pixhawk-cube/14036)
- [SWD Debug Port — PX4 Guide](https://docs.px4.io/main/en/debug/swd_debug.html)
- [Loading bootloader with DFU — ArduPilot Dev](https://ardupilot.org/dev/docs/using-DFU-to-load-bootloader.html)
- [Cannot update firmware on new Pixhawk Cubes — QGC GitHub](https://github.com/mavlink/qgroundcontrol/issues/7523)
- [px_uploader.py — PX4 GitHub](https://github.com/PX4/PX4-Autopilot/blob/main/Tools/px_uploader.py)
- [PX4 with no SD card — PX4 Forum](https://discuss.px4.io/t/px4-with-no-sd-card/45583)

---

## Risoluzione finale

Problema non risolto via software. Il Cube Black e la carrier board sono stati **sostituiti** con nuovi componenti.

**Lezione appresa**: Non impostare `IMU_GYRO_RATEMAX` oltre i 2000 Hz sul Cube Black (STM32F427). Per valori superiori serve un Cube Orange (STM32H7). Se possibile, avere un programmatore ST-Link a disposizione per situazioni di recovery.
