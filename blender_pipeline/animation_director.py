"""
Sutradara Animasi 58 Detik (1.740 Frame @ 30fps) — Menggerakkan seluruh Armature 3D TERBUKA
(Bima, Oren, Pedagang Rempah, Penumpang Trem), Hero Props (Kunci Emas & Perak), dan Dunia Dinamis!
"""

from __future__ import annotations

import math
from typing import Dict, List, Tuple

import bpy  # type: ignore
from mathutils import Euler, Vector  # type: ignore

from .camera_28_moves import (
    clamp,
    eval_golden_key_world,
    eval_tram_z_fwd,
    exp_ease_in_out,
    lerp,
    smoothstep,
)
from .config import TOTAL_FRAMES, frame_to_sec, w_to_b
from .scenes_6_locations import SceneHandles


def _set_bone_rot(arm_obj, bone_name: str, deg_xyz: Tuple[float, float, float], frame: int) -> None:
    pb = arm_obj.pose.bones.get(bone_name)
    if pb is None:
        return
    pb.rotation_euler = Euler(tuple(math.radians(a) for a in deg_xyz), "XYZ")
    pb.keyframe_insert(data_path="rotation_euler", frame=frame)


def _set_bone_loc(arm_obj, bone_name: str, loc_xyz: Tuple[float, float, float], frame: int) -> None:
    pb = arm_obj.pose.bones.get(bone_name)
    if pb is None:
        return
    pb.location = Vector(loc_xyz)
    pb.keyframe_insert(data_path="location", frame=frame)


def _set_obj_xform(obj, loc, rot_deg=None, scale=None, frame: int = 1) -> None:
    obj.location = Vector(loc)
    obj.keyframe_insert(data_path="location", frame=frame)
    if rot_deg is not None:
        obj.rotation_euler = Euler(tuple(math.radians(a) for a in rot_deg), "XYZ")
        obj.keyframe_insert(data_path="rotation_euler", frame=frame)
    if scale is not None:
        obj.scale = Vector(scale)
        obj.keyframe_insert(data_path="scale", frame=frame)


def animate_entire_short(
    bima_rig,
    oren_rig,
    golden_key,
    silver_key,
    merchants: List["bpy.types.Object"],
    passengers: List["bpy.types.Object"],
    handles: SceneHandles,
) -> None:
    """Keyframe seluruh aktor, hero props, partikel 3D, dan mesin kota melintasi 1..1740 frame."""

    # Pastikan semua frame 1..1740 ter-set di scene
    scene = bpy.context.scene
    scene.frame_start = 1
    scene.frame_end = TOTAL_FRAMES

    # Keyframe interval 2 frame (15Hz keyframe -> 30fps mulus dengan interpolasi Bezier Blender,
    # sekaligus cepat saat membangun .blend di Colab!), ditambah 1-frame presisi di momen impact/blink!
    key_frames = sorted(
        set(range(1, TOTAL_FRAMES + 1, 2))
        | {1, TOTAL_FRAMES}
        | set(range(1, 30))         # [CAM 01] dolly start
        | set(range(615, 685))      # [CAM 12]-[CAM 13] Oren paw slap
        | set(range(950, 1020))     # [CAM 18] KLAK! axle lock
        | set(range(1545, 1590))    # [CAM 25]-[CAM 26] DONG! shockwave
        | set(range(1655, 1741))    # [CAM 27]-[CAM 28] Silver Key twist & loop
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

        # ==================== 1. KUNCI EMAS (HERO PROP #1) ====================
        kp_w, k_yaw, k_roll = eval_golden_key_world(t)
        k_sc = 1.48 if (31.4 <= t <= 34.0) else (1.15 if t < 5.0 else 1.28)
        _set_obj_xform(
            golden_key,
            w_to_b(*kp_w),
            rot_deg=(k_roll * 0.4, k_roll, k_yaw),
            scale=(k_sc, k_sc, k_sc),
            frame=fr,
        )

        # ==================== 2. KUNCI PERAK (PLOT TWIST [CAM 27]-[CAM 28]!) ====================
        if t < 55.25:
            # Tersembunyi manis di dalam saku kanan robek Bima
            _set_obj_xform(silver_key, w_to_b(-0.24, 16.25, 115.80), rot_deg=(0, 0, 0), scale=(0.01, 0.01, 0.01), frame=fr)
            if handles.silver_sparkle:
                _set_obj_xform(handles.silver_sparkle, w_to_b(-0.24, 16.25, 115.80), scale=(0.001, 0.001, 0.001), frame=fr)
        else:
            u_s = clamp((t - 55.25) / 2.75)
            sp_w = (lerp(-0.40, 0.0, u_s), lerp(16.22, 12.2, u_s * u_s), lerp(115.46, 117.6, u_s))
            _set_obj_xform(
                silver_key,
                w_to_b(*sp_w),
                rot_deg=(18.0 + u_s * 160.0, 26.0 + u_s * 140.0, 18.0 + u_s * 240.0),
                scale=(1.35, 1.35, 1.35),
                frame=fr,
            )
            if handles.silver_sparkle:
                glint = 1.0 if t < 56.6 else 0.001
                _set_obj_xform(
                    handles.silver_sparkle,
                    w_to_b(sp_w[0] - 0.08, sp_w[1] + 0.14, sp_w[2] - 0.08),
                    rot_deg=(0, t * 180.0, 0),
                    scale=(0.35 * glint, 0.35 * glint, 1.85 * glint),
                    frame=fr,
                )

        # ==================== 3. BIMA (PROTAGONIS — RIG TERBUKA 2-SEGMEN + EKSPRESI!) ====================
        # Kedipan natural periodik setiap ~3.1 detik (tidak seragam!)
        blink_phase = (t % 3.1)
        blink_val = 1.0 if (2.94 < blink_phase < 3.06) else 0.0

        # Default pose tulang (reset lembut tiap fase)
        b_loc_w = (-0.08, 25.35, 1.85)
        b_rot_z = 180.0  # menghadap -Y (ke kamera di z=-3.5..0)
        b_rot_x = 0.0
        spine_p = (0.0, 0.0, 0.0)
        head_p = (0.0, 0.0, 0.0)
        uarm_l, farm_l = (0.0, 0.0, 0.0), (0.0, 0.0, 0.0)
        uarm_r, farm_r = (0.0, 0.0, 0.0), (0.0, 0.0, 0.0)
        thigh_l, shin_l = (0.0, 0.0, 0.0), (0.0, 0.0, 0.0)
        thigh_r, shin_r = (0.0, 0.0, 0.0), (0.0, 0.0, 0.0)
        brow_l, brow_r = (0.0, 0.0, 0.0), (0.0, 0.0, 0.0)
        lid_z = -0.020 * blink_val
        jaw_open = 0.0
        scarf_amp = 10.0
        jambul_bounce = math.sin(t * 7.0) * 5.0

        if t < 9.5:
            # LOKASI 1: Panik di belakang meja mencoba menyambar Kunci Emas!
            b_loc_w = (-0.08, 25.35, 1.85)
            b_rot_z = 180.0
            spine_p = (14.0, 0.0, -8.0)
            head_p = (-8.0, 0.0, 10.0)
            uarm_r, farm_r = (86.0, 0.0, -14.0), (26.0, 0.0, 0.0)
            uarm_l, farm_l = (48.0, 0.0, 22.0), (42.0, 0.0, 0.0)
            brow_l, brow_r = (0.0, -18.0, 0.0), (0.0, 18.0, 0.0)  # alis panik worried!
            jaw_open = 24.0
            lid_z = 0.012 if blink_val < 0.5 else -0.022
            scarf_amp = 12.0
            jambul_bounce = math.sin(t * 14.0) * 10.0
        elif t < 14.6:
            # LOKASI 2A: Melompat heroik di atas deretan tenda warna-warni!
            u = clamp((t - 10.8) / 3.8)
            b_loc_w = (lerp(-0.4, 0.1, u), lerp(18.0, 15.2, u) + abs(math.sin(u * math.pi * 2.0)) * 1.4, lerp(10.6, 15.4, u))
            b_rot_z = 0.0
            spine_p = (22.0, 0.0, 0.0)
            uarm_r, farm_r = (115.0, 0.0, -12.0), (18.0, 0.0, 0.0)
            uarm_l, farm_l = (-48.0, 0.0, 18.0), (35.0, 0.0, 0.0)
            thigh_r, shin_r = (58.0, 0.0, 0.0), (-64.0, 0.0, 0.0)
            thigh_l, shin_l = (-34.0, 0.0, 0.0), (-50.0, 0.0, 0.0)
            brow_l, brow_r = (0.0, 14.0, 0.0), (0.0, -14.0, 0.0)  # fokus tekad!
            jaw_open = 10.0
            scarf_amp = 32.0
        elif t < 22.6:
            # LOKASI 2B & 3A: Lari kencang menuruni tangga & gang kafe (siklus lari asimetris!)
            if t < 18.2:
                u = clamp((t - 14.6) / 3.6)
                b_loc_w = (lerp(0.1, 0.2, u), lerp(12.2, 5.1, u), lerp(16.0, 27.6, u))
            else:
                u = clamp((t - 18.2) / 4.4)
                b_loc_w = (lerp(0.2, -0.05, u), 5.02, lerp(28.5, 36.4, u))
            b_rot_z = 0.0
            cyc = math.sin(t * 15.0)
            spine_p = (20.0, cyc * 6.0, cyc * 10.0)
            uarm_r, farm_r = (cyc * 62.0, 0.0, -10.0), (54.0, 0.0, 0.0)
            uarm_l, farm_l = (-cyc * 62.0, 0.0, 10.0), (54.0, 0.0, 0.0)
            thigh_r, shin_r = (-cyc * 54.0, 0.0, 0.0), (-max(0.0, -cyc) * 68.0 - 14.0, 0.0, 0.0)
            thigh_l, shin_l = (cyc * 54.0, 0.0, 0.0), (-max(0.0, cyc) * 68.0 - 14.0, 0.0, 0.0)
            brow_l, brow_r = (0.0, 14.0, 0.0), (0.0, -14.0, 0.0)
            scarf_amp = 28.0
        elif t < 26.2:
            # LOKASI 3B ([CAM 14]): Bima MELUNCUR LUTUT di atas cobblestone basah mengejar kunci!
            u = clamp((t - 22.6) / 2.6)
            b_loc_w = (lerp(-0.05, -0.14, u), 5.02, lerp(36.4, 39.2, u))
            b_rot_z = 0.0
            b_rot_x = -26.0  # tubuh rebah meluncur atletis!
            spine_p = (24.0, 0.0, -12.0)
            uarm_r, farm_r = (118.0, 0.0, -8.0), (14.0, 0.0, 0.0)
            uarm_l, farm_l = (-42.0, 0.0, 22.0), (40.0, 0.0, 0.0)
            thigh_r, shin_r = (42.0, 0.0, 0.0), (-105.0, 0.0, 0.0)
            thigh_l, shin_l = (18.0, 0.0, 0.0), (-92.0, 0.0, 0.0)
            brow_l, brow_r = (0.0, -16.0, 0.0), (0.0, 16.0, 0.0)
            jaw_open = 22.0
            scarf_amp = 38.0
        elif t < 38.5:
            # LOKASI 4 ([CAM 19]): Bima terlempar naik di cerobong uap zamrud!
            u = clamp((t - 33.8) / 4.4)
            b_loc_w = (-0.9, lerp(-16.0, 9.8, u), lerp(50.0, 61.8, clamp(u * 1.4)))
            b_rot_z = 180.0
            b_rot_x = math.sin(u * 8.0) * 16.0
            uarm_r, farm_r = (135.0, 0.0, -25.0), (24.0, 0.0, 0.0)
            uarm_l, farm_l = (130.0, 0.0, 25.0), (24.0, 0.0, 0.0)
            thigh_r, shin_r = (25.0, 0.0, 0.0), (-45.0, 0.0, 0.0)
            thigh_l, shin_l = (-20.0, 0.0, 0.0), (-35.0, 0.0, 0.0)
            jaw_open = 28.0
            scarf_amp = 42.0
        elif t < 46.2:
            # LOKASI 5A ([CAM 21]-[CAM 23]): Lari kencang di atap trem merah yang meluncur mundur!
            u = clamp((t - 40.6) / 5.6)
            b_loc_w = (0.0, 13.38, tram_z + lerp(-4.4, 4.6, u))
            b_rot_z = 0.0
            cyc = math.sin(t * 17.0)
            spine_p = (24.0, cyc * 6.0, cyc * 12.0)
            uarm_r, farm_r = (cyc * 68.0, 0.0, -10.0), (58.0, 0.0, 0.0)
            uarm_l, farm_l = (-cyc * 68.0, 0.0, 10.0), (58.0, 0.0, 0.0)
            thigh_r, shin_r = (-cyc * 58.0, 0.0, 0.0), (-max(0.0, -cyc) * 72.0 - 14.0, 0.0, 0.0)
            thigh_l, shin_l = (cyc * 58.0, 0.0, 0.0), (-max(0.0, cyc) * 72.0 - 14.0, 0.0, 0.0)
            brow_l, brow_r = (0.0, 16.0, 0.0), (0.0, -16.0, 0.0)
            scarf_amp = 42.0
        elif t < 49.2:
            # LOKASI 5B ([CAM 24]): SLOW-MO 20% LOMPATAN HEROIK DI DEPAN MATAHARI CRIMSON!
            u = exp_ease_in_out((t - 46.2) / 2.8, 4.5)
            b_loc_w = (0.0, 14.5 + math.sin(u * math.pi) * 4.4, lerp(tram_z + 5.2, 110.5, u))
            b_rot_z = -48.0  # heroic front-3/4 profile menghadap menara jam & kamera!
            b_rot_x = lerp(12.0, -10.0, u)
            spine_p = (26.0, 0.0, -18.0)
            head_p = (-14.0, 0.0, 22.0)
            uarm_r, farm_r = (142.0, 0.0, -14.0), (14.0, 0.0, 0.0)  # tangan kanan menggapai kunci dramatis!
            uarm_l, farm_l = (-46.0, 0.0, 24.0), (36.0, 0.0, 0.0)
            thigh_r, shin_r = (64.0, 0.0, 0.0), (-56.0, 0.0, 0.0)
            thigh_l, shin_l = (-42.0, 0.0, 0.0), (-44.0, 0.0, 0.0)
            brow_l, brow_r = (0.0, 14.0, 0.0), (0.0, -14.0, 0.0)
            jaw_open = 18.0
            scarf_amp = 46.0
        else:
            # LOKASI 6 ([CAM 25]-[CAM 28]): Balkon menara jam -> putar kunci -> tersenyum lega menepuk dada!
            b_loc_w = (-0.15, 15.42, 115.85)
            if t < 52.8:
                b_rot_z = 0.0
                spine_p = (10.0, 0.0, 0.0)
                uarm_r, farm_r = (108.0, 0.0, -10.0), (22.0, 0.0, 0.0)
                uarm_l, farm_l = (32.0, 0.0, 14.0), (38.0, 0.0, 0.0)
                brow_l, brow_r = (0.0, 10.0, 0.0), (0.0, -10.0, 0.0)
                scarf_amp = 14.0
            else:
                # Berbalik ke kamera tersenyum lega (^^) sambil menepuk dada — Kunci Perak jatuh di belakangnya!
                b_rot_z = 180.0
                spine_p = (-5.0, 0.0, 4.0)
                head_p = (4.0, 6.0, -4.0)
                uarm_r, farm_r = (48.0, 0.0, 28.0), (88.0, 0.0, 32.0)  # tangan kanan menepuk dada lega!
                uarm_l, farm_l = (12.0, 0.0, -14.0), (28.0, 0.0, 0.0)
                brow_l, brow_r = (0.0, -10.0, 0.0), (0.0, 10.0, 0.0)
                lid_z = -0.022  # mata tersenyum lega ^^!
                jaw_open = 16.0
                scarf_amp = 8.0

        _set_obj_xform(bima_rig, w_to_b(*b_loc_w), rot_deg=(b_rot_x, 0.0, b_rot_z), frame=fr)
        _set_bone_rot(bima_rig, "Spine", spine_p, fr)
        _set_bone_rot(bima_rig, "Head", head_p, fr)
        _set_bone_rot(bima_rig, "Jambul", (jambul_bounce, 0.0, 0.0), fr)
        _set_bone_rot(bima_rig, "Brow_L", brow_l, fr)
        _set_bone_rot(bima_rig, "Brow_R", brow_r, fr)
        _set_bone_loc(bima_rig, "Eyelid_L", (0.0, 0.0, lid_z), fr)
        _set_bone_loc(bima_rig, "Eyelid_R", (0.0, 0.0, lid_z), fr)
        _set_bone_rot(bima_rig, "Jaw", (jaw_open, 0.0, 0.0), fr)
        _set_bone_rot(bima_rig, "UpperArm_L", uarm_l, fr)
        _set_bone_rot(bima_rig, "Forearm_L", farm_l, fr)
        _set_bone_rot(bima_rig, "UpperArm_R", uarm_r, fr)
        _set_bone_rot(bima_rig, "Forearm_R", farm_r, fr)
        _set_bone_rot(bima_rig, "Thigh_L", thigh_l, fr)
        _set_bone_rot(bima_rig, "Shin_L", shin_l, fr)
        _set_bone_rot(bima_rig, "Thigh_R", thigh_r, fr)
        _set_bone_rot(bima_rig, "Shin_R", shin_r, fr)
        # Secondary spring motion syal merah bata 3 segmen!
        _set_bone_rot(bima_rig, "Scarf_01", (scarf_amp * 0.7 + math.sin(t * 7.5) * 6.0, 0.0, math.cos(t * 5.2) * 8.0), fr)
        _set_bone_rot(bima_rig, "Scarf_02", (scarf_amp * 0.5 + math.sin(t * 7.5 - 0.8) * 10.0, 0.0, math.cos(t * 5.2 - 0.8) * 12.0), fr)
        _set_bone_rot(bima_rig, "Scarf_03", (scarf_amp * 0.3 + math.sin(t * 7.5 - 1.6) * 14.0, 0.0, math.cos(t * 5.2 - 1.6) * 14.0), fr)

        # ==================== 4. "OREN" — KUCING KAMPUNG GANG KAFE ([CAM 12]-[CAM 13]!) ====================
        _set_obj_xform(oren_rig, w_to_b(-0.82, 5.02, 36.85), rot_deg=(0.0, 0.0, -155.0), frame=fr)
        slap_u = clamp((t - 20.3) / 0.65) if t < 21.55 else (clamp(1.0 - (t - 21.55) / 0.35) if t < 22.0 else 0.0)
        slap_hit = clamp((t - 21.45) / 0.16) if 21.45 <= t <= 22.1 else 0.0
        oren_blink = -0.018 if (20.1 < t < 20.32 or 23.4 < t < 23.62) else 0.0
        _set_bone_rot(oren_rig, "Body", (0.0, -slap_u * 8.0 + slap_hit * 14.0, slap_hit * -16.0), fr)
        _set_bone_rot(oren_rig, "Head", (6.0, 0.0, -12.0 + slap_hit * 18.0), fr)
        _set_bone_loc(oren_rig, "Eyelid_L", (0.0, 0.0, oren_blink), fr)
        _set_bone_loc(oren_rig, "Eyelid_R", (0.0, 0.0, oren_blink), fr)
        # Cakar kanan terangkat memperlihatkan paw pads di [CAM 12] -> menepis kunci di [CAM 13]!
        _set_bone_rot(oren_rig, "RightPaw_Slap", (-95.0 * slap_u + 70.0 * slap_hit, 0.0, -28.0 * slap_u + 68.0 * slap_hit), fr)
        _set_bone_rot(oren_rig, "Bell", (0.0, math.sin(t * 14.0) * (18.0 * slap_u + 4.0), 0.0), fr)
        _set_bone_rot(oren_rig, "Tail_01", (0.0, 0.0, math.sin(t * 2.6) * 20.0), fr)
        _set_bone_rot(oren_rig, "Tail_02", (0.0, 0.0, math.sin(t * 2.6 - 0.7) * 24.0), fr)
        _set_bone_rot(oren_rig, "Tail_03", (0.0, 0.0, math.sin(t * 2.6 - 1.4) * 28.0), fr)

        # ==================== 5. FIGURAN PASAR (Pedagang Rempah terjungkal di [CAM 09]!) ====================
        m_specs = [
            ((-1.02, 12.0, 17.5), 155.0, -1.0),
            ((1.15, 12.0, 17.8), -150.0, 1.0),
        ]
        for mi, m_rig in enumerate(merchants[:2]):
            mpos, myaw, msgn = m_specs[mi]
            tumble = clamp((t - 14.65) / 0.55) if t >= 14.65 else 0.0
            _set_obj_xform(m_rig, w_to_b(*mpos), rot_deg=(-28.0 * tumble, msgn * 22.0 * tumble, myaw), frame=fr)
            _set_bone_rot(m_rig, "Arm_L", (110.0 * tumble, 0.0, 22.0 * tumble), fr)
            _set_bone_rot(m_rig, "Arm_R", (118.0 * tumble, 0.0, -22.0 * tumble), fr)
            # Topi jerami terangkat & miring komikal saat terkejut ledakan bubuk kunyit!
            _set_bone_loc(m_rig, "Hat", (0.0, 0.0, 0.24 * tumble), fr)
            _set_bone_rot(m_rig, "Hat", (-18.0 * tumble, msgn * 16.0 * tumble, 0.0), fr)

        # ==================== 6. FIGURAN STASIUN (Penumpang Trem mundur di [CAM 21]!) ====================
        p_specs = [
            ((-3.2, 10.05, 76.0), 80.0),
            ((3.3, 10.05, 83.5), -85.0),
            ((-3.3, 10.05, 96.5), 115.0),
            ((3.3, 10.05, 99.5), -110.0),
        ]
        for pi, p_rig in enumerate(passengers[:4]):
            ppos, pyaw = p_specs[pi]
            # Berjalan pelan mundur selama waktu terbalik (38..51.8s)!
            rev_shift = -clamp((t - 38.0) / 13.8) * 1.4 if 38.0 <= t <= 51.8 else 0.0
            _set_obj_xform(p_rig, w_to_b(ppos[0], ppos[1], ppos[2] + rev_shift), rot_deg=(0.0, 0.0, pyaw), frame=fr)
            _set_bone_rot(p_rig, "Scarf", (18.0 + math.sin(t * 10.0 + pi) * 12.0, 0.0, 0.0), fr)
            _set_bone_rot(p_rig, "Beret", (-14.0, 12.0, 0.0), fr)

        # ==================== 7. DUNIA 3D DINAMIS (RODA GIGI, TREM, JARUM JAM, CAMAR, PARTIKEL) ====================
        # a) Lokasi 1: Dua roda gigi gantung foreground
        if len(handles.fg_hanging_gears) >= 2:
            handles.fg_hanging_gears[0].rotation_euler = Euler((0.0, math.radians(t * 24.0), math.radians(8.0)), "XYZ")
            handles.fg_hanging_gears[0].keyframe_insert(data_path="rotation_euler", frame=fr)
            handles.fg_hanging_gears[1].rotation_euler = Euler((0.0, math.radians(-t * 26.0 + 15.0), math.radians(-8.0)), "XYZ")
            handles.fg_hanging_gears[1].keyframe_insert(data_path="rotation_euler", frame=fr)

        # b) Lokasi 2: Awan ledakan bubuk kunyit & cabai ([CAM 09] 14.3..17.6s)
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

        # c) Lokasi 4: Roda gigi raksasa (MAJU -> MACET KLAK! -> BERPUTAR MUNDUR!)
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

        # d) Lokasi 4: Uap zamrud & 12 percikan berlian organik [CAM 18]
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

        # e) Lokasi 5: Trem merah meluncur MUNDUR + burung camar terbang mundur!
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

        # f) Lokasi 6: Jarum jam raksasa (berputar mundur -> DONG! normal), camar beku -> terbang, & loop gears!
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

        # Piringan Matahari Crimson raksasa hanya menyala penuh di Fase 3A ([CAM 20]-[CAM 24])!
        if handles.crimson_sun_orb is not None:
            sc_sun = 1.0 if (38.0 <= t <= 52.2) else 0.001
            _set_obj_xform(handles.crimson_sun_orb, w_to_b(-34.0, 32.0, 195.0), scale=(sc_sun, sc_sun, sc_sun), frame=fr)
