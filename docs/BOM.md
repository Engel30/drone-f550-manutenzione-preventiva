# Bill of Materials (BOM) — Esacottero F550

> Corso di Manutenzione Preventiva — A.A. 2025/2026
> Ultimo aggiornamento: 2026-03-17

## 1. Struttura

| ID | Componente | Modello | Qtà | Note |
|----|-----------|---------|-----|------|
| S-01 | Frame | DJI F550 Hexacopter | 1 | Frame esagonale con PDB integrata |
| S-02 | Landing Gear | Piedi flessibili ad arco | 1 set | Ammortizzano l'atterraggio |
| S-03 | Mast GPS | Albero ~15 cm | 1 | Allontana il GPS dalle interferenze EMI |

## 2. Propulsione

| ID | Componente | Modello | Qtà | Note |
|----|-----------|---------|-----|------|
| P-01 | Motore Brushless | AIR2213 / KV920 | 6 | 3 CW + 3 CCW |
| P-02 | ESC | Tekko32 F4 | 6 | Uno per motore |
| P-03 | Eliche | TBD — 2 pale | 6 | Dimensione TBD (probabile 10x4.5) |

## 3. Avionica / Flight Controller

| ID | Componente | Modello | Qtà | Note |
|----|-----------|---------|-----|------|
| A-01 | Flight Controller | CubePilot Cube Black | 1 | Contiene IMU multiple |
| A-02 | Carrier Board | TBD (da verificare modello) | 1 | Interfaccia tra Cube e periferiche |
| A-03 | Accelerometro (IMU interna) | Integrato nel Cube Black (x2) | 2 | Montati su pedana antivibrante interna con piedini in gomma |
| A-04 | Accelerometro (esterno) | Integrato nel Cube Black (x1) | 1 | Saldato direttamente sul frame |
| A-05 | Giroscopio | Integrato nel Cube Black (x2) | 2 | Rilevano velocità angolare |
| A-06 | GPS | CubePilot Here+ | 1 | GNSS + magnetometro, montato su mast |
| A-07 | Base RTK | TBD (marca da verificare) | 1 | Stazione base per correzione RTK |
| A-08 | Buzzer | Incluso con Cube Black | 1 | Segnalazioni acustiche e allarmi |

## 4. Alimentazione

| ID | Componente | Modello | Qtà | Note |
|----|-----------|---------|-----|------|
| E-01 | Batteria LiPo | 4S 5600 mAh (marca TBD) | 1 | 16.8V a piena carica, connettore XT60 |
| E-02 | BEC / Regolatore di tensione | Generico step-down 16.8V → 5V | 1 | Alimenta avionica e periferiche |
| E-03 | Connettore batteria | XT60 | 1 coppia | Maschio su batteria, femmina su drone |

## 5. Comunicazione e Controllo

| ID | Componente | Modello | Qtà | Note |
|----|-----------|---------|-----|------|
| C-01 | Ricevitore RC | FrSky X8R | 1 | Ricevitore a bordo del drone |
| C-02 | Radiocomando (TX) | TBD (joypad di volo FrSky) | 1 | Trasmettitore a terra |
| C-03 | Telemetria | Holybro 433 MHz | 1 set | Coppia TX/RX per link dati con QGroundControl |

## 6. Software

| ID | Componente | Versione | Note |
|----|-----------|---------|------|
| SW-01 | Firmware FC | PX4 | Flight stack principale |
| SW-02 | Ground Station | QGroundControl | Configurazione, missioni, monitoraggio |

## Legenda

- **TBD**: informazione da completare
- **CW/CCW**: senso di rotazione orario/antiorario
- **IMU**: Inertial Measurement Unit (accelerometro + giroscopio)
- **BEC**: Battery Eliminator Circuit
- **EMI**: ElectroMagnetic Interference
- **RTK**: Real-Time Kinematic (correzione GPS centimetrica)

## Note aggiuntive

- Il frame F550 ha la PDB (Power Distribution Board) integrata nei bracci/piastra inferiore
- Il Cube Black contiene internamente 3 IMU (ciascuna con accelerometro + giroscopio): 2 su pedana antivibrante isolata, 1 fissa. Questo fornisce ridondanza tripla per la navigazione inerziale
- Il firmware PX4 utilizza la votazione tra le IMU per aumentare l'affidabilità (sensor voting)
