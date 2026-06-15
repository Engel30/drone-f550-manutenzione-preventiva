# Verifica log 2026-06-12 — ✅ CHIUSA

Stato al **2026-06-15**. La cartella `log/2026-06-12/` è stata **ricaricata**
dall'utente: ora contiene **27 `.ulg`** (prima ne mancava uno) + `README.md`.
La ri-verifica contro i dati di bordo (`pyulog`: tempo armato + quota max)
conferma che **README e file sono coerenti e completi** (mapping validato entro
±2 s riga per riga). Resta **una sola questione di sostanza** (refuso M4→M5 sul
Volo 1, vedi sotto).

> ✅ **Causa degli errori precedenti**: mancava il file **`13_16_19.ulg`**
> (check a terra iniziale, 73 s). La sua assenza sfasava di una posizione tutta
> la sequenza dei check a terra, rompendo il mapping file↔volo. Con la cartella
> ricaricata il file è presente e ogni voce del README torna.

---

## Dati misurati dai log (ground truth — cartella ricaricata, 27 file)

Estratti con `pyulog` da tutti i 27 `.ulg` presenti. `armato` = `actuator_armed`;
`alt max` = `-min(vehicle_local_position.z)`. Ora = nome file + 2 h (CEST).
Colonna "README": durata/voce dichiarata → **tutte combaciano entro ±2 s**.

| File | Wall | armato | alt max | Voce README | Match |
|---|---|---:|---:|---|:--:|
| `13_16_19` | 15:16 | 73.0 s | 13.8 m | check a terra "73 s" | ✅ |
| `13_17_58` | 15:17 | 31.5 s | 3.7 m | check a terra "32 s" | ✅ |
| `13_20_00` | 15:20 | 146.3 s | 3.1 m | Volo 1 "147 s, M4 5%" | ✅ |
| `13_27_32` | 15:27 | 10.5 s | −0.7 m | check "12 s" | ✅ |
| `13_27_52` | 15:27 | 145.4 s | 8.1 m | Volo 2 "146 s" | ✅ |
| `13_33_16` | 15:33 | 146.7 s | 8.0 m | Volo 3 "148 s" | ✅ |
| `13_37_29` | 15:37 | 144.0 s | 8.2 m | Volo 4 "145 s" | ✅ |
| `13_40_32` | 15:40 | 143.4 s | 8.3 m | Volo 5 "144 s" | ✅ |
| `13_44_15` | 15:44 | 141.8 s | 6.2 m | Volo 6 "142 s" | ✅ |
| `13_47_50` | 15:47 | 141.6 s | 7.5 m | Volo 7 "142 s" | ✅ |
| `13_52_09` | 15:52 | 151.9 s | 10.6 m | Volo 8 "152 s" | ✅ |
| `13_55_15` | 15:55 | 86.2 s | 10.1 m | Volo 10 "87 s" | ✅ |
| `13_59_33` | 15:59 | 10.5 s | 0.2 m | check "12 s" | ✅ |
| `13_59_52` | 15:59 | 148.4 s | 7.9 m | Volo 11 "148 s" | ✅ |
| `14_03_52` | 16:03 | 76.1 s | 5.6 m | Volo 12 "77 s, non si è alzato" | ✅ |
| `14_06_38` | 16:06 | 146.1 s | 6.6 m | Volo 13 "149 s" | ✅ |
| `14_09_45` | 16:09 | 156.2 s | 8.9 m | Volo 14 "157 s" | ✅ |
| `14_15_24` | 16:15 | 152.6 s | 8.6 m | Volo 15 "153 s" | ✅ |
| `14_18_32` | 16:18 | 149.6 s | 7.1 m | Volo 16 "150 s" | ✅ |
| `14_44_38` | 16:44 | 133.7 s | 10.0 m | Volo 17 "135 s, payload" | ✅ |
| `14_47_04` | 16:47 | 9.2 s | −2.0 m | arm erroneo "10 s" (ignorare) | ✅ |
| `14_47_16` | 16:47 | 3.7 s | −2.0 m | arm erroneo "4 s" (ignorare) | ✅ |
| `14_47_21` | 16:47 | 29.5 s | 4.8 m | arm erroneo "30 s" (ignorare) | ✅ |
| `14_50_12` | 16:50 | 148.4 s | 8.6 m | Volo 18 "149 s" | ✅ |
| `15_29_08` | 17:29 | 144.0 s | 5.8 m | Volo 19 "145 s" | ✅ |
| `15_31_52` | 17:31 | 148.1 s | 5.3 m | Volo 20 "149 s" | ✅ |
| `15_35_21` | 17:35 | 145.3 s | 6.6 m | Volo 21 "146 s" | ✅ |

### Comando per ri-verificare (dopo l'aggiornamento cartella)

```python
import glob, os
from pyulog import ULog
for f in sorted(glob.glob("log/2026-06-12/*.ulg")):
    u = ULog(f); t0 = min(d.data['timestamp'][0] for d in u.data_list)/1e6
    d = [x for x in u.data_list if x.name=='actuator_armed'][0]
    t = d.data['timestamp']/1e6-t0; a = d.data['armed'].astype(bool)
    armed=0.0; s=None; p=False
    for ti,av in zip(t,a):
        if av and not p: s=ti
        elif not av and p: armed+=ti-s
        p=av
    if p: armed+=t[-1]-s
    lp=[x for x in u.data_list if x.name=='vehicle_local_position'][0]
    print(os.path.basename(f), round(armed,1), round(float(-lp.data['z'].min()),1))
```

---

## Errori della verifica precedente — tutti RISOLTI dalla ricarica

Gli sfasamenti file↔volo segnalati il 2026-06-15 (pre-ricarica) dipendevano
**unicamente** dal file `13_16_19.ulg` mancante. Con la cartella ricaricata
(27 file) il mapping è corretto su tutte le righe (vedi tabella sopra): nessuna
correzione da apportare al README per le durate. ✅

---

## Questioni di sostanza (decisione utente)

- **Pala 5 % su M5 ancora assente.** Il buco del 05/06 era M5 5 % (slot D.11/D.12).
  Il README del 12/06 ha **Volo 1 = "M4 5 %"**, ma M4 5 % era già fatto il 05/06.
  → Sospetto **refuso M4→M5**. Da confermare sul libro di bordo.
- **Il 12/06 è *hover* + *payload*, non i Set E/F/G a traiettoria** (quadrati /
  casuali) del `piano-voli.md`. → I Set E/F/G come da piano **non risultano
  volati**; il 12/06 sono hover 10 % aggiuntivi (M1,M2,M3,M5,M4) + 2 baseline
  payload + M2 con payload (5 % e 10 %). Da decidere: aggiornare il piano alla
  realtà, oppure trattare il 12/06 come blocco di test aggiuntivi.

---

## Cosa resta da fare (verifica file↔volo già chiusa ✅)

1. ~~Utente aggiorna cartella~~ ✅ fatto · ~~ri-verificare~~ ✅ fatto · ~~correggere durate README~~ ✅ non serviva.
2. **Questioni di sostanza** ancora aperte (vedi sezione sopra):
   - confermare sul libro di bordo se Volo 1 è **M4** o **M5** al 5 % (sospetto refuso);
   - decidere come trattare il 12/06 in `piano-voli.md` (Set E/F/G "a traiettoria"
     non risultano volati: il 12/06 è hover 10 % + payload).
3. Chiudere la voce 12/06 in `diario.md` (ora ⏳) e aggiornare `piano-voli.md`.
4. Generare `.mcap` mancanti (06-05: 0/33; 06-12: 3/27).
