# Log volo 2026-06-05 — Set D: traiettoria quadrata, pala 5 %

Prima sessione delle prove di **traiettoria quadrata 3×3 m** del
[`piano-voli.md`](../../piano-voli.md) (**Set D** — danno **5 %**). Tutti i voli:
~20–30 s di hover poi quadrato di lato ~3 m a velocità differenti, una pala
accorciata del **5 %** montata a turno su un motore. La giornata copre anche i
voli baseline a pale sane.

> 🌬️ **Meteo**: vento **18–25 km/h** per tutta la sessione (condizione non
> ideale: utile per valutare la robustezza al disturbo, ma introduce variabilità
> nei dati di assetto/ESC non imputabile alle pale).

> Nota: i timestamp nei nomi dei file `.ulg` sono ora locale Pixhawk (UTC),
> **2 ore indietro** rispetto al wall-clock CEST degli appunti → `ora reale ≈
> nome file + 2 h` (es. `13_21_21.ulg` = volo delle 15:21). In caso di dubbio fa
> fede l'ora UTC del GPS nel log.

## Note pratiche

- **Sito di decollo**: Ancona (Università Politecnica delle Marche),
  lat 43.6008° N, lon 13.4821° E.
- **Come aprire i `.ulg`**: PX4 Flight Review (<https://review.px4.io>),
  QGroundControl, PlotJuggler, oppure `pyulog` (`ulog_info file.ulg`).
- **`.mcap` non ancora generati** per questa cartella. Per produrli:
  `python3 foxglove/ulog_to_mcap.py log/2026-06-05/<file>.ulg --auto-trim --satellite`.
- **Batteria**: le tensioni `[V]` provengono dagli **appunti di volo** (lettura
  esterna), riferimento qualitativo. Il power module di bordo è noto guasto
  (vedi `log/2026-06-04/README.md`): non fidarsi di `battery_status`.

---

## Mappa file ↔ piano voli

Tabella in ordine cronologico. `armato` e `alt max` sono **misurati dal log**
(`actuator_armed`, `vehicle_local_position`); servono a distinguere i voli reali
dagli arming a terra abortiti. I 18 "Volo N" sono la numerazione degli appunti;
la colonna **Set D** rimanda alle righe del piano voli.

| File | Wall CEST | armato | alt max | Volo (appunti) | Set D | Pala 5 % su | V batt | Note |
|---|---|---:|---:|---|---|---|---|---|
| `12_57_40.ulg` | 14:57 | 47.6 s | 9.2 m | — | — | — | — | pre-sessione (riscaldamento), non in appunti |
| `12_59_25.ulg` | 14:59 | 138.7 s | 16.4 m | — | — | — | — | pre-sessione (test quadrato), non in appunti |
| `13_06_51.ulg` | 15:06 | 182.0 s | 15.0 m | — | — | — | — | pre-sessione (test quadrato), non in appunti |
| `13_21_21.ulg` | 15:21 | 146.9 s | 12.1 m | **Volo 1** | **D.1** | pale sane | — | baseline; "GPS ok" |
| `13_25_30.ulg` | 15:25 | 145.7 s | 11.2 m | **Volo 2** | **D.3** | **M1** | — | |
| `13_32_04.ulg` | 15:32 | 11.0 s | 4.6 m | — | — | (M1) | — | arming abortito prima di Volo 3 |
| `13_32_25.ulg` | 15:32 | 149.8 s | 12.9 m | **Volo 3** | **D.4** | **M1** | 15.8 | ripetizione M1 |
| `13_37_21.ulg` | 15:37 | 151.9 s | 10.0 m | **Volo 4** | **D.7** | **M3** | — | |
| `13_40_36.ulg` | 15:40 | 147.5 s | 10.9 m | **Volo 5** | **D.8** | **M3** | — | ripetizione M3 |
| `13_45_18.ulg` | 15:45 | 152.4 s | 12.2 m | **Volo 6** | **D.13** | **M6** | 14.8 | |
| `13_48_10.ulg` | 15:48 | 10.4 s | 2.4 m | — | — | (M6) | — | arming abortito prima di Volo 7 |
| `13_48_31.ulg` | 15:48 | 99.8 s | 10.5 m | **Volo 7** | (M6, extra) | **M6** | — | annullato per batteria scarica → atterraggio manuale |
| `13_53_23.ulg` | 15:53 | 58.6 s | 3.3 m | — | (M6, extra) | (M6) | — | hop non in elenco (tentativo prima di Volo 8) |
| `13_54_31.ulg` | 15:54 | 197.1 s | 4.9 m | **Volo 8** | (M6, extra) | **M6** | 16.5 | portato in manuale al bordo geofence → hold → atterraggio a mano |
| `13_58_49.ulg` | 15:58 | 78.3 s | 4.4 m | — | (M6, extra) | (M6) | — | hop non in elenco (tra Volo 8 e 9) |
| `14_00_18.ulg` | 16:00 | 7.5 s | — | — | — | (M6) | — | arming abortito prima di Volo 9 |
| `14_00_57.ulg` | 16:00 | 67.2 s | 2.2 m | **Volo 9** | (M6, extra) | **M6** | — | ha ripreso dal 3° checkpoint e atterrato bene |
| `14_04_42.ulg` | 16:04 | 11.0 s | — | — | — | (M6) | — | arming abortito prima di Volo 10 |
| `14_05_24.ulg` | 16:05 | 142.7 s | 8.5 m | **Volo 10** | **D.14** | **M6** | — | ripetizione M6 (volo "pulito" di riferimento) |
| `14_08_33.ulg` | 16:08 | 142.0 s | 7.6 m | **Volo 11** | **D.5** | **M2** | — | |
| `14_11_02.ulg` | 16:11 | 148.5 s | 8.3 m | **Volo 12** | **D.6** | **M2** | — | ripetizione M2 |
| `14_15_51.ulg` | 16:15 | 12.9 s | — | — | — | (M4) | — | arming abortito |
| `14_16_12.ulg` | 16:16 | 94.3 s | 3.2 m | — | (M4, extra) | (M4) | — | volo non in elenco (prima di Volo 13) |
| `14_16_38.ulg` | 16:16 | 14.6 s | 0.2 m | — | — | (M4) | — | arming abortito |
| `14_17_24.ulg` | 16:17 | 87.4 s | 8.3 m | **Volo 13** | **D.9** | **M4** | 14.8 | batteria scarica |
| `14_20_13.ulg` | 16:20 | 14.1 s | 0.7 m | **Volo 14** | (M4, extra) | **M4** | 14.2 | volo in manuale per provare il comportamento a batteria scarica (molto breve/basso) |
| `14_20_32.ulg` | 16:20 | 8.4 s | 0.9 m | (Volo 14) | — | (M4) | — | arming/hop ravvicinato (parte di Volo 14) |
| `14_34_05.ulg` | 16:34 | 143.7 s | 6.3 m | **Volo 15** | **D.10** | **M4** | 15.8 | ripetizione M4 (volo "pulito" di riferimento) |
| `14_36_39.ulg` | 16:36 | 11.0 s | — | — | — | (M4) | — | arming abortito prima di Volo 16 |
| `14_36_57.ulg` | 16:36 | 73.6 s | 5.2 m | **Volo 16** | (M4, extra) | **M4** | — | atterraggio manuale per batteria scarica |
| `15_09_44.ulg` | 17:09 | 101.8 s | 11.2 m | **Volo 17** | (M4, extra) | **M4** | 15.1 | batteria scarica, atterraggio manuale (dopo cambio/ricarica pacco) |
| `15_12_45.ulg` | 17:12 | 13.1 s | 5.1 m | — | — | (M4) | — | arming abortito prima di Volo 18 |
| `15_13_10.ulg` | 17:13 | 57.2 s | 12.7 m | **Volo 18** | (M4, extra) | **M4** | — | batteria scarica, atterraggio manuale |

> Legenda **Set D**: i codici `D.x` sono lo slot del piano voli; le voci
> `(Mx, extra)` sono **ripetizioni reali in più** sullo stesso motore (rivoli per
> batteria scarica / atterraggi manuali), utili come dati aggiuntivi ma non
> contate fra i 14 slot nominali.

## ⚠️ Lacune del Set D (da chiarire prima della relazione)

Gli appunti del 5 giugno coprono **solo il danno 5 %** (Set D) e presentano due
buchi rispetto al piano (2 baseline + pala 5 % ×6 motori, 2 ripetizioni each):

1. **M5 non eseguito**: non c'è nessun volo con pala 5 % su **M5** (i motori
   coperti sono M1, M2, M3, M4, M6). → Slot **D.11/D.12 ancora scoperti.**
2. **Solo 1 volo baseline** (Volo 1) invece di 2. → Slot **D.2 scoperto.**

In compenso M6 e M4 hanno **molte ripetizioni in più** del previsto, quasi tutte
legate a problemi di **batteria scarica** (atterraggi manuali, voli annullati):
la giornata è stata condizionata dall'autonomia, non dalla procedura.

> Da verificare con i piloti se M5 5 % e il 2° baseline siano stati volati in
> un'altra sessione (es. 06-12) o vadano recuperati. Finché non chiarito, il
> Set D non è formalmente completo al 100 %.

## Osservazioni sui dati

- **Quote contenute** (alt max ~3–13 m): coerenti col profilo quadrato a ~3 m
  con hover iniziale; le quote più alte (12–16 m) sono nei voli di riscaldamento
  pre-sessione.
- **Vento 18–25 km/h**: da tenere presente nell'analisi assetto/ESC — parte
  dell'attività di controllo è reiezione del disturbo da vento, non effetto pala.
- **Batteria**: filo conduttore della seconda metà sessione (Voli 13–18 quasi
  tutti "batteria scarica"). Power module di bordo guasto → per lo stato di
  carica reale usare `esc_status.esc[*].esc_voltage`, non `battery_status`
  (stesso problema diagnosticato il 04/06).

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
prima di interpretare gli output per-motore.)
