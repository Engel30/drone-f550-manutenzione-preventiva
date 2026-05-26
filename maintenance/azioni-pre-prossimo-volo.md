# Azioni correttive pre-prossimo volo

> Checklist delle attività da completare **prima del prossimo volo** del F550 a seguito dei due incidenti del 2026-05-26 (log `10_45_41.ulg` e `10_54_52.ulg`).
>
> Riferimento diagnostico completo: [`troubleshooting-rtk.md`](./troubleshooting-rtk.md), sezione "Secondo modo di guasto".

## Riepilogo del problema

In due voli consecutivi il modulo Here+ (NEO-M8P, firmware HPG 1.40ROV) ha smesso di pubblicare `sensor_gps` per **21.6 s** (durata identica al centesimo in entrambi i log → comportamento deterministico, non guasto meccanico stocastico).

Il dropout in sé non è l'emergenza: lo è la reazione del failsafe attualmente configurato (`mc_pos_control: Failsafe: blind land`), che mette il drone in modalità senza controllo orizzontale → deriva libera a 2-3 m/s → quasi-schianto evitato solo dall'intervento manuale del pilota (con throttle saturato a +1, picchi di corrente 47 A, magnetometro disturbato a fine volo).

**La causa radice del dropout non è ancora confermata** (vedi `troubleshooting-rtk.md` per le ipotesi e per cosa è stato verificato sui sorgenti PX4 e sulla documentazione u-blox). Le azioni in questo documento sono divise tra: (1) modifiche che proteggono dallo schianto **a prescindere dalla causa**, (2) diagnostiche per discriminare le ipotesi residue, (3) mitigazioni precauzionali.

---

## 🔴 CRITICO — da completare prima di QUALSIASI volo

### A1. Riconfigurazione failsafe perdita posizione

> ⚠️ Questa è la modifica che da sola, indipendentemente dalla causa del dropout, **impedisce che si ripeta lo scenario di quasi-schianto**.

**Parametri PX4 da modificare** (riferimento: [PX4 Safety/Failsafe params](https://docs.px4.io/main/en/config/safety.html)):

| Parametro | Default attuale | Nuovo valore | Motivazione |
|---|---|---|---|
| `COM_POS_FS_DELAY` | 1 s | **20 s** | Copre la durata del gap GPS noto (21.6 s). PX4 mantiene posizione via dead-reckoning invece di triggerare il failsafe |
| `COM_POS_FS_EPH` | 5 m | **25 m** | Durante dead-reckoning l'EKF arriva a `pos_horiz_accuracy=21 m` prima del recupero spontaneo. Soglia 5 m è troppo aggressiva |
| `COM_POS_FS_EPV` | 10 m | **15 m** | Stesso ragionamento per la verticale |
| `COM_POSCTL_NAVL` | 1 (Land) | **0 (Altitude/Manual)** | In caso di perdita posizione, il pilota mantiene il controllo via stick anziché blind-land |
| `COM_POS_FS_GAIN` | 10 | (lasciare 10) | Moltiplicatore di tolleranza, ok |

**Procedura in QGC:**

1. QGC → Vehicle Setup → **Parameters**
2. Filtro: `COM_POS_FS_` → modificare DELAY, EPH, EPV come da tabella
3. Filtro: `COM_POSCTL_NAVL` → impostare a `0`
4. Click **Save** in basso a destra
5. Riavviare il Pixhawk (toggle USB o ricicla potenza)
6. Esportare i parametri post-modifica in `maintenance/profili-parametri/volo.params` (vedi TODO in `stato-lavori.md`)

**Test obbligatorio di verifica (a terra, eliche RIMOSSE):**

- [ ] Armare il drone in POSCTL
- [ ] Coprire l'antenna GPS con un foglio di alluminio (simula perdita fix)
- [ ] Cronometrare: PX4 non deve triggerare blind-land prima di **20 s**
- [ ] Dopo 20 s deve passare a Altitude mode con sticks attivi e responsive
- [ ] Rimuovere l'alluminio: il fix deve recuperare e tornare a POSCTL
- [ ] Disarmare

> ⚠️ Se il test fallisce (blind-land prima di 20 s), NON volare. I parametri non sono stati applicati correttamente.

---

### A2. Abilitare GPS_DUMP_COMM per il prossimo volo

> Senza il dump UART grezzo del prossimo dropout, ogni ipotesi sulla causa resta speculativa. Questa è la diagnostica più importante.

**Parametro:**

- `GPS_DUMP_COMM = 3` (Both / RX + TX) — registra nei file `gps_dump_*.bin` sulla SD tutto il traffico UART in entrambe le direzioni

**Procedura:**

1. [ ] In QGC → Parameters → filtro `GPS_DUMP_COMM` → impostare a `3`
2. [ ] Verificare che la SD card abbia almeno 500 MB liberi (il dump genera ~1-2 MB/min)
3. [ ] Volare normalmente (con failsafe già riconfigurato come A1)
4. [ ] Al prossimo dropout: estrarre i file dump dalla SD
5. [ ] Aprire i dump con [PX4 GPS log analysis tools](https://github.com/PX4/PX4-GPSDrivers) o convertire in formato leggibile da u-center

**Cosa cercare nel dump al momento del gap:**

- Il modulo smette di trasmettere completamente? → ipotesi watchdog interno u-blox
- Trasmette ma con frame corrotti / desincronizzati? → ipotesi parser desync / saturazione UART
- C'è qualcosa di anomalo nella RTCM in ingresso pochi secondi prima del gap? → ipotesi RTCM malformata che mette il modulo in stato anomalo

---

### A3. Volo di test con RTCM disabilitato (diagnostico)

> Test diagnostico per isolare se il dropout dipende dal flusso RTCM in ingresso.

**Procedura:**

1. [ ] In QGC → Application Settings → General → RTK GPS → **disattivare** "Use RTK"
2. [ ] Volare lo stesso profilo missione (ovviamente senza pretese di precisione RTK Fixed; il modulo opererà in 3D normale)
3. [ ] Tenere `GPS_DUMP_COMM = 3` per registrare il flusso
4. [ ] Durata test: almeno 10 minuti per replicare le condizioni dei voli incidente
5. [ ] Riattivare RTK per i voli operativi

**Interpretazione:**

- Se **nessun dropout** in 10 min senza RTCM → conferma forte che la causa è legata al flusso RTCM (firmware HPG 1.40 + RTCM, oppure saturazione UART da PVT + RTCM)
- Se **dropout presente** anche senza RTCM → causa altrove (watchdog interno indipendente da RTCM, problema HW)

---

## 🟡 IMPORTANTE — mitigazioni precauzionali

### B1. Aggiornamento firmware u-blox: HPG 1.40 → HPG 1.43

> **Nota onesta**: questa azione era stata presentata come "fix della causa primaria" in versioni precedenti del documento, ma le release notes ufficiali u-blox HPG 1.41/1.42/1.43 **non documentano alcun fix specifico** per PVT output stall, UART stall o re-inizializzazione del modulo in RTK Float. L'aggiornamento è comunque sensato come mitigazione precauzionale (è l'ultima versione stabile, gennaio 2022) e perché HPG 1.43 introduce *Improved MSM correction stream handling* che potrebbe migliorare robustezza con stream RTCM non standard.

**Materiale necessario:**

- [ ] Adattatore USB-to-TTL (FTDI, CP2102 o CH340 — qualsiasi va bene, ~5-10 €)
- [ ] Cavo breakout JST-GH 6 pin ↔ DuPont (incluso nel kit Here+, altrimenti acquistare)
- [ ] Software **u-center** (Windows): https://www.u-blox.com/en/product/u-center (versione consigliata 21.09 o successiva)
- [ ] File firmware: `UBX_M8_305_HPG_143_ROVER.74d7454b395e2fdf680d864f40b9dbed.bin` ([release note ufficiale, gennaio 2022](https://content.u-blox.com/sites/default/files/NEO-M8P_FW305-RTK143_RN_UBX-21035325.pdf))

**Cablaggio (pinout JST-GH 6 pin del Here+):**

```
Pin 1 (VCC 5V)  ──→  USB-TTL  VCC (5V)
Pin 2 (TX GPS)  ──→  USB-TTL  RX
Pin 3 (RX GPS)  ──→  USB-TTL  TX
Pin 6 (GND)     ──→  USB-TTL  GND
(Pin 4 e 5 = I2C magnetometro, non servono per l'update)
```

**Procedura:**

1. [ ] Smontare il Here+ rover dal mast (scollegare cavo JST-GH dal Pixhawk)
2. [ ] Cablare al PC via adattatore USB-TTL
3. [ ] Aprire u-center → Receiver → Connection → COM port dell'adattatore, baud **9600**
4. [ ] Verificare che i messaggi NMEA scorrano in console
5. [ ] **Backup configurazione corrente**: Tools → Receiver Configuration → Save to file (`.txt`)
6. [ ] Tools → **Firmware Update Utility**:
   - Firmware image: `UBX_M8_305_HPG_143_ROVER.bin`
   - FIS: lasciare default
   - Baudrate update: **115200**
   - Use safeboot: ☑
   - Use chip erase: ☑
   - Click **GO** (durata 5-10 min, non scollegare nulla)
7. [ ] Verificare in Receiver → Configuration: `FW Version = HPG 1.43ROV`
8. [ ] Riconfigurare il modulo:
   - **UBX-CFG-RATE**: PVT a **2 Hz** (sotto rispetto al default 5 Hz, alleggerisce la UART)
   - **UBX-CFG-GNSS**: GPS + GLONASS + Galileo (BeiDou disattivato)
   - **UBX-CFG-PRT**: UART a **115200 baud**
   - **UBX-CFG-MSG**: abilitare UBX-NAV-PVT, UBX-NAV-SAT, UBX-NAV-RELPOSNED
   - **UBX-CFG-CFG**: Save Current Configuration su **Battery-backed RAM + Flash** (altrimenti perdi tutto al power-cycle)
9. [ ] Rimontare il Here+ sul mast, ricollegare al Pixhawk
10. [ ] In QGC: impostare `SER_GPS1_BAUD = 115200` (deve combaciare col baud configurato sul modulo)
11. [ ] Verificare in QGC che il fix sia presente con ~12-15 satelliti come prima

> ⚠️ **Rischio brick**: durante l'update, interruzioni di corrente o disconnessione del cavo possono lasciare il modulo non funzionante. Mitigazioni: laptop sotto carica, cavi corti, USB del PC (non hub), nessuna applicazione che usa la porta seriale aperta in background.

---

### B2. Alzare baud-rate UART GPS da 38400 a 115200

> Il calcolo throughput: PVT 5 Hz (~100 byte) + RXM-RAWX 5 Hz (~500 byte) + RTCM ingresso ~200 byte/s = ~3500 byte/s in TX + ingresso = ~28 kbps occupati su 38400 → margine basso. A 115200 il margine triplica.

- [ ] Eseguito come parte di B1 step 8 (UBX-CFG-PRT) e step 10 (`SER_GPS1_BAUD`)
- [ ] Verificare nel `gps_dump_*.bin` post-modifica che non ci siano frame troncati

---

### B3. Aggiornamento PX4 alla release stable corrente

Il driver `gps` di PX4 ha avuto multipli fix sulla gestione errori UBX nelle release recenti.

- [ ] Verificare versione attuale: in QGC → Analyze → MAVLink Console → comando `ver all`
- [ ] Aggiornare a PX4 stable (current) via QGC → Vehicle Setup → Firmware
- [ ] Dopo flash: ri-uploadare il file parametri salvato (i parametri vengono mantenuti, ma fare backup .params è buona pratica)
- [ ] Ri-eseguire calibrazioni (compass, accelerometro, ESC) — PX4 lo richiede dopo un flash major

---

### B4. Test a terra prolungato del modulo GPS

> Dopo aggiornamento firmware (B1) e prima del primo volo outdoor, validare che il modulo non manifesti più dropout in condizioni controllate.

**Procedura:**

- [ ] Drone all'aperto, vista cielo libera, **eliche rimosse**
- [ ] Armare con `COM_ARM_WO_GPS = 0` (modalità POSCTL, richiede fix)
- [ ] Motori al regime hover-equivalent (throttle ~50%) per **5 minuti consecutivi**
- [ ] In parallelo: QGC → Analyze → MAVLink Console → `listener sensor_gps` o `listener vehicle_gps_position`
- [ ] Verifiche durante i 5 minuti:
  - [ ] `sensor_gps.timestamp` cresce regolarmente, **nessun salto > 2 s**
  - [ ] `fix_type` resta a 5 (RTK Float) o 6 (RTK Fixed) per tutto il test
  - [ ] `satellites_used` resta ≥ 10
- [ ] Disarmare e analizzare il log `.ulg` generato con lo script `plot/info_log.py` o pyulog inline

**Esito atteso:** zero dropout in 5 minuti di stress test.

**Se il test fallisce** (dropout riproducibile a terra): tornare al troubleshooting hardware (vedi C1).

---

## 🟢 IGIENICO — da fare per esclusione, costo trascurabile

### C1. Ispezione meccanica connettori GPS

> Probabilità di causa scartata dai dati (la durata fissa 21.6 s del gap esclude un connettore intermittente, che avrebbe durate stocastiche), ma l'ispezione costa nulla.

- [ ] Estrarre il connettore JST-GH 10 pin del cavo GPS lato Pixhawk 6X
- [ ] Verificare crimping pin per pin (continuità + assenza di gioco con tester)
- [ ] Reinserire fino al click
- [ ] **Hot-glue** sul connettore per immobilizzarlo (anti-vibrazione)
- [ ] Stessa procedura sul connettore lato modulo Here+ se accessibile

---

### C2. Mitigazioni EMI (preventive)

I dati hanno escluso EMI come causa scatenante (vedi `troubleshooting-rtk.md`), ma restano buone pratiche di igiene EM:

- [ ] **Ferrite clip** sul cavo GPS in prossimità del connettore Pixhawk
- [ ] Verificare **separazione fisica** cavo GPS ↔ cavi fase motore (lato opposto del frame se possibile)
- [ ] Valutare cavo GPS **schermato** (treccia metallica + drain wire collegato a GND Pixhawk)

---

## 🟢 RIDONDANZA STRUTTURALE — pianificazione a medio termine

### D1. Secondo modulo GPS sulla porta GPS2

> Soluzione definitiva: anche se la causa radice non viene identificata, un secondo modulo indipendente copre il blending.

- [ ] Acquisto modulo **Holybro M9N** (~60 €, multi-costellazione, generazione hardware diversa dal NEO-M8P)
- [ ] Connessione alla porta **GPS2** del Pixhawk 6X
- [ ] Configurazione PX4: `GPS_2_PROTOCOL = u-blox`, `SENS_GPS_MASK` impostato per blending automatico
- [ ] Test di hot-failover: simulare guasto del Here+ (scollegare a caldo) → l'EKF deve continuare usando il M9N

### D2. Upgrade hardware a u-blox ZED-F9P (lungo termine)

Il NEO-M8P è EOL (end-of-life) dal 2023 (l'ultimo firmware risale a gennaio 2022). Il successore è il **ZED-F9P** (multi-banda L1+L2, fix Fixed più rapido, multi-costellazione contemporanea, generazione hardware completamente diversa). Da considerare per un eventuale upgrade del setup RTK.

---

## Procedura di volo dopo le modifiche

Dopo aver completato almeno la sezione 🔴:

1. [ ] **Test parametri**: ripetere A1 step di verifica (alluminio sull'antenna a terra)
2. [ ] **Verificare GPS_DUMP_COMM = 3** attivo
3. [ ] **Test motori a terra**: B4 (5 minuti) — verificare nessun dropout
4. [ ] **Primo volo di verifica**: hover manuale (POSCTL) in line-of-sight, breve (~1 min), pilota pronto a switch in STABILIZED
5. [ ] **Volo diagnostico A3** (RTCM disabilitato): missione semplice in AUTO, 10 min, line-of-sight
6. [ ] **Solo dopo successo**: tornare a missioni con landing autonomo e RTK attivo

Per ogni volo di verifica, analizzare il `.ulg` con script in `plot/` per confermare:
- Nessun gap in `sensor_gps.timestamp`
- `pos_horiz_accuracy` resta sotto 1 m per tutta la missione
- Nessun reset driver nei `logged_messages`
- Se possibile, analizzare anche i file `gps_dump_*.bin` con u-center per ispezionare il flusso UART

---

## Checklist riepilogativa stampabile

| # | Azione | Priorità | Stato |
|---|---|---|---|
| A1 | Modifica parametri failsafe (COM_POS_FS_*, COM_POSCTL_NAVL) | 🔴 | [ ] |
| A1.test | Test a terra con antenna coperta | 🔴 | [ ] |
| A2 | Abilitare `GPS_DUMP_COMM = 3` | 🔴 | [ ] |
| A3 | Volo di test con RTCM disabilitato (diagnostico) | 🔴 | [ ] |
| B1 | Aggiornamento firmware u-blox HPG 1.40 → **1.43** | 🟡 | [ ] |
| B2 | Alzare baud-rate UART GPS a 115200 | 🟡 | [ ] |
| B3 | Aggiornamento PX4 alla release stable corrente | 🟡 | [ ] |
| B4 | Stress test 5 min motori armati a terra | 🟡 | [ ] |
| C1 | Ispezione + hot-glue connettori GPS | 🟢 | [ ] |
| C2 | Ferrite clip + separazione fisica cavi | 🟢 | [ ] |
| D1 | Installazione secondo GPS M9N (GPS2) | 🟢 | [ ] |
| D2 | Pianificazione upgrade a ZED-F9P | 🟢 | [ ] |

---

## Riferimenti

- [`troubleshooting-rtk.md`](./troubleshooting-rtk.md) — diagnosi completa con timeline e analisi quantitativa dei due log incidente
- [`test-a-banco.md`](./test-a-banco.md) — procedure di sicurezza per test indoor con bypass arming
- [`stato-lavori.md`](./stato-lavori.md) — tracking generale delle attività di commissioning
- Log analizzati: `log/2026-05-26/10_45_41.ulg`, `log/2026-05-26/10_54_52.ulg`

### Fonti verificate

- [PX4 Failsafe parameters (main)](https://docs.px4.io/main/en/config/safety.html)
- [PX4 GPS parameters (`GPS_DUMP_COMM`)](https://docs.px4.io/main/en/advanced_config/parameter_reference.html#GPS_DUMP_COMM)
- [Sorgente driver GPS PX4 (`gps.cpp`)](https://github.com/PX4/PX4-Autopilot/blob/main/src/drivers/gps/gps.cpp) — timeout effettivi del driver
- [Release note u-blox HPG 1.43 (UBX-21035325, 10 gen 2022)](https://content.u-blox.com/sites/default/files/NEO-M8P_FW305-RTK143_RN_UBX-21035325.pdf) — bugfix limitati a MSM e BDS D2; nessun fix UART/PVT stall documentato
- [Release note u-blox HPG 1.40 (UBX-17021504, 2018)](https://content.u-blox.com/sites/default/files/NEO-M8P-FW301-HPG140_RN_(UBX-17021504).pdf) — versione attualmente flashata
- [Pagina prodotto u-blox NEO-M8P (EOL)](https://www.u-blox.com/en/product/neo-m8p-series)
- [u-center download](https://www.u-blox.com/en/product/u-center)
