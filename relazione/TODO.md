# TODO — questioni aperte sulla relazione

Lista di punti da rivedere prima della consegna. Aggiungere qui ciò che emerge
durante le verifiche, così non si perde.

---

## ✅ Cap. 6 — discrepanza sulla causa del dropout GPS: EMI vs contatto meccanico

**RISOLTO (2026-06-16).** Riallineato il testo alla lettura \enquote{due cause in
sequenza}: il dropout è attribuito al **contatto meccanico intermittente** (EMI
esplicitamente falsificata con la riga `13_51_13` e le metriche RF costanti), la
schermatura resta come parte della soluzione (con la ri-crimpatura come correzione
dominante), e un bridge collega esplicitamente il guasto cavo (risolto) al guasto
RTK (residuo, Modo B) come secondo modo indipendente. Modificati:
`06-casi-diagnostici.tex` (paragrafo BER, caption `tab:ber`, paragrafo causa
radice + bridge) e `10-conclusioni.tex`. Sotto la cronistoria originale del punto.

---



**Problema.** Il Capitolo 6 (sezione \enquote{Messa a punto del collegamento GPS}
→ \enquote{Dropout del GPS in volo}) attribuisce la causa radice del dropout a
**interferenze elettromagnetiche (EMI)**:

> «…la causa radice nelle interferenze elettromagnetiche (EMI): il cavo GPS
> auto-costruito, non schermato e instradato vicino ai cavi di potenza, captava
> il disturbo irradiato dallo stadio motori. Questo spiega la correlazione con il
> regime: più corrente scorre nei cavi di potenza, più forte è il disturbo.»

Ma il documento diagnostico
`maintenance/troubleshooting-gps-dropout-2026-05-27.md` **falsifica
esplicitamente l'ipotesi EMI** e conclude per un **contatto meccanico
intermittente nel cavo, attivato dalla vibrazione**:

- Le metriche RF del modulo (`noise_per_ms`, `jamming_indicator`, `agc`) sono
  **costanti** prima/durante/dopo i gap → nessuna interferenza RF in atto.
- **Controprova decisiva (ed è una riga già presente nella nostra tabella
  `tab:ber`):** il volo `13_51_13` gira a **39 597 sum-RPM** (pieno regime di
  lift → piena corrente nei cavi motore) **con BER 0,2 %**. Se il meccanismo
  fosse EMI accoppiata dalla corrente, quel volo dovrebbe essere \enquote{sporco};
  invece è pulito. **La relazione include la riga che contraddice la propria
  spiegazione.**
- Il BER oscilla 0,2 % ↔ 49 % tra voli consecutivi a parità di regime →
  firma di un difetto meccanico intermittente (come si posa il cavo), non di una
  EMI stazionaria che scalerebbe con la corrente.

**Nota.** La **soluzione resta valida** in entrambe le letture: la ricostruzione
del cavo con schermatura + ri-crimpatura ha rimosso sia un eventuale problema EMI
sia (soprattutto) il contatto marginale. È il **meccanismo attribuito** a essere
errato, non la correzione.

**Decisione presa (2026-06-15):** non toccare ora il testo; ci torniamo. La
direzione probabile è riallineare la spiegazione del Cap. 6 a
\enquote{contatto marginale intermittente modulato dalla vibrazione} (mantenendo
la schermatura come parte della soluzione), oppure — se si vuole tenere il taglio
EMI — spiegare comunque la riga `13_51_13` che la smentisce.

**File da toccare quando si decide:**
`relazione/capitoli/06-casi-diagnostici.tex` (paragrafo dopo `tab:ber`) e
`relazione/capitoli/10-conclusioni.tex` (cita \enquote{interferenze
elettromagnetiche» tra i risultati).

---

## 🔴 BOM/relazione — verificare marca e modello reali di GPS e base RTK

**Problema.** I dati di GPS e base RTK in BOM (e di riflesso nella relazione) sono
incerti o presunti, probabilmente non corretti:

- **A-06 GPS**: in BOM è `CubePilot Here+ o compatibile`. Dai log il chip GNSS è
  con certezza **u-blox NEO-M8P-0, firmware HPG 1.40ROV** (stringa `MON-VER`
  ripetuta in tutti i reinit). Il Here+ monta effettivamente un M8P, quindi è
  *plausibile*, ma il \enquote{o compatibile} va sciolto: confermare modello esatto
  del modulo/carrier (Here+ vs Here2 vs altro) e versione.
- **A-07 Base RTK**: in BOM è `TBD (marca da verificare)`. Da identificare marca e
  modello reali (e set di messaggi RTCM3 supportati — rilevante per il Modo B RTK).

**Come verificare.** Ispezione fisica delle etichette su modulo e base; in QGC il
modulo riporta firmware/protocollo (`[gps] u-blox firmware version ...`); per la
base, connetterla e leggere `MON-VER` o l'etichetta. Aggiornare poi:
- `docs/BOM.md` righe **A-06** e **A-07** (sciogliere i TBD/«o compatibile»);
- eventuali citazioni del modulo nella relazione (Cap. 2/3 e troubleshooting).
