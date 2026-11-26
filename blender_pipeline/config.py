"""
Konfigurasi Global Produksi Animasi 3D Sinematik "DETIK KE-75"
Durasi: 75.0 Detik @ 30 FPS (2.250 Frame) | Format 9:16 Vertikal (720x1280 / 1080x1920)
6 Lokasi Shoot 3D | 28 Gerakan Kamera Dinamis | 10 Varian Karakter Peran Ganda (Free-Rig)
"""
from __future__ import annotations

import os
from typing import Dict, List, Tuple

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHARACTERS_DIR = os.path.join(PROJECT_ROOT, "characters")
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "output")
EVAL_RENDERS_DIR = os.path.join(PROJECT_ROOT, "eval_renders")
AUDIO_OUT_DIR = os.path.join(PROJECT_ROOT, "audio", "output")
AUDIO_MASTER_WAV = os.path.join(AUDIO_OUT_DIR, "detik75_master_75s.wav")
AUDIO_MASTER_MP3 = os.path.join(AUDIO_OUT_DIR, "detik75_master_75s.mp3")

FPS = 30
DURATION_SEC = 75.0
TOTAL_FRAMES = int(round(DURATION_SEC * FPS))  # 2250 frames

DEFAULT_WIDTH = 720
DEFAULT_HEIGHT = 1280
FULLHD_WIDTH = 1080
FULLHD_HEIGHT = 1920
SENSOR_HEIGHT_MM = 36.0

# ============================================================================
# KOORDINAT DUNIA 6 LOKASI SHOOT (World: X-Right, Y-Up, Z-Forward)
# Dipisahkan bersih di ruang 3D agar tidak pernah saling bocor di kamera wide-angle!
# ============================================================================
LOC1_Z_RANGE = (-4.0, 22.0)      # Lokasi 1: Kabin Kereta Maglev "Express 09" (Y_floor = 0.0)
LOC1_FLOOR_Y = 0.02

LOC2_Z_RANGE = (22.0, 31.0)      # Lokasi 2: Sambungan Gerbong & Pintu Darurat Merah (Y_floor = 0.0)
LOC2_FLOOR_Y = 0.02
PORTAL_DOOR_Z = 29.8

LOC3_ORIGIN = (18.0, 44.0, 64.0) # Lokasi 3: Menara Air Baja Seberang (Kira Sniper Perch, Y_deck = 44.02)
LOC3_FLOOR_Y = 44.02

LOC4_Z_RANGE = (46.0, 74.0)      # Lokasi 4: Atap Badai Brutalist "Apex Tower" (Y_floor = 38.0)
LOC4_FLOOR_Y = 38.02
ROOFTOP_DOOR_Z = 56.0
CAKE_POS_W = (0.0, 38.06, 61.2)

LOC5_Z_RANGE = (104.0, 117.0)    # Lokasi 5: Ruang ICU Kamar 404 (X = -4.2..+3.6, Y_floor = 12.0)
LOC5_FLOOR_Y = 12.02
ICU_BED_POS_W = (-0.85, 12.02, 111.2)
ICU_MATTRESS_Y = 12.84
ICU_GLASS_X = 3.55               # Jendela kaca observasi besar di dinding kanan ICU

LOC6_X_RANGE = (3.65, 11.5)      # Lokasi 6: Koridor Cahaya Keemasan di balik kaca observasi ICU
LOC6_Z_RANGE = (102.0, 124.0)
LOC6_FLOOR_Y = 12.02

# ============================================================================
# 6 SCENE VIDEO KLIP EVALUASI UNTUK DINILAI PENGGUNA (Dirender Paralel di GitHub Actions)
# ============================================================================
EVAL_SCENE_CLIPS: List[Dict[str, object]] = [
    {
        "id": "scene_01_maglev_hook",
        "title": "Scene 1 (00:00.0–00:04.5) • Hook 2 Detik & Lari di Maglev Express 09",
        "start_sec": 0.0,
        "end_sec": 4.5,
    },
    {
        "id": "scene_02_portal_cincin",
        "title": "Scene 2 (00:09.6–00:14.4) • Bullet-Time Cincin Maya & Lompatan Portal Badai",
        "start_sec": 9.6,
        "end_sec": 14.4,
    },
    {
        "id": "scene_03_atap_sniper_kira",
        "title": "Scene 3 (00:19.6–00:24.4) • Atap Badai Petir & Whip-Zoom ke Sniper Kira",
        "start_sec": 19.6,
        "end_sec": 24.4,
    },
    {
        "id": "scene_04_koper_kue_aging",
        "title": "Scene 4 (00:38.6–00:43.6) • Kejutan Kue Lilin, Hujan Naik & Raka Menua",
        "start_sec": 38.6,
        "end_sec": 43.6,
    },
    {
        "id": "scene_05_matchcut_icu",
        "title": "Scene 5 (00:46.0–00:51.0) • Rangkaian Match-Cut Cepat ke Ruang ICU 404",
        "start_sec": 46.0,
        "end_sec": 51.0,
    },
    {
        "id": "scene_06_twist_koridor_emas",
        "title": "Scene 6 (01:05.4–01:10.8) • Kakek Raka Tersenyum -> Pan Jendela ke Koridor Emas",
        "start_sec": 65.4,
        "end_sec": 70.8,
    },
]

# 12 Keyframe Resolusi Tinggi untuk Contact Sheet Evaluasi Cepat
HERO_EVAL_KEYFRAMES: List[Tuple[str, float, str, str]] = [
    # Sheet 1: Babak I (Maglev Express 09 & Non-Euclidean Portal)
    ("kf_01_hook_mata_raka.png", 0.55, "[CAM 01] 00:00.6 • Lokasi 1", "2s Hook! Extreme close-up mata Raka & luka alis kiri"),
    ("kf_02_lari_maglev_miring.png", 3.40, "[CAM 02] 00:03.4 • Lokasi 1", "Whip-pan pullback Raka mendekap koper hitam-emas di Maglev miring"),
    ("kf_03_cincin_maya_bullettime.png", 10.60, "[CAM 05] 00:10.6 • Lokasi 2", "Maya bersyal kuning menjentikkan cincin emas di depan Bima & Sena"),
    ("kf_04_portal_terjun_badai.png", 14.40, "[CAM 07] 00:14.4 • Lokasi 2->4", "Pintu merah membuka langit petir; Raka terjun bebas ke badai"),
    # Sheet 2: Babak II (Atap Badai Apex Tower, Menara Air Kira & Kue Ulang Tahun)
    ("kf_05_atap_laser_merah.png", 20.60, "[CAM 09] 00:20.6 • Lokasi 4", "Raka di genangan beton reflektif dengan laser merah di dada"),
    ("kf_06_menara_sniper_kira.png", 24.20, "[CAM 11] 00:24.2 • Lokasi 3", "Whip-zoom ke Menara Air: Kira berjas hujan marun berkaca-kaca"),
    ("kf_07_kepungan_sinar_biru.png", 33.20, "[CAM 14] 00:33.2 • Lokasi 4", "Bima & Sena mengepung Raka di tepi atap; sinar pemindai biru tajam"),
    ("kf_08_kue_lilin_aging.png", 42.60, "[CAM 17] 00:42.6 • Lokasi 4", "Koper terbuka: lilin kue menyala tenang, hujan naik & Raka menua!"),
    # Sheet 3: Babak III (Match-Cut ICU Kamar 404 & Twist Koridor Emas)
    ("kf_09_matchcut_dokter_sena.png", 46.80, "[CAM 19] 00:46.8 • Lokasi 5", "Match-cut! Pemindai biru -> penlight medis Dokter Sena di ICU"),
    ("kf_10_keluarga_icu_404.png", 54.50, "[CAM 23] 00:54.5 • Lokasi 5", "Pull-back Kakek Raka (78) dikelilingi Maya, Bima & Kira menangis"),
    ("kf_11_cincin_beep_haru.png", 64.80, "[CAM 25] 01:04.8 • Lokasi 5", "Cincin emas bergetar di nakas dekat foto nikah; EKG kembali BEEP!"),
    ("kf_12_twist_koridor_emas.png", 70.80, "[CAM 27] 01:10.8 • Lokasi 6", "Final Twist! Raka Muda & Maya Muda tersenyum di Koridor Cahaya Emas"),
]


def sec_to_frame(t_sec: float) -> int:
    return max(1, min(TOTAL_FRAMES, int(round(t_sec * FPS)) + 1))


def frame_to_sec(frame: int) -> float:
    return max(0.0, (frame - 1) / float(FPS))


def w_to_b(x: float, y_up: float, z_fwd: float) -> Tuple[float, float, float]:
    """Konversi koordinat dunia (X-kanan, Y-atas, Z-maju) ke Blender Z-Up (X-kanan, Y-maju, Z-atas)."""
    return (float(x), float(z_fwd), float(y_up))
