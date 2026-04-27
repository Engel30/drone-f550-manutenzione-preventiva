# Troubleshooting: Pixhawk 6X — GPS non aggancia satelliti dopo migrazione da CAN a UART

**Data**: 2026-04-27  
**Stato**: RISOLTO  
**Componente**: Pixhawk 6X, modulo GPS u-blox (protocollo UBX), porta GPS2

---

## Descrizione del problema

Dopo aver riconvertito il modulo GPS da DroneCAN a UART sulla porta GPS2 del Pixhawk 6X, il driver GPS non leggeva correttamente il dispositivo.

### Sintomi

- `gps status` in MAVLink console: `status: NOT OK`, `baudrate: 0`, `rate reading: 0 B/s`
- Nessun satellite agganciato in QGroundControl
- Il modulo era fisicamente collegato al connettore GPS2

### Causa

Doppia:

1. **Residui di configurazione DroneCAN**: il parametro `UAVCAN_ENABLE` rimaneva attivo, conflitto con il driver UART.
2. **Mismatch porta**: il parametro `GPS_1_CONFIG` era ancora impostato su GPS1 (valore `201`), mentre il cavo fisico era collegato a GPS2.

---

## Soluzione applicata

### Passo 1: Disabilitare DroneCAN

In **Vehicle Setup → Parameters** di QGroundControl:

```
UAVCAN_ENABLE = 0   (Disabled)
```

Salvare e **riavviare il Pixhawk** (riconnessione USB o power cycle).

**Verifica in MAVLink console:**
```
uavcan status
```

Deve rispondere: `ERROR [uavcan] application not running` (il driver non è attivo).

### Passo 2: Reindirizzare il GPS alla porta corretta

```
GPS_1_CONFIG = 202   (GPS 2)
```

Salvare e riavviare nuovamente.

**Verifica in MAVLink console:**
```
gps status
```

Deve mostrare:
- `protocol: UBX`
- `status: OK`
- `port: /dev/ttyS7` (o simile su 6X)
- `baudrate: 115200`
- `rate reading: ~800 B/s`

### Passo 3: Cold start all'aperto

Posizionare il drone all'aperto, cielo libero, per **5–10 minuti** senza ostacoli. Monitorare periodicamente:

```
listener sensor_gps
```

Aspettare che `fix_type` passi da 0 → 2 → 3 e `satellites_used` diventi ≥ 6. Successivamente il fix rimane stabile anche interno.

---

## Considerazioni e lezioni apprese

- **GPS vs I2C sul connettore GPS2**: il connettore espone sia UART sia I2C, ma il modulo u-blox comunica via **UART**, non I2C. L'I2C serve esclusivamente alla bussola del modulo. Non esiste una "modalità GPS via I2C" da attivare.

- **Parametri non presenti su 6X**: riferimenti in letteratura a `CAN_P1_DRIVER` e `CAN_P2_DRIVER` non esistono sul firmware attuale del 6X. Basta `UAVCAN_ENABLE = 0`.

- **Diagnostica RF**: se il problema persiste all'aperto, controllare i campi in `listener sensor_gps`:
  - `noise_per_ms`: target < 60 (alto = poco segnale o interferenza)
  - `jamming_indicator`: target < 30 (alto = ambiente RF rumoroso)
  - `automatic_gain_control`: alto = segnale debole

- **Manutenzione preventiva**: ogni cambio di firmware, parametri di comunicazione o riconfigurazione della porta GPS richiede una verifica della coppia `GPS_x_CONFIG` ↔ porta fisica usata.
