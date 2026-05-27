# Troubleshooting RTK — QGroundControl + PX4

> **Aggiornamento 2026-05-27 — diagnosi del dropout `sensor_gps` confermata.**
>
> L'analisi del 27/05, con `GPS_DUMP_COMM = 1` abilitato per la prima volta, ha identificato la causa primaria dei dropout `sensor_gps` osservati nei voli 26/05 (gap 21.6 s) e moltiplicati nei voli 27/05 (fino a 6 reinit/100 s, BER UART fino al 49 %): si tratta di un **difetto di conduzione intermittente nel cavo GPS auto-costruito**, attivato dalle vibrazioni meccaniche durante il regime di lift dei motori. Il modulo NEO-M8P-0 non perde mai il fix dal proprio lato e PX4 non comanda mai reset al modulo — il problema è esclusivamente sul link UART fisico.
>
> Vedi **[`troubleshooting-gps-dropout-2026-05-27.md`](./troubleshooting-gps-dropout-2026-05-27.md)** per la diagnosi completa e le azioni correttive.
>
> Le sezioni di analisi forense più sotto restano valide come metodologia e timeline degli incidenti del 26/05, ma le **ipotesi sulla causa radice** (firmware HPG 1.40, RTCM malformato, watchdog interno modulo, saturazione UART) sono state tutte **falsificate** dai dati del 27/05.

## Sintomo iniziale

Durante l'atterraggio autonomo, PX4 disattiva l'autopilota con errore `no valid position estimate`. RTK mai arrivato a Fixed: sempre Float.

## Diagnosi

L'errore EKF2 deriva dalla mancanza di un fix RTK affidabile. Indagando:

1. Il messaggio MAVLink `GPS_RTCM_DATA` non compariva nell'Inspector → QGC non stava inviando correzioni al drone.
2. La base RTK è collegata via USB (visibile su `/dev/ttyACM*`).
3. Survey-in convergeva lentamente: dopo 200 s, accuracy ferma a **3.6 m** (necessaria < 2 m, ideale < 1 m).

## Causa radice

Survey-in con accuracy 3.6 m è insufficiente per risolvere le ambiguità di fase intera lato rover → il rover non raggiunge mai RTK Fixed, resta in Float (precisione 20-50 cm) o peggio in SBAS.

La lenta convergenza è quasi sempre dovuta a **multipath** e **vista cielo parziale** sulla base, non al tempo di osservazione (la curva ~1/√t si appiattisce in presenza di bias sistematico).

## Soluzioni

### A. Migliorare il setup della base (soluzione strutturale)

- **Ground plane metallico** sotto l'antenna base (disco alluminio ≥ 10 cm) — riduce multipath del 50-80%.
- Antenna sollevata ≥ 1.5 m da terra, su treppiede.
- Cielo aperto, lontano da edifici/alberi/auto/cavi.
- Lontano da fonti EMI (PC, WiFi, radio) di almeno 2 m.

Target: survey-in < 1 m in 2-3 minuti.

### B. Posizione fissa della base (workaround rapido)

QGC → Application Settings → General → RTK GPS → **Use Specified Base Position**.

- Bypassa il survey-in: rover va a Fixed in 30-60 s.
- L'**altitudine** va inserita come altezza ellissoidica WGS84 (NON quota slm; differenza in Italia ~45-50 m).
- Precisione assoluta limitata dall'errore della posizione data alla base; precisione **relativa** centimetrica → adatto a voli ripetuti dallo stesso punto.

### Configurazione QGC raccomandata

- Accuracy survey-in: **1.0 m**
- Min Duration: **300 s**

## Parametri PX4 rilevanti

- `EKF2_GPS_CTRL` — bitmask, default 7 ok
- `EKF2_HGT_REF` — impostare a `GPS` (1) per atterraggi di precisione con RTK
- `EKF2_REQ_EPH`, `EKF2_REQ_EPV`, `EKF2_REQ_SACC` — soglie minime accettazione GPS dall'EKF
- `GPS_UBX_DYNMODEL` = 7 (airborne <2g) per u-blox

---

## Secondo modo di guasto: buco di pubblicazione `sensor_gps` → degradazione EKF → quasi-schianto

**Log di riferimento** `log/2026-05-26/10_54_52.ulg` (analisi diretta dall'ulg).

### Sintomi nel log di QGC

```
1:24:07.708  [commander] Armed by external command
1:24:09.728  [commander] Takeoff detected
1:24:37.742  [commander] Pilot took over using sticks
1:24:40.687  [mc_pos_control] invalid setpoints
1:24:40.687  [mc_pos_control] Failsafe: blind land
1:24:40.795  [failsafe] Failsafe activated
1:24:45.731  [gps] ubx msg 0x0103 invalid len 7416
1:24:46.009  [gps] u-blox firmware version: HPG 1.40ROV
1:24:46.019  [gps] u-blox protocol version: 20.30
1:24:46.029  [gps] u-blox module: NEO-M8P-0
1:25:11.016  [commander] Landing detected
1:25:13.023  [commander] Disarmed by landing
1:25:13.023  [health_and_arming_checks] Preflight Fail: Strong magnetic interference
```

### Timeline puntuale ricostruito dai topic uORB

| Wall-clock | PX4 ts | EKF `pos_horiz_accuracy` | I motori (somma 6 ESC) | `nav_state` | Evento |
|---|---|---|---|---|---|
| 1:24:36.73 | **1475.667** | 0.229 m | 18.7 A | AUTO_MISSION | **Ultimo `sensor_gps` pubblicato** |
| 1:24:37.74 | 1477.742 | 0.500 m | 19.0 A → 14.2 A | AUTO_MISSION → POSCTL | Pilot took over (**+2.07 s** dal gap) |
| 1:24:40.69 | 1480.687 | 1.236 m | 18.5 A | POSCTL | `invalid setpoints` → blind land |
| 1:24:40.80 | 1480.795 | 1.236 m | 18.5 A | POSCTL → ALTCTL | Failsafe attivato (`cs_gnss_pos=0` a ts=1482.68) |
| 1:24:45.73 | 1485.731 | 3.97 m | 18.7 A | ALTCTL | Driver rileva `ubx invalid len` (**+10 s** dal gap) |
| 1:24:46.03 | 1486.029 | 4.45 m | 18.6 A | ALTCTL | Driver completa CFG-RST + MON-VER |
| 1:24:47.5 | 1487.5 | 5.5 m | **47.5 A** picco | ALTCTL | Pilota dà throttle massimo (drone in deriva orizzontale a 2 m/s) |
| 1:24:48.5 | 1488.5 | 7.1 m | **43.6 A** picco | ALTCTL | Seconda manovra evasiva |
| 1:24:59.32 | **1497.276** | 19.36 m | 19.5 A | ALTCTL | **Primo `sensor_gps` di nuovo valido** (gap = 21.61 s) |
| 1:24:59.4 | 1498.3 | 0.58 m | 19.7 A | ALTCTL → POSCTL → AUTO_PRECLAND | `cs_gnss_pos=1`, EKF riallinea |
| 1:25:11.02 | 1511.016 | 0.24 m | landing | LAND | Atterraggio |

### Cosa dicono i dati — ipotesi falsificate

**❌ Sag di alimentazione**
- `system_power.voltage5v_v` oscilla normalmente 5.04-5.24 V per tutto il volo, inclusi i 22 s del gap. Minimo 5.016 V (transitorio normale del BEC).
- `sensors3v3[0..3]` stabili a 3.26-3.31 V.
- **Il NEO-M8P è sempre stato in spec.** Non è un brown-out.

**❌ EMI radiato/conduttivo da motori in transitorio**
- All'istante dell'ultimo `sensor_gps` (ts=1475.667) la corrente totale motori è **18.7 A**, perfettamente in hover steady-state da 30 s. Nessun transitorio.
- `sensor_mag[0]` norm: **std=0.016 G** nei 25 s prima del gap, identico al baseline.
- I picchi di corrente 47 A e 43 A (con conseguenti spike EMI) sono arrivati **12-13 s DOPO** la fine del GPS — sono conseguenza delle manovre evasive del pilota, non causa.

**❌ Manovra del pilota come trigger**
- Il pilota ha preso i comandi a ts=1477.742, cioè **2.07 s DOPO** che `sensor_gps` aveva smesso di pubblicare. In quei 2 s l'EKF era già passato da 0.229 a 0.500 m di accuracy. Il pilota ha **reagito** al degrado visibile in QGC, non lo ha causato.

**❌ Guasto definitivo del modulo**
- `fix_type` ritorna a **5 (RTK Float)** sia prima sia dopo il reset. Il modulo non si è mai guastato: ha continuato a vedere 15 satelliti, eph 1-2 cm. Il flusso UART tra modulo e Pixhawk si è solo **interrotto in trasmissione** per 22 s.

### Pattern confermato su un secondo log

Lo stesso pattern si è verificato in un volo precedente, `log/2026-05-26/10_45_41.ulg`, con condizioni operative diverse (AUTO_RTL "land at destination" in discesa a 2.4 m/s, non hover):

- Modulo NEO-M8P-0 / firmware HPG 1.40ROV
- 5 V rail stabile (5.07-5.20 V) all'istante del gap
- Magnetometro **più stabile del baseline** (std 0.018 G vs 0.030 G) all'istante del gap
- Corrente motori 15.7 A all'istante del gap (regime discesa controllata)
- Fix_type=5 (RTK Float) sia prima sia dopo
- Stesso messaggio `[gps] ubx msg 0x0103 invalid len` (con valore garbage diverso: 64528 vs 7416)
- Stesso trio `firmware version / protocol / module` post-reinit

**Dato killer: durata del gap praticamente identica al centesimo.**

| Log | Inizio gap (ts) | Fine gap (ts) | Durata |
|---|---|---|---|
| 10_45_41 | 950.674 | 972.279 | **21.605 s** |
| 10_54_52 | 1475.667 | 1497.276 | **21.609 s** |

Differenza 4 ms. Un guasto meccanico (connettore intermittente) avrebbe durate stocastiche; un'EMI ambientale altrettanto. **Una durata identica al centesimo in due voli diversi indica un comportamento deterministico** — o un watchdog interno al modulo, o un timeout/sequenza deterministica del driver PX4.

In più, in `10_45_41` il driver fa **3 reset consecutivi** (ts 961, 971, 987) — è il pattern di un driver che entra in uno stato di re-inizializzazione e fa ciclo di auto-detection.

---

### Cosa abbiamo verificato direttamente sul codice e sui documenti ufficiali

> ⚠️ Le ipotesi sulla causa radice vanno presentate per quello che sono: **ipotesi**. Le seguenti verifiche servono a delimitare cosa è documentato vs cosa è congettura.

#### Sul driver GPS di PX4 ([fonte 1, fonte 2])

I timeout dichiarati nel codice (`PX4-Autopilot/src/drivers/gps/gps.cpp` e `PX4-GPSDrivers/src/gps_helper.h`):

| Costante | Valore | Quando si applica |
|---|---|---|
| `TIMEOUT_5HZ` | 500 ms (+ 300 ms margine) | Driver healthy, rate 5 Hz |
| `TIMEOUT_1HZ` | 1300 ms | Driver healthy, rate 1 Hz |
| `TIMEOUT_INIT_5HZ` | 1500 ms | Durante init, rate 5 Hz |
| `TIMEOUT_INIT_1HZ` | 3900 ms | Durante init, rate 1 Hz |
| `TIMEOUT_DUMP_ADD` | +450 ms | Se logging RTCM3 attivo |

**Nessun timeout interno da 21.6 s esiste nel codice.** Il driver non triggera automaticamente un `CFG-RST` lato modulo dopo silenzio: alla scadenza del timeout chiude la UART, marca `_healthy = false`, e re-entra nel loop di configurazione. Il `CFG-RST` + `MON-VER` visibili nel log sono parte della **sequenza di re-init del driver PX4**, non un comando applicato al modulo dopo un evento interno u-blox.

L'auto-detection cicla i baudrate (9600/19200/38400/57600/115200/230400) e per ciascuno tenta `configure()` con ACK su CFG-PRT/CFG-MSG/CFG-RATE. Il tempo totale di questa sequenza dipende dal numero di baud falliti prima di trovare quello giusto; può facilmente arrivare a decine di secondi se il modulo non risponde subito.

#### Sul firmware u-blox NEO-M8P ([fonte 3, fonte 4])

- **L'ultimo firmware ufficiale per NEO-M8P è HPG 1.43** (FW 3.05, release 10 gennaio 2022, file `UBX_M8_305_HPG_143_ROVER.bin`).
- **Non esiste alcun "HPG 1.50"** (il riferimento in versioni precedenti di questo documento era errato).
- Le release notes di HPG 1.43 documentano due soli miglioramenti funzionali rispetto a HPG 1.40:
  1. *Improved MSM correction stream handling* (stream MSM che includono messaggi non supportati o SBAS).
  2. *Improved M8P base station BDS D2 encoding* (BeiDou GEO).
- **Nessun fix esplicito** su PVT output stall, UART stall, RTK Float dropout, o re-inizializzazione del modulo.
- L'unica *known limitation* affine in HPG 1.43 riguarda mix di correzioni GLONASS con cambio di reference station ID + data outage → genera **errori di posizione**, non interruzione della pubblicazione UBX per 21 s.

Conclusione: la frase *"HPG 1.40 ha bug documentati di PVT output stall in RTK Float con RTCM in ingresso"* non è confermata dalla documentazione u-blox ufficiale disponibile. È un'ipotesi plausibile ma non un fatto verificato.

### Ipotesi sulla causa radice — riordinate per evidenza

> Tutte ipotesi non ancora confermate. Solo nuovi voli con `GPS_DUMP_COMM = 3` possono discriminarle.

1. **🟡 Watchdog interno al firmware u-blox**
   Il modulo potrebbe entrare in uno stato (es. per RTCM malformata, race condition in HPG 1.40, buffer interno saturato) da cui esce dopo un timeout interno fisso. Un watchdog hardware u-blox spiegherebbe la durata identica al centesimo. **Non documentato pubblicamente**, ma compatibile con i dati.

2. **🟡 Tempo deterministico della sequenza di re-init del driver PX4**
   La sequenza chiude UART → cicla baud → configure → primo `sensor_gps` valido può richiedere un tempo riproducibile. Tuttavia il driver inizia il ciclo solo **dopo** aver dichiarato `_healthy = false` (≤ 1.5 s dal silenzio), quindi questa ipotesi spiega al massimo gli ultimi ~15-20 s, non l'intervallo completo di 21.6 s a partire dall'ultimo PVT.

3. **🟡 Saturazione UART 38400 baud**
   PVT 5 Hz + UBX-RXM-RAWX + RTCM in ingresso sulla stessa UART a 38400 baud è vicino al limite di throughput. Un buffer overrun lato modulo (TX) o lato Pixhawk (RX) può desincronizzare il parser. Mitigazione naturale: alzare a 115200.

4. **🟢 Falso contatto su connettore JST-GH GPS** (precedentemente prima ipotesi)
   Declassata: improbabile dato il timing rigorosamente fisso (21.605 vs 21.609 s) — un connettore intermittente avrebbe durate stocastiche. Da ispezionare comunque per esclusione.

### Perché questo guasto ha quasi fatto schiantare il drone

Il **dropout GPS in sé non è l'emergenza**. L'emergenza l'ha creata la **logica di failsafe**:

1. PX4 ha triggerato `mc_pos_control: invalid setpoints` quando l'EKF ha marcato `xy_valid = false` (3-5 s dopo l'inizio del gap, allo scadere di `EKF2_NOAID_TOUT` che era al default 5 s).
2. `mc_pos_control` ha applicato il suo **blind-land interno** → in `10_54_52` il drone è passato in **ALTCTL**, in `10_45_41` è andato in **DESCEND** (nav_state=12) → entrambe modalità **senza controllo orizzontale**.
3. In 10-15 s il drone è derivato di 15 m orizzontalmente (velocità 2-3 m/s) — il pilota ha dovuto contro-attaccare per evitare lo schianto.

### Architettura failsafe a due livelli — correzione importante (2026-05-27)

> ⚠️ Durante l'applicazione delle modifiche failsafe abbiamo scoperto che la diagnosi iniziale era incompleta. Verifica sui parametri del Pixhawk: `COM_POSCTL_NAVL` era **già a `Altitude`** prima degli incidenti, eppure il blind-land è scattato lo stesso. Significa che la modifica del solo failsafe commander non basta.

PX4 ha due livelli di failsafe sovrapposti sulla perdita di posizione:

| Livello | Modulo | Logica | Parametro principale |
|---|---|---|---|
| **Alto (commander)** | `commander` | "La posizione è persa, applico la policy" | `COM_POSCTL_NAVL`, `COM_POS_FS_EPH` |
| **Basso (controller)** | `mc_pos_control` | "Non ricevo setpoint validi, non posso fare controllo orizzontale, atterro" | Hard-coded (blind-land verticale) |

Il livello basso **scavalca** quello alto: se `mc_pos_control` decide che i setpoint sono invalidi (perché l'EKF ha marcato `xy_valid = false`), triggera il blind-land **prima** che il commander possa applicare `COM_POSCTL_NAVL`.

Il vero gating per quanto a lungo l'EKF tollera l'assenza di GPS è **`EKF2_NOAID_TOUT`** (default 5 s, cap firmware **10 s**). Dopo questo tempo l'EKF dichiara `xy_valid = false` e `mc_pos_control` interviene.

#### Conseguenze pratiche con configurazione attuale

- Cap firmware `EKF2_NOAID_TOUT = 10 s` significa che **non possiamo coprire l'intero gap di 21.6 s**. Resta una finestra di ~11.6 s in cui il failsafe scatterà comunque.
- Al prossimo dropout, attorno a t = 10 s scatterà o il blind-land di `mc_pos_control` **oppure** il commander con `COM_POSCTL_NAVL = Altitude` — quale dei due vince la race condition è da verificare empiricamente col test a terra (foglio di alluminio sull'antenna).
- Mitigazioni residue applicate: velocità ridotte (5 m/s vs 10) → meno inerzia → drift orizzontale dimezzato durante gli ~11.6 s scoperti.
- **Rete di sicurezza finale**: il pilota deve essere briefato a flippare immediatamente in **STABILIZED** se vede deriva o perdita di quota anomala. STABILIZED bypassa l'intero stack failsafe PX4 e dà controllo manuale puro.

### Spiegazione dei picchi di corrente (47 A in 10_54_52, 28 A in 10_45_41)

I picchi NON sono transitorio motore "anomalo" come ipotizzato inizialmente. Sono la **conseguenza meccanica del pilota che reagisce a un drone fuori controllo**.

Sequenza in `10_54_52` intorno a ts=1487.5-1488.5:
- Drone in ALTCTL, in deriva orizzontale a 2 m/s, già sceso di 6 m sotto il punto di hover
- Pilota porta throttle a +1.0 → tutti e 6 i motori vanno al 100% di duty cycle (`actuator_motors.control[i] = 1.0`)
- Con batteria 4S ~15.7 V e 6 motori in saturazione: **picco istantaneo 47.5 A**
- 1 s dopo (ts=1488): pilota inverte (drone sale troppo) → throttle a 0 → corrente crolla a **7.1 A**
- Subito dopo (ts=1488.5): pilota dà di nuovo throttle → **43.6 A**
- È **Pilot-Induced Oscillation (PIO) classico**: corregge eccessivamente perché ha perso riferimento spaziale stabile

In `10_45_41` il picco è più contenuto (28.8 A) perché il drone era già in modalità AUTO_LAND (failsafe gestiva ancora un minimo di controllo verticale) e il pilota non ha potuto bypassarla con stick override (in DESCEND failsafe gli stick PX4 sono molto attenuati).

**Il quasi-schianto e i picchi di corrente sono entrambi causati dalla logica di failsafe sbagliata, non dal modulo GPS.** Il modulo GPS è il trigger originale, ma è la catena di reazioni (failsafe → deriva → PIO → saturazione motore) a generare il rischio reale.

### Azioni prioritarie (dettagli completi in [`azioni-pre-prossimo-volo.md`](./azioni-pre-prossimo-volo.md))

1. **🔴 [APPLICATO 2026-05-27] Riconfigurare failsafe perdita posizione**. La modifica chiave si è rivelata `EKF2_NOAID_TOUT` (cap a 10 s), non solo `COM_POSCTL_NAVL` come ipotizzato inizialmente. Più limiti di velocità/tilt per ridurre la deriva nei ~11.6 s residui scoperti.
2. **🔴 [APPLICATO 2026-05-27] Abilitare `GPS_DUMP_COMM = Full communication`** per registrare il traffico UART grezzo. Senza il dump del prossimo dropout, tutte le ipotesi sulla causa restano speculative.
3. **🔴 Test a terra con foglio di alluminio sull'antenna GPS** (eliche RIMOSSE) per verificare empiricamente cosa scatta a t = 10 s: blind-land di `mc_pos_control` o commander Altitude.
4. **🔴 Volo di test con `Use RTK = off`** (RTCM disabilitata da QGC). Se il dropout sparisce → causa nel flusso RTCM/firmware; se rimane → causa altrove.
5. **🟡 Aggiornare firmware u-blox a HPG 1.43** (precauzionale: nessun fix specifico documentato, ma comunque l'ultima release stabile).
6. **🟡 Alzare baud-rate UART GPS da 38400 a 115200** per ridurre rischio saturazione.
7. **🟡 Aggiornare PX4** alla release stable corrente.
8. **🟢 Ispezione connettore JST-GH GPS** (per esclusione).
9. **🟢 Mitigazioni EMI** (ferrite clip, separazione cavi).

## Da fare

- [ ] Test con ground plane sotto antenna base (per il problema RTK Fixed, non per il dropout)
- [ ] Verifica costellazioni attive sulla base (GPS+GLONASS+Galileo)
- [ ] Decidere tra soluzione A (operativa) o B (punto fisso laboratorio)
- [ ] Formalizzare procedura pre-volo RTK in checklist dedicata
- [ ] Aggiungere modo di guasto in FMEA: "Survey-in base RTK non converge → degradazione posizione → abort missione in landing"
- [ ] Aggiungere modo di guasto in FMEA: "Dropout UART GPS → EKF dead-reckoning → failsafe blind-land in ALTCTL → deriva orizzontale incontrollata"
- [x] Analisi diretta dei due ulg incidente (`10_45_41` e `10_54_52`)
- [ ] **PRIMA DEL PROSSIMO VOLO**: applicare almeno le azioni 🔴 della checklist sopra

## Riferimenti

- [PX4 RTK GPS docs (main)](https://docs.px4.io/main/en/advanced/rtk_gps.html)
- Flight Review (analisi log): https://logs.px4.io
- Messaggi RTCM3 minimi per F9P: 1005, 1077, 1087, 1097, 1127, 1230
- **[fonte 1]** [Sorgente `gps.cpp` (PX4-Autopilot main)](https://github.com/PX4/PX4-Autopilot/blob/main/src/drivers/gps/gps.cpp) — timeout `TIMEOUT_5HZ = 500 ms`, `TIMEOUT_INIT_5HZ = 1500 ms`, logica di re-init dopo `receive() ≤ 0`
- **[fonte 2]** [Sorgente `ubx.cpp` (PX4-GPSDrivers main)](https://github.com/PX4/PX4-GPSDrivers/blob/main/src/ubx.cpp) — parser UBX, generazione del messaggio "ubx msg 0xXXXX invalid len" quando il payload non rispetta la lunghezza attesa
- **[fonte 3]** [Release note u-blox HPG 1.43 (UBX-21035325, gennaio 2022)](https://content.u-blox.com/sites/default/files/NEO-M8P_FW305-RTK143_RN_UBX-21035325.pdf) — ultima versione firmware per NEO-M8P; bugfix limitati a gestione MSM e BDS D2; nessun fix per stall PVT/UART
- **[fonte 4]** [Release note u-blox HPG 1.40 (UBX-17021504, 2018)](https://content.u-blox.com/sites/default/files/NEO-M8P-FW301-HPG140_RN_(UBX-17021504).pdf) — versione attualmente flashata sul Here+
- [Pagina prodotto u-blox NEO-M8P](https://www.u-blox.com/en/product/neo-m8p-series)
- [PR PX4-GPSDrivers #109 — RTK→DGNSS timeout](https://github.com/PX4/PX4-GPSDrivers/pull/109) — discussione su gestione del timeout RTCM in PX4
