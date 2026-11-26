"""
characters — Paket Karakter 2.5D Shared-Engine & Free-Rig untuk "DETIK KE-75".

Berisi 5 karakter utama dalam seluruh peran ganda (Memori Sci-Fi / Realitas ICU / Twist Akhir):
  1. Raka  : RakaMemoriCharacter (26 thn + morph-target aging 0..1) & RakaRealitasCharacter (78 thn ICU)
  2. Sena  : SenaMemoriCharacter (Agen Pemburu) & SenaRealitasCharacter (Dokter ICU)
  3. Bima  : BimaMemoriCharacter (Penghadang Zirah) & BimaRealitasCharacter (Putra Sulung)
  4. Kira  : KiraMemoriCharacter (Penembak Jitu) & KiraRealitasCharacter (Putri Bungsu)
  5. Maya  : MayaRealitasCharacter (75 thn Mantel & Syal Kuning) & MayaMudaCharacter (25 thn Gaun Vintage)
"""
from __future__ import annotations

import os as _os
import sys as _sys

_HERE = _os.path.dirname(_os.path.abspath(__file__))
if _HERE not in _sys.path:
    _sys.path.insert(0, _HERE)

from character_engine_25d import (
    BaseCharacter25D,
    Character25D,
    Easing,
    StoryboardScene,
    Vec3,
    extract_lipsync_curve,
    interpolate,
    spring,
)
from detik75_rig_addons import Detik75CharacterBase, build_raka_aging_layers, lerp_hex
from raka_memori import RakaMemoriCharacter
from raka_realitas import RakaRealitasCharacter
from sena_memori import SenaMemoriCharacter
from sena_realitas import SenaRealitasCharacter
from bima_memori import BimaMemoriCharacter
from bima_realitas import BimaRealitasCharacter
from kira_memori import KiraMemoriCharacter
from kira_realitas import KiraRealitasCharacter
from maya_realitas import MayaRealitasCharacter
from maya_muda import MayaMudaCharacter

CHARACTER_REGISTRY = {
    ("raka", "memori"): RakaMemoriCharacter,
    ("raka", "realitas"): RakaRealitasCharacter,
    ("sena", "memori"): SenaMemoriCharacter,
    ("sena", "realitas"): SenaRealitasCharacter,
    ("bima", "memori"): BimaMemoriCharacter,
    ("bima", "realitas"): BimaRealitasCharacter,
    ("kira", "memori"): KiraMemoriCharacter,
    ("kira", "realitas"): KiraRealitasCharacter,
    ("maya", "memori"): MayaRealitasCharacter,
    ("maya", "realitas"): MayaRealitasCharacter,
    ("maya", "muda"): MayaMudaCharacter,
}


def create_character(name: str, mode: str = "memori", scale: float = 3.0, fps: int = 30) -> Detik75CharacterBase:
    """Factory cepat untuk membuat instance karakter Free-Rig berdasarkan nama & mode dunia."""
    key = (name.strip().lower(), mode.strip().lower())
    if key not in CHARACTER_REGISTRY:
        raise KeyError(f"Karakter {key} tidak ditemukan. Pilihan: {list(CHARACTER_REGISTRY.keys())}")
    return CHARACTER_REGISTRY[key](scale=scale, fps=fps)


__all__ = [
    "BaseCharacter25D",
    "Character25D",
    "Detik75CharacterBase",
    "Easing",
    "StoryboardScene",
    "Vec3",
    "extract_lipsync_curve",
    "interpolate",
    "spring",
    "RakaMemoriCharacter",
    "RakaRealitasCharacter",
    "SenaMemoriCharacter",
    "SenaRealitasCharacter",
    "BimaMemoriCharacter",
    "BimaRealitasCharacter",
    "KiraMemoriCharacter",
    "KiraRealitasCharacter",
    "MayaRealitasCharacter",
    "MayaMudaCharacter",
    "CHARACTER_REGISTRY",
    "create_character",
]
