# Log volo 2026-05-27 — Prove con pale modificate

Sessione dedicata allo studio dell'effetto di **posizionamento** e **danneggiamento**
delle pale sull'esacottero F550. Tutti i voli in modalità **Stabilize**.

> Nota: i timestamp nei nomi dei file `.ulg` sono ora locale Pixhawk, **2 ore
> indietro** rispetto al wall-clock. Es. `13_56_40.ulg` = volo delle 15:56:40.

## Set 1 — Baseline: pale sane, swap di posizione

Le 6 pale (numerate 1…6) sono montate sui 6 motori (M1…M6); in configurazione
"default" la pala `i` sta sul motore `Mi`. A ogni prova si scambia una coppia
di pale fra due motori per valutare eventuali accoppiamenti pala-motore.

| File | Wall time | Prova | Swap rispetto al default | V batt |
|---|---|---|---|---|
| `13_50_41.ulg` | 15:50:41 | Stab 0 (?) | nessuno (default) | — |
| `13_50_52.ulg` | 15:50:52 | Stab 0 (?) | nessuno (default) | — |
| `13_51_13.ulg` | 15:51:13 | Stab 0 (?) | nessuno (default) | — |
| `13_51_37.ulg` | 15:51:37 | Stab 0 (?) | nessuno (default) | — |
| `13_56_40.ulg` | 15:56:40 | Stab 1 | pala 2 ↔ pala 4 (su M2 e M4) | 15.4 V |
| `14_00_42.ulg` | 16:00:42 | Stab 2 | pala 2 ↔ pala 5 (su M2 e M5) | 15.2 V |
| `14_05_57.ulg` | 16:05:57 | Stab 3 | pala 4 ↔ pala 5 (su M4 e M5) | 15.0 V |
| `14_09_26.ulg` | 16:09:26 | Stab 4 | pala 1 ↔ pala 3 (su M1 e M3) | 14.9 V |
| `14_12_24.ulg` | 16:12:24 | Stab 5 | pala 3 ↔ pala 6 (su M3 e M6) | 14.9 V |
| `14_15_52.ulg` | 16:15:52 | Stab 6 | pala 3 ↔ pala 6 (ripetizione, V più bassa) | 14.8 V |

⚠ I 4 log fra le 15:50 e le 15:51 sono tutti candidati per Stab 0: probabilmente
1 prova reale + 3 tentativi di arming abortiti. Da identificare guardando la
durata armato / l'effettivo decollo.

Pre-test (non in note):
- `13_40_57.ulg` — 15:40:57

## Set 2 — Pala danneggiata 5%, ruotata per motore

Una pala accorciata del 5% su un lato (squilibrio statico). Si monta su un
motore alla volta, ruotando attraverso M1…M6. **L'ordine cronologico effettivo
in volo è stato M2 → M4 → M5 → M1 → M3 → M6**; la numerazione "Stab N" qui
sotto è quella assegnata negli appunti a posteriori.

| File | Wall time | Prova | Motore con pala 5% | V batt |
|---|---|---|---|---|
| `15_47_35.ulg` | 17:47:35 | Stab 2 | **M2** | — |
| `15_50_20.ulg` | 17:50:20 | Stab 3 | **M4** | — |
| `15_54_10.ulg` | 17:54:10 | Stab 1 | **M5** | 13.2 V |
| `16_00_57.ulg` | 18:00:57 | Stab 4 | **M1** | — |
| `16_03_10.ulg` | 18:03:10 | Stab 5 | **M3** | — |
| `16_05_24.ulg` | 18:05:24 | Stab 6 | **M6** | 14.8 V |

⚠ `15_50_20.ulg` corrisponde alla prova M4 annotata "17:52-17:53": c'è uno
scarto di ~2 min fra appunto e timestamp del log. Verificare durata volo per
escludere ambiguità.

## Set 3 — Pala danneggiata 10%, M1

| File | Wall time | Prova | Motore con pala 10% | V batt |
|---|---|---|---|---|
| `16_07_29.ulg` | 18:07:29 | Stab 1 | **M1** | — |

## Layout motori (PX4 hexa_x)

```
         fronte
           ▲
    M2 ─────── M6
   ╱             ╲
  M3              M5
   ╲             ╱
    M4 ─────── M1
```

(Numerazione PX4 standard hexa_x; confermare contro il mixer file del firmware
prima di interpretare per-motor outputs.)
