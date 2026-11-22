"""
OrenCharacter — "Oren" Kucing Kampung Gang Kafe (Desain Karakter + Rigging 100% Terbuka)

Dibangun di atas backend SvgCanvas2D + resvg_py yang sama dengan generator.html
agar gaya 3D Cel-Shaded, variable-width ink outline, stepped shadow, dan fuzzy
golden rim-light menyatu 100% dengan Bima & figuran.

RIGGING TIDAK TERKUNCI:
  - Default selalu pose desain netral (`OrenRig()`).
  - Semua tulang & ekspresi (posisi cakar kiri/kanan, paw pads, keluarnya kuku, tinggi kelopak mata,
    lirikan gaze, ekspresi mulut, gerak telinga, lengkung & ayunan ekor pegas, ayunan lonceng,
    kemiringan tubuh/kepala, squash-stretch, rim light) bebas diatur per adegan melalui `OrenRig`.
"""

from __future__ import annotations

import math
from typing import Any, Optional

from . import bima_character as _eng
from .rig_controls import OrenRig

OREN_PALETTE = {
    "fur_main": "#E67E22",
    "fur_light": "#F5A14B",
    "fur_dark": "#B65312",
    "stripe": "#A3450E",
    "belly": "#F5E6CA",
    "belly_shade": "#D9C39E",
    "collar": "#4F9DA6",
    "collar_dark": "#2D646C",
    "bell": "#C2723E",
    "bell_hi": "#F8C89B",
    "eye_olive": "#7E9A32",
    "eye_olive_hi": "#B9D45C",
    "nose_pink": "#DC8A8E",
    "paw_pad": "#B56D68",
    "ink": "#1E141C",
    "rim_gold": "#FFE4A0",
}


def _draw_paw_pad_closeup(
    ctx: Any,
    x: float,
    y: float,
    rot: float,
    scale: float,
    claws_out: float,
    rim_i: float,
    rim_color: str,
) -> None:
    """Cakar depan lebar dengan bantalan cakar (paw pads) bertekstur kulit kasar."""
    ctx.save()
    ctx.translate(x, y)
    ctx.rotate(rot)
    ctx.scale(scale, scale)

    paw_g = ctx.createRadialGradient(4, -5, 2, 0, 0, 26)
    paw_g.addColorStop(0, OREN_PALETTE["belly"])
    paw_g.addColorStop(0.55, OREN_PALETTE["fur_light"])
    paw_g.addColorStop(1, OREN_PALETTE["fur_dark"])
    ctx.fillStyle = paw_g
    ctx.strokeStyle = OREN_PALETTE["ink"]
    ctx.lineWidth = 3.2
    ctx.beginPath()
    ctx.ellipse(0, 2, 22, 18.5, 0, 0, math.pi * 2)
    ctx.fill()
    ctx.stroke()

    for tx, ty, tr in [(-14, -12, 7.6), (0, -16, 8.2), (14, -11, 7.6)]:
        ctx.fillStyle = OREN_PALETTE["belly"]
        ctx.beginPath()
        ctx.arc(tx, ty, tr, 0, math.pi * 2)
        ctx.fill()
        ctx.stroke()

    pad_g = ctx.createRadialGradient(-2, 4, 1, 0, 6, 13)
    pad_g.addColorStop(0, "#CE847E")
    pad_g.addColorStop(0.65, OREN_PALETTE["paw_pad"])
    pad_g.addColorStop(1, "#7B403D")
    ctx.fillStyle = pad_g
    ctx.strokeStyle = "#4A2322"
    ctx.lineWidth = 1.6
    ctx.beginPath()
    ctx.moveTo(0, -1)
    ctx.bezierCurveTo(10, -2, 13, 9, 6, 13)
    ctx.quadraticCurveTo(0, 11, -6, 13)
    ctx.bezierCurveTo(-13, 9, -10, -2, 0, -1)
    ctx.closePath()
    ctx.fill()
    ctx.stroke()

    for bx, by, brx, bry in [(-13.5, -11.5, 4.3, 5.2), (0, -15.5, 4.6, 5.6), (13.5, -10.5, 4.3, 5.2)]:
        ctx.fillStyle = pad_g
        ctx.beginPath()
        ctx.ellipse(bx, by, brx, bry, bx * 0.015, 0, math.pi * 2)
        ctx.fill()
        ctx.stroke()

    ctx.fillStyle = "rgba(62, 24, 24, 0.36)"
    for dx, dy in [(-4, 5), (0, 8), (4, 5), (-2, 10), (3, 9), (-13, -11), (0, -15), (13, -10)]:
        ctx.beginPath()
        ctx.arc(dx, dy, 0.9, 0, math.pi * 2)
        ctx.fill()

    # Kuku tipis keluar secara proporsional mengikuti rig.claws_out (0..1)
    if claws_out > 0.05:
        cl = max(0.0, min(1.0, claws_out))
        ctx.fillStyle = "#FFF9EE"
        ctx.strokeStyle = OREN_PALETTE["ink"]
        ctx.lineWidth = 1.6
        for cx, cy, rot_c in [(-16, -20, -0.35), (0, -25, 0.0), (16, -19, 0.35)]:
            ctx.save()
            ctx.translate(cx, cy + (1.0 - cl) * 5.0)
            ctx.rotate(rot_c)
            ctx.beginPath()
            ctx.moveTo(-2.2, 3)
            ctx.quadraticCurveTo(0, 3 - 8.5 * cl, 2.2, 3)
            ctx.closePath()
            ctx.fill()
            ctx.stroke()
            ctx.restore()

    if rim_i > 0.05:
        ctx.strokeStyle = rim_color
        ctx.globalAlpha = 0.65 * rim_i
        ctx.lineWidth = 2.0
        ctx.beginPath()
        ctx.arc(0, 2, 19.5, -0.7, 0.6)
        ctx.stroke()

    ctx.restore()


def render_oren_canvas(
    ctx: Any,
    rig: Optional[OrenRig] = None,
    scale: float = 3.0,
) -> None:
    """Render 360° karakter Oren secara langsung dari parameter OrenRig tanpa animasi terkunci."""
    r = rig or OrenRig()
    deg = ((float(r.angle) % 360.0) + 360.0) % 360.0
    rad = math.radians(deg)
    s = math.sin(rad)
    c = math.cos(rad)
    ox = 140.0

    by_off = float(r.body_bob)
    tail_sway = float(r.tail_sway)
    tail_curl = float(r.tail_curl)
    bell_sway = float(r.bell_sway)
    rim_intensity = float(r.rim_intensity)
    rim_color = r.rim_color or OREN_PALETTE["rim_gold"]

    ctx.save()
    ctx.setTransform(scale, 0, 0, scale, 0, 0)
    ctx.clearRect(0, 0, 280, 320)

    # 0. Ground contact shadow
    if r.ground_shadow:
        sg = ctx.createRadialGradient(ox, 286, 8, ox, 286, 76)
        sg.addColorStop(0, "rgba(24, 16, 26, 0.34)")
        sg.addColorStop(1, "rgba(24, 16, 26, 0)")
        ctx.fillStyle = sg
        ctx.beginPath()
        ctx.ellipse(ox, 286, 76, 15, 0, 0, math.pi * 2)
        ctx.fill()

    # Root transform (squash-stretch & body lean)
    ctx.save()
    ctx.translate(ox, 282)
    ctx.scale(float(r.squash_x), float(r.squash_y))
    ctx.rotate(float(r.body_lean))
    ctx.translate(-ox, -282)

    # 1. EKOR TEBAL (bebas dikontrol lewat tail_sway & tail_curl)
    def draw_tail() -> None:
        tx0 = ox - s * 44
        ty0 = 248 + by_off
        side_dir = -1.0 if s >= -0.2 else 1.0
        tx1 = tx0 + side_dir * 58.0 + tail_sway * 0.6
        ty1 = 194 + by_off - tail_curl * 8.0
        tx2 = tx0 + side_dir * (44.0 - tail_curl * 12.0) + tail_sway * 1.25
        ty2 = 132 + by_off + tail_curl * 14.0

        ctx.save()
        ctx.lineCap = "round"
        ctx.lineJoin = "round"
        ctx.strokeStyle = OREN_PALETTE["ink"]
        ctx.lineWidth = 27.0
        ctx.beginPath()
        ctx.moveTo(tx0, ty0)
        ctx.bezierCurveTo(tx1, ty1 + 26, tx1, ty1 - 24, tx2, ty2)
        ctx.stroke()

        tail_g = ctx.createLinearGradient(tx0, ty0, tx2, ty2)
        tail_g.addColorStop(0, OREN_PALETTE["fur_dark"])
        tail_g.addColorStop(0.55, OREN_PALETTE["fur_main"])
        tail_g.addColorStop(1, OREN_PALETTE["fur_light"])
        ctx.strokeStyle = tail_g
        ctx.lineWidth = 20.5
        ctx.beginPath()
        ctx.moveTo(tx0, ty0)
        ctx.bezierCurveTo(tx1, ty1 + 26, tx1, ty1 - 24, tx2, ty2)
        ctx.stroke()

        ctx.strokeStyle = OREN_PALETTE["stripe"]
        ctx.lineWidth = 5.2
        for u in [0.28, 0.52, 0.74]:
            bx = (1 - u) ** 3 * tx0 + 3 * (1 - u) ** 2 * u * tx1 + 3 * (1 - u) * u ** 2 * tx1 + u ** 3 * tx2
            by = (1 - u) ** 3 * ty0 + 3 * (1 - u) ** 2 * u * (ty1 + 26) + 3 * (1 - u) * u ** 2 * (ty1 - 24) + u ** 3 * ty2
            ctx.beginPath()
            ctx.moveTo(bx - 8.5, by - 2.5)
            ctx.lineTo(bx + 8.5, by + 2.5)
            ctx.stroke()

        ctx.fillStyle = OREN_PALETTE["belly"]
        ctx.beginPath()
        ctx.arc(tx2, ty2, 8.8, 0, math.pi * 2)
        ctx.fill()

        if rim_intensity > 0.05:
            ctx.strokeStyle = rim_color
            ctx.globalAlpha = 0.7 * rim_intensity
            ctx.lineWidth = 2.6
            ctx.beginPath()
            ctx.moveTo(tx0 + 6, ty0 - 6)
            ctx.bezierCurveTo(tx1 + 8, ty1 + 22, tx1 + 8, ty1 - 24, tx2 + 6, ty2)
            ctx.stroke()
        ctx.restore()

    if c >= -0.05:
        draw_tail()

    # 2. TUBUH BULAT PADAT SEPERTI BUAH PIR (CHUNKY PEAR-SHAPED)
    ctx.fillStyle = OREN_PALETTE["ink"]
    ctx.beginPath()
    ctx.moveTo(ox, 134 + by_off)
    ctx.bezierCurveTo(ox + 48, 134 + by_off, ox + 75, 198 + by_off, ox + 71, 252 + by_off)
    ctx.bezierCurveTo(ox + 68, 286 + by_off, ox + 36, 294 + by_off, ox, 294 + by_off)
    ctx.bezierCurveTo(ox - 40, 294 + by_off, ox - 74, 286 + by_off, ox - 76, 252 + by_off)
    ctx.bezierCurveTo(ox - 80, 198 + by_off, ox - 50, 134 + by_off, ox, 134 + by_off)
    ctx.closePath()
    ctx.fill()

    ctx.save()
    ctx.beginPath()
    ctx.moveTo(ox, 139 + by_off)
    ctx.bezierCurveTo(ox + 44, 139 + by_off, ox + 70, 200 + by_off, ox + 66, 250 + by_off)
    ctx.bezierCurveTo(ox + 63, 281 + by_off, ox + 34, 288 + by_off, ox, 288 + by_off)
    ctx.bezierCurveTo(ox - 34, 288 + by_off, ox - 66, 281 + by_off, ox - 69, 250 + by_off)
    ctx.bezierCurveTo(ox - 73, 200 + by_off, ox - 44, 139 + by_off, ox, 139 + by_off)
    ctx.closePath()
    ctx.clip()

    body_g = ctx.createLinearGradient(ox - 68, 180, ox + 68, 270)
    body_g.addColorStop(0, OREN_PALETTE["fur_dark"])
    body_g.addColorStop(0.28, OREN_PALETTE["fur_main"])
    body_g.addColorStop(0.76, OREN_PALETTE["fur_light"])
    body_g.addColorStop(1, OREN_PALETTE["fur_main"])
    ctx.fillStyle = body_g
    ctx.fillRect(ox - 80, 130, 160, 170)

    ctx.fillStyle = OREN_PALETTE["stripe"]
    for sy_line in [182, 206, 232, 256]:
        ctx.beginPath()
        ctx.moveTo(ox - 74, sy_line + by_off)
        ctx.quadraticCurveTo(ox - 42 + s * 16, sy_line + 8 + by_off, ox - 26 + s * 22, sy_line + 2 + by_off)
        ctx.quadraticCurveTo(ox - 44 + s * 16, sy_line + 15 + by_off, ox - 74, sy_line + 12 + by_off)
        ctx.closePath()
        ctx.fill()

        ctx.beginPath()
        ctx.moveTo(ox + 72, sy_line + by_off)
        ctx.quadraticCurveTo(ox + 42 + s * 16, sy_line + 8 + by_off, ox + 26 + s * 22, sy_line + 2 + by_off)
        ctx.quadraticCurveTo(ox + 44 + s * 16, sy_line + 15 + by_off, ox + 72, sy_line + 12 + by_off)
        ctx.closePath()
        ctx.fill()

    if c > -0.15:
        ctx.save()
        ctx.globalAlpha = min(1.0, (c + 0.15) * 3.0)
        belly_x = ox + s * 42
        ctx.translate(belly_x, 224 + by_off)
        ctx.scale(max(0.1, c), 1.0)
        bel_g = ctx.createRadialGradient(8, -14, 4, 0, 4, 52)
        bel_g.addColorStop(0, "#FFF6E5")
        bel_g.addColorStop(0.62, OREN_PALETTE["belly"])
        bel_g.addColorStop(1, OREN_PALETTE["belly_shade"])
        ctx.fillStyle = bel_g
        ctx.beginPath()
        ctx.moveTo(0, -56)
        ctx.bezierCurveTo(32, -52, 46, -12, 42, 34)
        ctx.bezierCurveTo(36, 58, 18, 64, 0, 64)
        ctx.bezierCurveTo(-18, 64, -36, 58, -42, 34)
        ctx.bezierCurveTo(-46, -12, -32, -52, 0, -56)
        ctx.closePath()
        ctx.fill()
        ctx.fillStyle = "rgba(138, 108, 82, 0.22)"
        ctx.beginPath()
        ctx.ellipse(-6, 42, 22, 11, 0.08, 0, math.pi * 2)
        ctx.fill()
        ctx.restore()

    ctx.fillStyle = "rgba(58, 22, 24, 0.34)"
    ctx.beginPath()
    ctx.moveTo(ox - 76, 175 + by_off)
    ctx.quadraticCurveTo(ox - 34, 244 + by_off, ox + 12, 290 + by_off)
    ctx.lineTo(ox - 76, 290 + by_off)
    ctx.closePath()
    ctx.fill()

    ctx.fillStyle = "rgba(48, 18, 24, 0.36)"
    ctx.beginPath()
    ctx.ellipse(ox + s * 12, 168 + by_off, 52, 12, 0, 0, math.pi * 2)
    ctx.fill()

    if rim_intensity > 0.05:
        ctx.strokeStyle = rim_color
        ctx.globalAlpha = min(0.95, 0.78 * rim_intensity)
        ctx.lineWidth = 4.6
        ctx.lineCap = "round"
        ctx.beginPath()
        ctx.moveTo(ox + 42, 152 + by_off)
        ctx.bezierCurveTo(ox + 64, 194 + by_off, ox + 66, 232 + by_off, ox + 58, 266 + by_off)
        ctx.stroke()
        ctx.globalAlpha = 1.0

    ctx.restore()  # end body clip

    ctx.fillStyle = OREN_PALETTE["fur_main"]
    ctx.strokeStyle = OREN_PALETTE["ink"]
    ctx.lineWidth = 2.6
    for side in (-1, 1):
        fx = ox + side * 66
        fy = 224 + by_off
        ctx.beginPath()
        ctx.moveTo(fx - side * 5, fy - 12)
        ctx.lineTo(fx + side * 8, fy - 4)
        ctx.lineTo(fx - side * 2, fy + 2)
        ctx.lineTo(fx + side * 7, fy + 10)
        ctx.lineTo(fx - side * 6, fy + 14)
        ctx.closePath()
        ctx.fill()
        ctx.stroke()

    # 3. KAKI BELAKANG & CAKAR DEPAN (100% TERBUKA)
    for side in (-1, 1):
        px = ox + side * 40 + s * 8
        py = 278 + by_off * 0.3
        ctx.fillStyle = OREN_PALETTE["belly"] if c > -0.2 else OREN_PALETTE["fur_main"]
        ctx.strokeStyle = OREN_PALETTE["ink"]
        ctx.lineWidth = 2.8
        ctx.beginPath()
        ctx.ellipse(px, py, 16.5, 11.5, side * 0.12, 0, math.pi * 2)
        ctx.fill()
        ctx.stroke()
        ctx.lineWidth = 1.8
        ctx.beginPath()
        ctx.moveTo(px - 5, py + 3)
        ctx.lineTo(px - 5, py + 10)
        ctx.moveTo(px + 5, py + 3)
        ctx.lineTo(px + 5, py + 10)
        ctx.stroke()

    if c > -0.35:
        lox, loy = float(r.left_paw_offset[0]), float(r.left_paw_offset[1])
        flx = ox - 24 + s * 28 + lox
        fly = 275 + loy
        ctx.fillStyle = OREN_PALETTE["belly"]
        ctx.strokeStyle = OREN_PALETTE["ink"]
        ctx.lineWidth = 2.8
        ctx.beginPath()
        ctx.roundRect(flx - 12, 232 + by_off, 24, max(18.0, 48 + loy), 11)
        ctx.fill()
        ctx.stroke()
        ctx.beginPath()
        ctx.ellipse(flx, fly + 6, 15.5, 10.5, 0, 0, math.pi * 2)
        ctx.fill()
        ctx.stroke()

        # Cakar depan kanan: bebas posisikan baik duduk netral maupun terangkat menepis
        if r.right_paw_raised > 0.02 or r.right_paw_target is not None or r.show_paw_pads:
            shx, shy = ox + 30 + s * 24, 212 + by_off
            if r.right_paw_target is not None:
                pawx, pawy = float(r.right_paw_target[0]), float(r.right_paw_target[1])
            else:
                lift = max(0.0, min(1.5, float(r.right_paw_raised)))
                pawx = ox + 28 + s * 26 + lift * 48.0
                pawy = 270 + by_off - lift * 108.0
            ctx.strokeStyle = OREN_PALETTE["ink"]
            ctx.lineWidth = 26.0
            ctx.lineCap = "round"
            ctx.beginPath()
            ctx.moveTo(shx, shy)
            ctx.quadraticCurveTo((shx + pawx) * 0.5 + 12, (shy + pawy) * 0.5 + 6, pawx, pawy)
            ctx.stroke()
            ctx.strokeStyle = OREN_PALETTE["fur_main"]
            ctx.lineWidth = 20.0
            ctx.beginPath()
            ctx.moveTo(shx, shy)
            ctx.quadraticCurveTo((shx + pawx) * 0.5 + 12, (shy + pawy) * 0.5 + 6, pawx, pawy)
            ctx.stroke()

            if r.show_paw_pads or r.right_paw_raised >= 0.45:
                _draw_paw_pad_closeup(
                    ctx,
                    pawx + 5,
                    pawy - 3,
                    float(r.right_paw_rot),
                    float(r.right_paw_scale),
                    float(r.claws_out),
                    rim_intensity,
                    rim_color,
                )
            else:
                ctx.fillStyle = OREN_PALETTE["belly"]
                ctx.strokeStyle = OREN_PALETTE["ink"]
                ctx.lineWidth = 2.8
                ctx.beginPath()
                ctx.ellipse(pawx, pawy, 16.0, 12.0, float(r.right_paw_rot), 0, math.pi * 2)
                ctx.fill()
                ctx.stroke()
        else:
            frx = ox + 24 + s * 28
            fry = 275
            ctx.fillStyle = OREN_PALETTE["belly"]
            ctx.strokeStyle = OREN_PALETTE["ink"]
            ctx.lineWidth = 2.8
            ctx.beginPath()
            ctx.roundRect(frx - 12, 232 + by_off, 24, 48, 11)
            ctx.fill()
            ctx.stroke()
            ctx.beginPath()
            ctx.ellipse(frx, fry + 6, 15.5, 10.5, 0, 0, math.pi * 2)
            ctx.fill()
            ctx.stroke()

    # 4. KALUNG KAIN BIRU TOSKA PUDAR (#4F9DA6) BERSERABUT + LONCENG TEMBAGA TUA PENYOK
    col_y = 160 + by_off
    col_g = ctx.createLinearGradient(ox - 54, col_y, ox + 54, col_y)
    col_g.addColorStop(0, OREN_PALETTE["collar_dark"])
    col_g.addColorStop(0.55, OREN_PALETTE["collar"])
    col_g.addColorStop(1, OREN_PALETTE["collar_dark"])
    ctx.fillStyle = col_g
    ctx.strokeStyle = OREN_PALETTE["ink"]
    ctx.lineWidth = 2.8
    ctx.beginPath()
    ctx.moveTo(ox - 52, col_y - 6)
    ctx.quadraticCurveTo(ox, col_y + 12, ox + 52, col_y - 6)
    ctx.lineTo(ox + 50, col_y + 7)
    ctx.quadraticCurveTo(ox, col_y + 24, ox - 50, col_y + 7)
    ctx.closePath()
    ctx.fill()
    ctx.stroke()

    ctx.strokeStyle = "#8AC4CB"
    ctx.lineWidth = 1.2
    for fx_off in [-36, -18, 20, 38]:
        ctx.beginPath()
        ctx.moveTo(ox + fx_off, col_y + 12)
        ctx.lineTo(ox + fx_off + (2 if fx_off > 0 else -2), col_y + 17)
        ctx.stroke()

    if c > -0.1:
        bx = ox + s * 44 + bell_sway
        by = col_y + 22
        ctx.save()
        ctx.translate(bx, by)
        ctx.rotate(bell_sway * 0.04)
        ctx.strokeStyle = OREN_PALETTE["ink"]
        ctx.lineWidth = 2.0
        ctx.beginPath()
        ctx.arc(0, -10, 3.6, 0, math.pi * 2)
        ctx.stroke()
        bell_g = ctx.createRadialGradient(-3, -4, 1.5, 0, 0, 12)
        bell_g.addColorStop(0, OREN_PALETTE["bell_hi"])
        bell_g.addColorStop(0.45, OREN_PALETTE["bell"])
        bell_g.addColorStop(1, "#6E371B")
        ctx.fillStyle = bell_g
        ctx.strokeStyle = OREN_PALETTE["ink"]
        ctx.lineWidth = 2.4
        ctx.beginPath()
        ctx.moveTo(0, -10)
        ctx.bezierCurveTo(10.5, -10, 12.0, -1, 8.8, 4.5)
        ctx.quadraticCurveTo(5.2, 3.0, 5.5, 7.8)
        ctx.bezierCurveTo(1.5, 11.2, -10.5, 10.5, -10.8, 0)
        ctx.bezierCurveTo(-10.8, -6.8, -6.2, -10, 0, -10)
        ctx.closePath()
        ctx.fill()
        ctx.stroke()
        ctx.fillStyle = OREN_PALETTE["ink"]
        ctx.beginPath()
        ctx.arc(-1, 4.5, 2.2, 0, math.pi * 2)
        ctx.fill()
        ctx.strokeStyle = OREN_PALETTE["ink"]
        ctx.lineWidth = 1.7
        ctx.beginPath()
        ctx.moveTo(-8, 1.5)
        ctx.quadraticCurveTo(-1, 5.0, 6.5, 2.0)
        ctx.stroke()
        ctx.restore()

    # 5. KEPALA KUCING CHUNKY + TELINGA KANAN SOBEK V
    hx = ox + float(r.head_offset_x)
    hy = 108 + by_off * 1.15 + float(r.head_offset_y)
    ctx.save()
    ctx.translate(hx, hy)
    ctx.rotate(float(r.head_tilt))

    for side in (-1, 1):
        ex = side * 38 + s * 10
        ey = -42
        twitch = float(r.ear_right_twitch) if side == -1 else float(r.ear_left_twitch)
        ctx.save()
        ctx.translate(ex, ey)
        ctx.rotate(side * 0.24 + twitch)
        ctx.fillStyle = OREN_PALETTE["fur_main"]
        ctx.strokeStyle = OREN_PALETTE["ink"]
        ctx.lineWidth = 3.2
        ctx.lineJoin = "round"
        if side == -1:
            ctx.beginPath()
            ctx.moveTo(-18, 22)
            ctx.lineTo(-10, -22)
            ctx.lineTo(1, -9)
            ctx.lineTo(5, -1)
            ctx.lineTo(9, -11)
            ctx.lineTo(18, 18)
            ctx.closePath()
            ctx.fill()
            ctx.stroke()
        else:
            ctx.beginPath()
            ctx.moveTo(-18, 18)
            ctx.lineTo(2, -24)
            ctx.lineTo(18, 22)
            ctx.closePath()
            ctx.fill()
            ctx.stroke()
        if c > -0.2:
            ctx.fillStyle = "#E6A3A3"
            ctx.beginPath()
            ctx.moveTo(-9, 13)
            ctx.lineTo(0, -10)
            ctx.lineTo(9, 13)
            ctx.closePath()
            ctx.fill()
        ctx.restore()

    ctx.fillStyle = OREN_PALETTE["ink"]
    ctx.beginPath()
    ctx.moveTo(0, -54)
    ctx.bezierCurveTo(38, -54, 62, -32, 62, 2)
    ctx.lineTo(72, 12)
    ctx.lineTo(60, 22)
    ctx.lineTo(67, 31)
    ctx.bezierCurveTo(56, 52, 28, 59, 0, 59)
    ctx.bezierCurveTo(-30, 59, -59, 52, -70, 31)
    ctx.lineTo(-63, 22)
    ctx.lineTo(-75, 12)
    ctx.lineTo(-65, 2)
    ctx.bezierCurveTo(-65, -32, -40, -54, 0, -54)
    ctx.closePath()
    ctx.fill()

    ctx.save()
    ctx.beginPath()
    ctx.moveTo(0, -50)
    ctx.bezierCurveTo(35, -50, 58, -29, 58, 2)
    ctx.lineTo(67, 11)
    ctx.lineTo(56, 20)
    ctx.lineTo(62, 29)
    ctx.bezierCurveTo(52, 48, 26, 54, 0, 54)
    ctx.bezierCurveTo(-26, 54, -52, 48, -62, 29)
    ctx.lineTo(-56, 20)
    ctx.lineTo(-67, 11)
    ctx.lineTo(-58, 2)
    ctx.bezierCurveTo(-58, -29, -35, -50, 0, -50)
    ctx.closePath()
    ctx.clip()

    head_g = ctx.createRadialGradient(18, -16, 8, 4, 2, 72)
    head_g.addColorStop(0, OREN_PALETTE["fur_light"])
    head_g.addColorStop(0.58, OREN_PALETTE["fur_main"])
    head_g.addColorStop(1, OREN_PALETTE["fur_dark"])
    ctx.fillStyle = head_g
    ctx.fillRect(-75, -60, 150, 120)

    if c > -0.3:
        fx = s * 36
        ctx.fillStyle = OREN_PALETTE["stripe"]
        ctx.save()
        ctx.translate(fx, -32)
        ctx.scale(max(0.15, c), 1)
        for sx_b, w_b, h_b in [(-16, 7, 22), (0, 8, 26), (16, 7, 22)]:
            ctx.beginPath()
            ctx.ellipse(sx_b, -6, w_b * 0.55, h_b * 0.55, sx_b * 0.012, 0, math.pi * 2)
            ctx.fill()
        ctx.restore()
    else:
        ctx.fillStyle = OREN_PALETTE["stripe"]
        for by_s in [-24, -4, 16]:
            ctx.beginPath()
            ctx.ellipse(0, by_s, 36, 5.5, 0, 0, math.pi * 2)
            ctx.fill()

    ctx.fillStyle = "rgba(56, 20, 22, 0.25)"
    ctx.beginPath()
    ctx.ellipse(-28, 38, 42, 24, 0.2, 0, math.pi * 2)
    ctx.fill()

    if rim_intensity > 0.05:
        ctx.strokeStyle = rim_color
        ctx.globalAlpha = 0.85 * rim_intensity
        ctx.lineWidth = 4.0
        ctx.lineCap = "round"
        ctx.beginPath()
        ctx.moveTo(22, -45)
        ctx.bezierCurveTo(46, -34, 56, -12, 56, 6)
        ctx.stroke()
        ctx.globalAlpha = 1.0

    # WAJAH OREN (depan/3-4 atau side-profile mulus di 90°)
    lid_frac = max(0.0, min(1.0, float(r.eyelid_level)))
    eye_open = max(0.08, 1.0 - max(0.0, min(1.0, float(r.blink))) * 0.92)

    if c > 0.16:
        face_x = s * 38
        sc_f = max(0.28, c)
        ctx.save()
        ctx.globalAlpha = min(1.0, (c - 0.16) * 4.5)
        ctx.translate(face_x, 0)
        ctx.scale(sc_f, 1.0)

        ctx.fillStyle = OREN_PALETTE["belly"]
        ctx.strokeStyle = OREN_PALETTE["ink"]
        ctx.lineWidth = 2.0
        ctx.beginPath()
        ctx.ellipse(-10.5, 22, 13.5, 10.2, -0.08, 0, math.pi * 2)
        ctx.ellipse(10.5, 22, 13.5, 10.2, 0.08, 0, math.pi * 2)
        ctx.fill()
        ctx.stroke()
        ctx.fillStyle = OREN_PALETTE["belly"]
        ctx.fillRect(-10, 14, 20, 14)

        # Ekspresi mulut terbuka (bebas ganti per adegan!)
        ctx.strokeStyle = OREN_PALETTE["ink"]
        ctx.lineWidth = 2.4
        ctx.lineCap = "round"
        if r.mouth_style == "open_meow":
            ctx.fillStyle = "#5C222A"
            ctx.beginPath()
            ctx.ellipse(0, 26, 7.5, 6.2, 0, 0, math.pi * 2)
            ctx.fill()
            ctx.stroke()
            ctx.fillStyle = "#E47A82"
            ctx.beginPath()
            ctx.ellipse(0, 29, 4.5, 2.4, 0, 0, math.pi * 2)
            ctx.fill()
        elif r.mouth_style == "hiss":
            ctx.fillStyle = "#5C222A"
            ctx.beginPath()
            ctx.ellipse(0, 27, 10.5, 7.2, 0, 0, math.pi * 2)
            ctx.fill()
            ctx.stroke()
            ctx.fillStyle = "#FFFDF8"
            for fx_t in (-6.5, 6.5):
                ctx.beginPath()
                ctx.moveTo(fx_t - 2, 21)
                ctx.lineTo(fx_t, 27)
                ctx.lineTo(fx_t + 2, 21)
                ctx.closePath()
                ctx.fill()
        elif r.mouth_style == "neutral":
            ctx.beginPath()
            ctx.moveTo(0, 17)
            ctx.lineTo(0, 23)
            ctx.moveTo(-10, 25)
            ctx.quadraticCurveTo(-5, 28, 0, 23)
            ctx.quadraticCurveTo(5, 28, 10, 25)
            ctx.stroke()
        else:  # smug
            ctx.beginPath()
            ctx.moveTo(0, 17)
            ctx.lineTo(0, 22)
            ctx.moveTo(-12, 24)
            ctx.quadraticCurveTo(-5, 29, 0, 22)
            ctx.quadraticCurveTo(6, 29, 14, 21)
            ctx.stroke()

        # Hidung merah muda kering berbintik halus
        ctx.fillStyle = OREN_PALETTE["nose_pink"]
        ctx.strokeStyle = OREN_PALETTE["ink"]
        ctx.lineWidth = 1.9
        ctx.beginPath()
        ctx.moveTo(-7.2, 11.5)
        ctx.quadraticCurveTo(0, 9.2, 7.2, 11.5)
        ctx.quadraticCurveTo(4.0, 18.2, 0, 18.8)
        ctx.quadraticCurveTo(-4.0, 18.2, -7.2, 11.5)
        ctx.closePath()
        ctx.fill()
        ctx.stroke()
        ctx.fillStyle = "rgba(110, 44, 48, 0.45)"
        for nx, ny in [(-2.5, 13.0), (1.8, 12.6), (0.2, 15.2)]:
            ctx.beginPath()
            ctx.arc(nx, ny, 0.7, 0, math.pi * 2)
            ctx.fill()

        # Mata hijau zaitun dengan kelopak bebas diatur (eyelid_level 0..1)
        for ex, is_left in [(-20.0, True), (20.0, False)]:
            ctx.save()
            ctx.translate(ex, 0.0)
            ctx.scale(1.0, eye_open)
            eg = ctx.createRadialGradient(2, -2, 1.5, 0, 0, 13)
            eg.addColorStop(0, OREN_PALETTE["eye_olive_hi"])
            eg.addColorStop(0.55, OREN_PALETTE["eye_olive"])
            eg.addColorStop(1, "#445818")
            ctx.fillStyle = eg
            ctx.strokeStyle = OREN_PALETTE["ink"]
            ctx.lineWidth = 2.8
            ctx.beginPath()
            ctx.ellipse(0, 0, 13.0, 10.5, 0, 0, math.pi * 2)
            ctx.fill()
            ctx.stroke()

            px_p = float(r.gaze_x) * 4.5
            py_p = 1.8 + float(r.gaze_y) * 2.5
            ctx.fillStyle = "#161118"
            ctx.beginPath()
            ctx.ellipse(px_p, py_p, 2.8, 6.8, 0, 0, math.pi * 2)
            ctx.fill()
            ctx.fillStyle = "#FFFFFF"
            ctx.beginPath()
            ctx.arc(px_p + 2.2, py_p - 2.2, 1.8, 0, math.pi * 2)
            ctx.fill()

            lid_h = 3.0 + lid_frac * 18.0
            lid_y = -13.0 + lid_h
            if lid_frac > 0.04:
                ctx.fillStyle = OREN_PALETTE["fur_main"]
                ctx.fillRect(-15, -13, 30, lid_h)
                ctx.strokeStyle = OREN_PALETTE["ink"]
                ctx.lineWidth = 3.4
                ctx.lineCap = "round"
                lid_tilt = 2.2 if is_left else -2.2
                ctx.beginPath()
                ctx.moveTo(-14, lid_y - lid_tilt * 0.45)
                ctx.lineTo(14, lid_y + lid_tilt * 0.45)
                ctx.stroke()
            ctx.restore()

        ctx.restore()
    elif abs(c) <= 0.28 and abs(s) > 0.7:
        dir_x = 1.0 if s >= 0 else -1.0
        ctx.save()
        ctx.globalAlpha = min(1.0, (0.28 - abs(c)) * 6.0) if abs(c) > 0.12 else 1.0
        ex_p = dir_x * 34.0
        ctx.fillStyle = OREN_PALETTE["eye_olive"]
        ctx.strokeStyle = OREN_PALETTE["ink"]
        ctx.lineWidth = 2.6
        ctx.beginPath()
        ctx.ellipse(ex_p, 1.0, 9.5, 9.0, 0, 0, math.pi * 2)
        ctx.fill()
        ctx.stroke()
        ctx.fillStyle = "#161118"
        ctx.beginPath()
        ctx.ellipse(ex_p + dir_x * 3.5, 2.0, 2.2, 5.8, 0, 0, math.pi * 2)
        ctx.fill()
        ctx.fillStyle = "#FFFFFF"
        ctx.beginPath()
        ctx.arc(ex_p + dir_x * 4.5, 0.0, 1.5, 0, math.pi * 2)
        ctx.fill()
        lid_h = 3.0 + lid_frac * 15.5
        if lid_frac > 0.04:
            ctx.fillStyle = OREN_PALETTE["fur_main"]
            ctx.fillRect(ex_p - 12, -11, 24, lid_h)
            ctx.strokeStyle = OREN_PALETTE["ink"]
            ctx.lineWidth = 3.2
            ctx.beginPath()
            ctx.moveTo(ex_p - 11, -11 + lid_h)
            ctx.lineTo(ex_p + 11, -13 + lid_h)
            ctx.stroke()
        ctx.fillStyle = OREN_PALETTE["belly"]
        ctx.strokeStyle = OREN_PALETTE["ink"]
        ctx.lineWidth = 2.0
        ctx.beginPath()
        ctx.ellipse(dir_x * 48, 20, 13, 10, 0, 0, math.pi * 2)
        ctx.fill()
        ctx.stroke()
        ctx.fillStyle = OREN_PALETTE["nose_pink"]
        ctx.beginPath()
        ctx.arc(dir_x * 55, 14, 4.8, 0, math.pi * 2)
        ctx.fill()
        ctx.stroke()
        ctx.restore()

    ctx.restore()  # end head clip

    # Kumis kaku asimetris (droop bebas diatur lewat rig.whisker_droop)
    if c > -0.25:
        wx = s * 38
        wd = float(r.whisker_droop)
        ctx.save()
        ctx.globalAlpha = min(1.0, (c + 0.25) * 3.0)
        ctx.strokeStyle = OREN_PALETTE["ink"]
        ctx.lineCap = "round"
        ctx.lineWidth = 2.1
        ctx.beginPath()
        ctx.moveTo(wx - 22, 18)
        ctx.lineTo(wx - 72, 12 + wd)
        ctx.moveTo(wx - 24, 24)
        ctx.lineTo(wx - 76, 26 + wd)
        ctx.moveTo(wx - 21, 29)
        ctx.lineTo(wx - 62, 39 + wd)
        ctx.moveTo(wx + 22, 18)
        ctx.lineTo(wx + 68, 8 + wd)
        ctx.moveTo(wx + 23, 25)
        ctx.lineTo(wx + 48, 29 + wd * 0.6)
        ctx.lineTo(wx + 66, 22 + wd)
        ctx.stroke()
        ctx.restore()

    ctx.restore()  # end head translate

    if c < -0.05:
        draw_tail()

    ctx.restore()  # end body lean
    ctx.restore()  # end scale


class OrenCharacter:
    """
    Komponen Desain Karakter 2.5D 'Oren' dengan rigging 100% terbuka (`OrenRig`).
    Default merender pose desain netral tanpa animasi terkunci.
    """

    def __init__(self, scale: float = 3.0) -> None:
        self.scale = float(scale)

    def render_svg(
        self,
        angle: Optional[float] = None,
        rig: Optional[OrenRig] = None,
        **rig_overrides: Any,
    ) -> str:
        active_rig = OrenRig(**vars(rig)) if rig is not None else OrenRig()
        if angle is not None:
            active_rig.angle = float(angle)
        for k, v in rig_overrides.items():
            if hasattr(active_rig, k):
                setattr(active_rig, k, v)
        w = int(round(280 * self.scale))
        h = int(round(320 * self.scale))
        ctx = _eng.SvgCanvas2D(w, h)
        render_oren_canvas(ctx, rig=active_rig, scale=self.scale)
        return ctx.to_svg()

    def render_pil(
        self,
        angle: Optional[float] = None,
        rig: Optional[OrenRig] = None,
        **rig_overrides: Any,
    ) -> Any:
        import io
        import resvg_py
        from PIL import Image

        svg_str = self.render_svg(angle=angle, rig=rig, **rig_overrides)
        png_bytes = resvg_py.svg_to_bytes(svg_string=svg_str, skip_system_fonts=True)
        return Image.open(io.BytesIO(png_bytes)).convert("RGBA")
