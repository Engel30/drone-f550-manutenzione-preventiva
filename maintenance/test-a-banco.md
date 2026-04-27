# Test a banco — procedura di sicurezza e bypass arming

> Configurazione del Pixhawk 6X / PX4 per consentire l'armamento e il funzionamento dei motori in laboratorio (indoor, senza GPS valido), con prescrizioni di sicurezza.

## Premessa di sicurezza

> ⚠️ **Eliche sempre rimosse** durante qualsiasi test a banco. Un disarmo→riarmo accidentale con eliche montate è la prima causa di incidenti in laboratorio.

> ⚠️ **Drone vincolato** al banco di prova durante i test a motori accesi.

> ⚠️ Disabilitare i check di arming significa rinunciare a salvaguardie. La configurazione descritta è **valida solo a banco**, mai in volo. I parametri vanno ripristinati prima di qualsiasi volo reale.

## Problema indoor: rifiuto di arming per GPS

In ambiente indoor il GPS riporta TDOP/HDOP elevati e l'EKF non si fida del fix. Le modalità di volo che richiedono posizione (Position, Mission, Hold, Return) bloccano l'arming. Per test di laboratorio si impiegano modalità **GPS-indipendenti** e si permette l'arming senza fix valido.

## Architettura dei check di arming in PX4

L'arming è un AND di check indipendenti (GPS, magnetometro, consistenza IMU, batteria, RC, salute EKF). È una scelta progettuale: non si disabilita la sicurezza con un singolo flag, ogni check ha il suo parametro. Si interviene solo sui check effettivamente impeditivi nel contesto di banco, lasciando attivi gli altri.

## Parametri configurati per il bench test

| Parametro | Valore | Significato |
|-----------|-------:|-------------|
| `COM_ARM_WO_GPS` | `1` | Permette arming senza fix GPS valido |
| Modalità di volo | **Stabilized** o **Manual** | Non richiedono posizione GPS/EKF |

I check **non** disabilitati (e che restano alleati per la diagnostica):
- `COM_ARM_MAG_STR` — coerenza magnetometri
- `COM_ARM_IMU_*` — consistenza tra le 3 IMU
- Check batteria (se power module configurato)

Disabilitare questi check è **sconsigliato** anche a banco: una IMU che diverge o un magnetometro disturbato sono informazioni utili da intercettare *prima* del volo.

## Procedura operativa

1. Eliche **rimosse**, drone vincolato al banco
2. Power module collegato, batteria carica
3. Verificare `COM_ARM_WO_GPS = 1` in *Parameters*
4. Selezionare modalità **Stabilized** dal radiocomando o da QGC
5. Armare il sistema
6. Throttle al minimo, poi piccola escursione per verificare risposta motori e popolazione di `esc_status`
7. Disarmare prima di disconnettere la batteria

Se l'arming è ancora rifiutato, QGC mostra il motivo specifico nel pannello *Arming Check Report* (icona scudo): leggere il messaggio esatto invece di disabilitare a tappeto altri check.

## Profili "banco" vs "volo"

Il rischio principale di questa configurazione è dimenticare `COM_ARM_WO_GPS = 1` durante un volo reale. Per la relazione e per la sicurezza operativa è opportuno mantenere due **set di parametri** distinti, esportabili via QGC:

| Profilo | `COM_ARM_WO_GPS` | Modalità tipica | Uso |
|---------|:----------------:|-----------------|-----|
| Banco | `1` | Stabilized / Manual | Test in laboratorio, indoor, senza GPS |
| Volo | `0` | Position / Altitude | Volo outdoor con GPS valido |

QGC consente l'esportazione in `.params` (text file) — conservare entrambe le versioni nel repository sotto `maintenance/profili-parametri/` (da creare al momento del primo export).
