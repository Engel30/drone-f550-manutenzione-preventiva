# Analisi dell'incidente — log `11_14_44.ulg` (2026-05-26)

## Sintesi

Il drone si è schiantato dopo **~13 secondi di volo**. La causa primaria identificata
è un **takeover dal modo automatico al modo POSCTL con lo stick di throttle a fondo
corsa in basso** (`thr = −1.0`): nell'istante del passaggio di modo, PX4 ha
interpretato lo stick come "comanda discesa alla massima velocità", mentre era già
in corso un transitorio in rollio. Il tentativo del pilota di recuperare ha innescato
una **PIO (Pilot Induced Oscillation)** sul cyclic che è degenerata fino al
ribaltamento; il commander è quindi passato autonomamente a `AUTO_LAND` con il
drone capovolto, esito impatto al suolo. **Non sono presenti segnali di guasto
hardware** prima dell'evento (batteria stabile, RPM bilanciati, vibrazioni normali,
nessun fault dell'EKF).

## Cronologia (tempi assoluti del log)

| Tempo [s]  | Evento                                                      | Fonte                           |
| ---------- | ----------------------------------------------------------- | ------------------------------- |
| 1064.81    | Armato (comando esterno)                                    | `logged_messages` INFO          |
| 1066.88    | Takeoff rilevato — `nav_state` = 3 (AUTO_MISSION)           | INFO + `vehicle_status`         |
| ~1066–1074 | Salita auto fino a ~3 m di quota, assetto pressoché piatto  | `vehicle_local_position`        |
| **1074.4** | **Inizio oscillazione anomala** in roll/pitch (drone ancora in auto) | `vehicle_attitude`     |
| 1075.94    | Pilota prende il controllo — `nav_state` passa a 2 (POSCTL) | INFO + `vehicle_status`         |
| 1075.9–1079.1 | Oscillazioni divergenti, comandi pilota saturati ±1.0   | `manual_control_setpoint`       |
| **1078.52** | **`nav_state` = 15 (AUTO_LAND)** — commander toglie il controllo al pilota | `vehicle_status`     |
| 1078.8     | Comandi motore (`actuator_motors.control`) crollano da ~0.6 a 0.0–0.16 | `actuator_motors`          |
| **1079.15** | **`fd_roll`=1** (|roll| > 60° per > 0.3 s) → attitude failure *registrato* (log a ~2 Hz, trigger fisico anteriore) | `failure_detector_status`    |
| 1079.16    | Failsafe attivato                                           | WARNING `logged_messages`       |
| 1079.85    | `fd_motor`=1, `motor_failure_mask`=8 (M3) — conseguenza impatto | `failure_detector_status`   |
| ~1079.9    | **Impatto al suolo**: vibrazioni accel da 2 → 9 m/s², gyro da 0.28 → 1.66 rad/s, clipping su tutti gli assi | `vehicle_imu_status` |

## Ricostruzione dinamica

### Fase 1 — Volo nominale (t = 1066.9 → 1074.4 s)

- Decollo automatico, salita verticale a 3 m con `vz` controllato (~−1.4 m/s).
- Assetto piatto: roll/pitch < 5°.
- RPM dei 6 motori bilanciati: ~5000–5600 RPM.
- Vibrazioni: `accel_vibration_metric` ≈ 1–2 m/s² (nominale).
- Batteria a 15.7–15.8 V, corrente nominale.

### Fase 2 — Transitorio pre-takeover (t = 1074.4 → 1075.9 s)

In modalità ancora **auto-mission**, il roll cresce da +3° a **+42°** in 0.6 s e il
pitch da −0.5° a **+18°**. Già qui il setpoint di rate è in saturazione (±100 °/s su
roll e pitch). Il velivolo entra in un transitorio importante *prima* che il pilota
intervenga sul cyclic.

Osservazione chiave su `manual_control_setpoint` in questa fase:

- Roll/pitch/yaw stick: **centrati a 0** (in AUTO_MISSION PX4 li ignora comunque);
- Throttle stick: **già a −1.0** (tutto in basso), fin dall'armo a t=1064.8 s.

Cause possibili del transitorio iniziale: tuning aggressivo del controllore di
posizione in auto, effetto suolo a ~3 m, o disturbo aerodinamico locale.

### Fase 3 — Takeover con throttle stick saturato (t = 1075.94 s)

Quando l'utente attiva POSCTL, PX4 inizia a leggere `manual_control_setpoint` come
comando reale. Il throttle stick è a **−1.0** dall'inizio del log: nessuno l'aveva
ricentrato. In POSCTL questa scala mappa così:

- `thr = 0` → hold quota (hover);
- `thr = +1` → salita massima;
- `thr = −1` → **discesa massima**.

Risultato: nell'istante del takeover il drone riceve simultaneamente un *setpoint di
velocità verticale verso il basso al massimo* e si trova già in transitorio di roll.
Questo è il **fattore scatenante non visibile** se si guardano solo gli stick del
cyclic (che effettivamente erano centrati).

### Fase 4 — PIO sul cyclic (t = 1076.0 → 1078.5 s)

In risposta alla situazione, il pilota agisce sul cyclic. Da `manual_control_setpoint`
in questa finestra:

- Roll stick: oscillazioni −0.41 → −0.95 → +0.26 (saturazioni multiple);
- Pitch stick: oscillazioni −1.0 → +0.93 → +0.36 (saturato);
- Yaw stick: rimane a 0;
- Throttle stick: **continua a −1.0** per tutta la fase.

I comandi del pilota sono sfasati rispetto al moto del velivolo e ne alimentano
l'oscillazione invece di smorzarla. Il rate setpoint satura a ±220 °/s su roll, il
velivolo non riesce a inseguire: ampiezze di roll +56°, −47°, +77°, fino a **−104°**
(capovolto). Questo è il pattern canonico di **PIO (Pilot Induced Oscillation)**,
amplificato dalla discesa imposta dal throttle.

### Fase 5 — Override del commander e impatto (t = 1078.5 → 1079.9 s)

A t=1078.52 s il commander cambia autonomamente `nav_state` da 2 (POSCTL) a **15
(AUTO_LAND)**, togliendo il controllo al pilota. Il control allocator riduce i
comandi motore al minimo di discesa controllata: in `actuator_motors.control` i
valori crollano da ~0.6 a 0.0–0.16 e gli RPM ESC passano da ~6000 a ~1000–2000.

Da notare: questo crollo dei comandi motore precede di ~0.6 s il timestamp con cui
`failure_detector_status` registra `fd_roll = 1` (t=1079.15 s). La discrepanza è
dovuta al campionamento basso (~2 Hz) di `failure_detector_status`: il trigger
fisico è anteriore, e il commander reagisce sul flag interno prima che venga
loggato.

A ~3 m di quota, capovolto, con i motori a thrust di land minimo, il drone
**cade in caduta libera**: `vz = +4.95 m/s` all'istante dell'impatto. Le metriche
IMU saturano (accel_vib da 2 → 9 m/s², gyro_vib da 0.28 → 1.66 rad/s, clipping
> 0 su X/Y/Z), confermando l'urto.

## Diagnosi finale

| Livello                | Causa                                               | Evidenza chiave |
| ---------------------- | --------------------------------------------------- | --------------- |
| **Primaria (procedurale)** | **Takeover in POSCTL con throttle stick a −1.0**: PX4 ha letto un comando di discesa massima nell'istante del cambio modo. Lo stick non è mai stato ricentrato prima del takeover. | `manual_control_setpoint.throttle = −1.0` per tutto il log, anche pre-takeover |
| **Concorrente (controllo pilota)** | **PIO sul cyclic**: comandi roll/pitch saturati a ±0.95–1.0 sfasati rispetto al moto del drone, che hanno alimentato l'oscillazione divergente. | Roll attuato +77° → −104° con stick saturati e rate setpoint a ±220°/s |
| **Aggravante (dinamica iniziale)** | Transitorio in roll/pitch già presente in AUTO_MISSION prima del takeover (roll da 3° a 42° in 0.6 s), riconducibile a tuning aggressivo o effetto suolo a ~3 m. | Roll cresce a +42° con `nav_state = 3` |

**Nessuna causa hardware**: telemetria ESC e battery `OK`, vibrazioni nominali fino
all'impatto, EKF senza fault. Il crollo dei comandi motore osservato a t≈1078.8 s
non è un guasto: è l'attivazione automatica di `AUTO_LAND` da parte del commander
con il drone capovolto.

## Plot di riferimento

Cartella `plot/incidente/`:

1. `cronologia_volo.png`     — roll/pitch/yaw + quota con eventi annotati
2. `dinamica_angolare.png`   — rate setpoint vs misurato sui 3 assi (saturazione PIO)
3. `motori_rpm.png`          — RPM 6 ESC + comandi motore normalizzati
4. `comandi_pilota.png`      — stick RC (roll/pitch/yaw e throttle)
5. `vibrazioni_impatto.png`  — `accel/gyro_vibration_metric` + clipping (firma impatto)

## Raccomandazioni di manutenzione preventiva

1. **Procedura pre-takeover obbligatoria**: lo stick di throttle deve essere
   **centrato (thr ≈ 0)** prima del cambio modo da AUTO a POSCTL/ALTCTL. Aggiungere
   alla checklist di volo. Valutare l'uso del parametro `COM_RC_OVERRIDE` per
   imporre che il takeover sia accettato solo con stick neutri.
2. **Verifica strutturale post-impatto**: controllare deformazioni frame F550,
   integrità eliche/motori, fissaggi GPS mast, eventuali microfratture PCB Pixhawk.
3. **Re-calibrazione**: accelerometri, giroscopi e magnetometri dopo l'urto; il
   clipping registrato (>40 conteggi) può aver introdotto bias residui.
4. **Revisione tuning PID rate controller**: i guadagni attuali producono saturazione
   del rate setpoint (±220 °/s) già a 3 m. Valutare riduzione di `MC_ROLLRATE_P` /
   `MC_PITCHRATE_P` o aumento di `MC_ROLLRATE_D` per smorzare le oscillazioni.
5. **Modo di transizione**: preferire ALTCTL come modo di passaggio invece di POSCTL
   in caso di takeover di emergenza; in ALTCTL la mappatura del throttle è più
   permissiva e l'errore di stick è meno catastrofico.
6. **Failsafe**: la soglia `FD_FAIL_R` (60°) ha funzionato, ma il velivolo era già
   irrecuperabile. Considerare l'attivazione del **parachute** o di un termination
   anticipato (`FD_FAIL_R_TTRI` < 0.3 s) per voli a bassa quota.
