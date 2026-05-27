#!/usr/bin/env python3
"""
Converte un log ULog PX4 in MCAP, preservando tutti i topic uORB e aggiungendo
il topic /tf (foxglove.FrameTransform) calcolato da vehicle_local_position +
vehicle_attitude con conversione PX4 (FRD/NED) → Foxglove (FLU/ENU).

Output: file .mcap autoconsistente, apribile direttamente in Foxglove con
la scena 3D già pronta — nessuna extension richiesta.

Uso:  python3 ulog_to_mcap.py <input.ulg> [output.mcap]
"""

import argparse
import base64
import json
import math
import os
import sys
from pathlib import Path

import numpy as np
from mcap.writer import Writer
from pyulog import ULog


# ──────────────────────────────────────────────────────────────────────────
# Schemi
# ──────────────────────────────────────────────────────────────────────────

# Fattore di scaling visivo per gli RPM eliche: la velocità angolare reale
# viene divisa per questo valore prima di essere integrata. Serve a evitare
# l'aliasing wagon-wheel sulla scena 3D (a 5000 RPM reali un'elica gira a 83 Hz,
# ben oltre il framerate utile per la visualizzazione).
PROP_RPM_VISUAL_SCALE = 60.0

# Convenzione PX4 hexa_x per la direzione di rotazione delle eliche (vista dall'alto):
# +1 = CCW, -1 = CW. Determina il segno della velocità angolare attorno a Z+.
PROP_DIRECTION = {1: +1, 2: +1, 3: -1, 4: -1, 5: +1, 6: -1}

# Origin del joint motor_Mx → prop_Mx nell'URDF (deve corrispondere a f550.urdf)
PROP_ORIGIN_Z = 0.022

# Margini in secondi attorno alla finestra armato in modalità --auto-trim
AUTO_TRIM_PRE_BUFFER_S  = 1.0
AUTO_TRIM_POST_BUFFER_S = 0.5

# Default dell'overlay satellitare (vedi --satellite)
SATELLITE_DEFAULT_SIZE_M = 200.0
SATELLITE_DEFAULT_ZOOM   = 19
SATELLITE_PLANE_Z        = -0.05


FRAME_TRANSFORM_SCHEMA = {
    "type": "object",
    "title": "foxglove.FrameTransform",
    "properties": {
        "timestamp": {
            "type": "object",
            "properties": {
                "sec": {"type": "integer"},
                "nsec": {"type": "integer"},
            },
        },
        "parent_frame_id": {"type": "string"},
        "child_frame_id": {"type": "string"},
        "translation": {
            "type": "object",
            "properties": {
                "x": {"type": "number"},
                "y": {"type": "number"},
                "z": {"type": "number"},
            },
        },
        "rotation": {
            "type": "object",
            "properties": {
                "x": {"type": "number"},
                "y": {"type": "number"},
                "z": {"type": "number"},
                "w": {"type": "number"},
            },
        },
    },
}

# Schema per `logged_messages`: i log INFO/WARN/ERROR estratti dalla sezione
# speciale del ULog (non sono nei normali data_list). Mappato su foxglove.Log
# per essere visualizzato dal Log panel di Foxglove con livelli colorati.
LOG_SCHEMA = {
    "type": "object",
    "title": "foxglove.Log",
    "properties": {
        "timestamp": {"type": "object", "properties": {
            "sec":  {"type": "integer"},
            "nsec": {"type": "integer"},
        }},
        "level":   {"type": "integer"},
        "message": {"type": "string"},
        "name":    {"type": "string"},
    },
}

# Mapping livelli PX4 (syslog-style, 0=EMERG..7=DEBUG) → Foxglove Log levels
# (UNKNOWN=0, DEBUG=1, INFO=2, WARNING=3, ERROR=4, FATAL=5)
PX4_TO_FOXGLOVE_LEVEL = {
    0: 5, 1: 5, 2: 4, 3: 4, 4: 3, 5: 2, 6: 2, 7: 1,
}

# Schema per attitude_euler: roll/pitch/yaw misurati + setpoint, già in gradi.
# Topic derivato per plottare l'assetto senza dover convertire quaternioni in UI.
ATTITUDE_EULER_SCHEMA = {
    "type": "object",
    "title": "px4.attitude_euler_deg",
    "properties": {
        "timestamp":      {"type": "integer"},
        "roll":           {"type": "number"},
        "pitch":          {"type": "number"},
        "yaw":            {"type": "number"},
        "roll_setpoint":  {"type": "number"},
        "pitch_setpoint": {"type": "number"},
        "yaw_setpoint":   {"type": "number"},
    },
}

# Schema per flight_state: altitudine positiva-verso-l'alto (relativa al takeoff)
# + stringhe leggibili per nav_state e arming_state. Le label permettono al
# pannello State Transitions di mostrare "AUTO_MISSION" invece di "3".
FLIGHT_STATE_SCHEMA = {
    "type": "object",
    "title": "px4.flight_state",
    "properties": {
        "timestamp":               {"type": "integer"},
        "altitude_rel_takeoff_m":  {"type": "number"},
        "nav_state":               {"type": "integer"},
        "nav_state_name":          {"type": "string"},
        "nav_state_description":   {"type": "string"},
        "arming_state":            {"type": "integer"},
        "arming_state_name":       {"type": "string"},
        "arming_state_description":{"type": "string"},
    },
}

# Mappature enum PX4 → nome (da PX4-Autopilot/msg/VehicleStatus.msg).
# Tenute qui statiche per non dipendere da px4_msgs a runtime.
NAV_STATE_NAMES = {
    0:  "MANUAL",
    1:  "ALTCTL",
    2:  "POSCTL",
    3:  "AUTO_MISSION",
    4:  "AUTO_LOITER",
    5:  "AUTO_RTL",
    6:  "POSITION_SLOW",
    7:  "FREE7",
    8:  "FREE8",
    9:  "FREE9",
    10: "ACRO",
    11: "FREE11",
    12: "DESCEND",
    13: "TERMINATION",
    14: "OFFBOARD",
    15: "STAB",
    16: "FREE16",
    17: "AUTO_TAKEOFF",
    18: "AUTO_LAND",
    19: "AUTO_FOLLOW_TARGET",
    20: "AUTO_PRECLAND",
    21: "ORBIT",
    22: "AUTO_VTOL_TAKEOFF",
    23: "EXTERNAL1",
    24: "EXTERNAL2",
    25: "EXTERNAL3",
    26: "EXTERNAL4",
    27: "EXTERNAL5",
    28: "EXTERNAL6",
    29: "EXTERNAL7",
    30: "EXTERNAL8",
}

ARMING_STATE_NAMES = {
    0: "INIT",
    1: "STANDBY",
    2: "ARMED",
    3: "STANDBY_ERROR",
    4: "SHUTDOWN",
    5: "IN_AIR_RESTORE",
}

# Descrizioni brevi per ciascun nav_state — usate dal pannello Raw Messages /
# Indicator in Foxglove per spiegare il modo di volo attivo durante lo
# scrubbing. Frase compatta con parole chiave (no codici, no enum tecnici).
NAV_STATE_DESCRIPTIONS = {
    0:  "Manuale acrobatico — nessuna stabilizzazione (su multirotore ricade in STAB)",
    1:  "Altitude control — mantiene quota; stick pitch/roll = inclinazione",
    2:  "Position control — mantiene posizione e quota; stick = velocità desiderata",
    3:  "Esecuzione automatica dei waypoint del piano di volo",
    4:  "Hold automatico sul punto corrente — richiede GPS",
    5:  "Return-To-Launch — salita a quota sicura, ritorno a home, atterraggio",
    6:  "Position control lento — limiti di velocità ridotti per manovre fini",
    10: "Acrobatico — stabilizza solo i rate angolari, no autolivellamento",
    12: "Failsafe: discesa verticale controllata (perdita GPS in volo)",
    13: "Failsafe estremo: spegnimento dei motori",
    14: "Offboard — setpoint inviati via MAVLink/ROS da computer companion",
    15: "Stabilized — autolivellamento attitudine, throttle manuale",
    17: "Decollo automatico verticale fino a quota target",
    18: "Atterraggio automatico verticale sul posto (failsafe o comandato)",
    19: "Inseguimento di un bersaglio mobile",
    20: "Atterraggio di precisione su marker visivo",
    21: "Orbita attorno a un punto a raggio e velocità costanti",
    22: "Decollo VTOL — transizione verticale → orizzontale",
}

ARMING_STATE_DESCRIPTIONS = {
    0: "Boot iniziale del firmware",
    1: "Disarmato — pronto all'arming dopo pre-flight check",
    2: "Armato — motori abilitati a girare",
    3: "Disarmato con errore nei pre-flight check",
    4: "Spegnimento in corso",
    5: "Ripristino dello stato in volo dopo reboot del flight controller",
}

# Schema minimale per foxglove.SceneUpdate. Foxglove riconosce il tipo dal
# campo `title`, quindi non serve trascrivere l'intero schema ufficiale —
# basta che i campi che usiamo siano descritti per il MCAP writer.
# Il campo `data` di ModelPrimitive è bytes; in JSON-encoding viene serializzato
# come stringa base64 (Foxglove la decodifica automaticamente sul ModelPrimitive).
SCENE_UPDATE_SCHEMA = {
    "type": "object",
    "title": "foxglove.SceneUpdate",
    "properties": {
        "deletions": {"type": "array", "items": {"type": "object"}},
        "entities": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id":            {"type": "string"},
                    "timestamp":     {"type": "object", "properties": {
                        "sec":  {"type": "integer"},
                        "nsec": {"type": "integer"},
                    }},
                    "frame_id":      {"type": "string"},
                    "lifetime":      {"type": "object", "properties": {
                        "sec":  {"type": "integer"},
                        "nsec": {"type": "integer"},
                    }},
                    "frame_locked":  {"type": "boolean"},
                    "metadata":      {"type": "array", "items": {"type": "object"}},
                    "models": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "pose": {"type": "object"},
                                "scale": {"type": "object"},
                                "color": {"type": "object"},
                                "override_color": {"type": "boolean"},
                                "url":        {"type": "string"},
                                "media_type": {"type": "string"},
                                "data":       {"type": "string",
                                               "contentEncoding": "base64"},
                            },
                        },
                    },
                },
            },
        },
    },
}


PX4_TYPE_TO_JSON = {
    "float32": {"type": "number"},
    "float64": {"type": "number"},
    "int8":   {"type": "integer"},
    "int16":  {"type": "integer"},
    "int32":  {"type": "integer"},
    "int64":  {"type": "integer"},
    "uint8":  {"type": "integer"},
    "uint16": {"type": "integer"},
    "uint32": {"type": "integer"},
    "uint64": {"type": "integer"},
    "bool":   {"type": "boolean"},
    "char":   {"type": "string"},
}


# ──────────────────────────────────────────────────────────────────────────
# Quaternioni: composizione PX4 → Foxglove
# ──────────────────────────────────────────────────────────────────────────

def qmul(a, b):
    """Hamilton product (w, x, y, z)."""
    aw, ax, ay, az = a
    bw, bx, by, bz = b
    return (
        aw * bw - ax * bx - ay * by - az * bz,
        aw * bx + ax * bw + ay * bz - az * by,
        aw * by - ax * bz + ay * bw + az * bx,
        aw * bz + ax * by - ay * bx + az * bw,
    )


_S = math.sqrt(2) / 2
# 180° attorno all'asse (1,1,0)/√2 — riallinea NED→ENU
Q_NED_TO_ENU = (0.0, _S, _S, 0.0)
# 180° attorno a X — riallinea body FRD→FLU
Q_FRD_TO_FLU = (0.0, 1.0, 0.0, 0.0)


def attitude_ned_to_enu(qw, qx, qy, qz):
    """PX4 attitude quaternion (FRD body in NED world) → ROS/Foxglove (FLU in ENU)."""
    q = (qw, qx, qy, qz)
    return qmul(qmul(Q_NED_TO_ENU, q), Q_FRD_TO_FLU)


def quat_to_euler_deg(q0, q1, q2, q3):
    """Quaternione PX4 (FRD body in NED world) → roll/pitch/yaw in gradi.

    Convenzione ZYX intrinseca, identica a `plot/incidente/plot_incidente.py`,
    così i valori coincidono numericamente con quelli citati in relazione_schianto.md.
    """
    roll  = math.atan2(2 * (q0 * q1 + q2 * q3), 1 - 2 * (q1 * q1 + q2 * q2))
    pitch = math.asin(max(-1.0, min(1.0, 2 * (q0 * q2 - q3 * q1))))
    yaw   = math.atan2(2 * (q0 * q3 + q1 * q2), 1 - 2 * (q2 * q2 + q3 * q3))
    return math.degrees(roll), math.degrees(pitch), math.degrees(yaw)


# ──────────────────────────────────────────────────────────────────────────
# Helpers ulog
# ──────────────────────────────────────────────────────────────────────────

def build_topic_schema(data):
    props = {}
    for fd in data.field_data:
        base = fd.type_str.split("[")[0]
        props[fd.field_name] = PX4_TYPE_TO_JSON.get(base, {"type": "number"})
    return {"type": "object", "title": f"px4.{data.name}", "properties": props}


def sanitize(v):
    """Converti numpy scalar in python e NaN/Inf in None (JSON-safe)."""
    if hasattr(v, "item"):
        v = v.item()
    if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
        return None
    return v


def find_topic(ulog, name, multi_id=0):
    for d in ulog.data_list:
        if d.name == name and d.multi_id == multi_id:
            return d
    return None


def armed_window_s(ulog, pre=AUTO_TRIM_PRE_BUFFER_S, post=AUTO_TRIM_POST_BUFFER_S):
    """Trova [t_start, t_end] del periodo armato del drone, con buffer in secondi.

    Usa `vehicle_status.arming_state == 2` come marker di armato. Restituisce
    (None, None) se la sequenza non è disponibile (log troppo breve o privo
    di vehicle_status, es. log di test bench).
    """
    vs = find_topic(ulog, "vehicle_status")
    if vs is None or "arming_state" not in vs.data:
        return (None, None)
    arming = np.asarray(vs.data["arming_state"])
    idx_arm = np.where(arming == 2)[0]
    if len(idx_arm) == 0:
        return (None, None)
    ts = vs.data["timestamp"]
    return (int(ts[idx_arm[0]]) / 1e6 - pre, int(ts[idx_arm[-1]]) / 1e6 + post)


# ──────────────────────────────────────────────────────────────────────────
# Conversione
# ──────────────────────────────────────────────────────────────────────────

def takeoff_latlon(ulog):
    """Trova (lat, lon) al primo sample di vehicle_global_position dentro la
    finestra armata. Ritorna (None, None) se non disponibile.
    """
    vgp = find_topic(ulog, "vehicle_global_position")
    vs  = find_topic(ulog, "vehicle_status")
    if vgp is None or vs is None or "arming_state" not in vs.data:
        return (None, None, None)
    arming = np.asarray(vs.data["arming_state"])
    idx_arm = np.where(arming == 2)[0]
    if len(idx_arm) == 0:
        return (None, None, None)
    t_arm = int(vs.data["timestamp"][idx_arm[0]])
    t_gp  = np.asarray(vgp.data["timestamp"])
    j = int(np.searchsorted(t_gp, t_arm).clip(0, len(t_gp) - 1))
    return float(vgp.data["lat"][j]), float(vgp.data["lon"][j]), t_arm


def convert(ulog_path, mcap_path, t_start_s=None, t_end_s=None,
            auto_trim=False, satellite=False,
            satellite_size_m=SATELLITE_DEFAULT_SIZE_M,
            satellite_zoom=SATELLITE_DEFAULT_ZOOM):
    print(f"Loading: {ulog_path}")
    ulog = ULog(ulog_path)
    print(f"  {len(ulog.data_list)} topic, "
          f"{sum(len(d.data['timestamp']) for d in ulog.data_list)} messaggi totali")

    if auto_trim:
        arm_start, arm_end = armed_window_s(ulog)
        if arm_start is None:
            print("  ⚠ auto-trim: nessun arming_state==2 trovato → nessun trim")
        else:
            if t_start_s is None:
                t_start_s = arm_start
            if t_end_s is None:
                t_end_s = arm_end
            print(f"  ✓ auto-trim sul periodo armato "
                  f"(buffer pre={AUTO_TRIM_PRE_BUFFER_S}s, post={AUTO_TRIM_POST_BUFFER_S}s)")

    t_start_us = int(t_start_s * 1e6) if t_start_s is not None else None
    t_end_us   = int(t_end_s   * 1e6) if t_end_s   is not None else None
    if t_start_us is not None or t_end_us is not None:
        s = f"{t_start_s:.3f}" if t_start_s is not None else "−∞"
        e = f"{t_end_s:.3f}"   if t_end_s   is not None else "+∞"
        print(f"  finestra: [{s}, {e}] s")

    def in_window(t_us):
        if t_start_us is not None and t_us < t_start_us:
            return False
        if t_end_us is not None and t_us > t_end_us:
            return False
        return True

    with open(mcap_path, "wb") as f:
        writer = Writer(f)
        writer.start()

        ft_schema_id = writer.register_schema(
            name="foxglove.FrameTransform",
            encoding="jsonschema",
            data=json.dumps(FRAME_TRANSFORM_SCHEMA).encode(),
        )
        ft_channel_id = writer.register_channel(
            schema_id=ft_schema_id, topic="/tf", message_encoding="json",
        )

        log_schema_id = writer.register_schema(
            name="foxglove.Log",
            encoding="jsonschema",
            data=json.dumps(LOG_SCHEMA).encode(),
        )
        log_channel_id = writer.register_channel(
            schema_id=log_schema_id, topic="logged_messages", message_encoding="json",
        )

        euler_schema_id = writer.register_schema(
            name="px4.attitude_euler_deg",
            encoding="jsonschema",
            data=json.dumps(ATTITUDE_EULER_SCHEMA).encode(),
        )
        euler_channel_id = writer.register_channel(
            schema_id=euler_schema_id, topic="attitude_euler", message_encoding="json",
        )

        flight_state_schema_id = writer.register_schema(
            name="px4.flight_state",
            encoding="jsonschema",
            data=json.dumps(FLIGHT_STATE_SCHEMA).encode(),
        )
        flight_state_channel_id = writer.register_channel(
            schema_id=flight_state_schema_id, topic="flight_state",
            message_encoding="json",
        )

        # ── Overlay satellitare (foxglove.SceneUpdate, opzionale) ────────
        # Una sola entità "satellite_ground" emessa al primo timestamp utile,
        # con frame_locked=True così resta ancorata a local_origin per sempre.
        if satellite:
            lat0, lon0, t_arm_us = takeoff_latlon(ulog)
            if lat0 is None:
                print("  ⚠ --satellite: nessun vehicle_global_position/arming_state, overlay disabilitato")
                satellite = False
            else:
                print(f"  Takeoff GPS: lat={lat0:.7f}, lon={lon0:.7f}")
                from satellite_layer import build_satellite_glb_for_takeoff
                glb_bytes, plane_w, plane_h = build_satellite_glb_for_takeoff(
                    lat0, lon0, satellite_size_m, satellite_zoom,
                )
                scene_schema_id = writer.register_schema(
                    name="foxglove.SceneUpdate",
                    encoding="jsonschema",
                    data=json.dumps(SCENE_UPDATE_SCHEMA).encode(),
                )
                scene_channel_id = writer.register_channel(
                    schema_id=scene_schema_id,
                    topic="satellite_overlay",
                    message_encoding="json",
                )
                # Timestamp d'emissione: inizio della finestra armata se
                # disponibile, altrimenti t=0. Foxglove userà questo come
                # log_time del messaggio.
                t_emit_us = int(t_start_us if t_start_us is not None
                                else (t_arm_us if t_arm_us is not None else 0))
                t_emit_ns = t_emit_us * 1000
                glb_b64 = base64.b64encode(glb_bytes).decode("ascii")
                scene_msg = {
                    "deletions": [],
                    "entities": [{
                        "id": "satellite_ground",
                        "timestamp": {"sec": t_emit_ns // 10**9,
                                      "nsec": t_emit_ns % 10**9},
                        "frame_id": "local_origin",
                        "lifetime": {"sec": 0, "nsec": 0},
                        "frame_locked": True,
                        "metadata": [],
                        "models": [{
                            "pose": {
                                "position":    {"x": 0.0, "y": 0.0,
                                                "z": SATELLITE_PLANE_Z},
                                # -90° attorno a X: annulla la conversione
                                # glTF Y-up → world Z-up che Foxglove applica
                                # automaticamente ai ModelPrimitive. Senza
                                # questa rotazione il piano XY del GLB
                                # finisce verticale (XZ) nel mondo.
                                "orientation": {"x": -0.7071067811865475,
                                                "y": 0.0,
                                                "z": 0.0,
                                                "w":  0.7071067811865475},
                            },
                            "scale":          {"x": 1.0, "y": 1.0, "z": 1.0},
                            "color":          {"r": 1.0, "g": 1.0, "b": 1.0, "a": 1.0},
                            "override_color": False,
                            "url":            "",
                            "media_type":     "model/gltf-binary",
                            "data":           glb_b64,
                        }],
                    }],
                }
                writer.add_message(
                    channel_id=scene_channel_id,
                    log_time=t_emit_ns,
                    publish_time=t_emit_ns,
                    data=json.dumps(scene_msg).encode(),
                )
                print(f"  ✓ satellite_overlay: piano {plane_w:.1f}×{plane_h:.1f} m "
                      f"({len(glb_bytes)/1024:.0f} KB GLB embedded)")

        # Registra schema + canale per ogni topic uORB
        channels = {}
        for d in ulog.data_list:
            topic_name = d.name if d.multi_id == 0 else f"{d.name}_{d.multi_id}"
            sid = writer.register_schema(
                name=f"px4.{d.name}",
                encoding="jsonschema",
                data=json.dumps(build_topic_schema(d)).encode(),
            )
            channels[(d.name, d.multi_id)] = writer.register_channel(
                schema_id=sid, topic=topic_name, message_encoding="json",
            )

        # ── Scrivi tutti i messaggi uORB ─────────────────────────────────
        for d in ulog.data_list:
            cid = channels[(d.name, d.multi_id)]
            ts = d.data["timestamp"]
            keys = list(d.data.keys())
            n = len(ts)
            for i in range(n):
                t_us = int(ts[i])
                if not in_window(t_us):
                    continue
                msg = {k: sanitize(d.data[k][i]) for k in keys}
                t_ns = t_us * 1000
                writer.add_message(
                    channel_id=cid, log_time=t_ns, publish_time=t_ns,
                    data=json.dumps(msg).encode(),
                )

        # ── Inietta /tf da vehicle_local_position + vehicle_attitude ─────
        vlp = find_topic(ulog, "vehicle_local_position")
        va  = find_topic(ulog, "vehicle_attitude")
        if vlp is None or va is None:
            print("  ⚠ vehicle_local_position o vehicle_attitude mancante: /tf vuoto")
        else:
            t_pos = np.asarray(vlp.data["timestamp"])
            x_n = np.asarray(vlp.data["x"])  # NED north
            y_n = np.asarray(vlp.data["y"])  # NED east
            z_n = np.asarray(vlp.data["z"])  # NED down
            t_att = np.asarray(va.data["timestamp"])
            qw = np.asarray(va.data["q[0]"])
            qx = np.asarray(va.data["q[1]"])
            qy = np.asarray(va.data["q[2]"])
            qz = np.asarray(va.data["q[3]"])

            # Offset di posizione: prendi la posizione al momento dell'armo (o
            # al primo sample come fallback) e azzera lì la traiettoria.
            # Così il drone parte da (0, 0, 0) sulla griglia in Foxglove.
            t_arm = None
            vs = find_topic(ulog, "vehicle_status")
            if vs is not None and "arming_state" in vs.data:
                arming = np.asarray(vs.data["arming_state"])
                idx_arm = np.where(arming == 2)[0]  # 2 = ARMED in PX4
                if len(idx_arm) > 0:
                    t_arm = int(vs.data["timestamp"][idx_arm[0]])
            j0 = np.searchsorted(t_pos, t_arm).clip(0, len(t_pos) - 1) if t_arm else 0
            off_x = float(y_n[j0])      # NED→ENU: ENU_x = NED_y
            off_y = float(x_n[j0])      # NED→ENU: ENU_y = NED_x
            off_z = float(-z_n[j0])     # NED→ENU: ENU_z = -NED_z
            print(f"  ✓ Offset traiettoria @ armo (t={t_arm/1e6 if t_arm else 0:.2f}s): "
                  f"x={off_x:+.2f}, y={off_y:+.2f}, z={off_z:+.2f}")

            # Per ogni sample di attitude → posizione più vicina nel tempo
            idx = np.searchsorted(t_pos, t_att).clip(0, len(t_pos) - 1)

            n_tf_body = 0
            for i in range(len(t_att)):
                t_us = int(t_att[i])
                if not in_window(t_us):
                    continue
                j = int(idx[i])
                # NED → ENU + offset: drone parte da (0,0,0) all'armo
                tx = float(y_n[j]) - off_x
                ty = float(x_n[j]) - off_y
                tz = float(-z_n[j]) - off_z
                qw_e, qx_e, qy_e, qz_e = attitude_ned_to_enu(
                    float(qw[i]), float(qx[i]), float(qy[i]), float(qz[i])
                )
                t_ns = t_us * 1000
                msg = {
                    "timestamp": {"sec": t_ns // 10**9, "nsec": t_ns % 10**9},
                    "parent_frame_id": "local_origin",
                    "child_frame_id": "base_link",
                    "translation": {"x": tx, "y": ty, "z": tz},
                    "rotation":    {"x": qx_e, "y": qy_e, "z": qz_e, "w": qw_e},
                }
                writer.add_message(
                    channel_id=ft_channel_id, log_time=t_ns, publish_time=t_ns,
                    data=json.dumps(msg).encode(),
                )
                n_tf_body += 1
            print(f"  ✓ /tf: {n_tf_body} FrameTransform local_origin → base_link")

            # ── Topic derivato: attitude_euler (roll/pitch/yaw in gradi) ──
            # PX4 esprime il setpoint d'assetto come quaternione q_d[0..3],
            # quindi serve la stessa conversione del misurato.
            sp = find_topic(ulog, "vehicle_attitude_setpoint")
            if sp is not None:
                t_sp     = np.asarray(sp.data["timestamp"])
                q_d_w    = np.asarray(sp.data["q_d[0]"])
                q_d_x    = np.asarray(sp.data["q_d[1]"])
                q_d_y    = np.asarray(sp.data["q_d[2]"])
                q_d_z    = np.asarray(sp.data["q_d[3]"])
            else:
                t_sp = None

            n_euler = 0
            for i in range(len(t_att)):
                t_us = int(t_att[i])
                if not in_window(t_us):
                    continue
                r, p, y = quat_to_euler_deg(
                    float(qw[i]), float(qx[i]), float(qy[i]), float(qz[i])
                )
                if t_sp is not None:
                    j = int(np.searchsorted(t_sp, t_att[i]).clip(0, len(t_sp) - 1))
                    r_sp, p_sp, y_sp = quat_to_euler_deg(
                        float(q_d_w[j]), float(q_d_x[j]),
                        float(q_d_y[j]), float(q_d_z[j]),
                    )
                else:
                    r_sp = p_sp = y_sp = 0.0
                t_ns = t_us * 1000
                msg = {
                    "timestamp":      t_ns,
                    "roll":           r, "pitch":          p, "yaw":           y,
                    "roll_setpoint":  r_sp, "pitch_setpoint": p_sp, "yaw_setpoint":  y_sp,
                }
                writer.add_message(
                    channel_id=euler_channel_id,
                    log_time=t_ns, publish_time=t_ns,
                    data=json.dumps(msg).encode(),
                )
                n_euler += 1
            print(f"  ✓ attitude_euler: {n_euler} sample (rpy + setpoint, gradi)")

            # ── Topic derivato: flight_state ─────────────────────────────
            # Emette altitudine positiva-verso-l'alto (relativa al takeoff)
            # + nome leggibile di nav_state e arming_state. Frequenza
            # allineata a vehicle_local_position (più denso di vehicle_status,
            # quindi cattura le transizioni di stato con latenza < periodo).
            vs_for_state = find_topic(ulog, "vehicle_status")
            if vs_for_state is not None and "nav_state" in vs_for_state.data:
                t_vs       = np.asarray(vs_for_state.data["timestamp"], dtype=np.int64)
                nav_arr    = np.asarray(vs_for_state.data["nav_state"])
                arming_arr = np.asarray(vs_for_state.data["arming_state"])
            else:
                t_vs = nav_arr = arming_arr = None

            n_fs = 0
            for i in range(len(t_pos)):
                t_us = int(t_pos[i])
                if not in_window(t_us):
                    continue
                # Altitudine relativa al takeoff: NED z è positiva verso il
                # basso, off_z è già stato calcolato (con segno positivo-up)
                # come riferimento all'armo. Il risultato è (alt - alt_armo).
                altitude_rel = float(-z_n[i]) - off_z
                if t_vs is not None:
                    j = int(np.searchsorted(t_vs, t_us, side="right") - 1)
                    j = max(0, min(j, len(t_vs) - 1))
                    nav_v = int(nav_arr[j])
                    arm_v = int(arming_arr[j])
                else:
                    nav_v = arm_v = -1
                t_ns = t_us * 1000
                msg = {
                    "timestamp":               t_ns,
                    "altitude_rel_takeoff_m":  altitude_rel,
                    "nav_state":               nav_v,
                    "nav_state_name":          NAV_STATE_NAMES.get(nav_v, f"UNKNOWN_{nav_v}"),
                    "nav_state_description":   NAV_STATE_DESCRIPTIONS.get(nav_v, ""),
                    "arming_state":            arm_v,
                    "arming_state_name":       ARMING_STATE_NAMES.get(arm_v, f"UNKNOWN_{arm_v}"),
                    "arming_state_description":ARMING_STATE_DESCRIPTIONS.get(arm_v, ""),
                }
                writer.add_message(
                    channel_id=flight_state_channel_id,
                    log_time=t_ns, publish_time=t_ns,
                    data=json.dumps(msg).encode(),
                )
                n_fs += 1
            print(f"  ✓ flight_state: {n_fs} sample "
                  f"(altitudine rel. takeoff + nav_state_name + arming_state_name)")

        # ── Inietta /tf eliche da esc_status (rotazione attorno a Z+) ────
        esc = find_topic(ulog, "esc_status")
        if esc is None:
            print("  ⚠ esc_status mancante: eliche statiche")
        else:
            t_esc = np.asarray(esc.data["timestamp"], dtype=np.int64)
            rpm = np.stack([
                np.asarray(esc.data[f"esc[{k}].esc_rpm"], dtype=np.float64)
                for k in range(6)
            ])  # shape (6, N)

            # Integrazione angolo cumulativo per ciascuna elica
            angles = np.zeros_like(rpm)
            dt_s = np.diff(t_esc).astype(np.float64) / 1e6  # μs → s
            for k in range(6):
                direction = PROP_DIRECTION[k + 1]
                omega = rpm[k, :-1] * (2 * math.pi / 60) / PROP_RPM_VISUAL_SCALE * direction
                angles[k, 1:] = np.cumsum(omega * dt_s)

            n_tf_prop = 0
            for i in range(len(t_esc)):
                t_us = int(t_esc[i])
                if not in_window(t_us):
                    continue
                t_ns = t_us * 1000
                ts_obj = {"sec": t_ns // 10**9, "nsec": t_ns % 10**9}
                for k in range(6):
                    theta = float(angles[k, i])
                    qw = math.cos(theta / 2)
                    qz = math.sin(theta / 2)
                    msg = {
                        "timestamp": ts_obj,
                        "parent_frame_id": f"motor_M{k+1}",
                        "child_frame_id":  f"prop_M{k+1}",
                        "translation": {"x": 0.0, "y": 0.0, "z": PROP_ORIGIN_Z},
                        "rotation":    {"x": 0.0, "y": 0.0, "z": qz, "w": qw},
                    }
                    writer.add_message(
                        channel_id=ft_channel_id,
                        log_time=t_ns, publish_time=t_ns,
                        data=json.dumps(msg).encode(),
                    )
                    n_tf_prop += 1
            print(f"  ✓ /tf eliche: {n_tf_prop} transform motor_Mx → prop_Mx "
                  f"(scale visivo 1/{PROP_RPM_VISUAL_SCALE:.0f})")

        # ── Logged messages (INFO/WARN/ERROR di PX4) ─────────────────────
        n_log = 0
        for lm in ulog.logged_messages:
            t_us = int(lm.timestamp)
            if not in_window(t_us):
                continue
            t_ns = t_us * 1000
            msg = {
                "timestamp": {"sec": t_ns // 10**9, "nsec": t_ns % 10**9},
                "level":     PX4_TO_FOXGLOVE_LEVEL.get(lm.log_level, 2),
                "message":   lm.message,
                "name":      "PX4",
            }
            writer.add_message(
                channel_id=log_channel_id,
                log_time=t_ns, publish_time=t_ns,
                data=json.dumps(msg).encode(),
            )
            n_log += 1
        print(f"  ✓ logged_messages: {n_log} INFO/WARN/ERROR")

        writer.finish()

    size_mb = os.path.getsize(mcap_path) / 1e6
    print(f"Output: {mcap_path}  ({size_mb:.1f} MB)")


# Cartella convenzionale che contiene il singolo .ulg "corrente" su cui
# operano gli script del repo. Permette di omettere l'argomento `input`.
REPO_ROOT       = Path(__file__).resolve().parent.parent
LOG_CURRENT_DIR = REPO_ROOT / "log_current"
LOG_ARCHIVE_DIR = REPO_ROOT / "log"


def find_current_ulog() -> Path:
    """Restituisce l'unico (o il più recente) .ulg in log_current/."""
    if not LOG_CURRENT_DIR.is_dir():
        raise FileNotFoundError(
            f"Cartella {LOG_CURRENT_DIR} non esiste. Crea log_current/ e "
            f"copiaci il .ulg da convertire."
        )
    candidates = sorted(LOG_CURRENT_DIR.glob("*.ulg"))
    if not candidates:
        raise FileNotFoundError(
            f"Nessun .ulg trovato in {LOG_CURRENT_DIR}. Copia il log corrente "
            f"in questa cartella prima di eseguire lo script."
        )
    if len(candidates) > 1:
        latest = max(candidates, key=lambda p: p.stat().st_mtime)
        print(f"  ⚠ Più di un .ulg in log_current/, uso il più recente: {latest.name}")
        return latest
    return candidates[0]


def convert_one(inp: Path, out: Path, args) -> bool:
    """Esegue convert() su un singolo .ulg e ritorna True/False in base
    al successo. Usato sia per la modalità singola che per --all."""
    try:
        convert(str(inp), str(out), args.start, args.end, args.auto_trim,
                satellite=args.satellite,
                satellite_size_m=args.satellite_size,
                satellite_zoom=args.satellite_zoom)
        return True
    except Exception as e:
        print(f"  ✗ ERRORE su {inp.name}: {type(e).__name__}: {e}")
        return False


def convert_all(root: Path, args) -> int:
    """Conversione in batch: trova ricorsivamente tutti i .ulg sotto `root`
    e li converte uno per uno, scrivendo ogni .mcap accanto al .ulg sorgente.
    Ritorna 0 se tutti riusciti, 1 altrimenti."""
    if not root.is_dir():
        print(f"ERRORE: '{root}' non è una directory.", file=sys.stderr)
        return 1
    ulgs = sorted(root.rglob("*.ulg"))
    if not ulgs:
        print(f"Nessun .ulg trovato sotto {root}.")
        return 0
    print(f"╔══════════════════════════════════════════════════════════╗")
    print(f"║ Batch: {len(ulgs)} file .ulg da convertire in {root}")
    print(f"╚══════════════════════════════════════════════════════════╝")
    ok = fail = 0
    for i, ulg in enumerate(ulgs, 1):
        mcap = ulg.with_suffix(".mcap")
        rel = ulg.relative_to(root)
        print(f"\n[{i}/{len(ulgs)}] {rel}")
        if convert_one(ulg, mcap, args):
            ok += 1
        else:
            fail += 1
    summary = f"Riepilogo: {ok}/{len(ulgs)} OK" + (f", {fail} falliti" if fail else "")
    print(f"\n╔══════════════════════════════════════════════════════════╗")
    print(f"║ {summary}")
    print(f"╚══════════════════════════════════════════════════════════╝")
    return 0 if fail == 0 else 1


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument("input", nargs="?",
                    help="file .ulg di input (default: unico .ulg in log_current/)")
    ap.add_argument("output", nargs="?",
                    help="file .mcap di output (default: accanto al sorgente "
                         "se input è esplicito, altrimenti log_current/<stem>.mcap)")
    ap.add_argument("--all", nargs="?", const=str(LOG_ARCHIVE_DIR),
                    default=None, metavar="DIR",
                    help=f"modalità batch: converte ricorsivamente tutti i "
                         f".ulg trovati in DIR, scrivendo ogni .mcap accanto "
                         f"al sorgente. DIR di default: {LOG_ARCHIVE_DIR}.")
    ap.add_argument("--start", type=float, default=None, metavar="SEC",
                    help="timestamp di inizio in secondi (esclude messaggi precedenti)")
    ap.add_argument("--end", type=float, default=None, metavar="SEC",
                    help="timestamp di fine in secondi (esclude messaggi successivi)")
    ap.add_argument("--auto-trim", action="store_true",
                    help="trim automatico sul periodo armato del drone "
                         "(vehicle_status.arming_state==2 ± buffer). "
                         "Override individuale via --start/--end.")
    ap.add_argument("--satellite", action="store_true",
                    help="incorpora un piano satellitare ESRI World Imagery "
                         "centrato sul punto di takeoff (foxglove.SceneUpdate "
                         "con ModelPrimitive embedded come GLB).")
    ap.add_argument("--satellite-size", type=float,
                    default=SATELLITE_DEFAULT_SIZE_M, metavar="M",
                    help=f"lato del piano satellitare in metri "
                         f"(default {SATELLITE_DEFAULT_SIZE_M:.0f}).")
    ap.add_argument("--satellite-zoom", type=int,
                    default=SATELLITE_DEFAULT_ZOOM, metavar="Z",
                    help=f"zoom level XYZ delle tile ESRI "
                         f"(default {SATELLITE_DEFAULT_ZOOM}, max utile ~19-20).")
    args = ap.parse_args()

    if args.all is not None:
        if args.input or args.output:
            ap.error("--all è incompatibile con argomenti posizionali input/output.")
        sys.exit(convert_all(Path(args.all), args))

    if args.input:
        inp = Path(args.input)
        # Path esplicito: output di default accanto al sorgente
        default_out = inp.with_suffix(".mcap")
    else:
        inp = find_current_ulog()
        # Default log_current/: output nella stessa cartella
        default_out = LOG_CURRENT_DIR / (inp.stem + ".mcap")
    out = Path(args.output) if args.output else default_out
    sys.exit(0 if convert_one(inp, out, args) else 1)


if __name__ == "__main__":
    main()
