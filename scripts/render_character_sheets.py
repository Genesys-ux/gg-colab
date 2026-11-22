"""
Render 4 studio-grade Character Design Review Sheets (Desain Netral + Rigging 100% Terbuka).
Semua karakter humanoid dirender dari modul ekspor generator.html (`characters/`) dalam mode
`animation="static"` (tidak terkunci ke animasi/pose tertentu) sehingga bebas disesuaikan per adegan.
"""

from __future__ import annotations

import os
import shutil
import sys
from typing import Tuple

from PIL import Image, ImageDraw, ImageFont

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

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

PREVIEW_DIR = os.path.join(PROJECT_DIR, "previews")
ARTIFACT_DIR = r"C:\Users\lutfi\.gemini\antigravity\brain\47e864ac-ef32-4f4e-a877-90846cd98a78"
os.makedirs(PREVIEW_DIR, exist_ok=True)


def get_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = (
        ["C:/Windows/Fonts/segoeuib.ttf", "C:/Windows/Fonts/arialbd.ttf"]
        if bold
        else ["C:/Windows/Fonts/segoeui.ttf", "C:/Windows/Fonts/arial.ttf"]
    )
    for p in candidates:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except OSError:
                pass
    return ImageFont.load_default()


FONT_H1 = get_font(34, bold=True)
FONT_H2 = get_font(22, bold=True)
FONT_SUB = get_font(18, bold=False)
FONT_TAG = get_font(16, bold=True)
FONT_SMALL = get_font(14, bold=False)


def make_gradient_bg(
    w: int,
    h: int,
    top_rgb: Tuple[int, int, int],
    bot_rgb: Tuple[int, int, int],
) -> Image.Image:
    img = Image.new("RGB", (w, h), top_rgb)
    draw = ImageDraw.Draw(img)
    for y in range(h):
        u = y / max(1, h - 1)
        r = int(top_rgb[0] + (bot_rgb[0] - top_rgb[0]) * u)
        g = int(top_rgb[1] + (bot_rgb[1] - top_rgb[1]) * u)
        b = int(top_rgb[2] + (bot_rgb[2] - top_rgb[2]) * u)
        draw.line([(0, y), (w, y)], fill=(r, g, b))
    return img


def draw_header(
    canvas: Image.Image,
    title: str,
    subtitle: str,
    accent: Tuple[int, int, int] = (242, 183, 5),
) -> None:
    draw = ImageDraw.Draw(canvas)
    w = canvas.width
    draw.rectangle([0, 0, w, 96], fill=(20, 17, 30))
    draw.rectangle([0, 92, w, 96], fill=accent)
    draw.text((32, 16), title, font=FONT_H1, fill=(248, 244, 252))
    draw.text((34, 58), subtitle, font=FONT_SUB, fill=(182, 174, 202))


def draw_wrapped_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    x: int,
    y: int,
    max_chars: int,
    line_height: int,
    font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
    fill: Tuple[int, int, int],
    max_lines: int = 3,
) -> None:
    words = text.split(" ")
    lines, cur = [], ""
    for wd in words:
        if len((cur + " " + wd).strip()) > max_chars:
            if cur:
                lines.append(cur.strip())
            cur = wd
        else:
            cur = (cur + " " + wd).strip()
    if cur:
        lines.append(cur)
    for li, ln in enumerate(lines[:max_lines]):
        draw.text((x, y + li * line_height), ln, font=font, fill=fill)


def paste_fit(
    canvas: Image.Image,
    sprite: Image.Image,
    box: Tuple[int, int, int, int],
    valign: str = "bottom",
) -> None:
    x0, y0, x1, y1 = box
    bw, bh = x1 - x0, y1 - y0
    sw, sh = sprite.size
    ratio = min(bw / sw, bh / sh)
    nw, nh = max(1, int(sw * ratio)), max(1, int(sh * ratio))
    resized = sprite.resize((nw, nh), Image.Resampling.LANCZOS)
    px = x0 + (bw - nw) // 2
    if valign == "bottom":
        py = y1 - nh
    elif valign == "top":
        py = y0
    else:
        py = y0 + (bh - nh) // 2
    canvas.paste(resized, (px, py), resized)


def save_sheet(img: Image.Image, filename: str) -> str:
    p_local = os.path.join(PREVIEW_DIR, filename)
    img.save(p_local, quality=95)
    if os.path.isdir(ARTIFACT_DIR):
        shutil.copy2(p_local, os.path.join(ARTIFACT_DIR, filename))
    print(f"Saved sheet: {p_local} ({img.width}x{img.height})")
    return p_local


def render_sheet_01_bima_turnaround() -> None:
    w, h = 2100, 1180
    sheet = make_gradient_bg(w, h, (245, 241, 232), (225, 217, 204))
    draw_header(
        sheet,
        "SHEET 01 — BIMA (DESAIN KARAKTER NETRAL • RIGGING TERBUKA 360°)",
        "Basis: C:\\Users\\lutfi\\Downloads\\122\\generator.html (bima_preset.json -> static neutral) + Hero Bible Detail Pass",
    )
    draw = ImageDraw.Draw(sheet)

    bima = BimaHeroCharacter(scale=3.0, fps=30, lighting_phase="phase1", hero_details=True)

    cards = [
        ("0° DEPAN (NETRAL)", 0, True),
        ("45° 3/4 KIRI (NETRAL)", 45, True),
        ("90° SAMPING (NETRAL)", 90, True),
        ("180° BELAKANG (NETRAL)", 180, True),
        ("0° PURE GENERATOR.HTML", 0, False),
    ]
    cw, gap, start_x = 390, 20, 35
    card_top, card_bot = 120, 850

    for idx, (label, ang, hero_flag) in enumerate(cards):
        cx0 = start_x + idx * (cw + gap)
        cx1 = cx0 + cw
        bg_col = (250, 248, 243) if hero_flag else (238, 234, 245)
        border_col = (196, 178, 148) if hero_flag else (142, 126, 172)
        draw.rounded_rectangle([cx0, card_top, cx1, card_bot], radius=16, fill=bg_col, outline=border_col, width=2)
        badge_bg = (36, 30, 50) if hero_flag else (96, 54, 122)
        draw.rounded_rectangle([cx0 + 16, card_top + 14, cx1 - 16, card_top + 48], radius=10, fill=badge_bg)
        draw.text((cx0 + 28, card_top + 21), label, font=FONT_TAG, fill=(255, 245, 214))

        img = bima.render_pil(angle=ang, animation="static", hero_details=hero_flag)
        paste_fit(sheet, img, (cx0 + 10, card_top + 56, cx1 - 10, card_bot - 16))

    # Strip callout close-up detail desain Bima
    bima_front_hd = bima.render_pil(angle=12, animation="static", hero_details=True, silver_key_peek=True)
    callouts = [
        (
            "1. WAJAH, LOUPE & JAMBUL",
            "Freckles hidung, corengan oli pipi kiri, loupe kuningan & jambul pegas (unlocked)",
            (110, 110, 610, 560),
        ),
        (
            "2. SAKU ROBEK & ALAT SABUK",
            "Saku kanan bawah robek + 2 benang (silver_key_peek opsional per adegan) + obeng/pinset",
            (130, 720, 590, 1080),
        ),
        (
            "3. SEPATU BOT & CELANA KARGO",
            "Celana navy #2B3A55 digulung + bot kulit lumpur + tali oranye menyala (+15% chunky)",
            (130, 1140, 590, 1500),
        ),
    ]
    cw2, gap2 = 656, 24
    for idx, (title_c, desc_c, crop_box) in enumerate(callouts):
        x0 = 35 + idx * (cw2 + gap2)
        y0, x1, y1 = 874, x0 + cw2, 1152
        draw.rounded_rectangle([x0, y0, x1, y1], radius=14, fill=(30, 26, 42), outline=(242, 183, 5), width=2)
        crop = bima_front_hd.crop(crop_box)
        draw.rounded_rectangle([x0 + 14, y0 + 14, x0 + 254, y1 - 14], radius=10, fill=(246, 242, 234))
        paste_fit(sheet, crop, (x0 + 18, y0 + 18, x0 + 250, y1 - 18), valign="center")
        draw.text((x0 + 272, y0 + 28), title_c, font=FONT_H2, fill=(242, 183, 5))
        draw_wrapped_text(draw, desc_c, x0 + 272, y0 + 68, 34, 26, FONT_SUB, (232, 228, 240), max_lines=3)

    save_sheet(sheet, "sheet_01_bima_turnaround.png")


def render_sheet_02_bima_expressions_and_phases() -> None:
    w, h = 2100, 1480
    sheet = make_gradient_bg(w, h, (26, 22, 36), (16, 14, 24))
    draw_header(
        sheet,
        "SHEET 02 — BUKTI RIGGING TERBUKA (HumanoidRig) & MATRIKS 3 FASE PDF",
        "Semua sendi IK/FK, ekspresi, syal, jambul, dan fase lighting 100% bebas diatur manual per adegan (tanpa lock!)",
    )
    draw = ImageDraw.Draw(sheet)

    draw.text((36, 114), "A. CONTOH KONTROL MANUAL HumanoidRig (POSE, TARGET IK TANGAN/KAKI, SYAL & EKSPRESI BEBAS)", font=FONT_H2, fill=(242, 183, 5))
    bima = BimaHeroCharacter(scale=3.0, fps=30, lighting_phase="phase1", hero_details=True)

    # Semua pose di bawah memakai animation="static" + manual HumanoidRig (membuktikan 0% rigging terkunci!)
    rig_demos = [
        (
            "DESAIN NETRAL (DEFAULT)",
            HumanoidRig(angle=0),
        ),
        (
            "MANUAL IK: MERAIH KUNCI",
            HumanoidRig(
                angle=26,
                torso_lean_z=0.10,
                head_tilt=-0.06,
                eyes="shocked",
                eyebrows="worried",
                mouth="open_yell",
                eye_gaze_x=0.55,
                eye_gaze_y=-0.35,
                right_hand_target=(92, 178, 42),
                left_hand_target=(-68, 262, 10),
                scarf_sway=-24,
                jambul_sway=-10,
            ),
        ),
        (
            "MANUAL IK: LOMPAT BEBAS",
            HumanoidRig(
                angle=22,
                pelvis_y=-42,
                head_bob_y=-46,
                jump_height=42,
                torso_lean_z=0.06,
                eyes="focused",
                eyebrows="angry",
                mouth="grit_teeth",
                right_hand_target=(84, 152, 36),
                left_hand_target=(-76, 166, 26),
                left_foot_target=(-32, 396, -24),
                right_foot_target=(42, 408, 22),
                scarf_sway=-32,
                jambul_sway=12,
            ),
        ),
        (
            "MANUAL KOMEDI: KAGET",
            HumanoidRig(
                angle=8,
                head_tilt=0.12,
                squash_x=1.08,
                squash_y=0.93,
                eyes="asymmetric",
                eyebrows="raised",
                mouth="small_o",
                sweat_drop=True,
                dizzy_stars=0.95,
                right_hand_target=(78, 188, 34),
                left_hand_target=(-48, 134, 38),
                jambul_sway=14,
            ),
        ),
        (
            "MANUAL ENDING: SAKU ROBEK",
            HumanoidRig(
                angle=10,
                eyes="happy",
                eyebrows="happy",
                mouth="happy_open",
                right_hand_target=(84, 166, 32),
                left_hand_target=(-18, 248, 38),
                silver_key_peek=True,
                thread_sway=5.0,
            ),
        ),
    ]

    cw, gap = 390, 20
    for idx, (lbl, r_cfg) in enumerate(rig_demos):
        x0 = 35 + idx * (cw + gap)
        y0, x1, y1 = 152, x0 + cw, 768
        draw.rounded_rectangle([x0, y0, x1, y1], radius=16, fill=(244, 240, 232), outline=(88, 78, 112), width=2)
        draw.rounded_rectangle([x0 + 16, y0 + 12, x1 - 16, y0 + 44], radius=9, fill=(32, 26, 46))
        draw.text((x0 + 26, y0 + 18), lbl, font=FONT_TAG, fill=(255, 242, 200))
        img = bima.render_pil(animation="static", rig=r_cfg)
        paste_fit(sheet, img, (x0 + 10, y0 + 50, x1 - 10, y1 - 12))

    # Baris 2: 4 Kartu Respons 3 Fase Pencahayaan dari PDF (dalam pose desain netral!)
    draw.text((36, 796), "B. RESPONS MATERIAL & WARNA BIMA DI 3 FASE PENCAHAYAAN (POSE DESAIN NETRAL • TABEL PDF)", font=FONT_H2, fill=(92, 235, 255))
    phases = [
        (
            "FASE 1: LOW SUN & BLUE SHADE (00:00-00:26)",
            "Jaket emas hangat / bayangan zaitun, syal kontras, specular kuningan cel-shade",
            "phase1",
            (242, 198, 126),
            (62, 92, 140),
            (255, 230, 150),
        ),
        (
            "FASE 2: INDIGO & EMERALD TURN (00:27-00:38)",
            "Mustard gelap + rim merah tungku, syal tepi zamrud, loupe pantulkan uap hijau",
            "phase2",
            (24, 34, 68),
            (16, 76, 66),
            (255, 112, 56),
        ),
        (
            "FASE 3A: ULTRA-LOW CRIMSON SUN (00:39-00:52)",
            "Jaket jingga-emas menyala, syal menyatu langit crimson, celana jangkar gelap",
            "phase3_crimson",
            (196, 64, 48),
            (54, 32, 94),
            (255, 178, 92),
        ),
        (
            "FASE 3B: FROZEN TWILIGHT (00:53-00:58)",
            "Bayangan ungu pekat + crisp cyan rim light super tajam & pantulan cyan di loupe",
            "phase3_twilight",
            (58, 34, 96),
            (24, 46, 86),
            (102, 245, 255),
        ),
    ]
    pw, pgap = 492, 20
    for idx, (title_p, desc_p, pkey, bg_top, bg_bot, border_rgb) in enumerate(phases):
        x0 = 35 + idx * (pw + pgap)
        y0, x1, y1 = 836, x0 + pw, 1450
        card_bg = make_gradient_bg(pw, y1 - y0, bg_top, bg_bot)
        sheet.paste(card_bg, (x0, y0))
        draw.rectangle([x0, y0, x1, y1], outline=border_rgb, width=3)
        draw.rectangle([x0 + 3, y0 + 3, x1 - 3, y0 + 44], fill=(16, 14, 24))
        draw.text((x0 + 14, y0 + 13), title_p, font=FONT_TAG, fill=border_rgb)
        draw.rectangle([x0 + 3, y1 - 58, x1 - 3, y1 - 3], fill=(16, 14, 24))
        draw_wrapped_text(draw, desc_p, x0 + 14, y1 - 50, 48, 22, FONT_SMALL, (224, 224, 236), max_lines=2)

        img = bima.render_pil(angle=22, animation="static", lighting_phase=pkey)
        paste_fit(sheet, img, (x0 + 20, y0 + 50, x1 - 20, y1 - 62))

    save_sheet(sheet, "sheet_02_bima_expressions_and_phases.png")


def render_sheet_03_oren_and_hero_props() -> None:
    w, h = 2100, 1420
    sheet = make_gradient_bg(w, h, (244, 239, 230), (222, 214, 200))
    draw_header(
        sheet,
        'SHEET 03 — "OREN" (DESAIN NETRAL + OrenRig TERBUKA) & HERO PROPS (KeyPropRig)',
        "Seluruh pose Oren & orientasi 3D Kunci Emas/Perak tidak terkunci — bebas disesuaikan per adegan",
        accent=(230, 126, 34),
    )
    draw = ImageDraw.Draw(sheet)

    draw.text((36, 114), 'A. "OREN" — TURNAROUND DESAIN NETRAL (0°-180°) + CONTOH KONTROL MANUAL OrenRig', font=FONT_H2, fill=(38, 28, 46))
    oren = OrenCharacter(scale=3.0)
    oren_views = [
        ("0° DEPAN (NETRAL)", OrenRig(angle=0), False),
        ("45° 3/4 KIRI (NETRAL)", OrenRig(angle=45), False),
        ("90° SAMPING (NETRAL)", OrenRig(angle=90), False),
        ("180° BELAKANG (NETRAL)", OrenRig(angle=180), False),
        (
            "MANUAL OrenRig: CAKAR + KUKU",
            OrenRig(
                angle=16,
                body_lean=-0.06,
                gaze_x=0.45,
                eyelid_level=0.58,
                right_paw_raised=1.0,
                show_paw_pads=True,
                claws_out=0.85,
                tail_sway=22.0,
                bell_sway=6.0,
            ),
            True,
        ),
    ]
    cw, gap = 390, 20
    for idx, (lbl, orig_cfg, is_custom) in enumerate(oren_views):
        x0 = 35 + idx * (cw + gap)
        y0, x1, y1 = 152, x0 + cw, 670
        draw.rounded_rectangle(
            [x0, y0, x1, y1],
            radius=16,
            fill=(252, 248, 240) if not is_custom else (255, 242, 224),
            outline=(230, 126, 34) if is_custom else (196, 178, 152),
            width=3 if is_custom else 2,
        )
        draw.rounded_rectangle([x0 + 16, y0 + 12, x1 - 16, y0 + 44], radius=9, fill=(176, 78, 20) if is_custom else (42, 34, 52))
        draw.text((x0 + 24, y0 + 18), lbl, font=FONT_TAG, fill=(255, 246, 228))
        img = oren.render_pil(rig=orig_cfg)
        paste_fit(sheet, img, (x0 + 14, y0 + 52, x1 - 14, y1 - 14))

    draw.text((36, 706), "B. HERO PROPS MICRO-PBR CEL-SHADED — KUNCI EMAS (~14 CM) VS KUNCI PERAK (~11 CM)", font=FONT_H2, fill=(38, 28, 46))
    gold = GoldenKeyProp(scale=3.0)
    silver = SilverKeyProp(scale=3.0)

    prop_cards = [
        (
            "KUNCI EMAS — MASTER CLOCK KEY (~14 CM)",
            "Kepala roda gigi matahari berongga (tembus sinar Low Sun [CAM 01]), kuningan antik & patina",
            gold.render_pil(rig=KeyPropRig(yaw_deg=0, roll_deg=-18, sun_glow=True)),
            (46, 34, 24),
            (242, 183, 5),
        ),
        (
            "KUNCI EMAS — SUDUT 3D (38° YAW)",
            "Memperlihatkan ketebalan bevel kuningan, goresan logam & pita specular cel-shade",
            gold.render_pil(rig=KeyPropRig(yaw_deg=38, roll_deg=-12, sun_glow=False)),
            (36, 28, 36),
            (230, 174, 48),
        ),
        (
            "KUNCI PERAK — PLOT TWIST KEY (~11 CM)",
            "Kepala bulan sabit mekanis + gerigi tajam, brushed steel dingin (#D6E4F0) untuk [CAM 27]",
            silver.render_pil(rig=KeyPropRig(yaw_deg=0, roll_deg=18)),
            (26, 34, 50),
            (180, 214, 240),
        ),
        (
            "PERBANDINGAN SKALA (14 CM VS 11 CM)",
            "Kunci Perak lebih ramping & dingin agar langsung terasa janggal saat jatuh dari saku kuning",
            None,
            (30, 26, 40),
            (140, 225, 245),
        ),
    ]
    pw, pgap = 492, 20
    for idx, (t_p, d_p, p_img, bg_rgb, acc_rgb) in enumerate(prop_cards):
        x0 = 35 + idx * (pw + pgap)
        y0, x1, y1 = 744, x0 + pw, 1390
        draw.rounded_rectangle([x0, y0, x1, y1], radius=16, fill=bg_rgb, outline=acc_rgb, width=3)
        draw.rounded_rectangle([x0 + 14, y0 + 14, x1 - 14, y0 + 48], radius=9, fill=(18, 16, 26))
        draw.text((x0 + 24, y0 + 21), t_p, font=FONT_TAG, fill=acc_rgb)

        if p_img is not None:
            paste_fit(sheet, p_img, (x0 + 36, y0 + 58, x1 - 36, y1 - 76), valign="center")
        else:
            g_cmp = gold.render_pil(rig=KeyPropRig(yaw_deg=12, roll_deg=0, sun_glow=True))
            s_cmp = silver.render_pil(rig=KeyPropRig(yaw_deg=-12, roll_deg=0))
            paste_fit(sheet, g_cmp, (x0 + 20, y0 + 68, x0 + 250, y1 - 76), valign="center")
            paste_fit(sheet, s_cmp, (x0 + 240, y0 + 68, x1 - 20, y1 - 76), valign="center")

        draw.rectangle([x0 + 10, y1 - 66, x1 - 10, y1 - 10], fill=(18, 16, 26))
        draw_wrapped_text(draw, d_p, x0 + 20, y1 - 58, 48, 22, FONT_SMALL, (224, 224, 236), max_lines=2)

    save_sheet(sheet, "sheet_03_oren_and_hero_props.png")


def render_sheet_04_figuran_and_cast_lineup() -> None:
    w, h = 2100, 1280
    sheet = make_gradient_bg(w, h, (245, 241, 233), (225, 217, 205))
    draw_header(
        sheet,
        "SHEET 04 — FIGURAN DESAIN NETRAL (GENERATOR.HTML) & FULL CAST LINEUP",
        "Desain dasar netral tanpa kunci pose adegan — bebas dioverride via HumanoidRig • Saffron eksklusif Bima!",
        accent=(42, 106, 108),
    )
    draw = ImageDraw.Draw(sheet)

    pedagang = create_pedagang_rempah(scale=3.0, fps=30)
    penumpang = create_penumpang_trem(scale=3.0, fps=30)
    bima = BimaHeroCharacter(scale=3.0, fps=30, lighting_phase="phase1", hero_details=True)
    oren = OrenCharacter(scale=3.0)

    fig_cards = [
        (
            "PEDAGANG REMPAH (0° NETRAL)",
            "Desain netral: siluet gempal, topi jerami, apron goni, non-saffron",
            pedagang.render_pil(angle=0, animation="static"),
        ),
        (
            "PEDAGANG REMPAH (45° NETRAL)",
            "Pose, properti & ekspresi panik diatur bebas di adegan Lokasi 2",
            pedagang.render_pil(angle=45, animation="static"),
        ),
        (
            "PENUMPANG TREM (0° NETRAL)",
            "Desain netral: siluet jangkung, mantel lumut, baret marun, syal teal",
            penumpang.render_pil(angle=0, animation="static"),
        ),
        (
            "PENUMPANG TREM (45° NETRAL)",
            "Baret melayang, koran & ekspresi kaget diatur bebas di Lokasi 5",
            penumpang.render_pil(angle=45, animation="static"),
        ),
    ]
    cw, gap = 310, 16
    for idx, (t_f, d_f, img_f) in enumerate(fig_cards):
        x0 = 32 + idx * (cw + gap)
        y0, x1, y1 = 126, x0 + cw, 748
        draw.rounded_rectangle([x0, y0, x1, y1], radius=14, fill=(252, 249, 242), outline=(186, 174, 152), width=2)
        draw.rounded_rectangle([x0 + 12, y0 + 12, x1 - 12, y0 + 44], radius=8, fill=(42, 62, 68))
        draw.text((x0 + 18, y0 + 19), t_f, font=FONT_TAG, fill=(242, 248, 246))
        paste_fit(sheet, img_f, (x0 + 8, y0 + 50, x1 - 8, y1 - 56))
        draw_wrapped_text(draw, d_f, x0 + 14, y1 - 46, 34, 20, FONT_SMALL, (64, 56, 74), max_lines=2)

    rx0, ry0, rx1, ry1 = 1356, 126, 2068, 748
    draw.rounded_rectangle([rx0, ry0, rx1, ry1], radius=16, fill=(24, 21, 34), outline=(242, 183, 5), width=2)
    draw.text((rx0 + 22, ry0 + 18), "FOCAL ANCHOR & ATURAN PALET", font=FONT_H2, fill=(242, 183, 5))
    swatches = [
        ("#F2B705", (242, 183, 5), "BIMA — Jaket Parka Saffron (EKSKLUSIF!)"),
        ("#C84B31", (200, 75, 49), "BIMA — Syal Terracotta (Secondary Motion)"),
        ("#2B3A55", (43, 58, 85), "BIMA — Celana Kargo Navy (Dark Anchor)"),
        ("#B8860B", (184, 134, 11), "BIMA / KUNCI EMAS — Tarnished Brass"),
        ("#E67E22", (230, 126, 34), "OREN — Belang Oranye + #F5E6CA Krem"),
        ("#D6E4F0", (214, 228, 240), "KUNCI PERAK — Cold Brushed Steel"),
        ("#2A6A6C", (42, 106, 108), "FIGURAN PASAR — Teal & #D6C098 Goni"),
        ("#465F4E", (70, 95, 78), "FIGURAN TREM — Hijau Lumut & #762C3C Baret"),
    ]
    for si, (hx, rgb, desc) in enumerate(swatches):
        sy = ry0 + 66 + si * 66
        draw.rounded_rectangle([rx0 + 22, sy, rx0 + 82, sy + 46], radius=8, fill=rgb, outline=(255, 255, 255), width=2)
        draw.text((rx0 + 98, sy + 4), hx, font=FONT_TAG, fill=(255, 245, 214))
        draw.text((rx0 + 98, sy + 24), desc, font=FONT_SMALL, fill=(208, 204, 222))

    lx0, ly0, lx1, ly1 = 32, 774, 2068, 1252
    draw.rounded_rectangle([lx0, ly0, lx1, ly1], radius=16, fill=(250, 247, 240), outline=(176, 162, 140), width=2)
    draw.text((lx0 + 22, ly0 + 14), "FULL CAST LINEUP NETRAL — UJI SILUET & KONTRAS SKALA (0,2 DETIK)", font=FONT_H2, fill=(32, 26, 44))
    floor_y = ly1 - 44
    draw.line([(lx0 + 40, floor_y), (lx1 - 40, floor_y)], fill=(175, 165, 150), width=2)

    cast_lineup = [
        ("PENUMPANG TREM", penumpang.render_pil(angle=16, animation="static"), (140, ly0 + 52, 540, floor_y + 12)),
        ("PEDAGANG REMPAH", pedagang.render_pil(angle=-14, animation="static"), (560, ly0 + 68, 960, floor_y + 12)),
        ("BIMA (PROTAGONIS)", bima.render_pil(angle=12, animation="static"), (990, ly0 + 86, 1390, floor_y + 12)),
        ("OREN (KUCING)", oren.render_pil(rig=OrenRig(angle=-16)), (1410, ly0 + 240, 1690, floor_y + 12)),
        ("HERO KEYS", GoldenKeyProp(scale=3.0).render_pil(rig=KeyPropRig(yaw_deg=12, roll_deg=-15)), (1710, ly0 + 130, 1890, floor_y - 30)),
        ("", SilverKeyProp(scale=3.0).render_pil(rig=KeyPropRig(yaw_deg=-12, roll_deg=15)), (1870, ly0 + 150, 2030, floor_y - 30)),
    ]
    for lbl, spr, box in cast_lineup:
        paste_fit(sheet, spr, box, valign="bottom")
        if lbl:
            cx = (box[0] + box[2]) // 2
            draw.text((cx - len(lbl) * 4, floor_y + 12), lbl, font=FONT_TAG, fill=(44, 36, 56))

    save_sheet(sheet, "sheet_04_figuran_and_cast_lineup.png")


if __name__ == "__main__":
    render_sheet_01_bima_turnaround()
    render_sheet_02_bima_expressions_and_phases()
    render_sheet_03_oren_and_hero_props()
    render_sheet_04_figuran_and_cast_lineup()
    print("Semua 4 Character Design Sheets (Netral + Rigging Terbuka) selesai dirender!")
