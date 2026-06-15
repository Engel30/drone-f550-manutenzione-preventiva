# Piano voli

Programma completo delle prove di volo richieste dal docente per lo studio
dell'effetto del danneggiamento delle pale sul comportamento dell'esacottero.

> ✅ **Campagna voli conclusa (2026-06-15).** Volati: i Set A–C (hover) il 27/05
> e 04/06; il Set D (quadrato 5 %) il 05/06; il **Set E (quadrato 10 %)** il
> 12/06 (+ il quadrato M5 5 % mancante del Set D). I **Set F e G (traiettoria
> casuale)** **non sono stati eseguiti**. Il 12/06 include inoltre un **blocco
> extra payload** (non previsto nei Set A–G): 2 voli liberi a pale sane + 3
> quadrati con pala accorciata su M2. Mappatura 12/06 in
> [`log/2026-06-12/README.md`](log/2026-06-12/README.md), verifica in
> [`maintenance/verifica-log-12-06-2026.md`](maintenance/verifica-log-12-06-2026.md).
> Prossima attività di progetto: la relazione.

> **Stato pale al 15 %**: le prove con danno **15 %** sono **rimandate** per
> indicazione del docente e **non vanno volate**. Restano in fondo al documento
> per riferimento futuro, marcate come `[SOSPESO]`.

Per gli appunti delle prove già eseguite vedi
[`log/2026-05-27/README.md`](log/2026-05-27/README.md).
Per le azioni bloccanti pre-volo vedi
[`maintenance/azioni-pre-prossimo-volo.md`](maintenance/azioni-pre-prossimo-volo.md).

---

## Riepilogo numerico

| Set | Tipo volo | Voli previsti | Voli eseguiti | Rimanenti |
|---|---|---:|---:|---:|
| A | Hover baseline, pale sane (swap posizione) | 6 | **6** | 0 |
| B | Hover con pala danneggiata 5 % (×6 motori) | 6 | **6** | 0 |
| C | Hover con pala danneggiata 10 % (×6 motori) | 6 | **6** | 0 |
| D | Quadrato 3×3 m, danno 5 % (2 sane + 12) | 14 | **13/14**¹ | 1 (D.12, rip. M5) |
| E | Quadrato 3×3 m, danno 10 % (2 sane + 12) | 14 | **14/14**² ✅ | 0 |
| F | Traiettoria casuale ~1 min, danno 5 % (2 sane + 12) | 14 | **0 — non eseguito** | 14 |
| G | Traiettoria casuale ~1 min, danno 10 % (2 sane + 12) | 14 | **0 — non eseguito** | 14 |
| **Totale attivo** | | **74** | **18 (A–C) + 13 (D) + 14 (E)** | F/G non eseguiti |
| P | **Payload** (extra, fuori piano A–G): 2 liberi sani + 3 quadrati M2 | — | **5** (06-12) | — |
| H | Hover con pala 15 % `[SOSPESO]` | (6) | 0 | (6) |
| I | Quadrato 3×3 m, danno 15 % `[SOSPESO]` | (14) | 0 | (14) |
| L | Traiettoria casuale, danno 15 % `[SOSPESO]` | (14) | 0 | (14) |

¹ **Set D** (5 % quadrato): 11 slot volati il **2026-06-05**
([`log/2026-06-05/README.md`](log/2026-06-05/README.md)) + lo slot **M5**
(D.11) recuperato il **2026-06-12** (Volo 1, `13_20_00`). Il 2° baseline (D.2)
riusa il baseline D.1 (pale sane = config identica). Resta solo **D.12**, la
ripetizione di M5 5 %: è stato volato **un solo** volo M5 5 % (D.11), senza
ripetizione.

² **Set E** (10 % quadrato) volato il **2026-06-12**
([`log/2026-06-12/README.md`](log/2026-06-12/README.md)): i 12 slot con pala
danneggiata sono mappati (sotto). I 2 baseline a pale sane (E.1/E.2) **riusano**
il baseline quadrato del Set D (`13_21_21.ulg`): essendo a pale sane la
configurazione è identica, non serve rivolarli → Set E **completo (14/14)**. I
**Set F e G (casuale)** non sono stati eseguiti. Il blocco **payload** (5 voli)
è aggiuntivo e non rientra in A–G.

---

## Set A — Hover baseline, pale sane (6 voli) ✅

6 voli in hovering Stabilize, ~1 minuto ciascuno, **con tutte e 6 le pale nuove**,
scambiando a ogni volo la posizione di **due pale**.

| # | Configurazione swap | Stato | Log |
|---|---|---|---|
| A.1 | pala 2 ↔ pala 4 | ✅ | `log/2026-05-27/13_56_40.ulg` |
| A.2 | pala 2 ↔ pala 5 | ✅ | `log/2026-05-27/14_00_42.ulg` |
| A.3 | pala 4 ↔ pala 5 | ✅ | `log/2026-05-27/14_05_57.ulg` |
| A.4 | pala 1 ↔ pala 3 | ✅ | `log/2026-05-27/14_09_26.ulg` |
| A.5 | pala 3 ↔ pala 6 | ✅ | `log/2026-05-27/14_12_24.ulg` |
| A.6 | pala 3 ↔ pala 6 (ripetuto) | ✅ | `log/2026-05-27/14_15_52.ulg` |

## Set B — Hover, pala danneggiata 5 % (6 voli) ✅

6 voli in hovering Stabilize, ~1 minuto ciascuno, una pala accorciata del 5 %
montata a turno su ciascuno dei 6 motori M1…M6.

| # | Motore con pala 5 % | Stato | Log |
|---|---|---|---|
| B.1 | M1 | ✅ | `log/2026-05-27/16_00_57.ulg` |
| B.2 | M2 | ✅ | `log/2026-05-27/15_47_35.ulg` |
| B.3 | M3 | ✅ | `log/2026-05-27/16_03_10.ulg` |
| B.4 | M4 | ✅ | `log/2026-05-27/15_50_20.ulg` |
| B.5 | M5 | ✅ | `log/2026-05-27/15_54_10.ulg` |
| B.6 | M6 | ✅ | `log/2026-05-27/16_05_24.ulg` |

## Set C — Hover, pala danneggiata 10 % (6 voli) ✅

6 voli in hovering Stabilize, ~1 minuto ciascuno, una pala accorciata del 10 %
montata a turno su ciascuno dei 6 motori M1…M6. C.2–C.6 completati il 2026-06-04
(vedi [`log/2026-06-04/README.md`](log/2026-06-04/README.md)).

| # | Motore con pala 10 % | Stato | Log |
|---|---|---|---|
| C.1 | M1 | ✅ | `log/2026-05-27/16_07_29.ulg` |
| C.2 | M2 | ✅ | `log/2026-06-04/12_39_37.ulg` |
| C.3 | M3 | ✅ | `log/2026-06-04/12_21_42.ulg` |
| C.4 | M4 | ✅ | `log/2026-06-04/12_43_47.ulg` |
| C.5 | M5 | ✅ | `log/2026-06-04/12_46_09.ulg` |
| C.6 | M6 | ✅ | `log/2026-06-04/12_28_29.ulg` |

---

## Set D — Traiettoria quadrata 3×3 m, danno 5 % (14 voli)

Tutti i voli: altezza ~3 m, traiettoria quadrata di lato ~3 m, con 30 s di
hovering prima di iniziare la traiettoria. Spostamenti sui singoli tratti a
**velocità differenti in ordine casuale** (es. 1, 1.5, 2, 2.5 m/s).

Eseguito il **2026-06-05** (vento 18–25 km/h). Mappatura completa file ↔ volo
in [`log/2026-06-05/README.md`](log/2026-06-05/README.md), incluse le numerose
ripetizioni extra per batteria scarica su M4 e M6.

| # | Configurazione | Stato | Log |
|---|---|---|---|
| D.1 | tutte le pale sane | ✅ | `log/2026-06-05/13_21_21.ulg` |
| D.2 | tutte le pale sane (ripetizione) | ↪️ riusa D.1 | `log/2026-06-05/13_21_21.ulg` (baseline pale sane condiviso) |
| D.3 | pala 5 % su M1 | ✅ | `log/2026-06-05/13_25_30.ulg` |
| D.4 | pala 5 % su M1 (ripetizione) | ✅ | `log/2026-06-05/13_32_25.ulg` |
| D.5 | pala 5 % su M2 | ✅ | `log/2026-06-05/14_08_33.ulg` |
| D.6 | pala 5 % su M2 (ripetizione) | ✅ | `log/2026-06-05/14_11_02.ulg` |
| D.7 | pala 5 % su M3 | ✅ | `log/2026-06-05/13_37_21.ulg` |
| D.8 | pala 5 % su M3 (ripetizione) | ✅ | `log/2026-06-05/13_40_36.ulg` |
| D.9 | pala 5 % su M4 | ✅ | `log/2026-06-05/14_17_24.ulg` |
| D.10 | pala 5 % su M4 (ripetizione) | ✅ | `log/2026-06-05/14_34_05.ulg` |
| D.11 | pala 5 % su M5 | ✅ | `log/2026-06-12/13_20_00.ulg` (Volo 1, 12/06) |
| D.12 | pala 5 % su M5 (ripetizione) | ⚠️ ripetizione non volata | — (eseguito **1 solo** volo M5 5 %, = D.11; nessun secondo volo da mappare) |
| D.13 | pala 5 % su M6 | ✅ | `log/2026-06-05/13_45_18.ulg` |
| D.14 | pala 5 % su M6 (ripetizione) | ✅ | `log/2026-06-05/14_05_24.ulg` |

## Set E — Traiettoria quadrata 3×3 m, danno 10 % (14 voli) ✅

Stessa procedura del Set D, sostituendo la pala 5 % con la pala 10 %.
Eseguito il **2026-06-12** (vento 15–25 km/h); mappatura e durate verificate in
[`log/2026-06-12/README.md`](log/2026-06-12/README.md) e
[`maintenance/verifica-log-12-06-2026.md`](maintenance/verifica-log-12-06-2026.md).

| # | Configurazione | Stato | Log |
|---|---|---|---|
| E.1 | tutte le pale sane | ↪️ riusa D.1 | `log/2026-06-05/13_21_21.ulg` (baseline quadrato, pale sane) |
| E.2 | tutte le pale sane (ripetizione) | ↪️ riusa D.1 | `log/2026-06-05/13_21_21.ulg` (baseline pale sane condiviso) |
| E.3 | pala 10 % su M1 | ✅ | `log/2026-06-12/13_27_52.ulg` (Volo 2) |
| E.4 | pala 10 % su M1 (ripetizione) | ✅ | `log/2026-06-12/13_33_16.ulg` (Volo 3) |
| E.5 | pala 10 % su M2 | ✅ | `log/2026-06-12/13_52_09.ulg` (Volo 8) |
| E.6 | pala 10 % su M2 (ripetizione) | ✅ | `log/2026-06-12/13_59_52.ulg` (Volo 11)³ |
| E.7 | pala 10 % su M3 | ✅ | `log/2026-06-12/13_37_29.ulg` (Volo 4) |
| E.8 | pala 10 % su M3 (ripetizione) | ✅ | `log/2026-06-12/13_40_32.ulg` (Volo 5) |
| E.9 | pala 10 % su M4 | ✅ | `log/2026-06-12/14_15_24.ulg` (Volo 15) |
| E.10 | pala 10 % su M4 (ripetizione) | ✅ | `log/2026-06-12/14_18_32.ulg` (Volo 16) |
| E.11 | pala 10 % su M5 | ✅ | `log/2026-06-12/14_06_38.ulg` (Volo 13)⁴ |
| E.12 | pala 10 % su M5 (ripetizione) | ✅ | `log/2026-06-12/14_09_45.ulg` (Volo 14) |
| E.13 | pala 10 % su M6 | ✅ | `log/2026-06-12/13_44_15.ulg` (Volo 6) |
| E.14 | pala 10 % su M6 (ripetizione) | ✅ | `log/2026-06-12/13_47_50.ulg` (Volo 7) |

³ M2 al 10 % ha **3 voli** (Volo 8, 10, 11): il **Volo 10** (`13_55_15`, 87 s)
è un atterraggio di emergenza per batteria scarica → ripetizione extra, non
conteggiata negli slot E.5/E.6.
⁴ M5 al 10 % ha **3 voli** (Volo 12, 13, 14): il **Volo 12** (`14_03_52`) non
si è alzato correttamente (errore magnetometro) → scartato; E.11/E.12 = Volo 13
e 14.

---

## Set F — Traiettoria casuale del pilota ~1 min, danno 5 % (14 voli) ❌ non eseguito

> ❌ **Non eseguito.** Le traiettorie casuali (Set F e G) non sono state volate
> nella campagna. Le tabelle restano per riferimento/eventuale ripresa.

Traiettorie casuali del pilota a velocità differenti, durata complessiva
~1 minuto a volo.

| # | Configurazione | Stato | Log |
|---|---|---|---|
| F.1 | tutte le pale sane | ⏳ da fare | |
| F.2 | tutte le pale sane (ripetizione) | ⏳ da fare | |
| F.3 | pala 5 % su M1 | ⏳ da fare | |
| F.4 | pala 5 % su M1 (ripetizione) | ⏳ da fare | |
| F.5 | pala 5 % su M2 | ⏳ da fare | |
| F.6 | pala 5 % su M2 (ripetizione) | ⏳ da fare | |
| F.7 | pala 5 % su M3 | ⏳ da fare | |
| F.8 | pala 5 % su M3 (ripetizione) | ⏳ da fare | |
| F.9 | pala 5 % su M4 | ⏳ da fare | |
| F.10 | pala 5 % su M4 (ripetizione) | ⏳ da fare | |
| F.11 | pala 5 % su M5 | ⏳ da fare | |
| F.12 | pala 5 % su M5 (ripetizione) | ⏳ da fare | |
| F.13 | pala 5 % su M6 | ⏳ da fare | |
| F.14 | pala 5 % su M6 (ripetizione) | ⏳ da fare | |

## Set G — Traiettoria casuale del pilota ~1 min, danno 10 % (14 voli) ❌ non eseguito

> ❌ **Non eseguito** (vedi nota al Set F).

Stessa procedura del Set F, sostituendo la pala 5 % con la pala 10 %.

| # | Configurazione | Stato | Log |
|---|---|---|---|
| G.1 | tutte le pale sane | ⏳ da fare | |
| G.2 | tutte le pale sane (ripetizione) | ⏳ da fare | |
| G.3 | pala 10 % su M1 | ⏳ da fare | |
| G.4 | pala 10 % su M1 (ripetizione) | ⏳ da fare | |
| G.5 | pala 10 % su M2 | ⏳ da fare | |
| G.6 | pala 10 % su M2 (ripetizione) | ⏳ da fare | |
| G.7 | pala 10 % su M3 | ⏳ da fare | |
| G.8 | pala 10 % su M3 (ripetizione) | ⏳ da fare | |
| G.9 | pala 10 % su M4 | ⏳ da fare | |
| G.10 | pala 10 % su M4 (ripetizione) | ⏳ da fare | |
| G.11 | pala 10 % su M5 | ⏳ da fare | |
| G.12 | pala 10 % su M5 (ripetizione) | ⏳ da fare | |
| G.13 | pala 10 % su M6 | ⏳ da fare | |
| G.14 | pala 10 % su M6 (ripetizione) | ⏳ da fare | |

---

## Set P — Voli con payload (blocco extra, fuori piano A–G) ✅

Test aggiuntivo dell'effetto del **payload** montato, eseguito il **2026-06-12**
(non previsto nel piano originale del docente). Due voli di riferimento a pale
sane su **traiettoria libera** del pilota, poi tre voli su **traiettoria
quadrata 3×3 m** con la pala accorciata su **M2**.

| # | Configurazione | Traiettoria | Stato | Log |
|---|---|---|---|---|
| P.1 | payload, pale sane | libera | ✅ | `log/2026-06-12/14_44_38.ulg` (Volo 17) |
| P.2 | payload, pale sane | libera | ✅ | `log/2026-06-12/14_50_12.ulg` (Volo 18) |
| P.3 | payload, pala 10 % su M2 | quadrato | ✅ | `log/2026-06-12/15_29_08.ulg` (Volo 19) |
| P.4 | payload, pala 10 % su M2 | quadrato | ✅ | `log/2026-06-12/15_31_52.ulg` (Volo 20) |
| P.5 | payload, pala 5 % su M2 | quadrato | ✅ | `log/2026-06-12/15_35_21.ulg` (Volo 21) |

---

## Set sospesi — danno 15 %

> Per decisione del docente, le prove con pala danneggiata al 15 % **non vanno
> eseguite per ora**. Le mantengo qui in attesa di eventuale ripresa.

### Set H — Hover, pala 15 % `[SOSPESO]` (6 voli)

Hover Stabilize, ~1 minuto, una pala accorciata 15 % a turno su M1…M6.

### Set I — Quadrato 3×3 m, danno 15 % `[SOSPESO]` (14 voli)

Stessa procedura dei Set D/E, con pala 15 %. 2 voli pale sane + 2 × 6 voli con
pala 15 % a turno su M1…M6.

### Set L — Traiettoria casuale ~1 min, danno 15 % `[SOSPESO]` (14 voli)

Stessa procedura dei Set F/G, con pala 15 %. 2 voli pale sane + 2 × 6 voli con
pala 15 % a turno su M1…M6.

---

## Convenzioni di registrazione log

Per ogni nuova sessione di voli:

1. Tutti i `.ulg` finiscono in `log/<YYYY-MM-DD>/`.
2. Si aggiunge un `README.md` in quella cartella che mappa `<file>.ulg` →
   `<set>.<#>` di questo piano + motore + tipo danno + tensione batteria
   (formato come [`log/2026-05-27/README.md`](log/2026-05-27/README.md)).
3. Si aggiorna la colonna **Log** della tabella corrispondente in questo
   documento e si marca lo stato come ✅.
4. Si aggiunge una voce in [`diario.md`](diario.md) per la giornata.
