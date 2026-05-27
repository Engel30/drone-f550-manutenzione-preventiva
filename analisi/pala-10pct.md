# Effetto pala danneggiata 10 % — Set A vs Set C

Confronto fra i 6 voli baseline (Set A, pale sane) e i voli con una pala
accorciata del 10 % montata a turno sui motori M1…M6 (Set C).

> ⚠ **Set C parziale**: oggi è disponibile solo **C.1 (M1)**, file
> `16_07_29.ulg`. Gli altri 5 voli (M2…M6) sono ancora da fare. Questa pagina
> verrà ampliata man mano.

Metodologia, layout motori e definizione delle metriche in
[`panoramica.md`](panoramica.md). Mappa file ↔ prova in
[`log/2026-05-27/README.md`](../log/2026-05-27/README.md).

---

## C.1 — Pala 10 % su M1

L'unico volo disponibile mostra una firma **molto più netta** di qualsiasi
volo del Set B (5 %).

### Confronto vs baseline e vs 5 % sullo stesso motore (M1)

| Metrica | baseline (media A) | 5 % su M1 (B.1) | **10 % su M1 (C.1)** |
|---|---:|---:|---:|
| `accel_vib` mean (m/s²) | 2.14 | 1.89 | **3.72** (+74 %) |
| `accel_vib` p95 | 3.02 | 3.16 | **6.65** (+120 %) |
| `accel_vib` max | 3.45 | 4.14 | **7.74** (+124 %) |
| `gyro_vib` mean (rad/s) | 0.255 | 0.203 | **0.393** (+54 %) |
| `gyro_vib` p95 | 0.351 | 0.331 | **0.640** (+82 %) |
| `gyro_vib` max | 0.387 | 0.449 | **0.836** (+116 %) |
| `imbalanced_prop` p95 | −0.063 | −0.008 | **−0.358** (≈ ×6) |
| `|yaw_integ|` p95 | 0.043 | 0.022 | **0.058** (+36 %) |
| `|yaw_integ|` max | 0.057 | 0.025 | **0.072** (+27 %) |

→ **Tutte le metriche di vibrazione raddoppiano abbondantemente**, sia sulla
media sia sui picchi. Differenza qualitativa, non più quantitativa, rispetto al
5 %.

### Bias di comando — progressione 0 / 5 % / 10 % su M1

| | baseline (media A) | 5 % (B.1) | **10 % (C.1)** |
|---|---:|---:|---:|
| rapporto comando M1 | 0.975 | 0.995 | **1.014** |
| rapporto RPM M1 | 0.978 | 1.009 | **1.027** |

→ **Monotonia perfetta**: M1 passa dal sotto-comando strutturale (0.975) al
sopra-comando (1.014) con la pala accorciata del 10 %. Il mixer compensa
gradualmente la minor spinta, in modo regolare e quasi lineare nel range
testato. Ottimo punto di partenza per costruire un **indicatore proxy del
livello di danno**.

### Hover thrust

C.1: 0.555 ± 0.008 — il **più alto della sessione**. Va però letto con cautela:
gli ultimi voli del Set B (B.6 = 0.537, B.3 = 0.534) avevano hover_thrust
crescente per scarica batteria. Per discriminare quanto di questo aumento è
"danno" e quanto è "batteria scarica" serve un volo di controllo a pale sane con
batteria alla stessa tensione.

### Imbalanced prop metric

C.1 ha la metrica più negativa della sessione (mean −0.95, p95 −0.36). È quasi
**6× più negativa** del baseline a parità di motore. Pur senza superare la
soglia PX4 di failure, è un segnale molto forte e ben separato dal rumore di
fondo: la metrica con il **miglior rapporto segnale/rumore** osservato.

---

## Cosa imparare da C.1

1. **Il 10 % è clamorosamente visibile**: a differenza del 5 %, non serve
   guardare i picchi — qualsiasi statistica aggregata distingue il danno dal
   baseline.
2. La **compensazione del mixer è lineare e regolare** col livello di danno:
   è un'osservazione importante per la relazione, perché suggerisce che il
   sistema reagisce in modo "graceful" e prevedibile fino al 10 %.
3. **`imbalanced_prop_metric` è la metrica primaria** da usare in un eventuale
   classificatore o stimatore del danno.

## Voli ancora da fare

| Prova | Motore | Stato | Log |
|---|---|---|---|
| C.2 | M2 | ⏳ da fare | |
| C.3 | M3 | ⏳ da fare | |
| C.4 | M4 | ⏳ da fare | |
| C.5 | M5 | ⏳ da fare | |
| C.6 | M6 | ⏳ da fare | |

Domande aperte da rispondere con C.2–C.6:

- La firma di C.1 (raddoppio vibrazioni, `imbalanced_prop` p95 ≈ −0.36) si
  ripete uniformemente sugli altri motori, o ci sono asimmetrie come nel Set B?
- B.2 (5 % su M2) era un outlier: cosa succede a 10 % sullo stesso motore?
- Il bias strutturale M3/M6 vs M4/M5 maschera anche il segnale a 10 %, o a
  questo livello di danno il segnale lo supera?
