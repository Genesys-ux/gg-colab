"""
Entry Point Utama Blender Python (bpy) + EEVEE Next — "Jangan Sampai Kunci Ini Jatuh!"
Jalankan di Google Colab GPU atau Blender 4.2+ lokal:

  1. Simpan file .blend siap edit + render 12 preview screenshot:
     blender -b -P blender_pipeline/render_eevee.py -- --mode previews --width 720 --height 1280 --samples 32

  2. Render Video Final 58 detik (1.740 frame) + muxing audio narasi ElevenLabs otomatis (dengan auto-resume!):
     blender -b -P blender_pipeline/render_eevee.py -- --mode video --width 1080 --height 1920 --samples 32 --resume

  3. Bangun & simpan hanya file .blend:
     blender -b -P blender_pipeline/render_eevee.py -- --mode save-blend
"""

from __future__ import annotations

import argparse
import math
import os
import shutil
import subprocess
import sys
import time
from typing import List, Tuple

import bpy  # type: ignore

# Pastikan root project ada di sys.path saat dipanggil lewat `blender -b -P blender_pipeline/render_eevee.py`
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_THIS_DIR)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from blender_pipeline.animation_director import animate_entire_short
from blender_pipeline.assets_loader import download_polyhaven_pbr_pack
from blender_pipeline.camera_28_moves import build_and_animate_virtual_camera, clamp
from blender_pipeline.characters_3d import (
    build_bima_3d,
    build_golden_key_3d,
    build_oren_3d,
    build_pedagang_rempah_3d,
    build_penumpang_trem_3d,
    build_silver_key_3d,
)
from blender_pipeline.config import (
    AUDIO_MASTER_MP3,
    AUDIO_MASTER_WAV,
    DEFAULT_HEIGHT,
    DEFAULT_WIDTH,
    FPS,
    HERO_PREVIEW_SHOTS,
    OUTPUT_DIR,
    PREVIEW_DIR,
    TOTAL_FRAMES,
    sec_to_frame,
)
from blender_pipeline.lighting_3_phases import setup_world_and_lights
from blender_pipeline.materials_cel_pbr import create_material_library, hex_to_linear_rgba
from blender_pipeline.scenes_6_locations import build_all_6_locations


def reset_scene() -> None:
    bpy.ops.wm.read_factory_settings(use_empty=True)


def configure_eevee_next(width: int, height: int, samples: int = 32) -> None:
    """Konfigurasi render engine EEVEE Next 4.2+ (aman lintas versi 3.6/4.2/4.3/5.0!)."""
    scene = bpy.context.scene
    avail_engines = [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items]
    if "BLENDER_EEVEE_NEXT" in avail_engines:
        scene.render.engine = "BLENDER_EEVEE_NEXT"
    else:
        scene.render.engine = "BLENDER_EEVEE"

    scene.render.resolution_x = int(width)
    scene.render.resolution_y = int(height)
    scene.render.resolution_percentage = 100
    scene.render.fps = FPS
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"

    # Motion blur shutter alami untuk whip-pan, 360° barrel roll & vertical plunge!
    scene.render.use_motion_blur = True
    scene.render.motion_blur_shutter = 0.35

    eevee = scene.eevee
    if hasattr(eevee, "taa_render_samples"):
        eevee.taa_render_samples = int(samples)
    if hasattr(eevee, "use_shadows"):
        eevee.use_shadows = True
    if hasattr(eevee, "use_volumetric_shadows"):
        eevee.use_volumetric_shadows = True
    if hasattr(eevee, "volumetric_tile_size"):
        try:
            eevee.volumetric_tile_size = "4"
        except Exception:
            pass
    if hasattr(eevee, "use_raytracing"):
        eevee.use_raytracing = True
    if hasattr(eevee, "use_gtao"):
        eevee.use_gtao = True

    # Color management filmic kartun kontras kaya (AgX Punchy / Filmic fallback)
    vs = scene.view_settings
    for vt in ("AgX", "Filmic", "Standard"):
        try:
            vs.view_transform = vt
            break
        except Exception:
            continue
    for lk in ("AgX - Punchy", "AgX - Medium High Contrast", "Medium High Contrast", "None"):
        try:
            vs.look = lk
            break
        except Exception:
            continue
    vs.exposure = 0.15


def setup_compositor() -> None:
    """
    Kompositor Blender 4.2+:
      1. Glare Fog Glow (pengganti resmi EEVEE Bloom di Blender 4.2!)
      2. Radial Cyan-Gold Shockwave Ring ([CAM 18] & [CAM 26])
      3. Hidden 2-Frame Black Wipe Cut di jeruji selokan ([CAM 15], t=26.0s) + seamless loop fade ([CAM 28])
    """
    scene = bpy.context.scene
    scene.use_nodes = True
    tree = scene.node_tree
    nodes = tree.nodes
    links = tree.links
    nodes.clear()

    rl = nodes.new("CompositorNodeRLayers")
    rl.location = (-600, 0)

    # 1. Fog Glow Bloom
    glare = nodes.new("CompositorNodeGlare")
    glare.glare_type = "FOG_GLOW"
    glare.quality = "HIGH"
    glare.threshold = 0.92
    glare.size = 7
    if hasattr(glare, "mix"):
        glare.mix = -0.35
    glare.location = (-320, 0)
    links.new(rl.outputs["Image"], glare.inputs["Image"])

    # 2. Radial Cyan-Gold Shockwave Ring (Outer Ellipse - Inner Ellipse -> Blur -> Add!)
    outer_e = nodes.new("CompositorNodeEllipseMask")
    outer_e.location = (-600, -340)
    outer_e.x = 0.5
    outer_e.y = 0.54

    inner_e = nodes.new("CompositorNodeEllipseMask")
    inner_e.location = (-600, -560)
    inner_e.x = 0.5
    inner_e.y = 0.54

    ring_sub = nodes.new("CompositorNodeMath")
    ring_sub.operation = "SUBTRACT"
    ring_sub.use_clamp = True
    ring_sub.location = (-360, -420)
    links.new(outer_e.outputs["Mask"], ring_sub.inputs[0])
    links.new(inner_e.outputs["Mask"], ring_sub.inputs[1])

    ring_blur = nodes.new("CompositorNodeBlur")
    ring_blur.filter_type = "FAST_GAUSS"
    ring_blur.size_x = 28
    ring_blur.size_y = 28
    ring_blur.location = (-160, -420)
    links.new(ring_sub.outputs["Value"], ring_blur.inputs["Image"])

    ring_scale = nodes.new("CompositorNodeMath")
    ring_scale.operation = "MULTIPLY"
    ring_scale.inputs[1].default_value = 0.0
    ring_scale.location = (40, -420)
    links.new(ring_blur.outputs["Image"], ring_scale.inputs[0])

    mix_sw = nodes.new("CompositorNodeMixRGB")
    mix_sw.blend_type = "ADD"
    mix_sw.inputs[2].default_value = hex_to_linear_rgba("#52F6FF")
    mix_sw.location = (220, 0)
    links.new(ring_scale.outputs["Value"], mix_sw.inputs[0])
    links.new(glare.outputs["Image"], mix_sw.inputs[1])

    # Keyframe Shockwave di [CAM 18] (31.9..33.3s) & [CAM 26] (51.8..54.5s)!
    def kf_sw(t_s: float, rad: float, alpha: float) -> None:
        fr = sec_to_frame(t_s)
        # Kompensasi rasio 9:16 agar cincin tetap bulat proporsional
        outer_e.width = max(0.01, rad)
        outer_e.height = max(0.01, rad * (9.0 / 16.0))
        inner_e.width = max(0.005, rad * 0.82)
        inner_e.height = max(0.005, rad * 0.82 * (9.0 / 16.0))
        outer_e.keyframe_insert(data_path="width", frame=fr)
        outer_e.keyframe_insert(data_path="height", frame=fr)
        inner_e.keyframe_insert(data_path="width", frame=fr)
        inner_e.keyframe_insert(data_path="height", frame=fr)
        ring_scale.inputs[1].default_value = alpha
        ring_scale.inputs[1].keyframe_insert(data_path="default_value", frame=fr)

    kf_sw(0.0, 0.05, 0.0)
    kf_sw(31.8, 0.08, 0.0)
    kf_sw(32.3, 0.58, 0.55)
    kf_sw(33.4, 1.35, 0.0)
    kf_sw(51.7, 0.08, 0.0)
    kf_sw(52.4, 0.52, 0.95)
    kf_sw(53.15, 0.96, 0.95)
    kf_sw(54.5, 1.65, 0.0)

    # 3. Hidden 2-Frame Black Wipe Cut di jeruji selokan ([CAM 15], t=25.92..26.08s) + loop dip ([CAM 28])
    mix_wipe = nodes.new("CompositorNodeMixRGB")
    mix_wipe.blend_type = "MIX"
    mix_wipe.inputs[2].default_value = (0.0, 0.0, 0.0, 1.0)
    mix_wipe.location = (460, 0)
    links.new(mix_sw.outputs["Image"], mix_wipe.inputs[1])

    def kf_wipe(t_s: float, fac: float) -> None:
        fr = sec_to_frame(t_s)
        mix_wipe.inputs[0].default_value = clamp(fac)
        mix_wipe.inputs[0].keyframe_insert(data_path="default_value", frame=fr)

    kf_wipe(0.0, 0.0)
    kf_wipe(25.85, 0.0)
    kf_wipe(25.97, 1.0)   # 2-frame pure black wipe peak!
    kf_wipe(26.04, 1.0)
    kf_wipe(26.15, 0.0)
    kf_wipe(57.45, 0.0)
    kf_wipe(58.0, 0.48)   # transisi gelap halus menyambung ke celah roda gigi [CAM 01]

    comp = nodes.new("CompositorNodeComposite")
    comp.location = (720, 0)
    links.new(mix_wipe.outputs["Image"], comp.inputs["Image"])


def build_complete_project(width: int, height: int, samples: int, download_pbr: bool = False) -> str:
    """Bangun seluruh dunia 3D, karakter rig terbuka, 28 kamera, lighting 3 fase, & kompositor."""
    t0 = time.perf_counter()
    if download_pbr:
        download_polyhaven_pbr_pack(resolution="1k")

    reset_scene()
    configure_eevee_next(width, height, samples=samples)

    print("[Blender] 1/5 Membangun pustaka shader Cel-Shaded + PBR Realistis...")
    mats = create_material_library()

    print("[Blender] 2/5 Membangun 6 Lokasi 3D Berdetail Halus (Bevel/Lathe/Cloth/Cogwheels)...")
    handles = build_all_6_locations(mats)

    print("[Blender] 3/5 Membangun Karakter 3D Rig Terbuka (Bima, Oren, Hero Props, Figuran)...")
    bima_rig = build_bima_3d(mats)
    oren_rig = build_oren_3d(mats)
    golden_key = build_golden_key_3d(mats)
    silver_key = build_silver_key_3d(mats)
    merchants = [
        build_pedagang_rempah_3d("Pedagang_01_Rig", mats),
        build_pedagang_rempah_3d("Pedagang_02_Rig", mats),
    ]
    passengers = [
        build_penumpang_trem_3d(f"Penumpang_0{i+1}_Rig", mats)
        for i in range(4)
    ]

    print("[Blender] 4/5 Mengatur Evolusi Pencahayaan 3 Fase + Volumetric Haze + Kompositor...")
    setup_world_and_lights(mats)
    setup_compositor()

    print("[Blender] 5/5 Menganimasikan 28 Gerakan Kamera Continuous One-Take & Aktor (1.740 Frame)...")
    build_and_animate_virtual_camera()
    animate_entire_short(bima_rig, oren_rig, golden_key, silver_key, merchants, passengers, handles)

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    blend_path = os.path.join(OUTPUT_DIR, "jangan_sampai_kunci_ini_jatuh.blend")
    bpy.ops.wm.save_as_mainfile(filepath=blend_path)
    print(f"[Blender] Scene 3D selesai dibangun & disimpan ke: {blend_path} ({time.perf_counter() - t0:.1f}s)")
    return blend_path


def _try_build_contact_sheets(shot_paths: List[Tuple[str, str, str]]) -> None:
    """Rakit 3 contact sheet 4-panel jika Pillow (PIL) tersedia di Python Blender/sistem."""
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        print("[Preview] Pillow tidak terpasang di embedded Python Blender (lewatkan contact sheet; bisa dibuat di sel Colab).")
        return

    def make_sheet(title: str, accent: Tuple[int, int, int], items: List[Tuple[str, str, str]], out_name: str):
        cw, ch, gap, pad = 480, 854, 22, 30
        w = pad * 2 + cw * 4 + gap * 3
        h = 96 + ch + 86
        sheet = Image.new("RGB", (w, h), (18, 16, 26))
        draw = ImageDraw.Draw(sheet)
        draw.rectangle([0, 0, w, 78], fill=(14, 12, 22))
        draw.rectangle([0, 74, w, 78], fill=accent)
        font_b = ImageFont.load_default()
        draw.text((28, 24), title, font=font_b, fill=(248, 245, 255))
        for idx, (fp, badge, desc) in enumerate(items):
            if not os.path.exists(fp):
                continue
            x0, y0 = pad + idx * (cw + gap), 94
            im = Image.open(fp).convert("RGB").resize((cw, ch), Image.Resampling.LANCZOS)
            sheet.paste(im, (x0, y0))
            draw.rectangle([x0, y0, x0 + cw, y0 + ch], outline=accent, width=3)
            draw.rectangle([x0, y0 + ch + 6, x0 + cw, y0 + ch + 70], fill=(28, 24, 40))
            draw.text((x0 + 10, y0 + ch + 14), badge, font=font_b, fill=accent)
            draw.text((x0 + 10, y0 + ch + 36), desc[:62], font=font_b, fill=(230, 226, 240))
        out_p = os.path.join(PREVIEW_DIR, out_name)
        sheet.save(out_p, quality=94)
        print(f"[Preview] Contact sheet tersimpan: {out_p}")

    make_sheet("EEVEE NEXT SHEET 01 — FASE 1 LOW SUN (LOKASI 1 BENGKEL & LOKASI 2 PASAR)", (242, 183, 5), shot_paths[0:4], "eevee_sheet_01_fase1.png")
    make_sheet("EEVEE NEXT SHEET 02 — GANG KAFE OREN & FASE 2 STORY TURN GORONG-GORONG", (46, 224, 166), shot_paths[4:8], "eevee_sheet_02_story_turn.png")
    make_sheet("EEVEE NEXT SHEET 03 — FASE 3 KLIMAKS STASIUN TREM & FINALE MENARA JAM TWILIGHT", (102, 240, 255), shot_paths[8:12], "eevee_sheet_03_climax_finale.png")


def render_previews() -> None:
    os.makedirs(PREVIEW_DIR, exist_ok=True)
    scene = bpy.context.scene
    shot_records: List[Tuple[str, str, str]] = []
    t0 = time.perf_counter()
    for fname, t_sec, badge, desc in HERO_PREVIEW_SHOTS:
        fr = sec_to_frame(t_sec)
        scene.frame_set(fr)
        out_fp = os.path.join(PREVIEW_DIR, fname)
        scene.render.filepath = out_fp
        ts = time.perf_counter()
        bpy.ops.render.render(write_still=True)
        print(f"  [EEVEE Preview] {fname} (frame {fr:04d}, t={t_sec:05.2f}s) selesai dalam {time.perf_counter() - ts:.2f}s")
        shot_records.append((out_fp, badge, desc))
    _try_build_contact_sheets(shot_records)
    print(f"[EEVEE Preview] Semua 12 screenshot preview selesai dalam {time.perf_counter() - t0:.1f}s -> {PREVIEW_DIR}")


def render_video_sequence(start_frame: int, end_frame: int, resume: bool, out_mp4: str) -> None:
    frames_dir = os.path.join(OUTPUT_DIR, "frames")
    os.makedirs(frames_dir, exist_ok=True)
    scene = bpy.context.scene

    t0 = time.perf_counter()
    total_to_do = end_frame - start_frame + 1
    for idx, fr in enumerate(range(start_frame, end_frame + 1), start=1):
        fp = os.path.join(frames_dir, f"frame_{fr:04d}.png")
        if resume and os.path.exists(fp) and os.path.getsize(fp) > 4096:
            continue
        scene.frame_set(fr)
        scene.render.filepath = fp
        bpy.ops.render.render(write_still=True)
        if idx == 1 or idx % 15 == 0 or fr == end_frame:
            el = time.perf_counter() - t0
            print(f"[EEVEE Render] Frame {fr:04d}/{end_frame:04d} ({idx*100.0/total_to_do:5.1f}%) | elapsed {el:.1f}s", flush=True)

    # Muxing otomatis dengan FFmpeg + master voiceover ElevenLabs bila seluruh 1..1740 frame telah lengkap
    if start_frame == 1 and end_frame >= TOTAL_FRAMES:
        ffmpeg = shutil.which("ffmpeg")
        if not ffmpeg:
            print("[FFmpeg] Tidak ditemukan di PATH; frame PNG siap di:", frames_dir)
            return
        audio_in = AUDIO_MASTER_WAV if os.path.exists(AUDIO_MASTER_WAV) else (AUDIO_MASTER_MP3 if os.path.exists(AUDIO_MASTER_MP3) else None)
        cmd = [
            ffmpeg, "-y", "-v", "warning",
            "-framerate", str(FPS),
            "-i", os.path.join(frames_dir, "frame_%04d.png"),
        ]
        if audio_in:
            cmd += ["-i", audio_in]
        cmd += ["-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "17", "-preset", "medium"]
        if audio_in:
            cmd += ["-c:a", "aac", "-b:a", "192k", "-shortest"]
        cmd.append(out_mp4)
        print(f"[FFmpeg] Menggabungkan 1.740 frame + audio narasi -> {out_mp4}")
        subprocess.run(cmd, check=True)
        print(f"[DONE] Video final EEVEE Next selesai: {out_mp4}")


def _parse_args() -> argparse.Namespace:
    argv = sys.argv
    if "--" in argv:
        argv = argv[argv.index("--") + 1 :]
    else:
        argv = []
    p = argparse.ArgumentParser(description='Blender EEVEE Next Pipeline — "Jangan Sampai Kunci Ini Jatuh!"')
    p.add_argument("--mode", choices=("save-blend", "previews", "video"), default="previews")
    p.add_argument("--width", type=int, default=DEFAULT_WIDTH)
    p.add_argument("--height", type=int, default=DEFAULT_HEIGHT)
    p.add_argument("--samples", type=int, default=32)
    p.add_argument("--download-pbr", action="store_true")
    p.add_argument("--blend-in", default="", help="Muat file .blend yang sudah ada tanpa membangun ulang scene")
    p.add_argument("--start-frame", type=int, default=1)
    p.add_argument("--end-frame", type=int, default=TOTAL_FRAMES)
    p.add_argument("--resume", action="store_true", help="Lewati frame PNG yang sudah selesai dirender")
    p.add_argument("--out-mp4", default=os.path.join(OUTPUT_DIR, "jangan_sampai_kunci_ini_jatuh_eevee.mp4"))
    return p.parse_args(argv)


def main() -> None:
    args = _parse_args()
    if args.blend_in and os.path.exists(args.blend_in):
        bpy.ops.wm.open_mainfile(filepath=args.blend_in)
        configure_eevee_next(args.width, args.height, samples=args.samples)
    else:
        build_complete_project(args.width, args.height, args.samples, download_pbr=args.download_pbr)

    if args.mode == "previews":
        render_previews()
    elif args.mode == "video":
        render_video_sequence(args.start_frame, args.end_frame, args.resume, args.out_mp4)


if __name__ == "__main__":
    main()
