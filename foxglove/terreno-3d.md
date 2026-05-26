# Terreno 3D con edifici — design document

> Documento di progettazione per l'estensione dell'overlay satellitare attuale
> da **piano 2D statico** (ESRI World Imagery, 200 m attorno al takeoff) a
> **terreno 3D con edifici** (ortofoto AGEA + DEM Copernicus + edifici OSM,
> bbox calcolata sull'intera traiettoria di tutti i voli archiviati).
>
> Stato: **non implementato**. Questo file descrive cosa fare e perché. Da
> applicare quando si decide di procedere.

## Indice

1. [Motivazione](#motivazione)
2. [Stato attuale](#stato-attuale)
3. [Sorgenti dati scelte](#sorgenti-dati-scelte)
4. [Architettura](#architettura)
5. [Step 1 — Bounding box dai log](#step-1--bounding-box-dai-log)
6. [Step 2 — Terreno (DEM + ortofoto)](#step-2--terreno-dem--ortofoto)
7. [Step 3 — Edifici (OSM estrusi)](#step-3--edifici-osm-estrusi)
8. [Step 4 — Integrazione in ulog_to_mcap.py](#step-4--integrazione-in-ulog_to_mcappy)
9. [Limiti noti e mitigazioni](#limiti-noti-e-mitigazioni)
10. [Possibili estensioni future](#possibili-estensioni-future)

---

## Motivazione

L'overlay satellitare attuale (`--satellite`) ha due problemi:

1. **Qualità texture insufficiente**: ESRI World Imagery oltre zoom 19 ha buchi
   o blur in molte zone d'Italia. La risoluzione effettiva è ~30 cm/px.
2. **Bidimensionale**: la scena 3D di Foxglove mostra un piano piatto a quota
   zero. Manca il rilievo del terreno e qualunque traccia degli ostacoli
   (edifici, capannoni) attorno al drone.

Obiettivo: scena 3D realistica del campo volo che copra tutta l'area visitata
dai voli archiviati, restando completamente gratuita e riproducibile.

## Stato attuale

Pipeline in `foxglove/satellite_layer.py` + `foxglove/ulog_to_mcap.py:366-436`:

```
ESRI tile XYZ → stitch PNG → GLB con quad XY → ModelPrimitive in SceneUpdate
                                                  (un solo timestamp)
```

Risultato: una `foxglove.SceneUpdate` con entità `satellite_ground`, emessa
una volta sola, contenente un piano 200 m × 200 m a `z = -0.05 m`.

## Sorgenti dati scelte

| Strato | Sorgente | Risoluzione | Accesso | Note |
|---|---|---|---|---|
| Ortofoto | **AGEA via WMS PCN Minambiente** | ~20 cm/px | HTTP, no auth | URL: `http://wms.pcn.minambiente.it/ogc?map=/ms_ogc/WMS_v1.3/raster/ortofoto_colore_06.map`. Copre tutta Italia. HTTP only (non HTTPS) — limite del servizio pubblico. |
| Elevazione | **Copernicus GLO-30 DEM** | 30 m | HTTPS S3 pubblico | Bucket: `s3://copernicus-dem-30m/`. GeoTIFF COG (Cloud Optimized). Niente registrazione. |
| Edifici | **OpenStreetMap via Overpass API** | poligoni di pianta | HTTPS, no auth, rate-limited | Endpoint: `https://overpass-api.de/api/interpreter`. Tag `building=*`, altezze in `height` o `building:levels`. |

### Perché queste scelte (e cosa è stato scartato)

- **TINITALY (INGV) scartato**: ha risoluzione 10 m migliore di Copernicus,
  ma richiede registrazione manuale con email. Viola la riproducibilità
  citata in `CLAUDE.md`. Copernicus 30 m è sufficiente per visualizzare
  colline e dislivelli del campo volo.
- **Geoportale Emilia-Romagna scartato**: il WMS `agea2014_rgb` risponde
  401 NTLM, richiede credenziali ER.
- **Mapbox / MapTiler scartati**: richiedono API key. AGEA PCN è davvero
  zero-config.
- **Google Photorealistic 3D Tiles scartato**: qualità superiore ma
  Foxglove non supporta 3D Tiles nativamente; pre-conversione in glTF è
  complessa e va comunque autenticata.

## Architettura

Quattro step indipendenti. Ognuno può essere fermato e dà già un risultato:

```
┌──────────────────────────────────────────────────────────────────┐
│  log/**/*.ulg                                                    │
│       │                                                          │
│       ▼                                                          │
│  [1] bbox_from_logs.py  →  (lat_min, lon_min, lat_max, lon_max)  │
│                                                                  │
│       │ + buffer 200 m                                           │
│       ▼                                                          │
│  [2] terrain_layer.py::build_terrain_glb                         │
│       ├── agea_fetch()    → ortofoto PNG                         │
│       ├── dem_fetch()     → array numpy heights[ny, nx]          │
│       └── (triangola, drapi texture)  → mesh                     │
│                                                                  │
│       │                                                          │
│       ▼                                                          │
│  [3] terrain_layer.py::osm_buildings_fetch + extrude             │
│       └── Overpass QL → lista poligoni con altezza               │
│       └── extrude_to_mesh() → triangoli appesi alla mesh         │
│                                                                  │
│       │                                                          │
│       ▼                                                          │
│  [4] ulog_to_mcap.py --terrain                                   │
│       → emette SceneUpdate(entity_id="terrain_3d", model=GLB)    │
│       → SOSTITUISCE l'attuale entity_id="satellite_ground"       │
│         se --terrain è attivo (i due overlay sono mutex)         │
└──────────────────────────────────────────────────────────────────┘
```

I due overlay (`--satellite` 2D rapido, `--terrain` 3D completo) **non si
attivano insieme**: dovrebbero essere mutuamente esclusivi nella CLI.

---

## Step 1 — Bounding box dai log

**File nuovo**: `foxglove/bbox_from_logs.py`

**Scopo**: scansionare ricorsivamente `log/`, aprire ogni `.ulg`, estrarre
i campi `lat` / `lon` dal topic `vehicle_global_position`, restituire
`(lat_min, lon_min, lat_max, lon_max, lat_takeoff, lon_takeoff)` con un
buffer di 200 m oltre i bordi.

**Funzioni chiave** (firma proposta):

```python
def compute_bbox(log_dir: Path, buffer_m: float = 200.0) -> Bbox:
    """
    Apre tutti i .ulg sotto log_dir, calcola la bounding box geografica
    di vehicle_global_position. Aggiunge buffer_m di margine convertendo
    metri → gradi alla latitudine media.

    Ritorna Bbox(lat_min, lon_min, lat_max, lon_max, lat_c, lon_c).
    """

def _bbox_buffer_deg(lat_c: float, buffer_m: float) -> tuple[float, float]:
    """
    Conversione metri → gradi.
        Δlat = buffer_m / 111_320
        Δlon = buffer_m / (111_320 · cos(lat_c))
    """
```

**Librerie**: `pyulog` (già nel progetto, vedi `ulog_to_mcap.py`).

**Gotcha**: i log a terra hanno `vehicle_global_position` con timestamp ma
spesso lat/lon = 0 (no GPS fix). Filtrare `eph < 10 m` o `lat != 0` prima
di calcolare min/max.

**Output di esempio**:

```
Modena, campo F.lli Cervi:
  Voli analizzati: 23  (in log/2026-04-27, log/2026-04-28, log/2026-05-25, log/2026-05-26)
  Bbox raw:    44.6478 → 44.6512  N,  10.9156 → 10.9201 E   (~ 380 m × 360 m)
  Bbox + 200m: 44.6460 → 44.6530  N,  10.9128 → 10.9229 E   (~ 780 m × 760 m)
  Centro:      44.6495, 10.9178
```

---

## Step 2 — Terreno (DEM + ortofoto)

**File nuovo**: `foxglove/terrain_layer.py`

### 2a. Download DEM Copernicus

Il bucket S3 espone tile da 1°×1° con nome `Copernicus_DSM_COG_10_N{LL}_00_E{LLL}_00_DEM.tif`. Per il campo volo serve **un solo tile** (l'intera Italia è
~12 tile).

```python
def dem_fetch(bbox: Bbox, cache_dir: Path) -> np.ndarray:
    """
    Scarica i tile Copernicus GLO-30 che coprono bbox e li ricampiona su
    una griglia regolare allineata alla bbox.

    Ritorna heights[ny, nx] in metri ASL.
    Risoluzione griglia: ~10 m/punto (sufficiente per rilievi del campo).
    """
```

**URL pattern**:
```
https://copernicus-dem-30m.s3.amazonaws.com/Copernicus_DSM_COG_10_N{LL}_00_E{LLL}_00_DEM/Copernicus_DSM_COG_10_N{LL}_00_E{LLL}_00_DEM.tif
```
(es. per Modena: `N44_00_E010_00` — il prefisso `N{LL}` è il floor della latitudine).

**Librerie suggerite**: `rasterio` (legge GeoTIFF COG facendo HTTP range
requests, evita di scaricare 50 MB se ti serve un 1 km²).

**Riferimento di quota**: i DEM Copernicus sono in **WGS84 ellipsoidico**,
non MSL. Per il drone vale lo stesso (`vehicle_global_position.alt` PX4
è ellipsoidico). Se si nota offset costante, sottrarre l'undulazione del
geoide (EGM2008, ~46 m a Modena) — ma probabilmente non serve.

### 2b. Download ortofoto AGEA

WMS standard, richiesta `GetMap` con bbox in EPSG:4326 (lat/lon) o EPSG:3857
(Web Mercator). Il PCN supporta entrambi.

```python
def agea_fetch(bbox: Bbox, pixels_per_meter: float, cache_dir: Path) -> Image.Image:
    """
    Scarica una singola ortofoto PNG sulla bbox. Per bbox grandi (> ~1 km²)
    spezzare in tile da 2048×2048 e cucire, il server WMS rifiuta richieste
    troppo grandi.
    """
```

**URL pattern (esempio)**:
```
http://wms.pcn.minambiente.it/ogc?
    map=/ms_ogc/WMS_v1.3/raster/ortofoto_colore_06.map
    &service=WMS&version=1.3.0&request=GetMap
    &layers=OI.ORTOIMMAGINI.2012
    &bbox=44.646,10.913,44.653,10.923
    &crs=EPSG:4326&width=2048&height=2048&format=image/png
```

**Layer disponibili**: `OI.ORTOIMMAGINI.2006` (AGEA 2006), `2012`, `2018`,
`OI.ORTOFOTO.COLORE-AGEA-2019`. Usare la più recente disponibile sulla zona
(la copertura varia per regione). Strategia: provare in ordine 2019 → 2018
→ 2012 → 2006 e usare la prima che ritorna pixel non bianchi.

**Cache**: stessa logica di `satellite_layer.py:.tile_cache` — file PNG
con chiave bbox+layer.

### 2c. Costruzione mesh

```python
def build_terrain_glb(bbox: Bbox,
                      heights: np.ndarray,   # [ny, nx], m
                      ortho: Image.Image,
                      lat_origin: float,
                      lon_origin: float) -> bytes:
    """
    Costruisce un GLB con:
      - vertices: griglia nx × ny in ENU locale (origine = takeoff)
      - z = heights - heights[lat_origin, lon_origin]  (terreno relativo al takeoff)
      - UV: mappa bilineare bbox → ortho
      - indices: 2 triangoli per cella

    Ritorna i bytes GLB pronti per ModelPrimitive.
    """
```

Conversione coordinate (riferimento: `satellite_layer.py:43-54` ma serve
l'inverso, lat/lon → metri ENU):

```python
dx_m = (lon - lon_origin) * 111_320 * cos(lat_origin)
dy_m = (lat - lat_origin) * 111_320
dz_m = h - h_origin
```

Per bbox piccole (< 2 km) la proiezione flat-earth è accurata a meno di
qualche cm.

**Numero vertici**: bbox 800 m × 800 m con DEM 10 m → 80 × 80 = 6400 vertici,
12 800 triangoli. Trascurabile per Foxglove.

**Texture mapping**: la texture (PNG ortofoto) è già allineata alla bbox.
UV di ogni vertice:
```python
u = (lon - lon_min) / (lon_max - lon_min)
v = 1.0 - (lat - lat_min) / (lat_max - lat_min)   # V flipped (glTF)
```

**Riutilizzabilità**: la funzione `build_textured_plane_glb` in
`satellite_layer.py:115-222` è il template — stesso pattern di accessor,
bufferView, ecc. Cambia solo la mesh (più triangoli, più UV) e la texture
PNG (più grande).

---

## Step 3 — Edifici (OSM estrusi)

### 3a. Query Overpass

Una query QL per la bbox:

```overpass
[out:json][timeout:25];
(
  way["building"]({{bbox}});
  relation["building"]({{bbox}});
);
out body geom;
```

POST a `https://overpass-api.de/api/interpreter` con body `data=<query>`.

**Rate limit**: Overpass impone ~2 query/min sostenute. Per il nostro uso
(una query per ogni rigenerazione MCAP) è abbondante. Cache su disco la
risposta JSON per bbox+timestamp giorno.

### 3b. Parsing e estrusione

```python
def osm_buildings_fetch(bbox: Bbox, cache_dir: Path) -> list[Building]:
    """
    Ritorna lista di Building(footprint_latlon, height_m).
    height_m: legge in ordine `height`, `building:height`,
    `building:levels` * 3.0, fallback 6.0 m.
    """

def extrude_buildings(buildings: list[Building],
                      lat_origin: float, lon_origin: float,
                      ground_z_at: Callable[[float, float], float],
                      ) -> tuple[np.ndarray, np.ndarray]:
    """
    Estrude ogni footprint a un parallelepipedo (pareti + tetto).
    z_base = ground_z_at(lat_centroid, lon_centroid)  (quota DEM)
    z_top  = z_base + height_m

    Ritorna (vertices, indices) da concatenare alla mesh del terreno.
    """
```

**Algoritmo estrusione**:
1. Footprint ha N vertici → 2N vertici (base + tetto).
2. Pareti laterali: per ogni lato del poligono, 2 triangoli (quad).
3. Tetto: triangolazione del poligono base (fan triangulation se convesso,
   altrimenti `mapbox-earcut` o `shapely`).

**Colore**: tinta unica grigia (RGB 0.7, 0.7, 0.7) come secondo materiale
nel GLB. Niente texture per gli edifici.

### 3c. Merge nella stessa mesh

Il GLB finale ha **due primitive** nella mesh:

1. `primitive[0]`: terreno triangolato, materiale 0 (texturato con ortofoto)
2. `primitive[1]`: edifici estrusi, materiale 1 (grigio uniforme)

Foxglove le renderizza assieme. Sempre una sola `ModelPrimitive` da emettere.

---

## Step 4 — Integrazione in ulog_to_mcap.py

### 4a. Nuovi argomenti CLI

```python
ap.add_argument("--terrain", action="store_true",
                help="overlay 3D completo: DEM Copernicus + ortofoto AGEA + "
                     "edifici OSM estrusi. Mutuamente esclusivo con --satellite. "
                     "Bbox calcolata su tutti i .ulg in log/.")
ap.add_argument("--terrain-buffer", type=float, default=200.0,
                help="margine in metri attorno alla bbox dei voli.")
ap.add_argument("--terrain-no-buildings", action="store_true",
                help="solo DEM+ortofoto, salta OSM (più veloce).")
```

### 4b. Validazione mutex con --satellite

```python
if args.terrain and args.satellite:
    ap.error("--terrain e --satellite sono mutuamente esclusivi. "
             "Usa --satellite per overlay 2D veloce, --terrain per "
             "scena 3D completa.")
```

### 4c. Emissione SceneUpdate

Stessa struttura di `ulog_to_mcap.py:366-436` ma:
- `entity.id = "terrain_3d"` (non più `satellite_ground`)
- GLB generato da `terrain_layer.build_terrain_glb(...)` invece di
  `satellite_layer.build_satellite_glb_for_takeoff(...)`
- Pose del modello: invariata (origine, identity quaternion). Il GLB
  è già georeferenziato in ENU locale.

### 4d. Aggiornamento README

Aggiungere in `foxglove/README.md` una sezione `### Overlay 3D
(--terrain)` parallela alla sezione `### Overlay satellitare
(--satellite)` esistente, che spiega:
- comando: `python3 foxglove/ulog_to_mcap.py --auto-trim --terrain`
- prima esecuzione: download di ~50 MB di tile + DEM + OSM (3–5 min)
- esecuzioni successive: cache, ~5 s
- come disattivare la griglia di Foxglove (già documentato per
  `--satellite`)

---

## Limiti noti e mitigazioni

| Limite | Causa | Mitigazione |
|---|---|---|
| DEM 30 m non vede dossi piccoli, recinzioni, dossi | Risoluzione Copernicus | Per la relazione: dichiarare come limite. Per ispezioni precise serve LiDAR proprio. |
| Alberi, pali, cavi mancanti | OSM li mappa raramente | Dichiarare limite. Eventualmente integrare con tag OSM `power=line`, `barrier=hedge` in step futuro. |
| Texture AGEA "vecchia" (2018–2019) | PCN aggiorna lentamente | Sufficiente per riconoscere il campo. Eventuale fallback a 2012 / 2006 se 2019 buca. |
| HTTP non HTTPS per PCN | Limite servizio pubblico | Documentare. Non è dato sensibile, MITM è low-risk. |
| Overlay statico, non segue drone | Scelta di design (step 4 streaming non incluso) | Bbox copre tutta la traiettoria, drone resta sempre dentro la scena. |
| Foxglove rallenta con mesh > 1M tri | Limite renderer browser | Bbox 800 m × 800 m con DEM 30 m → 700 tri, ben sotto soglia. |

---

## Possibili estensioni future

Da considerare **solo se** il design base funziona e si vuole spingere oltre:

### Streaming dinamico (segue il drone)

Invece di una sola `SceneUpdate` al primo timestamp, emetterne una ogni N
secondi che ricarica le tile attorno alla posizione corrente del drone.
Foxglove sostituisce automaticamente entità con lo stesso `id` quando ne
arrivano di nuove. Permette zoom alto (z=20+) con tile piccole senza
allocare tutta l'area in RAM.

**Costo**: ~200 righe in più, parsing della traiettoria, gestione cache LRU
delle tile attive.

### LOD multilivello

Mesh terreno con risoluzione variabile: 5 m nel raggio di 100 m dal drone,
30 m oltre. Solo se la performance lo richiede.

### Integrazione con campi LiDAR locali

Se in futuro il campo volo viene rilevato con LiDAR aereo / TLS, sostituire
il DEM Copernicus con un DSM ad alta risoluzione locale. Stessa pipeline,
solo il loader DEM cambia.

### Mesh fotogrammetrica da voli precedenti

Costruire una mesh da fotogrammetria delle immagini del drone stesso
(usando Meshroom / ODM). Sostituirebbe AGEA con dati di prima mano. Ottimo
ma è un progetto a sé.

---

## Riferimenti

- Foxglove SceneUpdate schema:
  https://docs.foxglove.dev/docs/visualization/message-schemas/scene-update
- Copernicus GLO-30 su AWS Open Data:
  https://registry.opendata.aws/copernicus-dem/
- Geoportale Nazionale Minambiente (WMS AGEA):
  http://www.pcn.minambiente.it/mattm/servizio-wms/
- OpenStreetMap building tag:
  https://wiki.openstreetmap.org/wiki/Key:building
- glTF 2.0 spec (per costruire il GLB):
  https://registry.khronos.org/glTF/specs/2.0/glTF-2.0.html
- Implementazione attuale di riferimento:
  `foxglove/satellite_layer.py`, `foxglove/ulog_to_mcap.py:366-436`
