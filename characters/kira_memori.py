"""
KiraMemoriCharacter — Komponen Karakter 2.5D Ringan (Shared Engine • ~65 baris)
Character : Kira (30 • Penembak Jitu)
Prompt    : Kira 30 tahun penembak jitu ramping lincah siluet tajam vertikal, jas hujan taktis merah marun gelap berkerudung, sarung tangan hitam, rambut bob hitam acak basah oleh hujan, mata ekspresif berkaca-kaca kemerahan
Requires  : character_engine_25d.py (simpan 1x di folder proyek yang sama)

Cara pakai (Free-Rig terbuka — tidak mengunci pose/ekspresi!):
    from kira_memori_character import KiraMemoriCharacter
    char = KiraMemoriCharacter(scale=3, fps=30)

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
    "name": "Kira (30 • Penembak Jitu)",
    "prompt": "Kira 30 tahun penembak jitu ramping lincah siluet tajam vertikal, jas hujan taktis merah marun gelap berkerudung, sarung tangan hitam, rambut bob hitam acak basah oleh hujan, mata ekspresif berkaca-kaca kemerahan",
    "headShape": "tall",
    "ears": False,
    "earPencil": False,
    "skinColor": "#FCEBE2",
    "blushColor": "#E5AEB2",
    "irisColor": "#4A2B29",
    "eyes": "focused",
    "eyebrows": "worried",
    "nose": "upturned_tiny",
    "mouth": "flat",
    "beard": "none",
    "faceAccessory": "none",
    "sweatDrop": False,
    "blush": True,
    "angerVein": False,
    "eyeGazeX": 0.22,
    "eyeGazeY": -0.05,
    "hat": "hood",
    "hatPrimary": "#581724",
    "hatAccent": "#E03142",
    "hatTilt": 0,
    "hatLiftY": 0,
    "loupeOpen": True,
    "backHair": "short",
    "hairColor": "#181620",
    "outfit": "trench_coat",
    "robeColor": "#611A28",
    "innerColor": "#18161F",
    "sashColor": "#1C161F",
    "trimColor": "#E63946",
    "beltStyle": "utility_belt",
    "cape": "none",
    "capeColor": "#4A121D",
    "emblem": "target",
    "pose": "ready",
    "prop": "none",
    "limbColor": "#141218",
    "groundShadow": True,
    "outlineShadow": 1.35,
    "outlineLit": 1,
    "rimIntensity": 0.45,
    "shadowDepth": 1.5,
    "customLayers": [
        {
            "layer": "torso",
            "facing": "front",
            "z_offset": 44,
            "type": "rect",
            "x": 84,
            "y": 199,
            "w": 40,
            "h": 63,
            "radius": 4,
            "fill": "#22141D",
            "stroke": "#140C12",
            "lineWidth": 1.8,
            "opacity": 0.98,
        },
        {
            "layer": "torso",
            "facing": "front",
            "z_offset": 45,
            "type": "line",
            "x": 104,
            "y": 201,
            "x2": 104,
            "y2": 262,
            "stroke": "#E03142",
            "lineWidth": 2,
            "opacity": 0.9,
        },
        {
            "layer": "head",
            "facing": "front",
            "z_offset": 46,
            "type": "ellipse",
            "x": 52,
            "y": 140,
            "rx": 8.5,
            "ry": 36,
            "rot": 0.1,
            "fill": "#181620",
            "stroke": "#100E16",
            "lineWidth": 1.8,
            "opacity": 0.98,
        },
        {
            "layer": "head",
            "facing": "front",
            "z_offset": 46,
            "type": "ellipse",
            "x": 154,
            "y": 140,
            "rx": 8.5,
            "ry": 36,
            "rot": -0.1,
            "fill": "#181620",
            "stroke": "#100E16",
            "lineWidth": 1.8,
            "opacity": 0.98,
        },
        {
            "layer": "head",
            "facing": "front",
            "z_offset": 47,
            "type": "line",
            "x": 61,
            "y": 100,
            "x2": 57,
            "y2": 154,
            "stroke": "#2F2C40",
            "lineWidth": 2.4,
            "opacity": 0.85,
        },
        {
            "layer": "head",
            "facing": "front",
            "z_offset": 47,
            "type": "line",
            "x": 88,
            "y": 94,
            "x2": 83,
            "y2": 108,
            "stroke": "#181620",
            "lineWidth": 3.4,
            "opacity": 0.92,
        },
        {
            "layer": "head",
            "facing": "front",
            "z_offset": 47,
            "type": "line",
            "x": 114,
            "y": 94,
            "x2": 120,
            "y2": 107,
            "stroke": "#181620",
            "lineWidth": 3,
            "opacity": 0.92,
        },
        {
            "layer": "head",
            "facing": "front",
            "z_offset": 49,
            "type": "ellipse",
            "x": 83.8,
            "y": 145.5,
            "rx": 12,
            "ry": 4.5,
            "rot": 0,
            "fill": "#DE5B6B",
            "opacity": 0.36,
        },
        {
            "layer": "head",
            "facing": "front",
            "z_offset": 49,
            "type": "ellipse",
            "x": 118.2,
            "y": 143,
            "rx": 12,
            "ry": 4.5,
            "rot": 0,
            "fill": "#DE5B6B",
            "opacity": 0.36,
        },
        {
            "layer": "head",
            "facing": "front",
            "z_offset": 50,
            "type": "circle",
            "x": 75.5,
            "y": 146.5,
            "r": 2.2,
            "fill": "#E8F9FF",
            "opacity": 0.94,
        },
        {
            "layer": "head",
            "facing": "front",
            "z_offset": 50,
            "type": "circle",
            "x": 126.5,
            "y": 144.2,
            "r": 2.2,
            "fill": "#E8F9FF",
            "opacity": 0.94,
        },
    ],
}


class KiraMemoriCharacter(Detik75CharacterBase):
    """Karakter 2.5D Kira (30 • Penembak Jitu) — Open Free-Rig, Layered IK, 360° Turntable."""

    DEFAULT_CONFIG: Dict[str, Any] = CHARACTER_CONFIG
    DEFAULT_ANIMATION = "free"
    DEFAULT_ANGLE: float = 0.0
    DEFAULT_FPS: int = 30
    DEFAULT_SCALE: float = 3.0
    DEFAULT_TIME_OFFSET: float = 1.7  # Fase unik otomatis agar multi-karakter tidak bergerak seragam
    DEFAULT_SQUASH_X: float = 0.94
    DEFAULT_SQUASH_Y: float = 1.03

    def _build_overrides(self, **kwargs: Any) -> Dict[str, Any]:
        kwargs.setdefault("squash_x", self.DEFAULT_SQUASH_X)
        kwargs.setdefault("squash_y", self.DEFAULT_SQUASH_Y)
        return super()._build_overrides(**kwargs)


def render_demo_scene(output_path: str = "demo.mp4", width: int = 720, height: int = 1280, fps: int = 30, scale: float = 2.5, audio_path: str | None = None) -> str:
    return render_character_demo(KiraMemoriCharacter, output_path=output_path, width=width, height=height, fps=fps, scale=scale, audio_path=audio_path)


if __name__ == "__main__":
    run_character_cli(KiraMemoriCharacter)
