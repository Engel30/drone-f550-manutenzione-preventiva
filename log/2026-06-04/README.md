# Log volo 2026-06-04 — Sessione validazione cavo GPS schermato

Sessione di **tentata validazione del cavo GPS rifatto con schermatura** (treccia
+ drain wire, fissaggio hot-glue sui connettori, instradamento separato dai
cavi motore). Riferimenti:

- `maintenance/azioni-pre-prossimo-volo.md` — checklist A0.1–A0.5 (cavo)
- `maintenance/troubleshooting-gps-dropout-2026-05-27.md` — diagnosi originale
- `plot/gps_dump_ber.py` — script di analisi BER usato per la verifica
- `plot/gps_reinit_correlate.py` — correlazione reinit ↔ throttle/vibrazione

`GPS_DUMP_COMM = 1` mantenuto attivo per misurare quantitativamente il BER UART
del nuovo cavo nelle condizioni discriminanti (motori in regime di lift).

> Nota: i timestamp nei nomi dei file `.ulg` sono ora locale Pixhawk, **2 ore
> indietro** rispetto al wall-clock. Es. `11_52_13.ulg` = volo delle 13:52:13.

> ⚠️ **Verdetto rivisto (sessione pomeridiana 2026-06-04).** Il giudizio iniziale
> "Cavo schermato OK" si basava sul **solo** volo `11_52_13`. I tre voli
> successivi mostrano che il link **si degrada riarmo dopo riarmo** e collassa
> su `12_28_29`. Vedi [Risultato](#risultato).

## File

| File | Wall time | Durata armato | Tipo | Note |
|---|---|---:|---|---|
| `11_50_58.ulg` | 13:50:58 | 10.7 s | Boot + init driver | Reboot/power-on Pixhawk: reinit driver GPS, sequenza CFG-MSG → BER apparente 47% ma è artefatto di init (NMEA→UBX switch + ACK driver), non degrado del cavo. Da ignorare per la valutazione del link. |
| `11_51_42.ulg` | 13:51:42 | 11.0 s | Test motori idle | Arming breve in idle (sum-RPM ≈ 4 200, 0% in lift). Garbage 0.90%, 5.00 PVT/s, 0 reinit, 0 CRC fail → link OK ma non discrimina (test in idle). |
| `11_52_13.ulg` | 13:52:13 | **146.0 s** | Volo lift | **Garbage 0.24%, 4.91 PVT/s, 0 reboot, 0 gap.** Pulito. È il volo su cui era stata (prematuramente) dichiarata la validazione. |
| `11_54_05.ulg` | 13:54:05 | 68.9 s | Volo lift | Garbage **2.53%**, 4.67 PVT/s, **1 reboot** driver, 1 gap (2.0 s). Marginale. |
| `12_21_42.ulg` | 14:21:42 | 83.1 s | Volo lift | Garbage 0.36%, 4.87 PVT/s, 0 reboot, 1 gap (3.0 s). Pulito. |
| `12_28_29.ulg` | 14:28:29 | 104.5 s | Volo lift | **Garbage 23.62%, 2.34 PVT/s (dimezzato), 7 reboot driver, 3 gap (11/23/12 s ≈ 47 s di outage GPS su 104 s armati). Regressione conclamata.** |

> Nota sul conteggio reinit: `gps_dump_ber.py` conta le righe di log `u-blox`
> (firmware/protocol/module), **3 per reboot effettivo**. La colonna `reinit`
> dello script va divisa per 3: i 21 di `12_28_29` = **7 reboot** reali.

## Risultato

**⚠️ A0.5 NON superato — validazione fallita. La schermatura non ha risolto.**

I quattro voli sotto carico in lift della stessa sessione, in ordine cronologico:

| Volo (wall) | armato | garb% | PVT/s | reboot drv | gap >2 s | esito |
|---|---:|---:|---:|---:|---|---|
| 11_52_13 (13:52) | 146 s | 0.24% | 4.91 | 0 | 0 | pulito |
| 11_54_05 (13:54) | 69 s | 2.53% | 4.67 | 1 | 1 (2.0 s) | marginale |
| 12_21_42 (14:21) | 83 s | 0.36% | 4.87 | 0 | 1 (3.0 s) | pulito |
| **12_28_29 (14:28)** | 104 s | **23.62%** | **2.34** | **7** | **3 (11/23/12 s)** | **collasso** |

Il link **non è stabile**: voli puliti e voli degradati si alternano nella stessa
sessione, con un trend di peggioramento che culmina in `12_28_29` (garbage ~100×
il volo di accettazione, PVT rate dimezzato, ~47 s di outage su 104 s armati).
È la **stessa firma di guasto del 27/05 pre-schermatura** (vedi sotto).

## Diagnosi differenziale — non è EMI, non è un evento singolo

Due analisi sui dati raw discriminano la natura del guasto.

**1. Non è corruzione di bit sulla UART (non è EMI).**
La colonna `garbage` (byte fuori da frame UBX validi) è alta, ma `CRC fail`
(frame ben incorniciati con checksum Fletcher-8 errato = bit-flip in transito) è
**≈ 0** su tutti i voli, ieri e oggi (`12_28_29`: 3 CRC fail su 56 643 byte).
Se il problema fosse integrità di segnale / EMI, i CRC fail esploderebbero. Il
garbage è invece il traffico **NMEA/CFG-MSG/ACK** emesso a ogni reboot del
driver. → La schermatura (treccia + drain wire) contrasta l'EMI, che **non era
mai la causa**: per questo non ha risolto.

**2. I reboot non sono innescati da picchi di throttle o vibrazione.**
Correlazione di `plot/gps_reinit_correlate.py` sulle 6 pre-window dei reboot
in volo di `12_28_29`:

| Metrica | pre-reboot (mediana) | fondo volo (mediana / p90) | rapporto |
|---|---:|---:|---:|
| throttle slew \|Δsum-RPM/Δt\| | 34 506 RPM/s | 40 427 / 45 588 | **×0.85** |
| vibrazione (accel_vibration_metric) | 3.5 m/s² | 3.3 / 3.7 m/s² | **×1.07** |

I reboot avvengono al livello **ambientale** del volo (vibrazione ~3.3 m/s²
sostenuti), distribuiti quasi regolarmente (1 ogni ~15 s), **non** su transitori
di spinta o picchi di vibrazione (1/7 sopra il p90 di slew, 2/7 di vibrazione).

**Conclusione:** firma di **contatto meccanico intermittente** sensibile
all'**esposizione vibratoria sostenuta** (non a shock acuti), non integrità di
segnale. Il sospetto resta su connettore/seating, drain wire, fatica del filo o
vibrazione del mast — non sulla schermatura né sul crimping in sé. Il
miglioramento mattutino è plausibilmente l'effetto transitorio del
riassemblaggio del connettore, che degrada poi riarmo dopo riarmo.

## Prossimi passi

1. Ispezione visiva + **wiggle/continuity test** sul connettore GPS lato Pixhawk
   e lato modulo sotto sollecitazione meccanica.
2. Verificare seating e strain-relief sul mast (vibrazione 3.3 m/s² sostenuta).
3. Ri-validare con un volo lift > 60 s solo dopo l'intervento meccanico
   (`plot/gps_dump_ber.py`), su **più riarmi consecutivi**, non uno solo.

## Mappa file ↔ piano voli

> **Sessione a doppio scopo.** Oltre alla validazione del cavo GPS, questi voli
> in hover Stabilize **sono le prove del Set C** (pala danneggiata 10 % a turno
> sui motori) del piano `piano-voli.md`. Il guasto GPS **non inquina i dati
> pala**: in Stabilized il controllo non usa il GPS e l'analisi danno-pala si
> basa su vibrazione/ESC/assetto (IMU), non sulla posizione.

⚠️ **Attenzione agli orari.** Il nome-file NON è sempre l'ora di volo reale: per
`11_54_05.ulg` il nome dice 13:54 ma l'**ora UTC GPS** (confermata dall'mtime del
file, 12:11 UTC = fine volo) dice **14:09–14:11**. L'abbinamento sotto usa l'ora
GPS reale, non il nome. La numerazione "Stabilize N" degli appunti di volo **non**
coincide con C.N: la mappatura è per **motore**.

| File | Ora reale (CEST) | Set C | Motore pala 10 % | V batt (appunti) | Note |
|---|---|---|---|---|---|
| `11_50_58.ulg` | 13:51:37 | — | — | — | arming a terra 11 s (check) |
| `11_51_42.ulg` | 13:51:43 | — | — | — | arming a terra 11 s (check) |
| `11_52_13.ulg` | 13:52→13:54 | (baseline) | pale sane | — | "Test 1" appunti (na) |
| `11_54_05.ulg` | 14:09→14:11 | (baseline) | pale sane | — | "Test 2" appunti (na) |
| `12_21_42.ulg` | 14:21→14:23 | **C.3** | M3 | 15.1 | "Stabilize 2" |
| `12_28_29.ulg` | 14:28→14:30 | **C.6** | M6 | 15.0 | "Stabilize 3"; volo col peggior guasto GPS |
| `12_39_37.ulg` | 14:39→14:41 | **C.2** | M2 | 16.6 (?) | "Stabilize 4"; V batt sopra il misurato a bordo |
| `12_43_47.ulg` | 14:43→14:45 | **C.4** | M4 | — | "Stabilize 5" |
| `12_46_09.ulg` | 14:46→14:47 | **C.5** | M5 | — | "Stabilize 6" |

> Nota tensioni: i valori `V batt` sono presi dagli appunti di volo (lettura
> esterna). La tensione a bordo all'armo (`battery_status`) è ~15.7–15.85 V per
> tutti i voli e **non coincide** con gli appunti (16.6 V è sopra il misurato):
> trattare gli appunti come riferimento qualitativo.

Coordinate decollo (da `vehicle_global_position`): lat **43.6008°N**,
lon **13.4821°E** (Università Politecnica delle Marche, Ancona).

## File `.mcap` generati

I `.mcap` sono stati prodotti con:

```bash
python3 foxglove/ulog_to_mcap.py log/2026-06-04/<file>.ulg --auto-trim --satellite
```

| File | Dimensione | Overlay satellitare |
|---|---:|---|
| `11_50_58.mcap` | 6.9 MB | assente (`vehicle_global_position` non ancora disponibile al trim) |
| `11_51_42.mcap` | 8.7 MB | 200×200 m |
| `11_52_13.mcap` | 107.5 MB | 200×200 m |
| `11_54_05.mcap` | 49.3 MB | 200×200 m |
| `12_21_42.mcap` | 58.8 MB | 200×200 m |
| `12_28_29.mcap` | 73.6 MB | 200×200 m |

## Analisi GPS — comandi di riproduzione

```bash
# BER UART per tutti i voli
python3 plot/gps_dump_ber.py log/2026-06-04/*.ulg

# Correlazione reinit ↔ throttle/vibrazione sul volo collassato
python3 plot/gps_reinit_correlate.py log/2026-06-04/12_28_29.ulg
```

Output sintetico BER (colonna `reinit` = righe log u-blox, ÷3 = reboot reali):

```
file                    armato     rx B   garb%  CRC  PVT/s  reinit  gap>2s  sumRPM
11_50_58.ulg             10.7s     4266  47.35%    2  0.91       3       0    4245
11_51_42.ulg             11.0s    10428   0.90%    0  5.00       0       0    4233
11_52_13.ulg            146.0s   118895   0.24%    4  4.91       0       0   29372
11_54_05.ulg             68.9s    54431   2.53%    1  4.67       3       1   29783
12_21_42.ulg             83.1s    67703   0.36%    4  4.87       0       1   28830
12_28_29.ulg            104.5s    56643  23.62%    3  2.34      21       3   28911
```

---

# Sessione tardo-pomeriggio (≈15:00–15:34) — pale sane, position + missione automatica

Secondo gruppo di log della giornata, **caricato separatamente** e non legato alla
campagna pale né alla validazione del cavo. **Tutti i voli con pale NON
danneggiate.** Cinque voli in **Position** (POSCTL) più, come ultimo, una
**missione automatica** (AUTO_MISSION + RTL). Non c'erano appunti di volo
dettagliati: le etichette sotto sono ricostruite dai dati di bordo
(`vehicle_status.nav_state`, `esc_status`, `sensor_gps`).

> Orari: nome-file = ora locale Pixhawk, **+2 h = wall-clock CEST** (es.
> `13_34_40.ulg` ≈ 15:34). Sito di decollo invariato: lat **43.6008°N**,
> lon **13.4821°E** (Ancona).

## Etichettatura voli

| File | ≈ Wall time | Armato | Modalità (% tempo armato) | Etichetta |
|---|---|---:|---|---|
| `12_58_57.ulg` | 14:58 | 14.7 s | POSCTL 100% | Hop breve in position, pale sane |
| `12_59_16.ulg` | 14:59 | 10.1 s | POSCTL 100% | Hop breve in position, pale sane |
| `13_13_29.ulg` | 15:13 | 10.7 s | POSCTL 91% / STAB 9% | **A terra al minimo** (sum-RPM ≈ 4 400, 0% in lift) — test/decollo abortito. Unico volo con RTK-float a terra |
| `13_14_52.ulg` | 15:14 | 14.2 s | POSCTL 100% | Hop breve in position, pale sane |
| `13_15_11.ulg` | 15:15 | **398.0 s** | POSCTL 91% / STAB 9% | **Volo lungo in position** (98% in lift), pale sane |
| `13_34_40.ulg` | 15:34 | 182.2 s | **AUTO_MISSION 84% / AUTO_RTL 16%** | **Missione automatica** (waypoint + rientro), pale sane |

## Analisi GPS — esito: link sano in tutti i voli

Qualità del fix nella finestra armato (`sensor_gps`):

| File | fix (% tempo) | sat | eph [m] | hdop | RTCM inj/s | reinit | gap >2 s | esito |
|---|---|---:|---:|---:|---:|---:|---:|---|
| `12_58_57` | 3D 100% | 13–14 | 0.73 | 0.83 | 0.0 | 0 | 0 | pulito |
| `12_59_16` | 3D 100% | 12–13 | 0.76 | 0.83 | 0.0 | 0 | 0 | pulito |
| `13_13_29` | RTK-float 100% | 13 | 0.45 | 0.86 | 3.1 | 0 | 0 | pulito (a terra) |
| `13_14_52` | 3D 100% | 13–14 | 0.42 | 0.86 | 0.0 | 0 | 0 | pulito |
| `13_15_11` | 3D 100% | 12–14 | 0.67 | 0.78 | 0.0 | 0 | 3 (≈2 s) | pulito |
| `13_34_40` | 3D 100% | 11–14 | 0.61 | 0.83 | 0.0 | 0 | 2 (≈2 s) | pulito |

Fix sano ovunque (12–14 satelliti, `eph` 0.4–0.8 m, `hdop` ≈ 0.8, `noise_per_ms`
≈ 110, `jamming` 15–23 basso, `spoofing` assente). **Zero reinit del driver** in
tutti i voli, **inclusa la missione automatica (182 s) e il volo lungo in
position (398 s, 98% in lift)** — proprio le condizioni di carico sostenuto che
mandavano in collasso `12_28_29` la mattina. I gap residui da ~2 s sui due voli
lunghi sono **isolati e regolari** (1 ogni ~95–100 s), non la firma di outage
(11/23/12 s) del volo collassato.

## Conferma del discriminante RTK (non è il carico motore, non è il cavo)

Incrociando i fix-type GPS di questa sessione con i voli "collassati" della
sessione cavo emerge la correlazione decisiva:

| Volo | sum-RPM medio | modo GPS | RTCM inj/s | reinit/gap | esito link |
|---|---:|---|---:|---|---|
| `11_52_13` (mattina) | 29 372 | 3D 95% / RTK-fl 4% | 0.1 | 0 / 0 | pulito |
| `11_54_05` (mattina) | 29 783 | **RTK-float 77%** | **3.1** | 1 reboot / 1 gap | marginale |
| `12_21_42` (mattina) | 28 830 | **RTK-float 100%** | **3.2** | 0 / 1 gap | marginale |
| `12_28_29` (mattina) | 28 911 | **RTK-float 100%** | **2.8** | **7 reboot / 3 gap** | **collasso** |
| `13_15_11` (pom.) | 30 383 | 3D 100% | 0.0 | 0 / 0 | pulito |
| `13_34_40` (pom.) | 29 813 | 3D 100% | 0.0 | 0 / 0 | pulito |

A **parità di regime motore** (sum-RPM ≈ 29–30 k, in lift), i voli **RTK con
RTCM iniettato** si degradano/collassano, mentre i voli **3D senza RTCM** restano
puliti anche più a lungo. Il fattore discriminante è il **modo RTK / iniezione
RTCM**, non la spinta né la vibrazione (vedi `gps_reinit_correlate.py` sopra) e
non la schermatura del cavo.

> **L'RTK era attivo ed efficace** (correzione *applicata*): nei voli `fix=5`
> l'`eph` (incertezza orizzontale) crolla a **0.02–0.07 m** contro **0.6–0.7 m**
> dei voli 3D — un miglioramento ~10× che solo le correzioni RTK danno. Il fix è
> però sempre **RTK-float (5)**, mai **RTK-fixed (6)**: ambiguità intere non
> risolte (baseline/distanza base/multipath/tempo).
> Nota sul campo `rtcm_msg_used`: vale **0 (UNKNOWN) su tutti i voli, anche quelli
> RTK con eph 0.02 m** → il driver u-blox **non popola** questo campo, quindi NON
> è un indicatore d'uso (errore di lettura iniziale: NON significa "non usato").
> L'indicatore affidabile d'uso RTK resta `fix_type=5/6` + il calo di `eph`.
>
> Resta valido il discriminante: il **modo RTK / iniezione RTCM** è la
> precondizione dei reinit (a parità di regime motore, 3D = pulito, RTK =
> collasso). Prossimo passo coerente: indagare l'interazione driver PX4 ↔ u-blox
> in modo RTCM-rover e la sorgente/instradamento RTCM — **lato software/config,
> non meccanico.**

## File `.mcap` generati (questa sessione)

Prodotti con `--auto-trim --satellite` (overlay ESRI World Imagery 200×200 m
centrato sul takeoff, presente in tutti):

```bash
python3 foxglove/ulog_to_mcap.py log/2026-06-04/<file>.ulg --auto-trim --satellite
```

| File | Dimensione | Overlay satellitare |
|---|---:|---|
| `12_58_57.mcap` | 9.5 MB | 200×200 m |
| `12_59_16.mcap` | 7.7 MB | 200×200 m |
| `13_13_29.mcap` | 7.6 MB | 200×200 m |
| `13_14_52.mcap` | 11 MB | 200×200 m |
| `13_15_11.mcap` | 276 MB | 200×200 m |
| `13_34_40.mcap` | 123 MB | 200×200 m |

---

# Sessione voli quadrati (≈16:06–16:15) — pale sane, A/B naturale RTK vs GPS

Terzo gruppo di log, **caricato separatamente**. Tre voli a **traiettoria
quadrata** (20 s di hover poi quadrato), **pale tutte sane**. Per puro caso i tre
voli realizzano un **A/B quasi controllato**: stessa traiettoria, stesso giorno,
pale sane — cambia **solo il modo GPS** (due in RTK reale, uno in GPS puro).

> Orari: nome-file = ora locale Pixhawk, **+2 h = wall-clock CEST**. Es.
> `14_07_19.ulg` = volo delle 16:07. (Coincide con gli appunti di volo.)

## Appunti di volo (utente)

| Test | Wall time | Note utente |
|---|---|---|
| Test 1 | 16:06–16:07 | volo breve |
| **Test 2** | 16:07–16:10 | **dopo il 2° vertice ha perso il GPS → controllo manuale → atterraggio autonomo** |
| Test 3 | 16:13–16:15 | volo ok; ha dato *motor failure* durante l'atterraggio |

## Classificazione GPS vs RTK e anatomia

| File | Test | Armato | Modo reale | RTCM | eph | fix | reinit | outage NAV | esito |
|---|---|---:|---|---:|---:|---|---:|---|---|
| `14_06_22.ulg` | 1 | 21 s | **RTK-float** | 3.06/s | 0.035 m | 5 (100%) | 0 | 0 s | sano |
| `14_07_19.ulg` | **2** | 76 s | **RTK-float** | 3.13/s | 0.019 m | 5 (100%) | **1** | **28.4 s (38%)** | **perdita GPS + failsafe** |
| `14_13_15.ulg` | 3 | 124 s | **GPS puro 3D** | **0** | 0.539 m | 3 (100%) | 0 | 2.0 s (isolato) | sano |

`CRC fail = 0` su tutti e tre: nessuna corruzione RTCM, nessun bit-flip UART.

## Test 2 — sequenza causale della perdita GPS

Ricostruita da `sensor_gps` (gap) + `vehicle_status` (nav_state/failsafe),
finestra armato `[234.7, 310.3] s`, tempi relativi all'armo:

| rel | evento |
|---:|---|
| 0.0 s | `AUTO_MISSION`, fix=5 RTK-float, eph 1.7 cm, RTCM 3.5/s → vola il quadrato |
| **41.6 s** | **`sensor_gps` si interrompe di colpo** (ultimo campione sano: fix=5, eph 0.017 m, sat 14, inj 3.5) |
| 51.8 s | `failsafe=1`, `nav_state=12` → l'EKF dichiara GPS perso (~10 s dopo) |
| 55.4 s | `nav_state=1` **ALTCTL** (sola quota, niente position-hold) = "controllo manuale" |
| 63.4 s | `nav_state=12` (transizione) |
| **70.1 s** | **GPS torna** (gap totale 28.4 s); 1 reboot driver loggato |
| 72.1 s | `nav_state=4` AUTO_LOITER, poi 72.5 s `nav_state=2` POSCTL, `failsafe=0` → atterra |

La perdita a ~42 s (≈21 s dopo i 20 s di hover) cade "dopo il secondo vertice"
degli appunti. Il passaggio in **ALTCTL con failsafe** è il "preso il controllo
manuale, atterraggio da solo".

## Verdetto — è il modo RTK, non una correzione corrotta

A **parità di traiettoria** (quadrato, pale sane), il volo **RTK** perde il GPS e
quello **GPS puro** no. Conferma il discriminante **modo RTK / iniezione RTCM**
già stabilito nelle sessioni precedenti (vedi
[`maintenance/indagine-rtk-attivo-2026-06-04.md`](../../maintenance/indagine-rtk-attivo-2026-06-04.md)).

Il guasto **non è una singola correzione RTCM sbagliata**: il flusso era sano fino
all'orlo del blackout (`CRC fail=0`, rate stabile 3.5/s, eph 1.7 cm sull'ultimo
campione valido). È **l'essere in modo RTK** la precondizione che innesca lo
stallo del driver PX4↔u-blox.

> ⚠️ **Raffinamento del modello reinit.** La gravità si misura sulla **durata
> dell'outage**, non sul **numero di reinit**: qui **1 solo reinit** ha prodotto
> 28.4 s di blackout e un failsafe operativo (atterraggio forzato), mentre
> `11_54_05` (1 reinit, gap 2.0 s) era benigno. Il reboot driver è il *recupero*,
> non il grilletto.

> Nota Test 3: il *motor failure* in atterraggio è **indipendente dal GPS** (volo
> in 3D puro, NAV sano per 124 s) — analizzato in
> [Motor failure detected — analisi](#motor-failure-detected--analisi-test-3--volo-2):
> è un **falso positivo** del detector PX4 in fase di discesa, non un guasto motore.

## Comandi di riproduzione

```bash
python3 plot/gps_rtk_check.py log/2026-06-04/14_06_22.ulg log/2026-06-04/14_07_19.ulg log/2026-06-04/14_13_15.ulg
python3 plot/gps_rtk_reinit_anatomy.py log/2026-06-04/14_0*.ulg log/2026-06-04/14_13_15.ulg
```

---

# Secondo gruppo voli quadrati (≈16:30–16:44) — pale sane

Quarto gruppo di log, **caricato separatamente**. Stessa configurazione dei
precedenti (traiettoria quadrata dopo ~20 s di hover, **pale tutte sane**). Si
vola in **GPS puro 3D** (RTK sospeso in attesa della chiusura dell'indagine RTCM).

## Appunti di volo (utente) e etichettatura

> Orari: nome-file = ora locale Pixhawk, **+2 h = wall-clock CEST**. Es.
> `14_42_14.ulg` = volo delle 16:42.

L'utente ha elencato **Volo 0/1/2**; la sessione contiene però **4** log
pomeridiani. Il file mancante dall'elenco è `14_38_41` ed è qui etichettato
(decollo non avvenuto): vedi riga in **grassetto**.

| File | Wall CEST | Etichetta | Armato | Esito |
|---|---|---|---:|---|
| `14_30_03.ulg` | 16:30 | **Volo 0** (16:30–16:32) | 109.5 s | volo pulito, RTL + atterraggio nominale |
| **`14_38_41.ulg`** | **16:38** | **(non in elenco) — decollo abortito** | **10.9 s** | **armato a terra, nessun decollo → `Disarmed by auto preflight disarming` (timeout COM_DISARM_PRFLT). Riarmo immediatamente prima di Volo 1.** |
| `14_39_06.ulg` | 16:39 | **Volo 1** (16:38–16:41) | 112.8 s | volo pulito, RTL + atterraggio nominale |
| `14_42_14.ulg` | 16:42 | **Volo 2** (16:42–16:44) | 95.7 s | **missione troncata da override RC** (`Pilot took over using sticks` @571 s) → POSCTL → atterraggio anticipato; *motor failure* = falso positivo al touchdown |

> `14_38_41` (16:38) e `14_39_06` (16:39) sono a un minuto l'uno dall'altro: il
> primo è un arming a terra di 11 s auto-disarmato (decollo mai avvenuto), il
> secondo è il **Volo 1** reale (~113 s, atterra ~16:41). Stesso pattern
> "log corto + volo reale" già visto in Test 1/Test 2.

## Volo 2 — perché la missione finisce presto (override RC, NON il motor failure)

Osservazione: il drone esce da `AUTO_MISSION` e atterra prima del previsto, in
**POSCTL**. La causa **non** è il motor failure (che arriva 19 s dopo, al
touchdown), ma un **override RC degli stick**:

| t | evento | nav_state |
|---:|---|---|
| 497.1 s | parte la missione quadrata | `AUTO_MISSION` |
| **571.0 s** | **`[commander] Pilot took over using sticks`** | **→ `POSCTL`** |
| 590.2 s | *motor failure* (falso positivo) + touchdown | `POSCTL` |
| 592.8 s | `Disarmed by landing` | — |

Con `COM_RC_OVERRIDE=1`, muovere gli stick in AUTO stacca dalla missione e passa
in POSCTL. L'input che ha innescato il takeover è **minuscolo e probabilmente
involontario**: un solo blip di **yaw a −0.106 (10.6%)** per ~0.1 s, mentre
**roll/pitch restano esattamente 0.000 per tutto il volo** e il **throttle è
fermo a −1.00** (stick tutto giù). Appena scatta POSCTL, col throttle al minimo
il drone **scende a rateo massimo e atterra** → da qui l'apparenza di
"atterraggio autonomo".

> ⚠️ Il blip (10.6%) è **sotto la soglia configurata `COM_RC_STICK_OV = 30%`**,
> eppure il takeover è scattato: compatibile con **bump/glitch/rumore sul canale
> yaw del TX**, non con una manovra voluta. **Da verificare sulla radio**: un
> input yaw ~10% involontario non dovrebbe abortire una missione.

> Confronto: lo stesso messaggio compare in **Volo 0** (`14_30_03` @514.6 s) ma
> **dopo** che la missione era finita ed era già in `AUTO_RTL` → presa manuale per
> atterrare = normale. In Volo 2 arriva **in piena missione** → la tronca.
> In **Volo 1** (`14_39_06`) e **Test 3** (`14_13_15`) nessun takeover: missione
> completata e `AUTO_RTL` automatico.

## Motor failure detected — analisi (Test 3 + Volo 2)

Due voli della giornata hanno loggato
`[health_and_arming_checks] Preflight Fail: Motor failure detected` seguito da
`[failsafe] Failsafe activated`:

| Volo | File | t fault | quota | fase | bit failure_detector | durata bit |
|---|---|---:|---:|---|---|---:|
| Test 3 | `14_13_15` | 691.5 s | 7.7 m | inizio discesa `RTL: land at destination` | `0x80` (MOTOR) | 24.9 s |
| Volo 2 | `14_42_14` | 590.2 s | 3.9 m | **touchdown** (`ground_contact=1` a 590.0 s) | `0x80` (MOTOR) | 2.6 s |

> Il prefisso *"Preflight Fail"* è solo il nome della categoria di check: il fault
> è **in volo/atterraggio**, non a terra prima dell'armo.

**Verdetto: falso positivo del Failure Detector di PX4, non un guasto motore/ESC.**

Evidenze (`FD_ACT_EN=1`, `FD_ESCS_EN=1`; soglie `FD_ACT_MOT_THR=0.2`,
`FD_ACT_MOT_C2T=2.0`, `FD_ACT_MOT_TOUT=100 ms`):

1. **Gli RPM seguono il comando** — nessun motore morto o debole. Al fault di
   Test 3 (`actuator_motors` vs `esc_status`):

   | motore | M1 | M2 | M3 | M4 | M5 | M6 |
   |---|---:|---:|---:|---:|---:|---:|
   | comando | 0.60 | 0.28 | 0.62 | 0.26 | 0.28 | 0.60 |
   | rpm | 5457 | 3542 | 5257 | 3514 | 3328 | 5428 |

   Tutti e 6 erogano RPM proporzionali al comando. Lo split alto/basso
   (M1·M3·M6 vs M2·M4·M5) è una **richiesta di coppia roll+pitch sostenuta**
   nella discesa, non un motore che non risponde.

2. **Il bit scatta solo in discesa/atterraggio**, mai durante hover o quadrato, e
   si **auto-cancella** in pochi secondi (al disarmo / fine manovra). In Volo 2
   coincide con `ground_contact=1` (spin-down al touchdown: M1 comandato a 0).

3. **Nessun indice motore ricorrente**: Test 3 = split simmetrico roll/pitch,
   Volo 2 = M1 in spegnimento al contatto. Non c'è un singolo motore colpevole.

4. **Il bit non ha causato l'atterraggio**: in entrambi il drone stava **già
   scendendo** (Test 3 in `AUTO_RTL: land at destination`; Volo 2 in `POSCTL`
   dopo l'override RC — vedi sezione sopra) e il bit/failsafe si è latchato *a
   discesa avviata*. Il *motor failure* è quindi **cosmetico**, non il movente
   dell'atterraggio anticipato.

**Meccanismo probabile.** Il detector `FD_ACT` confronta comando→RPM atteso con
l'RPM misurato (modello lineare via `C2T`). A bassa spinta / forte asimmetria di
coppia la relazione RPM-vs-throttle non è lineare attraverso lo zero (offset di
idle), così i motori a comando alto appaiono "sotto-prestanti" e il bit `MOTOR`
scatta oltre `FD_ACT_MOT_TOUT`. È una **sensibilità nota del check a bassa spinta**.

**Raccomandazione.** Trattare come benigno finché confinato all'atterraggio.
Se ricomparisse **sempre sullo stesso motore e in volo** (non in landing) →
indagare l'hardware. Mitigazione opzionale: alzare `FD_ACT_MOT_THR` o
`FD_ACT_MOT_TOUT`. Indipendente dal problema GPS/RTK.

## File `.mcap` generati (secondo + quarto gruppo)

Stessa pipeline `--auto-trim --satellite` (overlay ESRI 200×200 m):

| File | Dimensione | Etichetta |
|---|---:|---|
| `14_06_22.mcap` | 17 MB | Test 1 |
| `14_07_19.mcap` | 55 MB | Test 2 (perdita GPS) |
| `14_13_15.mcap` | 92 MB | Test 3 (motor failure in discesa) |
| `14_30_03.mcap` | 77 MB | Volo 0 |
| `14_38_41.mcap` | 8.3 MB | decollo abortito |
| `14_39_06.mcap` | 22 MB | Volo 1 |
| `14_42_14.mcap` | 72 MB | Volo 2 (motor failure al touchdown) |
