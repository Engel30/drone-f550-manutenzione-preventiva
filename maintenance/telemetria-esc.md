# Telemetria ESC — Tekko32 F4 45A (AM32)

> Stato: **da implementare** — telemetria non funzionante per errore di cablaggio

## Panoramica componente

| Parametro | Valore |
|-----------|--------|
| Modello | Holybro Tekko32 F4 45A ESC |
| Firmware | AM32 (`AM32_TEKKO32_F421`) |
| MCU | ARM 32-bit F4 (150 MHz) |
| Corrente continua | 45A |
| Tensione ingresso | 2–6S LiPo |
| Protocolli segnale | DShot 150/300/600/1200, PWM, OneShot, MultiShot |
| Quantità | 6 (uno per motore) |
| BOM ID | P-02 |

## Capacità di telemetria

Gli ESC Tekko32 F4 con firmware AM32 supportano la **telemetria KISS standard** tramite un filo dedicato. I dati trasmessi sono:

- **Temperatura** MOSFET dell'ESC
- **Tensione** batteria (misurata dall'ESC)
- **Corrente** assorbita dal singolo motore
- **Consumo accumulato** (mAh)
- **RPM** del motore (eRPM, convertiti in RPM reali dal flight controller)

Esiste anche il **DShot bidirezionale** (RPM sullo stesso filo del segnale motore), ma richiede MCU STM32H7 o i.MXRT. Il Cube Black monta un STM32F427, quindi questa modalità **non è disponibile**. L'unica strada è la **telemetria UART**.

## Situazione attuale

I fili di telemetria dei 6 ESC sono correttamente **uniti tra loro** (collegati in parallelo), ma il filo risultante è collegato alla porta **SBUSo/CONS** sulla carrier board del Cube Black.

**Questo collegamento è errato.** Nessuna delle due porte può ricevere telemetria ESC, per motivi architetturali diversi.

### Perché SBUSo non può funzionare

Il Cube Black ha un'architettura **dual-processor**:

```
┌─────────────────────────────────────────────────────┐
│                    CUBE BLACK                        │
│                                                      │
│  ┌────────────────────────┐  ┌────────────────────┐ │
│  │   FMU (principale)     │  │      PX4IO         │ │
│  │   STM32F427            │  │    STM32F103       │ │
│  │                        │  │   (co-processore)  │ │
│  │  • Flight stack PX4    │  │                    │ │
│  │  • Parametri           │  │  • PWM output      │ │
│  │  • TELEM1, TELEM2      │  │  • SBUS input      │ │
│  │  • GPS1, GPS2          │  │  • SBUSo output    │ │
│  │  • CONSOLE             │  │  • Failsafe        │ │
│  └───────────┬────────────┘  └──────────┬─────────┘ │
│              │      UART7 (bus interno)  │           │
│              └───────────────────────────┘           │
└─────────────────────────────────────────────────────┘
```

La porta **SBUSo** è gestita dal **PX4IO** (STM32F103), un processore separato dal FMU principale. Questo comporta tre problemi:

1. **Processore sbagliato** — il dato arriverebbe al PX4IO, che non implementa il protocollo KISS telemetry. Anche se lo facesse, non è prevista la ritrasmissione dei dati al FMU via UART7.
2. **Solo output** — nel firmware PX4IO quel pin è configurato come uscita (trasmissione). Non esiste codice che legga dati in ingresso su quella linea.
3. **Protocollo incompatibile** — SBUS usa segnale invertito a 100.000 baud; la telemetria KISS degli ESC usa UART standard (non invertito) a 115.200 baud. Anche a livello elettrico sono incompatibili.

SBUSo **non è una UART general-purpose** del processore principale: è un'uscita dedicata su un co-processore separato, e non è configurabile via parametri PX4.

### Perché CONS non può funzionare

La porta **CONS** (UART8, `/dev/ttyS6`) è la system console del Cube Black:

1. **Inizializzata dal bootloader NuttX** prima ancora che PX4 parta — è la prima periferica attiva all'avvio, usata per log di boot e accesso alla shell di debug.
2. **Non selezionabile in `DSHOT_TEL_CFG`** — il parametro offre come opzioni solo le porte "normali" (TELEM1, TELEM2, GPS1, GPS2). La console non compare tra le scelte.
3. **Perdita del debug** — riprogrammarla significherebbe perdere l'unico accesso diretto alla console di sistema, fondamentale per diagnostica di boot, crash e aggiornamenti firmware.

### Riepilogo porte analizzate

| Porta | Processore | Direzione | Protocollo | Configurabile PX4 | Utilizzabile per telemetria ESC |
|-------|-----------|-----------|------------|-------------------|-------------------------------|
| **SBUSo** | PX4IO (STM32F103) | Solo output | SBUS invertito, 100k baud | No | **No** |
| **CONS** | FMU (STM32F427) | I/O (riservata) | Console NuttX, 57600 baud | No | **No** |
| **TELEM2** | FMU (STM32F427) | Bidirezionale | UART standard | Sì (`DSHOT_TEL_CFG`) | **Sì** |

Di conseguenza, il flight controller non riceve alcun dato di feedback dai motori. La porta corretta è **TELEM2**.

## Obiettivo

Rendere funzionante la telemetria ESC per poter monitorare in tempo reale:

- RPM individuali dei 6 motori (rilevamento sbilanciamenti, cuscinetti usurati)
- Corrente assorbita per motore (individuazione eliche danneggiate, problemi meccanici)
- Temperatura ESC (prevenzione surriscaldamento)
- Tensione batteria vista da ciascun ESC

Questi dati sono fondamentali per la **manutenzione preventiva**: permettono di identificare degradazione e anomalie prima che causino guasti in volo.

## Procedura di implementazione

### Fase 1 — Ricablaggio hardware

1. **Scollegare** il filo telemetria dalla porta SBUSo/CONS
2. Collegare il filo telemetria unificato dei 6 ESC alla porta **TELEM2** (USART2) della carrier board:
   - **Pin 3 (RX)** ← filo telemetria ESC
   - **Pin 6 (GND)** ← massa comune (deve esserci un ground condiviso tra ESC e FC)
   - Gli altri pin di TELEM2 non servono per questa funzione
3. Se necessario, procurare un connettore **JST-GH a 6 pin** compatibile con TELEM2, oppure saldare il filo telemetria al pin RX di un cavo TELEM2 esistente

#### Mappa UART del Cube Black

| UART | Device | Porta carrier board | Utilizzo attuale | Disponibile |
|------|--------|---------------------|------------------|-------------|
| USART1 | /dev/ttyS0 | — | General purpose | Sì |
| USART2 | /dev/ttyS1 | **TELEM2** | — | **Sì (scelta consigliata)** |
| USART3 | /dev/ttyS2 | TELEM1 | Telemetria Holybro 433 MHz | No |
| UART4 | /dev/ttyS3 | GPS1 | CubePilot Here+ | No |
| USART6 | /dev/ttyS4 | GPS2 | — | Sì (alternativa) |
| UART7 | /dev/ttyS5 | PX4IO | Co-processore interno | No |
| UART8 | /dev/ttyS6 | CONSOLE | System console (NuttX) | No |

### Fase 2 — Configurazione software (QGroundControl)

In QGroundControl → **Parameters**, impostare:

| Parametro | Valore | Descrizione |
|-----------|--------|-------------|
| `DSHOT_TEL_CFG` | `TELEM2` | Abilita ricezione telemetria ESC sulla porta TELEM2 |
| `MOT_POLE_COUNT` | `14` | Numero poli magnetici dei motori AIR2213 (da verificare — tipico per outrunner di questa classe). Serve per convertire eRPM in RPM reali: `RPM = eRPM / (poli / 2)` |

**Riavviare** il flight controller dopo aver modificato i parametri.

### Fase 3 — Verifica

> **Prerequisito**: il flight controller deve essere alimentato con la **batteria** (non solo USB), altrimenti gli ESC non sono attivi e non trasmettono telemetria.

1. Aprire QGroundControl → **Analyze Tools** → **MAVLink Console**
2. Eseguire il comando per ogni motore (da 1 a 6):
   ```
   dshot esc_info -m 1
   ```
3. Se la telemetria funziona, l'output mostrerà:
   - Versione firmware ESC
   - Temperatura attuale
   - Tensione e corrente
   - RPM
4. Verificare che tutti e 6 gli ESC rispondano correttamente

### Possibili problemi

| Problema | Causa probabile | Soluzione |
|----------|----------------|-----------|
| Nessun dato da nessun ESC | Filo telemetria non sul pin RX corretto | Verificare pinout connettore TELEM2 |
| Dati solo da alcuni ESC | Saldatura/giunzione fili telemetria difettosa | Ricontrollare i collegamenti tra i 6 fili |
| RPM non realistici | `MOT_POLE_COUNT` errato | Verificare il numero esatto di poli dell'AIR2213 |
| Telemetria intermittente | Interferenze o ground non condiviso | Verificare collegamento GND e schermatura cavi |

## Riferimenti

- [PX4 — DShot & ESC Telemetry](https://docs.px4.io/main/en/peripherals/dshot.html)
- [PX4 — Cube Black (Pixhawk 2)](https://docs.px4.io/main/en/flight_controller/pixhawk-2.html)
- [Holybro Tekko32 F4 45A ESC](https://www.holybro.com/products/tekko32-f4-45a-esc)
