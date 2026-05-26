"""
Genera un GLB (binary glTF) contenente un piano XY texturato con un'immagine
satellitare scaricata da ESRI World Imagery, da embeddare in un messaggio
foxglove.SceneUpdate.ModelPrimitive nel file MCAP.

Il piano è:
- centrato sul punto di takeoff del drone (che è (0,0,0) in local_origin
  grazie all'offset applicato in ulog_to_mcap.py);
- orientato ENU: +Y = nord, +X = est, +Z = up (normale del piano verso l'alto);
- a quota z ≈ 0 (leggermente sotto per evitare z-fighting col drone all'armo).

Dipendenze: numpy, Pillow, pygltflib (urllib è stdlib).
"""

from __future__ import annotations

import io
import math
import urllib.request
from pathlib import Path

import numpy as np
import pygltflib
from PIL import Image


ESRI_URL = (
    "https://server.arcgisonline.com/ArcGIS/rest/services/"
    "World_Imagery/MapServer/tile/{z}/{y}/{x}"
)
TILE_SIZE_PX = 256
USER_AGENT = "manutenzione-preventiva-freddi/1.0 (educational)"

# Z-offset del piano sotto il livello di terra ricostruito (m). Evita z-fighting
# col drone nei primi frame quando è ancora a terra.
PLANE_Z_OFFSET = -0.05


# ──────────────────────────────────────────────────────────────────────────
# Web Mercator: conversioni lat/lon ↔ tile XYZ
# ──────────────────────────────────────────────────────────────────────────

def _lonlat_to_tile_xy(lon: float, lat: float, z: int) -> tuple[float, float]:
    """Coordinate frazionarie di tile (Web Mercator XYZ)."""
    lat_rad = math.radians(lat)
    n = 2.0 ** z
    x = (lon + 180.0) / 360.0 * n
    y = (1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n
    return x, y


def _meters_per_pixel(lat: float, z: int) -> float:
    """Ground sample distance Web Mercator a una data latitudine + zoom."""
    return 156543.03 * math.cos(math.radians(lat)) / (2 ** z)


# ──────────────────────────────────────────────────────────────────────────
# Tile downloader (con cache su disco)
# ──────────────────────────────────────────────────────────────────────────

def download_satellite_patch(
    center_lat: float,
    center_lon: float,
    size_m: float,
    zoom: int,
    cache_dir: Path,
) -> tuple[Image.Image, float, float]:
    """Scarica e cuce le tile ESRI necessarie a coprire size_m × size_m attorno
    a (center_lat, center_lon), poi ritaglia esattamente al centro.

    Ritorna (immagine_PIL, width_m, height_m). width_m/height_m possono
    differire di < 1 px da size_m a causa del rounding pixel.
    """
    mpp = _meters_per_pixel(center_lat, zoom)
    half_size_px = (size_m / 2.0) / mpp

    cx_t, cy_t = _lonlat_to_tile_xy(center_lon, center_lat, zoom)
    half_size_t = half_size_px / TILE_SIZE_PX

    tx_lo = int(math.floor(cx_t - half_size_t))
    tx_hi = int(math.floor(cx_t + half_size_t))
    ty_lo = int(math.floor(cy_t - half_size_t))
    ty_hi = int(math.floor(cy_t + half_size_t))
    nx, ny = tx_hi - tx_lo + 1, ty_hi - ty_lo + 1

    cache_dir.mkdir(parents=True, exist_ok=True)
    stitched = Image.new("RGB", (nx * TILE_SIZE_PX, ny * TILE_SIZE_PX))
    print(f"  Scarico {nx}×{ny} = {nx*ny} tile ESRI (zoom {zoom}, "
          f"~{mpp:.2f} m/px)…")

    for ix, tx in enumerate(range(tx_lo, tx_hi + 1)):
        for iy, ty in enumerate(range(ty_lo, ty_hi + 1)):
            tile_path = cache_dir / f"esri_z{zoom}_x{tx}_y{ty}.png"
            if not tile_path.exists():
                url = ESRI_URL.format(z=zoom, x=tx, y=ty)
                req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
                with urllib.request.urlopen(req, timeout=15) as resp:
                    tile_path.write_bytes(resp.read())
            stitched.paste(Image.open(tile_path), (ix * TILE_SIZE_PX, iy * TILE_SIZE_PX))

    cx_px = (cx_t - tx_lo) * TILE_SIZE_PX
    cy_px = (cy_t - ty_lo) * TILE_SIZE_PX
    left   = int(round(cx_px - half_size_px))
    upper  = int(round(cy_px - half_size_px))
    right  = int(round(cx_px + half_size_px))
    lower  = int(round(cy_px + half_size_px))
    cropped = stitched.crop((left, upper, right, lower))
    return cropped, (right - left) * mpp, (lower - upper) * mpp


# ──────────────────────────────────────────────────────────────────────────
# Generatore GLB: piano texturato single-quad
# ──────────────────────────────────────────────────────────────────────────

def build_textured_plane_glb(
    image: Image.Image,
    width_m: float,
    height_m: float,
) -> bytes:
    """Costruisce un GLB con un piano XY (z=0) texturato con `image`.

    Convenzioni UV (V=0 in alto, glTF standard):
        v0: SW (−W/2, −H/2, 0) → UV (0, 1)
        v1: SE (+W/2, −H/2, 0) → UV (1, 1)
        v2: NE (+W/2, +H/2, 0) → UV (1, 0)
        v3: NW (−W/2, +H/2, 0) → UV (0, 0)
    Winding CCW vista dall'alto → normale +Z (visibile da sopra).
    `doubleSided=True` per renderlo visibile anche da sotto se la camera scende.
    """
    W, H = width_m / 2.0, height_m / 2.0

    positions = np.array([
        [-W, -H, 0.0],
        [+W, -H, 0.0],
        [+W, +H, 0.0],
        [-W, +H, 0.0],
    ], dtype=np.float32)
    uvs = np.array([
        [0.0, 1.0],
        [1.0, 1.0],
        [1.0, 0.0],
        [0.0, 0.0],
    ], dtype=np.float32)
    indices = np.array([0, 1, 2, 0, 2, 3], dtype=np.uint16)

    png_io = io.BytesIO()
    image.save(png_io, format="PNG", optimize=True)
    png_bytes = png_io.getvalue()

    pos_bytes = positions.tobytes()
    uv_bytes = uvs.tobytes()
    idx_bytes = indices.tobytes()
    # Padding a 4 byte fra blocchi binari (richiesto da glTF)
    def pad4(b: bytes) -> bytes:
        return b + b"\x00" * ((4 - len(b) % 4) % 4)

    pos_bytes = pad4(pos_bytes)
    uv_bytes  = pad4(uv_bytes)
    idx_bytes = pad4(idx_bytes)
    png_bytes_padded = pad4(png_bytes)

    buf = pos_bytes + uv_bytes + idx_bytes + png_bytes_padded

    off_pos = 0
    off_uv  = off_pos + len(pos_bytes)
    off_idx = off_uv + len(uv_bytes)
    off_png = off_idx + len(idx_bytes)

    gltf = pygltflib.GLTF2(
        scene=0,
        scenes=[pygltflib.Scene(nodes=[0])],
        nodes=[pygltflib.Node(mesh=0)],
        meshes=[pygltflib.Mesh(primitives=[
            pygltflib.Primitive(
                attributes=pygltflib.Attributes(POSITION=0, TEXCOORD_0=1),
                indices=2,
                material=0,
            )
        ])],
        materials=[pygltflib.Material(
            pbrMetallicRoughness=pygltflib.PbrMetallicRoughness(
                baseColorTexture=pygltflib.TextureInfo(index=0),
                metallicFactor=0.0,
                roughnessFactor=1.0,
            ),
            doubleSided=True,
        )],
        textures=[pygltflib.Texture(source=0, sampler=0)],
        samplers=[pygltflib.Sampler(
            magFilter=9729,   # LINEAR
            minFilter=9987,   # LINEAR_MIPMAP_LINEAR
            wrapS=33071,      # CLAMP_TO_EDGE
            wrapT=33071,
        )],
        images=[pygltflib.Image(bufferView=3, mimeType="image/png")],
        accessors=[
            pygltflib.Accessor(
                bufferView=0, componentType=5126, count=4, type="VEC3",
                min=positions.min(axis=0).tolist(),
                max=positions.max(axis=0).tolist(),
            ),
            pygltflib.Accessor(
                bufferView=1, componentType=5126, count=4, type="VEC2",
            ),
            pygltflib.Accessor(
                bufferView=2, componentType=5123, count=6, type="SCALAR",
            ),
        ],
        bufferViews=[
            pygltflib.BufferView(buffer=0, byteOffset=off_pos,
                                 byteLength=len(positions.tobytes()), target=34962),
            pygltflib.BufferView(buffer=0, byteOffset=off_uv,
                                 byteLength=len(uvs.tobytes()), target=34962),
            pygltflib.BufferView(buffer=0, byteOffset=off_idx,
                                 byteLength=len(indices.tobytes()), target=34963),
            pygltflib.BufferView(buffer=0, byteOffset=off_png,
                                 byteLength=len(png_bytes)),
        ],
        buffers=[pygltflib.Buffer(byteLength=len(buf))],
    )
    gltf.set_binary_blob(buf)
    return b"".join(gltf.save_to_bytes())


# ──────────────────────────────────────────────────────────────────────────
# Entry-point comodo
# ──────────────────────────────────────────────────────────────────────────

def build_satellite_glb_for_takeoff(
    takeoff_lat: float,
    takeoff_lon: float,
    size_m: float = 200.0,
    zoom: int = 19,
    cache_dir: Path | None = None,
) -> tuple[bytes, float, float]:
    """Pipeline completa: scarica tile ESRI attorno al takeoff e ritorna i bytes
    di un GLB con piano texturato centrato.

    Ritorna (glb_bytes, width_m, height_m).
    """
    if cache_dir is None:
        cache_dir = Path(__file__).parent / ".tile_cache"
    image, w, h = download_satellite_patch(
        takeoff_lat, takeoff_lon, size_m, zoom, cache_dir
    )
    print(f"  Stitch finale: {image.size[0]}×{image.size[1]} px "
          f"({w:.1f}×{h:.1f} m), salvato in cache → {cache_dir}")
    glb = build_textured_plane_glb(image, w, h)
    print(f"  GLB generato: {len(glb)/1024:.1f} KB "
          f"(plane {w:.1f}m × {h:.1f}m, z={PLANE_Z_OFFSET}m)")
    return glb, w, h


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Uso: satellite_layer.py LAT LON [SIZE_M] [ZOOM]")
        sys.exit(1)
    lat = float(sys.argv[1])
    lon = float(sys.argv[2])
    size_m = float(sys.argv[3]) if len(sys.argv) > 3 else 200.0
    zoom = int(sys.argv[4]) if len(sys.argv) > 4 else 19
    glb, w, h = build_satellite_glb_for_takeoff(lat, lon, size_m, zoom)
    out = Path("/tmp/satellite_test.glb")
    out.write_bytes(glb)
    print(f"GLB scritto in {out}")
