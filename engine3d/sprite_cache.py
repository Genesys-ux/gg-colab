"""
SpriteCache — Merender karakter & Hero Props (dengan rigging 100% terbuka!) serta
partikel 3D volumetrik (debu emas, bubuk kunyit, uap zamrud, percikan api biru-zamrud)
menjadi tekstur RGBA untuk diintegrasikan secara depth-tested ke dunia 3D WebGPU.
"""

from __future__ import annotations

import math
from typing import Dict, Optional, Tuple

import numpy as np
from PIL import Image, ImageDraw

from characters import (
    BimaHeroCharacter,
    GoldenKeyProp,
    HumanoidRig,
    KeyPropRig,
    OrenCharacter,
    OrenRig,
    SilverKeyProp,
    create_pedagang_rempah,
    create_penumpang_trem,
)


def _make_soft_puff(size: int, rgb: Tuple[int, int, int], alpha_peak: float = 0.85, core_bright: bool = False) -> Image.Image:
    yy, xx = np.mgrid[0:size, 0:size]
    cx, cy = (size - 1) * 0.5, (size - 1) * 0.5
    r = np.sqrt(((xx - cx) / cx) ** 2 + ((yy - cy) / cy) ** 2)
    falloff = np.clip(1.0 - r, 0.0, 1.0) ** 1.85
    arr = np.zeros((size, size, 4), dtype=np.uint8)
    for ch in range(3):
        c = rgb[ch]
        if core_bright:
            val = np.clip(c + (255 - c) * (falloff ** 2.2), 0, 255)
        else:
            val = np.full_like(falloff, c)
        arr[:, :, ch] = val.astype(np.uint8)
    arr[:, :, 3] = np.clip(falloff * 255.0 * alpha_peak, 0, 255).astype(np.uint8)
    return Image.fromarray(arr, mode="RGBA")


def _make_spark_star(size: int, rgb: Tuple[int, int, int]) -> Image.Image:
    """Bintang percikan ramping meruncing (cel-shaded spark, bukan garis kotak!)."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    glow = _make_soft_puff(size, rgb, alpha_peak=0.88, core_bright=True)
    img.paste(glow, (0, 0), glow)
    draw = ImageDraw.Draw(img)
    c = size * 0.5
    # 4-point tapered diamond star
    pts = []
    for i in range(8):
        a = i * math.pi * 0.25
        r = c * (0.86 if i % 2 == 0 else 0.14)
        pts.append((c + math.cos(a) * r, c + math.sin(a) * r))
    draw.polygon(pts, fill=(255, 255, 255, 235))
    return img


class SpriteCache:
    """Cache & factory sprite 2.5D -> 3D billboard untuk seluruh cast dan FX partikel."""

    def __init__(self, char_scale: float = 2.4, prop_scale: float = 2.6) -> None:
        self.bima = BimaHeroCharacter(scale=char_scale, fps=30, hero_details=True)
        self.oren = OrenCharacter(scale=char_scale)
        self.gold_key = GoldenKeyProp(scale=prop_scale)
        self.silver_key = SilverKeyProp(scale=prop_scale)
        self.pedagang = create_pedagang_rempah(scale=char_scale * 0.85, fps=30)
        self.penumpang = create_penumpang_trem(scale=char_scale * 0.85, fps=30)

        self._img_cache: Dict[str, Image.Image] = {}

        # Pre-built soft volumetric 3D particle textures
        self.puff_turmeric = _make_soft_puff(128, (248, 198, 28), alpha_peak=0.92, core_bright=True)
        self.puff_chili = _make_soft_puff(128, (226, 62, 34), alpha_peak=0.82, core_bright=False)
        self.puff_emerald_steam = _make_soft_puff(128, (48, 224, 166), alpha_peak=0.74, core_bright=True)
        self.puff_golden_dust = _make_soft_puff(96, (255, 232, 148), alpha_peak=0.88, core_bright=True)
        self.puff_coffee_steam = _make_soft_puff(96, (236, 242, 252), alpha_peak=0.55, core_bright=False)
        self.spark_emerald = _make_spark_star(128, (54, 245, 212))
        self.spark_gold = _make_spark_star(128, (255, 224, 96))

    def _put_cache(self, key: str, img: Image.Image) -> Image.Image:
        if len(self._img_cache) > 160:
            old_k = next(iter(self._img_cache))
            del self._img_cache[old_k]
        self._img_cache[key] = img
        return img

    def render_bima(
        self,
        rig: HumanoidRig,
        lighting_phase: str,
        animation: str = "static",
        frame: int = 0,
        cache_tag: Optional[str] = None,
    ) -> Tuple[Image.Image, Optional[str]]:
        if cache_tag and cache_tag in self._img_cache:
            return self._img_cache[cache_tag], cache_tag
        img = self.bima.render_pil(frame=frame, animation=animation, rig=rig, lighting_phase=lighting_phase)  # type: ignore[arg-type]
        if cache_tag:
            self._put_cache(cache_tag, img)
        return img, cache_tag

    def render_oren(self, rig: OrenRig, cache_tag: Optional[str] = None) -> Tuple[Image.Image, Optional[str]]:
        if cache_tag and cache_tag in self._img_cache:
            return self._img_cache[cache_tag], cache_tag
        img = self.oren.render_pil(rig=rig)
        if cache_tag:
            self._put_cache(cache_tag, img)
        return img, cache_tag

    def render_golden_key(self, rig: KeyPropRig, cache_tag: Optional[str] = None) -> Tuple[Image.Image, Optional[str]]:
        if cache_tag and cache_tag in self._img_cache:
            return self._img_cache[cache_tag], cache_tag
        img = self.gold_key.render_pil(rig=rig)
        if cache_tag:
            self._put_cache(cache_tag, img)
        return img, cache_tag

    def render_silver_key(self, rig: KeyPropRig, cache_tag: Optional[str] = None) -> Tuple[Image.Image, Optional[str]]:
        if cache_tag and cache_tag in self._img_cache:
            return self._img_cache[cache_tag], cache_tag
        img = self.silver_key.render_pil(rig=rig)
        if cache_tag:
            self._put_cache(cache_tag, img)
        return img, cache_tag

    def render_pedagang(self, rig: HumanoidRig, cache_tag: Optional[str] = None) -> Tuple[Image.Image, Optional[str]]:
        if cache_tag and cache_tag in self._img_cache:
            return self._img_cache[cache_tag], cache_tag
        img = self.pedagang.render_pil(animation="static", rig=rig)
        if cache_tag:
            self._put_cache(cache_tag, img)
        return img, cache_tag

    def render_penumpang(self, rig: HumanoidRig, cache_tag: Optional[str] = None) -> Tuple[Image.Image, Optional[str]]:
        if cache_tag and cache_tag in self._img_cache:
            return self._img_cache[cache_tag], cache_tag
        img = self.penumpang.render_pil(animation="static", rig=rig)
        if cache_tag:
            self._put_cache(cache_tag, img)
        return img, cache_tag
