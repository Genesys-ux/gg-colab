"""
Animator Properti 3D & Fisika Dunia Dinamis untuk "DETIK KE-75":
  - Pegangan kereta Maglev berayun & garis cahaya terowongan melesat cepat
  - Cincin Kawin Emas Maya berputar dalam bullet-time menuju tombol darurat pintu merah
  - Pintu Darurat Merah membuka portal badai & meledak terbuka di tengah atap Apex Tower
  - Sinar Laser Merah Kira, Kerucut Pemindai Biru Sena, & Kipas AC Industri berputar
  - Koper Baja Hitam-Emas terpental terbuka menampakkan Kue Ulang Tahun & Api Lilin tenang
  - Partikel Hujan deras turun lalu BERBALIK NAIK KE LANGIT (reverse gravity) + Serpihan Kristal Pecah!
  - Tetesan Infus ICU, Gelombang Monitor EKG -> Flatline -> BEEP!, Cincin Bergetar di nakas,
    Jarum Detik Jam Dinding menyentuh angka 15 di detik ke-75, & Ranjang ICU menghilang di pantulan akhir!
"""
from __future__ import annotations

import math
from typing import Any, Dict

from mathutils import Euler, Vector  # type: ignore

from .camera_28_moves import clamp, lerp, smoothstep
from .config import (
    CAKE_POS_W,
    ICU_BED_POS_W,
    LOC4_FLOOR_Y,
    LOC5_FLOOR_Y,
    LOC6_FLOOR_Y,
    PORTAL_DOOR_Z,
    ROOFTOP_DOOR_Z,
    frame_to_sec,
    w_to_b,
)


def update_dynamic_props_for_frame(dyn: Dict[str, Any], frame: int) -> None:
    """Update langsung seluruh properti 3D per-frame (super cepat, tanpa ribuan F-Curve berat!)."""
    t = frame_to_sec(frame)
    rfy = LOC4_FLOOR_Y
    bx, by, bz = ICU_BED_POS_W

    # 1. Pegangan kereta Maglev berayun liar & garis cahaya terowongan melesat
    if t < 16.5:
        for strap, phase in dyn.get("straps", []):
            sway = math.sin(t * 6.8 + phase) * 26.0
            strap.rotation_euler = Euler((math.radians(90.0), math.radians(sway), 0.0), "XYZ")
        for st_obj, base_z in dyn.get("tunnel_streaks", []):
            cur_z = ((base_z - t * 28.0) % 32.0) - 2.0
            st_obj.location.y = cur_z

    # 2. Cincin Emas Maya (Bullet-time melayang dari kursi Maya z=17.6 ke Raka & tombol merah z=29.5!)
    ring = dyn.get("flying_ring")
    if ring is not None:
        if 10.1 <= t <= 13.4:
            ring.hide_render = False
            u = clamp((t - 10.1) / 2.9)
            rx = lerp(1.05, 0.90 if u > 0.78 else 0.22, smoothstep(u))
            ry = lerp(1.18, 1.24, u) + math.sin(u * math.pi) * 0.34
            rz = lerp(17.6, PORTAL_DOOR_Z - 0.28, smoothstep(u))
            ring.location = Vector(w_to_b(rx, ry, rz))
            ring.rotation_euler = Euler((t * 7.0, t * 11.0, t * 5.0), "XYZ")
        else:
            ring.hide_render = True

    # 3. Pintu Merah Portal Maglev membuka langit badai (t >= 12.9s)
    dl, dr = dyn.get("portal_door_l"), dyn.get("portal_door_r")
    pglow = dyn.get("portal_glow")
    if dl is not None and dr is not None:
        open_u = smoothstep((t - 12.9) / 0.85)
        dl.location = Vector(w_to_b(-0.42 - open_u * 0.78, 1.18, PORTAL_DOOR_Z))
        dr.location = Vector(w_to_b(0.42 + open_u * 0.78, 1.18, PORTAL_DOOR_Z))
        if pglow is not None:
            pglow.hide_render = (t < 12.8 or t > 16.5)

    # 4. Pintu Merah Surealis di Atap Apex Tower meledak terbuka (t >= 28.0s)
    rdl, rdr = dyn.get("rooftop_door_l"), dyn.get("rooftop_door_r")
    if rdl is not None and rdr is not None:
        ropen = smoothstep((t - 28.0) / 0.55)
        rdl.location = Vector(w_to_b(-0.42 - ropen * 0.76, rfy + 1.17, ROOFTOP_DOOR_Z))
        rdr.location = Vector(w_to_b(0.42 + ropen * 0.76, rfy + 1.17, ROOFTOP_DOOR_Z))

    # 5. Kipas AC Industri, Papan Angin & Lampu Beacon Menara Air
    for fan in dyn.get("ac_fans", []):
        fan.rotation_euler = Euler((0.0, 0.0, t * 8.5), "XYZ")
    wsign = dyn.get("wind_sign")
    if wsign is not None:
        wsign.rotation_euler = Euler((math.radians(math.sin(t * 14.0) * 5.5), 0.0, 0.0), "XYZ")
    beacon = dyn.get("tower_beacon")
    if beacon is not None:
        beacon.hide_render = (math.sin(t * 8.0) < -0.2)

    # 6. Garis Laser Merah Kira (19.5..39.0s) & Sinar Pemindai Biru Sena (30.5..38.2s)
    laser = dyn.get("laser_beam")
    if laser is not None:
        laser.hide_render = not (19.5 <= t <= 39.0)
        if not laser.hide_render:
            jitter = math.sin(t * 19.0) * 0.04
            laser.location = Vector(w_to_b(8.2, 41.1 + jitter, 62.1))
    scone = dyn.get("scanner_cone")
    if scone is not None:
        scone.hide_render = not (31.0 <= t <= 38.2)
        if not scone.hide_render:
            scone.location = Vector(w_to_b(0.42, rfy + 1.34, 60.95))

    # 7. Koper Hitam-Emas Terpental & Terbuka + Kue Ulang Tahun Berlilin Menyala (t >= 38.4s)
    show_cake = 38.6 <= t < 46.0
    for k in ("briefcase_base", "briefcase_gold", "briefcase_lid"):
        obj = dyn.get(k)
        if obj is not None:
            obj.hide_render = not show_cake
    lid = dyn.get("briefcase_lid")
    if lid is not None and show_cake:
        lid_ang = lerp(-5.0, -82.0, smoothstep((t - 38.7) / 1.1))
        lid.rotation_euler = Euler((math.radians(lid_ang), 0.0, 0.0), "XYZ")
    for cp in dyn.get("cake_parts", []):
        cp.hide_render = not (39.0 <= t < 46.0)
    flame = dyn.get("candle_flame")
    if flame is not None and not flame.hide_render:
        fl_s = 1.55 + math.sin(t * 24.0) * 0.18
        flame.scale = Vector((0.75, 0.75, fl_s))

    # 8. Partikel Hujan: Turun Deras (16..39.8s) -> Berhenti & MELAYANG NAIK KE LANGIT (39.8..46.0s)!
    in_rooftop = 16.0 <= t < 46.0
    for rd, rx, ry_seed, rz in dyn.get("rain_drops", []):
        rd.hide_render = not in_rooftop
        if in_rooftop:
            if t < 39.8:
                ry = ((ry_seed - t * 14.0) % 8.5)
            else:
                # Reverse velocity: melayang perlahan naik ke langit!
                frozen_y = ((ry_seed - 39.8 * 14.0) % 8.5)
                ry = frozen_y + smoothstep((t - 39.8) / 1.2) * (t - 39.8) * 1.35
            rd.location = Vector(w_to_b(rx, rfy + ry, rz))

    # 9. Serpihan Kaca Kristal Putih (Gedung & Realitas Retak Pecah t=42.0..46.0s!)
    show_shards = 41.8 <= t < 46.0
    for sh, sx, sy, sz in dyn.get("shatter_shards", []):
        sh.hide_render = not show_shards
        if show_shards:
            burst = smoothstep((t - 41.8) / 3.8)
            sh.location = Vector(w_to_b(sx * (1.0 + burst * 0.45), rfy + sy + burst * 1.8, sz))
            sh.rotation_euler = Euler((t * 2.4, t * 3.1, t * 1.8), "XYZ")

    # 10. Ruang ICU 404: EKG Gelombang Merah -> Flatline (56.5..63.8s) -> BEEP! (63.8s+)
    is_flat = 56.5 <= t < 63.8
    if dyn.get("ekg_wave") is not None:
        dyn["ekg_wave"].hide_render = is_flat or (t < 46.0)
    if dyn.get("ekg_flat") is not None:
        dyn["ekg_flat"].hide_render = (not is_flat) or (t < 46.0)

    # Tetesan cairan infus jatuh perlahan
    iv_drop = dyn.get("iv_drop")
    if iv_drop is not None:
        iv_drop.hide_render = t < 46.0
        if t >= 46.0:
            drop_u = (t * 0.85) % 1.0
            iv_drop.location = Vector(w_to_b(bx - 0.85, by + 1.62 - drop_u * 0.36, bz + 0.55))

    # Cincin Emas Maya di meja nakas bergetar pelan (62.0..65.5s)
    icu_ring = dyn.get("icu_ring")
    if icu_ring is not None and 62.0 <= t <= 66.0:
        vib = math.sin(t * 48.0) * 0.012
        icu_ring.location = Vector(w_to_b(bx - 1.01 + vib, by + 0.75 + abs(vib) * 0.6, bz - 0.27))

    # Jam dinding analog: tepat di t=75.0s jarum detik menyentuh angka 15 (90 derajat searah jarum jam!)
    csec = dyn.get("clock_sec")
    if csec is not None:
        sec_hand_deg = -((t % 60.0) / 60.0) * 360.0  # t=75.0 -> 15s -> -90 deg (angka 3 / detik 15!)
        csec.rotation_euler = Euler((0.0, math.radians(sec_hand_deg), 0.0), "XYZ")

    # Twist Akhir (t >= 68.4s): Ranjang ICU tampak kosong & Raka Muda membawa koper emas di Koridor!
    cor_case = dyn.get("corridor_briefcase")
    if cor_case is not None:
        cor_case.hide_render = t < 66.8
        if t >= 66.8:
            u_w = clamp((t - 69.2) / 5.2)
            cz = lerp(111.6, 117.8, smoothstep(u_w))
            cor_case.location = Vector(w_to_b(5.82, LOC6_FLOOR_Y + 0.72, cz))
