# CLAUDE.md — Istruzioni per Claude Code

## Progetto

Progetto universitario per il corso di **Manutenzione Preventiva** (A.A. 2025/2026).
Sistema: esacottero basato su frame DJI F550 con Pixhawk 6X e firmware PX4.

L'obiettivo finale è redigere una **relazione completa** sulle attività di manutenzione preventiva del drone.

## Team

- **Angelo** — proprietario della repo
- **Matteo** — collaboratore
- **Federico** — collaboratore

## Struttura della repository

```
README.md              → Overview del progetto (mostrato su GitHub)
CLAUDE.md              → Questo file — istruzioni per Claude Code
docs/
  BOM.md               → Bill of Materials (componenti, modelli, quantità)
  datasheets/           → PDF dei datasheet dei componenti
img/                    → Foto, schemi, diagrammi del drone
maintenance/            → Piani di manutenzione, checklist, FMEA
log/                    → Archivio storico dei log .ulg (per data)
log_current/            → Singolo .ulg "corrente" + .mcap generato
foxglove/               → Script di conversione .ulg→.mcap + URDF + doc Foxglove
plot/                   → Script di plotting matplotlib (IMU, ESC, batteria, ...)
  incidente/            → Analisi forense dello schianto (plot + relazione)
```

## Convenzioni

- **Lingua documentazione**: italiano
- **Lingua commit**: italiano
- **Nomi file/cartelle**: italiano
- **Lingua di risposta**: rispondi nella lingua in cui l'utente scrive
- La BOM usa codici identificativi per categoria (S-xx struttura, P-xx propulsione, A-xx avionica, E-xx alimentazione, C-xx comunicazione, SW-xx software)

## Comportamento atteso

- **Non fare commit automatici** — i commit li gestisce l'utente
- Per task semplici o con auto-accept attivo, procedi direttamente
- Per task complessi, proponi un piano e chiedi conferma prima di procedere
- Quando aggiorni la BOM, mantieni il formato tabellare e i codici ID esistenti
- Non rimuovere campi TBD senza averli prima confermati con l'utente
- Quando vengono fornite nuove informazioni sui componenti, aggiorna subito la BOM
- La documentazione deve essere adatta a essere inclusa nella relazione finale del corso

## Relazione finale

Formato e struttura ancora da definire. In stand-by fino a indicazioni dal professore.

## Contesto tecnico

- Il drone usa **PX4** (non ArduPilot) come firmware
- La ground station è **QGroundControl**
- Il Pixhawk 6X ha 3 IMU ridondanti integrate (sensor voting)
- Il frame F550 ha la PDB integrata nella piastra inferiore
- GPS montato su mast per ridurre interferenze EMI
