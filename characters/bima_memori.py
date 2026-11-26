"""
BimaMemoriCharacter — Komponen Karakter 2.5D Ringan (Shared Engine • ~65 baris)
Character : Bima (42 • Penghadang Zirah)
Prompt    : Bima 42 tahun penghadang baju zirah besar bahu lebar kokoh seperti perisai, rompi pelindung komposit abu-abu gelap dengan bahu tebal, brewok tipis, alis tebal, kantung mata dalam, ekspresi tegas berteriak mengadang
Requires  : character_engine_25d.py (simpan 1x di folder proyek yang sama)

Cara pakai (Free-Rig terbuka — tidak mengunci pose/ekspresi!):
    from bima_memori_character import BimaMemoriCharacter
    char = BimaMemoriCharacter(scale=3, fps=30)

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
    "name": "Bima (42 • Penghadang Zirah)",
    "prompt": "Bima 42 tahun penghadang baju zirah besar bahu lebar kokoh seperti perisai, rompi pelindung komposit abu-abu gelap dengan bahu tebal, brewok tipis, alis tebal, kantung mata dalam, ekspresi tegas berteriak mengadang",
    "headShape": "wide",
    "ears": True,
    "earPencil": False,
    "skinColor": "#E9C8AD",
    "blushColor": "#C99E86",
    "irisColor": "#3B2B22",
    "eyes": "angry",
    "eyebrows": "thick_arch",
    "nose": "upturned_tiny",
    "mouth": "open_yell",
    "beard": "stubble",
    "faceAccessory": "none",
    "sweatDrop": False,
    "blush": False,
    "angerVein": False,
    "eyeGazeX": 0,
    "eyeGazeY": 0,
    "hat": "none",
    "hatPrimary": "#363C48",
    "hatAccent": "#94A0B4",
    "hatTilt": 0,
    "hatLiftY": 0,
    "loupeOpen": True,
    "backHair": "short",
    "hairColor": "#25262E",
    "outfit": "tactical_vest",
    "robeColor": "#363C48",
    "innerColor": "#232832",
    "sashColor": "#191C24",
    "trimColor": "#94A0B4",
    "beltStyle": "utility_belt",
    "cape": "none",
    "capeColor": "#2B303A",
    "emblem": "shield",
    "pose": "crossed",
    "prop": "none",
    "limbColor": "#1B1F28",
    "groundShadow": True,
    "outlineShadow": 1.35,
    "outlineLit": 1,
    "rimIntensity": 0.45,
    "shadowDepth": 1.5,
    "customLayers": [
        {
            "layer": "head",
            "facing": "front",
            "z_offset": 49,
            "type": "line",
            "x": 74,
            "y": 150.5,
            "x2": 92,
            "y2": 151.8,
            "stroke": "#6E4F47",
            "lineWidth": 2.1,
            "opacity": 0.62,
        },
        {
            "layer": "head",
            "facing": "front",
            "z_offset": 49,
            "type": "line",
            "x": 109,
            "y": 148.2,
            "x2": 127,
            "y2": 149.5,
            "stroke": "#6E4F47",
            "lineWidth": 2.1,
            "opacity": 0.62,
        },
        {
            "layer": "torso",
            "facing": "both",
            "z_offset": 0,
            "type": "rect",
            "x": 54,
            "y": 198,
            "w": 28,
            "h": 20,
            "radius": 6,
            "fill": "#2B303B",
            "stroke": "#171A22",
            "lineWidth": 2.4,
            "opacity": 0.98,
        },
        {
            "layer": "torso",
            "facing": "both",
            "z_offset": 0,
            "type": "rect",
            "x": 134,
            "y": 198,
            "w": 28,
            "h": 20,
            "radius": 6,
            "fill": "#434A59",
            "stroke": "#171A22",
            "lineWidth": 2.4,
            "opacity": 0.98,
        },
        {
            "layer": "torso",
            "facing": "front",
            "z_offset": 45,
            "type": "line",
            "x": 58,
            "y": 205,
            "x2": 78,
            "y2": 205,
            "stroke": "#9BA7BC",
            "lineWidth": 2,
            "opacity": 0.85,
        },
        {
            "layer": "torso",
            "facing": "front",
            "z_offset": 45,
            "type": "line",
            "x": 138,
            "y": 205,
            "x2": 158,
            "y2": 205,
            "stroke": "#9BA7BC",
            "lineWidth": 2,
            "opacity": 0.85,
        },
    ],
}


class BimaMemoriCharacter(Detik75CharacterBase):
    """Karakter 2.5D Bima (42 • Penghadang Zirah) — Open Free-Rig, Layered IK, 360° Turntable."""

    DEFAULT_CONFIG: Dict[str, Any] = CHARACTER_CONFIG
    DEFAULT_ANIMATION = "free"
    DEFAULT_ANGLE: float = 0.0
    DEFAULT_FPS: int = 30
    DEFAULT_SCALE: float = 3.0
    DEFAULT_TIME_OFFSET: float = 0.45  # Fase unik otomatis agar multi-karakter tidak bergerak seragam
    DEFAULT_SQUASH_X: float = 1.09
    DEFAULT_SQUASH_Y: float = 1.01

    def _build_overrides(self, **kwargs: Any) -> Dict[str, Any]:
        kwargs.setdefault("squash_x", self.DEFAULT_SQUASH_X)
        kwargs.setdefault("squash_y", self.DEFAULT_SQUASH_Y)
        return super()._build_overrides(**kwargs)


def render_demo_scene(output_path: str = "demo.mp4", width: int = 720, height: int = 1280, fps: int = 30, scale: float = 2.5, audio_path: str | None = None) -> str:
    return render_character_demo(BimaMemoriCharacter, output_path=output_path, width=width, height=height, fps=fps, scale=scale, audio_path=audio_path)


if __name__ == "__main__":
    run_character_cli(BimaMemoriCharacter)
