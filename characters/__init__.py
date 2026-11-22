"""
Desain Karakter & Hero Props (Rigging 100% Terbuka / Tidak Terkunci)
untuk animasi 3D Python 'Jangan Sampai Kunci Ini Jatuh!'.
"""

from . import pedagang_rempah_character as _pedagang_mod
from . import penumpang_trem_character as _penumpang_mod
from .bima_character import BimaCharacter
from .bima_hero import BimaHeroCharacter, LIGHTING_PHASE_PROFILES
from .hero_props import GoldenKeyProp, SilverKeyProp
from .oren_character import OrenCharacter
from .pedagang_rempah_character import PedagangRempahCharacter
from .penumpang_trem_character import PenumpangTremCharacter
from .rig_controls import HumanoidRig, KeyPropRig, OrenRig, UnlockedHumanoidCharacter


def create_pedagang_rempah(scale: float = 3.0, fps: int = 30) -> UnlockedHumanoidCharacter:
    """Desain karakter Pedagang Rempah (rigging terbuka via HumanoidRig, default netral 'static')."""
    return UnlockedHumanoidCharacter(_pedagang_mod, "PedagangRempahCharacter", scale=scale, fps=fps)


def create_penumpang_trem(scale: float = 3.0, fps: int = 30) -> UnlockedHumanoidCharacter:
    """Desain karakter Penumpang Trem (rigging terbuka via HumanoidRig, default netral 'static')."""
    return UnlockedHumanoidCharacter(_penumpang_mod, "PenumpangTremCharacter", scale=scale, fps=fps)


__all__ = [
    "BimaCharacter",
    "BimaHeroCharacter",
    "LIGHTING_PHASE_PROFILES",
    "OrenCharacter",
    "GoldenKeyProp",
    "SilverKeyProp",
    "PedagangRempahCharacter",
    "PenumpangTremCharacter",
    "HumanoidRig",
    "OrenRig",
    "KeyPropRig",
    "UnlockedHumanoidCharacter",
    "create_pedagang_rempah",
    "create_penumpang_trem",
]
