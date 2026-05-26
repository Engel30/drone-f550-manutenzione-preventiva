# Troubleshooting RTK — QGroundControl + PX4

## Sintomo iniziale

Durante l'atterraggio autonomo, PX4 disattiva l'autopilota con errore `no valid position estimate`. RTK mai arrivato a Fixed: sempre Float.

## Diagnosi

L'errore EKF2 deriva dalla mancanza di un fix RTK affidabile. Indagando:

1. Il messaggio MAVLink `GPS_RTCM_DATA` non compariva nell'Inspector → QGC non stava inviando correzioni al drone.
2. La base RTK è collegata via USB (visibile su `/dev/ttyACM*`).
3. Survey-in convergeva lentamente: dopo 200 s, accuracy ferma a **3.6 m** (necessaria < 2 m, ideale < 1 m).

## Causa radice

Survey-in con accuracy 3.6 m è insufficiente per risolvere le ambiguità di fase intera lato rover → il rover non raggiunge mai RTK Fixed, resta in Float (precisione 20-50 cm) o peggio in SBAS.

La lenta convergenza è quasi sempre dovuta a **multipath** e **vista cielo parziale** sulla base, non al tempo di osservazione (la curva ~1/√t si appiattisce in presenza di bias sistematico).

## Soluzioni

### A. Migliorare il setup della base (soluzione strutturale)

- **Ground plane metallico** sotto l'antenna base (disco alluminio ≥ 10 cm) — riduce multipath del 50-80%.
- Antenna sollevata ≥ 1.5 m da terra, su treppiede.
- Cielo aperto, lontano da edifici/alberi/auto/cavi.
- Lontano da fonti EMI (PC, WiFi, radio) di almeno 2 m.

Target: survey-in < 1 m in 2-3 minuti.

### B. Posizione fissa della base (workaround rapido)

QGC → Application Settings → General → RTK GPS → **Use Specified Base Position**.

- Bypassa il survey-in: rover va a Fixed in 30-60 s.
- L'**altitudine** va inserita come altezza ellissoidica WGS84 (NON quota slm; differenza in Italia ~45-50 m).
- Precisione assoluta limitata dall'errore della posizione data alla base; precisione **relativa** centimetrica → adatto a voli ripetuti dallo stesso punto.

### Configurazione QGC raccomandata

- Accuracy survey-in: **1.0 m**
- Min Duration: **300 s**

## Parametri PX4 rilevanti

- `EKF2_GPS_CTRL` — bitmask, default 7 ok
- `EKF2_HGT_REF` — impostare a `GPS` (1) per atterraggi di precisione con RTK
- `EKF2_REQ_EPH`, `EKF2_REQ_EPV`, `EKF2_REQ_SACC` — soglie minime accettazione GPS dall'EKF
- `GPS_UBX_DYNMODEL` = 7 (airborne <2g) per u-blox

## Secondo modo di guasto: desincronizzazione UART → reset driver GPS

**Osservato nel log** `log_current/10_45_41.ulg` (volo del 2026-05-26).

### Sintomi nel log di QGC

Durante la fase di atterraggio autonomo (RTL → land at destination) compare la sequenza:

```
[mc_pos_control] invalid setpoints
[mc_pos_control] Failsafe: blind land
[failsafe] Failsafe activated
[gps] u-blox firmware version: HPG 1.40ROV
[gps] u-blox protocol version: 20.30
[gps] u-blox module: NEO-M8P-0
[gps] ubx msg 0x0103 invalid len 64528
[gps] u-blox firmware version: HPG 1.40ROV
...
[health_and_arming_checks] Preflight Fail: Strong magnetic interference
```

### Interpretazione

Il trio `firmware version` / `protocol version` / `module` **non è log periodico**: il driver `gps` di PX4 lo stampa solo a (ri)apertura del device dopo aver interrogato `MON-VER`. Vederlo ripetuto = il driver ha resettato il modulo.

La riga chiave è `ubx msg 0x0103 invalid len 64528`: il parser UBX ha trovato il sync header `0xB5 0x62` ma il campo lunghezza è spazzatura (≈ 0xFC10). È **desincronizzazione del flusso UART**, non un guasto del modulo. Dopo N pacchetti corrotti consecutivi il driver chiude la porta, fa `CFG-RST` e re-interroga il modulo — da cui il trio di righe.

### Causa radice probabile

Tre indizi convergono verso EMI / brown-out sul cavo GPS in fase ad alta corrente:

1. La desincronizzazione UART si manifesta **durante l'atterraggio autonomo**, quando i motori reagiscono con correnti più variabili per stabilizzare la quota.
2. Il messaggio finale `Preflight Fail: Strong magnetic interference` conferma che a fine volo il campo magnetico era pesantemente disturbato: EMI sul magnetometro = EMI plausibile anche sul UART GPS che corre nello stesso fascio.
3. Il F550 ha la PDB integrata nella piastra inferiore, quindi i cavi motore corrono molto vicini al cavo GPS che sale al mast.

In alternativa (o in concorso): sag di tensione sul rail che alimenta il modulo u-blox in transitorio motori → reset spontaneo del modulo.

### Mitigazioni proposte

- **Ferrite clip** sul cavo GPS in prossimità del connettore Pixhawk.
- **Separazione fisica** cavo GPS ↔ cavi fase motore (passaggio dal lato opposto del frame se possibile).
- **Verifica `noise_per_ms` e `jamming_indicator`** in `listener sensor_gps` durante un hover statico ad alta corrente (cfr. `troubleshooting-gps-pixhawk6x.md`).
- Plot dedicato in `plot/incidente/` che correli `sensor_gps.noise_per_ms`, `sensor_gps.jamming_indicator`, `satellites_used`, corrente di batteria e `vehicle_status.nav_state` per verificare la coincidenza temporale tra picco di corrente e reset GPS.

## Da fare

- [ ] Test con ground plane sotto antenna base
- [ ] Verifica costellazioni attive sulla base (GPS+GLONASS+Galileo)
- [ ] Decidere tra soluzione A (operativa) o B (punto fisso laboratorio)
- [ ] Una volta raggiunto Fixed stabile a terra, ripetere il volo con landing
- [ ] Formalizzare procedura pre-volo RTK in checklist dedicata
- [ ] Aggiungere modo di guasto in FMEA: "Survey-in base RTK non converge → degradazione posizione → abort missione in landing"
- [ ] Aggiungere secondo modo di guasto in FMEA: "EMI/sag sul UART GPS in fase ad alta corrente → desincronizzazione UBX → reset driver GPS → buchi nella stima di posizione → blind land failsafe"
- [ ] Script `plot/incidente/analisi_gps.py` per correlare reset GPS, corrente batteria e qualità RF sul log `10_45_41.ulg`

## Riferimenti

- [PX4 RTK GPS docs](https://docs.px4.io/main/en/advanced_features/rtk-gps.html)
- Flight Review (analisi log): https://logs.px4.io
- Messaggi RTCM3 minimi per F9P: 1005, 1077, 1087, 1097, 1127, 1230
