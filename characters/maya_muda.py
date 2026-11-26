"""
MayaMudaCharacter — Komponen Karakter 2.5D Ringan (Shared Engine • ~65 baris)
Character : Maya Muda (25 • Gaun Vintage Krem)
Prompt    : Maya 25 tahun anggun mungil koridor cahaya keemasan, gaun vintage krem muda berpita lembut, rambut disanggul rapi dengan beberapa helai lepas, senyum lembut yang sama dengan usia 75 tahun, cincin emas bercahaya halus
Requires  : character_engine_25d.py (simpan 1x di folder proyek yang sama)

Cara pakai (Free-Rig terbuka — tidak mengunci pose/ekspresi!):
    from maya_muda_character import MayaMudaCharacter
    char = MayaMudaCharacter(scale=3, fps=30)

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
    "name": "Maya Muda (25 • Gaun Vintage Krem)",
    "prompt": "Maya 25 tahun anggun mungil koridor cahaya keemasan, gaun vintage krem muda berpita lembut, rambut disanggul rapi dengan beberapa helai lepas, senyum lembut yang sama dengan usia 75 tahun, cincin emas bercahaya halus",
    "headShape": "round",
    "ears": True,
    "earPencil": False,
    "skinColor": "#FCECE2",
    "blushColor": "#F0BCB4",
    "irisColor": "#594033",
    "eyes": "happy",
    "eyebrows": "happy",
    "nose": "upturned_tiny",
    "mouth": "smirk",
    "beard": "none",
    "faceAccessory": "none",
    "sweatDrop": False,
    "blush": True,
    "angerVein": False,
    "eyeGazeX": -0.15,
    "eyeGazeY": 0,
    "hat": "none",
    "hatPrimary": "#2A1F24",
    "hatAccent": "#F2C94C",
    "hatTilt": 0,
    "hatLiftY": 0,
    "loupeOpen": True,
    "backHair": "chonmage",
    "hairColor": "#2A1F24",
    "outfit": "noble_robe",
    "robeColor": "#F5ECD8",
    "innerColor": "#FFFDF7",
    "sashColor": "#E8C568",
    "trimColor": "#F2CE68",
    "beltStyle": "bow",
    "cape": "none",
    "capeColor": "#F4C430",
    "emblem": "none",
    "pose": "wave",
    "prop": "none",
    "limbColor": "#8C6F52",
    "groundShadow": True,
    "outlineShadow": 1.35,
    "outlineLit": 1,
    "rimIntensity": 0.45,
    "shadowDepth": 1.5,
    "customLayers": [
        {
            "layer": "hat",
            "facing": "both",
            "z_offset": 0,
            "type": "ellipse",
            "x": 104,
            "y": 83,
            "rx": 22,
            "ry": 13,
            "rot": 0,
            "fill": "#2A1F24",
            "stroke": "#161015",
            "lineWidth": 3,
            "opacity": 0.98,
        },
        {
            "layer": "hat",
            "facing": "front",
            "z_offset": 18,
            "type": "line",
            "x": 88,
            "y": 90,
            "x2": 120,
            "y2": 90,
            "stroke": "#F2C94C",
            "lineWidth": 3.2,
            "opacity": 0.95,
        },
        {
            "layer": "head",
            "facing": "front",
            "z_offset": 44,
            "type": "ellipse",
            "x": 73,
            "y": 98,
            "rx": 34,
            "ry": 14,
            "rot": -0.24,
            "fill": "#2A1F24",
            "stroke": "#161015",
            "lineWidth": 2.2,
            "opacity": 0.98,
        },
        {
            "layer": "head",
            "facing": "front",
            "z_offset": 44,
            "type": "ellipse",
            "x": 135,
            "y": 98,
            "rx": 34,
            "ry": 14,
            "rot": 0.24,
            "fill": "#382A31",
            "stroke": "#161015",
            "lineWidth": 2.2,
            "opacity": 0.98,
        },
        {
            "layer": "head",
            "facing": "front",
            "z_offset": 46,
            "type": "line",
            "x": 54,
            "y": 104,
            "x2": 46,
            "y2": 137,
            "stroke": "#2A1F24",
            "lineWidth": 2.6,
            "opacity": 0.94,
        },
        {
            "layer": "head",
            "facing": "front",
            "z_offset": 46,
            "type": "line",
            "x": 152,
            "y": 103,
            "x2": 160,
            "y2": 135,
            "stroke": "#2A1F24",
            "lineWidth": 2.4,
            "opacity": 0.94,
        },
        {
            "layer": "torso",
            "facing": "front",
            "z_offset": 45,
            "type": "rect",
            "x": 88,
            "y": 232,
            "w": 32,
            "h": 28,
            "radius": 5,
            "fill": "#FAF4E6",
            "stroke": "#D9BA73",
            "lineWidth": 1.6,
            "opacity": 0.96,
        },
        {
            "layer": "torso",
            "facing": "front",
            "z_offset": 46,
            "type": "circle",
            "x": 104,
            "y": 226,
            "r": 4.6,
            "fill": "#FFE885",
            "stroke": "#B88928",
            "lineWidth": 1.5,
            "opacity": 0.98,
        },
    ],
}


class MayaMudaCharacter(Detik75CharacterBase):
    """Karakter 2.5D Maya Muda (25 • Gaun Vintage Krem) — Open Free-Rig, Layered IK, 360° Turntable."""

    DEFAULT_CONFIG: Dict[str, Any] = CHARACTER_CONFIG
    DEFAULT_ANIMATION = "free"
    DEFAULT_ANGLE: float = 0.0
    DEFAULT_FPS: int = 30
    DEFAULT_SCALE: float = 3.0
    DEFAULT_TIME_OFFSET: float = 2.53  # Fase unik otomatis agar multi-karakter tidak bergerak seragam
    RING_GLOW_HAND: str = "left"
    DEFAULT_SQUASH_X: float = 0.94
    DEFAULT_SQUASH_Y: float = 0.96

    def _build_overrides(self, **kwargs: Any) -> Dict[str, Any]:
        kwargs.setdefault("squash_x", self.DEFAULT_SQUASH_X)
        kwargs.setdefault("squash_y", self.DEFAULT_SQUASH_Y)
        return super()._build_overrides(**kwargs)


def render_demo_scene(output_path: str = "demo.mp4", width: int = 720, height: int = 1280, fps: int = 30, scale: float = 2.5, audio_path: str | None = None) -> str:
    return render_character_demo(MayaMudaCharacter, output_path=output_path, width=width, height=height, fps=fps, scale=scale, audio_path=audio_path)


if __name__ == "__main__":
    run_character_cli(MayaMudaCharacter)
