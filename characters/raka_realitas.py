"""
RakaRealitasCharacter — Komponen Karakter 2.5D Ringan (Shared Engine • ~65 baris)
Character : Kakek Raka (78 • Pasien ICU)
Prompt    : Kakek Raka 78 tahun pasien ICU demensia rapuh bahu menyusut, baju pasien rumah sakit biru pucat senada jaketnya, bekas luka kecil di alis kiri pengikat identitas, rambut putih perak tipis, kerutan lansia lembut, tatapan damai
Requires  : character_engine_25d.py (simpan 1x di folder proyek yang sama)

Cara pakai (Free-Rig terbuka — tidak mengunci pose/ekspresi!):
    from raka_realitas_character import RakaRealitasCharacter
    char = RakaRealitasCharacter(scale=3, fps=30)

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
    "name": "Kakek Raka (78 • Pasien ICU)",
    "prompt": "Kakek Raka 78 tahun pasien ICU demensia rapuh bahu menyusut, baju pasien rumah sakit biru pucat senada jaketnya, bekas luka kecil di alis kiri pengikat identitas, rambut putih perak tipis, kerutan lansia lembut, tatapan damai",
    "headShape": "tall",
    "ears": True,
    "earPencil": False,
    "skinColor": "#EDE5DF",
    "blushColor": "#CFB8B4",
    "irisColor": "#6B5344",
    "eyes": "chill",
    "eyebrows": "worried",
    "nose": "upturned_tiny",
    "mouth": "smirk",
    "beard": "none",
    "faceAccessory": "none",
    "sweatDrop": False,
    "blush": False,
    "angerVein": False,
    "eyeGazeX": 0,
    "eyeGazeY": 0.05,
    "hat": "none",
    "hatPrimary": "#9AB9D6",
    "hatAccent": "#DCEAF5",
    "hatTilt": 0,
    "hatLiftY": 0,
    "loupeOpen": True,
    "backHair": "short",
    "hairColor": "#E4E8F0",
    "outfit": "hanbok_kimono",
    "robeColor": "#9AB9D6",
    "innerColor": "#E3EEF7",
    "sashColor": "#789AB8",
    "trimColor": "#C5D9EB",
    "beltStyle": "knot",
    "cape": "none",
    "capeColor": "#9AB9D6",
    "emblem": "none",
    "pose": "ready",
    "prop": "none",
    "limbColor": "#DECBC0",
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
            "x": 124.5,
            "y": 100.5,
            "x2": 120.5,
            "y2": 116.5,
            "stroke": "#FADAD4",
            "lineWidth": 3.1,
            "opacity": 0.72,
        },
        {
            "layer": "head",
            "facing": "front",
            "z_offset": 48,
            "type": "line",
            "x": 123.2,
            "y": 100.5,
            "x2": 119.2,
            "y2": 116.5,
            "stroke": "#A64B53",
            "lineWidth": 2,
            "opacity": 0.92,
        },
        {
            "layer": "head",
            "facing": "front",
            "z_offset": 46,
            "type": "line",
            "x": 85,
            "y": 98,
            "x2": 116,
            "y2": 97,
            "stroke": "#8C6D63",
            "lineWidth": 1.5,
            "opacity": 0.58,
        },
        {
            "layer": "head",
            "facing": "front",
            "z_offset": 46,
            "type": "line",
            "x": 89,
            "y": 102.5,
            "x2": 112,
            "y2": 101.8,
            "stroke": "#8C6D63",
            "lineWidth": 1.25,
            "opacity": 0.42,
        },
        {
            "layer": "head",
            "facing": "front",
            "z_offset": 49,
            "type": "line",
            "x": 75,
            "y": 150.5,
            "x2": 91,
            "y2": 151.5,
            "stroke": "#7E5D55",
            "lineWidth": 1.6,
            "opacity": 0.55,
        },
        {
            "layer": "head",
            "facing": "front",
            "z_offset": 49,
            "type": "line",
            "x": 110,
            "y": 148.2,
            "x2": 126,
            "y2": 149.2,
            "stroke": "#7E5D55",
            "lineWidth": 1.6,
            "opacity": 0.55,
        },
        {
            "layer": "head",
            "facing": "front",
            "z_offset": 48,
            "type": "line",
            "x": 79,
            "y": 157,
            "x2": 72,
            "y2": 173,
            "stroke": "#8A685E",
            "lineWidth": 1.55,
            "opacity": 0.55,
        },
        {
            "layer": "head",
            "facing": "front",
            "z_offset": 48,
            "type": "line",
            "x": 124,
            "y": 155,
            "x2": 131,
            "y2": 171,
            "stroke": "#8A685E",
            "lineWidth": 1.55,
            "opacity": 0.55,
        },
        {
            "layer": "torso",
            "facing": "front",
            "z_offset": 45,
            "type": "circle",
            "x": 88,
            "y": 218,
            "r": 2.3,
            "fill": "#F4F8FC",
            "stroke": "#5D7E9C",
            "lineWidth": 1.2,
            "opacity": 0.9,
        },
        {
            "layer": "torso",
            "facing": "front",
            "z_offset": 45,
            "type": "circle",
            "x": 96,
            "y": 232,
            "r": 2.3,
            "fill": "#F4F8FC",
            "stroke": "#5D7E9C",
            "lineWidth": 1.2,
            "opacity": 0.9,
        },
        {
            "layer": "torso",
            "facing": "front",
            "z_offset": 45,
            "type": "rect",
            "x": 118,
            "y": 232,
            "w": 14,
            "h": 10,
            "radius": 2.5,
            "fill": "#EBF3FA",
            "stroke": "#6B8FAD",
            "lineWidth": 1.3,
            "opacity": 0.88,
        },
    ],
}


class RakaRealitasCharacter(Detik75CharacterBase):
    """Karakter 2.5D Kakek Raka (78 • Pasien ICU) — Open Free-Rig, Layered IK, 360° Turntable."""

    DEFAULT_CONFIG: Dict[str, Any] = CHARACTER_CONFIG
    DEFAULT_ANIMATION = "free"
    DEFAULT_ANGLE: float = 0.0
    DEFAULT_FPS: int = 30
    DEFAULT_SCALE: float = 3.0
    DEFAULT_TIME_OFFSET: float = 0.85  # Fase unik otomatis agar multi-karakter tidak bergerak seragam
    ICU_WRISTBAND: bool = True
    DEFAULT_SQUASH_X: float = 0.9
    DEFAULT_SQUASH_Y: float = 0.97

    def _build_overrides(self, **kwargs: Any) -> Dict[str, Any]:
        kwargs.setdefault("squash_x", self.DEFAULT_SQUASH_X)
        kwargs.setdefault("squash_y", self.DEFAULT_SQUASH_Y)
        return super()._build_overrides(**kwargs)


def render_demo_scene(output_path: str = "demo.mp4", width: int = 720, height: int = 1280, fps: int = 30, scale: float = 2.5, audio_path: str | None = None) -> str:
    return render_character_demo(RakaRealitasCharacter, output_path=output_path, width=width, height=height, fps=fps, scale=scale, audio_path=audio_path)


if __name__ == "__main__":
    run_character_cli(RakaRealitasCharacter)
