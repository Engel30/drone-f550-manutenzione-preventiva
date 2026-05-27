# Piano voli da eseguire

Programma completo delle prove di volo richieste dal docente per lo studio
dell'effetto del danneggiamento delle pale sul comportamento dell'esacottero.

> **Stato pale al 15 %**: le prove con danno **15 %** sono al momento **rimandate**
> per indicazione del docente. Restano in fondo al documento per riferimento
> futuro, marcate come `[SOSPESO]`.

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
| C | Hover con pala danneggiata 10 % (×6 motori) | 6 | **1** | 5 |
| D | Quadrato 3×3 m, danno 5 % (2 sane + 12) | 14 | 0 | 14 |
| E | Quadrato 3×3 m, danno 10 % (2 sane + 12) | 14 | 0 | 14 |
| F | Traiettoria casuale ~1 min, danno 5 % (2 sane + 12) | 14 | 0 | 14 |
| G | Traiettoria casuale ~1 min, danno 10 % (2 sane + 12) | 14 | 0 | 14 |
| **Totale attivo** | | **74** | **13** | **61** |
| H | Hover con pala 15 % `[SOSPESO]` | (6) | 0 | (6) |
| I | Quadrato 3×3 m, danno 15 % `[SOSPESO]` | (14) | 0 | (14) |
| L | Traiettoria casuale, danno 15 % `[SOSPESO]` | (14) | 0 | (14) |

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

## Set C — Hover, pala danneggiata 10 % (6 voli) — 1/6

6 voli in hovering Stabilize, ~1 minuto ciascuno, una pala accorciata del 10 %
montata a turno su ciascuno dei 6 motori M1…M6.

| # | Motore con pala 10 % | Stato | Log |
|---|---|---|---|
| C.1 | M1 | ✅ | `log/2026-05-27/16_07_29.ulg` |
| C.2 | M2 | ⏳ da fare | |
| C.3 | M3 | ⏳ da fare | |
| C.4 | M4 | ⏳ da fare | |
| C.5 | M5 | ⏳ da fare | |
| C.6 | M6 | ⏳ da fare | |

---

## Set D — Traiettoria quadrata 3×3 m, danno 5 % (14 voli)

Tutti i voli: altezza ~3 m, traiettoria quadrata di lato ~3 m, con 30 s di
hovering prima di iniziare la traiettoria. Spostamenti sui singoli tratti a
**velocità differenti in ordine casuale** (es. 1, 1.5, 2, 2.5 m/s).

| # | Configurazione | Stato | Log |
|---|---|---|---|
| D.1 | tutte le pale sane | ⏳ da fare | |
| D.2 | tutte le pale sane (ripetizione) | ⏳ da fare | |
| D.3 | pala 5 % su M1 | ⏳ da fare | |
| D.4 | pala 5 % su M1 (ripetizione) | ⏳ da fare | |
| D.5 | pala 5 % su M2 | ⏳ da fare | |
| D.6 | pala 5 % su M2 (ripetizione) | ⏳ da fare | |
| D.7 | pala 5 % su M3 | ⏳ da fare | |
| D.8 | pala 5 % su M3 (ripetizione) | ⏳ da fare | |
| D.9 | pala 5 % su M4 | ⏳ da fare | |
| D.10 | pala 5 % su M4 (ripetizione) | ⏳ da fare | |
| D.11 | pala 5 % su M5 | ⏳ da fare | |
| D.12 | pala 5 % su M5 (ripetizione) | ⏳ da fare | |
| D.13 | pala 5 % su M6 | ⏳ da fare | |
| D.14 | pala 5 % su M6 (ripetizione) | ⏳ da fare | |

## Set E — Traiettoria quadrata 3×3 m, danno 10 % (14 voli)

Stessa procedura del Set D, sostituendo la pala 5 % con la pala 10 %.

| # | Configurazione | Stato | Log |
|---|---|---|---|
| E.1 | tutte le pale sane | ⏳ da fare | |
| E.2 | tutte le pale sane (ripetizione) | ⏳ da fare | |
| E.3 | pala 10 % su M1 | ⏳ da fare | |
| E.4 | pala 10 % su M1 (ripetizione) | ⏳ da fare | |
| E.5 | pala 10 % su M2 | ⏳ da fare | |
| E.6 | pala 10 % su M2 (ripetizione) | ⏳ da fare | |
| E.7 | pala 10 % su M3 | ⏳ da fare | |
| E.8 | pala 10 % su M3 (ripetizione) | ⏳ da fare | |
| E.9 | pala 10 % su M4 | ⏳ da fare | |
| E.10 | pala 10 % su M4 (ripetizione) | ⏳ da fare | |
| E.11 | pala 10 % su M5 | ⏳ da fare | |
| E.12 | pala 10 % su M5 (ripetizione) | ⏳ da fare | |
| E.13 | pala 10 % su M6 | ⏳ da fare | |
| E.14 | pala 10 % su M6 (ripetizione) | ⏳ da fare | |

---

## Set F — Traiettoria casuale del pilota ~1 min, danno 5 % (14 voli)

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

## Set G — Traiettoria casuale del pilota ~1 min, danno 10 % (14 voli)

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
