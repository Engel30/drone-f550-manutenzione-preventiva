# Log volo 2026-06-04 — Volo di accettazione cavo GPS schermato

Sessione di **validazione del cavo GPS rifatto con schermatura** (treccia +
drain wire, fissaggio hot-glue sui connettori, instradamento separato dai
cavi motore). Riferimenti:

- `maintenance/azioni-pre-prossimo-volo.md` — checklist A0.1–A0.5 (cavo)
- `maintenance/troubleshooting-gps-dropout-2026-05-27.md` — diagnosi originale
- `plot/gps_dump_ber.py` — script di analisi BER usato per la verifica

`GPS_DUMP_COMM = 1` mantenuto attivo per misurare quantitativamente il BER UART
del nuovo cavo nelle condizioni discriminanti (motori in regime di lift).

> Nota: i timestamp nei nomi dei file `.ulg` sono ora locale Pixhawk, **2 ore
> indietro** rispetto al wall-clock. Es. `11_52_13.ulg` = volo delle 13:52:13.

## File

| File | Wall time | Durata armato | Tipo | Note |
|---|---|---:|---|---|
| `11_50_58.ulg` | 13:50:58 | 10.7 s | Boot + init driver | Reboot/power-on Pixhawk: 3 reinit driver GPS, sequenza CFG-MSG → BER apparente 47% ma è artefatto di init (NMEA→UBX switch + ACK driver), non degrado del cavo. Da ignorare per la valutazione del link. |
| `11_51_42.ulg` | 13:51:42 | 11.0 s | Test motori idle | Arming breve in idle (sum-RPM ≈ 4 200, 0% in lift). Garbage 0.90%, 5.00 PVT/s, 0 reinit, 0 CRC fail → link OK ma non discrimina (test in idle). |
| `11_52_13.ulg` | 13:52:13 | **146.0 s** | **Volo di accettazione** | **Volo principale**. Manuale (STABILIZED). Motori in regime di lift per il 93% del tempo armato (sum-RPM media 29 372, max 37 354). **Garbage 0.24%, 4.91 PVT/s, 0 reinit, 0 gap `sensor_gps` > 2 s**. Condizione di carico equivalente a quella che il 27/05 portava al collasso il vecchio cavo (49% garbage). |

## Risultato

**Cavo schermato OK ✓** — A0.5 superato.

Il volo `11_52_13` riproduce esattamente la condizione meccanica che il 27/05
distruggeva il link UART (motori a regime di lift, lunga durata armato) e
mostra un BER praticamente fisiologico (0.24% vs 49% del peggior caso 27/05,
~200× meglio).

## Mappa file ↔ piano voli

Nessuno di questi voli appartiene al piano `piano-voli.md` (Set A/B/C/D/E/F/G):
sono **voli di validazione hardware**, non prove sperimentali sulle pale.

Coordinate decollo (da `vehicle_global_position`): lat **43.6008°N**,
lon **13.4821°E** (Università Politecnica delle Marche, Ancona).

## File `.mcap` generati

I `.mcap` sono stati prodotti con:

```bash
python3 foxglove/ulog_to_mcap.py log/2026-06-04/<file>.ulg --auto-trim --satellite
```

- `11_50_58.mcap` (6.9 MB) — senza overlay satellitare (`vehicle_global_position` non ancora disponibile al momento del trim).
- `11_51_42.mcap` (8.7 MB) — overlay satellitare 200×200 m attivo.
- `11_52_13.mcap` (107.5 MB) — overlay satellitare 200×200 m attivo.

## Analisi GPS — comando di riproduzione

```bash
python3 plot/gps_dump_ber.py log/2026-06-04/*.ulg
```

Output sintetico:

```
file                    armato     rx B   garb%  CRC  PVT/s  reinit  gap>2s  sumRPM
11_50_58.ulg             10.7s     4266  47.35%    2  0.91       3       0    4245
11_51_42.ulg             11.0s    10428   0.90%    0  5.00       0       0    4233
11_52_13.ulg            146.0s   118895   0.24%    4  4.91       0       0   29372
```
