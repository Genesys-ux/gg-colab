"""
BimaHeroCharacter — Protagonis "Jangan Sampai Kunci Ini Jatuh!" (Magang Tukang Jam, 13 tahun)

Dibangun 100% di atas modul ekspor C:\\Users\\lutfi\\Downloads\\122\\generator.html
(`bima_character.py`), lalu diperkaya secara non-destruktif dengan:
  1. Detail Character Bible:
     - Celana kargo biru dongker (#2B3A55) digulung di mata kaki + sepatu bot kulit cokelat tua
       bersol lumpur kering & tali sepatu oranye menyala (#FF6B1A) (+15% chunky extremities)
     - Lengan jaket parka kuning kunyit (#F2B705) bernoda debu siku + telapak tangan chunky (+15%)
     - Rambut cokelat tua sculpted chunky clumps + 1 jambul ikonik berfisika pegas di dahi
     - Kacamata loupe kuningan (#B8860B) diangkat rapi di dahi (bebas tabrakan alis) + kilau lensa fase-reaktif
     - Bintik freckles tipis di pangkal hidung + corengan oli mesin hitam di pipi kiri (360° cylindrical!)
     - Saku kanan bawah jaket robek kecil + 2 helai benang menjuntai (setup [CAM 27] + opsional Kunci Perak mengintip)
     - Syal merah bata (#C84B31, 40cm) menjuntai dinamis terlihat jelas dari depan, 3/4, samping & belakang
     - Kantong sabuk kulit berisi obeng gagang biru, pinset kuningan, dan lap kotak-kotak
  2. Tabel Respons Warna 3 Fase Pencahayaan (sesuai PDF Production Bible):
     - phase1          : Low Sun & Blue Shade (00:00–00:26)
     - phase2          : Indigo & Emerald Turn + Furnace Rim (00:27–00:38)
     - phase3_crimson  : Ultra-Low Crimson Sun + Electric Blue Shade (00:39–00:52)
     - phase3_twilight : Frozen Violet-Gold Twilight + Crisp Cyan Rim (00:53–00:58)
"""

from __future__ import annotations

import copy
import math
from typing import Any, Dict, Literal, Optional, Tuple

from . import bima_character as _base
from .rig_controls import HumanoidRig, apply_humanoid_rig_to_pose, rig_to_render_kwargs

LightingPhase = Literal["phase1", "phase2", "phase3_crimson", "phase3_twilight"]

LIGHTING_PHASE_PROFILES: Dict[str, Dict[str, Any]] = {
    "phase1": {
        "label": "Fase 1: Low Sun & Blue Shade (00:00-00:26)",
        "robeColor": "#F2B705",
        "capeColor": "#C84B31",
        "limbColor": "#2B3A55",
        "trimColor": "#B8860B",
        "skinColor": "#F5D6BA",
        "blushColor": "#DFA88E",
        "hairColor": "#4A2C1D",
        "sashColor": "#5B3822",
        "bootColor": "#54311E",
        "laceColor": "#FF6E1A",
        "rimColor": "#FFE09A",
        "rimGlow": "rgba(255, 206, 112, 0.62)",
        "shadeTint": "rgba(38, 66, 116, 0.28)",
        "jacketShadowTint": "rgba(86, 102, 42, 0.34)",  # hijau zaitun hangat di blue shade
        "lensTop": "#FFF4C4",
        "lensMid": "#4CC9F0",
        "lensDeep": "#184C72",
        "rimIntensity": 1.18,
        "shadowDepth": 1.05,
    },
    "phase2": {
        "label": "Fase 2: Indigo & Emerald Turn (00:27-00:38)",
        "robeColor": "#B88412",  # mustard gelap
        "capeColor": "#7B261E",  # merah bata gelap pekat
        "limbColor": "#1A2240",  # hampir menyatu bayangan nila
        "trimColor": "#9C7A1E",
        "skinColor": "#C9B0A4",
        "blushColor": "#8C6F7E",
        "hairColor": "#2C1D24",
        "sashColor": "#3A2524",
        "bootColor": "#321E1B",
        "laceColor": "#FF5B1F",
        "rimColor": "#FF6324",  # hard furnace-orange rim light
        "rimGlow": "rgba(255, 92, 30, 0.72)",
        "scarfRimColor": "#3BF2AE",  # sorotan tepi zamrud pada syal
        "shadeTint": "rgba(20, 22, 74, 0.44)",  # deep indigo shade
        "jacketShadowTint": "rgba(22, 26, 78, 0.45)",
        "lensTop": "#C8FFE9",
        "lensMid": "#28DE98",  # pantulan uap hijau zamrud
        "lensDeep": "#0C4E42",
        "rimIntensity": 1.35,
        "shadowDepth": 1.25,
    },
    "phase3_crimson": {
        "label": "Fase 3A: Ultra-Low Crimson Sun (00:39-00:52)",
        "robeColor": "#FF9E18",  # menyala jingga-emas
        "capeColor": "#C93B2B",  # menyatu langit crimson
        "limbColor": "#1E2845",  # jangkar gelap di atas atap trem merah
        "trimColor": "#D6931A",
        "skinColor": "#F2C4A0",
        "blushColor": "#C97D6E",
        "hairColor": "#3C211C",
        "sashColor": "#4D2B1D",
        "bootColor": "#422318",
        "laceColor": "#FF7A1F",
        "rimColor": "#FFB85C",
        "rimGlow": "rgba(255, 86, 46, 0.74)",
        "shadeTint": "rgba(42, 24, 96, 0.36)",  # bayangan ungu-biru elektrik
        "jacketShadowTint": "rgba(62, 26, 98, 0.38)",
        "lensTop": "#FFE9B0",
        "lensMid": "#FF7648",
        "lensDeep": "#4C1D4E",
        "rimIntensity": 1.35,
        "shadowDepth": 1.22,
    },
    "phase3_twilight": {
        "label": "Fase 3B: Frozen Violet-Gold Twilight (00:53-00:58)",
        "robeColor": "#E39F1E",  # jingga-emas kontras bayangan ungu pekat
        "capeColor": "#A43A3B",
        "limbColor": "#1E2544",
        "trimColor": "#C49524",
        "skinColor": "#DFC2B8",
        "blushColor": "#A47B92",
        "hairColor": "#33202B",
        "sashColor": "#462A29",
        "bootColor": "#3C2320",
        "laceColor": "#FF7B2B",
        "rimColor": "#6BF7FF",  # crisp cyan rim light super tajam
        "rimGlow": "rgba(86, 240, 255, 0.78)",
        "shadeTint": "rgba(48, 24, 92, 0.38)",  # bayangan ungu pekat
        "jacketShadowTint": "rgba(56, 24, 96, 0.40)",
        "lensTop": "#F0FFFF",
        "lensMid": "#5CF2FF",  # pantulan crisp cyan senja beku
        "lensDeep": "#1D3B6E",
        "rimIntensity": 1.42,
        "shadowDepth": 1.18,
    },
}


def _draw_bima_leg(
    ctx: Any,
    hip: Any,
    knee: Any,
    ankle: Any,
    toe: Any,
    rimI: float,
    limbColor: Optional[str],
    phase: Dict[str, Any],
) -> None:
    """Celana kargo biru dongker (#2B3A55) digulung di mata kaki + sepatu bot kerja cokelat tua bertali oranye."""
    pant_col = limbColor or phase["limbColor"]
    boot_col = phase["bootColor"]
    lace_col = phase["laceColor"]

    # Titik gulungan celana (80% dari lutut ke pergelangan kaki)
    cuff_x = knee.x + (ankle.x - knee.x) * 0.76
    cuff_y = knee.y + (ankle.y - knee.y) * 0.76
    cuff_pt = _base._AttrDict({"x": cuff_x, "y": cuff_y, "z": ankle.z})

    ctx.save()
    ctx.lineCap = "round"
    ctx.lineJoin = "round"

    # 1. Celana kargo biru dongker bervolume (outline tebal + fill celana + shadow + rim)
    ctx.strokeStyle = "#1B131E"
    ctx.lineWidth = 15.0
    _base.traceTwoBonePath(ctx, hip, knee, cuff_pt, 0.28)
    ctx.stroke()

    ctx.strokeStyle = pant_col
    ctx.lineWidth = 10.6
    _base.traceTwoBonePath(ctx, hip, knee, cuff_pt, 0.28)
    ctx.stroke()

    # Highlight lembut sisi terang celana
    ctx.strokeStyle = _base.tintHex(pant_col, 0.22)
    ctx.lineWidth = 3.2
    _base.traceTwoBonePath(
        ctx,
        _base._AttrDict({"x": hip.x + 2.2, "y": hip.y + 2, "z": 0}),
        _base._AttrDict({"x": knee.x + 2.2, "y": knee.y, "z": 0}),
        _base._AttrDict({"x": cuff_x + 2.0, "y": cuff_y - 1, "z": 0}),
        0.28,
    )
    ctx.stroke()

    # Saku kargo kecil samping paha
    mid_th_x = (hip.x + knee.x) * 0.52
    mid_th_y = (hip.y + knee.y) * 0.52
    ctx.fillStyle = _base.shadeHex(pant_col, 0.80)
    ctx.strokeStyle = "#1B131E"
    ctx.lineWidth = 1.6
    ctx.beginPath()
    ctx.roundRect(mid_th_x - 4.8, mid_th_y - 6.0, 9.6, 12.0, 2.5)
    ctx.fill()
    ctx.stroke()

    # Gulungan lipatan ujung celana (rolled denim cuff) di mata kaki
    ang_shin = math.atan2(ankle.y - knee.y, ankle.x - knee.x)
    ctx.save()
    ctx.translate(cuff_x, cuff_y)
    ctx.rotate(ang_shin - math.pi * 0.5)
    ctx.fillStyle = _base.tintHex(pant_col, 0.26)
    ctx.strokeStyle = "#1B131E"
    ctx.lineWidth = 2.0
    ctx.beginPath()
    ctx.roundRect(-7.2, -3.5, 14.4, 7.2, 3.0)
    ctx.fill()
    ctx.stroke()
    ctx.restore()

    # 2. Sepatu bot kerja kulit cokelat tua (+15% chunky!) dengan sol karet lumpur & tali oranye
    dx_f = toe.x - ankle.x
    dy_f = toe.y - ankle.y
    foot_dir = -1.0 if dx_f < -1.5 else (1.0 if dx_f > 1.5 else -1.0)
    boot_ang = math.atan2(dy_f, abs(dx_f) + 12.0) * (0.35 if foot_dir > 0 else -0.35)

    ctx.save()
    ctx.translate(ankle.x, ankle.y)
    ctx.rotate(boot_ang)
    if foot_dir < 0:
        ctx.scale(-1, 1)

    # Leher bot (collar) di atas pergelangan
    boot_g = ctx.createLinearGradient(-10, -14, 24, 14)
    boot_g.addColorStop(0, _base.shadeHex(boot_col, 0.62))
    boot_g.addColorStop(0.5, _base.tintHex(boot_col, 0.16))
    boot_g.addColorStop(1, _base.shadeHex(boot_col, 0.52))

    # Badan sepatu bot kulit chunky
    ctx.fillStyle = boot_g
    ctx.strokeStyle = "#1B131E"
    ctx.lineWidth = 2.6
    ctx.beginPath()
    ctx.moveTo(-7.5, -12.0)
    ctx.lineTo(6.5, -12.0)
    ctx.lineTo(8.5, -2.5)
    ctx.quadraticCurveTo(18.5, -2.0, 22.0, 4.0)
    ctx.quadraticCurveTo(23.5, 9.5, 18.0, 10.5)
    ctx.lineTo(-9.0, 10.5)
    ctx.quadraticCurveTo(-11.0, 4.0, -7.5, -12.0)
    ctx.closePath()
    ctx.fill()
    ctx.stroke()

    # Sol karet tebal + noda lumpur kering
    ctx.fillStyle = "#261B18"
    ctx.strokeStyle = "#150F14"
    ctx.lineWidth = 2.1
    ctx.beginPath()
    ctx.roundRect(-10.0, 8.2, 31.5, 5.8, [2.0, 2.5, 3.0, 3.0])
    ctx.fill()
    ctx.stroke()

    # Tekstur lumpur kering di sol bawah
    ctx.fillStyle = "#8C7050"
    for mx, mr in [(-5.5, 1.8), (1.0, 2.2), (9.5, 1.9), (16.2, 1.6)]:
        ctx.beginPath()
        ctx.ellipse(mx, 11.4, mr, 1.2, 0.1, 0, math.pi * 2)
        ctx.fill()

    # Kilau kulit pada ujung toe cap
    ctx.fillStyle = "rgba(255, 232, 200, 0.35)"
    ctx.beginPath()
    ctx.ellipse(14.5, 3.2, 4.2, 2.0, 0.25, 0, math.pi * 2)
    ctx.fill()

    # Tali sepatu oranye menyala (#FF6E1A) menyilang rapi
    ctx.strokeStyle = "#1B131E"
    ctx.lineWidth = 3.2
    ctx.beginPath()
    ctx.moveTo(2.5, -8.2)
    ctx.lineTo(8.5, -6.4)
    ctx.moveTo(3.5, -4.4)
    ctx.lineTo(9.8, -2.6)
    ctx.moveTo(5.0, -0.8)
    ctx.lineTo(11.0, 0.8)
    ctx.stroke()

    ctx.strokeStyle = lace_col
    ctx.lineWidth = 1.8
    ctx.beginPath()
    ctx.moveTo(2.5, -8.2)
    ctx.lineTo(8.5, -6.4)
    ctx.moveTo(3.5, -4.4)
    ctx.lineTo(9.8, -2.6)
    ctx.moveTo(5.0, -0.8)
    ctx.lineTo(11.0, 0.8)
    ctx.stroke()

    # Rim light fase pencahayaan pada tepi sepatu
    if rimI > 0.05:
        ctx.strokeStyle = phase["rimColor"]
        ctx.globalAlpha = min(0.85, 0.45 * rimI)
        ctx.lineWidth = 1.8
        ctx.beginPath()
        ctx.moveTo(7.5, -10.0)
        ctx.quadraticCurveTo(17.5, -2.5, 21.0, 5.0)
        ctx.stroke()
    ctx.restore()
    ctx.restore()


def _draw_bima_arm(
    ctx: Any,
    sh: Any,
    elb: Any,
    hnd: Any,
    rimI: float,
    cfg: Any,
    phase: Dict[str, Any],
) -> None:
    """Lengan jaket parka kuning kunyit bervolume + noda debu siku + tangan chunky (+15%)."""
    sleeve_col = cfg.robeColor or phase["robeColor"]
    skin_col = cfg.skinColor or phase["skinColor"]

    # Pergelangan tangan (86% dari siku ke tangan)
    wr_x = elb.x + (hnd.x - elb.x) * 0.82
    wr_y = elb.y + (hnd.y - elb.y) * 0.82
    wr_pt = _base._AttrDict({"x": wr_x, "y": wr_y, "z": hnd.z})

    ctx.save()
    ctx.lineCap = "round"
    ctx.lineJoin = "round"

    # Outline luar lengan parka
    ctx.strokeStyle = "#1D141F"
    ctx.lineWidth = 15.6
    _base.traceTwoBonePath(ctx, sh, elb, wr_pt, 0.32)
    ctx.stroke()

    # Badan lengan jaket kuning kunyit
    ctx.strokeStyle = sleeve_col
    ctx.lineWidth = 11.2
    _base.traceTwoBonePath(ctx, sh, elb, wr_pt, 0.32)
    ctx.stroke()

    # Sisi shadow cel-shade bawah lengan
    ctx.strokeStyle = phase["jacketShadowTint"]
    ctx.lineWidth = 4.6
    _base.traceTwoBonePath(
        ctx,
        _base._AttrDict({"x": sh.x - 1.8, "y": sh.y + 2.2, "z": 0}),
        _base._AttrDict({"x": elb.x - 1.8, "y": elb.y + 2.4, "z": 0}),
        _base._AttrDict({"x": wr_x - 1.4, "y": wr_y + 2.0, "z": 0}),
        0.32,
    )
    ctx.stroke()

    # Noda debu halus di siku (sesuai brief!)
    ctx.fillStyle = "rgba(128, 102, 74, 0.42)"
    ctx.beginPath()
    ctx.ellipse(elb.x, elb.y + 1.5, 4.6, 3.2, 0.3, 0, math.pi * 2)
    ctx.fill()

    # Rim light tepi atas lengan
    if rimI > 0.05:
        ctx.strokeStyle = phase["rimColor"]
        ctx.globalAlpha = min(0.9, 0.55 * rimI)
        ctx.lineWidth = 2.0
        _base.traceTwoBonePath(
            ctx,
            _base._AttrDict({"x": sh.x + 2.4, "y": sh.y - 2.0, "z": 0}),
            _base._AttrDict({"x": elb.x + 2.4, "y": elb.y - 2.0, "z": 0}),
            _base._AttrDict({"x": wr_x + 1.8, "y": wr_y - 1.6, "z": 0}),
            0.32,
        )
        ctx.stroke()
        ctx.globalAlpha = 1.0

    # Manset pergelangan jaket (parka cuff)
    arm_ang = math.atan2(hnd.y - elb.y, hnd.x - elb.x)
    ctx.save()
    ctx.translate(wr_x, wr_y)
    ctx.rotate(arm_ang)
    ctx.fillStyle = _base.shadeHex(sleeve_col, 0.84)
    ctx.strokeStyle = "#1D141F"
    ctx.lineWidth = 2.0
    ctx.beginPath()
    ctx.roundRect(-4.5, -6.8, 7.5, 13.6, 2.8)
    ctx.fill()
    ctx.stroke()
    # Kancing kuningan manset
    ctx.fillStyle = phase["trimColor"]
    ctx.beginPath()
    ctx.arc(-0.8, 2.2, 1.6, 0, math.pi * 2)
    ctx.fill()
    ctx.restore()

    # Telapak tangan chunky (+15% lebih besar, warna kulit hangat + siluet ibu jari)
    ctx.save()
    ctx.translate(hnd.x, hnd.y)
    ctx.rotate(arm_ang)
    hand_g = ctx.createRadialGradient(2.2, -2.0, 1.0, 0, 0, 10.5)
    hand_g.addColorStop(0, _base.tintHex(skin_col, 0.24))
    hand_g.addColorStop(0.65, skin_col)
    hand_g.addColorStop(1, _base.shadeHex(skin_col, 0.78))
    ctx.fillStyle = hand_g
    ctx.strokeStyle = "#1D141F"
    ctx.lineWidth = 2.4
    # Ibu jari mungil ekspresif
    ctx.beginPath()
    ctx.ellipse(1.5, -6.2, 3.8, 2.7, -0.45, 0, math.pi * 2)
    ctx.fill()
    ctx.stroke()
    # Telapak tangan bulat chunky
    ctx.beginPath()
    ctx.ellipse(2.2, 0.5, 8.6, 7.2, 0, 0, math.pi * 2)
    ctx.fill()
    ctx.stroke()
    # Garis jemari halus
    ctx.strokeStyle = "rgba(85, 48, 36, 0.35)"
    ctx.lineWidth = 1.2
    ctx.beginPath()
    ctx.moveTo(5.2, -2.0)
    ctx.lineTo(9.0, -1.6)
    ctx.moveTo(5.5, 1.2)
    ctx.lineTo(9.4, 1.5)
    ctx.stroke()
    ctx.restore()
    ctx.restore()


def _draw_bima_outfit_details(
    ctx: Any,
    cfg: Any,
    s: float,
    c: float,
    shD: float,
    pose: Any,
    phase: Dict[str, Any],
    silver_key_peek: bool = False,
) -> None:
    """Tekstur kanvas katun + bayangan fase + saku kanan bawah robek dgn 2 benang menjuntai ([CAM 27] setup)."""
    # Tekstur kanvas katun halus di seluruh badan jaket (di dalam clip torso)
    _base.drawTextureOverlay(ctx, "weave", 52, 198, 120, 128, "rgba(76, 52, 18, 0.16)", 1.0)

    # Bayangan fase pencahayaan pada sisi teduh jaket
    ctx.fillStyle = phase["jacketShadowTint"]
    ctx.beginPath()
    ctx.moveTo(50, 196)
    ctx.lineTo(92, 196)
    ctx.quadraticCurveTo(84, 260, 96, 326)
    ctx.lineTo(50, 326)
    ctx.closePath()
    ctx.fill()

    # Saku kanan bawah robek (sisi anatomi kanan Bima = kiri penonton di [72, 288])
    if c > -0.05:
        ctx.save()
        ctx.globalAlpha = min(1.0, (c + 0.05) * 4.0)
        ctx.translate(104 + 48 * s, 0)
        ctx.scale(max(0.05, c), 1)
        ctx.translate(-104, 0)

        # Jahitan kontras kasar sepanjang plaket tengah jaket
        ctx.strokeStyle = "rgba(92, 54, 16, 0.55)"
        ctx.lineWidth = 1.3
        ctx.setLineDash([3.0, 2.6])
        ctx.beginPath()
        ctx.moveTo(100.5, 224)
        ctx.lineTo(100.5, 322)
        ctx.moveTo(107.5, 224)
        ctx.lineTo(107.5, 322)
        ctx.stroke()
        ctx.setLineDash([])

        # Robekan kecil pada sudut bawah saku kanan bawah (x=72..94, y=288..310)
        px, py = 72.0, 288.0
        sway = (
            float(pose.threadSway)
            if (pose is not None and getattr(pose, "threadSway", None) is not None)
            else (pose.capeSway if pose else 0.0) * 0.18
        )

        # Celah gelap bekas jahitan robek di sudut bawah saku
        ctx.fillStyle = "#2A1B16"
        ctx.strokeStyle = "#1E141C"
        ctx.lineWidth = 1.6
        ctx.beginPath()
        ctx.moveTo(px + 13.5, py + 21.5)
        ctx.lineTo(px + 17.5, py + 16.5)
        ctx.lineTo(px + 22.0, py + 19.5)
        ctx.lineTo(px + 21.8, py + 22.2)
        ctx.closePath()
        ctx.fill()
        ctx.stroke()

        # Opsional: ujung Kunci Perak (#D6E4F0) mulai meluncur keluar di [CAM 27]!
        if silver_key_peek:
            ctx.save()
            ctx.translate(px + 18.2, py + 22.5)
            ctx.rotate(0.28)
            ctx.fillStyle = "#D6E4F0"
            ctx.strokeStyle = "#1B2434"
            ctx.lineWidth = 1.7
            ctx.beginPath()
            ctx.arc(0, 6.5, 5.5, 0.25, math.pi * 1.75)
            ctx.arc(2.0, 6.5, 3.3, math.pi * 1.65, 0.35, True)
            ctx.closePath()
            ctx.fill()
            ctx.stroke()
            ctx.fillStyle = "#FFFFFF"
            ctx.beginPath()
            ctx.arc(-2.5, 4.5, 1.3, 0, math.pi * 2)
            ctx.fill()
            ctx.restore()

        # Dua helai benang menjuntai (setup visual wajib dari brief!)
        ctx.strokeStyle = "#3E2614"
        ctx.lineWidth = 1.55
        ctx.lineCap = "round"
        ctx.beginPath()
        ctx.moveTo(px + 14.5, py + 21.2)
        ctx.quadraticCurveTo(px + 12.0 + sway * 0.5, py + 27.5, px + 14.8 + sway, py + 33.0)
        ctx.moveTo(px + 20.2, py + 21.0)
        ctx.quadraticCurveTo(px + 23.2 + sway * 0.6, py + 26.5, px + 21.4 + sway * 1.1, py + 31.8)
        ctx.stroke()

        ctx.strokeStyle = "#FFE58A"
        ctx.lineWidth = 0.85
        ctx.beginPath()
        ctx.moveTo(px + 14.7, py + 21.2)
        ctx.quadraticCurveTo(px + 12.2 + sway * 0.5, py + 27.5, px + 15.0 + sway, py + 32.8)
        ctx.stroke()

        ctx.restore()


def _draw_bima_belt_tools(ctx: Any, cfg: Any, bx: float, by: float, facingDot: float, phase: Dict[str, Any]) -> None:
    """Apron mini kulit + alat tukang jam mengintip (obeng gagang biru, pinset kuningan, kain lap kotak-kotak)."""
    if facingDot < -0.1:
        return
    scX = max(0.12, abs(facingDot))
    ctx.save()
    ctx.translate(bx, by)
    ctx.scale(scX, 1)

    # Kain lap kotak-kotak merah-krem terselip di sisi kanan sabuk
    ctx.save()
    ctx.translate(29.0, 2.0)
    ctx.rotate(-0.14)
    ctx.fillStyle = "#F4E9D2"
    ctx.strokeStyle = "#1C141E"
    ctx.lineWidth = 1.7
    ctx.beginPath()
    ctx.moveTo(-4, 0)
    ctx.lineTo(7, 1)
    ctx.lineTo(10, 22)
    ctx.lineTo(-2, 24)
    ctx.closePath()
    ctx.fill()
    ctx.stroke()
    ctx.strokeStyle = "#C84B31"
    ctx.lineWidth = 1.4
    ctx.beginPath()
    ctx.moveTo(1.5, 1)
    ctx.lineTo(3.5, 22.5)
    ctx.moveTo(-3.2, 8)
    ctx.lineTo(7.8, 9)
    ctx.moveTo(-2.5, 15.5)
    ctx.lineTo(8.8, 16.5)
    ctx.stroke()
    ctx.restore()

    # Obeng gagang biru mengintip dari kantong kiri (-29)
    ctx.save()
    ctx.translate(-23.0, -14.0)
    ctx.rotate(-0.22)
    ctx.fillStyle = "#C9D6E5"
    ctx.fillRect(-1.0, 2.0, 2.0, 8.0)
    ctx.fillStyle = "#2478E0"
    ctx.strokeStyle = "#1C141E"
    ctx.lineWidth = 1.6
    ctx.beginPath()
    ctx.roundRect(-3.4, -9.5, 6.8, 11.5, 2.8)
    ctx.fill()
    ctx.stroke()
    ctx.fillStyle = "rgba(255,255,255,0.45)"
    ctx.fillRect(0.6, -7.8, 1.5, 8.0)
    ctx.restore()

    # Pinset kuningan mengintip dari kantong kanan (+13)
    ctx.save()
    ctx.translate(22.0, -13.0)
    ctx.rotate(0.24)
    ctx.strokeStyle = "#1C141E"
    ctx.lineWidth = 3.2
    ctx.beginPath()
    ctx.moveTo(-2.4, 5)
    ctx.lineTo(0, -10)
    ctx.lineTo(2.4, 5)
    ctx.stroke()
    ctx.strokeStyle = "#F4CE5C"
    ctx.lineWidth = 1.6
    ctx.beginPath()
    ctx.moveTo(-2.4, 5)
    ctx.lineTo(0, -10)
    ctx.lineTo(2.4, 5)
    ctx.stroke()
    ctx.restore()

    ctx.restore()


def _draw_bima_front_scarf_tail(
    ctx: Any,
    cfg: Any,
    s: float,
    c: float,
    pose: Any,
    rimI: float,
    phase: Dict[str, Any],
) -> None:
    """Ujung syal tipis merah bata (#C84B31, 40cm) menjuntai dinamis melewati bahu depan."""
    if c <= 0.08:
        return
    col = cfg.capeColor or phase["capeColor"]
    sway = (pose.capeSway if pose else 0.0) * 1.15
    ctx.save()
    ctx.translate(_base.OX, 323 + pose.pelvisY)
    ctx.rotate(pose.torsoLeanZ)
    ctx.translate(-104, -323)

    anchor_x = 128 + s * 28
    anchor_y = 208
    # Ujung syal menjuntai ke samping kanan-belakang agar siluet gerak langsung terbaca
    tail_g = ctx.createLinearGradient(anchor_x, anchor_y, anchor_x + 36 + sway, anchor_y + 72)
    tail_g.addColorStop(0, _base.tintHex(col, 0.18))
    tail_g.addColorStop(0.55, col)
    tail_g.addColorStop(1, _base.shadeHex(col, 0.62))

    ctx.fillStyle = tail_g
    ctx.strokeStyle = "#1D141F"
    ctx.lineWidth = 2.4
    ctx.lineJoin = "round"
    ctx.beginPath()
    ctx.moveTo(anchor_x - 6, anchor_y)
    ctx.quadraticCurveTo(anchor_x + 16 + sway * 0.5, anchor_y + 24, anchor_x + 28 + sway * 1.3, anchor_y + 62)
    ctx.lineTo(anchor_x + 12 + sway * 1.3, anchor_y + 68)
    ctx.quadraticCurveTo(anchor_x + 4 + sway * 0.4, anchor_y + 30, anchor_x - 16, anchor_y + 6)
    ctx.closePath()
    ctx.fill()
    ctx.stroke()

    # Garis aksen tenun + rumbai ujung syal
    ctx.strokeStyle = phase.get("scarfRimColor") or phase["trimColor"]
    ctx.lineWidth = 2.0
    ctx.beginPath()
    ctx.moveTo(anchor_x + 12 + sway * 1.15, anchor_y + 56)
    ctx.lineTo(anchor_x + 25 + sway * 1.18, anchor_y + 52)
    ctx.stroke()

    # Sorotan tepi zamrud / rim light pada syal (khusus Fase 2 & 3!)
    if rimI > 0.05:
        ctx.strokeStyle = phase.get("scarfRimColor") or phase["rimColor"]
        ctx.globalAlpha = min(0.9, 0.6 * rimI)
        ctx.lineWidth = 2.1
        ctx.beginPath()
        ctx.moveTo(anchor_x - 4, anchor_y + 2)
        ctx.quadraticCurveTo(anchor_x + 16 + sway * 0.5, anchor_y + 24, anchor_x + 27 + sway * 1.25, anchor_y + 58)
        ctx.stroke()
        ctx.globalAlpha = 1.0

    ctx.restore()


def _draw_bima_face_skin_details(ctx: Any, deg: float, phase: Dict[str, Any]) -> None:
    """Bintik freckles tipis di pangkal hidung + satu corengan oli mesin hitam di pipi kiri (360°!)."""
    # 1. Freckles tipis di pangkal hidung (tengah wajah)
    def draw_freckles() -> None:
        ctx.fillStyle = "rgba(154, 86, 52, 0.56)"
        for fx, fy, fr in [
            (92.0, 151.0, 1.25),
            (96.5, 149.2, 1.05),
            (101.2, 150.6, 1.2),
            (106.0, 149.0, 1.15),
            (110.5, 150.4, 1.2),
            (114.2, 152.2, 1.0),
        ]:
            ctx.beginPath()
            ctx.arc(fx, fy, fr, 0, math.pi * 2)
            ctx.fill()

    _base.placeOnCylinder(ctx, deg, -2.0, 102.0, 151.0, draw_freckles)

    # 2. Corengan oli mesin hitam di pipi kiri Bima (sisi kanan penonton: localDeg=+28)
    # Sapuan kuas diagonal lembut khas bekas usapan tangan tukang jam (bukan oval kaku!)
    def draw_oil_smudge() -> None:
        ctx.save()
        ctx.translate(136.0, 154.0)
        ctx.rotate(-0.34)
        # Lapisan luar lembut (feathered grease halo)
        ctx.fillStyle = "rgba(32, 28, 36, 0.28)"
        ctx.beginPath()
        ctx.moveTo(-10.5, -2.0)
        ctx.quadraticCurveTo(0.0, -5.2, 11.5, -1.2)
        ctx.quadraticCurveTo(8.5, 4.8, -1.5, 4.4)
        ctx.quadraticCurveTo(-9.5, 4.0, -10.5, -2.0)
        ctx.closePath()
        ctx.fill()
        # 2 goresan jari bekas oli mesin (asimetris & organik)
        ctx.strokeStyle = "rgba(24, 20, 28, 0.62)"
        ctx.lineWidth = 3.2
        ctx.lineCap = "round"
        ctx.beginPath()
        ctx.moveTo(-8.2, -1.0)
        ctx.quadraticCurveTo(0.5, -2.6, 8.8, -0.4)
        ctx.stroke()
        ctx.strokeStyle = "rgba(28, 24, 34, 0.44)"
        ctx.lineWidth = 2.1
        ctx.beginPath()
        ctx.moveTo(-5.5, 2.2)
        ctx.quadraticCurveTo(1.5, 1.0, 6.2, 2.6)
        ctx.stroke()
        ctx.restore()

    _base.placeOnCylinder(ctx, deg, 28.0, 136.0, 154.0, draw_oil_smudge)


def _draw_bima_goggles_and_hair(
    ctx: Any,
    cfg: Any,
    deg: float,
    s: float,
    c: float,
    pose: Any,
    rimI: float,
    phase: Dict[str, Any],
) -> None:
    """Kacamata loupe tukang jam bertengger tinggi di dahi (bebas tabrakan alis) + kilau fase-reaktif."""
    # Tali kulit cokelat retak melingkar 360° pada y=104 (di atas alis!)
    ctx.save()
    ctx.strokeStyle = "#1B131A"
    ctx.lineWidth = 8.8
    ctx.lineCap = "round"
    ctx.beginPath()
    ctx.moveTo(41, 105)
    ctx.quadraticCurveTo(104, 99 + c * 4, 169, 103)
    ctx.stroke()

    strG = ctx.createLinearGradient(42, 103, 168, 103)
    strG.addColorStop(0, "#382016")
    strG.addColorStop(0.55, "#6E442F")
    strG.addColorStop(1, "#2E1A12")
    ctx.strokeStyle = strG
    ctx.lineWidth = 5.2
    ctx.beginPath()
    ctx.moveTo(42, 105)
    ctx.quadraticCurveTo(104, 99 + c * 4, 168, 103)
    ctx.stroke()
    ctx.restore()

    def draw_loupe_pair() -> None:
        # Bayangan jatuh tipis pada dahi
        ctx.fillStyle = "rgba(24, 14, 18, 0.28)"
        ctx.fillRect(66, 109, 70, 4.5)
        # Jembatan kulit & kuningan
        ctx.fillStyle = "#4A2E1E"
        ctx.strokeStyle = "#1B131C"
        ctx.lineWidth = 2.0
        ctx.beginPath()
        ctx.roundRect(96, 100, 11, 6.5, 2)
        ctx.fill()
        ctx.stroke()

        # Lensa kiri (standar) & lensa kanan (loupe pembesar tukang jam sedikit lebih menonjol!)
        for idx, gx in enumerate([84.0, 119.0]):
            r_ext = 15.8 if idx == 0 else 16.8
            r_lens = 12.6 if idx == 0 else 13.4

            # Tabung kuningan tergores (extruded 3D brass barrel)
            ctx.fillStyle = "#6B4814"
            ctx.strokeStyle = "#1B131C"
            ctx.lineWidth = 2.1
            ctx.beginPath()
            ctx.arc(gx - s * 3.8, 103.0, r_ext, 0, math.pi * 2)
            ctx.fill()
            ctx.stroke()

            # Bantalan kulit cokelat
            ctx.fillStyle = "#3B251B"
            ctx.beginPath()
            ctx.arc(gx - s * 1.4, 103.0, r_ext, 0, math.pi * 2)
            ctx.fill()
            ctx.stroke()

            # Lensa kaca reflektif sesuai fase pencahayaan PDF!
            glG = ctx.createRadialGradient(gx + 4.0, 98.0, 1.5, gx, 103.0, r_lens)
            glG.addColorStop(0, phase["lensTop"])
            glG.addColorStop(0.45, phase["lensMid"])
            glG.addColorStop(1, phase["lensDeep"])
            ctx.fillStyle = glG
            ctx.beginPath()
            ctx.arc(gx, 103.0, r_lens, 0, math.pi * 2)
            ctx.fill()

            # Cincin lensa pembesar tambahan di lensa kanan (loupe khas tukang jam!)
            if idx == 1:
                ctx.strokeStyle = "rgba(255, 250, 224, 0.55)"
                ctx.lineWidth = 1.3
                ctx.beginPath()
                ctx.arc(gx, 103.0, r_lens * 0.62, 0, math.pi * 2)
                ctx.stroke()

            # Bezel kuningan tergores (scratched brass #B8860B)
            brG = ctx.createLinearGradient(gx - 14, 115, gx + 14, 90)
            brG.addColorStop(0, _base.shadeHex(phase["trimColor"], 0.62))
            brG.addColorStop(0.55, "#FCE18B")
            brG.addColorStop(1, _base.shadeHex(phase["trimColor"], 0.72))
            ctx.strokeStyle = "#1B131C"
            ctx.lineWidth = 5.0
            ctx.beginPath()
            ctx.arc(gx, 103.0, r_lens + 0.6, 0, math.pi * 2)
            ctx.stroke()
            ctx.strokeStyle = brG
            ctx.lineWidth = 2.8
            ctx.beginPath()
            ctx.arc(gx, 103.0, r_lens + 0.6, 0, math.pi * 2)
            ctx.stroke()

            # Paku keling kuningan & pita kilau specular tajam cel-shade
            ctx.fillStyle = "#FFFCE0"
            ctx.beginPath()
            ctx.arc(gx - 10.5, 103.0, 1.15, 0, math.pi * 2)
            ctx.arc(gx + 10.5, 103.0, 1.15, 0, math.pi * 2)
            ctx.fill()

            ctx.fillStyle = "rgba(255, 255, 255, 0.92)"
            ctx.beginPath()
            ctx.ellipse(gx + 4.2, 98.2, 4.0, 2.1, -0.52, 0, math.pi * 2)
            ctx.fill()

    _base.placeOnCylinder(ctx, deg, -3.0, 101.0, 103.0, draw_loupe_pair)


def _draw_bima_sculpted_hair(
    ctx: Any,
    cfg: Any,
    deg: float,
    s: float,
    c: float,
    pose: Any,
    rimI: float,
    phase: Dict[str, Any],
) -> None:
    """Rambut cokelat tua berbentuk rumpun tebal tersapu angin (sculpted chunky clumps) + 1 jambul ikonik berpegas."""
    hair_col = cfg.hairColor or phase["hairColor"]
    sway = (pose.featherSway if pose else 0.0) * 0.55

    hGrad = ctx.createLinearGradient(36, 40, 174, 106)
    hGrad.addColorStop(0, _base.shadeHex(hair_col, 0.52))
    hGrad.addColorStop(0.45, hair_col)
    hGrad.addColorStop(0.76, _base.tintHex(hair_col, 0.34))
    hGrad.addColorStop(1, _base.shadeHex(hair_col, 0.58))

    ctx.save()
    ctx.fillStyle = hGrad
    ctx.strokeStyle = "#1B131C"
    ctx.lineWidth = 3.2
    ctx.lineJoin = "round"
    ctx.lineCap = "round"

    # Rumpun rambut chunky tersapu angin (siluet rambut anak 13 th energik, bukan helm!)
    ctx.beginPath()
    ctx.moveTo(41, 102)
    # Rumpun samping kiri mencuat miring
    ctx.bezierCurveTo(32, 86, 33, 68, 45, 56)
    ctx.quadraticCurveTo(50, 64, 55, 65)
    # Rumpun kiri-atas tersapu ke belakang
    ctx.bezierCurveTo(54, 48, 70, 38, 92, 42)
    ctx.quadraticCurveTo(86, 51, 88, 56)
    # Rumpun puncak tengah tebal melengkung
    ctx.bezierCurveTo(100, 34, 128, 34, 146, 48)
    ctx.quadraticCurveTo(138, 55, 138, 60)
    # Rumpun kanan-belakang tersapu angin
    ctx.bezierCurveTo(154, 48, 172, 56, 176, 74)
    ctx.quadraticCurveTo(166, 78, 162, 82)
    ctx.quadraticCurveTo(174, 88, 168, 102)
    # Garis bawah rambut melengkung rapi di atas tali kacamata loupe
    ctx.quadraticCurveTo(148, 90, 128, 94)
    ctx.quadraticCurveTo(104, 87, 76, 94)
    ctx.quadraticCurveTo(56, 90, 41, 102)
    ctx.closePath()
    ctx.fill()
    ctx.stroke()

    # Bayangan cel-shade antar rumpun rambut (tanpa garis kaku melintang)
    ctx.strokeStyle = _base.shadeHex(hair_col, 0.40)
    ctx.lineWidth = 2.0
    ctx.beginPath()
    ctx.moveTo(64, 66)
    ctx.quadraticCurveTo(74, 76, 72, 88)
    ctx.moveTo(116, 56)
    ctx.quadraticCurveTo(126, 68, 124, 86)
    ctx.moveTo(148, 68)
    ctx.quadraticCurveTo(154, 78, 148, 90)
    ctx.stroke()

    # Pita kilau cel-shade melengkung mengikuti kontur rambut
    ctx.strokeStyle = phase["rimColor"]
    ctx.globalAlpha = min(0.82, 0.48 * rimI)
    ctx.lineWidth = 3.2
    ctx.beginPath()
    ctx.moveTo(96, 54)
    ctx.quadraticCurveTo(124, 48, 146, 64)
    ctx.stroke()
    ctx.globalAlpha = 1.0

    # SATU JAMBUL IKONIK DI DAHI (melengkung gagah di tengah dahi & memantul saat overshoot!)
    if c > -0.35:
        jx = 100 + s * 28
        ctx.fillStyle = hGrad
        ctx.strokeStyle = "#1B131C"
        ctx.lineWidth = 2.9
        ctx.beginPath()
        ctx.moveTo(jx - 8, 86)
        ctx.bezierCurveTo(
            jx - 16,
            56 - abs(sway) * 0.4,
            jx + 8 + sway,
            26 - abs(sway) * 0.35,
            jx + 28 + sway * 1.4,
            40,
        )
        ctx.bezierCurveTo(
            jx + 16 + sway * 0.8,
            42,
            jx + 10 + sway * 0.3,
            58,
            jx + 10,
            88,
        )
        ctx.quadraticCurveTo(jx + 1, 82, jx - 8, 86)
        ctx.closePath()
        ctx.fill()
        ctx.stroke()

        # Kilau hangat di puncak lengkung jambul
        ctx.strokeStyle = phase["rimColor"]
        ctx.globalAlpha = min(0.9, 0.62 * rimI)
        ctx.lineWidth = 2.0
        ctx.beginPath()
        ctx.moveTo(jx - 2, 54)
        ctx.quadraticCurveTo(jx + 10 + sway * 0.7, 38, jx + 20 + sway, 40)
        ctx.stroke()
        ctx.globalAlpha = 1.0

    ctx.restore()


class BimaHeroCharacter:
    """
    Desain Karakter Hero Bima berbasis ekspor generator.html (`BimaCharacter`) dengan
    detail Character Bible penuh + dukungan 3 Fase Pencahayaan PDF + RIGGING 100% TERBUKA.

    Default mode selalu `animation="static"` (pose desain netral, tanpa kunci animasi).
    Kirim `rig=HumanoidRig(...)` untuk mengatur bebas setiap sendi IK/FK, ekspresi wajah,
    syal, jambul, benang saku, maupun fase pencahayaan di tiap adegan.
    """

    def __init__(
        self,
        scale: float = 3.0,
        fps: int = 30,
        lighting_phase: LightingPhase = "phase1",
        hero_details: bool = True,
        silver_key_peek: bool = False,
        config_overrides: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.scale = float(scale)
        self.fps = int(fps)
        self.lighting_phase = lighting_phase
        self.hero_details = bool(hero_details)
        self.silver_key_peek = bool(silver_key_peek)
        self.base_config = copy.deepcopy(_base.CHARACTER_CONFIG)
        if config_overrides:
            self.base_config.update(config_overrides)

    def _build_phase_config(
        self,
        lighting_phase: LightingPhase,
        rig: Optional[HumanoidRig] = None,
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        phase = LIGHTING_PHASE_PROFILES.get(lighting_phase, LIGHTING_PHASE_PROFILES["phase1"])
        cfg = copy.deepcopy(self.base_config)
        cfg["robeColor"] = phase["robeColor"]
        cfg["capeColor"] = phase["capeColor"]
        cfg["limbColor"] = phase["limbColor"]
        cfg["trimColor"] = phase["trimColor"]
        cfg["skinColor"] = phase["skinColor"]
        cfg["blushColor"] = phase["blushColor"]
        cfg["hairColor"] = phase["hairColor"]
        cfg["sashColor"] = phase["sashColor"]
        cfg["rimIntensity"] = phase["rimIntensity"]
        cfg["shadowDepth"] = phase["shadowDepth"]
        if rig and rig.config_overrides:
            cfg.update(rig.config_overrides)
        return cfg, phase

    def render_svg(
        self,
        frame: int = 0,
        angle: float = 0.0,
        animation: str = "static",
        rig: Optional[HumanoidRig] = None,
        lighting_phase: Optional[LightingPhase] = None,
        hero_details: Optional[bool] = None,
        silver_key_peek: Optional[bool] = None,
        pad_top: Optional[int] = None,
        **kwargs: Any,
    ) -> str:
        active_phase_key: LightingPhase = (
            lighting_phase
            or (rig.lighting_phase if (rig and rig.lighting_phase) else None)  # type: ignore[assignment]
            or self.lighting_phase
        )
        use_hero = self.hero_details if hero_details is None else hero_details
        peek_silver = (
            silver_key_peek
            if silver_key_peek is not None
            else (rig.silver_key_peek if (rig and rig.silver_key_peek is not None) else self.silver_key_peek)
        )
        cfg, phase = self._build_phase_config(active_phase_key, rig=rig)
        merged_kw = rig_to_render_kwargs(rig, kwargs)
        active_anim = merged_kw.pop("animation", animation) or "static"
        active_angle = merged_kw.pop("angle", angle)

        # Pasang hook non-destruktif pada modul bima_character dan kembalikan di finally
        orig_compute_pose = _base.computeSkeletonPose
        orig_leg = _base.drawArticulatedLeg
        orig_arm = _base.drawArticulatedArm
        orig_outfit = _base.drawOutfitLayer
        orig_belt = _base.drawBeltAccessory
        orig_cape = _base.drawCapeOrBackItem
        orig_face_acc = _base.drawFaceAccessory
        orig_headwear = _base.drawHeadwear

        state: Dict[str, Any] = {"pose": None}

        def hooked_pose(c_cfg: Any, animMode: str, rawT: float, overrides: Any = None) -> Any:
            p = orig_compute_pose(c_cfg, animMode, rawT, overrides)
            p = apply_humanoid_rig_to_pose(p, rig, animMode, _base)
            if rig and rig.thread_sway is not None:
                p.threadSway = float(rig.thread_sway)
            state["pose"] = p
            return p

        _base.computeSkeletonPose = hooked_pose

        if use_hero:
            def hooked_leg(ctx: Any, hip: Any, knee: Any, ankle: Any, toe: Any, rimI: float, limbColor: Any = None) -> None:
                _draw_bima_leg(ctx, hip, knee, ankle, toe, rimI, limbColor, phase)

            def hooked_arm(ctx: Any, sh: Any, elb: Any, hnd: Any, rimI: float, limbColor: Any = None) -> None:
                _draw_bima_arm(ctx, sh, elb, hnd, rimI, _base._wrap(cfg), phase)

            def hooked_outfit(ctx: Any, c_cfg: Any, s: float, c: float, shD: float) -> None:
                orig_outfit(ctx, c_cfg, s, c, shD)
                _draw_bima_outfit_details(ctx, c_cfg, s, c, shD, state["pose"], phase, silver_key_peek=peek_silver)

            def hooked_belt(ctx: Any, c_cfg: Any, bx: float, by: float, facingDot: float) -> None:
                _draw_bima_belt_tools(ctx, c_cfg, bx, by, facingDot, phase)
                orig_belt(ctx, c_cfg, bx, by, facingDot)

            def hooked_cape(ctx: Any, c_cfg: Any, s: float, c: float, pose: Any, rimI: float, isBackPass: bool) -> None:
                orig_cape(ctx, c_cfg, s, c, pose, rimI, isBackPass)
                if not isBackPass:
                    _draw_bima_front_scarf_tail(ctx, c_cfg, s, c, pose, rimI, phase)

            def hooked_face_acc(ctx: Any, c_cfg: Any, deg: float, s: float, c: float, layerMode: Any = None) -> None:
                if layerMode == "skin":
                    _draw_bima_face_skin_details(ctx, deg, phase)
                    orig_face_acc(ctx, c_cfg, deg, s, c, layerMode)
                elif layerMode == "protruding" and c_cfg.faceAccessory == "goggles":
                    _draw_bima_goggles_and_hair(ctx, c_cfg, deg, s, c, state["pose"], c_cfg.rimIntensity, phase)
                else:
                    orig_face_acc(ctx, c_cfg, deg, s, c, layerMode)

            def hooked_headwear(ctx: Any, c_cfg: Any, deg: float, s: float, c: float, pose: Any, rimI: float) -> None:
                if c_cfg.hat == "none":
                    _draw_bima_sculpted_hair(ctx, c_cfg, deg, s, c, pose, rimI, phase)
                else:
                    orig_headwear(ctx, c_cfg, deg, s, c, pose, rimI)

            _base.drawArticulatedLeg = hooked_leg
            _base.drawArticulatedArm = hooked_arm
            _base.drawOutfitLayer = hooked_outfit
            _base.drawBeltAccessory = hooked_belt
            _base.drawCapeOrBackItem = hooked_cape
            _base.drawFaceAccessory = hooked_face_acc
            _base.drawHeadwear = hooked_headwear

        try:
            char = _base.BimaCharacter(config_overrides=cfg, scale=self.scale, fps=self.fps, default_animation="static")
            svg_out = char.render_svg(frame=frame, angle=active_angle, animation=active_anim, **merged_kw)
            # Otomatis tambah headroom atas jika karakter melompat atau pelvis/head naik tinggi
            need_pad = pad_top
            if need_pad is None:
                p_cur = state["pose"]
                top_lift = max(
                    0.0,
                    -(p_cur.headBobY if p_cur else 0.0),
                    (p_cur.jumpHeight if p_cur else 0.0),
                )
                if active_anim == "jump" or top_lift > 12.0:
                    need_pad = int(round(max(68.0, top_lift + 22.0) * self.scale))
                else:
                    need_pad = 0
            if need_pad > 0:
                w_px, h_px = char.pixel_size
                svg_out = svg_out.replace(
                    f'height="{h_px}" viewBox="0 0 {w_px} {h_px}"',
                    f'height="{h_px + need_pad}" viewBox="0 {-need_pad} {w_px} {h_px + need_pad}"',
                    1,
                )
            return svg_out
        finally:
            _base.computeSkeletonPose = orig_compute_pose
            _base.drawArticulatedLeg = orig_leg
            _base.drawArticulatedArm = orig_arm
            _base.drawOutfitLayer = orig_outfit
            _base.drawBeltAccessory = orig_belt
            _base.drawCapeOrBackItem = orig_cape
            _base.drawFaceAccessory = orig_face_acc
            _base.drawHeadwear = orig_headwear

    def render_pil(
        self,
        frame: int = 0,
        angle: float = 0.0,
        animation: str = "static",
        rig: Optional[HumanoidRig] = None,
        lighting_phase: Optional[LightingPhase] = None,
        hero_details: Optional[bool] = None,
        silver_key_peek: Optional[bool] = None,
        pad_top: Optional[int] = None,
        **kwargs: Any,
    ) -> Any:
        import io
        import resvg_py
        from PIL import Image

        svg_str = self.render_svg(
            frame=frame,
            angle=angle,
            animation=animation,
            rig=rig,
            lighting_phase=lighting_phase,
            hero_details=hero_details,
            silver_key_peek=silver_key_peek,
            pad_top=pad_top,
            **kwargs,
        )
        png_bytes = resvg_py.svg_to_bytes(svg_string=svg_str, skip_system_fonts=True)
        return Image.open(io.BytesIO(png_bytes)).convert("RGBA")
