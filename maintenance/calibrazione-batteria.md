# Calibrazione e configurazione del power module

> Procedura di setup e taratura del monitoraggio batteria sul Pixhawk 6X, inclusa la diagnostica del problema "battery_status never published" incontrato durante il commissioning.

## Hardware

Power module analogico (etichetta "PB01", 6 fili in uscita: 4 neri + 2 rossi) interposto tra batteria 4S 5600 mAh (E-01) e PDB del frame F550. Connesso al Pixhawk sulla porta **POWER1** via cavo a 6 pin.

Il power module svolge due funzioni indipendenti:
1. **Alimentazione** del flight controller a 5 V (linea VCC)
2. **Sensing** di tensione e corrente del bus principale (due segnali analogici letti dall'ADC del Pixhawk)

> **Nota BOM:** identificare modello esatto via QR sul power module e aggiornare `E-02` di conseguenza.

## Architettura del monitoraggio batteria in PX4

Il driver `battery_status` (modulo software) legge due canali ADC del Pixhawk e li converte in V/A tramite due fattori di scala:

```
V_batteria = V_ADC × BAT1_V_DIV
I_batteria = V_ADC × BAT1_A_PER_V
```

I parametri `BAT1_V_CHANNEL` e `BAT1_I_CHANNEL` indicano *quali* canali ADC leggere. Sul Pixhawk 6X di Holybro la porta POWER1 mappa sui canali **16 (tensione)** e **17 (corrente)**.

## Parametri configurati

| Parametro | Valore | Significato |
|-----------|-------:|-------------|
| `BAT1_SOURCE` | `0` | Power Module (sensing analogico via ADC) |
| `BAT1_N_CELLS` | `4` | Batteria 4S |
| `BAT1_V_CHANNEL` | `16` | Canale ADC tensione (POWER1 sul Pixhawk 6X) |
| `BAT1_I_CHANNEL` | `17` | Canale ADC corrente (POWER1 sul Pixhawk 6X) |
| `BAT1_V_DIV` | calibrato | Fattore di scala tensione (default 18.182) |
| `BAT1_A_PER_V` | calibrato | Fattore di scala corrente (default 36.364) |
| `BAT1_V_CHARGED` | `4.20` | V/cella a piena carica |
| `BAT1_V_EMPTY` | `3.20` | V/cella a scarica |
| `BAT1_CAPACITY` | `6700` | mAh |
| `SENS_EN_INA226/228/238` | `0` | Driver digitali I2C disabilitati (PM è analogico) |

## Procedura di calibrazione

### 1. Calibrazione tensione

Dopo aver impostato i parametri di base e riavviato il FC, con batteria collegata (eliche **rimosse**):

1. Misurare la tensione reale ai morsetti XT60 con multimetro
2. In QGC → *Vehicle Setup → Power* → click su **Calculate** accanto a *Voltage Divider*
3. Inserire il valore misurato → OK
4. `BAT1_V_DIV` viene ricalcolato come `BAT1_V_DIV_attuale × (V_misurata / V_letta)`
5. Verificare che la tensione mostrata in QGC coincida con il multimetro entro ±0.05 V

### 2. Calibrazione corrente (richiede pinza amperometrica DC)

Con eliche rimosse, drone vincolato:

1. Armare e portare i motori a throttle medio costante (es. 30 %)
2. Misurare la corrente vera con pinza amperometrica DC sul cavo positivo della batteria
3. In QGC → click **Calculate** accanto a *Amps per Volt*
4. Inserire il valore misurato → OK

In assenza di pinza amperometrica, lasciare `BAT1_A_PER_V = 36.364` (default Holybro). Per il monitoraggio di trend è sufficiente che la lettura sia *consistente nel tempo*, non assolutamente esatta.

### 3. Calcolo manuale (fallback se Calculate non funziona)

```
BAT1_V_DIV_nuovo = BAT1_V_DIV_attuale × (V_multimetro / V_QGC)
```

Esempio: V_QGC = 14.20 V, V_multimetro = 16.55 V, attuale = 18.182:
```
nuovo = 18.182 × (16.55 / 14.20) = 21.19
```

Scrivere il valore manualmente in *Parameters → BAT1_V_DIV*, salvare, riavviare.

## Troubleshooting incontrato

### Problema 1: `battery_status never published`

**Sintomi:**
- Modulo `battery_status` running (verificato con `battery_status status`)
- Nessuna pubblicazione del topic (`listener battery_status` → "never published")
- QGC mostra 0 V / nessuna lettura

**Causa:** `BAT1_V_CHANNEL` e `BAT1_I_CHANNEL` impostati a `-1` (sentinella "default board"). Il board file PX4 1.16.2 per FMUv6X non auto-popola questi canali sul carrier board in uso, quindi il driver non si abbona a nessun canale ADC e non pubblica nulla.

**Soluzione:** impostare esplicitamente `BAT1_V_CHANNEL = 16` e `BAT1_I_CHANNEL = 17`, salvare, riavviare il FC.

### Problema 2: pulsante "Calculate" inerte

**Causa:** con `BAT1_V_DIV = -1` la formula del Calculate (`nuovo = vecchio × misurata/letta`) parte da `-1` × ratio → QGC non scrive il risultato.

**Soluzione:** impostare manualmente `BAT1_V_DIV = 18.182` e `BAT1_A_PER_V = 36.364` come valori iniziali plausibili. Riavviare. A quel punto la formula del Calculate ha valori finiti e funziona.

## Verifica finale del setup

Dalla MAVLink Console di QGC:
```
listener battery_status
```

Output atteso (esempio con 4S carica):
```
voltage_v: 16.55
current_a: 0.30
discharged_mah: ...
cell_count: 4
```

## Cross-check diagnostico

Una volta calibrato il power module, è disponibile un controllo incrociato utile per la manutenzione preventiva:

```
sum(esc_status.esc_current[0..5])  ≈  battery_status.current_a
```

La somma delle correnti riportate dai 6 ESC deve coincidere con la corrente di bus misurata dal power module entro un piccolo errore (alcuni %, dovuto al consumo del BEC del flight controller). Discrepanze persistenti indicano:
- un ESC con calibrazione corrente errata
- una perdita anomala nel cablaggio
- un problema di calibrazione del power module

Questo cross-check è realizzabile in PlotJuggler trascinando entrambi i segnali nello stesso plot.
