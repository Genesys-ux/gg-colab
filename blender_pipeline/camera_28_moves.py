"""
Koreografi 28 Gerakan Kamera Virtual Continuous One-Take ([CAM 01] – [CAM 28]) untuk Blender 4.2+ EEVEE Next.
- Lensa Wide-Angle 18-22mm (sensor portrait 9:16 full-frame 36mm vertikal)
- Kurva gerak exponential ease-in-out, snappy speed-ramped dolly + subtle overshoot, whip-pan, 360° barrel roll, inverted low-skim
- Rotasi berbasis Quaternion berkesinambungan (bebas gimbal lock untuk motion blur EEVEE Next!)
- Depth of Field otomatis mengunci jarak fokus ke subjek hero (Bima / Kunci Emas / Oren / Kunci Perak)!
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Tuple

from .config import FPS, SENSOR_HEIGHT_MM, TOTAL_FRAMES, frame_to_sec, w_to_b


def clamp(v: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, float(v)))


def lerp(a: float, b: float, t: float) -> float:
    return float(a + (b - a) * t)


def lerp3(a: Tuple[float, float, float], b: Tuple[float, float, float], t: float) -> Tuple[float, float, float]:
    return (lerp(a[0], b[0], t), lerp(a[1], b[1], t), lerp(a[2], b[2], t))


def add3(a: Tuple[float, float, float], b: Tuple[float, float, float]) -> Tuple[float, float, float]:
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def smoothstep(t: float) -> float:
    u = clamp(t)
    return u * u * (3.0 - 2.0 * u)


def exp_ease_in_out(t: float, power: float = 7.5) -> float:
    u = clamp(t)
    if u <= 0.0:
        return 0.0
    if u >= 1.0:
        return 1.0
    if u < 0.5:
        return 0.5 * math.pow(2.0, power * (2.0 * u - 1.0))
    return 1.0 - 0.5 * math.pow(2.0, -power * (2.0 * u - 1.0))


def snappy_dolly_overshoot(t: float, overshoot: float = 0.045) -> float:
    u = clamp(t)
    if u <= 0.0:
        return 0.0
    if u >= 1.0:
        return 1.0
    base = 1.0 - math.exp(-7.2 * u)
    base_norm = base / (1.0 - math.exp(-7.2))
    ring = math.sin(u * math.pi * 1.45) * math.exp(-4.6 * u) * overshoot * 4.2
    return base_norm + ring * (1.0 - u)


def whip_curve(t: float) -> float:
    return exp_ease_in_out(t, power=9.5)


def eval_tram_z_fwd(t: float) -> float:
    """Posisi maju (sumbu Y di Blender / Z_fwd dunia) Trem Merah Vintage yang meluncur MUNDUR di Lokasi 5."""
    if t < 38.0:
        return 104.0
    if t < 46.2:
        return 104.0 - (t - 38.0) * 1.65
    base_46 = 104.0 - (46.2 - 38.0) * 1.65
    if t < 51.8:
        return base_46 - (t - 46.2) * 0.35
    base_51 = base_46 - (51.8 - 46.2) * 0.35
    return base_51 + (t - 51.8) * 1.9


def eval_golden_key_world(t: float) -> Tuple[Tuple[float, float, float], float, float]:
    """
    Posisi Kunci Emas dalam koordinat (x, y_up, z_fwd) + (yaw_deg, roll_deg) pada detik t (0..58).
    Dipakai bersama oleh kamera & animation_director agar framing selalu terkunci presisi!
    """
    if t < 2.2:
        u = clamp(t / 2.2)
        return (lerp(0.18, 0.22, u), lerp(27.28, 27.08, u * u), lerp(0.55, 0.72, u)), t * 45.0, -24.0 + u * 18.0
    if t < 4.2:
        u = (t - 2.2) / 2.0
        return (0.24 + u * 0.08, 27.08 - u * 0.24, 0.72 + u * 0.28), 99.0 + u * 75.0, -6.0 + u * 45.0
    if t < 5.8:
        u = (t - 4.2) / 1.6
        if u < 0.45:
            v = u / 0.45
            p = (lerp(0.32, 0.55, v), lerp(26.84, 26.38, v * v), lerp(1.0, 1.55, v))
        else:
            v = (u - 0.45) / 0.55
            p = (lerp(0.55, 0.28, v), lerp(26.38, 26.22, v) + math.sin(v * math.pi) * 0.48, lerp(1.55, 1.78, v))
        return p, t * 240.0, t * 180.0
    if t < 7.4:
        # Menggelinding cepat di atas meja kerja oak (z=1.78..2.38, kontinyu & bebas tembus!)
        u = (t - 5.8) / 1.6
        return (lerp(0.28, 0.05, u), 26.22 + abs(math.sin(u * math.pi * 4)) * 0.05, lerp(1.78, 2.38, u)), t * 320.0, t * 280.0
    if t < 9.0:
        # Terpental bersih melewati ambang jendela terbuka (y>=26.65 saat z=4.25!) keluar ke kota!
        u = (t - 7.4) / 1.6
        arc = math.sin(u * math.pi) * 1.15
        return (lerp(0.05, 0.0, u), lerp(26.22, 24.4, u * u) + arc, lerp(2.38, 6.8, u)), t * 380.0, t * 340.0
    if t < 11.0:
        u = (t - 9.0) / 2.0
        return (math.sin(u * 3.0) * 0.15, lerp(24.4, 17.7, u * u), lerp(6.8, 10.8, u)), t * 420.0, t * 360.0
    if t < 12.8:
        u = (t - 11.0) / 1.8
        return (lerp(0.0, 0.2, u), lerp(17.7, 15.8, u) + math.sin(u * math.pi) * 3.2, lerp(10.8, 14.2, u)), t * 340.0, t * 220.0
    if t < 14.6:
        u = (t - 12.8) / 1.8
        return (lerp(0.2, 0.25, u), lerp(15.8, 13.0, u), lerp(14.2, 16.9, u)), t * 420.0, t * 300.0
    if t < 16.2:
        u = (t - 14.6) / 1.6
        return (lerp(0.25, 1.85, u), lerp(13.0, 11.4, u) + math.sin(u * math.pi) * 0.9, lerp(16.9, 19.8, u)), t * 460.0, t * 340.0
    if t < 18.0:
        u = (t - 16.2) / 1.8
        return (lerp(1.85, 0.85, u), lerp(11.4, 5.45, u), lerp(19.8, 28.0, u)), t * 390.0, t * 290.0
    if t < 21.6:
        u = (t - 18.0) / 3.6
        return (lerp(0.85, -0.58, u), 5.35 + abs(math.sin(u * math.pi * 3)) * 0.30, lerp(28.0, 36.8, u)), t * 360.0, t * 260.0
    if t < 25.0:
        u = (t - 21.6) / 3.4
        return (lerp(-0.58, 0.0, u), lerp(5.75, 5.18, u) + math.sin(u * math.pi) * 0.85, lerp(36.8, 42.5, u)), t * 680.0, t * 520.0
    if t < 26.0:
        u = (t - 25.0) / 1.0
        return (0.0, lerp(5.18, 2.2, u * u), 42.5), t * 520.0, 0.0
    if t < 31.9:
        u = (t - 26.0) / 5.9
        bounce = abs(math.sin(u * math.pi * 2.5)) * 1.4 * (1.0 - u)
        return (math.sin(u * math.pi * 3.0) * 1.1 * (1.0 - u), lerp(-8.5, -17.0, u) + bounce, lerp(41.8, 42.96, u)), t * 360.0, t * 220.0
    if t < 34.0:
        rot_rev = 0.0 if t < 32.35 else -(t - 32.35) * 320.0
        return (0.0, -17.0, 42.96), 0.0, rot_rev
    if t < 38.2:
        # 2-tahap bebas tembus dinding: (1) meluncur lewat lorong portal z=58 -> cerobong z=62, (2) melesat spiral lurus naik di dalam cerobong!
        if t < 35.3:
            u1 = (t - 34.0) / 1.3
            return (
                math.sin(u1 * math.pi * 2.0) * 0.42,
                lerp(-17.0, -15.2, smoothstep(u1)),
                lerp(42.96, 62.0, smoothstep(u1)),
            ), t * 420.0, t * 300.0
        u2 = (t - 35.3) / 2.9
        ang = u2 * math.pi * 3.0
        r = lerp(1.05, 0.42, u2)
        return (
            math.cos(ang) * r,
            lerp(-15.2, 12.2, u2),
            62.0 + math.sin(ang) * r,
        ), t * 480.0, t * 320.0
    if t < 49.0:
        u = (t - 38.2) / 10.8
        return (lerp(0.42, 0.0, u), lerp(12.2, 19.5, u) + math.sin(u * math.pi) * 9.5, lerp(62.0, 115.2, u)), t * 320.0, t * 180.0
    if t < 51.8:
        u = smoothstep((t - 49.0) / 2.8)
        return (lerp(0.0, 0.0, u), lerp(19.5, 19.5, u), lerp(115.2, 117.05, u)), lerp(45.0, 0.0, u), lerp(-35.0, 0.0, u)
    return (0.0, 19.5, 117.05), 0.0, 90.0


@dataclass
class CameraFrameSpec:
    cam_id: str
    eye_w: Tuple[float, float, float]
    tgt_w: Tuple[float, float, float]
    focal_mm: float
    roll_deg: float
    fstop: float = 4.2


def eval_camera_world(t: float) -> CameraFrameSpec:
    """Evaluasi lengkap 28 gerakan kamera pada detik t (0.0 .. 58.0) dalam koordinat (x, y_up, z_fwd)."""
    key_p, _, _ = eval_golden_key_world(t)
    tram_z = eval_tram_z_fwd(t)

    # ==================== LOKASI 1: BENGKEL JAM LOTENG (00:00 - 00:09) ====================
    if t < 2.2:
        u = snappy_dolly_overshoot(t / 2.2, overshoot=0.055)
        eye = lerp3((0.0, 27.20, -3.55), (0.08, 27.06, -0.35), u)
        tgt = lerp3((0.10, 27.05, 0.95), (0.10, 26.95, 1.05), clamp(u))
        return CameraFrameSpec("CAM 01", eye, tgt, lerp(18.0, 21.0, clamp(u)), -3.5 * clamp(u), fstop=2.8)
    if t < 4.2:
        u = exp_ease_in_out((t - 2.2) / 2.0, 5.5)
        ang = math.radians(lerp(-12.0, 108.0, u))
        r = lerp(0.85, 1.28, u)
        eye = add3(key_p, (math.sin(ang) * r, lerp(0.05, 0.16, u), -math.cos(ang) * r))
        tgt = lerp3(key_p, (-0.10, 26.48, 2.68), 0.28 * u)
        return CameraFrameSpec("CAM 02", eye, tgt, 20.0, lerp(-8.0, 13.0, u), fstop=2.4)
    if t < 5.8:
        u = exp_ease_in_out((t - 4.2) / 1.6, 5.5)
        eye = lerp3((1.15, 27.38, 0.45), (1.22, 26.58, 0.92), u)
        tgt = lerp3(key_p, (0.25, 26.42, 1.65), 0.35)
        return CameraFrameSpec("CAM 03", eye, tgt, 19.0, lerp(8.0, -5.0, u), fstop=3.2)
    if t < 7.4:
        u = smoothstep((t - 5.8) / 1.6)
        eye = (lerp(0.95, 0.72, u), 26.32, lerp(1.45, 2.48, u))
        tgt = add3(key_p, (-0.10, 0.08, 0.55))
        return CameraFrameSpec("CAM 04", eye, tgt, 18.0, -3.5, fstop=3.0)
    if t < 9.0:
        u = whip_curve((t - 7.4) / 1.6)
        eye = lerp3((0.72, 26.40, 2.48), (0.15, 25.4, 6.4), u)
        tgt = lerp3(key_p, (0.0, 21.0, 11.2), u)
        return CameraFrameSpec("CAM 05", eye, tgt, 18.0, lerp(-4.0, 12.0, u), fstop=4.5)

    # ==================== LOKASI 2: PASAR REMPAH & BUAH BERTINGKAT (00:09 - 00:18) ====================
    if t < 11.0:
        u = (t - 9.0) / 2.0
        return CameraFrameSpec("CAM 06", add3(key_p, (1.85, 1.35, -1.75)), add3(key_p, (-0.2, -1.2, 1.2)), 18.0, lerp(12.0, -8.0, u), fstop=4.5)
    if t < 12.8:
        u = snappy_dolly_overshoot((t - 11.0) / 1.8, overshoot=0.05)
        eye = add3(key_p, (lerp(1.9, 2.8, clamp(u)), lerp(0.2, 1.6, clamp(u)), lerp(-1.8, -3.2, clamp(u))))
        return CameraFrameSpec("CAM 07", eye, add3(key_p, (0.0, -0.35, 0.5)), 19.5, lerp(-8.0, 4.0, clamp(u)), fstop=4.8)
    if t < 14.6:
        u = exp_ease_in_out((t - 12.8) / 1.8, 5.0)
        bima_p = (lerp(-0.4, 0.2, u), lerp(18.0, 15.6, u) + math.sin(u * math.pi) * 1.4, lerp(11.2, 15.2, u))
        eye = add3(bima_p, (lerp(2.4, 1.6, u), 1.45, lerp(2.8, 3.2, u)))
        tgt = lerp3(add3(bima_p, (0, 0.6, 0)), key_p, 0.35)
        return CameraFrameSpec("CAM 08", eye, tgt, 18.0, u * 360.0, fstop=4.5)
    if t < 16.2:
        u = (t - 14.6) / 1.6
        eye = lerp3((0.28, 14.35, 13.7), (0.20, 13.15, 16.4), u)
        tgt = (0.05, 12.90, 17.2)
        return CameraFrameSpec("CAM 09", eye, tgt, 18.0, lerp(-5.0, 6.0, u), fstop=4.0)
    if t < 18.0:
        u = exp_ease_in_out((t - 16.2) / 1.8, 5.5)
        eye = lerp3((0.6, 12.8, 18.5), (0.2, 6.2, 26.8), u)
        tgt = add3(key_p, (-0.3, -0.4, 1.4))
        return CameraFrameSpec("CAM 10", eye, tgt, 18.0, lerp(7.0, -5.0, u), fstop=4.5)

    # ==================== LOKASI 3: GANG KAFE & JEMURAN SEMPIT (00:18 - 00:26) ====================
    if t < 19.8:
        u = smoothstep((t - 18.0) / 1.8)
        eye = (lerp(-1.4, -0.8, u), 5.42, lerp(28.2, 34.4, u))
        tgt = (lerp(0.5, -0.4, u), 5.75, lerp(33.5, 38.0, u))
        return CameraFrameSpec("CAM 11", eye, tgt, 18.0, -5.0 + u * 8.0, fstop=3.8)
    if t < 21.4:
        u = snappy_dolly_overshoot((t - 19.8) / 1.6, overshoot=0.05)
        eye = lerp3((-0.8, 5.45, 34.4), (-0.08, 5.88, 35.10), u)
        tgt = lerp3((-0.4, 5.75, 38.0), (-0.82, 5.55, 36.85), clamp(u))
        return CameraFrameSpec("CAM 12", eye, tgt, 21.0, lerp(3.0, -6.0, clamp(u)), fstop=2.4)
    if t < 23.0:
        u = exp_ease_in_out((t - 21.4) / 1.6, 5.5)
        ang = math.radians(lerp(35.0, -62.0, u))
        pivot = (-0.65, 5.65, 37.3)
        eye = add3(pivot, (math.sin(ang) * 2.2, 0.45, -math.cos(ang) * 2.2))
        return CameraFrameSpec("CAM 13", eye, lerp3(pivot, key_p, clamp(u * 1.1)), 19.0, lerp(-6.0, 12.0, u), fstop=3.2)
    if t < 24.6:
        u = smoothstep((t - 23.0) / 1.6)
        eye = (lerp(0.62, 0.48, u), 5.45, lerp(40.9, 41.8, u))
        tgt = (lerp(-0.14, -0.06, u), 5.58, lerp(37.4, 38.6, u))
        return CameraFrameSpec("CAM 14", eye, tgt, 18.0, lerp(164.0, 170.0, u), fstop=3.6)
    if t < 26.0:
        u = exp_ease_in_out((t - 24.6) / 1.4, 7.0)
        eye = lerp3((0.35, 6.95, 42.15), (0.0, 4.95, 42.5), u)
        tgt = (0.0, lerp(5.05, 1.5, u), 42.52)
        return CameraFrameSpec("CAM 15", eye, tgt, 18.0, lerp(140.0, 0.0, u), fstop=4.0)

    # ==================== LOKASI 4: GORONG-GORONG MESIN — STORY TURN! (00:26 - 00:38) ====================
    if t < 28.8:
        u = exp_ease_in_out((t - 26.0) / 2.8, 6.5)
        eye = lerp3((0.0, -9.2, 42.2), (0.8, -14.8, 34.4), u)
        tgt = lerp3((0.0, -14.5, 44.5), (0.0, -16.8, 46.5), u)
        return CameraFrameSpec("CAM 16", eye, tgt, lerp(18.0, 20.0, u), lerp(0.0, -6.0, u), fstop=5.0)
    if t < 31.4:
        u = (t - 28.8) / 2.6
        swing = math.sin(u * math.pi * 1.35) * 4.2
        eye = (swing, lerp(-14.2, -16.2, u) + abs(swing) * 0.25, lerp(36.0, 39.2, u))
        return CameraFrameSpec("CAM 17", eye, key_p, 19.0, -swing * 2.5, fstop=4.2)
    if t < 34.0:
        u = snappy_dolly_overshoot((t - 31.4) / 1.2, overshoot=0.06)
        shake = math.exp(-max(0.0, t - 31.9) * 4.5) * 0.12 if t >= 31.9 else 0.0
        sh_x, sh_y = math.sin(t * 75.0) * shake, math.cos(t * 92.0) * shake
        eye = add3(lerp3((1.8, -15.8, 38.0), (0.42, -16.75, 40.85), clamp(u)), (sh_x, sh_y, 0.0))
        tgt = (sh_x * 0.4, -17.0 + sh_y * 0.4, 43.0)
        return CameraFrameSpec("CAM 18", eye, tgt, 21.0, sh_x * 20.0, fstop=2.2)
    if t < 38.0:
        # 2-tahap kamera bebas tembus dinding: melewati portal lorong (z=58) lalu spiral lurus naik di dalam cerobong terbuka (z=62)!
        if t < 35.2:
            u1 = smoothstep((t - 34.0) / 1.2)
            eye = (lerp(0.42, 0.0, u1), lerp(-16.75, -14.8, u1), lerp(40.85, 60.4, u1))
            tgt = (0.0, lerp(-16.8, -12.0, u1), lerp(43.5, 62.0, u1))
            return CameraFrameSpec("CAM 19", eye, tgt, 18.0, lerp(0.0, 14.0, u1), fstop=4.5)
        u2 = (t - 35.2) / 2.8
        ang = u2 * math.pi * 2.4
        r = lerp(1.6, 1.45, u2)
        y_cam = lerp(-14.8, 9.6, exp_ease_in_out(u2, 4.0))
        return CameraFrameSpec("CAM 19", (math.cos(ang) * r, y_cam, 62.0 + math.sin(ang) * r), (0.0, y_cam + 3.8, 62.0), 18.0, math.sin(ang) * 18.0, fstop=4.5)

    # ==================== LOKASI 5: STASIUN TREM LAYANG TERBUKA (00:38 - 00:49) ====================
    if t < 39.8:
        u = snappy_dolly_overshoot((t - 38.0) / 1.8, overshoot=0.04)
        return CameraFrameSpec("CAM 20", lerp3((0.0, 9.8, 62.0), (-2.6, 12.2, 66.5), clamp(u)), lerp3((0.0, 12.5, 78.0), (0.4, 12.4, 92.0), clamp(u)), 18.5, lerp(28.0, 0.0, clamp(u)), fstop=5.0)
    if t < 42.2:
        u = (t - 39.8) / 2.4
        z_tr = lerp(tram_z + 1.5, tram_z - 5.2, u)
        return CameraFrameSpec("CAM 21", (-6.8, 12.65, z_tr), (0.4, 12.25, tram_z + 0.6), 18.0, -3.5, fstop=4.8)
    if t < 43.8:
        u = whip_curve((t - 42.2) / 1.6)
        return CameraFrameSpec("CAM 22", (-3.2, 12.8, tram_z - 1.5), lerp3((0.2, 12.2, tram_z), key_p, u), 20.0, lerp(-3.5, 6.0, u), fstop=4.5)
    if t < 46.2:
        u = (t - 43.8) / 2.4
        bima_z = tram_z + lerp(-3.8, 4.4, u)
        return CameraFrameSpec("CAM 23", (lerp(-0.9, 0.7, u), 14.45, bima_z + 3.2), (0.0, 14.55, bima_z - 0.5), 18.5, lerp(6.0, -6.0, u), fstop=3.8)
    if t < 49.0:
        u = exp_ease_in_out((t - 46.2) / 2.8, 4.5)
        bima_leap = (0.0, 15.2 + math.sin(u * math.pi) * 4.2, lerp(tram_z + 5.2, 110.5, u))
        ang = math.radians(lerp(-15.0, 48.0, u))
        eye = add3(bima_leap, (math.sin(ang) * 4.6, lerp(-1.4, -0.5, u), -math.cos(ang) * 4.6))
        tgt = add3(bima_leap, (-0.95, 0.85, 2.2))
        return CameraFrameSpec("CAM 24", eye, tgt, 19.0, lerp(-6.0, 6.0, u), fstop=4.5)

    # ==================== LOKASI 6: WAJAH MENARA JAM UTAMA DI DERMAGA (00:49 - 00:58) ====================
    if t < 52.0:
        u = snappy_dolly_overshoot((t - 49.0) / 2.8, overshoot=0.05)
        return CameraFrameSpec("CAM 25", lerp3((2.8, 18.4, 111.5), (0.55, 19.35, 114.85), clamp(u)), lerp3((0.2, 19.1, 116.8), (0.0, 19.5, 117.2), clamp(u)), 21.0, lerp(5.0, 0.0, clamp(u)), fstop=2.4)
    if t < 54.5:
        u = exp_ease_in_out((t - 52.0) / 2.5, 4.5)
        return CameraFrameSpec("CAM 26", lerp3((0.55, 19.35, 114.85), (-11.5, 20.5, 86.0), u), lerp3((0.0, 19.5, 117.2), (4.5, 15.2, 114.0), u), 18.0, lerp(0.0, -3.0, u), fstop=6.4)
    if t < 56.4:
        u = snappy_dolly_overshoot((t - 54.5) / 1.5, overshoot=0.055)
        return CameraFrameSpec("CAM 27", lerp3((-1.4, 17.5, 111.8), (-0.32, 16.92, 113.85), clamp(u)), lerp3((-0.18, 16.6, 116.25), (-0.24, 16.22, 116.25), clamp(u)), 22.0, lerp(-2.0, 3.5, clamp(u)), fstop=2.4)

    # [CAM 28] Seamless Loop Whip-Pan Dive mengikuti Kunci Perak menembus celah 2 roda gigi -> kembali ke [CAM 01]!
    u = exp_ease_in_out((t - 56.4) / 1.6, 6.5)
    silver_y = lerp(15.6, 12.6, u * u)
    return CameraFrameSpec("CAM 28", lerp3((-0.15, 15.8, 114.4), (0.0, 13.15, 115.1), u), (0.0, silver_y, 117.6), 18.0, lerp(5.0, -4.0, u), fstop=3.6)


def build_and_animate_virtual_camera() -> "bpy.types.Object":
    """Buat kamera 9:16 18-22mm di Blender dan keyframe seluruh 28 gerakan kamera di 1..1740 frame."""
    import bpy  # type: ignore
    from mathutils import Matrix, Vector  # type: ignore

    from .mesh_utils import get_or_create_collection, link_object

    col = get_or_create_collection("Camera_Rig")
    cam_data = bpy.data.cameras.new("VirtualOneTake_CamData")
    cam_data.sensor_fit = "VERTICAL"
    cam_data.sensor_height = SENSOR_HEIGHT_MM
    cam_data.clip_start = 0.08
    cam_data.clip_end = 450.0
    cam_data.dof.use_dof = True

    cam_obj = bpy.data.objects.new("VirtualOneTake_Camera", cam_data)
    cam_obj.rotation_mode = "QUATERNION"
    link_object(cam_obj, col)
    bpy.context.scene.camera = cam_obj

    prev_q = None
    world_up = Vector((0.0, 0.0, 1.0))

    # Keyframe per frame untuk kurva exponential ease-in-out, overshoot, shake & 360° barrel roll 100% presisi!
    for fr in range(1, TOTAL_FRAMES + 1):
        t = frame_to_sec(fr)
        spec = eval_camera_world(t)
        eye_b = Vector(w_to_b(*spec.eye_w))
        tgt_b = Vector(w_to_b(*spec.tgt_w))

        fwd_vec = tgt_b - eye_b
        dist = max(0.25, float(fwd_vec.length))
        fwd = fwd_vec.normalized()
        up_ref = world_up if abs(fwd.dot(world_up)) < 0.992 else Vector((0.0, 1.0, 0.0))
        right = fwd.cross(up_ref).normalized()
        up = right.cross(fwd).normalized()

        rrad = math.radians(spec.roll_deg)
        cr, sr = math.cos(rrad), math.sin(rrad)
        r_rot = right * cr + up * sr
        u_rot = -right * sr + up * cr

        rot_mat = Matrix((
            (r_rot.x, u_rot.x, -fwd.x),
            (r_rot.y, u_rot.y, -fwd.y),
            (r_rot.z, u_rot.z, -fwd.z),
        ))
        q = rot_mat.to_quaternion()
        if prev_q is not None and q.dot(prev_q) < 0.0:
            q = -q
        prev_q = q.copy()

        cam_obj.location = eye_b
        cam_obj.rotation_quaternion = q
        cam_obj.keyframe_insert(data_path="location", frame=fr)
        cam_obj.keyframe_insert(data_path="rotation_quaternion", frame=fr)

        cam_data.lens = float(spec.focal_mm)
        cam_data.dof.focus_distance = dist
        cam_data.dof.aperture_fstop = float(spec.fstop)
        if fr == 1 or fr % 3 == 0 or fr == TOTAL_FRAMES:
            cam_data.keyframe_insert(data_path="lens", frame=fr)
            cam_data.dof.keyframe_insert(data_path="focus_distance", frame=fr)
            cam_data.dof.keyframe_insert(data_path="aperture_fstop", frame=fr)

    return cam_obj
