# Linee guida della relazione finale

> Documento di impostazione concordato il **2026-06-15**. Definisce tipo, tono,
> lunghezza e indice della relazione del corso di *Manutenzione Preventiva*
> (A.A. 2025/2026). Da rivedere se il docente fornisce un formato vincolante.

## 1. Tipo e impostazione

- **Genere**: relazione tecnica consegnata al docente, che **documenta il lavoro
  svolto** sul drone F550 (messa in funzione, configurazione, voli, acquisizione
  dati).
- **Struttura**: **tematico-cronologica**. I capitoli sono organizzati per tema;
  all'interno di ciascun tema si segue l'ordine temporale degli eventi. Questo
  evita di frammentare lo stesso argomento su più giornate (es. il GPS, toccato
  il 27/04, 25/05, 26/05, 27/05 e 04/06).
- **Filo conduttore**: il progetto prevedeva di *mettere in funzione il drone →
  configurarlo con QGroundControl → eseguire i test acquisendo dati*. La
  relazione segue questo arco.

## 2. Tono e registro

- Tecnico ma **chiaro e leggibile**; taglio descrittivo-operativo ("ecco il
  sistema e le attività svolte").
- Terminologia precisa (PX4, EKF2, uORB, BER…), ma al servizio del racconto, non
  fine a sé stessa.
- **Preferire tabelle a testo lungo e ridondante**. Numeri e parametri a
  supporto, raccolti in tabelle/appendici quando di dettaglio.
- Lingua: **italiano**.

## 3. Lunghezza

- **Massimo ~30 pagine.** Essenziale ma completa: non andare troppo nel
  dettaglio, ma non tralasciare nulla di sostanziale.
- I dettagli fini (tabelle log volo-per-volo, set completi di parametri, plot
  secondari) vanno in **appendice** o restano nei README della repo, richiamati
  per riferimento.

## 4. Indice

1. **Introduzione** — obiettivo del progetto, contesto del corso, sintesi del
   sistema.
2. **Il sistema** — architettura hardware (frame F550, Pixhawk 6X, propulsione,
   avionica, alimentazione) + sintesi BOM in tabella.
3. **Configurazione: QGroundControl & firmware PX4** — messa in funzione e
   configurazione via QGC, **con limitazioni e problematiche riscontrate**;
   migrazione GPS CAN→UART, power module, telemetria ESC, failsafe.
4. **Acquisizione dati** ⭐ — *cosa* viene loggato e *a che frequenza* (profilo
   `SDLOG_PROFILE`, topic uORB, rate IMU/ESC/GPS, FIFO ad alta frequenza).
   Capitolo cardine: è l'obiettivo dei test (configura → testa acquisendo dati).
5. **Campagna di volo** — come sono state condotte le sessioni e **tutti i tipi
   di volo**: baseline pale sane, pala danneggiata 5 %/10 % (*spiegare cosa
   significa*), traiettorie hover e quadrato, payload. Tabella Set A–E + quadro
   condizioni (vento, batteria).
6. **Casi diagnostici** — crash USB Cube Black, GPS no-fix, RTK, dropout GPS +
   incidente 26/05, riparazione cavo GPS schermato e volo di accettazione.
7. **[FORSE] Osservazioni sui dati** — brevi analisi/firme vibrazionali delle
   pale danneggiate. **Non richieste dal progetto** → inclusione da decidere.
8. **Manutenzione preventiva** — capitolo dedicato (aderenza al titolo del
   corso): checklist pre-volo, **FMEA** (modi di guasto, effetti, azioni
   preventive), lezioni apprese.
9. **Foxglove & interfaccia** *(bonus)* — strumento di visualizzazione non
   previsto dal progetto, realizzato per comodità di analisi. Posizionato in
   fondo come contributo extra.
10. **Conclusioni** + **Appendici** (tabelle log per data, set completi di
    parametri).

## 5. Apparato iconografico

Linea guida visiva: **ogni capitolo deve avere almeno una figura**; preferire
schemi e tabelle a muri di testo. Legenda dei tipi e di chi produce:

- 📷 **QGC** — screenshot di QGroundControl, da catturare (anche in replica).
- 📸 **Foto** — scatto reale (cartella `img/`, oggi vuota).
- 📐 **Schema** — diagramma da generare (blocchi, planimetrie, pipeline); può
  generarli Claude (mermaid/SVG/matplotlib).
- 📊 **Plot** — già presente in `plot/`, da inserire.

| Cap. | Figura proposta | Tipo | Stato / nota |
|---|---|---|---|
| 1 Introduzione | Foto del drone F550 come immagine di apertura | 📸 | Da scattare |
| 2 Il sistema | **Schema a blocchi** dell'architettura (Pixhawk 6X ↔ GPS, ESC, RC, telemetria, power module) | 📐 | Da generare |
| 2 Il sistema | Foto del drone con componenti etichettati | 📸 | Da scattare |
| 3 Configurazione | Screenshot QGC: Airframe, Sensors/Calibration, Flight Modes, **Failsafe** | 📷 | Da catturare |
| 3 Configurazione | Screenshot QGC della **problematica/limitazione** (es. survey-in RTK, messaggi di errore) | 📷 | Da catturare |
| 3 Configurazione | **Schema migrazione GPS CAN→UART** (wiring prima/dopo) | 📐 | Da generare |
| 4 Acquisizione dati | **Schema pipeline di logging** (sensori → topic uORB → SDLOG → `.ulg` → analisi) | 📐 | Da generare |
| 4 Acquisizione dati | Tabella topic ↔ frequenza (IMU/ESC/GPS, FIFO) | tabella | Da `DATI_LOG.md` |
| 5 Campagna di volo | **Foto della pala danneggiata** 5 %/10 % (mostra cosa significa) | 📸 | Da scattare — chiave |
| 5 Campagna di volo | **Mappa numerazione motori M1–M6** dell'esacottero | 📐 | Da generare |
| 5 Campagna di volo | **Planimetria traiettorie** hover e quadrato 3×3 m | 📐 | Da generare |
| 5 Campagna di volo | Foto setup payload | 📸 | Da scattare |
| 6 Casi diagnostici | Plot **BER GPS** vs regime motori (`gps_dump_ber.py`) | 📊/📐 | Da generare dallo script |
| 6 Casi diagnostici | Plot incidente: cronologia, comandi pilota, dinamica angolare | 📊 | Esistenti in `plot/incidente/` |
| 6 Casi diagnostici | **Foto cavo GPS schermato** (treccia rame + drain wire) prima/dopo | 📸 | Da scattare |
| 7 [FORSE] Osservazioni | Plot **firme vibrazionali** pala (`imu_confronto.png`, `imu_vibrazione.png`) | 📊 | Esistenti in `plot/imu/` |
| 8 Manutenzione preventiva | Tabella **FMEA** + box **checklist pre-volo** | tabella | Da `maintenance/` |
| 8 Manutenzione preventiva | Diagramma di flusso della checklist pre-volo | 📐 | Opzionale |
| 9 Foxglove (bonus) | **Screenshot dell'interfaccia** realizzata (layout pannelli, modello 3D URDF, overlay satellitare) | 📷 | Da catturare — chiave del bonus |
| 9 Foxglove (bonus) | Schema pipeline `ulog→mcap` | 📐 | Da generare |

> Gli schemi 📐 li può preparare Claude su richiesta (formato vettoriale per resa
> formale). Screenshot 📷 e foto 📸 vanno raccolti durante/dopo le sessioni e
> messi in `img/` con nomi parlanti.

## 6. Punti aperti

- **Cap. 7 (Osservazioni sui dati)**: includere brevi analisi o no — da decidere.
- **Formato/template**: in stand-by fino a indicazioni del docente (vedi
  `CLAUDE.md`).
- **Lunghezza dei singoli capitoli**: da affinare durante la stesura, nel
  vincolo delle 30 pagine.
