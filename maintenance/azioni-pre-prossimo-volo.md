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

> ⚠️ **Correzione importante rispetto a versioni precedenti del documento**: durante l'applicazione abbiamo scoperto che `COM_POSCTL_NAVL` **era già a `Altitude`** prima degli incidenti, eppure il blind-land è scattato. Il vero gating è `EKF2_NOAID_TOUT` (livello EKF), non i parametri commander. Vedi sezione "Architettura failsafe a due livelli" in [`troubleshooting-rtk.md`](./troubleshooting-rtk.md) per la spiegazione completa.

**Parametri PX4 — configurazione applicata 2026-05-27:**

| Parametro | Default | Applicato | Motivazione |
|---|---|---|---|
| `EKF2_NOAID_TOUT` | 5000000 μs (5 s) | **10000000 μs (10 s)** | Cap firmware. Ritarda la dichiarazione `xy_valid=false` da parte dell'EKF, che è la vera causa del blind-land di `mc_pos_control` |
| `COM_POSCTL_NAVL` | Land (1) | **Altitude (0)** | Era già a Altitude. Se il commander gestisce il failsafe prima di `mc_pos_control`, il pilota ha stick attivi |
| `COM_POS_FS_EPH` | 5 m | **10 m** | Soglia accuracy orizzontale failsafe commander |
| `MPC_VEL_MANUAL` | 10 m/s | **5 m/s** | Velocità max comandabile via stick in POSCTL → meno inerzia durante eventuale deriva |
| `MPC_XY_VEL_MAX` | 12 m/s | **5 m/s** | Cap globale velocità orizzontale |
| `MPC_XY_CRUISE` | 5 m/s | **3 m/s** | Velocità crociera missioni AUTO |
| `MPC_TILTMAX_AIR` | 45° | **25°** | Limita tilt → migliora stabilità + riduce velocità massima raggiungibile |

**Parametri non disponibili / non modificabili in questa build PX4:**

| Parametro | Stato | Note |
|---|---|---|
| `COM_POS_FS_DELAY` | Non esiste | Nei docs PX4 main ma non in questa firmware |
| `COM_POS_FS_EPV` | Non esiste | Idem |
| `MPC_ACC_HOR` | Auto-derivato | Calcolato da PX4 in base a velocità/tilt; valore mostrato non modificabile |
| `MPC_JERK_MAX` | Auto-vincolato (33) | Sistema trajectory shaping clampa al minimo feasibile |
| `MPC_JERK_AUTO` | Auto-vincolato (16) | Stesso |

**Procedura applicata in QGC:**

1. QGC → Vehicle Setup → **Parameters**
2. Per ogni parametro nella tabella: filtra il nome, modifica valore, **Save**
3. Verifica che il valore salvato corrisponda (alcuni parametri ritornano al valore precedente: significa auto-vincolo, vedi tabella sopra)
4. Riavviare il Pixhawk (toggle USB o ricicla potenza)
5. Esportare i parametri post-modifica:
   - QGC → Tools → **Save Parameters to File**
   - Salvare in `maintenance/profili-parametri/volo-2026-05-27.params`

**Test obbligatorio di verifica (a terra, eliche RIMOSSE):**

- [ ] Armare il drone in POSCTL (richiede fix GPS — aspettare che arrivi)
- [ ] Avviare cronometro
- [ ] Coprire l'antenna GPS con un foglio di alluminio (simula perdita fix)
- [ ] Osservare in QGC e annotare:
  - [ ] A che tempo appare il primo messaggio anomalo (`invalid setpoints`, cambio nav_state, failsafe activated)?
  - [ ] Il drone passa in **Altitude** (stick orizzontali attivi) o in **blind-land** (discesa verticale senza controllo orizzontale)?
  - [ ] Lo stick orizzontale risponde dopo il cambio modalità?
- [ ] Rimuovere l'alluminio dopo ~30 s
- [ ] Verificare che torni in POSCTL automaticamente
- [ ] Disarmare

**Esito atteso:** failsafe scatta attorno a **t = 10 s** (era ~3-5 s prima). Idealmente passa in Altitude con stick attivi. Se invece scatta blind-land, è la conferma che `mc_pos_control` vince la race condition contro il commander — vedi mitigazioni residue sotto.

**Mitigazioni residue se il test conferma blind-land a t=10s:**

- Briefing pilota: **flippare in STABILIZED dal radiocomando** appena si vede perdita di quota o deriva anomala. STABILIZED bypassa `mc_pos_control` e dà controllo manuale puro, ignorando lo stack position controller (e quindi anche tutti i limiti di velocità/tilt configurati).
- Con `MPC_XY_VEL_MAX ≈ 3` e `MPC_TILTMAX_AIR = 25`, la deriva orizzontale durante gli 11.6 s di blind-land scoperti scende a max ~35 m (vs ~58 m con velocità 5 m/s, vs ~115 m col default 10 m/s).

---

### A1-bis. Configurazione Flight Behavior sliders (QGC)

QGC → Vehicle Setup → **Flight Behavior** espone tre slider che sono **macro** sui parametri MPC: spostandoli si modificano simultaneamente più parametri di basso livello in modo coerente (e auto-vincolato — è il motivo per cui parametri come `MPC_JERK_MAX` e `MPC_ACC_HOR` non si lasciano modificare manualmente).

**Configurazione applicata (2026-05-27):**

| Slider | Valore | Parametri governati | Motivazione |
|---|---|---|---|
| **Responsiveness** | **0.5** (Medium) | `MPC_ACC_HOR_MAX`, `MPC_ACC_UP/DOWN_MAX`, `MPC_JERK_MAX`, `MPC_JERK_AUTO` | Compromesso tra reattività e prevedibilità. Responsiveness più alta (era 0.8) aumenta il rischio di PIO con pilota in training |
| **Horizontal Velocity** | **3 m/s** | `MPC_XY_VEL_MAX`, `MPC_XY_CRUISE` (probabilmente anche `MPC_VEL_MANUAL`) | Cap conservativo per F550 in fase test. Riduce la deriva massima durante i ~11.6 s di blind-land scoperti |
| **Vertical Velocity** | **1 m/s** | `MPC_Z_VEL_MAX_UP`, `MPC_Z_VEL_MAX_DN` | Sotto soglia Vortex Ring State (~2-3 m/s). Atterraggi più lenti → più tempo per intervento pilota |

**Quando sono attivi:** dovunque sia attivo il position controller — **POSCTL** (manuale con position hold), **ALTCTL** (parziale, solo Vertical Velocity e Responsiveness asse Z), **AUTO_*** (tutte le missioni).

**Quando NON sono attivi:** **MANUAL**, **ACRO**, **STABILIZED**. Il pilota in STABILIZED bypassa l'intero stack — è la rete di sicurezza per il recupero in emergenza.

**Considerazione sul recupero in emergenza:**

> Una preoccupazione naturale è "responsiveness 0.5 rende lento il drone se devo recuperarlo da una situazione critica". La risposta è no, perché:
> 1. Il recupero in emergenza si fa in **STABILIZED**, non in POSCTL → lo slider non si applica
> 2. Responsiveness alta è **statisticamente più PIO-prone** (Pilot-Induced Oscillation) — esattamente quello che ha causato i picchi 47 A negli incidenti precedenti
> 3. A 0.5 il drone raggiunge max accelerazione in ~0.4 s — adeguato per evasioni a 5-10 m, e per ostacoli più vicini nessuna configurazione di slider è sufficiente

**Verifica post-configurazione:**

- [ ] In Parameters → filtra `MPC_XY_VEL_MAX` e verifica valore ≈ 3
- [ ] In Parameters → filtra `MPC_Z_VEL_MAX_UP` e `MPC_Z_VEL_MAX_DN` → verificare ≈ 1
- [ ] In Parameters → filtra `MPC_JERK_MAX` e `MPC_JERK_AUTO` → annotare i valori auto-calcolati (per documentare nel `.params` esportato)

---

### A2. Abilitare GPS_DUMP_COMM per il prossimo volo

> Senza il dump UART grezzo del prossimo dropout, ogni ipotesi sulla causa resta speculativa. Questa è la diagnostica più importante.

**Parametro:**

- `GPS_DUMP_COMM = Full communication` (in QGC l'opzione è presentata con il nome, non con un valore numerico) — registra nei file `gps_dump_*.bin` sulla SD tutto il traffico UART in entrambe le direzioni

**Procedura:**

1. [x] In QGC → Parameters → filtro `GPS_DUMP_COMM` → impostato a `Full communication` (2026-05-27)
2. [ ] Verificare che la SD card abbia almeno 500 MB liberi (il dump genera ~1-2 MB/min)
3. [ ] Volare normalmente (con failsafe già riconfigurato come A1)
4. [ ] Al prossimo dropout: estrarre i file dump dalla SD **prima che vengano sovrascritti**
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
| A1 | Modifica parametri failsafe (EKF2_NOAID_TOUT, COM_POSCTL_NAVL, COM_POS_FS_EPH) + limiti velocità/tilt | 🔴 | [x] 2026-05-27 |
| A1-bis | Flight Behavior sliders: Responsiveness 0.5, Horizontal Vel 3 m/s, Vertical Vel 1 m/s | 🔴 | [x] 2026-05-27 |
| A1.test | Test a terra con antenna coperta — verificare comportamento a t=10s | 🔴 | [ ] |
| A2 | Abilitare `GPS_DUMP_COMM = Full communication` | 🔴 | [x] 2026-05-27 |
| A2.bis | Verificare ≥500 MB liberi sulla SD del Pixhawk | 🔴 | [ ] |
| A3 | Volo di test con RTCM disabilitato (diagnostico) | 🔴 | [ ] |
| A4 | Briefing pilota: switch in STABILIZED se vede deriva/perdita quota | 🔴 | [ ] |
| A5 | Export parametri in `maintenance/profili-parametri/volo-2026-05-27.params` | 🔴 | [ ] |
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
