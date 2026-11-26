"""
KiraRealitasCharacter — Komponen Karakter 2.5D Ringan (Shared Engine • ~65 baris)
Character : Kira (30 • Putri Bungsu)
Prompt    : Kira 30 tahun putri bungsu Raka ramping siluet vertikal, kardigan merah marun di atas kaus hitam, lanyard dan jam tangan layar merah, rambut bob hitam sebahu, mata ekspresif kelopak kemerahan menangis
Requires  : character_engine_25d.py (simpan 1x di folder proyek yang sama)

Cara pakai (Free-Rig terbuka — tidak mengunci pose/ekspresi!):
    from kira_realitas_character import KiraRealitasCharacter
    char = KiraRealitasCharacter(scale=3, fps=30)

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
    "name": "Kira (30 • Putri Bungsu)",
    "prompt": "Kira 30 tahun putri bungsu Raka ramping siluet vertikal, kardigan merah marun di atas kaus hitam, lanyard dan jam tangan layar merah, rambut bob hitam sebahu, mata ekspresif kelopak kemerahan menangis",
    "headShape": "tall",
    "ears": False,
    "earPencil": False,
    "skinColor": "#FCEBE2",
    "blushColor": "#E5AEB2",
    "irisColor": "#4A2B29",
    "eyes": "honey_oval",
    "eyebrows": "worried",
    "nose": "upturned_tiny",
    "mouth": "frown",
    "beard": "none",
    "faceAccessory": "none",
    "sweatDrop": False,
    "blush": True,
    "angerVein": False,
    "eyeGazeX": -0.15,
    "eyeGazeY": 0.08,
    "hat": "none",
    "hatPrimary": "#6E1F2E",
    "hatAccent": "#FF3347",
    "hatTilt": 0,
    "hatLiftY": 0,
    "loupeOpen": True,
    "backHair": "short",
    "hairColor": "#181620",
    "outfit": "magua",
    "robeColor": "#701F2E",
    "innerColor": "#1A1822",
    "sashColor": "#541622",
    "trimColor": "#591724",
    "beltStyle": "plain",
    "cape": "none",
    "capeColor": "#701F2E",
    "emblem": "none",
    "pose": "think",
    "prop": "none",
    "limbColor": "#1F1C26",
    "groundShadow": True,
    "outlineShadow": 1.35,
    "outlineLit": 1,
    "rimIntensity": 0.45,
    "shadowDepth": 1.5,
    "customLayers": [
        {
            "layer": "head",
            "facing": "front",
            "z_offset": 45,
            "type": "ellipse",
            "x": 47,
            "y": 142,
            "rx": 10.5,
            "ry": 42,
            "rot": 0.11,
            "fill": "#181620",
            "stroke": "#100E16",
            "lineWidth": 2,
            "opacity": 0.98,
        },
        {
            "layer": "head",
            "facing": "front",
            "z_offset": 45,
            "type": "ellipse",
            "x": 159,
            "y": 142,
            "rx": 10.5,
            "ry": 42,
            "rot": -0.11,
            "fill": "#181620",
            "stroke": "#100E16",
            "lineWidth": 2,
            "opacity": 0.98,
        },
        {
            "layer": "head",
            "facing": "front",
            "z_offset": 46,
            "type": "line",
            "x": 54,
            "y": 108,
            "x2": 50,
            "y2": 168,
            "stroke": "#353148",
            "lineWidth": 2.4,
            "opacity": 0.85,
        },
        {
            "layer": "head",
            "facing": "front",
            "z_offset": 46,
            "type": "line",
            "x": 152,
            "y": 108,
            "x2": 156,
            "y2": 168,
            "stroke": "#353148",
            "lineWidth": 2.4,
            "opacity": 0.85,
        },
        {
            "layer": "head",
            "facing": "front",
            "z_offset": 47,
            "type": "line",
            "x": 84,
            "y": 95,
            "x2": 79,
            "y2": 108,
            "stroke": "#181620",
            "lineWidth": 3.6,
            "opacity": 0.94,
        },
        {
            "layer": "head",
            "facing": "front",
            "z_offset": 47,
            "type": "line",
            "x": 112,
            "y": 95,
            "x2": 118,
            "y2": 107,
            "stroke": "#181620",
            "lineWidth": 3.2,
            "opacity": 0.94,
        },
        {
            "layer": "head",
            "facing": "front",
            "z_offset": 49,
            "type": "ellipse",
            "x": 83.8,
            "y": 146,
            "rx": 12.5,
            "ry": 5,
            "rot": 0,
            "fill": "#E05365",
            "opacity": 0.42,
        },
        {
            "layer": "head",
            "facing": "front",
            "z_offset": 49,
            "type": "ellipse",
            "x": 118.2,
            "y": 143.5,
            "rx": 12.5,
            "ry": 5,
            "rot": 0,
            "fill": "#E05365",
            "opacity": 0.42,
        },
        {
            "layer": "head",
            "facing": "front",
            "z_offset": 50,
            "type": "circle",
            "x": 75,
            "y": 148,
            "r": 2.5,
            "fill": "#E6F8FF",
            "stroke": "#7CC6E8",
            "lineWidth": 0.8,
            "opacity": 0.95,
        },
        {
            "layer": "head",
            "facing": "front",
            "z_offset": 50,
            "type": "circle",
            "x": 126.5,
            "y": 146,
            "r": 2.3,
            "fill": "#E6F8FF",
            "stroke": "#7CC6E8",
            "lineWidth": 0.8,
            "opacity": 0.95,
        },
        {
            "layer": "torso",
            "facing": "front",
            "z_offset": 45,
            "type": "rect",
            "x": 86,
            "y": 201,
            "w": 36,
            "h": 28,
            "radius": 3,
            "fill": "#1A1822",
            "opacity": 0.98,
        },
        {
            "layer": "torso",
            "facing": "front",
            "z_offset": 46,
            "type": "line",
            "x": 91,
            "y": 203,
            "x2": 104,
            "y2": 248,
            "stroke": "#E63346",
            "lineWidth": 2.8,
            "opacity": 0.95,
        },
        {
            "layer": "torso",
            "facing": "front",
            "z_offset": 46,
            "type": "line",
            "x": 117,
            "y": 203,
            "x2": 104,
            "y2": 248,
            "stroke": "#E63346",
            "lineWidth": 2.8,
            "opacity": 0.95,
        },
        {
            "layer": "torso",
            "facing": "front",
            "z_offset": 47,
            "type": "rect",
            "x": 97,
            "y": 248,
            "w": 14,
            "h": 18,
            "radius": 2,
            "fill": "#F7F9FC",
            "stroke": "#E63346",
            "lineWidth": 1.6,
            "opacity": 0.96,
        },
    ],
}


class KiraRealitasCharacter(Detik75CharacterBase):
    """Karakter 2.5D Kira (30 • Putri Bungsu) — Open Free-Rig, Layered IK, 360° Turntable."""

    DEFAULT_CONFIG: Dict[str, Any] = CHARACTER_CONFIG
    DEFAULT_ANIMATION = "free"
    DEFAULT_ANGLE: float = 0.0
    DEFAULT_FPS: int = 30
    DEFAULT_SCALE: float = 3.0
    DEFAULT_TIME_OFFSET: float = 1.77  # Fase unik otomatis agar multi-karakter tidak bergerak seragam
    WRIST_WATCH_RED: bool = True
    DEFAULT_SQUASH_X: float = 0.94
    DEFAULT_SQUASH_Y: float = 1.03

    def _build_overrides(self, **kwargs: Any) -> Dict[str, Any]:
        kwargs.setdefault("squash_x", self.DEFAULT_SQUASH_X)
        kwargs.setdefault("squash_y", self.DEFAULT_SQUASH_Y)
        return super()._build_overrides(**kwargs)


def render_demo_scene(output_path: str = "demo.mp4", width: int = 720, height: int = 1280, fps: int = 30, scale: float = 2.5, audio_path: str | None = None) -> str:
    return render_character_demo(KiraRealitasCharacter, output_path=output_path, width=width, height=height, fps=fps, scale=scale, audio_path=audio_path)


if __name__ == "__main__":
    run_character_cli(KiraRealitasCharacter)
