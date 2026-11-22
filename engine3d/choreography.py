"""
Koreografi Lengkap 58 Detik (1.740 Frame @ 30fps):
  - 6 Lokasi Terpadu
  - 28 Gerakan Kamera Virtual Continuous One-Take ([CAM 01] – [CAM 28])
  - 1 Hidden Wipe Cut (2 frame hitam di jeruji selokan [CAM 15])
  - 1 Seamless Loop ([CAM 28] menyambung mulus ke [CAM 01])
  - Menggerakkan seluruh karakter melalui RIGGING TERBUKA (HumanoidRig, OrenRig, KeyPropRig)!
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import List, Tuple

import numpy as np

from characters import HumanoidRig, KeyPropRig, OrenRig

from .lighting import LightingState, evaluate_lighting
from .math3d import (
    camera_relative_yaw_deg,
    clamp,
    exp_ease_in_out,
    lerp,
    lerp_vec,
    smoothstep,
    snappy_dolly_overshoot,
    vec3,
    whip_curve,
)
from .renderer_wgpu import BillboardDraw
from .sprite_cache import SpriteCache


@dataclass
class ShotCamera:
    cam_id: str
    location_label: str
    cam_pos: np.ndarray
    cam_target: np.ndarray
    focal_mm: float
    roll_deg: float
    motion_blur_uv: Tuple[float, float]
    shadow_center: np.ndarray
    shadow_radius: float
    outline_strength: float = 0.85


def _eval_golden_key_pos(t: float) -> Tuple[np.ndarray, float, float]:
    """Posisi 3D Kunci Emas + yaw & roll pada detik t (0..58)."""
    if t < 2.2:
        # Terpeleset dari jari Bima di loteng
        u = clamp(t / 2.2)
        p = vec3(lerp(0.18, 0.22, u), lerp(27.28, 27.08, u * u), lerp(0.55, 0.72, u))
        return p, t * 45.0, -24.0 + u * 18.0
    if t < 4.2:
        # Slow-motion melayang di udara ([CAM 02])
        u = (t - 2.2) / 2.0
        p = vec3(0.24 + u * 0.08, 27.08 - u * 0.24, 0.72 + u * 0.28)
        return p, 99.0 + u * 75.0, -6.0 + u * 45.0
    if t < 5.8:
        # Jatuh & memantul dari pinggir cangkir teh porselen ([CAM 03])
        u = (t - 4.2) / 1.6
        if u < 0.45:
            v = u / 0.45
            p = vec3(lerp(0.32, 0.55, v), lerp(26.84, 26.35, v * v), lerp(1.0, 1.55, v))
        else:
            v = (u - 0.45) / 0.55
            arc = math.sin(v * math.pi) * 0.48
            p = vec3(lerp(0.55, 0.28, v), lerp(26.35, 26.20, v) + arc, lerp(1.55, 2.10, v))
        return p, t * 240.0, t * 180.0
    if t < 7.4:
        # Menggelinding cepat di atas meja kayu oak ([CAM 04])
        u = (t - 5.8) / 1.6
        p = vec3(lerp(0.28, 0.05, u), 26.22 + abs(math.sin(u * math.pi * 4)) * 0.05, lerp(2.10, 3.65, u))
        return p, t * 320.0, t * 280.0
    if t < 9.0:
        # Terpental ke ambang jendela & jatuh keluar menuju kota ([CAM 05])
        u = (t - 7.4) / 1.6
        arc = math.sin(u * math.pi) * 0.65
        p = vec3(lerp(0.05, 0.0, u), lerp(26.22, 24.4, u * u) + arc, lerp(3.65, 6.8, u))
        return p, t * 380.0, t * 340.0
    if t < 11.0:
        # Terjun bebas ke arah tenda merah pasar ([CAM 06])
        u = (t - 9.0) / 2.0
        p = vec3(math.sin(u * 3.0) * 0.15, lerp(24.4, 17.7, u * u), lerp(6.8, 10.8, u))
        return p, t * 420.0, t * 360.0
    if t < 12.8:
        # Menghantam kanopi kain merah & melenting tinggi ([CAM 07])
        u = (t - 11.0) / 1.8
        arc = math.sin(u * math.pi) * 3.2
        p = vec3(lerp(0.0, 0.2, u), lerp(17.7, 15.8, u) + arc, lerp(10.8, 14.2, u))
        return p, t * 340.0, t * 220.0
    if t < 14.6:
        # Meluncur di atas deretan tenda menuju karung kunyit ([CAM 08])
        u = (t - 12.8) / 1.8
        p = vec3(lerp(0.2, 0.25, u), lerp(15.8, 13.0, u), lerp(14.2, 16.9, u))
        return p, t * 420.0, t * 300.0
    if t < 16.2:
        # Menghantam karung kunyit & terpental ke rel tangga ([CAM 09])
        u = (t - 14.6) / 1.6
        arc = math.sin(u * math.pi) * 0.9
        p = vec3(lerp(0.25, 1.85, u), lerp(13.0, 11.4, u) + arc, lerp(16.9, 19.8, u))
        return p, t * 460.0, t * 340.0
    if t < 18.0:
        # Meluncur cepat di rel kayu samping tangga pasar ([CAM 10])
        u = (t - 16.2) / 1.8
        p = vec3(lerp(1.85, 0.85, u), lerp(11.4, 5.45, u), lerp(19.8, 28.0, u))
        return p, t * 390.0, t * 290.0
    if t < 21.6:
        # Meluncur rendah menyusuri gang kafe ([CAM 11]-[CAM 12])
        u = (t - 18.0) / 3.6
        p = vec3(lerp(0.85, -0.75, u), 5.35 + abs(math.sin(u * math.pi * 3)) * 0.32, lerp(28.0, 36.8, u))
        return p, t * 360.0, t * 260.0
    if t < 25.0:
        # Ditepis cakar Oren seperti peluru lurus menuju jeruji besi ([CAM 13]-[CAM 14])
        u = (t - 21.6) / 3.4
        arc = math.sin(u * math.pi) * 0.85
        p = vec3(lerp(-0.75, 0.0, u), lerp(5.75, 5.18, u) + arc, lerp(36.8, 42.5, u))
        return p, t * 680.0, t * 520.0
    if t < 26.0:
        # Jatuh menembus celah jeruji selokan ([CAM 15])
        u = (t - 25.0) / 1.0
        p = vec3(0.0, lerp(5.18, 2.2, u * u), 42.5)
        return p, t * 520.0, 0.0
    if t < 31.9:
        # Jatuh memantul di antara dua roda gigi raksasa menuju soket poros utama ([CAM 16]-[CAM 18])
        u = (t - 26.0) / 5.9
        bounce = abs(math.sin(u * math.pi * 2.5)) * 1.4 * (1.0 - u)
        p = vec3(math.sin(u * math.pi * 3.0) * 1.1 * (1.0 - u), lerp(-8.5, -17.0, u) + bounce, lerp(41.8, 42.96, u))
        return p, t * 360.0, t * 220.0
    if t < 34.0:
        # MENANCAP di poros mesin — KLAK! ([CAM 18], tepat di bibir soket z=42.96 agar tidak tertelan silinder z=43.125!)
        p = vec3(0.0, -17.0, 42.96)
        rot_rev = 0.0 if t < 32.35 else -(t - 32.35) * 320.0
        return p, 0.0, rot_rev
    if t < 38.2:
        # Disemburkan uap zamrud melesat naik lewat cerobong ventilasi ([CAM 19])
        u = (t - 34.0) / 4.2
        ang = u * math.pi * 3.0
        r = lerp(1.6, 0.4, u)
        p = vec3(math.cos(ang) * r, lerp(-15.0, 12.0, u), lerp(52.0, 62.0, min(1.0, u * 1.4)))
        return p, t * 480.0, t * 320.0
    if t < 49.0:
        # Terlempar tinggi dari cerobong melesat di langit crimson menuju menara jam ([CAM 20]-[CAM 24])
        u = (t - 38.2) / 10.8
        arc = math.sin(u * math.pi) * 9.5
        p = vec3(lerp(0.2, 0.0, u), lerp(12.5, 19.5, u) + arc, lerp(64.0, 115.2, u))
        return p, t * 320.0, t * 180.0
    if t < 51.8:
        # Bima meraih & memasukkan kunci ke lubang pusat jam ([CAM 25])
        u = (t - 49.0) / 2.8
        p = vec3(lerp(0.35, 0.0, smoothstep(u)), lerp(19.2, 19.5, smoothstep(u)), lerp(115.6, 117.15, smoothstep(u)))
        return p, lerp(45.0, 0.0, smoothstep(u)), lerp(-35.0, 0.0, smoothstep(u))
    # Terkunci manis di pusat jarum jam! ([CAM 26]-[CAM 28])
    return vec3(0.0, 19.5, 117.15), 0.0, 90.0


def evaluate_camera(t: float, tram_z: float) -> ShotCamera:
    """Evaluasi posisi, target, focal length (18-22mm), Dutch/barrel roll & directional motion blur untuk 28 gerakan kamera."""
    key_p, _, _ = _eval_golden_key_pos(t)

    # ==================== LOKASI 1: BENGKEL JAM LOTENG (00:00 - 00:09) ====================
    if t < 2.2:
        # [CAM 01] Snappy Speed-Ramped Dolly-In menembus celah 2 roda gigi gantung -> berhenti overshoot 5cm depan kunci!
        u = snappy_dolly_overshoot(t / 2.2, overshoot=0.055)
        eye = lerp_vec(vec3(0.0, 27.20, -3.55), vec3(0.08, 27.06, -0.35), u)
        tgt = lerp_vec(vec3(0.10, 27.05, 0.95), vec3(0.10, 26.95, 1.05), clamp(u))
        speed_peak = math.exp(-((t / 2.2 - 0.28) * 4.5) ** 2)
        return ShotCamera("CAM 01", "Lokasi 1: Bengkel Jam Loteng", eye, tgt, lerp(18.0, 21.0, clamp(u)), -3.5 * clamp(u), (0.0, speed_peak * 0.007), vec3(0, 26.5, 1.5), 9.0, 0.72)

    if t < 4.2:
        # [CAM 02] Micro Dutch-Tilt Orbit (120°) melingkari kunci slow-mo memperlihatkan Bima panik di background!
        u = exp_ease_in_out((t - 2.2) / 2.0, 5.5)
        ang = math.radians(lerp(-12.0, 108.0, u))
        r = lerp(0.82, 1.25, u)
        eye = key_p + vec3(math.sin(ang) * r, lerp(0.05, 0.16, u), -math.cos(ang) * r)
        tgt = lerp_vec(key_p, vec3(-0.15, 26.95, 1.85), 0.25 * u)
        return ShotCamera("CAM 02", "Lokasi 1: Bengkel Jam Loteng", eye, tgt, 20.0, lerp(-8.0, 13.0, u), (0.008 * math.sin(u * math.pi), 0.0), vec3(0, 26.5, 1.5), 9.0, 0.78)

    if t < 5.8:
        # [CAM 03] Fast Crane Drop mengikuti kunci memantul dari pinggir cangkir teh porselen!
        u = exp_ease_in_out((t - 4.2) / 1.6, 5.5)
        eye = lerp_vec(vec3(1.15, 27.38, 0.45), vec3(1.22, 26.58, 0.92), u)
        tgt = lerp_vec(key_p, vec3(0.25, 26.42, 1.65), 0.35)
        mb = math.sin(u * math.pi) * 0.009
        return ShotCamera("CAM 03", "Lokasi 1: Bengkel Jam Loteng", eye, tgt, 19.0, lerp(8.0, -5.0, u), (0.0, mb), vec3(0, 26.5, 1.8), 9.0, 0.80)

    if t < 7.4:
        # [CAM 04] Low-Angle Tracking Slide sejajar permukaan meja kayu melewati obeng & kaca pembesar!
        u = smoothstep((t - 5.8) / 1.6)
        eye = vec3(lerp(0.95, 0.65, u), 26.26, lerp(1.55, 3.05, u))
        tgt = key_p + vec3(-0.15, 0.08, 0.45)
        return ShotCamera("CAM 04", "Lokasi 1: Bengkel Jam Loteng", eye, tgt, 18.0, -3.5, (0.012, 0.0), vec3(0, 26.5, 2.2), 10.0, 0.82)

    if t < 9.0:
        # [CAM 05] Whip-Pan & Dive Through Window menembus bingkai jendela kayu cat mengelupas keluar menuju kota!
        u = whip_curve((t - 7.4) / 1.6)
        eye = lerp_vec(vec3(0.65, 26.35, 3.05), vec3(0.15, 25.4, 6.4), u)
        tgt = lerp_vec(key_p, vec3(0.0, 21.0, 11.2), u)
        mb = math.sin(u * math.pi) * 0.042
        return ShotCamera("CAM 05", "Lokasi 1 → 2: Terjun Keluar Jendela", eye, tgt, 18.0, lerp(-4.0, 12.0, u), (mb * 0.7, mb * 0.5), vec3(0, 22.0, 7.5), 16.0, 0.85)

    # ==================== LOKASI 2: PASAR REMPAH & BUAH BERTINGKAT (00:09 - 00:18) ====================
    if t < 11.0:
        # [CAM 06] High-Speed Vertical Plunge paralel di samping kunci, balkon rumah melesat ke atas!
        u = (t - 9.0) / 2.0
        eye = key_p + vec3(1.85, 1.35, -1.75)
        tgt = key_p + vec3(-0.2, -1.2, 1.2)
        return ShotCamera("CAM 06", "Lokasi 2: Pasar Rempah Bertingkat", eye, tgt, 18.0, lerp(12.0, -8.0, u), (0.0, 0.036), vec3(0, 19.0, 10.5), 22.0, 0.86)

    if t < 12.8:
        # [CAM 07] Elastic Bounce Pull-Back — kunci memantul dari kanopi kain merah dengan overshoot halus di puncak!
        u = snappy_dolly_overshoot((t - 11.0) / 1.8, overshoot=0.05)
        eye = key_p + vec3(lerp(1.9, 2.8, clamp(u)), lerp(0.2, 1.6, clamp(u)), lerp(-1.8, -3.2, clamp(u)))
        tgt = key_p + vec3(0.0, -0.35, 0.5)
        return ShotCamera("CAM 07", "Lokasi 2: Pasar Rempah Bertingkat", eye, tgt, 19.5, lerp(-8.0, 4.0, clamp(u)), (0.0, -0.022 * (1.0 - clamp(u))), vec3(0, 16.0, 12.5), 22.0, 0.85)

    if t < 14.6:
        # [CAM 08] Speed-Ramped Chase Roll (360° BARREL ROLL!) mendahului Bima melompat di atas deretan tenda!
        u = exp_ease_in_out((t - 12.8) / 1.8, 5.0)
        bima_pos = vec3(lerp(-0.4, 0.2, u), lerp(18.0, 15.6, u) + math.sin(u * math.pi) * 1.4, lerp(11.2, 15.2, u))
        eye = bima_pos + vec3(lerp(2.4, 1.6, u), 1.45, lerp(2.8, 3.2, u))
        tgt = lerp_vec(bima_pos + vec3(0, 0.6, 0), key_p, 0.35)
        barrel_roll = u * 360.0
        return ShotCamera("CAM 08", "Lokasi 2: Pasar Rempah (360° Barrel Roll)", eye, tgt, 18.0, barrel_roll, (0.028 * math.sin(u * math.pi), 0.012), vec3(0, 14.5, 14.5), 22.0, 0.85)

    if t < 16.2:
        # [CAM 09] Crash Dolly-Through Particle Cloud — menerobos langsung awan bubuk kunyit kuning cerah + pedagang!
        u = (t - 14.6) / 1.6
        eye = lerp_vec(vec3(0.28, 14.35, 13.7), vec3(0.20, 13.15, 16.4), u)
        tgt = vec3(0.05, 12.90, 17.2)
        return ShotCamera("CAM 09", "Lokasi 2: Ledakan Bubuk Kunyit", eye, tgt, 18.0, lerp(-5.0, 6.0, u), (0.008, 0.010), vec3(0, 12.5, 16.8), 18.0, 0.84)

    if t < 18.0:
        # [CAM 10] Whip-Tilt Down Stairs menyalip peti jeruk yang tumpah di foreground!
        u = exp_ease_in_out((t - 16.2) / 1.8, 5.5)
        eye = lerp_vec(vec3(0.6, 12.8, 18.5), vec3(0.2, 6.2, 26.8), u)
        tgt = key_p + vec3(-0.3, -0.4, 1.4)
        return ShotCamera("CAM 10", "Lokasi 2 → 3: Tangga Pasar", eye, tgt, 18.0, lerp(7.0, -5.0, u), (0.018, 0.030 * math.sin(u * math.pi)), vec3(0, 8.5, 24.0), 18.0, 0.85)

    # ==================== LOKASI 3: GANG KAFE & JEMURAN SEMPIT (00:18 - 00:26) ====================
    if t < 19.8:
        # [CAM 11] Tight Corridor Swoop rendah melewati kolong meja kafe & kaki kursi besi!
        u = smoothstep((t - 18.0) / 1.8)
        eye = vec3(lerp(-1.4, -0.8, u), 5.42, lerp(28.2, 34.4, u))
        tgt = vec3(lerp(0.5, -0.4, u), 5.75, lerp(33.5, 38.0, u))
        return ShotCamera("CAM 11", "Lokasi 3: Gang Kafe Sempit", eye, tgt, 18.0, -5.0 + u * 8.0, (0.014, 0.0), vec3(0, 6.0, 34.0), 18.0, 0.86)

    if t < 21.4:
        # [CAM 12] Whip-Pan Snap to Cat — mengunci Oren & cakar lebarnya dengan subtle overshoot!
        u = snappy_dolly_overshoot((t - 19.8) / 1.6, overshoot=0.05)
        eye = lerp_vec(vec3(-0.8, 5.45, 34.4), vec3(-0.08, 5.90, 35.10), u)
        tgt = lerp_vec(vec3(-0.4, 5.75, 38.0), vec3(-0.84, 5.74, 36.85), clamp(u))
        whip = math.exp(-((t - 20.1) * 5.0) ** 2) * 0.045
        return ShotCamera("CAM 12", 'Lokasi 3: Gang Kafe ("Oren" Snap!)', eye, tgt, 21.0, lerp(3.0, -6.0, clamp(u)), (-whip, 0.0), vec3(-0.5, 6.0, 36.8), 14.0, 0.80)

    if t < 23.0:
        # [CAM 13] Speed-Ramped Arc Around Impact saat cakar Oren menepis Kunci Emas!
        u = exp_ease_in_out((t - 21.4) / 1.6, 5.5)
        ang = math.radians(lerp(35.0, -62.0, u))
        pivot = vec3(-0.65, 5.75, 37.3)
        eye = pivot + vec3(math.sin(ang) * 2.2, 0.45, -math.cos(ang) * 2.2)
        tgt = lerp_vec(pivot, key_p, clamp(u * 1.1))
        return ShotCamera("CAM 13", "Lokasi 3: Tepisan Oren!", eye, tgt, 19.0, lerp(-6.0, 12.0, u), (0.026 * math.sin(u * math.pi), 0.0), vec3(0, 6.0, 38.0), 14.0, 0.84)

    if t < 24.6:
        # [CAM 14] Inverted Low-Skim Track mendekati cobblestone basah menangkap Bima meluncur lutut mengejar kunci!
        u = smoothstep((t - 23.0) / 1.6)
        eye = vec3(lerp(0.62, 0.48, u), 5.45, lerp(40.9, 41.8, u))
        tgt = vec3(lerp(-0.14, -0.06, u), 5.58, lerp(37.4, 38.6, u))
        return ShotCamera("CAM 14", "Lokasi 3: Inverted Cobblestone Skim", eye, tgt, 18.0, lerp(164.0, 170.0, u), (0.008, 0.004), vec3(0, 6.0, 39.5), 15.0, 0.85)

    if t < 26.0:
        # [CAM 15] Vertical Dive into Grate (Hidden Wipe Cut 2 frame hitam di t=26.0!)
        u = exp_ease_in_out((t - 24.6) / 1.4, 7.0)
        eye = lerp_vec(vec3(0.35, 6.95, 42.15), vec3(0.0, 4.95, 42.5), u)
        tgt = vec3(0.0, lerp(5.05, 1.5, u), 42.52)
        return ShotCamera("CAM 15", "Lokasi 3 → 4: Menembus Jeruji (Hidden Wipe)", eye, tgt, 18.0, lerp(140.0, 0.0, u), (0.0, 0.048 * u), vec3(0, 5.2, 42.5), 12.0, 0.82)

    # ==================== LOKASI 4: GORONG-GORONG MESIN JAM — STORY TURN! (00:26 - 00:38) ====================
    if t < 28.8:
        # [CAM 16] Explosive Pull-Out Reveal menyingkap skala raksasa mesin & lighting Indigo-Emerald!
        u = exp_ease_in_out((t - 26.0) / 2.8, 6.5)
        eye = lerp_vec(vec3(0.0, -9.2, 42.2), vec3(0.8, -14.8, 34.4), u)
        tgt = lerp_vec(vec3(0.0, -14.5, 44.5), vec3(0.0, -16.8, 46.5), u)
        return ShotCamera("CAM 16", "Lokasi 4: Gorong-Gorong Mesin (STORY TURN!)", eye, tgt, lerp(18.0, 20.0, u), lerp(0.0, -6.0, u), (0.0, -0.025 * math.sin(u * math.pi)), vec3(0, -16.0, 45.0), 22.0, 0.86)

    if t < 31.4:
        # [CAM 17] Pendulum Swing Track mengayun seperti bandul antara dua roda gigi raksasa!
        u = (t - 28.8) / 2.6
        swing = math.sin(u * math.pi * 1.35) * 4.2
        eye = vec3(swing, lerp(-14.2, -16.2, u) + abs(swing) * 0.25, lerp(36.0, 39.2, u))
        tgt = key_p
        return ShotCamera("CAM 17", "Lokasi 4: Gorong-Gorong Mesin", eye, tgt, 19.0, -swing * 2.5, (math.cos(u * math.pi * 1.35) * 0.018, 0.0), vec3(0, -16.5, 45.0), 22.0, 0.85)

    if t < 34.0:
        # [CAM 18] Snappy Crash-Zoom In + Shockwave Shake — KLAK! Kunci menancap di poros mesin!
        u = snappy_dolly_overshoot((t - 31.4) / 1.2, overshoot=0.06)
        shake = math.exp(-max(0.0, t - 31.9) * 4.5) * 0.12 if t >= 31.9 else 0.0
        sh_x = math.sin(t * 75.0) * shake
        sh_y = math.cos(t * 92.0) * shake
        eye = lerp_vec(vec3(1.8, -15.8, 38.0), vec3(0.42, -16.75, 40.85), clamp(u)) + vec3(sh_x, sh_y, 0.0)
        tgt = vec3(0.0, -17.0, 43.4) + vec3(sh_x * 0.4, sh_y * 0.4, 0.0)
        return ShotCamera("CAM 18", "Lokasi 4: KLAK! Poros Jantung Kota!", eye, tgt, 21.0, sh_x * 20.0, (0.0, 0.015 * (1.0 - clamp(u))), vec3(0, -17.0, 44.0), 18.0, 0.74)

    if t < 38.0:
        # [CAM 19] Reverse Spiral Ascent — melesat naik secara spiral di cerobong ventilasi penuh uap zamrud!
        u = (t - 34.0) / 4.0
        ang = u * math.pi * 2.6
        r = lerp(2.8, 1.9, u)
        y_cam = lerp(-15.5, 9.2, exp_ease_in_out(u, 4.0))
        z_center = lerp(49.0, 62.0, clamp(u * 1.35))
        eye = vec3(math.cos(ang) * r, y_cam, z_center + math.sin(ang) * r)
        tgt = vec3(0.0, y_cam + 3.8, z_center)
        return ShotCamera("CAM 19", "Lokasi 4 → 5: Cerobong Uap Zamrud", eye, tgt, 18.0, math.sin(ang) * 18.0, (0.016, 0.034), vec3(0, y_cam + 2.0, z_center), 18.0, 0.84)

    # ==================== LOKASI 5: STASIUN TREM LAYANG TERBUKA (00:38 - 00:49) ====================
    if t < 39.8:
        # [CAM 20] Burst-Out Horizon Leveling — menjebol keluar kisi ventilasi peron menuju langit crimson!
        u = snappy_dolly_overshoot((t - 38.0) / 1.8, overshoot=0.04)
        eye = lerp_vec(vec3(0.0, 9.8, 62.0), vec3(-2.6, 12.2, 66.5), clamp(u))
        tgt = lerp_vec(vec3(0.0, 12.5, 78.0), vec3(0.4, 12.4, 92.0), clamp(u))
        return ShotCamera("CAM 20", "Lokasi 5: Stasiun Trem (CLIMAX SHIFT!)", eye, tgt, 18.5, lerp(28.0, 0.0, clamp(u)), (0.0, 0.026 * (1.0 - clamp(u))), vec3(0, 12.0, 82.0), 28.0, 0.85)

    if t < 42.2:
        # [CAM 21] High-Speed Lateral Tracking (Parallax Wall) sejajar trem merah melesat mundur melewati pilar besi!
        u = (t - 39.8) / 2.4
        z_track = lerp(tram_z + 1.5, tram_z - 5.2, u)
        eye = vec3(-6.8, 12.65, z_track)
        tgt = vec3(0.4, 12.25, tram_z + 0.6)
        return ShotCamera("CAM 21", "Lokasi 5: Stasiun Trem (Parallax Wall)", eye, tgt, 18.0, -3.5, (0.014, 0.0), vec3(0, 12.0, tram_z), 28.0, 0.86)

    if t < 43.8:
        # [CAM 22] Whip-Pan Up to Flying Key — mengunci kilauan Kunci Emas di langit crimson!
        u = whip_curve((t - 42.2) / 1.6)
        eye = vec3(-3.2, 12.8, tram_z - 1.5)
        tgt = lerp_vec(vec3(0.2, 12.2, tram_z), key_p, u)
        return ShotCamera("CAM 22", "Lokasi 5: Whip-Pan ke Kunci Terbang", eye, tgt, 20.0, lerp(-3.5, 6.0, u), (0.015, -0.042 * math.sin(u * math.pi)), vec3(0, 14.0, tram_z + 8.0), 28.0, 0.85)

    if t < 46.2:
        # [CAM 23] Dynamic Rooftop Dolly-Forward tepat di depan Bima yang berlari di atap trem berlawanan laju trem!
        u = (t - 43.8) / 2.4
        bima_z = tram_z + lerp(-3.8, 4.4, u)
        eye = vec3(lerp(-0.9, 0.7, u), 14.45, bima_z + 3.2)
        tgt = vec3(0.0, 14.55, bima_z - 0.5)
        return ShotCamera("CAM 23", "Lokasi 5: Lari di Atap Trem!", eye, tgt, 18.5, lerp(6.0, -6.0, u), (0.012, 0.008), vec3(0, 13.5, bima_z), 24.0, 0.84)

    if t < 49.0:
        # [CAM 24] Slow-Mo Apex Leap Arc (20% slow-mo) mengorbit 90° mengelilingi siluet Bima di depan matahari crimson raksasa!
        u = exp_ease_in_out((t - 46.2) / 2.8, 4.5)
        bima_leap = vec3(0.0, 15.2 + math.sin(u * math.pi) * 4.2, lerp(tram_z + 5.2, 110.5, u))
        ang = math.radians(lerp(-15.0, 48.0, u))
        eye = bima_leap + vec3(math.sin(ang) * 4.6, lerp(-1.4, -0.5, u), -math.cos(ang) * 4.6)
        tgt = bima_leap + vec3(-0.95, 0.85, 2.2)
        return ShotCamera("CAM 24", "Lokasi 5 → 6: Slow-Mo Lompatan Matahari Crimson", eye, tgt, 19.0, lerp(-6.0, 6.0, u), (0.004, 0.0), bima_leap, 28.0, 0.84)

    # ==================== LOKASI 6: WAJAH MENARA JAM UTAMA DI DERMAGA (00:49 - 00:58) ====================
    if t < 52.0:
        # [CAM 25] Precision Speed-Ramped Dolly-In dari bahu Bima menuju kunci di pusat jarum jam!
        u = snappy_dolly_overshoot((t - 49.0) / 2.8, overshoot=0.05)
        eye = lerp_vec(vec3(2.8, 18.4, 111.5), vec3(0.55, 19.35, 114.85), clamp(u))
        tgt = lerp_vec(vec3(0.2, 19.1, 116.8), vec3(0.0, 19.5, 117.2), clamp(u))
        return ShotCamera("CAM 25", "Lokasi 6: Menara Jam Utama (DONG!)", eye, tgt, 21.0, lerp(5.0, 0.0, clamp(u)), (0.0, 0.015 * (1.0 - clamp(u))), vec3(0, 19.0, 118.0), 22.0, 0.74)

    if t < 54.5:
        # [CAM 26] Radial Shockwave Pull-Back — epic wide pull-back memperlihatkan menara jam, burung camar, trem, mercusuar & twilight!
        u = exp_ease_in_out((t - 52.0) / 2.5, 4.5)
        eye = lerp_vec(vec3(0.55, 19.35, 114.85), vec3(-11.5, 20.5, 86.0), u)
        tgt = lerp_vec(vec3(0.0, 19.5, 117.2), vec3(4.5, 15.2, 114.0), u)
        return ShotCamera("CAM 26", "Lokasi 6: Frozen Twilight Shockwave Pull-Back", eye, tgt, 18.0, lerp(0.0, -3.0, u), (0.0, -0.012 * math.sin(u * math.pi)), vec3(0, 16.0, 114.0), 38.0, 0.85)

    if t < 56.4:
        # [CAM 27] Comedic Snap-Zoom to Pocket — Bima tersenyum lega -> snap-zoom ke saku robek & Kunci Perak meluncur keluar!
        u = snappy_dolly_overshoot((t - 54.5) / 1.5, overshoot=0.055)
        eye = lerp_vec(vec3(-1.4, 17.5, 111.4), vec3(-0.32, 16.92, 113.45), clamp(u))
        tgt = lerp_vec(vec3(-0.18, 16.6, 115.85), vec3(-0.24, 16.18, 115.85), clamp(u))
        return ShotCamera("CAM 27", "Lokasi 6: Twist Komedi — Kunci Perak!", eye, tgt, 22.0, lerp(-2.0, 3.5, clamp(u)), (0.008 * (1.0 - clamp(u)), 0.0), vec3(0, 16.5, 116.5), 16.0, 0.76)

    # [CAM 28] Seamless Loop Whip-Pan Dive mengikuti Kunci Perak menembus celah dua roda gigi jam -> kembali ke [CAM 01]!
    u = exp_ease_in_out((t - 56.4) / 1.6, 6.5)
    silver_y = lerp(15.6, 12.6, u * u)
    eye = lerp_vec(vec3(-0.15, 15.8, 114.4), vec3(0.0, 13.15, 115.1), u)
    tgt = vec3(0.0, silver_y, 117.6)
    return ShotCamera("CAM 28", "Lokasi 6 → 1: Seamless Loop Dive!", eye, tgt, 18.0, lerp(5.0, -4.0, u), (0.0, 0.044 * math.sin(u * math.pi)), vec3(0, 14.0, 117.0), 14.0, 0.80)


def collect_frame_billboards(
    t: float,
    cam: ShotCamera,
    lighting: LightingState,
    tram_z: float,
    sprites: SpriteCache,
    quantize_deg: float = 8.0,
) -> List[BillboardDraw]:
    """
    Kumpulkan seluruh aktor (Bima, Oren, Figuran), Hero Props (Kunci Emas & Perak),
    dan partikel 3D volumetrik untuk frame pada detik ke-t menggunakan RIGGING TERBUKA!
    """
    bbs: List[BillboardDraw] = []
    phase = lighting.phase_name
    key_p, key_yaw, key_roll = _eval_golden_key_pos(t)
    frame_idx = int(round(t * 30.0))

    def q_ang(deg: float) -> float:
        return round((deg % 360.0) / quantize_deg) * quantize_deg

    # ==================== 1. HERO PROP: KUNCI EMAS ====================
    if t < 56.2:
        k_rig = KeyPropRig(
            yaw_deg=q_ang(key_yaw),
            roll_deg=round(key_roll / 6.0) * 6.0,
            sun_glow=(t < 10.0 or t > 41.0),
            lighting_phase=phase,  # type: ignore[arg-type]
        )
        k_tag = f"gold_{int(k_rig.yaw_deg)}_{int(k_rig.roll_deg)}_{int(k_rig.sun_glow)}_{phase}"
        k_img, k_cache = sprites.render_golden_key(k_rig, cache_tag=k_tag)
        # Ukuran hero prop dibuat dramatis & terbaca di 18-22mm wide-angle
        if 31.4 <= t <= 34.0:
            k_scale = 0.72  # hero close-up KLAK! di poros mesin
        elif t < 5.0:
            k_scale = 0.44
        elif t < 35.0:
            k_scale = 0.56
        else:
            k_scale = 0.58
        bbs.append(
            BillboardDraw(
                center=key_p,
                width=k_scale * 0.62,
                height=k_scale,
                rgba_image=k_img,
                anchor_bottom=False,
                fog_scale=0.20,
                emissive_boost=0.28 if (t > 40.0 or 31.4 <= t <= 34.0) else 0.08,
                cache_key=k_cache,
            )
        )

    # ==================== 2. BIMA (PROTAGONIS — UNLOCKED HumanoidRig PER ADEGAN!) ====================
    bima_pos = None
    bima_facing = 180.0
    bima_rig = None
    bima_anim = "static"
    bima_roll = 0.0
    bima_h = 1.65

    if t < 8.5:
        # Lokasi 1: Bima panik di belakang meja mencoba menyambar kunci!
        bima_pos = vec3(-0.08, 25.35, 1.85)
        bima_facing = 180.0
        bima_rig = HumanoidRig(
            eyes="panic" if t > 1.2 else "shocked",
            eyebrows="worried",
            mouth="open_yell",
            sweat_drop=True,
            eye_gaze_x=0.35,
            eye_gaze_y=0.25,
            right_hand_target=(88, 192, 42),
            left_hand_target=(-68, 224, 30),
            scarf_sway=-12.0,
            jambul_sway=-8.0,
        )
    elif 11.2 <= t < 18.2:
        # Lokasi 2: Bima melompat dari atap mengejar kunci melintasi tenda & tangga!
        if t < 14.6:
            u = (t - 11.2) / 3.4
            bima_pos = vec3(lerp(-0.4, 0.1, u), lerp(18.0, 15.2, u) + abs(math.sin(u * math.pi * 2)) * 1.4, lerp(10.6, 15.4, u))
            bima_anim = "jump"
            bima_rig = HumanoidRig(eyes="focused", eyebrows="angry", mouth="grit_teeth", scarf_sway=-28.0, jambul_sway=10.0)
        else:
            u = (t - 14.6) / 3.6
            bima_pos = vec3(lerp(0.1, 0.3, u), lerp(12.2, 5.4, u), lerp(16.0, 26.8, u))
            bima_anim = "run"
            bima_rig = HumanoidRig(eyes="shocked", eyebrows="worried", mouth="open_yell", sweat_drop=True, scarf_sway=-24.0)
        bima_facing = 0.0
    elif 18.2 <= t < 25.2:
        # Lokasi 3: Bima mengejar di gang lalu meluncur dengan lutut mencoba meraih kunci ([CAM 14])!
        u = clamp((t - 18.2) / 6.5)
        bima_pos = vec3(lerp(0.2, -0.15, u), 5.05, lerp(28.5, 39.2, u))
        bima_facing = 0.0
        if t >= 22.8:
            # Meluncur lutut rendah mengejar kunci!
            bima_roll = -18.0
            bima_rig = HumanoidRig(
                torso_lean_z=0.16,
                eyes="panic",
                eyebrows="worried",
                mouth="grit_teeth",
                sweat_drop=True,
                right_hand_target=(95, 200, 44),
                left_hand_target=(-64, 245, 22),
                scarf_sway=-34.0,
            )
        else:
            bima_anim = "run"
            bima_rig = HumanoidRig(eyes="focused", eyebrows="angry", mouth="grit_teeth", scarf_sway=-26.0)
    elif 33.8 <= t < 38.2:
        # Lokasi 4: Bima terlempar naik di cerobong uap zamrud! ([CAM 19])
        u = (t - 33.8) / 4.4
        bima_pos = vec3(-0.9, lerp(-16.0, 9.8, u), lerp(50.0, 61.8, clamp(u * 1.4)))
        bima_facing = 180.0
        bima_roll = math.sin(u * 8.0) * 16.0
        bima_rig = HumanoidRig(
            eyes="asymmetric",
            eyebrows="raised",
            mouth="open_yell",
            sweat_drop=True,
            right_hand_target=(86, 154, 34),
            left_hand_target=(-84, 158, 34),
            scarf_sway=28.0,
            jambul_sway=14.0,
        )
    elif 40.6 <= t < 49.2:
        # Lokasi 5: Bima berlari kencang di atap trem ([CAM 21]-[CAM 23]) lalu LOMPAT di depan matahari crimson ([CAM 24])!
        if t < 46.2:
            u = (t - 40.6) / 5.6
            bima_pos = vec3(0.0, 13.38, tram_z + lerp(-4.4, 4.6, u))
            bima_facing = 0.0
            bima_anim = "run"
            bima_rig = HumanoidRig(eyes="focused", eyebrows="angry", mouth="grit_teeth", scarf_sway=-36.0, jambul_sway=-12.0)
        else:
            u = exp_ease_in_out((t - 46.2) / 2.8, 4.5)
            bima_pos = vec3(0.0, 14.5 + math.sin(u * math.pi) * 4.4, lerp(tram_z + 5.2, 110.5, u))
            bima_facing = -115.0  # heroic front-3/4 dynamic profile menghadap menara jam & kamera!
            bima_roll = lerp(-10.0, 14.0, u)
            bima_rig = HumanoidRig(
                pelvis_y=-24.0,
                head_bob_y=-26.0,
                jump_height=38.0,
                torso_lean_z=0.12,
                eyes="focused",
                eyebrows="raised",
                mouth="open_yell",
                right_hand_target=(96, 158, 42),
                left_hand_target=(-74, 198, 22),
                left_foot_target=(-26, 404, -22),
                right_foot_target=(38, 412, 24),
                scarf_sway=-38.0,
                jambul_sway=12.0,
            )
    elif t >= 49.2:
        # Lokasi 6: Bima di balkon wajah menara jam ([CAM 25] memutar kunci -> [CAM 26]-[CAM 27] lega + saku robek!)
        bima_pos = vec3(-0.15, 15.42, 115.85)
        bima_facing = 0.0 if t < 53.0 else 180.0
        if t < 52.2:
            bima_rig = HumanoidRig(
                eyes="focused",
                eyebrows="raised",
                mouth="grit_teeth",
                right_hand_target=(82, 165, 42),
                left_hand_target=(-52, 235, 24),
                scarf_sway=-14.0,
            )
        else:
            # Tersenyum lega menepuk dada sambil Kunci Perak meluncur keluar dari saku robek ([CAM 27]!)
            bima_rig = HumanoidRig(
                eyes="happy",
                eyebrows="happy",
                mouth="happy_open",
                right_hand_target=(16, 246, 44),
                left_hand_target=(-52, 280, 20),
                silver_key_peek=(54.2 <= t <= 56.6),
                thread_sway=math.sin(t * 6.0) * 3.5,
                scarf_sway=math.sin(t * 2.5) * 6.0,
            )

    if bima_pos is not None and bima_rig is not None:
        rel_yaw = q_ang(camera_relative_yaw_deg(bima_pos, bima_facing, cam.cam_pos))
        bima_rig.angle = rel_yaw
        b_img, _ = sprites.render_bima(bima_rig, lighting_phase=phase, animation=bima_anim, frame=frame_idx)
        aspect_b = b_img.width / float(max(1, b_img.height))
        bbs.append(
            BillboardDraw(
                center=bima_pos,
                width=bima_h * aspect_b,
                height=bima_h,
                rgba_image=b_img,
                anchor_bottom=True,
                roll_deg=bima_roll,
                fog_scale=0.35,
            )
        )

    # ==================== 3. OREN — KUCING KAMPUNG GANG KAFE (Lokasi 3: 18..25s) ====================
    if 17.5 <= t <= 25.5:
        oren_pos = vec3(-0.82, 5.02, 36.85)
        oren_yaw = q_ang(camera_relative_yaw_deg(oren_pos, 155.0, cam.cam_pos))
        # Menepis Kunci Emas tepat di [CAM 12]-[CAM 13] (20.4..22.4s)!
        slap_amt = clamp((t - 20.3) / 0.7) if t < 22.4 else clamp(1.0 - (t - 22.4) / 0.8)
        o_rig = OrenRig(
            angle=oren_yaw,
            body_lean=-0.07 * slap_amt,
            eyelid_level=0.56,
            gaze_x=0.42,
            mouth_style="smug",
            right_paw_raised=slap_amt,
            show_paw_pads=(slap_amt > 0.35),
            claws_out=slap_amt * 0.9,
            tail_sway=math.sin(t * 3.2) * 18.0 + slap_amt * 12.0,
            bell_sway=slap_amt * 6.0,
        )
        o_img, _ = sprites.render_oren(o_rig)
        bbs.append(
            BillboardDraw(
                center=oren_pos,
                width=0.72,
                height=0.82,
                rgba_image=o_img,
                anchor_bottom=True,
                fog_scale=0.35,
            )
        )

    # ==================== 4. FIGURAN PASAR (Pedagang Rempah — Lokasi 2: 9..18s) ====================
    if 8.5 <= t <= 18.5:
        merchants = [
            (vec3(-0.98, 12.0, 17.6), 25.0, -18.0 if t > 14.8 else 0.0),
            (vec3(1.12, 12.0, 17.8), -35.0, 20.0 if t > 14.9 else 0.0),
            (vec3(-2.4, 14.2, 12.0), 40.0, 0.0),
        ]
        for mi, (mp, mface, mroll) in enumerate(merchants):
            myaw = q_ang(camera_relative_yaw_deg(mp, mface, cam.cam_pos))
            panicking = (t > 14.6)
            mrig = HumanoidRig(
                angle=myaw,
                pose="panic" if panicking else "ready",
                eyes="shocked" if panicking else "chill",
                eyebrows="worried" if panicking else "happy",
                mouth="open_yell" if panicking else "smirk",
                sweat_drop=panicking,
                hat_lift_y=12.0 if panicking else 0.0,
                hat_tilt=-14.0 if panicking else 0.0,
            )
            m_tag = f"merch_{mi}_{int(myaw)}_{int(panicking)}"
            m_img, m_cache = sprites.render_pedagang(mrig, cache_tag=m_tag)
            bbs.append(
                BillboardDraw(
                    center=mp,
                    width=1.82 * (m_img.width / float(m_img.height)),
                    height=1.82,
                    rgba_image=m_img,
                    anchor_bottom=True,
                    roll_deg=mroll,
                    fog_scale=0.45,
                    cache_key=m_cache,
                )
            )

    # ==================== 5. FIGURAN STASIUN (Penumpang Trem — Lokasi 5: 38..49s) ====================
    if 37.8 <= t <= 50.0:
        passengers = [
            (vec3(-3.2, 10.05, 76.0), 80.0),
            (vec3(3.3, 10.05, 83.5), -85.0),
            (vec3(-3.3, 10.05, 96.5), 115.0),
            (vec3(3.3, 10.05, 99.5), -110.0),
        ]
        for pi, (pp, pface) in enumerate(passengers):
            pyaw = q_ang(camera_relative_yaw_deg(pp, pface, cam.cam_pos))
            prig = HumanoidRig(
                angle=pyaw,
                eyes="asymmetric",
                eyebrows="raised",
                mouth="small_o",
                prop="scroll" if pi % 2 == 0 else "none",
                hat_lift_y=11.0,
                hat_tilt=-16.0,
                scarf_sway=34.0,  # syal melayang mundur menegaskan time reversal [CAM 21]!
                sweat_drop=True,
            )
            p_tag = f"pass_{pi}_{int(pyaw)}"
            p_img, p_cache = sprites.render_penumpang(prig, cache_tag=p_tag)
            bbs.append(
                BillboardDraw(
                    center=pp,
                    width=1.96 * (p_img.width / float(p_img.height)),
                    height=1.96,
                    rgba_image=p_img,
                    anchor_bottom=True,
                    fog_scale=0.45,
                    cache_key=p_cache,
                )
            )

    # ==================== 6. HERO PROP #2: KUNCI PERAK (Plot Twist [CAM 27]-[CAM 28]!) ====================
    if t >= 55.4:
        u_s = clamp((t - 55.4) / 2.6)
        s_pos = vec3(lerp(-0.44, 0.0, u_s), lerp(16.12, 12.2, u_s * u_s), lerp(115.48, 117.6, u_s))
        s_rig = KeyPropRig(yaw_deg=q_ang(18.0 + u_s * 240.0), roll_deg=26.0 + u_s * 160.0)
        s_img, s_cache = sprites.render_silver_key(s_rig, cache_tag=f"silver_{int(s_rig.yaw_deg)}")
        bbs.append(
            BillboardDraw(
                center=s_pos,
                width=0.56 * 0.62,
                height=0.56,
                rgba_image=s_img,
                anchor_bottom=False,
                fog_scale=0.08,
                emissive_boost=0.35,
                cache_key=s_cache,
            )
        )
        # Kilau dingin tajam pada kepala Kunci Perak agar langsung terbaca!
        if t < 56.5:
            bbs.append(
                BillboardDraw(
                    center=s_pos + vec3(-0.08, 0.14, -0.08),
                    width=0.22,
                    height=0.22,
                    rgba_image=sprites.spark_emerald,
                    anchor_bottom=False,
                    tint=(0.82, 0.94, 1.0, 0.85),
                    fog_scale=0.0,
                    emissive_boost=1.4,
                    cache_key="fx_spark_emerald",
                    is_fx=True,
                )
            )

    # ==================== 7. PARTIKEL 3D VOLUMETRIK (is_fx=True -> soft blending tanpa depth-write!) ====================
    # a) Partikel debu berkilau dalam sinar Low Sun (Lokasi 1: 0..9s)
    if t < 9.5:
        for di in range(14):
            dp = vec3(
                math.sin(di * 2.1 + t * 0.4) * 1.9,
                26.4 + (di % 5) * 0.52 + math.sin(t + di) * 0.12,
                -0.8 + (di * 0.36) % 4.6,
            )
            bbs.append(
                BillboardDraw(
                    center=dp,
                    width=0.11,
                    height=0.11,
                    rgba_image=sprites.puff_golden_dust,
                    anchor_bottom=False,
                    tint=(1.0, 0.94, 0.72, 0.62),
                    fog_scale=0.05,
                    emissive_boost=0.65,
                    cache_key="fx_gold_dust",
                    is_fx=True,
                )
            )

    # b) Ledakan awan bubuk kunyit kuning cerah & cabai merah (Lokasi 2 [CAM 09]: 14.3..17.4s)
    if 14.3 <= t <= 17.4:
        exp_u = clamp((t - 14.3) / 1.4)
        fade = clamp(1.0 - max(0.0, t - 16.0) / 1.4)
        for ci in range(18):
            a = ci * 0.72
            r_c = (0.35 + (ci % 4) * 0.52) * (0.35 + exp_u * 1.35)
            cp = vec3(
                0.25 + math.cos(a) * r_c,
                12.85 + ((ci % 3) * 0.55 + exp_u * 1.15),
                16.9 + math.sin(a) * r_c,
            )
            is_chili = (ci % 5 == 0)
            bbs.append(
                BillboardDraw(
                    center=cp,
                    width=1.20 + (ci % 3) * 0.36,
                    height=1.20 + (ci % 3) * 0.36,
                    rgba_image=sprites.puff_chili if is_chili else sprites.puff_turmeric,
                    anchor_bottom=False,
                    tint=(1.0, 1.0, 1.0, 0.54 * fade),
                    fog_scale=0.15,
                    emissive_boost=0.22,
                    cache_key="fx_chili" if is_chili else "fx_turmeric",
                    is_fx=True,
                )
            )

    # c) Kepulan uap zamrud gorong-gorong + percikan api biru-zamrud saat KLAK! (Lokasi 4: 26..39s)
    if 26.0 <= t <= 39.2:
        for ei in range(14):
            ep = vec3(
                math.sin(ei * 1.7 + t * 0.8) * (3.2 if t < 34.0 else 1.8),
                (-22.5 + ((ei * 1.9 + t * 2.2) % 14.0)) if t < 34.0 else (lerp(-14.0, 10.0, (t - 34.0) / 4.2) + (ei % 4 - 1.5) * 2.4),
                (43.8 + (ei % 4) * 2.2) if t < 34.0 else 61.5 + math.cos(ei) * 1.6,
            )
            bbs.append(
                BillboardDraw(
                    center=ep,
                    width=2.4,
                    height=2.4,
                    rgba_image=sprites.puff_emerald_steam,
                    anchor_bottom=False,
                    tint=(0.35, 1.0, 0.78, 0.36),
                    fog_scale=0.15,
                    emissive_boost=0.55,
                    cache_key="fx_emerald_steam",
                    is_fx=True,
                )
            )
        # Percikan biru-zamrud menyebar organik & asimetris dari lubang poros ([CAM 18] 31.8..33.8s, Kunci Emas tetap tajam di tengah!)
        if 31.8 <= t <= 33.8:
            sp_u = clamp((t - 31.8) / 1.5)
            sp_a = clamp(1.0 - sp_u)
            spark_seeds = [
                (0.18, 0.52, 0.30, 1.0), (0.85, 0.86, 0.22, 0.8), (1.42, 0.62, 0.34, 1.0),
                (2.15, 0.98, 0.24, 0.75), (2.78, 0.58, 0.28, 0.95), (3.48, 0.92, 0.26, 0.85),
                (4.02, 0.55, 0.32, 1.0), (4.72, 1.04, 0.22, 0.72), (5.34, 0.66, 0.28, 0.92),
                (5.88, 0.88, 0.20, 0.78), (1.08, 1.18, 0.20, 0.70), (3.82, 1.22, 0.24, 0.74),
            ]
            for si, (ang_s, rad_mul, sz_s, a_mul) in enumerate(spark_seeds):
                r_s = (0.42 + sp_u * 1.15) * rad_mul
                sp_p = vec3(
                    math.cos(ang_s) * r_s,
                    -17.0 + math.sin(ang_s) * r_s - sp_u * sp_u * 0.28,
                    43.05 - (si % 3) * 0.04,
                )
                bbs.append(
                    BillboardDraw(
                        center=sp_p,
                        width=sz_s,
                        height=sz_s,
                        rgba_image=sprites.spark_emerald,
                        anchor_bottom=False,
                        tint=(0.70, 1.0, 0.96, sp_a * a_mul * 0.88),
                        fog_scale=0.0,
                        emissive_boost=1.05,
                        cache_key="fx_spark_emerald",
                        is_fx=True,
                    )
                )

    return bbs
