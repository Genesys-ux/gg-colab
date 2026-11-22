"""
Render 12 Screenshot Keyframe 9:16 (720x1280) melintasi seluruh 6 Lokasi, 3 Fase Pencahayaan,
dan 28 Gerakan Kamera — plus 3 Contact Sheet Review agar pengguna dapat menilai komposisi,
3D parallax, cel-shading, lighting & karakter SEBELUM render video final 58 detik.
"""

from __future__ import annotations

import os
import shutil
import sys
import time
from typing import List, Tuple

from PIL import Image, ImageDraw, ImageFont

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

from engine3d.choreography import collect_frame_billboards, evaluate_camera
from engine3d.lighting import evaluate_lighting
from engine3d.math3d import focal_mm_to_vfov_rad, look_at_matrix, perspective_matrix
from engine3d.renderer_wgpu import WgpuCelRenderer
from engine3d.scenes_builder import build_dynamic_world, build_static_world
from engine3d.sprite_cache import SpriteCache

SHOT_DIR = os.path.join(PROJECT_DIR, "previews", "shots_3d")
ARTIFACT_DIR = r"C:\Users\lutfi\.gemini\antigravity\brain\47e864ac-ef32-4f4e-a877-90846cd98a78"
os.makedirs(SHOT_DIR, exist_ok=True)


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
FONT_SUB = get_font(18, bold=False)
FONT_TAG = get_font(17, bold=True)
FONT_SMALL = get_font(15, bold=False)

# 12 Keyframe Hero Screenshots mencakup 6 Lokasi + 3 Fase Lighting + 28 Gerakan Kamera
HERO_SHOTS: List[Tuple[str, float, str, str]] = [
    # Sheet 1: Fase 1 (Low Sun & Blue Shade — Lokasi 1 & 2)
    ("shot_01_cam01_bengkel_dolly.png", 0.22, "[CAM 01] 00:00.2 • Lokasi 1", "Dolly-in menembus celah 2 roda gigi ke Kunci Emas & Bima"),
    ("shot_02_cam03_cangkir_teh.png", 5.15, "[CAM 03] 00:05.2 • Lokasi 1", "Fast crane drop kunci memantul dari cangkir teh porselen"),
    ("shot_03_cam07_tenda_pasar.png", 11.75, "[CAM 07] 00:11.8 • Lokasi 2", "Elastic bounce di kanopi merah Pasar Rempah bertingkat"),
    ("shot_04_cam09_bubuk_kunyit.png", 15.05, "[CAM 09] 00:15.1 • Lokasi 2", "Crash dolly menerobos awan ledakan bubuk kunyit + pedagang"),
    # Sheet 2: Akhir Fase 1 (Lokasi 3 Gang Kafe) & Fase 2 Story Turn (Lokasi 4 Gorong-Gorong)
    ("shot_05_cam12_oren_snap.png", 21.05, "[CAM 12] 00:21.1 • Lokasi 3", 'Whip-pan mengunci "Oren" & cakar lebar di gang kafe teduh'),
    ("shot_06_cam14_cobblestone_skim.png", 23.85, "[CAM 14] 00:23.9 • Lokasi 3", "Inverted low-skim cobblestone basah + Bima meluncur lutut"),
    ("shot_07_cam16_gorong_reveal.png", 28.10, "[CAM 16] 00:28.1 • Lokasi 4", "STORY TURN! Indigo-Emerald + tungku oranye & roda gigi raksasa"),
    ("shot_08_cam18_poros_klak.png", 32.35, "[CAM 18] 00:32.4 • Lokasi 4", "KLAK! Crash-zoom kunci menancap poros + percikan biru-zamrud"),
    # Sheet 3: Fase 3 Klimaks (Lokasi 5 Stasiun Trem Crimson) & Finale (Lokasi 6 Menara Jam Twilight & Loop)
    ("shot_09_cam21_trem_parallax.png", 41.35, "[CAM 21] 00:41.4 • Lokasi 5", "CLIMAX! Lateral tracking trem merah mundur + parallax pilar besi"),
    ("shot_10_cam24_lompat_matahari.png", 47.60, "[CAM 24] 00:47.6 • Lokasi 5", "Slow-mo 20% orbit 90° lompatan Bima di depan matahari crimson"),
    ("shot_11_cam26_twilight_shockwave.png", 53.15, "[CAM 26] 00:53.2 • Lokasi 6", "Shockwave pull-back Frozen Violet-Gold Twilight + cyan rim!"),
    ("shot_12_cam27_twist_kunci_perak.png", 55.85, "[CAM 27] 00:55.9 • Lokasi 6", "Twist komedi! Snap-zoom saku robek Bima & Kunci Perak jatuh"),
]


def make_contact_sheet(
    title: str,
    subtitle: str,
    accent: Tuple[int, int, int],
    items: List[Tuple[Image.Image, str, str]],
    out_name: str,
) -> None:
    cw, ch = 500, 888  # 9:16 crisp scaled preview
    gap = 24
    pad_x = 34
    w = pad_x * 2 + cw * 4 + gap * 3
    h = 110 + ch + 104
    sheet = Image.new("RGB", (w, h), (18, 16, 26))
    draw = ImageDraw.Draw(sheet)

    draw.rectangle([0, 0, w, 92], fill=(14, 12, 22))
    draw.rectangle([0, 88, w, 92], fill=accent)
    draw.text((34, 14), title, font=FONT_H1, fill=(248, 245, 255))
    draw.text((36, 54), subtitle, font=FONT_SUB, fill=(184, 178, 206))

    for idx, (img, badge, desc) in enumerate(items):
        x0 = pad_x + idx * (cw + gap)
        y0 = 112
        resized = img.convert("RGB").resize((cw, ch), Image.Resampling.LANCZOS)
        sheet.paste(resized, (x0, y0))
        draw.rectangle([x0, y0, x0 + cw, y0 + ch], outline=accent, width=3)
        # Label bawah bersih
        draw.rectangle([x0, y0 + ch + 8, x0 + cw, y0 + ch + 82], fill=(28, 24, 40))
        draw.text((x0 + 12, y0 + ch + 14), badge, font=FONT_TAG, fill=accent)
        # Wrap desc max 2 lines
        words = desc.split(" ")
        lines, cur = [], ""
        for wd in words:
            if len((cur + " " + wd).strip()) > 52:
                lines.append(cur.strip())
                cur = wd
            else:
                cur = (cur + " " + wd).strip()
        if cur:
            lines.append(cur)
        for li, ln in enumerate(lines[:2]):
            draw.text((x0 + 12, y0 + ch + 39 + li * 20), ln, font=FONT_SMALL, fill=(230, 226, 240))

    p_local = os.path.join(SHOT_DIR, out_name)
    sheet.save(p_local, quality=94)
    if os.path.isdir(ARTIFACT_DIR):
        shutil.copy2(p_local, os.path.join(ARTIFACT_DIR, out_name))
    print(f"Saved contact sheet: {p_local} ({w}x{h})")


def main() -> None:
    t_start = time.perf_counter()
    width, height = 720, 1280
    renderer = WgpuCelRenderer(width=width, height=height)
    print(f"WGPU 3D Renderer aktif: {renderer.adapter_name} ({width}x{height})")

    static_verts = build_static_world()
    print(f"Dunia 3D statis (6 Lokasi): {static_verts.shape[0]:,} vertex ({static_verts.shape[0] // 3:,} segitiga)")
    renderer.upload_static_world(static_verts)

    sprites = SpriteCache(char_scale=2.2, prop_scale=2.4)
    rendered_items: List[Tuple[Image.Image, str, str]] = []

    for fname, t_sec, badge, desc in HERO_SHOTS:
        t0 = time.perf_counter()
        lighting = evaluate_lighting(t_sec)
        dyn_verts, tram_z = build_dynamic_world(t_sec)
        cam = evaluate_camera(t_sec, tram_z)
        bbs = collect_frame_billboards(t_sec, cam, lighting, tram_z, sprites, quantize_deg=4.0)

        vfov = focal_mm_to_vfov_rad(cam.focal_mm)
        view_m = look_at_matrix(cam.cam_pos, cam.cam_target, roll_deg=cam.roll_deg)
        proj_m = perspective_matrix(vfov, width / float(height), 0.08, 220.0)

        rgba = renderer.render_frame(
            cam_pos=cam.cam_pos,
            cam_target=cam.cam_target,
            view_mat=view_m,
            proj_mat=proj_m,
            lighting=lighting,
            dynamic_vertices=dyn_verts,
            billboards=bbs,
            motion_blur_uv=cam.motion_blur_uv,
            outline_strength=cam.outline_strength,
            time_sec=t_sec,
            shadow_center=cam.shadow_center,
            shadow_radius=cam.shadow_radius,
        )
        img = Image.fromarray(rgba, mode="RGBA")
        out_p = os.path.join(SHOT_DIR, fname)
        img.convert("RGB").save(out_p, quality=94)
        rendered_items.append((img, badge, desc))
        print(f"  [OK] {fname} (t={t_sec:05.2f}s, {cam.cam_id}, {lighting.phase_name}, {len(bbs)} sprites) in {(time.perf_counter()-t0)*1000:.0f}ms")

    make_contact_sheet(
        "PREVIEW 3D SHEET 01 — FASE 1: LOW SUN & BLUE SHADE (LOKASI 1 BENGKEL & LOKASI 2 PASAR)",
        "Wide-angle 18-22mm • Heavy 3D parallax • Cel-shaded + Procedural PBR • Warm Golden Haze",
        (242, 183, 5),
        rendered_items[0:4],
        "preview_3d_01_fase1.png",
    )
    make_contact_sheet(
        "PREVIEW 3D SHEET 02 — LOKASI 3 GANG KAFE (OREN) & FASE 2 STORY TURN (LOKASI 4 GORONG-GORONG)",
        "Cahaya matahari terputus -> Deep Indigo Shade + Emerald Steam Haze + Hard Furnace Orange Rim",
        (46, 224, 166),
        rendered_items[4:8],
        "preview_3d_02_story_turn.png",
    )
    make_contact_sheet(
        "PREVIEW 3D SHEET 03 — FASE 3 KLIMAKS (STASIUN TREM CRIMSON) & FINALE (MENARA JAM TWILIGHT + TWIST)",
        "Ultra-Low Crimson Sun -> Radial Shockwave -> Frozen Violet-Gold Twilight + Crisp Cyan Rim & Kunci Perak",
        (102, 240, 255),
        rendered_items[8:12],
        "preview_3d_03_climax_finale.png",
    )
    print(f"Selesai merender 12 screenshot 3D + 3 contact sheet dalam {time.perf_counter() - t_start:.1f} detik!")


if __name__ == "__main__":
    main()
