# Progetto Manutenzione Preventiva — Esacottero F550

> Corso di Manutenzione Preventiva — A.A. 2025/2026
> Università — Team: Angelo, Matteo, Federico

## A cosa serve questa repo

Repository di lavoro per il progetto di **manutenzione preventiva** di un esacottero
DJI F550 equipaggiato con Pixhawk 6X e firmware PX4. Qui raccogliamo, in modo
versionato e ordinato:

- la **documentazione tecnica** del drone (BOM, datasheet, schemi),
- i **piani di manutenzione** (checklist pre/post volo, FMEA, troubleshooting),
- i **log di volo** (`.ulg` PX4) e gli strumenti per analizzarli (Foxglove, matplotlib),
- gli **script di plotting** usati per ispezionare IMU, ESC, batteria e diagnosticare problemi.

L'output finale del corso sarà una **relazione tecnica** sulle attività di
manutenzione preventiva svolte sul drone; questa repo è la base di lavoro da cui
verrà estratta.

> ⚠️ Repo in evoluzione: contenuti e struttura non sono ancora definitivi.

## Struttura della repository

```
manutenzione-preventiva-freddi/
├── README.md              # Questo file
├── CLAUDE.md              # Istruzioni di lavoro per Claude Code
│
├── docs/
│   ├── BOM.md             # Bill of Materials (componenti, modelli, codici ID)
│   └── datasheets/        # Datasheet PDF dei componenti
│
├── img/                   # Foto, schemi e diagrammi del drone
│
├── maintenance/           # Documentazione di manutenzione e diagnostica
│   ├── stato-lavori.md
│   ├── azioni-pre-prossimo-volo.md
│   ├── calibrazione-batteria.md
│   ├── configurazione-logging.md
│   ├── telemetria-esc.md
│   ├── test-a-banco.md
│   ├── troubleshooting-gps-pixhawk6x.md
│   ├── troubleshooting-rtk.md
│   └── troubleshooting-cube-black-usb.md
│
├── log/                   # Archivio storico log .ulg (sottocartelle per data)
├── log_current/           # Log "corrente" in analisi + .mcap convertito
│
├── foxglove/              # Visualizzazione 3D dei log
│   ├── ulog_to_mcap.py    # Conversione .ulg → .mcap per Foxglove Studio
│   ├── f550.urdf          # Modello 3D dell'esacottero
│   ├── drone f550.json    # Layout pannelli Foxglove
│   ├── satellite_layer.py
│   └── terreno-3d.md
│
└── plot/                  # Script matplotlib di analisi log
    ├── run_all.py         # Esegue tutti i plot sul log corrente
    ├── info_log.py        # Estrae metadati dal .ulg
    ├── imu/               # Plot accelerometro, giroscopio, sensor voting
    ├── esc/               # Plot RPM, corrente, temperatura ESC
    ├── batteria/          # Plot tensione, corrente, capacità residua
    └── incidente/         # Analisi forense dello schianto del 2026-04-28
```

## Componenti principali (estratto BOM)

| Categoria | Componente | Modello |
|-----------|------------|---------|
| Frame | DJI F550 (esacottero) | PDB integrata nella piastra inferiore |
| Flight Controller | Pixhawk 6X | 3 IMU ridondanti, firmware PX4 |
| Motori | AIR2213 KV920 ×6 | 3 CW + 3 CCW |
| ESC | Tekko32 F4 ×6 | Telemetria DShot |
| GPS | CubePilot Here+ | Montato su mast anti-EMI, base RTK |
| Telemetria | Holybro 433 MHz | Link verso QGroundControl |
| Batteria | LiPo 4S 5600 mAh | — |
| GCS | QGroundControl | — |

Dettaglio completo e codici ID in [`docs/BOM.md`](docs/BOM.md).

## Workflow tipico

1. **Volo** → il Pixhawk salva un `.ulg` su SD card.
2. Il log viene archiviato in `log/<YYYY-MM-DD>/` e copiato in `log_current/`.
3. `foxglove/ulog_to_mcap.py` produce un `.mcap` per visualizzazione 3D in Foxglove Studio.
4. `plot/run_all.py` genera i grafici di IMU, ESC e batteria per ispezione.
5. Anomalie e azioni correttive vengono documentate in `maintenance/`.
