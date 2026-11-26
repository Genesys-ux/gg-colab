"""
MayaRealitasCharacter — Komponen Karakter 2.5D Ringan (Shared Engine • ~65 baris)
Character : Nenek Maya (75 • Mantel & Syal Kuning)
Prompt    : Maya 75 tahun anggun mungil tenang, mantel wol krem keemasan dengan syal sutra kuning hangat satu-satunya warna hangat di film, rambut perak disanggul rapi dengan helai lepas, senyum lembut, cincin emas bercahaya halus
Requires  : character_engine_25d.py (simpan 1x di folder proyek yang sama)

Cara pakai (Free-Rig terbuka — tidak mengunci pose/ekspresi!):
    from maya_realitas_character import MayaRealitasCharacter
    char = MayaRealitasCharacter(scale=3, fps=30)

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
    "name": "Nenek Maya (75 • Mantel & Syal Kuning)",
    "prompt": "Maya 75 tahun anggun mungil tenang, mantel wol krem keemasan dengan syal sutra kuning hangat satu-satunya warna hangat di film, rambut perak disanggul rapi dengan helai lepas, senyum lembut, cincin emas bercahaya halus",
    "headShape": "round",
    "ears": True,
    "earPencil": False,
    "skinColor": "#F7E8DE",
    "blushColor": "#E6B9B2",
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
    "eyeGazeX": 0.1,
    "eyeGazeY": 0,
    "hat": "none",
    "hatPrimary": "#DCE2EC",
    "hatAccent": "#F2C138",
    "hatTilt": 0,
    "hatLiftY": 0,
    "loupeOpen": True,
    "backHair": "chonmage",
    "hairColor": "#DCE2EC",
    "outfit": "trench_coat",
    "robeColor": "#DFC798",
    "innerColor": "#FAF0DA",
    "sashColor": "#C9A86A",
    "trimColor": "#F4C430",
    "beltStyle": "buckle",
    "cape": "scarf",
    "capeColor": "#F4C430",
    "emblem": "none",
    "pose": "wave",
    "prop": "none",
    "limbColor": "#59483B",
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
            "fill": "#DCE2EC",
            "stroke": "#1E1722",
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
            "stroke": "#F2C138",
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
            "fill": "#DCE2EC",
            "stroke": "#231B26",
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
            "fill": "#E4EAF3",
            "stroke": "#231B26",
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
            "y2": 136,
            "stroke": "#E6ECF5",
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
            "y2": 134,
            "stroke": "#E6ECF5",
            "lineWidth": 2.4,
            "opacity": 0.94,
        },
        {
            "layer": "head",
            "facing": "front",
            "z_offset": 48,
            "type": "line",
            "x": 68,
            "y": 141,
            "x2": 62,
            "y2": 145,
            "stroke": "#AD8B82",
            "lineWidth": 1.3,
            "opacity": 0.48,
        },
        {
            "layer": "head",
            "facing": "front",
            "z_offset": 48,
            "type": "line",
            "x": 135,
            "y": 139,
            "x2": 141,
            "y2": 143,
            "stroke": "#AD8B82",
            "lineWidth": 1.3,
            "opacity": 0.48,
        },
        {
            "layer": "torso",
            "facing": "front",
            "z_offset": 46,
            "type": "ellipse",
            "x": 104,
            "y": 209,
            "rx": 28,
            "ry": 9.5,
            "rot": 0.04,
            "fill": "#F4C430",
            "stroke": "#8C6512",
            "lineWidth": 2,
            "opacity": 0.98,
        },
        {
            "layer": "torso",
            "facing": "front",
            "z_offset": 47,
            "type": "rect",
            "x": 108,
            "y": 213,
            "w": 13,
            "h": 36,
            "radius": 5,
            "fill": "#F7D046",
            "stroke": "#8C6512",
            "lineWidth": 1.8,
            "opacity": 0.96,
        },
    ],
}


class MayaRealitasCharacter(Detik75CharacterBase):
    """Karakter 2.5D Nenek Maya (75 • Mantel & Syal Kuning) — Open Free-Rig, Layered IK, 360° Turntable."""

    DEFAULT_CONFIG: Dict[str, Any] = CHARACTER_CONFIG
    DEFAULT_ANIMATION = "free"
    DEFAULT_ANGLE: float = 0.0
    DEFAULT_FPS: int = 30
    DEFAULT_SCALE: float = 3.0
    DEFAULT_TIME_OFFSET: float = 2.26  # Fase unik otomatis agar multi-karakter tidak bergerak seragam
    RING_GLOW_HAND: str = "left"
    DEFAULT_SQUASH_X: float = 0.93
    DEFAULT_SQUASH_Y: float = 0.94

    def _build_overrides(self, **kwargs: Any) -> Dict[str, Any]:
        kwargs.setdefault("squash_x", self.DEFAULT_SQUASH_X)
        kwargs.setdefault("squash_y", self.DEFAULT_SQUASH_Y)
        return super()._build_overrides(**kwargs)


def render_demo_scene(output_path: str = "demo.mp4", width: int = 720, height: int = 1280, fps: int = 30, scale: float = 2.5, audio_path: str | None = None) -> str:
    return render_character_demo(MayaRealitasCharacter, output_path=output_path, width=width, height=height, fps=fps, scale=scale, audio_path=audio_path)


if __name__ == "__main__":
    run_character_cli(MayaRealitasCharacter)
