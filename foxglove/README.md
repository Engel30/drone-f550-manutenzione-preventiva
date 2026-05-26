# Visualizzazione voli PX4 in Foxglove — Setup e riproducibilità

Documentazione del workflow di replay di un log PX4 (`.ulg`) tramite
[Foxglove](https://foxglove.dev). Lo script converte il log in `.mcap` con
scena 3D pre-calcolata (drone + eliche + opzionale overlay satellitare),
così Foxglove non richiede plugin/extension.

Il workflow è stato sviluppato per l'analisi forense dello schianto del
2026-05-26, ma è generico e funziona con qualunque log PX4 — è sufficiente
mettere il `.ulg` corrente in `log_current/` alla root del repository.

## Indice

1. [Obiettivo e architettura](#obiettivo-e-architettura)
2. [Stack software](#stack-software)
3. [Pipeline di conversione `.ulg` → `.mcap`](#pipeline-di-conversione-ulg--mcap)
4. [Modello 3D del drone (URDF)](#modello-3d-del-drone-urdf)
5. [Setup Foxglove](#setup-foxglove)
6. [Layout dei pannelli](#layout-dei-pannelli)
7. [Comandi rapidi](#comandi-rapidi)
8. [Troubleshooting](#troubleshooting)
9. [Decisioni tecniche](#decisioni-tecniche)

---

## Obiettivo e architettura

Lo scopo è poter riprodurre visualmente l'incidente:

- **Replay temporale** della telemetria con scrubbing avanti/indietro;
- **Scena 3D** con il modello dell'esacottero che si muove e ruota nello spazio,
  con le eliche che girano a velocità proporzionale agli RPM reali;
- **Pannelli sincronizzati** che mostrano IMU, RPM motori, comandi pilota, log
  di sistema, stato di volo e flag di failure.

La conversione del log PX4 in un formato direttamente apribile da Foxglove è
necessaria perché l'extension PX4 ufficiale di Foxglove si è rivelata
inaffidabile sul nostro log (alcuni topic non venivano convertiti). La
pipeline custom precompila tutto il materiale necessario nel file `.mcap`
così Foxglove non richiede plugin/extension.

```
                  ┌──────────────────────────────────────────┐
                  │           log_current/<vol>.ulg          │
                  │   147 topic uORB + logged_messages       │
                  │   timestamp PX4 (μs since boot)          │
                  └────────────────┬─────────────────────────┘
                                   │
                  ┌────────────────▼─────────────────────────┐
                  │  foxglove/ulog_to_mcap.py                │
                  │  ─────────────────────────────────────── │
                  │  • Copia 147 topic uORB → JSON schemas   │
                  │  • Calcola FrameTransform local_origin   │
                  │    → base_link (NED→ENU, FRD→FLU)        │
                  │  • Integra angoli eliche da esc_status   │
                  │  • Deriva attitude_euler (rpy + setpt)   │
                  │  • Estrae logged_messages → foxglove.Log │
                  │  • Overlay satellitare (--satellite)     │
                  │  • Auto-trim sul periodo armato          │
                  └────────────────┬─────────────────────────┘
                                   │
                  ┌────────────────▼─────────────────────────┐
                  │          log_current/<vol>.mcap          │
                  │  150 channels, ~104k messaggi, ~10 MB    │
                  └────────────────┬─────────────────────────┘
                                   │
                                   │  drag-and-drop
                                   ▼
            ┌────────────────────────────────────────────────┐
            │    Foxglove Desktop (Windows)                  │
            │    + f550.urdf in 3D panel Custom Layer        │
            │    + layout_incidente.json (pannelli salvati)  │
            └────────────────────────────────────────────────┘
```

---

## Stack software

| Componente | Versione | Ruolo | Dove gira |
|---|---|---|---|
| **Foxglove Desktop** | ≥ 2.0 | Visualizzazione, 3D scene, panel | Windows |
| **WSL2 Ubuntu 22.04** | — | Filesystem progetto + script | Windows |
| **Python 3.10+** | — | Esecuzione script di conversione | WSL |
| **pyulog** | ≥ 1.0 | Lettura `.ulg` PX4 | WSL |
| **mcap** Python lib | ≥ 1.3 | Scrittura `.mcap` | WSL |
| **zstandard** | (auto) | Compressione chunk MCAP | WSL |
| **numpy** | — | Aritmetica vettoriale (integrazione angoli) | WSL |
| **Pillow** | ≥ 9 | Stitching tile satellitari (overlay opzionale) | WSL |
| **pygltflib** | ≥ 1.16 | Generazione GLB piano texturato (overlay opzionale) | WSL |

Installazione delle dipendenze WSL:

```bash
pip install --user pyulog mcap numpy Pillow pygltflib
```

(Su Ubuntu recenti potrebbe servire `--break-system-packages` o un venv;
in alternativa `apt install python3-numpy python3-pip` e poi
`pip install --user pyulog mcap`.)

---

## Pipeline di conversione `.ulg` → `.mcap`

Tutto il lavoro è in `ulog_to_mcap.py`. Il file espone una CLI con 3 modalità:

```bash
# 1) Default — singolo .ulg in log_current/
#    Legge l'unico .ulg presente e scrive log_current/<stem>.mcap
python3 foxglove/ulog_to_mcap.py [opzioni]

# 2) Singolo file esplicito
#    Utile per riconvertire un .ulg dell'archivio o cambiare output
python3 foxglove/ulog_to_mcap.py <input.ulg> [output.mcap] [opzioni]

# 3) Batch ricorsivo
#    Converte tutti i .ulg trovati in DIR (ricorsivamente). Ogni .mcap
#    viene scritto accanto al sorgente. Senza DIR usa log/ alla root.
python3 foxglove/ulog_to_mcap.py --all [DIR] [opzioni]
```

### Cosa fa lo script

1. **Carica il `.ulg`** con `pyulog.ULog`, ottenendo:
   - `ulog.data_list`: lista di topic uORB (~147 per un volo PX4 standard);
   - `ulog.logged_messages`: messaggi INFO/WARN/ERROR del firmware (sezione
     speciale, non in `data_list`).

2. **Auto-trim** (con `--auto-trim`): cerca la finestra temporale `[t_arm, t_disarm]`
   in `vehicle_status.arming_state == 2` e applica un buffer di 1 s pre / 0.5 s post.
   Questo elimina i messaggi "boot ghost" che farebbero stirare la timeline di
   Foxglove fino a `t = 0` (sono ~18 minuti di standby in cui il Pixhawk è acceso
   ma non si fa nulla di interessante).

3. **Registra in MCAP** uno schema JSON per ogni topic uORB:
   - I tipi di campo C-like (`float32`, `uint64`, ecc.) sono mappati su tipi
     JSON Schema (`number`, `integer`, `boolean`, `string`);
   - Topic con istanze multiple (es. `vehicle_imu_status` × 3) ricevono nomi
     suffisati (`vehicle_imu_status`, `vehicle_imu_status_1`, `_2`).

4. **Copia i messaggi uORB** uno-a-uno (con filtro `in_window`), serializzandoli
   come JSON. Valori `NaN`/`Inf` vengono sostituiti con `null` (JSON-safe).

5. **Inietta topic derivati** essenziali per il replay 3D:

   - **`/tf` body**: trasformata `local_origin → base_link` calcolata da
     `vehicle_local_position.{x,y,z}` (translation) e `vehicle_attitude.q[0..3]`
     (rotation). Vedi la sezione [Conversioni di coordinate](#conversioni-di-coordinate).
   - **`/tf` eliche**: 6 trasformate `motor_Mx → prop_Mx` con rotazione attorno
     a Z proporzionale agli RPM di `esc_status.esc[k].esc_rpm`.
     Vedi [Animazione delle eliche](#animazione-delle-eliche).
   - **`attitude_euler`**: topic derivato con roll/pitch/yaw **in gradi**, sia
     misurato sia setpoint. Comodo per i plot senza dover convertire i quaternioni
     dentro Foxglove.
   - **`logged_messages`**: i messaggi INFO/WARN/ERROR di PX4 esposti come
     schema `foxglove.Log`, visualizzabili dal Log panel.

### Conversioni di coordinate

PX4 esprime telemetria in convenzione **FRD-NED**:
- Body frame: **F**orward (+X), **R**ight (+Y), **D**own (+Z);
- World frame: **N**orth (+X), **E**ast (+Y), **D**own (+Z).

Foxglove (e ROS) usa **FLU-ENU**:
- Body frame: **F**orward (+X), **L**eft (+Y), **U**p (+Z);
- World frame: **E**ast (+X), **N**orth (+Y), **U**p (+Z).

#### Traslazione

```
x_ENU = y_NED   (NED east → ENU x)
y_ENU = x_NED   (NED north → ENU y)
z_ENU = −z_NED  (NED down → ENU up)
```

#### Rotazione (quaternione)

```
q_ENU_FLU = q_NED→ENU  ⊗  q_PX4  ⊗  q_FRD→FLU
```

dove:
- `q_NED→ENU = (0, √2/2, √2/2, 0)` — rotazione di 180° attorno all'asse `(1,1,0)/√2`;
- `q_FRD→FLU = (0, 1, 0, 0)` — rotazione di 180° attorno all'asse X body;
- `⊗` è il prodotto di Hamilton.

L'implementazione è in `attitude_ned_to_enu()` nello script.

#### Offset di posizione

`vehicle_local_position` ha origine al punto di **inizializzazione dell'EKF**,
che in pratica può essere distante da dove il drone sta a terra. Per il nostro
log, all'armo il drone risulta a `(8.5, 10.7, −5.0)` ENU rispetto a quell'origine.

Per visualizzare il drone partire dalla griglia, lo script campiona la posizione
nel momento dell'armo (`vehicle_status.arming_state == 2`) e la sottrae da tutte
le successive translation del `/tf` body. Risultato: il drone parte da `(0, 0, 0)`
sulla griglia.

### Animazione delle eliche

A 5000 RPM reali un'elica fa 83 giri/s; con un sample rate di 50 Hz di
`esc_status`, ogni frame mostrerebbe ~2 rivoluzioni complete → effetto aliasing
"wagon-wheel" totalmente inutile.

Lo script applica un fattore di scaling **visivo**:

```
ω_display [rad/s] = (RPM × 2π/60 × direzione) / PROP_RPM_VISUAL_SCALE
```

con `PROP_RPM_VISUAL_SCALE = 60.0`. A 5000 RPM reali, l'elica display gira a
~83 RPM (~1.4 Hz) — visibile, ben distinguibile fra "ferma", "lenta" e "veloce".

La direzione di rotazione segue la convenzione PX4 `hexa_x`:
- **CCW** (positiva attorno a Z+): M1, M2, M5;
- **CW** (negativa attorno a Z+): M3, M4, M6.

L'angolo è integrato cumulativamente con `np.cumsum(ω × dt)` su tutto il log
(non solo sulla finestra `--auto-trim`), così le eliche partono con fasi
naturalmente sfasate invece di tutte sincronizzate a 0°.

### Topic aggiunti dallo script

| Topic | Schema | Numero msg | Scopo |
|---|---|---|---|
| `/tf` | `foxglove.FrameTransform` | ~2k body + ~6k eliche | Posa drone + rotazione eliche |
| `attitude_euler` | `px4.attitude_euler_deg` | ~2k | RPY in gradi (misurato + setpoint) |
| `logged_messages` | `foxglove.Log` | ~10 | INFO/WARN/ERROR firmware |

I 147 topic uORB originali sono preservati con nomi identici al `.ulg`
(es. `vehicle_attitude`, `esc_status`, `actuator_motors`, ecc.), quindi tutti
i message path che usi nei pannelli funzionano esattamente come se Foxglove
stesse leggendo direttamente l'ulog.

---

## Modello 3D del drone (URDF)

Il modello è in `f550.urdf` — URDF puro, senza dipendenze da xacro né mesh
esterne. Geometria stilizzata ma fedele alle proporzioni reali dell'F550:

| Componente | Geometria | Dimensione |
|---|---|---|
| Frame centrale | box | 150×150×40 mm |
| Pixhawk (cappello) | box | 80×50×25 mm |
| Mast GPS | cylinder + disco | 150 mm + 70 mm disc |
| Bracci (×6) | cylinder | Ø24, lunghi 220 mm |
| Motori (×6) | cylinder | Ø28, alti 30 mm |
| Hub eliche (×6) | cylinder | Ø24, alto 6 mm |
| Pale elica (×12) | box con incidenza | 115×20×4 mm, pitch 7° |

Configurazione `hexa_x`: bracci a ±30°, ±90°, ±150° dalla direzione di marcia.
I due bracci anteriori (M1, M3) sono colorati **rosso** per indicare il fronte;
gli altri 4 sono bianchi.

Catena cinematica per ciascun motore:

```
base_link
  └── arm_Mx       (fixed joint, rotazione attorno a Z del corpo)
       └── motor_Mx (fixed joint)
            └── prop_Mx (continuous joint, axis Z) ← angolo da /tf
```

I joint `prop_Mx_joint` sono di tipo `continuous` (rotazione illimitata): il
loro angolo è fornito a runtime dai `FrameTransform` `motor_Mx → prop_Mx`
emessi dallo script.

---

## Setup Foxglove

### Installazione (Windows)

Scarica e installa Foxglove Desktop da <https://foxglove.dev/download>.
Account gratuito richiesto al primo avvio.

### Apertura del `.mcap` da WSL

`File → Open local file…` → naviga al path UNC:

```
\\wsl$\Ubuntu\home\angelo\manutenzione-preventiva-freddi\log_current\<vol>.mcap
```

(Sostituisci `Ubuntu` con il nome esatto della tua distro WSL: lo trovi con
`wsl -l -v` da PowerShell.)

### Configurazione del 3D panel

1. Aggiungi un pannello **3D** (`+` in alto a destra).
2. Settings del pannello → sezione **Frame**:
   - `Fixed frame: local_origin`
   - `Display frame: base_link`
   - `Follow mode: Position` (solo traslazione, mantiene orizzonte stabile)
3. Settings → **Scene** → **Grid**:
   - `Show grid: ON`, `Frame: local_origin`, `Size: 30 m`, `Divisions: 30`
4. Settings → **Custom Layers** → `Add → URDF`:
   - URL: `file://wsl.localhost/Ubuntu/home/angelo/manutenzione-preventiva-freddi/foxglove/f550.urdf`
   - (alternativa se file:// fa storie: lancia
     `python3 -m http.server 8000` nella cartella `foxglove/` da WSL,
     poi usa URL `http://localhost:8000/f550.urdf`.)
5. Settings → **Transforms** → `base_link`:
   - `Show trail: ON`, `Trail duration: 20 s`, `Color: rosso o arancio`.

### Overlay satellitare (sostituisce la griglia)

Per dare realismo alla scena 3D è possibile sostituire la griglia con
un'immagine satellitare georeferenziata sul punto di takeoff. L'opzione
`--satellite` di `ulog_to_mcap.py`:

1. legge `vehicle_global_position` al momento dell'armo per ottenere `(lat, lon)`
   del takeoff;
2. scarica le tile [ESRI World Imagery](https://server.arcgisonline.com) (free,
   nessun token) necessarie a coprire un quadrato di N×N metri attorno al
   takeoff;
3. cuce le tile in un'unica PNG e la usa come `baseColorTexture` di una mesh
   GLB (piano XY a `z=−0.05 m`);
4. embedda i bytes del GLB **direttamente nel MCAP** dentro un messaggio
   `foxglove.SceneUpdate.ModelPrimitive` (campo `data`, base64).

L'MCAP risultante è **autoconsistente**: nessun server HTTP, nessun file
esterno, nessuna connessione internet durante il replay. Le tile scaricate
vengono cachate in `.tile_cache/` per evitare re-download in rigenerazioni
successive (la cartella è in `.gitignore`).

```bash
# 200×200 m, zoom 19 (default — adatto per voli locali)
python3 foxglove/ulog_to_mcap.py --auto-trim --satellite

# Area panoramica più ampia
python3 foxglove/ulog_to_mcap.py --auto-trim --satellite \
    --satellite-size 500 --satellite-zoom 18
```

In Foxglove, una volta caricato il `.mcap`:

1. **Disattiva la griglia**: Settings del pannello 3D → **Scene** → **Grid** → OFF.
2. L'overlay appare automaticamente come parte della scena (è registrato nel
   topic `satellite_overlay`, schema `foxglove.SceneUpdate`).
3. Verifica nel pannello 3D, sezione **Topics**, che `satellite_overlay` sia
   abilitato (di default Foxglove abilita tutti i topic SceneUpdate).

**Convenzioni geografiche del piano:**

| Direzione | Asse ENU | Lato del piano |
|---|---|---|
| Nord | +Y | bordo alto |
| Est  | +X | bordo destro |
| Sud  | −Y | bordo basso |
| Ovest| −X | bordo sinistro |

Il drone parte sempre da `(0, 0, 0)` (offset già applicato in `/tf`), quindi
il **centro esatto** dell'immagine satellitare coincide con il punto di
takeoff. La proiezione delle tile (Web Mercator) introduce un errore inferiore
al pixel su scale < 500 m alle nostre latitudini.

**Nota tecnica — orientamento del piano:** glTF usa convenzione Y-up, ma il
mondo Foxglove è Z-up (ROS REP-103). Foxglove applica automaticamente una
rotazione di +90° attorno a X quando carica un ModelPrimitive glTF; senza
correzioni, il piano XY del mesh finisce sul piano XZ del mondo (verticale).
Per questo motivo il messaggio `SceneUpdate` emesso da `ulog_to_mcap.py`
applica una rotazione di **−90° attorno a X** nella `pose.orientation` del
modello, che annulla la conversione automatica e riallinea il piano al
piano XY del mondo (la griglia di Foxglove). In quaternione:
`{x: −0.7071, y: 0, z: 0, w: 0.7071}`.

### URDF da WSL via HTTP (alternativa robusta)

```bash
cd foxglove
python3 -m http.server 8000
```

Da Foxglove (Windows) puoi raggiungere il server come `http://localhost:8000`
grazie al port forwarding nativo di WSL2.

---

## Layout dei pannelli

Configurazione consigliata, ottimizzata per analisi del crash. Per ciascun
pannello: `+ Add panel` → tipo → configura come indicato.

| # | Pannello | Tipo Foxglove | Message paths |
|---|---|---|---|
| 1 | **3D Scene** | 3D | (URDF + `/tf` + grid) |
| 2 | **Log** | Log | `logged_messages` |
| 3 | **State Transitions nav_state** | State Transitions | `vehicle_status.nav_state` |
| 4 | **Indicator FD ROLL** | Indicator | `failure_detector_status.fd_roll` |
| 5 | **Indicator FD MOTOR** | Indicator | `failure_detector_status.fd_motor` |
| 6 | **Indicator FAILSAFE** | Indicator | `vehicle_status.failsafe` |
| 7 | **Indicator ARMED** | Indicator | `vehicle_status.arming_state` (verde se =2) |
| 8 | **Plot ESC RPM + cmd** | Plot | `esc_status.esc[0..5].esc_rpm` + `actuator_motors.control[0..5]` (scale ×6000) |
| 9 | **Plot Rates** | Plot | `vehicle_angular_velocity.xyz[0..2]` + `vehicle_rates_setpoint.{roll,pitch,yaw}` (scale ×57.2958 per °/s) |
| 10 | **Plot Attitude** | Plot | `attitude_euler.{roll,pitch,yaw,roll_setpoint,pitch_setpoint,yaw_setpoint}` |
| 11 | **Plot Stick pilota** | Plot | `manual_control_setpoint.{roll,pitch,yaw,throttle}` |
| 12 | **Plot Vibration & Clipping** | Plot | `vehicle_imu_status.{accel,gyro}_vibration_metric` + `accel_clipping[0..2]` |

### Cosa rivela ciascun pannello per il crash

| Pannello | Insight |
|---|---|
| Log | Cronologia testuale del crash (9 INFO da PX4 firmware) |
| State Transitions | Le 3 transizioni AUTO_MISSION → POSCTL → AUTO_LAND |
| Indicators | Lampadine: si accendono in cronologia, raccontano il fallimento in 2 sec |
| ESC RPM | Lag ESC visibile durante AUTO_LAND (~0.3 s) |
| Rates | Saturazione setpoint a ±220°/s → PIO confermata |
| Attitude | Roll a −104° (drone capovolto) mentre setpoint resta limitato |
| Stick | Throttle inchiodato a −1.0 dall'armo: la causa primaria |
| Vibration | Vibrazioni nominali fino a impatto → nessun guasto pre-crash |

### Salvataggio del layout

Una volta sistemati i pannelli:

`Layout` (menu in alto al centro) → `Export layout` → salva in
`foxglove/layout_incidente.json`.

Il file JSON è committato nel repository. Per riusarlo:
`Layout → Import from file → layout_incidente.json`.

---

## Comandi rapidi

### Rigenerazione del MCAP (caso standard)

```bash
# Legge l'unico .ulg in log_current/, scrive log_current/<stem>.mcap
python3 foxglove/ulog_to_mcap.py --auto-trim
```

### Rigenerazione con overlay satellitare

```bash
python3 foxglove/ulog_to_mcap.py --auto-trim --satellite
```

### Conversione batch (tutto l'archivio in un colpo)

```bash
# Converte ogni log/<data>/*.ulg in log/<data>/*.mcap
python3 foxglove/ulog_to_mcap.py --all --auto-trim --satellite

# Solo una sottocartella specifica
python3 foxglove/ulog_to_mcap.py --all log/2026-04-28/ --auto-trim
```

I `.mcap` vengono **sempre rigenerati** (non c'è skip): se hai cambiato
opzioni (es. abilitato `--satellite`) basta rilanciare il comando e tutti
i file vengono ricreati con le nuove impostazioni. La cache delle tile
satellitari evita di riscaricare le stesse aree geografiche.

### Aggiornare un singolo .mcap

```bash
# Specifica path esplicito del .ulg e (opzionalmente) del .mcap
python3 foxglove/ulog_to_mcap.py log/2026-04-28/10_28_38.ulg --auto-trim --satellite
```

Senza secondo argomento posizionale, l'output è scritto accanto al sorgente
con stesso `stem` ed estensione `.mcap` (sovrascrive se esiste).

### Finestra esplicita

```bash
python3 foxglove/ulog_to_mcap.py --start 1063.968 --end 1079.903
```

### Tuning velocità eliche

Modifica in cima a `ulog_to_mcap.py`:

```python
PROP_RPM_VISUAL_SCALE = 60.0   # ↓ valore = eliche più veloci, ↑ valore = più lente
```

Poi rigenera il MCAP.

### Test rapido del MCAP generato

```bash
python3 -c "
from mcap.reader import make_reader
import glob
with open(sorted(glob.glob('log_current/*.mcap'))[-1], 'rb') as f:
    r = make_reader(f)
    s = r.get_summary()
    print(f'Channels: {len(s.channels)}, Messaggi: {s.statistics.message_count}')
    print(f'Durata: {(s.statistics.message_end_time - s.statistics.message_start_time)/1e9:.2f}s')
"
```

---

## Troubleshooting

### "Drone parte sotto la griglia"

Causa: l'origine dell'EKF (`vehicle_local_position` origin) non coincide
con il punto di decollo fisico. Lo script applica un offset di posizione
prendendo come riferimento il momento dell'armo. Se ancora non funziona,
verifica che `vehicle_status.arming_state == 2` sia presente nel log
(comando di check più sotto).

### "Le eliche non girano"

- Riavvia Foxglove (i joint `continuous` dell'URDF a volte non vengono
  ri-aggiornati al solo reload del file).
- Verifica nel pannello 3D, settings → Transforms, che esistano i frame
  `prop_M1`…`prop_M6`. Se mancano, il MCAP non contiene i `/tf` eliche;
  rigeneralo con `--auto-trim`.

### "Il pannello 3D non vede `local_origin` e `base_link`"

Stai aprendo direttamente il `.ulg`? Non più necessario: apri il `.mcap`
generato dallo script. I frame sono inclusi nativamente nel file.

### "Foxglove timeline parte da 0 e non da quando ho armato"

Usa l'opzione `--auto-trim` quando generi il MCAP. Senza, alcuni messaggi
di boot a `t = 0` stirano la timeline.

### Verifica integrità log (debug)

```bash
python3 -c "
import glob
from pyulog import ULog
ulog = ULog(sorted(glob.glob('log_current/*.ulg'))[-1])
import numpy as np
for d in ulog.data_list:
    if d.name == 'vehicle_status':
        arming = np.asarray(d.data['arming_state'])
        idx = np.where(arming == 2)[0]
        if len(idx):
            t0 = d.data['timestamp'][idx[0]]
            t1 = d.data['timestamp'][idx[-1]]
            print(f'Armed da {t0/1e6:.3f}s a {t1/1e6:.3f}s')
"
```

---

## Decisioni tecniche

Razionale delle scelte fatte (utile per spiegare in sede d'esame):

### Perché conversione `.ulg` → `.mcap` invece di usare il plugin PX4

L'extension ufficiale `px4_converter` di Foxglove registra **schema converter**
che vengono attivati on-demand quando un pannello si abbona a un topic uORB.
Sul nostro log, l'extension non agganciava `vehicle_attitude` (solo
`vehicle_local_position`), risultando in transform tree vuoto e impossibilità
di posizionare il drone nella scena 3D.

Pre-calcolando i `FrameTransform` nel `.mcap` eliminiamo la dipendenza
dall'extension e otteniamo un file **self-contained** che funziona in qualunque
istanza di Foxglove (web, desktop, ogni versione).

### Perché URDF e non mesh fotorealistica

Tre motivi:

1. **Riproducibilità**: 80 righe di URDF puro vs gigabytes di asset 3D che
   andrebbero gestiti separatamente (Git LFS, ecc.);
2. **Manutenibilità**: cambiare la geometria significa modificare numeri in
   un file XML, non aprire Blender;
3. **Sufficienza visiva**: per analisi tecnica di un crash, lo stile schematic
   è anche **più leggibile** del fotorealistico — frecce dei bracci ben
   evidenti, eliche distinguibili dal motore, mast GPS chiaramente visibile.

### Perché scaling 1/60 sulle eliche

L'occhio umano percepisce continuità di rotazione fino a ~60 Hz; sopra è
aliasing wagon-wheel. A 5000 RPM = 83 Hz reali serve un fattore minimo
di ~1.4 per scendere sotto 60 Hz. Si è scelto 60× per portarle bene dentro
la finestra di percezione (visibile come ~1.4 Hz a piena potenza). Numero
configurabile in cima allo script per chi volesse iperrealismo.

### Perché auto-trim sul `vehicle_status.arming_state`

In PX4 il logger ha un comportamento detto **"log when armed"**: il logger
attivo solo quando il drone è armato, ma alcuni topic (configurazione,
parametri) emettono messaggi a `t ≈ 0` durante il boot. Questi singoli
messaggi facevano stirare la timeline di Foxglove di 18 minuti, costringendo
a scrubbing manuale ogni volta. Il trim sul periodo armato cattura il volo
reale e nient'altro.

### Perché topic derivato `attitude_euler` invece di conversione UI

Foxglove non supporta nativamente la conversione quaternione → Euler nel
sistema dei message path. Per plottare roll/pitch/yaw in gradi avremmo
dovuto plottare i 4 componenti del quaternione separati (cripticio per chi
guarda il pannello) oppure usare estensioni con scripting. Aggiungere il
topic derivato in fase di conversione è la soluzione più pulita:
- ~10 righe di codice extra,
- nessuna logica in UI da rifare ogni volta,
- valori numericamente identici a quelli citati in `relazione_schianto.md`
  (stessa funzione `quat_to_euler` di `plot_incidente.py`).

---

## File della cartella `foxglove/`

```
foxglove/
├── README.md             ← questo file
├── ulog_to_mcap.py       ← script di conversione (≈ 300 righe)
├── satellite_layer.py    ← downloader tile ESRI + generatore GLB texturato
├── f550.urdf             ← modello 3D dell'esacottero (≈ 240 righe)
├── layout_incidente.json ← layout Foxglove esportato (da generare)
└── .tile_cache/          ← cache locale tile ESRI (gitignored)
```

Il `.mcap` di output **non** è nella cartella `foxglove/` ma è messo
accanto al `.ulg` di origine (in `plot/`), così che il rapporto 1:1 tra
log raw e log rigenerato sia immediato.

---

## Riferimenti esterni

- [Foxglove documentation](https://docs.foxglove.dev)
- [MCAP file format specification](https://mcap.dev)
- [PX4 ULog file format](https://docs.px4.io/main/en/dev_log/ulog_file_format.html)
- [pyulog on GitHub](https://github.com/PX4/pyulog)
- [Foxglove px4_converter extension](https://github.com/foxglove/px4_converter)
  (per riferimento, non utilizzata in questo workflow)

