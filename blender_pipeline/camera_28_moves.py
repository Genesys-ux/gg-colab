"""
Koreografi 28 Gerakan Kamera Virtual 3D ([CAM 01] – [CAM 28]) untuk "DETIK KE-75"
Memenuhi seluruh aturan wajib `3d-cinematic-animation-director`:
  - > 25 gerakan kamera (28 kamera dinamis melintasi 6 lokasi 3D!)
  - Continuous 3D virtual camera di tiap babak + Match-Cut 0,5 detik presisi di Babak III
  - Travel camera dengan 3D parallax kuat, snappy speed-ramped dolly-in + subtle overshoot,
    whip-pan transitions, zoom transitions, exponential ease-in-out, dan wide-angle lens (18-24mm).
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import List, Tuple

from .config import (
    CAKE_POS_W,
    FPS,
    ICU_BED_POS_W,
    LOC1_FLOOR_Y,
    LOC3_ORIGIN,
    LOC4_FLOOR_Y,
    LOC5_FLOOR_Y,
    LOC6_FLOOR_Y,
    PORTAL_DOOR_Z,
    SENSOR_HEIGHT_MM,
    TOTAL_FRAMES,
    frame_to_sec,
    w_to_b,
)


def clamp(v: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, float(v)))


def lerp(a: float, b: float, t: float) -> float:
    return float(a + (b - a) * t)


def lerp3(a: Tuple[float, float, float], b: Tuple[float, float, float], t: float) -> Tuple[float, float, float]:
    return (lerp(a[0], b[0], t), lerp(a[1], b[1], t), lerp(a[2], b[2], t))


def smoothstep(t: float) -> float:
    u = clamp(t)
    return u * u * (3.0 - 2.0 * u)


def exp_ease_in_out(t: float, power: float = 7.2) -> float:
    u = clamp(t)
    if u <= 0.0:
        return 0.0
    if u >= 1.0:
        return 1.0
    if u < 0.5:
        return 0.5 * math.pow(2.0, power * (2.0 * u - 1.0))
    return 1.0 - 0.5 * math.pow(2.0, -power * (2.0 * u - 1.0))


def snappy_overshoot(t: float, overshoot: float = 0.055) -> float:
    """Snappy speed-ramped dolly dengan perlambatan halus & subtle overshoot di akhir."""
    u = clamp(t)
    if u <= 0.0:
        return 0.0
    if u >= 1.0:
        return 1.0
    base = (1.0 - math.exp(-7.0 * u)) / (1.0 - math.exp(-7.0))
    ring = math.sin(u * math.pi * 1.5) * math.exp(-4.5 * u) * overshoot * 4.0
    return base + ring * (1.0 - u)


@dataclass
class CameraShotSpec:
    cam_id: int
    t0: float
    t1: float
    pos0: Tuple[float, float, float]
    pos1: Tuple[float, float, float]
    tgt0: Tuple[float, float, float]
    tgt1: Tuple[float, float, float]
    lens0: float = 20.0
    lens1: float = 20.0
    roll0: float = 0.0
    roll1: float = 0.0
    curve: str = "exp"  # 'exp' | 'overshoot' | 'linear' | 'smooth'


# ============================================================================
# DEFINISI 28 SHOT KAMERA KONTINU & MATCH-CUT (00:00.0 – 01:15.0)
# ============================================================================
BX, BY, BZ = ICU_BED_POS_W
WX, WY, WZ = LOC3_ORIGIN
RFY = LOC4_FLOOR_Y

CAMERA_28_SHOTS: List[CameraShotSpec] = [
    # --- BABAK I: PENGEJARAN DI KERETA MAGLEV (Lokasi 1 & 2, 00:00 – 00:18) ---
    # CAM 01 (00:00–00:02.0): 2-SECOND HOOK! Extreme close-up mata Raka & luka alis kiri -> mulai mundur
    CameraShotSpec(1, 0.0, 2.0, (0.04, 1.48, 3.15), (0.08, 1.44, 2.45), (0.0, 1.48, 4.05), (0.0, 1.35, 5.2), 26.0, 22.0, -3.0, 6.0, "overshoot"),
    # CAM 02 (00:02.0–00:06.0): Whip-pan pullback tracking Raka berlari mendekap koper di lorong Maglev miring ekstrem!
    CameraShotSpec(2, 2.0, 6.0, (0.08, 1.44, 2.45), (-0.32, 1.15, 9.2), (0.0, 1.35, 5.2), (0.0, 1.22, 13.5), 22.0, 18.0, 6.0, -11.5, "exp"),
    # CAM 03 (00:06.0–00:08.5): Tracking rendah ke depan: Bima berzirah taktis memblokir pintu sambungan gerbong!
    CameraShotSpec(3, 6.0, 8.5, (-0.32, 0.72, 11.5), (0.28, 0.85, 16.5), (0.0, 1.25, 22.8), (0.0, 1.30, 23.2), 18.0, 19.0, -11.5, 5.5, "overshoot"),
    # CAM 04 (00:08.5–00:10.2): Whip-pan 180 ke belakang: Sena mengejar mengacungkan pemindai cahaya biru tajam!
    CameraShotSpec(4, 8.5, 10.2, (0.28, 1.18, 18.4), (-0.25, 1.22, 19.2), (-0.1, 1.32, 13.0), (0.0, 1.34, 15.2), 19.0, 21.0, 5.5, -6.0, "overshoot"),
    # CAM 05 (00:10.2–00:11.8): Bullet-time! Emphasis zoom ke Nenek Maya bersyal kuning menjentikkan cincin emas ke udara
    CameraShotSpec(5, 10.2, 11.8, (0.15, 1.25, 16.2), (0.35, 1.34, 17.5), (1.15, 1.18, 17.8), (0.42, 1.48, 18.8), 21.0, 26.0, -6.0, 2.0, "exp"),
    # CAM 06 (00:11.8–00:13.4): Snappy dolly mengikuti Raka menangkap cincin & menempelkannya ke tombol darurat pintu merah
    CameraShotSpec(6, 11.8, 13.4, (0.22, 1.28, 21.0), (-0.18, 1.26, 27.2), (0.15, 1.28, 26.5), (0.55, 1.24, PORTAL_DOOR_Z), 24.0, 19.0, 2.0, -4.0, "overshoot"),
    # CAM 07 (00:13.4–00:16.2): Pintu kereta terbuka ke langit badai; Raka melompat & kamera ikut terjun menembus portal!
    CameraShotSpec(7, 13.4, 16.2, (-0.18, 1.26, 27.2), (0.0, 1.45, 31.2), (0.0, 1.35, PORTAL_DOOR_Z + 1.5), (0.0, 1.30, 34.0), 19.0, 17.0, -4.0, 14.0, "exp"),
    # CAM 08 (00:16.2–00:18.0): Freefall dive mendarat ke Atap Badai Apex Tower
    CameraShotSpec(8, 16.2, 18.0, (0.0, RFY + 6.8, 52.5), (-0.45, RFY + 1.45, 55.8), (0.0, RFY + 1.0, 59.5), (0.0, RFY + 0.95, 59.8), 17.0, 19.0, 14.0, -5.0, "overshoot"),

    # --- BABAK II: KEPUNGAN DI ATAP BADAI APEX TOWER (Lokasi 3 & 4, 00:18 – 00:46) ---
    # CAM 09 (00:18.0–00:21.5): Low tracking Raka berguling di genangan air hujan atap; garis laser merah menari di dada
    CameraShotSpec(9, 18.0, 21.5, (-0.45, RFY + 0.85, 56.2), (0.35, RFY + 1.18, 57.6), (0.0, RFY + 0.95, 60.2), (0.0, RFY + 1.15, 60.5), 19.0, 21.0, -5.0, 3.0, "smooth"),
    # CAM 10 (00:21.5–00:23.2): Snappy whip-zoom melintasi jurang badai dari dada Raka menuju Menara Air seberang!
    CameraShotSpec(10, 21.5, 23.2, (0.35, RFY + 1.4, 58.0), (14.2, WY + 1.35, WZ - 1.4), (8.0, WY + 1.0, WZ), (WX - 1.1, WY + 1.25, WZ - 0.2), 20.0, 26.0, 3.0, -6.0, "exp"),
    # CAM 11 (00:23.2–00:28.0): Close-up sinematik Kira di Menara Air (Lokasi 3) mengunci teropong dengan mata berkaca-kaca
    CameraShotSpec(11, 23.2, 28.0, (WX - 2.85, WY + 1.32, WZ - 1.15), (WX - 2.35, WY + 1.36, WZ - 0.85), (WX - 1.05, WY + 1.28, WZ - 0.15), (WX - 1.05, WY + 1.32, WZ - 0.15), 26.0, 29.0, -2.0, 1.5, "overshoot"),
    # CAM 12 (00:28.0–00:31.2): Whip-back ke Atap (Lokasi 4): pintu merah surealis meledak terbuka, Bima & Sena melompat keluar!
    CameraShotSpec(12, 28.0, 31.2, (-2.2, RFY + 1.35, 61.5), (-1.6, RFY + 1.25, 62.8), (0.0, RFY + 1.35, 56.0), (0.0, RFY + 1.25, 58.5), 18.5, 19.5, 7.0, -3.0, "overshoot"),
    # CAM 13 (00:31.2–00:34.6): Orbit parallax 120 derajat mengelilingi Raka yang terpojok di tepi atap dikepung Bima & Sena
    CameraShotSpec(13, 31.2, 34.6, (-2.6, RFY + 1.45, 62.5), (2.4, RFY + 1.38, 63.2), (0.0, RFY + 1.22, 61.0), (0.0, RFY + 1.25, 61.2), 19.5, 20.0, -3.0, 4.0, "exp"),
    # CAM 14 (00:34.6–00:38.0): Dolly-in intens Sena mengarahkan sinar biru menyilaukan tepat ke mata Raka!
    CameraShotSpec(14, 34.6, 38.0, (1.35, RFY + 1.35, 60.0), (0.42, RFY + 1.38, 60.5), (-0.2, RFY + 1.32, 61.8), (0.0, RFY + 1.36, 62.0), 20.0, 24.0, 4.0, -4.0, "overshoot"),
    # CAM 15 (00:38.0–00:39.8): KEJUTAN #2! Tembakan laser menghantam koper; slow-mo kamera turun mengikuti koper terbuka
    CameraShotSpec(15, 38.0, 39.8, (0.65, RFY + 1.25, 59.8), (0.32, RFY + 0.48, 59.9), (0.0, RFY + 0.85, 61.4), (CAKE_POS_W[0], CAKE_POS_W[1] + 0.18, CAKE_POS_W[2]), 22.0, 25.0, -4.0, 0.0, "overshoot"),
    # CAM 16 (00:39.8–00:42.4): Macro hero shot kue ulang tahun kecil & api lilin oranye tenang sementara rintik hujan naik ke langit!
    CameraShotSpec(16, 39.8, 42.4, (0.28, RFY + 0.36, 59.85), (-0.28, RFY + 0.42, 59.90), (CAKE_POS_W[0], CAKE_POS_W[1] + 0.22, CAKE_POS_W[2]), (CAKE_POS_W[0], CAKE_POS_W[1] + 0.24, CAKE_POS_W[2]), 25.0, 26.0, 0.0, 2.0, "smooth"),
    # CAM 17 (00:42.4–00:44.5): Tilt-up ke Raka yang meraih lilin sambil menua real-time (26 -> 78 thn) di tengah serpihan kristal!
    CameraShotSpec(17, 42.4, 44.5, (-0.28, RFY + 0.65, 60.1), (0.0, RFY + 1.32, 60.4), (0.0, RFY + 1.15, 62.2), (0.0, RFY + 1.35, 62.2), 24.0, 22.0, 2.0, -2.0, "exp"),
    # CAM 18 (00:44.5–00:46.0): Pull-back dramatis gedung pencakar langit pecah menjadi jutaan serpihan cahaya putih!
    CameraShotSpec(18, 44.5, 46.0, (0.0, RFY + 1.32, 60.4), (0.0, RFY + 2.25, 56.8), (0.0, RFY + 1.35, 62.2), (0.0, RFY + 1.5, 62.0), 22.0, 18.0, -2.0, 8.0, "exp"),

    # --- BABAK III: MATCH-CUT CEPAT KE RUANG ICU 404 & TWIST KORIDOR EMAS (Lokasi 5 & 6, 00:46 – 01:15) ---
    # CAM 19 (00:46.0–00:47.5): MATCH-CUT #1! Pemindai biru -> Senter penlight medis Dokter Sena memeriksa mata pasien di ICU
    CameraShotSpec(19, 46.0, 47.5, (BX + 0.15, LOC5_FLOOR_Y + 1.42, BZ - 1.15), (BX + 0.28, LOC5_FLOOR_Y + 1.45, BZ - 0.95), (BX + 0.45, LOC5_FLOOR_Y + 1.38, BZ + 0.15), (BX + 0.42, LOC5_FLOOR_Y + 1.36, BZ + 0.15), 25.0, 24.0, 0.0, 0.0, "overshoot"),
    # CAM 20 (00:47.5–00:49.0): MATCH-CUT #2! Laser merah -> Layar monitor EKG & Kira menangis menggenggam tangan ayahnya
    CameraShotSpec(20, 47.5, 49.0, (BX + 0.45, LOC5_FLOOR_Y + 1.42, BZ - 0.85), (BX + 0.15, LOC5_FLOOR_Y + 1.28, BZ - 1.25), (BX + 0.95, LOC5_FLOOR_Y + 1.48, BZ + 0.62), (BX + 0.55, LOC5_FLOOR_Y + 1.18, BZ - 0.10), 25.0, 22.0, 0.0, -1.5, "overshoot"),
    # CAM 21 (00:49.0–00:50.8): MATCH-CUT #3! Teriakan Bima -> Putra sulung Raka di sisi ranjang berbisik lirih penuh haru
    CameraShotSpec(21, 49.0, 50.8, (BX - 0.15, LOC5_FLOOR_Y + 1.28, BZ - 1.20), (BX - 0.35, LOC5_FLOOR_Y + 1.32, BZ - 1.05), (BX - 0.68, LOC5_FLOOR_Y + 1.26, BZ + 0.15), (BX - 0.62, LOC5_FLOOR_Y + 1.24, BZ + 0.18), 23.0, 22.0, -1.5, 1.0, "overshoot"),
    # CAM 22 (00:50.8–00:52.8): MATCH-CUT #4! Hujan badai -> Tetesan cairan infus bening jatuh perlahan
    CameraShotSpec(22, 50.8, 52.8, (BX - 0.62, LOC5_FLOOR_Y + 1.62, BZ - 0.25), (BX - 0.45, LOC5_FLOOR_Y + 1.48, BZ - 0.65), (BX - 0.85, LOC5_FLOOR_Y + 1.62, BZ + 0.55), (BX - 0.25, LOC5_FLOOR_Y + 1.25, BZ + 0.35), 26.0, 22.0, 0.0, 0.0, "smooth"),
    # CAM 23 (00:52.8–00:58.0): Pull-back emosional dari Kakek Raka (78) di ranjang ICU bersama Nenek Maya menggenggam tangannya
    CameraShotSpec(23, 52.8, 58.0, (BX + 0.05, LOC5_FLOOR_Y + 1.35, BZ - 0.95), (BX + 0.25, LOC5_FLOOR_Y + 1.68, BZ - 2.95), (BX, LOC5_FLOOR_Y + 1.15, BZ + 0.35), (BX, LOC5_FLOOR_Y + 1.18, BZ + 0.25), 22.0, 19.5, 0.0, 0.0, "exp"),
    # CAM 24 (00:58.0–01:02.0): Slow orbit lembut ke Nenek Maya & kue mungil di meja nakas saat flatline panjang terdengar
    CameraShotSpec(24, 58.0, 62.0, (BX + 0.25, LOC5_FLOOR_Y + 1.68, BZ - 2.95), (BX - 0.65, LOC5_FLOOR_Y + 1.32, BZ - 1.85), (BX, LOC5_FLOOR_Y + 1.18, BZ + 0.25), (BX - 0.65, LOC5_FLOOR_Y + 1.05, BZ + 0.05), 19.5, 22.0, 0.0, 0.0, "smooth"),
    # CAM 25 (01:02.0–01:05.2): KEJUTAN #4! Emphasis zoom ke cincin kawin emas bergetar di nakas dekat foto pernikahan -> EKG BEEP!
    CameraShotSpec(25, 62.0, 65.2, (BX - 0.85, LOC5_FLOOR_Y + 1.05, BZ - 1.15), (BX - 0.95, LOC5_FLOOR_Y + 0.94, BZ - 0.78), (BX - 1.05, LOC5_FLOOR_Y + 0.78, BZ - 0.12), (BX - 1.02, LOC5_FLOOR_Y + 0.80, BZ - 0.05), 24.0, 28.0, 0.0, 0.0, "overshoot"),
    # CAM 26 (01:05.2–01:08.2): Kakek Raka membuka mata tersenyum damai; kamera mulai bergeser (pan) ke kanan menuju jendela kaca
    CameraShotSpec(26, 65.2, 68.2, (BX + 0.15, LOC5_FLOOR_Y + 1.38, BZ - 1.75), (1.85, LOC5_FLOOR_Y + 1.48, BZ - 1.45), (BX, LOC5_FLOOR_Y + 1.18, BZ + 0.25), (4.8, LOC6_FLOOR_Y + 1.35, BZ + 0.4), 22.0, 21.0, 0.0, 0.0, "exp"),
    # CAM 27 (01:08.2–01:13.2): FINAL SHOT! Menembus kaca observasi ke Koridor Cahaya Keemasan: Raka Muda (26) & Maya Muda (25) menoleh tersenyum!
    CameraShotSpec(27, 68.2, 73.2, (1.85, LOC5_FLOOR_Y + 1.48, BZ - 1.45), (3.15, LOC5_FLOOR_Y + 1.45, BZ - 0.65), (5.8, LOC6_FLOOR_Y + 1.32, 111.5), (6.5, LOC6_FLOOR_Y + 1.35, 115.2), 21.0, 22.0, 0.0, 0.0, "smooth"),
    # CAM 28 (01:13.2–01:15.0): Tilt lembut ke jam dinding detik ke-15 / cahaya keemasan sebelum fade ke layar hitam "DETIK KE-75"
    CameraShotSpec(28, 73.2, 75.0, (3.15, LOC5_FLOOR_Y + 1.45, BZ - 0.65), (3.35, LOC5_FLOOR_Y + 1.52, BZ - 0.25), (6.5, LOC6_FLOOR_Y + 1.35, 115.2), (7.2, LOC6_FLOOR_Y + 1.42, 118.5), 22.0, 24.0, 0.0, 0.0, "smooth"),
]


def eval_camera_world(t_sec: float) -> Tuple[Tuple[float, float, float], Tuple[float, float, float], float, float, int]:
    """Evaluasi (cam_pos_w, target_pos_w, lens_mm, roll_deg, cam_id) pada detik t_sec (0..75)."""
    t = clamp(t_sec, 0.0, 75.0)
    chosen = CAMERA_28_SHOTS[-1]
    for sh in CAMERA_28_SHOTS:
        if t < sh.t1 or sh.cam_id == 28:
            chosen = sh
            break

    dur = max(1e-4, chosen.t1 - chosen.t0)
    raw_u = clamp((t - chosen.t0) / dur)
    if chosen.curve == "overshoot":
        u = snappy_overshoot(raw_u)
    elif chosen.curve == "exp":
        u = exp_ease_in_out(raw_u)
    elif chosen.curve == "smooth":
        u = smoothstep(raw_u)
    else:
        u = raw_u

    pos = lerp3(chosen.pos0, chosen.pos1, u)
    tgt = lerp3(chosen.tgt0, chosen.tgt1, u)
    lens = lerp(chosen.lens0, chosen.lens1, u)
    roll = lerp(chosen.roll0, chosen.roll1, u)

    # Tambahkan micro camera shake organik saat berlari di Maglev (0..13s) & badai petir atap (18..38s)
    if 1.8 <= t <= 13.2:
        pos = (pos[0] + math.sin(t * 17.0) * 0.025, pos[1] + abs(math.cos(t * 14.0)) * 0.02, pos[2])
    elif 18.0 <= t <= 38.0 and chosen.cam_id != 11:
        pos = (pos[0] + math.sin(t * 9.5) * 0.018, pos[1] + math.cos(t * 11.0) * 0.015, pos[2])

    return pos, tgt, lens, roll, chosen.cam_id


def build_and_animate_camera(start_frame: int = 1, end_frame: int = TOTAL_FRAMES):
    """Bangun kamera virtual 3D Blender & bake keyframe hanya pada rentang frame aktif."""
    import bpy  # type: ignore
    from mathutils import Quaternion, Vector  # type: ignore
    from .mesh_utils import get_or_create_collection, link_object

    col = get_or_create_collection("Camera_Rig_28Moves")
    cam_data = bpy.data.cameras.new("Cam_Detik75")
    cam_data.sensor_fit = "VERTICAL"
    cam_data.sensor_height = SENSOR_HEIGHT_MM
    cam_data.clip_start = 0.08
    cam_data.clip_end = 220.0
    if hasattr(cam_data, "dof"):
        cam_data.dof.use_dof = True
        cam_data.dof.aperture_fstop = 2.8

    cam_obj = bpy.data.objects.new("Cam_Detik75", cam_data)
    cam_obj.rotation_mode = "QUATERNION"
    link_object(cam_obj, col)
    bpy.context.scene.camera = cam_obj

    f_lo = max(1, start_frame - 1)
    f_hi = min(TOTAL_FRAMES, end_frame + 1)
    prev_q = None

    for fr in range(f_lo, f_hi + 1):
        t = frame_to_sec(fr)
        pos_w, tgt_w, lens_mm, roll_deg, _ = eval_camera_world(t)
        cb = Vector(w_to_b(*pos_w))
        tb = Vector(w_to_b(*tgt_w))
        vec = tb - cb
        dist = max(0.25, vec.length)
        q_look = vec.normalized().to_track_quat("-Z", "Y")
        q_roll = Quaternion((0.0, 0.0, 1.0), math.radians(roll_deg))
        q_final = q_look @ q_roll
        if prev_q is not None and prev_q.dot(q_final) < 0.0:
            q_final.negate()
        prev_q = q_final.copy()

        cam_obj.location = cb
        cam_obj.rotation_quaternion = q_final
        cam_obj.keyframe_insert(data_path="location", frame=fr)
        cam_obj.keyframe_insert(data_path="rotation_quaternion", frame=fr)

        cam_data.lens = float(lens_mm)
        cam_data.keyframe_insert(data_path="lens", frame=fr)
        if hasattr(cam_data, "dof"):
            cam_data.dof.focus_distance = dist
            cam_data.dof.keyframe_insert(data_path="focus_distance", frame=fr)

    return cam_obj
