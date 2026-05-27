# Azioni correttive pre-prossimo volo

> Checklist delle attività da completare **prima del prossimo volo** del F550.
>
> Origine: due incidenti del 2026-05-26 (log `10_45_41.ulg` e `10_54_52.ulg`), aggiornato il 2026-05-27 dopo la **diagnosi definitiva** della causa dei dropout GPS.
>
> Riferimenti diagnostici:
> - [`troubleshooting-gps-dropout-2026-05-27.md`](./troubleshooting-gps-dropout-2026-05-27.md) — **diagnosi confermata** del 27/05 (causa: cavo GPS difettoso)
> - [`troubleshooting-rtk.md`](./troubleshooting-rtk.md) — analisi forense incidente 26/05

## Riepilogo del problema (aggiornato al 2026-05-27)

I dropout `sensor_gps` osservati nei voli 26/05 (singolo gap 21.6 s) e nei voli 27/05 (fino a 6 gap in 100 s, BER UART fino al 49 %) hanno la **stessa causa primaria**, ora identificata grazie all'abilitazione di `GPS_DUMP_COMM = 1` e all'analisi degli 11 log della giornata 27/05:

> **Causa radice**: difetto di conduzione **intermittente** nel cavo GPS auto-costruito, attivato dalle vibrazioni meccaniche durante il regime di lift dei motori.

Evidenze chiave (dettagli completi in [`troubleshooting-gps-dropout-2026-05-27.md`](./troubleshooting-gps-dropout-2026-05-27.md)):

- Il modulo NEO-M8P-0 non perde mai il fix (sempre RTK Float a 15 sat quando pubblica).
- PX4 non comanda mai reset al modulo (nessun `CFG-RST` trasmesso); fa solo auto-baud probing dopo timeout 800 ms.
- Metriche RF (`noise_per_ms`, `jamming_indicator`, `agc`) costanti prima/durante/dopo i gap.
- **BER UART modulato dal regime motori**: 0.2 % a motori in idle, fino al 49 % a motori in lift, a parità di tutto il resto.
- BER oscillante violentemente tra voli consecutivi (0.2 % vs 49 %) con stessi parametri: firma di un **difetto meccanico intermittente** dipendente dalla geometria con cui si posa il cavo.

Il dropout in sé non è l'emergenza primaria: lo è la reazione del failsafe (`mc_pos_control: Failsafe: blind land`) che mette il drone in modalità senza controllo orizzontale → deriva libera. Entrambi gli aspetti vanno corretti:

1. **Sostituzione/riparazione del cavo GPS** — elimina la causa radice (sezione A0 sotto).
2. **Riconfigurazione failsafe perdita posizione** — proteggere comunque dallo schianto in caso di dropout futuri (sezione A1).

---

## 🔴 CRITICO — da completare prima di QUALSIASI volo

### A0. Cavo GPS — ricontrollo, ricostruzione, schermatura

> **Causa radice identificata.** Senza questa azione il problema rimane, qualunque parametro PX4 o firmware modulo si modifichi. Vedi [`troubleshooting-gps-dropout-2026-05-27.md`](./troubleshooting-gps-dropout-2026-05-27.md) per la diagnosi.

#### A0.1 Ispezione preliminare (test "wiggle")

Test di continuità intermittente — l'obiettivo è riprodurre a banco il difetto che in volo si attiva con la vibrazione.

- [ ] Smontare il cavo GPS dal drone (lato Pixhawk **e** lato modulo).
- [ ] Multimetro in modalità continuità acustica (cicalino).
- [ ] Per ciascun conduttore (TX, RX, GND, e gli altri pin di servizio): tenere i puntali sui due capi e **piegare/torcere/flettere il cavo lentamente lungo tutta la sua lunghezza**, cercando interruzioni.
- [ ] Stessa cosa con il cavo connesso ai due connettori JST: muovere/tirare lievemente i singoli pin lato connettore — un crimping marginale si rivela come perdita di continuità sotto sollecitazione.
- [ ] Annotare quale conduttore mostra l'interruzione e in che punto (zona connettore A, zona centrale, zona connettore B).

> Se il test wiggle riproduce l'interruzione: causa confermata, procedere a A0.2.
> Se non la riproduce: la marginalità può attivarsi solo a vibrazione di banda larga — il difetto è comunque dimostrato dai log, procedere a A0.2 indipendentemente.

#### A0.2 Ricostruzione del cavo

- [ ] Procurarsi materiale:
  - **Cavo multipolare** ≥ 6 conduttori AWG 26-28, lunghezza minima necessaria (≤ 25 cm).
  - **Treccia di schermatura** (calza in rame stagnato) o cavo già schermato di partenza.
  - Connettori **JST-GH** del passo corretto (verificare numero pin lato Pixhawk e lato modulo NEO-M8P-0).
  - Pin femmina pre-crimpati o crimpatrice JST-GH dedicata (le pinze generiche danneggiano il pin).
  - Termorestringente, **drain wire** per scaricare la schermatura.
- [ ] **Crimpare** i pin, verificarne la tenuta con tirata leggera prima dell'inserimento nell'housing JST.
- [ ] Inserire i pin nell'housing — il click di fondo corsa deve essere netto. Test trazione su ciascun pin.
- [ ] **Saldatura solo dove necessaria**: se si fanno giunzioni intermedie evitare saldature fredde — preparare il filo (twist + pre-stagno), applicare flux, tempo di contatto minimo con la punta calda; verificare che il pad finale sia lucido (non opaco/granuloso → indica saldatura fredda).
- [ ] **Schermatura**: avvolgere la treccia su tutta la lunghezza utile, **collegare il drain wire al GND solo lato Pixhawk** (single-ended) per evitare ground-loop.
- [ ] Termorestringente sopra alla schermatura per protezione meccanica e fissaggio.

#### A0.3 Test di accettazione del nuovo cavo (a banco, eliche RIMOSSE)

> Replicare la condizione discriminante del log `13_50_41` vs `13_50_52`: stesso drone, motori prima in idle poi in regime di lift, monitorando il BER UART tramite il dump GPS.

- [ ] Mantenere `GPS_DUMP_COMM = 1`.
- [ ] Drone all'aperto, fix GPS acquisito, armato in POSCTL.
- [ ] **Fase 1 — idle, 60 s**: motori al minimo (post-arming, senza throttle).
- [ ] **Fase 2 — regime lift, 60 s**: throttle ~50 % (eliche rimosse, regime equivalente a hover) — drone fissato/zavorrato.
- [ ] **Fase 3 — torsione del cavo, 60 s**: mantenendo regime lift, applicare manualmente piegature/torsioni controllate al cavo per replicare il test wiggle in dinamica.
- [ ] Disarmare. Estrarre il `.ulg` ed eseguire l'analisi `gps_dump`:

```bash
python3 plot/info_log.py log/<data>/<orario>.ulg   # (oppure script analogo)
# verificare: garbage_pct < 0.5%, CRC fail = 0, NAV-PVT rate ≥ 4.9 Hz, 0 reinit driver
```

**Esito atteso (cavo OK):** garbage RX < 0.5 %, zero reinit del driver, NAV-PVT a 5 Hz in tutte le 3 fasi. Se anche solo una fase mostra BER > 1 %, il cavo va rifatto.

#### A0.4 Instradamento e fissaggio

- [ ] Cavo GPS instradato sul lato **opposto** del telaio rispetto ai fasci ESC-motore (separazione fisica ≥ 5 cm dove possibile).
- [ ] Nessun loop libero che possa muoversi in volo → fissare con fascette dolci o velcro a punti strutturali del frame.
- [ ] Connettore JST sul Pixhawk: **hot-glue** a basso volume sul corpo del connettore per impedire micro-spostamenti da vibrazione.
- [ ] Stessa cosa lato modulo se il connettore è esposto a vibrazione del mast.

#### A0.5 Volo di accettazione

- [ ] Volo breve (3-5 min) in POSCTL, hover line-of-sight, pilota pronto allo switch in STABILIZED.
- [ ] Mantenere `GPS_DUMP_COMM = 1` per validazione.
- [ ] Analisi `.ulg` post-volo: garbage RX < 1 %, zero reinit driver, nessun gap `sensor_gps` > 2 s.
- [ ] **Solo dopo questo volo OK**: il cavo è considerato a posto e si può tornare ad attività operative.

---

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

### A2. ~~Abilitare GPS_DUMP_COMM per il prossimo volo~~ ✅ COMPLETATO — diagnosi raggiunta

> `GPS_DUMP_COMM = 1` è stato abilitato il 2026-05-27 e ha permesso di identificare la causa primaria. Il dump va **mantenuto attivo** anche nei test del nuovo cavo (sezione A0.3, A0.5) per validare quantitativamente il BER UART.

- [x] `GPS_DUMP_COMM = 1` impostato (Full communication, RX+TX)
- [x] Analisi degli 11 log della giornata 27/05 completata → causa identificata nel cavo GPS
- [x] Documento diagnostico [`troubleshooting-gps-dropout-2026-05-27.md`](./troubleshooting-gps-dropout-2026-05-27.md) prodotto
- [ ] **Mantenere `GPS_DUMP_COMM = 1` attivo fino alla validazione del nuovo cavo** (A0.5 OK)
- [ ] Solo dopo validazione del cavo, **disabilitare** (`GPS_DUMP_COMM = 0`) per alleggerire il logging in operativo

---

### A3. ~~Volo di test con RTCM disabilitato (diagnostico)~~ ⊘ NON PIÙ NECESSARIO

> Era un test per discriminare l'ipotesi "il flusso RTCM mette il modulo in stato anomalo". La diagnosi del 27/05 ha escluso questa ipotesi: il problema è fisico, sul cavo, non sul protocollo. **Saltare questa azione.**

---

## 🟡 IMPORTANTE — mitigazioni precauzionali

> **Nota dopo diagnosi del 27/05**: le azioni B1, B2, B3 erano state pianificate quando la causa radice non era ancora identificata e si sospettava un problema firmware/protocollo. Ora che la causa è confermata nel cavo (A0), queste azioni **non sono più necessarie per risolvere i dropout**; restano però buone pratiche di igiene/aggiornamento e vanno eseguite quando comodo, **non bloccanti per i prossimi voli**.

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

### C1. ~~Ispezione meccanica connettori GPS~~ → assorbito in A0

> Le attività di questa sezione sono ora **incorporate** nella ricostruzione del cavo (A0). L'hot-glue dei connettori è in A0.4.

---

### C2. ~~Mitigazioni EMI (preventive)~~ → schermatura assorbita in A0, separazione fisica in A0.4

> La schermatura del cavo (treccia + drain wire) è in A0.2; la separazione fisica dai cavi motore è in A0.4. Ferrite clip resta opzionale come ulteriore protezione, da valutare solo se il volo di accettazione A0.5 mostra ancora margini bassi.

- [ ] (Opzionale) **Ferrite clip** sul cavo GPS in prossimità del connettore Pixhawk — solo se A0.5 mostra BER residuo > 0.5 % a regime di lift.

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

Dopo aver completato A0 (cavo) e A1 (failsafe):

1. [ ] **Test wiggle + accettazione cavo a banco** (A0.1, A0.3) — verifica BER UART < 0.5 % a regime di lift
2. [ ] **Test parametri failsafe**: ripetere A1 step di verifica (alluminio sull'antenna a terra)
3. [ ] **Verificare GPS_DUMP_COMM = 1** attivo durante i voli di validazione
4. [ ] **Volo di accettazione cavo** (A0.5): hover manuale (POSCTL) in line-of-sight, 3-5 min, pilota pronto a switch in STABILIZED
5. [ ] **Solo dopo successo A0.5**: tornare a missioni con landing autonomo e RTK attivo
6. [ ] Una volta validato il cavo: **disabilitare** `GPS_DUMP_COMM = 0` per i voli operativi

Per ogni volo di verifica, analizzare il `.ulg` con script in `plot/` per confermare:
- Nessun gap in `sensor_gps.timestamp` > 2 s
- `pos_horiz_accuracy` resta sotto 1 m per tutta la missione
- Nessun reset driver nei `logged_messages` (assenza di "u-blox firmware version" durante il volo)
- Analisi `gps_dump`: garbage RX < 0.5 %, CRC fail = 0, NAV-PVT rate ≈ 5 Hz

---

## Checklist riepilogativa stampabile

| # | Azione | Priorità | Stato |
|---|---|---|---|
| **A0.1** | **Test wiggle multimetro su cavo GPS attuale** | 🔴 | **[ ]** |
| **A0.2** | **Ricostruzione cavo GPS con schermatura (treccia + drain wire)** | 🔴 | **[ ]** |
| **A0.3** | **Test a banco nuovo cavo: idle + lift + torsione, verifica BER < 0.5%** | 🔴 | **[ ]** |
| **A0.4** | **Instradamento + hot-glue connettori + separazione cavi motore** | 🔴 | **[ ]** |
| **A0.5** | **Volo di accettazione 3-5 min, verifica zero reinit driver** | 🔴 | **[ ]** |
| A1 | Modifica parametri failsafe (EKF2_NOAID_TOUT, COM_POSCTL_NAVL, COM_POS_FS_EPH) + limiti velocità/tilt | 🔴 | [x] 2026-05-27 |
| A1-bis | Flight Behavior sliders: Responsiveness 0.5, Horizontal Vel 3 m/s, Vertical Vel 1 m/s | 🔴 | [x] 2026-05-27 |
| A1.test | Test a terra con antenna coperta — verificare comportamento a t=10s | 🔴 | [ ] |
| A2 | Abilitare `GPS_DUMP_COMM = Full communication` + analisi dump | 🔴 | [x] 2026-05-27 (diagnosi raggiunta) |
| A2.bis | Verificare ≥500 MB liberi sulla SD del Pixhawk | 🔴 | [ ] |
| A3 | ~~Volo di test con RTCM disabilitato~~ | ⊘ | obsoleto (diagnosi raggiunta) |
| A4 | Briefing pilota: switch in STABILIZED se vede deriva/perdita quota | 🔴 | [ ] |
| A5 | Export parametri in `maintenance/profili-parametri/volo-2026-05-27.params` | 🔴 | [ ] |
| B1 | Aggiornamento firmware u-blox HPG 1.40 → **1.43** | 🟡 | [ ] non bloccante (era ipotesi falsificata) |
| B2 | Alzare baud-rate UART GPS a 115200 | 🟡 | [ ] non bloccante |
| B3 | Aggiornamento PX4 alla release stable corrente | 🟡 | [ ] non bloccante |
| B4 | Stress test 5 min motori armati a terra | 🟡 | [ ] (sovrapponibile a A0.3) |
| C1 | ~~Ispezione + hot-glue connettori GPS~~ | ⊘ | assorbito in A0.4 |
| C2 | ~~Ferrite clip + separazione fisica cavi~~ | ⊘ | schermatura in A0.2, separazione in A0.4 |
| D1 | Installazione secondo GPS M9N (GPS2) | 🟢 | [ ] ridondanza per sicurezza futura |
| D2 | Pianificazione upgrade a ZED-F9P | 🟢 | [ ] lungo termine |

---

## Riferimenti

- [`troubleshooting-gps-dropout-2026-05-27.md`](./troubleshooting-gps-dropout-2026-05-27.md) — **diagnosi completa** del 27/05 con analisi di tutti gli 11 log della giornata e identificazione del cavo come causa radice
- [`troubleshooting-rtk.md`](./troubleshooting-rtk.md) — analisi forense incidente 2026-05-26 (compatibile con la nuova diagnosi)
- [`troubleshooting-gps-pixhawk6x.md`](./troubleshooting-gps-pixhawk6x.md) — problemi GPS precedenti (riconoscimento modulo, configurazione GPS_1_CONFIG)
- [`test-a-banco.md`](./test-a-banco.md) — procedure di sicurezza per test indoor con bypass arming
- [`stato-lavori.md`](./stato-lavori.md) — tracking generale delle attività di commissioning
- Log analizzati 2026-05-26: `10_45_41.ulg`, `10_54_52.ulg`
- Log analizzati 2026-05-27: tutti gli 11 voli (`13_40_57.ulg` … `14_15_52.ulg`)

### Fonti verificate

- [PX4 Failsafe parameters (main)](https://docs.px4.io/main/en/config/safety.html)
- [PX4 GPS parameters (`GPS_DUMP_COMM`)](https://docs.px4.io/main/en/advanced_config/parameter_reference.html#GPS_DUMP_COMM)
- [Sorgente driver GPS PX4 (`gps.cpp`)](https://github.com/PX4/PX4-Autopilot/blob/main/src/drivers/gps/gps.cpp) — timeout effettivi del driver
- [Release note u-blox HPG 1.43 (UBX-21035325, 10 gen 2022)](https://content.u-blox.com/sites/default/files/NEO-M8P_FW305-RTK143_RN_UBX-21035325.pdf) — bugfix limitati a MSM e BDS D2; nessun fix UART/PVT stall documentato
- [Release note u-blox HPG 1.40 (UBX-17021504, 2018)](https://content.u-blox.com/sites/default/files/NEO-M8P-FW301-HPG140_RN_(UBX-17021504).pdf) — versione attualmente flashata
- [Pagina prodotto u-blox NEO-M8P (EOL)](https://www.u-blox.com/en/product/neo-m8p-series)
- [u-center download](https://www.u-blox.com/en/product/u-center)
