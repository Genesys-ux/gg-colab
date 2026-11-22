"""
Konfigurasi Global Produksi 3D Blender (bpy) + EEVEE Next.
Format: YouTube Shorts 9:16 Vertikal | 58 Detik @ 30fps (1.740 Frame) | 6 Lokasi | 28 Gerakan Kamera.
"""

from __future__ import annotations

import os
from typing import Dict, List, Tuple

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS_DIR = os.path.join(PROJECT_ROOT, "assets")
PBR_TEXTURES_DIR = os.path.join(ASSETS_DIR, "textures")
CUSTOM_MODELS_DIR = os.path.join(ASSETS_DIR, "models")
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "output")
PREVIEW_DIR = os.path.join(PROJECT_ROOT, "previews", "blender_eevee")
AUDIO_MASTER_WAV = os.path.join(PROJECT_ROOT, "audio", "output", "narration_master_58s.wav")
AUDIO_MASTER_MP3 = os.path.join(PROJECT_ROOT, "audio", "output", "narration_master_58s.mp3")

FPS = 30
DURATION_SEC = 58.0
TOTAL_FRAMES = int(round(DURATION_SEC * FPS))  # 1740 frames

# Resolusi default (bisa dioverride via CLI --width / --height)
DEFAULT_WIDTH = 720
DEFAULT_HEIGHT = 1280
FULLHD_WIDTH = 1080
FULLHD_HEIGHT = 1920

# Sensor full-frame 9:16 vertikal (tinggi 36mm, lebar 20.25mm -> lensa 18-22mm akurat)
SENSOR_HEIGHT_MM = 36.0

# 12 Keyframe Hero Preview untuk penilaian pengguna sebelum render 1.740 frame
HERO_PREVIEW_SHOTS: List[Tuple[str, float, str, str]] = [
    # Sheet 1: Fase 1 (Low Sun & Blue Shade — Lokasi 1 & 2)
    ("shot_01_cam01_bengkel_dolly.png", 0.28, "[CAM 01] 00:00.3 • Lokasi 1", "Dolly-in menembus celah 2 roda gigi ke Kunci Emas & Bima"),
    ("shot_02_cam03_cangkir_teh.png", 5.15, "[CAM 03] 00:05.2 • Lokasi 1", "Fast crane drop kunci memantul dari cangkir teh porselen"),
    ("shot_03_cam07_tenda_pasar.png", 11.75, "[CAM 07] 00:11.8 • Lokasi 2", "Elastic bounce di kanopi kain merah Pasar Rempah bertingkat"),
    ("shot_04_cam09_bubuk_kunyit.png", 15.10, "[CAM 09] 00:15.1 • Lokasi 2", "Crash dolly menerobos ledakan bubuk kunyit + pedagang terjungkal"),
    # Sheet 2: Akhir Fase 1 (Lokasi 3 Gang Kafe) & Fase 2 Story Turn (Lokasi 4 Gorong-Gorong)
    ("shot_05_cam12_oren_snap.png", 21.05, "[CAM 12] 00:21.1 • Lokasi 3", 'Whip-pan mengunci "Oren" & cakar lebar di gang kafe teduh'),
    ("shot_06_cam14_cobblestone_skim.png", 23.85, "[CAM 14] 00:23.9 • Lokasi 3", "Inverted low-skim cobblestone basah + Bima meluncur lutut"),
    ("shot_07_cam16_gorong_reveal.png", 28.10, "[CAM 16] 00:28.1 • Lokasi 4", "STORY TURN! Indigo-Emerald + tungku oranye & roda gigi raksasa"),
    ("shot_08_cam18_poros_klak.png", 32.35, "[CAM 18] 00:32.4 • Lokasi 4", "KLAK! Crash-zoom kunci menancap poros + percikan biru-zamrud"),
    # Sheet 3: Fase 3 Klimaks (Lokasi 5 Stasiun Trem Crimson) & Finale (Lokasi 6 Menara Jam Twilight)
    ("shot_09_cam21_trem_parallax.png", 41.35, "[CAM 21] 00:41.4 • Lokasi 5", "CLIMAX! Lateral tracking trem merah mundur + parallax pilar besi"),
    ("shot_10_cam24_lompat_matahari.png", 47.60, "[CAM 24] 00:47.6 • Lokasi 5", "Slow-mo 20% orbit 90° lompatan Bima di depan matahari crimson"),
    ("shot_11_cam26_twilight_shockwave.png", 53.15, "[CAM 26] 00:53.2 • Lokasi 6", "Shockwave pull-back Frozen Violet-Gold Twilight + cyan rim!"),
    ("shot_12_cam27_twist_kunci_perak.png", 55.85, "[CAM 27] 00:55.9 • Lokasi 6", "Twist komedi! Snap-zoom saku robek Bima & Kunci Perak jatuh"),
]

# Daftar tekstur PBR CC0 opsional dari Poly Haven (diunduh otomatis di Colab jika diaktifkan)
POLYHAVEN_PBR_ASSETS: Dict[str, str] = {
    "oak_wood": "wood_planks_dirt",
    "peeling_plaster": "plastered_wall_04",
    "cobblestone": "cobblestone_floor_08",
    "woven_fabric": "burlap_fabric_01",
    "oxidized_metal": "rusty_metal_02",
}


def sec_to_frame(t_sec: float) -> int:
    return max(1, min(TOTAL_FRAMES, int(round(t_sec * FPS)) + 1))


def frame_to_sec(frame: int) -> float:
    return max(0.0, (frame - 1) / float(FPS))


def w_to_b(x: float, y_up: float, z_fwd: float) -> Tuple[float, float, float]:
    """Konversi koordinat (X-kanan, Y-atas, Z-maju) ke sistem Z-Up Blender (X-kanan, Y-maju, Z-atas)."""
    return (float(x), float(z_fwd), float(y_up))
