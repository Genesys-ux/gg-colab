"""
Sutradara Animasi Dunia Dinamis 58 Detik (1.740 Frame @ 30fps) untuk Blender 4.2+ EEVEE Next:
  - Lokasi 1: Dua roda gigi kuningan gantung foreground ([CAM 01])
  - Lokasi 2: Awan ledakan bubuk kunyit & cabai 3D ([CAM 09])
  - Lokasi 4: 5 Roda gigi raksasa berputar MAJU -> MACET KLAK! -> BERPUTAR MUNDUR + uap zamrud + 12 percikan berlian ([CAM 16]-[CAM 19])
  - Lokasi 5: Trem Lisbon 28 'Remodelado' meluncur MUNDUR + 6 burung camar terbang mundur ([CAM 20]-[CAM 24])
  - Lokasi 6: Jarum jam Venesia filigree berputar mundur -> DONG! normal + 12 camar beku -> terbang + roda gigi loop + kilau Kunci Perak + Matahari Crimson!

(Karakter & Hero Props 100% identik Preview 1 dikendalikan per-frame oleh `ExactCharacterCastManager` di `characters_25d_exact.py`!)
"""

from __future__ import annotations

import math
from typing import Tuple

import bpy  # type: ignore
from mathutils import Euler, Vector  # type: ignore

from .camera_28_moves import clamp, eval_tram_z_fwd, lerp
from .config import TOTAL_FRAMES, frame_to_sec, w_to_b
from .scenes_6_locations import SceneHandles


def _set_obj_xform(obj, loc, rot_deg=None, scale=None, frame: int = 1) -> None:
    obj.location = Vector(loc)
    obj.keyframe_insert(data_path="location", frame=frame)
    if rot_deg is not None:
        obj.rotation_euler = Euler(tuple(math.radians(a) for a in rot_deg), "XYZ")
        obj.keyframe_insert(data_path="rotation_euler", frame=frame)
    if scale is not None:
        obj.scale = Vector(scale)
        obj.keyframe_insert(data_path="scale", frame=frame)


def animate_dynamic_world(handles: SceneHandles) -> None:
    """Keyframe seluruh properti & mekanisme dunia 3D dinamis melintasi 1..1740 frame."""
    scene = bpy.context.scene
    scene.frame_start = 1
    scene.frame_end = TOTAL_FRAMES

    key_frames = sorted(
        set(range(1, TOTAL_FRAMES + 1, 2))
        | {1, TOTAL_FRAMES}
        | set(range(1, 30))
        | set(range(950, 1020))
        | set(range(1545, 1590))
        | set(range(1655, 1741))
    )

    spark_seeds = [
        (0.18, 0.52, 0.30), (0.85, 0.86, 0.22), (1.42, 0.62, 0.34),
        (2.15, 0.98, 0.24), (2.78, 0.58, 0.28), (3.48, 0.92, 0.26),
        (4.02, 0.55, 0.32), (4.72, 1.04, 0.22), (5.34, 0.66, 0.28),
        (5.88, 0.88, 0.20), (1.08, 1.18, 0.20), (3.82, 1.22, 0.24),
    ]

    for fr in key_frames:
        t = frame_to_sec(fr)
        tram_z = eval_tram_z_fwd(t)

        # 1. Lokasi 1: Dua roda gigi kuningan gantung foreground
        if len(handles.fg_hanging_gears) >= 2:
            handles.fg_hanging_gears[0].rotation_euler = Euler((0.0, math.radians(t * 24.0), math.radians(8.0)), "XYZ")
            handles.fg_hanging_gears[0].keyframe_insert(data_path="rotation_euler", frame=fr)
            handles.fg_hanging_gears[1].rotation_euler = Euler((0.0, math.radians(-t * 26.0 + 15.0), math.radians(-8.0)), "XYZ")
            handles.fg_hanging_gears[1].keyframe_insert(data_path="rotation_euler", frame=fr)

        # 2. Lokasi 2: Ledakan awan bubuk kunyit & cabai ([CAM 09] 14.3..17.6s)
        for ci, puff in enumerate(handles.turmeric_puffs):
            if 14.3 <= t <= 17.6:
                exp_u = clamp((t - 14.3) / 1.4)
                fade = clamp(1.0 - max(0.0, t - 16.0) / 1.6)
                ang = ci * 0.72
                rc = (0.35 + (ci % 4) * 0.50) * (0.35 + exp_u * 1.35)
                cp_w = (0.25 + math.cos(ang) * rc, 12.80 + (ci % 3) * 0.52 + exp_u * 1.10, 16.9 + math.sin(ang) * rc)
                sc_p = max(0.01, (0.45 + exp_u * 0.95) * fade)
                _set_obj_xform(puff, w_to_b(*cp_w), scale=(sc_p, sc_p, sc_p), frame=fr)
            else:
                _set_obj_xform(puff, w_to_b(0.25, 12.0, 16.9), scale=(0.001, 0.001, 0.001), frame=fr)

        # 3. Lokasi 4: Roda gigi raksasa (MAJU -> MACET KLAK! -> BERPUTAR MUNDUR!)
        if t < 31.9:
            g_ang = (t - 26.0) * 18.0
        elif t < 32.35:
            g_ang = (31.9 - 26.0) * 18.0 + math.sin((t - 31.9) * 70.0) * 1.8
        else:
            dt_r = t - 32.35
            g_ang = (31.9 - 26.0) * 18.0 - (dt_r ** 1.45) * 68.0
        for g_obj, g_mul in handles.underground_gears:
            g_obj.rotation_euler = Euler((0.0, math.radians(g_ang * g_mul), 0.0), "XYZ")
            g_obj.keyframe_insert(data_path="rotation_euler", frame=fr)

        # 4. Lokasi 4: Uap zamrud & 12 percikan berlian organik [CAM 18]
        for ei, ep in enumerate(handles.emerald_puffs):
            ex = math.sin(ei * 1.7 + t * 0.8) * (3.2 if t < 34.0 else 1.8)
            ey_up = (-22.5 + ((ei * 1.9 + t * 2.2) % 14.0)) if t < 34.0 else (lerp(-14.0, 10.0, clamp((t - 34.0) / 4.2)) + (ei % 4 - 1.5) * 2.4)
            ez_fwd = (43.8 + (ei % 4) * 2.2) if t < 34.0 else (61.5 + math.cos(ei) * 1.6)
            _set_obj_xform(ep, w_to_b(ex, ey_up, ez_fwd), frame=fr)

        for si, sp in enumerate(handles.klak_sparks):
            if 31.8 <= t <= 33.8:
                sp_u = clamp((t - 31.8) / 1.5)
                sp_a = clamp(1.0 - sp_u)
                ang_s, rad_m, sz_s = spark_seeds[si % len(spark_seeds)]
                r_s = (0.40 + sp_u * 1.15) * rad_m
                sp_w = (math.cos(ang_s) * r_s, -17.0 + math.sin(ang_s) * r_s - sp_u * sp_u * 0.25, 43.04 - (si % 3) * 0.04)
                sc_k = max(0.01, sz_s * 3.2 * sp_a)
                _set_obj_xform(sp, w_to_b(*sp_w), rot_deg=(0.0, math.degrees(ang_s) + 90.0, 0.0), scale=(0.35 * sc_k, 0.35 * sc_k, 1.85 * sc_k), frame=fr)
            else:
                _set_obj_xform(sp, w_to_b(0.0, -17.0, 43.04), scale=(0.001, 0.001, 0.001), frame=fr)

        # 5. Lokasi 5: Trem Lisbon 28 meluncur MUNDUR + burung camar terbang mundur!
        if handles.tram_root is not None:
            _set_obj_xform(handles.tram_root, w_to_b(0.0, 9.65, tram_z), frame=fr)
        for root_g, wl, wr, gi in handles.station_seagulls:
            bx = -5.2 + (gi % 3) * 5.2 + math.sin(gi * 2.1) * 1.1
            by = 14.8 + (gi // 3) * 2.3 + math.sin(t * 2.5 + gi) * 0.4
            bz = 98.0 - max(0.0, t - 38.0) * 2.5 - gi * 3.6
            flap = math.sin(-t * 9.0 + gi) * 28.0
            _set_obj_xform(root_g, w_to_b(bx, by, bz), frame=fr)
            wl.rotation_euler = Euler((0.0, math.radians(-flap), 0.0), "XYZ")
            wl.keyframe_insert(data_path="rotation_euler", frame=fr)
            wr.rotation_euler = Euler((0.0, math.radians(flap), 0.0), "XYZ")
            wr.keyframe_insert(data_path="rotation_euler", frame=fr)

        # 6. Lokasi 6: Jarum jam Venesia filigree, camar beku -> terbang, loop gears, kilau perak & matahari crimson!
        if t < 51.8:
            min_ang = max(0.0, t - 46.0) * 115.0
            hr_ang = 35.0 + max(0.0, t - 46.0) * 16.0
        else:
            snap_m = (51.8 - 46.0) * 115.0
            snap_h = 35.0 + (51.8 - 46.0) * 16.0
            min_ang = snap_m - (t - 51.8) * 6.0
            hr_ang = snap_h - (t - 51.8) * 0.8
        if handles.clock_minute_hand:
            handles.clock_minute_hand.rotation_euler = Euler((0.0, math.radians(-min_ang), 0.0), "XYZ")
            handles.clock_minute_hand.keyframe_insert(data_path="rotation_euler", frame=fr)
        if handles.clock_hour_hand:
            handles.clock_hour_hand.rotation_euler = Euler((0.0, math.radians(-hr_ang), 0.0), "XYZ")
            handles.clock_hour_hand.keyframe_insert(data_path="rotation_euler", frame=fr)

        for root_g, wl, wr, gi in handles.harbor_seagulls:
            ang_g = gi * 0.55
            rad_g = 7.2 + (gi % 3) * 3.0
            if t < 51.8:
                fly_t = 0.0
                flap_g = 24.0 * math.sin(gi * 1.7)
            else:
                fly_t = t - 51.8
                flap_g = math.sin(fly_t * 10.0 + gi) * 32.0
            gx = math.cos(ang_g + fly_t * 0.35) * rad_g
            gy = 17.5 + (gi % 4) * 2.3 + math.sin(fly_t * 2.2 + gi) * 0.8
            gz = 111.5 - (gi % 3) * 3.2 + math.sin(ang_g + fly_t * 0.35) * 4.5
            _set_obj_xform(root_g, w_to_b(gx, gy, gz), rot_deg=(0.0, 0.0, math.degrees(ang_g + fly_t * 0.35) + 90.0), frame=fr)
            wl.rotation_euler = Euler((0.0, math.radians(-flap_g), 0.0), "XYZ")
            wl.keyframe_insert(data_path="rotation_euler", frame=fr)
            wr.rotation_euler = Euler((0.0, math.radians(flap_g), 0.0), "XYZ")
            wr.keyframe_insert(data_path="rotation_euler", frame=fr)

        if len(handles.loop_gears) >= 2:
            handles.loop_gears[0].rotation_euler = Euler((0.0, math.radians(t * 24.0), math.radians(8.0)), "XYZ")
            handles.loop_gears[0].keyframe_insert(data_path="rotation_euler", frame=fr)
            handles.loop_gears[1].rotation_euler = Euler((0.0, math.radians(-t * 26.0 + 15.0), math.radians(-8.0)), "XYZ")
            handles.loop_gears[1].keyframe_insert(data_path="rotation_euler", frame=fr)

        if handles.silver_sparkle is not None:
            if 55.4 <= t <= 56.6:
                u_s = clamp((t - 55.4) / 2.6)
                sp_w = (lerp(-0.44, 0.0, u_s) - 0.08, lerp(16.12, 12.2, u_s * u_s) + 0.14, lerp(115.48, 117.6, u_s) - 0.08)
                _set_obj_xform(handles.silver_sparkle, w_to_b(*sp_w), rot_deg=(0, t * 180.0, 0), scale=(0.35, 0.35, 1.85), frame=fr)
            else:
                _set_obj_xform(handles.silver_sparkle, w_to_b(-0.44, 16.22, 115.40), scale=(0.001, 0.001, 0.001), frame=fr)

        if handles.crimson_sun_orb is not None:
            sc_sun = 1.0 if (38.0 <= t <= 52.2) else 0.001
            _set_obj_xform(handles.crimson_sun_orb, w_to_b(-30.0, 29.0, 192.0), scale=(sc_sun, sc_sun, sc_sun), frame=fr)
