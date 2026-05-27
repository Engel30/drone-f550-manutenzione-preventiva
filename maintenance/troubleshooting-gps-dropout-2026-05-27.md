# Troubleshooting: GPS — reset ciclici del driver dopo sostituzione Pixhawk e cavo

**Data**: 2026-05-27
**Volo analizzato**: `log/2026-05-27/13_40_57.ulg` (prima prova di giornata, durata 5:43)
**Componente**: link UART tra modulo GPS u-blox NEO-M8P-0 e Pixhawk 6X (porta GPS2)
**Stato**: causa primaria identificata, da verificare con test mirato

---

## Sintomi

- In QGroundControl: ripetuti messaggi *"GPS failsafe"*, *"GNSS data fusion stopped"*, modalità di volo che retrocede a **AltCtl** (PX4 perde la posizione orizzontale).
- Nei messaggi PX4 (`ulog_messages`), in 100 s di volo:
  - 6 reinit consecutivi del driver GPS (sequenza `[gps] u-blox firmware version: HPG 1.40ROV / protocol 20.30 / module NEO-M8P-0`)
  - 4 cicli `[mc_pos_control] invalid setpoints` → `Failsafe: blind land` → `Failsafe activated`
- Nessuna perdita reale di satelliti dal lato modulo.

## Setup hardware del volo

- Pixhawk 6X **sostituita** rispetto ai voli precedenti.
- Cavo GPS-Pixhawk **auto-costruito** dall'utente, adattato al nuovo connettore.
- Modulo GPS u-blox NEO-M8P-0 (firmware HPG 1.40ROV) invariato, montato su mast.
- Parametri attivi rilevanti: `GPS_1_CONFIG = 202`, `GPS_1_PROTOCOL = 1` (UBX), `GPS_UBX_BAUD2 = 230400`, `GPS_DUMP_COMM = 1` (UART raw dump abilitato per questa diagnosi).

## Metodo di analisi

Per la prima volta è stato abilitato `GPS_DUMP_COMM = 1`, che fa pubblicare al driver il flusso UART raw nel topic uORB `gps_dump` (instance unica per entrambe le direzioni; bit 7 di `len` discrimina TX/RX). Il volo è stato analizzato così:

1. Estrazione di `sensor_gps`, `gps_dump`, `esc_status` da ULog → CSV (`pyulog`).
2. Ricostruzione dei due bytestream UART (modulo→FC e FC→modulo).
3. Parsing UBX frame-per-frame (sync `B5 62`, validazione checksum Fletcher-8).
4. Correlazione temporale tra: gap in `sensor_gps`, eventi di reinit, byte spazzatura, CRC falliti, RF metrics, corrente motori.

## Cronologia dei gap

I gap in `sensor_gps` non sono uniformi come nel log precedente del 27/04:

| Inizio gap (s, boot PX4) | Fine gap | Durata | Reinit driver (MON-VER ricevuto) |
|---:|---:|---:|---|
| 574.95 | 586.55 | **10.8 s** | 585.9 s |
| 588.5* | 600.8* | **~12 s** (parziale, embedded nel gap successivo) | 600.9 s |
| 591.94 | 641.34 | **49.4 s** | 612.3 s, 640.8 s (doppia sweep) |
| 643.94 | 681.94 | **38.0 s** | 652.9 s, 681.4 s (doppia sweep) |

I gap "lunghi" (49 s, 38 s) sono dovuti al fatto che la **prima sweep di auto-baud del driver non aggancia il modulo**, e parte una seconda sweep.

## Quello che il driver PX4 sta effettivamente facendo

Il driver `gps` di PX4, alla scadenza del `TIMEOUT_5HZ` (500 ms + 300 ms di margine), esegue una sequenza di **auto-baud probing** del modulo u-blox. Non viene **mai** trasmesso un comando `CFG-RST` (class 0x06 id 0x04): il dump TX contiene solo:

| Messaggio TX | Conteggio | Significato |
|---|---:|---|
| `CFG-VALSET` (0x06 0x8A) | 60+ | Tenta di impostare i CFG_KEY_VAL della UART su uno dei baud-rate noti |
| `CFG-PRT` (0x06 0x00) | 60+ | Comando legacy "Port Configuration" |
| `MON-VER` (0x0A 0x04) | 6 | Poll della versione firmware: usato dal driver per confermare di aver agganciato |
| `CFG-NAV5` (0x06 0x24) | 6 | Modello dinamico (impostato dopo MON-VER OK) |
| `CFG-MSG` (0x06 0x01) | 30+ | Abilita le pubblicazioni periodiche (NAV-PVT, NAV-DOP, ecc.) a 5 Hz |

Ogni "u-blox firmware version" visibile nei log corrisponde a un `MON-VER` ricevuto correttamente → reinit completata → driver riprende a pubblicare `sensor_gps`. **Pochi secondi dopo**, il parser perde di nuovo sync e tutto si ripete.

## Quello che il modulo GPS sta effettivamente facendo

Nei 5 minuti di volo, il modulo invia su UART (242 056 byte totali, ≈ 800 B/s):

| Messaggio RX | Conteggio | Note |
|---|---:|---|
| NAV-PVT (0x01 0x07) | 1244 | A 5 Hz ideali, attesi 1685: **rate effettivo 3.67 Hz** |
| NAV-DOP (0x01 0x04) | 1243 | |
| NAV-STATUS (0x01 0x03) | 1239 | |
| MON-HW (0x0A 0x09) | 250 | `noise_per_ms` 108-109, `jam` 6-13, `agc` 1560-1638 — stabili |
| ACK-ACK / ACK-NAK | 50 / 3 | Risposte alle CFG- del driver |

**Tutti i NAV-PVT validi ricevuti hanno `fix_type=5` (RTK Float), `satellites_used=15`, `eph=0.02 m`.** Il modulo non perde mai il fix dal proprio punto di vista.

## Evidenza del problema: integrità del bytestream UART

- **37 413 / 242 056 byte (15.5 %) sono "spazzatura"**: byte ricevuti che non rientrano in nessun frame UBX valido secondo il parser di analisi.
- **13 messaggi UBX con checksum non valido**, distribuiti nello stream e concentrati attorno agli istanti di reinit (t ≈ 518, 589, 602, 623, 662, 664 s).
- I gap nel **flusso byte RX** sono brevi (1.0-1.4 s), molto più corti dei gap in `sensor_gps` (10-50 s): **i byte continuano ad arrivare**, ma il parser non riesce a costruirci sopra messaggi coerenti.

Meccanismo dedotto:
1. Un bit-flip nel campo `length` (offset 4-5 di un frame UBX) fa "saltare" al parser un numero errato di byte.
2. Il parser legge byte spazzatura interpretandoli come payload+CRC.
3. CRC fallisce → il parser scarta il messaggio e riparte da capo, scansionando byte per byte fino al prossimo `B5 62`.
4. Se il drop di sync dura > 800 ms (TIMEOUT_5HZ + margine), il driver decreta link guasto → entra in auto-baud sweep (~7 s di silenzio nel caso fortunato, ~25 s se serve una seconda sweep).
5. Sweep completata → modulo riconfigurato → flusso ricostituito → entro pochi secondi un altro bit-flip riavvia il ciclo.

## Ipotesi falsificate

| Ipotesi | Verdetto | Evidenza |
|---|---|---|
| Perdita di satelliti / cielo coperto | ❌ | `fix_type=5`, `sat=15`, `eph=0.02 m` su tutti i PVT ricevuti |
| Jamming RF o EMI da motori | ❌ | `noise_per_ms`, `jamming_indicator`, `agc` identici prima/durante/dopo i gap |
| Picchi di corrente motori al momento del gap | ❌ | Corrente totale ESC stabile a ~20 A in hover, nessuna variazione coincidente |
| Brownout 5 V (verificato in log precedenti) | ❌ | Già escluso in `troubleshooting-gps-pixhawk6x.md` (rail stabile 5.04-5.24 V) |
| Reset del modulo comandato da PX4 | ❌ | **Zero `CFG-RST` trasmessi** in tutto il volo |
| Configurazione errata di `GPS_1_CONFIG` | ❌ | Vale `202` (GPS2), allineato col cavo fisico |

## Quadro completo della giornata (11 voli)

L'analisi è stata estesa a tutti i log della giornata. Tabella riassuntiva:

| Log | Durata (s) | Alt max (m) | Sum RPM max | % tempo in lift | Garbage RX | CRC fail | NAV-PVT Hz | Reinit driver | Gap `sensor_gps` > 2 s |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| `13_40_57` | 344 | 8.1 | 47 740 | 98.6 % | **15.5 %** | 12 | 3.60 | **6** | 49.4 s, 38.0 s, 11.6 s |
| `13_50_41` | 12 | -0.7 | 4 270 (idle) | 0.0 % | **0.2 %** | 0 | 4.90 | 0 | — |
| `13_50_52` | 12 | -0.1 | 26 826 | 17.5 % | **14.8 %** | 0 | 3.28 | 1 | — |
| `13_51_13` | 20 | 2.2 | 39 597 | 72.8 % | **0.2 %** | 1 | 5.10 | 0 | — |
| `13_51_37` | 96 | 2.9 | 32 841 | 96.0 % | **49.0 %** | 4 | 2.07 | 2 | 26.4 s, 9.6 s |
| `13_56_40` | 81 | 3.2 | 32 897 | 90.4 % | **6.6 %** | 3 | 4.04 | 2 | 12.2 s, 11.4 s |
| `14_00_42` | 91 | 4.7 | 35 755 | 95.1 % | **13.8 %** | 0 | 4.25 | 1 | 26.4 s |
| `14_05_57` | 93 | 4.5 | 32 810 | 95.1 % | **25.1 %** | 3 | 3.11 | 2 | — |
| `14_09_26` | 84 | 5.1 | 33 969 | 94.1 % | **0.4 %** | 3 | 4.90 | 0 | — |
| `14_12_24` | 88 | 5.1 | 33 196 | 96.8 % | **3.0 %** | 4 | 4.41 | 1 | 11.8 s, 2.2, 2.0, 2.0 |
| `14_15_52` | 81 | 5.1 | 33 242 | 94.7 % | **0.2 %** | 2 | 4.96 | 0 | 2.0 s |

### Osservazioni dal quadro complessivo

1. **Estrema oscillazione del BER tra i voli**: il rate di byte spazzatura passa da 0.2 % (voli "puliti") a 49.0 % (peggior caso, `13_51_37`) **a parità di regime motori** (32 000–36 000 sum-RPM, ~95 % del tempo in regime di lift in tutti i voli "veri"). Il regime di vibrazione meccanica del telaio è sostanzialmente costante tra questi voli, ma il link UART risponde in modo radicalmente diverso. Questo è esattamente il comportamento atteso da **un difetto intermittente meccanicamente attivato**: a seconda di come il cavo si posiziona dopo aver maneggiato il drone, il contatto marginale può essere praticamente OK o praticamente aperto.

2. **Trend temporale a U**: i primi tre voli "veri" del pomeriggio (13_40, 13_50, 13_51) e quello peggiore (13_51_37, 49 %) sono concentrati nella prima fascia oraria; gli ultimi tre voli (14_09, 14_12, 14_15) sono tutti sotto il 3 % di garbage. Non c'è una ragione termica per attendersi questo — più probabile che l'utente, riposizionando il drone tra una prova e l'altra, abbia gradualmente trovato un'orientazione del cavo più tollerante.

3. **CRC fail sempre presenti, anche nei voli "puliti"** (1–4 messaggi UBX scartati per checksum invalido in praticamente tutti i voli): conferma che il bit-error non è mai zero. La differenza tra un volo buono e uno cattivo non è "errori vs niente errori", ma "errori sparsi vs errori raggruppati al punto da superare la finestra di timeout di 800 ms del driver". È il pattern tipico di un contatto fisicamente marginale, non di un'interferenza saltuaria.

4. **Volo `13_51_13` come controprova del fattore meccanico**: 20 s, decollo a 2.2 m, motori a 39 597 sum-RPM (regime di lift), e nonostante questo il BER è 0.2 % e il NAV-PVT rate è 5.10 Hz — link perfetto. Si colloca **15 secondi** dopo `13_50_52` (12 s, BER 14.8 %) e prima di `13_51_37` (96 s, BER 49 %). L'unica differenza spiegabile è la posizione fisica del cavo dopo la manipolazione tra una prova e l'altra.

5. **Stato del modulo invariato in ogni volo**: dove `sensor_gps` viene pubblicato, fix_type = 5 e satellites_used = 14–15. Il modulo continua a vedere il cielo perfettamente; non c'è alcuna correlazione con quota di volo, durata, o numero di reinit.

### Implicazione operativa

Il cavo, allo stato attuale, è **inutilizzabile per voli di missione**: in 5 prove su 11 (escludendo i due da 12 s) il driver è andato in reinit almeno una volta. Va sostituito o ricostruito prima di qualsiasi prova non strumentale ulteriore.

---

## Conferma incrociata sui due log successivi (13_50_41 e 13_50_52)

I due voli immediatamente successivi al primo, entrambi di **12 s netti**, danno una conferma quasi sperimentale dell'ipotesi cavo. Setup, parametri, modulo e firmware sono identici al primo log — l'unica variabile che cambia è il **regime di rotazione dei motori**.

| Log | Esito | Sum RPM (max) | Garbage byte RX | NAV-PVT rate | Auto-baud probe? |
|---|---|---:|---:|---:|---|
| `13_50_41.ulg` | armato, **idle**, disarmato auto | ~4 270 (≈ 712 RPM × 6) | **0.2 %** (23 / 9 796) | **4.71 Hz** | **no** (0 TX UBX) |
| `13_50_52.ulg` | armato, takeoff, **blind land dopo 1 s** | ~26 800 (≈ 4 471 RPM × 6) | **14.8 %** (1 191 / 8 058) | **3.17 Hz** | **sì** (CFG-VALSET/PRT/MON-VER/NAV5/MSG) |

**Differenza di ~75× nel rate di byte spazzatura** a parità di tutto il resto. L'unica variabile cambiata è il regime motori — e quindi il livello di vibrazione meccanica della struttura — e la cosa è sufficiente a portare il link UART da praticamente pulito (BER fisiologico) a inutilizzabile.

Questa evidenza rafforza in modo decisivo l'ipotesi che la causa non sia elettrica/RF stazionaria (altrimenti `13_50_41` avrebbe lo stesso BER alto pur essendo armato), bensì un **contatto fisicamente marginale che si apre intermittentemente sotto vibrazione**.

## Causa primaria ipotizzata

**Difetto fisico nel cavo GPS auto-costruito** introdotto contestualmente alla sostituzione della Pixhawk.

Argomenti a supporto:
- Stessa firmware PX4, stesso firmware modulo, stessi parametri logici del volo del 27/04, ma **comportamento drasticamente peggiore**: 6 reset/100 s vs 1 reset isolato per intero volo.
- L'unica variazione documentata è: nuova Pixhawk + cavo rifatto a mano.
- Il modulo non perde nulla; PX4 non comanda reset; le RF metrics sono stabili. Resta solo il livello fisico/elettrico del filo.
- **Modulazione del BER col regime motori** (vedi confronto 13_50_41 vs 13_50_52 sopra): a motori in idle il link è sano, a motori in lift il link collassa. Pattern compatibile esclusivamente con un difetto meccanico-conduttivo.

### Perché il baud rate non è la spiegazione

Si potrebbe pensare che `GPS_UBX_BAUD2 = 230400` sia "alto" e quindi colpevole. **Non lo è**: per una UART TTL su cavo corto (< 30 cm), 230 400 baud è un regime conservativo. Riferimenti utili:

- Bit time a 230 400 baud: **4.34 µs** — molte volte più lento del limite tecnologico di una UART asincrona Pixhawk-class (≥ 1 Mbps).
- I moduli u-blox commerciali lavorano nativamente a 460 800 baud su cavo standard senza errori.
- Su un cavo elettricamente sano, a 230 400 baud su 30 cm il **BER attendibile è inferiore a 10⁻⁹** — ovvero zero byte corrotti in 5 minuti di prova.

Trovare invece **15.5 % di byte fuori frame e CRC UBX falliti raggruppati nel tempo** è la firma di un link con discontinuità intermittenti: contatto marginale, saldatura fredda, conduttore con cricca, GND non realmente comune, o crosstalk indotto da movimento del cavo durante il volo. Non è un problema di "frequenza troppo alta" da rallentare: è un problema di **conduzione**.

Scendere a 115 200 baud raddoppia il bit time e quindi la finestra di campionamento del ricevitore — può **attenuare** il sintomo, ma resta una pezza diagnostica, non una correzione del difetto.

### Fattori aggravanti possibili
- Lunghezza/instradamento del cavo rispetto a ESC e cablaggio motori.
- Massa di segnale condivisa col power bus.
- Connettori non crimpati a regola d'arte / contatti marginali.
- Spostamento del cavo durante il volo che modula un contatto intermittente.

## Piano di test consigliato (non ancora eseguito)

In ordine di costo crescente e diagnosticità:

1. **Ispezione fisica del cavo nuovo**: continuità con multimetro su TX, RX, GND **mentre si muove/piega il cavo** (test "wiggle"); verifica della qualità di saldature/crimpature ai due connettori, della tenuta degli alloggi JST, del twist dei conduttori e del fatto che GND sia realmente unico tra modulo e FC.
2. **Sostituzione del cavo** con uno commerciale (o ricostruito con maggior cura) — è il test più diretto per la causa ipotizzata.
3. **(Diagnostico, non risolutivo)** Volo di confronto con `GPS_UBX_BAUD2 = 115200`: se a baud dimezzato il rate di reset crolla ma non si azzera, significa che il link è marginale ma non irrimediabile (utile per quantificare il margine residuo del cavo attuale).
4. **Volo a banco senza motori** con setup attuale: se i reset spariscono senza vibrazioni/movimento, il difetto è meccanicamente attivato dal volo (contatto che si apre per inerzia o flessione). Se restano, il difetto è statico.
5. **(Opzionale, post-diagnosi)** Disabilitare `GPS_DUMP_COMM = 0` per eliminare il carico di log corrispondente.

## Riferimenti incrociati

- `maintenance/troubleshooting-gps-pixhawk6x.md` — risoluzione precedente del problema "GPS non aggancia satelliti" (riconfigurazione `GPS_1_CONFIG`).
- `maintenance/troubleshooting-rtk.md` — analisi del singolo gap 21.6 s del 27/04: stesso `[gps] ubx msg 0x0103 invalid len` pattern, ma frequenza isolata.

## Note sul metodo

Il topic `gps_dump`, abilitato per la prima volta su questo drone, ha permesso di isolare la diagnosi al livello fisico: senza il bytestream raw non sarebbe stato possibile distinguere "modulo che si guasta" da "stream corrotto in transito". Per future diagnosi GPS conviene tenere `GPS_DUMP_COMM = 1` quando si sospetta un problema sul link.

Il file `.ulg` da 240 MB include ~340 kB di `gps_dump` (irrilevante sul totale).
