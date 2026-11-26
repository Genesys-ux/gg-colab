"""
RakaMemoriCharacter — Komponen Karakter 2.5D Ringan (Shared Engine • ~65 baris)
Character : Raka (26 • Kurir Pelarian)
Prompt    : Raka 26 tahun kurir pelarian atletis bahu tegap, jaket bomber kulit biru tua berkerah tinggi aksen emas tipis, sepatu bot taktis hitam, bekas luka kecil di alis kiri, rambut hitam berombak tertiup angin, tatapan fokus terengah
Requires  : character_engine_25d.py (simpan 1x di folder proyek yang sama)

Cara pakai (Free-Rig terbuka — tidak mengunci pose/ekspresi!):
    from raka_memori_character import RakaMemoriCharacter
    char = RakaMemoriCharacter(scale=3, fps=30)

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
    "name": "Raka (26 • Kurir Pelarian)",
    "prompt": "Raka 26 tahun kurir pelarian atletis bahu tegap, jaket bomber kulit biru tua berkerah tinggi aksen emas tipis, sepatu bot taktis hitam, bekas luka kecil di alis kiri, rambut hitam berombak tertiup angin, tatapan fokus terengah",
    "headShape": "chubby_oval",
    "ears": True,
    "earPencil": False,
    "skinColor": "#F6DFC8",
    "blushColor": "#DFB4A2",
    "irisColor": "#5A3825",
    "eyes": "focused",
    "eyebrows": "thick_arch",
    "nose": "upturned_tiny",
    "mouth": "grit_teeth",
    "beard": "none",
    "faceAccessory": "none",
    "sweatDrop": True,
    "blush": False,
    "angerVein": False,
    "eyeGazeX": 0.18,
    "eyeGazeY": 0,
    "hat": "none",
    "hatPrimary": "#1B3159",
    "hatAccent": "#E2B44B",
    "hatTilt": 0,
    "hatLiftY": 0,
    "loupeOpen": True,
    "backHair": "windswept_bolt",
    "hairColor": "#1A1C26",
    "outfit": "cyber_jacket",
    "robeColor": "#1B3159",
    "innerColor": "#E2B44B",
    "sashColor": "#111B30",
    "trimColor": "#4D7EC4",
    "beltStyle": "buckle",
    "cape": "none",
    "capeColor": "#152442",
    "emblem": "none",
    "pose": "ready",
    "prop": "none",
    "limbColor": "#151A26",
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
            "layer": "torso",
            "facing": "front",
            "z_offset": 44,
            "type": "rect",
            "x": 76,
            "y": 197,
            "w": 56,
            "h": 14,
            "radius": 4,
            "fill": "#12213D",
            "stroke": "#0D1526",
            "lineWidth": 2,
            "opacity": 0.96,
        },
        {
            "layer": "torso",
            "facing": "front",
            "z_offset": 45,
            "type": "line",
            "x": 80,
            "y": 204,
            "x2": 128,
            "y2": 204,
            "stroke": "#E2B44B",
            "lineWidth": 1.5,
            "opacity": 0.85,
        },
        {
            "layer": "torso",
            "facing": "front",
            "z_offset": 42,
            "type": "line",
            "x": 63,
            "y": 222,
            "x2": 75,
            "y2": 256,
            "stroke": "#2B4B82",
            "lineWidth": 2.2,
            "opacity": 0.7,
        },
    ],
}


class RakaMemoriCharacter(Detik75CharacterBase):
    """Karakter 2.5D Raka (26 • Kurir Pelarian) — Open Free-Rig, Layered IK, 360° Turntable."""

    DEFAULT_CONFIG: Dict[str, Any] = CHARACTER_CONFIG
    DEFAULT_ANIMATION = "free"
    DEFAULT_ANGLE: float = 0.0
    DEFAULT_FPS: int = 30
    DEFAULT_SCALE: float = 3.0
    DEFAULT_TIME_OFFSET: float = 1.83  # Fase unik otomatis agar multi-karakter tidak bergerak seragam
    SUPPORTS_AGING: bool = True
    DEFAULT_SQUASH_X: float = 1.02
    DEFAULT_SQUASH_Y: float = 1.01

    def _build_overrides(self, **kwargs: Any) -> Dict[str, Any]:
        kwargs.setdefault("squash_x", self.DEFAULT_SQUASH_X)
        kwargs.setdefault("squash_y", self.DEFAULT_SQUASH_Y)
        return super()._build_overrides(**kwargs)


def render_demo_scene(output_path: str = "demo.mp4", width: int = 720, height: int = 1280, fps: int = 30, scale: float = 2.5, audio_path: str | None = None) -> str:
    return render_character_demo(RakaMemoriCharacter, output_path=output_path, width=width, height=height, fps=fps, scale=scale, audio_path=audio_path)


if __name__ == "__main__":
    run_character_cli(RakaMemoriCharacter)
