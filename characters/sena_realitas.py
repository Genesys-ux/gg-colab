"""
SenaRealitasCharacter — Komponen Karakter 2.5D Ringan (Shared Engine • ~65 baris)
Character : Dokter Sena (35 • Spesialis ICU)
Prompt    : Dokter spesialis ICU 35 tahun tinggi postur tegak presisi, jas dokter putih panjang di atas kemeja biru gelap, kacamata bening bingkai tipis, rambut klimis disisir rapi ke belakang, ekspresi lelah dan empatik
Requires  : character_engine_25d.py (simpan 1x di folder proyek yang sama)

Cara pakai (Free-Rig terbuka — tidak mengunci pose/ekspresi!):
    from sena_realitas_character import SenaRealitasCharacter
    char = SenaRealitasCharacter(scale=3, fps=30)

    # 1) Bebas atur badan, kepala, tangan IK, mulut & ekspresi sendiri (tanpa preset terkunci):
    img = char.render_pil(
        frame=15, animation="free", angle=20,
        pelvis_y=10, torso_lean_deg=6, head_tilt_deg=-5,
        right_hand_target=(82, 175, 34), mouth_open=0.65, eyes="suspicious",
    )

    # 2) Campur layer bebas (mis. lari sambil panik / jalan sambil bicara & bersedekap):
    img = char.render_pil(frame=15, animation="walk", arm_pose="crossed", mouth_open=0.5, eyes="smug")
    img = char.render_pil(frame=15, animation="talk", pose="think", gesture_energy=0.8)
"""

from __future__ import annotations

from typing import Any, Dict

import os as _os, sys as _sys
if _os.path.dirname(_os.path.abspath(__file__)) not in _sys.path:
    _sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))

from character_engine_25d import (
    BaseCharacter25D,
    Easing,
    StoryboardScene,
    Vec3,
    extract_lipsync_curve,
    interpolate,
    render_character_demo,
    run_character_cli,
    spring,
)
from detik75_rig_addons import Detik75CharacterBase

CHARACTER_CONFIG: Dict[str, Any] = {
    "name": "Dokter Sena (35 • Spesialis ICU)",
    "prompt": "Dokter spesialis ICU 35 tahun tinggi postur tegak presisi, jas dokter putih panjang di atas kemeja biru gelap, kacamata bening bingkai tipis, rambut klimis disisir rapi ke belakang, ekspresi lelah dan empatik",
    "headShape": "tall",
    "ears": True,
    "earPencil": False,
    "skinColor": "#F4E4DA",
    "blushColor": "#D6B8B0",
    "irisColor": "#2B4C66",
    "eyes": "chill",
    "eyebrows": "worried",
    "nose": "none",
    "mouth": "flat",
    "beard": "none",
    "faceAccessory": "round_glasses",
    "sweatDrop": False,
    "blush": False,
    "angerVein": False,
    "eyeGazeX": -0.1,
    "eyeGazeY": 0.08,
    "hat": "none",
    "hatPrimary": "#F5F8FC",
    "hatAccent": "#2E7CE6",
    "hatTilt": 0,
    "hatLiftY": 0,
    "loupeOpen": True,
    "backHair": "side_part",
    "hairColor": "#161922",
    "outfit": "lab_coat",
    "robeColor": "#F5F8FC",
    "innerColor": "#1B365D",
    "sashColor": "#122440",
    "trimColor": "#2E7CE6",
    "beltStyle": "plain",
    "cape": "none",
    "capeColor": "#F5F8FC",
    "emblem": "none",
    "pose": "think",
    "prop": "none",
    "limbColor": "#1E2533",
    "groundShadow": True,
    "outlineShadow": 1.35,
    "outlineLit": 1,
    "rimIntensity": 0.45,
    "shadowDepth": 1.5,
    "customLayers": [
        {
            "layer": "head",
            "facing": "front",
            "z_offset": 48,
            "type": "line",
            "x": 77,
            "y": 151,
            "x2": 89,
            "y2": 151.5,
            "stroke": "#9B7C76",
            "lineWidth": 1.3,
            "opacity": 0.42,
        },
        {
            "layer": "head",
            "facing": "front",
            "z_offset": 48,
            "type": "line",
            "x": 112,
            "y": 149,
            "x2": 124,
            "y2": 149.5,
            "stroke": "#9B7C76",
            "lineWidth": 1.3,
            "opacity": 0.42,
        },
        {
            "layer": "torso",
            "facing": "front",
            "z_offset": 44,
            "type": "rect",
            "x": 93,
            "y": 202,
            "w": 22,
            "h": 26,
            "radius": 2,
            "fill": "#1B365D",
            "opacity": 0.92,
        },
        {
            "layer": "torso",
            "facing": "front",
            "z_offset": 46,
            "type": "rect",
            "x": 71,
            "y": 235,
            "w": 16,
            "h": 22,
            "radius": 2.5,
            "fill": "#FFFFFF",
            "stroke": "#2B3648",
            "lineWidth": 1.5,
            "opacity": 0.96,
        },
        {
            "layer": "torso",
            "facing": "front",
            "z_offset": 47,
            "type": "rect",
            "x": 72.5,
            "y": 236.5,
            "w": 13,
            "h": 5,
            "radius": 1,
            "fill": "#2574D9",
            "opacity": 0.96,
        },
    ],
}


class SenaRealitasCharacter(Detik75CharacterBase):
    """Karakter 2.5D Dokter Sena (35 • Spesialis ICU) — Open Free-Rig, Layered IK, 360° Turntable."""

    DEFAULT_CONFIG: Dict[str, Any] = CHARACTER_CONFIG
    DEFAULT_ANIMATION = "free"
    DEFAULT_ANGLE: float = 0.0
    DEFAULT_FPS: int = 30
    DEFAULT_SCALE: float = 3.0
    DEFAULT_TIME_OFFSET: float = 2.69  # Fase unik otomatis agar multi-karakter tidak bergerak seragam
    DEFAULT_SQUASH_X: float = 0.96
    DEFAULT_SQUASH_Y: float = 1.04

    def _build_overrides(self, **kwargs: Any) -> Dict[str, Any]:
        kwargs.setdefault("squash_x", self.DEFAULT_SQUASH_X)
        kwargs.setdefault("squash_y", self.DEFAULT_SQUASH_Y)
        return super()._build_overrides(**kwargs)


def render_demo_scene(output_path: str = "demo.mp4", width: int = 720, height: int = 1280, fps: int = 30, scale: float = 2.5, audio_path: str | None = None) -> str:
    return render_character_demo(SenaRealitasCharacter, output_path=output_path, width=width, height=height, fps=fps, scale=scale, audio_path=audio_path)


if __name__ == "__main__":
    run_character_cli(SenaRealitasCharacter)
