"""
SenaMemoriCharacter — Komponen Karakter 2.5D Ringan (Shared Engine • ~65 baris)
Character : Agen Sena (35 • Pemburu Taktis)
Prompt    : Agen pemburu taktis 35 tahun tinggi kaku presisi, mantel panjang hitam-perak berpotongan tajam, kacamata visor tipis bercahaya biru, rahang tegas, rambut klimis disisir rapi ke belakang, ekspresi dingin
Requires  : character_engine_25d.py (simpan 1x di folder proyek yang sama)

Cara pakai (Free-Rig terbuka — tidak mengunci pose/ekspresi!):
    from sena_memori_character import SenaMemoriCharacter
    char = SenaMemoriCharacter(scale=3, fps=30)

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
    "name": "Agen Sena (35 • Pemburu Taktis)",
    "prompt": "Agen pemburu taktis 35 tahun tinggi kaku presisi, mantel panjang hitam-perak berpotongan tajam, kacamata visor tipis bercahaya biru, rahang tegas, rambut klimis disisir rapi ke belakang, ekspresi dingin",
    "headShape": "tall",
    "ears": True,
    "earPencil": False,
    "skinColor": "#F4E4DA",
    "blushColor": "#D6B8B0",
    "irisColor": "#2B4C66",
    "eyes": "focused",
    "eyebrows": "flat",
    "nose": "none",
    "mouth": "flat",
    "beard": "none",
    "faceAccessory": "cyber_visor",
    "sweatDrop": False,
    "blush": False,
    "angerVein": False,
    "eyeGazeX": -0.15,
    "eyeGazeY": 0,
    "hat": "none",
    "hatPrimary": "#1A1E29",
    "hatAccent": "#38C8FF",
    "hatTilt": 0,
    "hatLiftY": 0,
    "loupeOpen": True,
    "backHair": "side_part",
    "hairColor": "#161922",
    "outfit": "trench_coat",
    "robeColor": "#1B1F2B",
    "innerColor": "#CFD8E6",
    "sashColor": "#0E121A",
    "trimColor": "#38C8FF",
    "beltStyle": "buckle",
    "cape": "none",
    "capeColor": "#141722",
    "emblem": "none",
    "pose": "point",
    "prop": "none",
    "limbColor": "#13161F",
    "groundShadow": True,
    "outlineShadow": 1.35,
    "outlineLit": 1,
    "rimIntensity": 0.45,
    "shadowDepth": 1.5,
    "customLayers": [
        {
            "layer": "torso",
            "facing": "front",
            "z_offset": 45,
            "type": "line",
            "x": 70,
            "y": 222,
            "x2": 95,
            "y2": 260,
            "stroke": "#DCE6F5",
            "lineWidth": 2.2,
            "opacity": 0.88,
        },
        {
            "layer": "torso",
            "facing": "front",
            "z_offset": 45,
            "type": "line",
            "x": 138,
            "y": 222,
            "x2": 113,
            "y2": 260,
            "stroke": "#DCE6F5",
            "lineWidth": 2.2,
            "opacity": 0.88,
        },
        {
            "layer": "torso",
            "facing": "front",
            "z_offset": 46,
            "type": "circle",
            "x": 126,
            "y": 242,
            "r": 4.5,
            "fill": "#38D6FF",
            "stroke": "#E6FAFF",
            "lineWidth": 1.4,
            "opacity": 0.92,
        },
    ],
}


class SenaMemoriCharacter(Detik75CharacterBase):
    """Karakter 2.5D Agen Sena (35 • Pemburu Taktis) — Open Free-Rig, Layered IK, 360° Turntable."""

    DEFAULT_CONFIG: Dict[str, Any] = CHARACTER_CONFIG
    DEFAULT_ANIMATION = "free"
    DEFAULT_ANGLE: float = 0.0
    DEFAULT_FPS: int = 30
    DEFAULT_SCALE: float = 3.0
    DEFAULT_TIME_OFFSET: float = 0.63  # Fase unik otomatis agar multi-karakter tidak bergerak seragam
    DEFAULT_SQUASH_X: float = 0.96
    DEFAULT_SQUASH_Y: float = 1.04

    def _build_overrides(self, **kwargs: Any) -> Dict[str, Any]:
        kwargs.setdefault("squash_x", self.DEFAULT_SQUASH_X)
        kwargs.setdefault("squash_y", self.DEFAULT_SQUASH_Y)
        return super()._build_overrides(**kwargs)


def render_demo_scene(output_path: str = "demo.mp4", width: int = 720, height: int = 1280, fps: int = 30, scale: float = 2.5, audio_path: str | None = None) -> str:
    return render_character_demo(SenaMemoriCharacter, output_path=output_path, width=width, height=height, fps=fps, scale=scale, audio_path=audio_path)


if __name__ == "__main__":
    run_character_cli(SenaMemoriCharacter)
