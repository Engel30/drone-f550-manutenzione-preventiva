# Indagine: il drone sta usando l'RTK o solo il GPS?

**Data apertura**: 2026-06-04
**Stato**: 🟡 aperta — in attesa di nuovi log per discriminare
**Collegata a**: [`troubleshooting-rtk.md`](./troubleshooting-rtk.md) (dropout/reinit driver),
[`troubleshooting-gps-dropout-2026-05-27.md`](./troubleshooting-gps-dropout-2026-05-27.md)
**Tool**: [`plot/gps_rtk_check.py`](../plot/gps_rtk_check.py)

---

## La domanda

Crediamo di volare in RTK (base accesa, RTK configurato in QGC), ma **non è detto
che le correzioni arrivino davvero al drone**. Dobbiamo poter dire, log per log,
se quel volo era in **GPS puro (3D)** o in **RTK reale**. Serve perché:

- il guasto dei reinit driver compare **solo quando l'RTK è davvero attivo**
  (RTCM iniettato) — quindi sapere "GPS o RTK" è la chiave per riprodurre/escludere il guasto;
- alcuni voli "andati lisci" potrebbero esserlo stati **perché l'RTK era spento di
  fatto**, non perché il problema sia risolto.

## Cosa abbiamo scoperto il 2026-06-04 (l'innesco di questa indagine)

Sessione pomeridiana, pale sane (vedi [`log/2026-06-04/README.md`](../log/2026-06-04/README.md)):
QGC mostrava **"3D lock"** e — verificato sui log — il drone **non stava usando
l'RTK**, pur essendo l'RTK "acceso" lato base/QGC.

| Volo | fix_type | RTCM iniettato a bordo | eph | verdetto |
|---|---|---:|---:|---|
| `13_15_11` (398 s) | 3D 100% | **0** | 0.68 m | GPS puro |
| `13_34_40` (auto, 182 s) | 3D 100% | **0** | 0.61 m | GPS puro |
| `13_13_29` (a terra) | RTK-float | 3.1/s | 0.40 m | RTK (non convergente) |
| `12_28_29` (mattina) | RTK-float | 2.8/s | **0.02 m** | RTK reale |

Quindi al mattino le correzioni arrivavano (`injection ~3/s`, eph 2 cm), al
pomeriggio **zero byte RTCM al Pixhawk** → fix 3D → QGC "3D lock". La catena
RTCM (base → QGC → radio → Pixhawk) si è interrotta tra una sessione e l'altra.

## Come si legge "GPS vs RTK" da un log (non fidarsi di un solo campo)

La firma robusta di **RTK realmente attivo** è la **congiunzione** di 3 segnali
indipendenti in `sensor_gps`:

1. **`fix_type >= 5`** — 5 = RTK-float, 6 = RTK-fixed (3 = GPS 3D, 4 = DGPS).
2. **`rtcm_injection_rate > 0`** — PX4 sta iniettando RTCM nel ricevitore.
3. **`eph` crolla sotto ~0.10 m** — precisione che solo l'RTK dà.

Corrispondenza con l'indicatore di QGC: `3D Lock` = fix 3 (no RTK),
`3D RTK GPS Lock (float)` = fix 5, `...(fixed)` = fix 6.

> ⚠️ **Campo da NON usare**: `rtcm_msg_used`. Sul nostro u-blox vale **sempre
> 0 = UNKNOWN**, anche nei voli con eph 2 cm: il driver non lo popola. Non
> indica "non usato". (Errore commesso e corretto il 04/06.)

> Nota di lettura: un RTK appena agganciato (es. `13_13_29`, a terra) è `fix=5`
> con RTCM iniettato ma `eph` ancora ~0.4 m perché **non ha convergione**. È RTK,
> ma non ancora a precisione piena. La convergenza float→fixed richiede tempo +
> buona geometria/baseline.

### Comando

```bash
python3 plot/gps_rtk_check.py log/<data>/<file>.ulg          # uno o più file / glob
```
Stampa, per la finestra armato: distribuzione `fix_type`, satelliti, `eph`
mediana, % campioni con RTCM iniettato, CRC fail RTCM, e un **verdetto**
(GPS PURO / RTK-FLOAT / RTK-FIXED / ⚠ INCOERENTE = RTCM iniettato ma fix 3D).

## Punti da verificare (checklist)

### Sul drone / a bordo (dai log)
- [ ] **Classificare ogni nuovo log** con `gps_rtk_check.py`: GPS o RTK reale?
- [ ] Quando l'RTK *dovrebbe* essere attivo ma `injection_rate = 0`: capire **dove
      si rompe la catena RTCM** (è il caso del 04/06 pomeriggio).
- [ ] Verificare se l'iniezione RTCM **cala/si azzera durante** il volo (es. quando
      QGC perde il link in missione automatica) vs è assente fin dall'inizio.
- [ ] Controllare il **trend float→fixed**: raggiungiamo mai `fix_type = 6`? Con
      quale `eph` e dopo quanto tempo?
- [ ] Correlare i **reinit driver** con la presenza/assenza di RTCM (confermare che
      i reinit appaiono solo con RTCM iniettato — vedi `gps_dump_ber.py`).

### Sulla catena correzioni (base → QGC → drone)
- [ ] In QGC, `MAVLink Inspector`: il messaggio **`GPS_RTCM_DATA`** viene inviato al
      drone? (assenza = QGC non sta trasmettendo correzioni — già visto in passato,
      vedi `troubleshooting-rtk.md`).
- [ ] La **base** è connessa (`/dev/ttyACM*`) e ha completato il **survey-in**
      (accuracy < 1–2 m)? Oppure usare **Use Specified Base Position** per bypassarlo.
- [ ] Il **link telemetria** che trasporta l'RTCM regge il throughput in volo? In
      missione automatica QGC deve restare connesso perché l'RTCM continui ad arrivare.
- [ ] Messaggi RTCM3 corretti per il modulo (per F9P: 1005,1077,1087,1097,1127,1230;
      per il NEO-M8P attuale verificare il set MSM supportato).

### Decisione operativa
- [ ] Decidere se per le prove **serve** l'RTK (precisione cm) o se il **GPS 3D**
      (eph ~0.6 m) è sufficiente. Le prove pala si basano su IMU/ESC/assetto, non
      sulla posizione assoluta → spesso l'RTK non è necessario.
- [ ] Se l'RTK non serve per una data prova, **spegnerlo di proposito** (e annotarlo)
      così evitiamo anche il modo di guasto dei reinit.

## Piano per i log in arrivo

L'utente caricherà altri log a breve. Procedura:

1. Convertire (se servono i `.mcap`): `foxglove/ulog_to_mcap.py --auto-trim --satellite`.
2. **Classificare GPS vs RTK**: `python3 plot/gps_rtk_check.py <nuovi log>`.
3. Per i log RTK: verificare reinit/gap (`gps_dump_ber.py`) e trend float→fixed.
4. Annotare l'esito qui sotto e, se è una sessione nuova, nel README della data.

## Log analizzati

| Log | GPS o RTK | eph | RTCM | Note |
|---|---|---:|---:|---|
| `2026-06-04/13_15_11` | GPS puro | 0.68 m | 0 | volo lungo, 0 reinit |
| `2026-06-04/13_34_40` | GPS puro | 0.61 m | 0 | missione auto, 0 reinit |
| `2026-06-04/13_13_29` | RTK-float (a terra) | 0.40 m | 3.1/s | non convergente |
| `2026-06-04/12_28_29` | RTK reale | 0.02 m | 2.8/s | 7 reinit (volo collassato) |
| `2026-06-04/14_06_22` (Test 1) | RTK reale | 0.035 m | 3.1/s | volo corto 21 s, 0 reinit, sano |
| `2026-06-04/14_07_19` (Test 2) | RTK reale | 0.019 m | 3.1/s | **1 reinit → 28.4 s outage (38%) → failsafe ALTCTL → atterraggio manuale** |
| `2026-06-04/14_13_15` (Test 3) | GPS puro | 0.54 m | 0 | stessa missione quadrata, 124 s, 0 perdita GPS |

*(aggiornare la tabella man mano che arrivano nuovi log)*

## Esito sessione voli quadrati (≈16:06–16:15, pale sane) — A/B naturale

Tre voli a **traiettoria quadrata** (20 s hover + quadrato), pale sane, stesso
giorno: due in RTK reale, uno in GPS puro. **È l'esperimento A/B più pulito
finora**: a parità di traiettoria, solo il modo GPS cambia.

- **Test 2** (`14_07_19`, RTK reale, eph 1.9 cm) è **l'unico dei tre che ha perso
  il GPS**. Sequenza: `sensor_gps` si interrompe di colpo a rel 41.6 s (ultimo
  campione sanissimo: fix=5, eph 0.017 m, RTCM 3.5/s) → 28.4 s di blackout NAV →
  a rel 51.8 s l'EKF dichiara GPS perso → `nav_state` cade in **ALTCTL**
  (`failsafe=1`, sola quota, niente position-hold) → GPS recupera a rel 70.1 s
  (1 reboot driver) → POSCTL e atterraggio. Il passaggio in ALTCTL è il "preso
  il controllo manuale / atterraggio da solo" degli appunti.
- **Test 3** (`14_13_15`, GPS puro, RTCM=0) ha volato la **stessa missione** per
  124 s **senza alcuna perdita GPS**.

**Verdetto:** la perdita del Test 2 è legata al **modo RTK** (precondizione del
guasto), **non a una singola correzione RTCM corrotta** — il flusso RTCM era sano
fino all'orlo (`CRC fail=0`, rate stabile, eph 1.7 cm sull'ultimo campione). È il
fatto di iniettare RTCM nel ricevitore a innescare lo stallo del driver, coerente
con le sessioni precedenti.

> ⚠️ **Raffinamento del modello.** La metrica di gravità **non è il numero di
> reinit** ma la **durata dell'outage**: qui **1 solo reinit** ha causato 28.4 s
> di blackout e un failsafe operativo, mentre `11_54_05` (1 reinit, gap 2.0 s) era
> benigno. Il reboot driver è il *recupero*, non il grilletto.
