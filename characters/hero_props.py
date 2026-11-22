"""
Hero Props — Kunci Emas (Master Clock Key, ~14 cm) & Kunci Perak (Plot Twist Key, ~11 cm)

Menggunakan SvgCanvas2D + resvg_py yang sama dengan generator.html agar pita specular
cel-shaded, patina gelap, goresan micro-PBR, dan outline variabel menyatu 100% dengan
Bima & seluruh adegan 3D Python.
"""

from __future__ import annotations

import math
from typing import Any, Optional

from . import bima_character as _eng
from .rig_controls import KeyPropRig


_KEY_PHASE_GLOW = {
    "phase1": ("rgba(255, 240, 175, 0.72)", "rgba(255, 198, 72, 0.28)"),
    "phase2": ("rgba(148, 255, 214, 0.72)", "rgba(38, 224, 152, 0.28)"),
    "phase3_crimson": ("rgba(255, 216, 152, 0.76)", "rgba(255, 92, 52, 0.32)"),
    "phase3_twilight": ("rgba(198, 252, 255, 0.78)", "rgba(86, 232, 255, 0.30)"),
}


def render_golden_key_canvas(
    ctx: Any,
    yaw_deg: float = 0.0,
    tilt_deg: float = -22.0,
    scale: float = 3.0,
    sun_glow: bool = True,
    pitch_deg: float = 0.0,
    glow_intensity: float = 1.0,
    sparkle_alpha: float = 1.0,
    extrude_depth: float = 1.0,
    lighting_phase: str = "phase1",
) -> None:
    """
    Render Kunci Emas (Master Clock Key ~14 cm) dengan transformasi 3D terbuka:
      - Kepala roda gigi matahari BERONGGA (celah transparan di tengah agar sinar Low Sun
        & haze menembus langsung di [CAM 01]!)
      - Kuningan emas antik berpatina gelap di lekukan ukiran + micro-scratches + pita specular cel-shade
    """
    rad = math.radians(yaw_deg)
    cos_y = math.cos(rad)
    sin_y = math.sin(rad)
    sc_x = max(0.18, abs(cos_y))
    sc_y = max(0.28, abs(math.cos(math.radians(pitch_deg))))
    extrude_dx = -sin_y * 7.0 * float(extrude_depth)

    ctx.save()
    ctx.setTransform(scale, 0, 0, scale, 0, 0)
    ctx.clearRect(0, 0, 260, 420)

    # Optional phase-reactive glow piercing through hollow sun-gear bow
    if sun_glow and glow_intensity > 0.01:
        g0, g1 = _KEY_PHASE_GLOW.get(lighting_phase, _KEY_PHASE_GLOW["phase1"])
        ctx.save()
        ctx.globalAlpha = max(0.0, min(1.0, float(glow_intensity)))
        gl = ctx.createRadialGradient(130, 128, 6, 130, 128, 92)
        gl.addColorStop(0, g0)
        gl.addColorStop(0.42, g1)
        gl.addColorStop(1, "rgba(255, 180, 40, 0)")
        ctx.fillStyle = gl
        ctx.beginPath()
        ctx.arc(130, 128, 92, 0, math.pi * 2)
        ctx.fill()
        ctx.restore()

    ctx.save()
    ctx.translate(130, 210)
    ctx.rotate(math.radians(tilt_deg))
    ctx.scale(sc_x, sc_y)

    def trace_sun_gear_outer(ox: float, oy: float) -> None:
        teeth = 12
        r_out = 54.0
        r_in = 42.5
        ctx.beginPath()
        for i in range(teeth * 2):
            a = (i * math.pi) / teeth
            r = r_out if (i % 2 == 0) else r_in
            # Sedikit datar di puncak gigi roda matahari
            a_shift = a - 0.06 if (i % 2 == 0) else a
            px = ox + math.cos(a_shift) * r
            py = oy + math.sin(a_shift) * r
            if i == 0:
                ctx.moveTo(px, py)
            else:
                ctx.lineTo(px, py)
            if i % 2 == 0:
                a2 = a + 0.06
                ctx.lineTo(ox + math.cos(a2) * r, oy + math.sin(a2) * r)
        ctx.closePath()

    def trace_hollow_bow_evenodd(ox: float, oy: float) -> None:
        # Cincin roda gigi matahari berongga memakai dua path (outer + lubang tengah)
        trace_sun_gear_outer(ox, oy)

    # --- 1. EXTRUDED 3D DEPTH WALL (sisi tebal kuningan gelap berpatina) ---
    ctx.fillStyle = "#5E3F0A"
    ctx.strokeStyle = "#1E141B"
    ctx.lineWidth = 3.2
    ctx.lineJoin = "round"

    # Depth wall batang & gigi kunci
    ctx.beginPath()
    ctx.roundRect(-8.5 + extrude_dx, -38, 17.0, 212, 6.0)
    ctx.fill()
    ctx.stroke()

    # Depth wall gigi bit mekanik
    ctx.beginPath()
    ctx.moveTo(6 + extrude_dx, 108)
    ctx.lineTo(44 + extrude_dx, 108)
    ctx.lineTo(44 + extrude_dx, 122)
    ctx.lineTo(29 + extrude_dx, 122)
    ctx.lineTo(29 + extrude_dx, 134)
    ctx.lineTo(46 + extrude_dx, 134)
    ctx.lineTo(46 + extrude_dx, 149)
    ctx.lineTo(20 + extrude_dx, 149)
    ctx.lineTo(20 + extrude_dx, 162)
    ctx.lineTo(38 + extrude_dx, 162)
    ctx.lineTo(38 + extrude_dx, 173)
    ctx.lineTo(6 + extrude_dx, 173)
    ctx.closePath()
    ctx.fill()
    ctx.stroke()

    # Depth wall kepala roda gigi matahari
    trace_sun_gear_outer(extrude_dx, -86)
    ctx.fill()
    ctx.stroke()

    # --- 2. FRONT FACE KUNINGAN EMAS ANTIK + PITA SPECULAR CEL-SHADE ---
    brass_g = ctx.createLinearGradient(-52, -140, 56, 175)
    brass_g.addColorStop(0.0, "#8B600A")
    brass_g.addColorStop(0.24, "#D9A426")
    brass_g.addColorStop(0.46, "#FFE57A")
    brass_g.addColorStop(0.54, "#FFF9D6")  # pita specular tegas cel-shade!
    brass_g.addColorStop(0.64, "#E2AE2B")
    brass_g.addColorStop(0.88, "#9E6E0E")
    brass_g.addColorStop(1.0, "#6E4A08")

    # Batang silinder kunci bertingkat
    ctx.fillStyle = brass_g
    ctx.strokeStyle = "#1E141B"
    ctx.lineWidth = 3.0
    ctx.beginPath()
    ctx.roundRect(-8.5, -40, 17.0, 214, 6.0)
    ctx.fill()
    ctx.stroke()

    # Cincin dekoratif bertingkat pada leher batang
    for cy_ring, rw, rh in [(-32, 26, 9), (-18, 22, 7), (78, 22, 8)]:
        ctx.fillStyle = brass_g
        ctx.beginPath()
        ctx.roundRect(-rw * 0.5, cy_ring, rw, rh, 3.2)
        ctx.fill()
        ctx.stroke()
        # Garis patina gelap di lekukan ukiran
        ctx.strokeStyle = "#4A3006"
        ctx.lineWidth = 1.4
        ctx.beginPath()
        ctx.moveTo(-rw * 0.42, cy_ring + rh - 1.5)
        ctx.lineTo(rw * 0.42, cy_ring + rh - 1.5)
        ctx.stroke()
        ctx.strokeStyle = "#1E141B"
        ctx.lineWidth = 3.0

    # Gigi bit kunci mekanis rumit
    ctx.fillStyle = brass_g
    ctx.beginPath()
    ctx.moveTo(6, 108)
    ctx.lineTo(44, 108)
    ctx.lineTo(44, 122)
    ctx.lineTo(28, 122)
    ctx.lineTo(28, 134)
    ctx.lineTo(46, 134)
    ctx.lineTo(46, 149)
    ctx.lineTo(20, 149)
    ctx.lineTo(20, 162)
    ctx.lineTo(38, 162)
    ctx.lineTo(38, 173)
    ctx.lineTo(6, 173)
    ctx.closePath()
    ctx.fill()
    ctx.stroke()

    # Lekukan ukiran patina gelap pada gigi bit
    ctx.fillStyle = "rgba(58, 36, 6, 0.48)"
    ctx.fillRect(11, 113, 28, 4.0)
    ctx.fillRect(11, 139, 30, 4.5)

    # Kepala Roda Gigi Matahari (Outer Face)
    ctx.fillStyle = brass_g
    trace_sun_gear_outer(0, -86)
    ctx.fill()
    ctx.stroke()

    # Alur ukiran patina gelap konsentris di sekitar cincin roda gigi
    ctx.strokeStyle = "#5A3A08"
    ctx.lineWidth = 2.6
    ctx.beginPath()
    ctx.arc(0, -86, 35.5, 0, math.pi * 2)
    ctx.stroke()

    # 8 paku keling & sinar ukir kecil
    for i in range(8):
        a = (i * math.pi) / 4.0
        rx, ry = math.cos(a) * 35.5, -86 + math.sin(a) * 35.5
        ctx.fillStyle = "#FFF7CC"
        ctx.strokeStyle = "#4A3006"
        ctx.lineWidth = 1.2
        ctx.beginPath()
        ctx.arc(rx, ry, 2.2, 0, math.pi * 2)
        ctx.fill()
        ctx.stroke()

    # Lubang berongga di tengah (menampilkan cahaya matahari & haze yang menembus!)
    # Pinggiran bevel bagian dalam lubang
    ctx.fillStyle = "#6E4B0B"
    ctx.strokeStyle = "#1E141B"
    ctx.lineWidth = 2.6
    ctx.beginPath()
    ctx.arc(0, -86, 25.0, 0, math.pi * 2)
    ctx.fill()
    ctx.stroke()

    # Isi lubang cahaya matahari hangat (simulasi celah transparan ditembus Low Sun haze!)
    hole_g = ctx.createRadialGradient(2, -88, 2, 0, -86, 22)
    if sun_glow:
        hole_g.addColorStop(0, "#FFFDF0")
        hole_g.addColorStop(0.55, "#FFE08A")
        hole_g.addColorStop(1, "rgba(240, 178, 72, 0.35)")
    else:
        hole_g.addColorStop(0, "rgba(255, 255, 255, 0)")
        hole_g.addColorStop(1, "rgba(255, 255, 255, 0)")
    ctx.fillStyle = hole_g
    ctx.beginPath()
    ctx.arc(extrude_dx * 0.4, -86, 21.5, 0, math.pi * 2)
    ctx.fill()

    # 4 jari-jari halus penopang cincin matahari dengan celah lubang terbuka
    ctx.strokeStyle = "#1E141B"
    ctx.lineWidth = 4.6
    for a in [0, math.pi * 0.5, math.pi, math.pi * 1.5]:
        ctx.beginPath()
        ctx.moveTo(math.cos(a) * 12.0, -86 + math.sin(a) * 12.0)
        ctx.lineTo(math.cos(a) * 24.5, -86 + math.sin(a) * 24.5)
        ctx.stroke()
    ctx.strokeStyle = "#F5C846"
    ctx.lineWidth = 2.2
    for a in [0, math.pi * 0.5, math.pi, math.pi * 1.5]:
        ctx.beginPath()
        ctx.moveTo(math.cos(a) * 12.0, -86 + math.sin(a) * 12.0)
        ctx.lineTo(math.cos(a) * 24.5, -86 + math.sin(a) * 24.5)
        ctx.stroke()

    # Cincin pusat kecil berongga
    ctx.strokeStyle = "#1E141B"
    ctx.lineWidth = 4.8
    ctx.beginPath()
    ctx.arc(0, -86, 10.5, 0, math.pi * 2)
    ctx.stroke()
    ctx.strokeStyle = "#FFE074"
    ctx.lineWidth = 2.4
    ctx.beginPath()
    ctx.arc(0, -86, 10.5, 0, math.pi * 2)
    ctx.stroke()

    # Goresan logam micro-PBR realistis (scratched brass!)
    ctx.strokeStyle = "rgba(74, 46, 8, 0.52)"
    ctx.lineWidth = 1.0
    for x1, y1, x2, y2 in [
        (-28, -112, -16, -104),
        (24, -64, 34, -72),
        (-4, 14, 5, 22),
        (-5, 58, 4, 52),
        (16, 118, 34, 114),
    ]:
        ctx.beginPath()
        ctx.moveTo(x1, y1)
        ctx.lineTo(x2, y2)
        ctx.stroke()

    # Pita specular cel-shade tajam di batang & kepala
    ctx.strokeStyle = "rgba(255, 254, 240, 0.92)"
    ctx.lineWidth = 3.2
    ctx.lineCap = "round"
    ctx.beginPath()
    ctx.moveTo(3.2, -10)
    ctx.lineTo(3.2, 68)
    ctx.moveTo(16, -124)
    ctx.quadraticCurveTo(34, -112, 38, -90)
    ctx.stroke()

    # Bintang kilau cel-shade khas anime/kartun 3D
    ctx.fillStyle = "#FFFFFF"
    sx, sy = 36, -114
    ctx.beginPath()
    ctx.moveTo(sx, sy - 11)
    ctx.lineTo(sx + 2.5, sy - 2.5)
    ctx.lineTo(sx + 11, sy)
    ctx.lineTo(sx + 2.5, sy + 2.5)
    ctx.lineTo(sx, sy + 11)
    ctx.lineTo(sx - 2.5, sy + 2.5)
    ctx.lineTo(sx - 11, sy)
    ctx.lineTo(sx - 2.5, sy - 2.5)
    ctx.closePath()
    ctx.fill()

    ctx.restore()
    ctx.restore()


def render_silver_key_canvas(
    ctx: Any,
    yaw_deg: float = 0.0,
    tilt_deg: float = 20.0,
    scale: float = 3.0,
) -> None:
    """
    Render Kunci Perak (Plot Twist Key — [CAM 27], ~11 cm — lebih ramping dari Kunci Emas):
      - Kepala berbentuk bulan sabit mekanis & gerigi tajam
      - Material perak dingin kebiruan (#D6E4F0) bertekstur brushed steel + guratan halus
    """
    rad = math.radians(yaw_deg)
    cos_y = math.cos(rad)
    sin_y = math.sin(rad)
    sc_x = max(0.18, abs(cos_y))
    extrude_dx = -sin_y * 5.5

    ctx.save()
    ctx.setTransform(scale, 0, 0, scale, 0, 0)
    ctx.clearRect(0, 0, 260, 420)

    # Aura dingin kebiruan tipis agar terasa kontras dingin vs kuning hangat
    gl = ctx.createRadialGradient(130, 140, 8, 130, 140, 76)
    gl.addColorStop(0, "rgba(186, 224, 255, 0.36)")
    gl.addColorStop(1, "rgba(140, 192, 240, 0)")
    ctx.fillStyle = gl
    ctx.beginPath()
    ctx.arc(130, 140, 76, 0, math.pi * 2)
    ctx.fill()

    ctx.save()
    ctx.translate(130, 215)
    ctx.rotate(math.radians(tilt_deg))
    # Skala 0.82x (lebih ramping & pendek: ~11 cm dibanding Kunci Emas ~14 cm!)
    ctx.scale(sc_x * 0.84, 0.84)

    def trace_crescent_bow(ox: float, oy: float) -> None:
        ctx.beginPath()
        ctx.arc(ox, oy, 46.0, 0.52, math.pi * 2 - 0.52)
        ctx.arc(ox + 18.0, oy - 2.0, 34.0, math.pi * 2 - 0.78, 0.78, True)
        ctx.closePath()

    # 1. Extruded dark steel side wall
    ctx.fillStyle = "#485E78"
    ctx.strokeStyle = "#171E2B"
    ctx.lineWidth = 3.2
    ctx.lineJoin = "round"
    ctx.beginPath()
    ctx.roundRect(-6.5 + extrude_dx, -36, 13.0, 198, 5.0)
    ctx.fill()
    ctx.stroke()

    # Sharp precision serrated bit teeth (depth wall)
    ctx.beginPath()
    ctx.moveTo(5 + extrude_dx, 102)
    ctx.lineTo(38 + extrude_dx, 108)
    ctx.lineTo(22 + extrude_dx, 118)
    ctx.lineTo(42 + extrude_dx, 128)
    ctx.lineTo(20 + extrude_dx, 138)
    ctx.lineTo(36 + extrude_dx, 150)
    ctx.lineTo(5 + extrude_dx, 158)
    ctx.closePath()
    ctx.fill()
    ctx.stroke()

    trace_crescent_bow(extrude_dx, -82)
    ctx.fill()
    ctx.stroke()

    # 2. Front brushed steel cold silver (#D6E4F0)
    steel_g = ctx.createLinearGradient(-46, -130, 48, 165)
    steel_g.addColorStop(0.0, "#6E86A2")
    steel_g.addColorStop(0.28, "#B8CEE2")
    steel_g.addColorStop(0.48, "#D6E4F0")
    steel_g.addColorStop(0.55, "#FFFFFF")  # crisp cold specular band
    steel_g.addColorStop(0.68, "#9EB7D0")
    steel_g.addColorStop(1.0, "#506782")

    # Slim shaft
    ctx.fillStyle = steel_g
    ctx.strokeStyle = "#171E2B"
    ctx.lineWidth = 2.8
    ctx.beginPath()
    ctx.roundRect(-6.5, -38, 13.0, 200, 5.0)
    ctx.fill()
    ctx.stroke()

    # Collar rings
    for cy_r, rw in [(-32, 20), (-19, 17), (74, 18)]:
        ctx.fillStyle = steel_g
        ctx.beginPath()
        ctx.roundRect(-rw * 0.5, cy_r, rw, 6.5, 2.5)
        ctx.fill()
        ctx.stroke()

    # Sharp toothed bit
    ctx.fillStyle = steel_g
    ctx.beginPath()
    ctx.moveTo(5, 102)
    ctx.lineTo(38, 108)
    ctx.lineTo(22, 118)
    ctx.lineTo(42, 128)
    ctx.lineTo(20, 138)
    ctx.lineTo(36, 150)
    ctx.lineTo(5, 158)
    ctx.closePath()
    ctx.fill()
    ctx.stroke()

    # Mechanical crescent moon bow
    ctx.fillStyle = steel_g
    trace_crescent_bow(0, -82)
    ctx.fill()
    ctx.stroke()

    # Roda gigi mekanis mini terpasang di dalam lengkung bulan sabit!
    ctx.save()
    ctx.translate(16, -82)
    ctx.fillStyle = "#A9C1D9"
    ctx.strokeStyle = "#171E2B"
    ctx.lineWidth = 2.0
    ctx.beginPath()
    for i in range(16):
        a = (i * math.pi) / 8.0
        r = 16.5 if (i % 2 == 0) else 12.2
        if i == 0:
            ctx.moveTo(math.cos(a) * r, math.sin(a) * r)
        else:
            ctx.lineTo(math.cos(a) * r, math.sin(a) * r)
    ctx.closePath()
    ctx.fill()
    ctx.stroke()
    ctx.fillStyle = "#2E3F57"
    ctx.beginPath()
    ctx.arc(0, 0, 5.5, 0, math.pi * 2)
    ctx.fill()
    ctx.stroke()
    ctx.restore()

    # Guratan brushed steel halus
    ctx.strokeStyle = "rgba(44, 62, 86, 0.36)"
    ctx.lineWidth = 0.9
    for y_br in range(-114, -46, 7):
        ctx.beginPath()
        ctx.moveTo(-40, y_br)
        ctx.lineTo(-14, y_br - 2)
        ctx.stroke()
    for y_sh in range(-6, 92, 11):
        ctx.beginPath()
        ctx.moveTo(-4, y_sh)
        ctx.lineTo(4, y_sh - 1.5)
        ctx.stroke()

    # Specular cel-shade dingin pada tepi bulan sabit & batang
    ctx.strokeStyle = "rgba(244, 252, 255, 0.94)"
    ctx.lineWidth = 2.8
    ctx.lineCap = "round"
    ctx.beginPath()
    ctx.moveTo(2.4, -10)
    ctx.lineTo(2.4, 64)
    ctx.moveTo(-34, -104)
    ctx.quadraticCurveTo(-40, -82, -32, -60)
    ctx.stroke()

    ctx.restore()
    ctx.restore()


class GoldenKeyProp:
    """Kunci Emas (Master Clock Key ~14 cm) — Hero Prop Utama dengan kontrol 3D terbuka (`KeyPropRig`)."""

    def __init__(self, scale: float = 3.0) -> None:
        self.scale = float(scale)

    def render_svg(
        self,
        yaw_deg: Optional[float] = None,
        tilt_deg: Optional[float] = None,
        sun_glow: Optional[bool] = None,
        rig: Optional[KeyPropRig] = None,
        **rig_overrides: Any,
    ) -> str:
        r = KeyPropRig(**vars(rig)) if rig is not None else KeyPropRig(roll_deg=-22.0)
        if yaw_deg is not None:
            r.yaw_deg = float(yaw_deg)
        if tilt_deg is not None:
            r.roll_deg = float(tilt_deg)
        if sun_glow is not None:
            r.sun_glow = bool(sun_glow)
        for k, v in rig_overrides.items():
            if hasattr(r, k):
                setattr(r, k, v)
        ctx = _eng.SvgCanvas2D(int(round(260 * self.scale)), int(round(420 * self.scale)))
        render_golden_key_canvas(
            ctx,
            yaw_deg=r.yaw_deg,
            tilt_deg=r.roll_deg,
            scale=self.scale,
            sun_glow=r.sun_glow,
            pitch_deg=r.pitch_deg,
            glow_intensity=r.glow_intensity,
            sparkle_alpha=r.sparkle_alpha,
            extrude_depth=r.extrude_depth,
            lighting_phase=r.lighting_phase,
        )
        return ctx.to_svg()

    def render_pil(self, **kwargs: Any) -> Any:
        import io
        import resvg_py
        from PIL import Image

        png_bytes = resvg_py.svg_to_bytes(svg_string=self.render_svg(**kwargs), skip_system_fonts=True)
        return Image.open(io.BytesIO(png_bytes)).convert("RGBA")


class SilverKeyProp:
    """Kunci Perak (Plot Twist Key ~11 cm, [CAM 27]) — Hero Prop Ending dengan kontrol 3D terbuka (`KeyPropRig`)."""

    def __init__(self, scale: float = 3.0) -> None:
        self.scale = float(scale)

    def render_svg(
        self,
        yaw_deg: Optional[float] = None,
        tilt_deg: Optional[float] = None,
        rig: Optional[KeyPropRig] = None,
        **rig_overrides: Any,
    ) -> str:
        r = KeyPropRig(**vars(rig)) if rig is not None else KeyPropRig(roll_deg=20.0)
        if yaw_deg is not None:
            r.yaw_deg = float(yaw_deg)
        if tilt_deg is not None:
            r.roll_deg = float(tilt_deg)
        for k, v in rig_overrides.items():
            if hasattr(r, k):
                setattr(r, k, v)
        ctx = _eng.SvgCanvas2D(int(round(260 * self.scale)), int(round(420 * self.scale)))
        render_silver_key_canvas(ctx, yaw_deg=r.yaw_deg, tilt_deg=r.roll_deg, scale=self.scale)
        return ctx.to_svg()

    def render_pil(self, **kwargs: Any) -> Any:
        import io
        import resvg_py
        from PIL import Image

        png_bytes = resvg_py.svg_to_bytes(svg_string=self.render_svg(**kwargs), skip_system_fonts=True)
        return Image.open(io.BytesIO(png_bytes)).convert("RGBA")
