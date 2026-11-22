"""
Entry Point Utama Blender Python (bpy) + EEVEE Next — "Jangan Sampai Kunci Ini Jatuh!" (v2 — Colab Pro Ready!)

Pembaruan Penting v2 (sesuai feedback evaluasi visual):
  1. DESAIN KARAKTER 100% DIPERTAHANKAN PERSIS PREVIEW PERTAMA via `ExactCharacterCastManager`
     (Bima, Oren, Pedagang Rempah, Penumpang Trem, Kunci Emas & Kunci Perak tetap dari rig terbuka `characters/`!).
  2. LANGIT CERAH & WARNA VIBRANT PERSIS PREVIEW PERTAMA (menghapus infinite World VolumeScatter yang
     membuat langit hitam pekat, menggantinya dengan 3-stop World Sky cerah + Compositor Mist Pass Haze!).
  3. PROPERTI, BANGUNAN & TANAMAN BERBASIS REFERENSI NYATA + 15 MODEL 3D CC0 ASLI POLY HAVEN + PBR 2K!
"""

from __future__ import annotations

import argparse
import importlib
import os
import shutil
import site
import subprocess
import sys
import time
from typing import List, Optional, Tuple

import bpy  # type: ignore

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_THIS_DIR)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)


def ensure_sprite_dependencies() -> None:
    """Auto-install pillow & resvg-py ke Python bawaan Blender bila belum terpasang (self-healing di Colab!)."""
    missing = []
    for mod_name, pkg_name in (("PIL", "pillow"), ("resvg_py", "resvg-py")):
        try:
            __import__(mod_name)
        except ImportError:
            missing.append(pkg_name)
    if not missing:
        return
    py_exe = sys.executable
    print(f"[Auto-Install] Memasang {missing} ke Python Blender ({py_exe})...", flush=True)
    res = subprocess.run([py_exe, "-m", "pip", "install", "-q", *missing], check=False)
    if res.returncode != 0:
        subprocess.run([py_exe, "-m", "ensurepip", "--default-pip"], check=False)
        subprocess.run([py_exe, "-m", "pip", "install", "-q", *missing], check=True)
    # Pastikan direktori site-packages & import cache ter-refresh di proses Blender saat ini
    for sp in site.getsitepackages():
        if sp not in sys.path and os.path.isdir(sp):
            sys.path.append(sp)
    importlib.invalidate_caches()
    print("[Auto-Install] pillow & resvg-py siap digunakan!", flush=True)

from blender_pipeline.animation_director import animate_dynamic_world
from blender_pipeline.assets_loader import (
    download_polyhaven_3d_models,
    download_polyhaven_pbr_pack,
    reset_model_cache,
)
from blender_pipeline.camera_28_moves import build_and_animate_virtual_camera, clamp
from blender_pipeline.characters_25d_exact import ExactCharacterCastManager
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
    reset_model_cache()
    bpy.ops.wm.read_factory_settings(use_empty=True)


def configure_eevee_next(width: int, height: int, samples: int = 64) -> None:
    """Konfigurasi Blender 4.2+ EEVEE Next dengan warna kartun cerah, Mist Pass Haze & Motion Blur."""
    scene = bpy.context.scene
    avail_engines = [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items]
    scene.render.engine = "BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in avail_engines else "BLENDER_EEVEE"

    scene.render.resolution_x = int(width)
    scene.render.resolution_y = int(height)
    scene.render.resolution_percentage = 100
    scene.render.fps = FPS
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"

    # Aktifkan Mist Pass untuk atmospheric haze cerah di Compositor (tanpa menggelapkan langit!)
    if hasattr(scene, "view_layers") and len(scene.view_layers) > 0:
        vl = scene.view_layers[0]
        if hasattr(vl, "use_pass_mist"):
            vl.use_pass_mist = True

    scene.render.use_motion_blur = True
    scene.render.motion_blur_shutter = 0.28

    eevee = scene.eevee
    if hasattr(eevee, "taa_render_samples"):
        eevee.taa_render_samples = int(samples)
    if hasattr(eevee, "use_shadows"):
        eevee.use_shadows = True
    if hasattr(eevee, "use_raytracing"):
        eevee.use_raytracing = True
    if hasattr(eevee, "use_gtao"):
        eevee.use_gtao = True

    # Color management CERAH & JENUH (Filmic / Standard agar warna langit & karakter tidak kusam gelap!)
    vs = scene.view_settings
    for vt in ("Filmic", "Standard", "AgX"):
        try:
            vs.view_transform = vt
            break
        except Exception:
            continue
    for lk in ("Medium High Contrast", "High Contrast", "None"):
        try:
            vs.look = lk
            break
        except Exception:
            continue
    vs.exposure = 0.22


def setup_compositor() -> None:
    """
    Kompositor Blender 4.2+:
      1. Atmospheric Haze via Mist Pass (Golden -> Emerald -> Crimson -> Twilight) — LANGIT TETAP CERAH!
      2. Glare Fog Glow (Bloom halus)
      3. Radial Cyan-Gold Shockwave Ring ([CAM 18] & [CAM 26])
      4. Hidden 2-Frame Black Wipe Cut ([CAM 15], t=26.0s) + seamless loop fade ([CAM 28])
    """
    scene = bpy.context.scene
    scene.use_nodes = True
    tree = scene.node_tree
    nodes = tree.nodes
    links = tree.links
    nodes.clear()

    rl = nodes.new("CompositorNodeRLayers")
    rl.location = (-860, 0)

    # 1. Atmospheric Mist Haze (hanya memengaruhi kedalaman objek 3D; tidak mematikan langit!)
    haze_mix = nodes.new("CompositorNodeMixRGB")
    haze_mix.blend_type = "MIX"
    haze_mix.inputs[2].default_value = hex_to_linear_rgba("#FFD282")
    haze_mix.location = (-560, 40)

    mist_scale = nodes.new("CompositorNodeMath")
    mist_scale.operation = "MULTIPLY"
    mist_scale.use_clamp = True
    mist_scale.inputs[1].default_value = 0.24
    mist_scale.location = (-700, -180)
    if rl.outputs.get("Mist") is not None:
        links.new(rl.outputs["Mist"], mist_scale.inputs[0])
        links.new(mist_scale.outputs["Value"], haze_mix.inputs[0])
    else:
        haze_mix.inputs[0].default_value = 0.0
    links.new(rl.outputs["Image"], haze_mix.inputs[1])

    def kf_haze(t_s: float, hex_c: str, strength: float) -> None:
        fr = sec_to_frame(t_s)
        haze_mix.inputs[2].default_value = hex_to_linear_rgba(hex_c)
        haze_mix.inputs[2].keyframe_insert(data_path="default_value", frame=fr)
        mist_scale.inputs[1].default_value = strength
        mist_scale.inputs[1].keyframe_insert(data_path="default_value", frame=fr)

    kf_haze(0.0, "#FFD282", 0.16)
    kf_haze(25.8, "#F2BE70", 0.20)
    kf_haze(26.1, "#18A682", 0.42)
    kf_haze(37.9, "#18A682", 0.40)
    kf_haze(38.6, "#FF6E38", 0.22)
    kf_haze(51.7, "#FF6E38", 0.20)
    kf_haze(52.6, "#7A4AC4", 0.16)
    kf_haze(58.0, "#7A4AC4", 0.16)

    # 2. Fog Glow Bloom
    glare = nodes.new("CompositorNodeGlare")
    glare.glare_type = "FOG_GLOW"
    glare.quality = "HIGH"
    glare.threshold = 1.05
    glare.size = 7
    if hasattr(glare, "mix"):
        glare.mix = -0.40
    glare.location = (-300, 40)
    links.new(haze_mix.outputs["Image"], glare.inputs["Image"])

    # 3. Radial Cyan-Gold Shockwave Ring ([CAM 18] & [CAM 26])
    outer_e = nodes.new("CompositorNodeEllipseMask")
    outer_e.location = (-600, -360)
    outer_e.x = 0.5
    outer_e.y = 0.54

    inner_e = nodes.new("CompositorNodeEllipseMask")
    inner_e.location = (-600, -560)
    inner_e.x = 0.5
    inner_e.y = 0.54

    ring_sub = nodes.new("CompositorNodeMath")
    ring_sub.operation = "SUBTRACT"
    ring_sub.use_clamp = True
    ring_sub.location = (-360, -440)
    links.new(outer_e.outputs["Mask"], ring_sub.inputs[0])
    links.new(inner_e.outputs["Mask"], ring_sub.inputs[1])

    ring_blur = nodes.new("CompositorNodeBlur")
    ring_blur.filter_type = "FAST_GAUSS"
    ring_blur.size_x = 34
    ring_blur.size_y = 34
    ring_blur.location = (-160, -440)
    links.new(ring_sub.outputs["Value"], ring_blur.inputs["Image"])

    ring_scale = nodes.new("CompositorNodeMath")
    ring_scale.operation = "MULTIPLY"
    ring_scale.inputs[1].default_value = 0.0
    ring_scale.location = (40, -440)
    links.new(ring_blur.outputs["Image"], ring_scale.inputs[0])

    mix_sw = nodes.new("CompositorNodeMixRGB")
    mix_sw.blend_type = "ADD"
    mix_sw.inputs[2].default_value = hex_to_linear_rgba("#90FAFF")
    mix_sw.location = (220, 40)
    links.new(ring_scale.outputs["Value"], mix_sw.inputs[0])
    links.new(glare.outputs["Image"], mix_sw.inputs[1])

    def kf_sw(t_s: float, rad: float, alpha: float) -> None:
        fr = sec_to_frame(t_s)
        outer_e.width = max(0.01, rad)
        outer_e.height = max(0.01, rad * (9.0 / 16.0))
        inner_e.width = max(0.005, rad * 0.78)
        inner_e.height = max(0.005, rad * 0.78 * (9.0 / 16.0))
        outer_e.keyframe_insert(data_path="width", frame=fr)
        outer_e.keyframe_insert(data_path="height", frame=fr)
        inner_e.keyframe_insert(data_path="width", frame=fr)
        inner_e.keyframe_insert(data_path="height", frame=fr)
        ring_scale.inputs[1].default_value = alpha
        ring_scale.inputs[1].keyframe_insert(data_path="default_value", frame=fr)

    kf_sw(0.0, 0.05, 0.0)
    kf_sw(31.8, 0.08, 0.0)
    kf_sw(32.3, 0.60, 0.45)
    kf_sw(33.4, 1.35, 0.0)
    kf_sw(51.7, 0.08, 0.0)
    kf_sw(52.4, 0.56, 0.92)
    kf_sw(53.15, 1.02, 0.92)
    kf_sw(54.5, 1.65, 0.0)

    # 4. Hidden 2-Frame Black Wipe Cut ([CAM 15], t=26.0s) + seamless loop dip ([CAM 28])
    mix_wipe = nodes.new("CompositorNodeMixRGB")
    mix_wipe.blend_type = "MIX"
    mix_wipe.inputs[2].default_value = (0.0, 0.0, 0.0, 1.0)
    mix_wipe.location = (460, 40)
    links.new(mix_sw.outputs["Image"], mix_wipe.inputs[1])

    def kf_wipe(t_s: float, fac: float) -> None:
        fr = sec_to_frame(t_s)
        mix_wipe.inputs[0].default_value = clamp(fac)
        mix_wipe.inputs[0].keyframe_insert(data_path="default_value", frame=fr)

    kf_wipe(0.0, 0.0)
    kf_wipe(25.85, 0.0)
    kf_wipe(25.97, 1.0)
    kf_wipe(26.04, 1.0)
    kf_wipe(26.15, 0.0)
    kf_wipe(57.45, 0.0)
    kf_wipe(58.0, 0.45)

    comp = nodes.new("CompositorNodeComposite")
    comp.location = (720, 40)
    links.new(mix_wipe.outputs["Image"], comp.inputs["Image"])


def build_complete_project(
    width: int,
    height: int,
    samples: int,
    download_assets: bool = False,
    pbr_res: str = "2k",
) -> Tuple[str, ExactCharacterCastManager]:
    """Bangun dunia 3D referensi nyata + Poly Haven CC0 + karakter 100% asli Preview 1."""
    t0 = time.perf_counter()
    if download_assets:
        print(f"[Assets] Mengunduh Tekstur PBR CC0 ({pbr_res}) & 15 Model 3D Nyata dari Poly Haven...")
        download_polyhaven_pbr_pack(resolution=pbr_res)
        download_polyhaven_3d_models(resolution="1k")

    reset_scene()
    configure_eevee_next(width, height, samples=samples)

    print("[Blender] 1/5 Membangun pustaka shader Cel-Shaded Cerah + PBR 2K...")
    mats = create_material_library()

    print("[Blender] 2/5 Membangun 6 Lokasi 3D Berbasis Referensi Nyata + Model CC0 Poly Haven...")
    handles = build_all_6_locations(mats)

    print("[Blender] 3/5 Memasang Karakter 100% Asli Preview 1 (Bima, Oren, Hero Props, Figuran)...")
    cast_mgr = ExactCharacterCastManager(char_scale=3.0 if width >= 1000 else 2.6, prop_scale=3.2)
    cast_mgr.build_actor_planes()

    print("[Blender] 4/5 Mengatur Langit 3-Stop Cerah + Pencahayaan 3 Fase + Kompositor Mist Haze...")
    setup_world_and_lights(mats)
    setup_compositor()

    print("[Blender] 5/5 Menganimasikan 28 Gerakan Kamera & Mekanisme Dunia Dinamis (1.740 Frame)...")
    build_and_animate_virtual_camera()
    animate_dynamic_world(handles)

    # Set pose awal frame 1 agar .blend langsung rapi saat dibuka di Blender UI
    try:
        cast_mgr.update_for_frame(1)
    except Exception as exc:
        print(f"[Warn] Skip sprite frame 1 init ({exc})")

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    blend_path = os.path.join(OUTPUT_DIR, "jangan_sampai_kunci_ini_jatuh.blend")
    bpy.ops.wm.save_as_mainfile(filepath=blend_path)
    print(f"[Blender] Scene 3D selesai dibangun & disimpan ke: {blend_path} ({time.perf_counter() - t0:.1f}s)")
    return blend_path, cast_mgr


def _rebind_cast_manager_from_loaded_blend(width: int) -> ExactCharacterCastManager:
    """Sambungkan ulang `ExactCharacterCastManager` ke bidang aktor saat memuat file `.blend`."""
    cast_mgr = ExactCharacterCastManager(char_scale=3.0 if width >= 1000 else 2.6, prop_scale=3.2)
    names = [
        ("Actor_Bima", True), ("Actor_Oren", True),
        ("Actor_GoldenKey", False), ("Actor_SilverKey", False),
        ("Actor_Pedagang_0", True), ("Actor_Pedagang_1", True), ("Actor_Pedagang_2", True),
        ("Actor_Penumpang_0", True), ("Actor_Penumpang_1", True), ("Actor_Penumpang_2", True), ("Actor_Penumpang_3", True),
    ]
    missing = False
    for nm, ab in names:
        obj = bpy.data.objects.get(nm)
        if obj is None or not obj.data.materials:
            missing = True
            break
        tex = obj.data.materials[0].node_tree.nodes.get("Sprite_Tex")
        if tex is None:
            missing = True
            break
        cast_mgr.actors[nm] = (obj, tex, ab)
    if missing:
        cast_mgr.build_actor_planes()
    return cast_mgr


def render_previews(cast_mgr: ExactCharacterCastManager) -> None:
    os.makedirs(PREVIEW_DIR, exist_ok=True)
    scene = bpy.context.scene
    t0 = time.perf_counter()
    for fname, t_sec, _badge, _desc in HERO_PREVIEW_SHOTS:
        fr = sec_to_frame(t_sec)
        scene.frame_set(fr)
        cast_mgr.update_for_frame(fr, quantize_deg=4.0)
        out_fp = os.path.join(PREVIEW_DIR, fname)
        scene.render.filepath = out_fp
        ts = time.perf_counter()
        bpy.ops.render.render(write_still=True)
        print(f"  [EEVEE Preview] {fname} (frame {fr:04d}, t={t_sec:05.2f}s) selesai dalam {time.perf_counter() - ts:.2f}s")
    print(f"[EEVEE Preview] Semua 12 screenshot preview selesai dalam {time.perf_counter() - t0:.1f}s -> {PREVIEW_DIR}")


def render_video_sequence(cast_mgr: ExactCharacterCastManager, start_frame: int, end_frame: int, resume: bool, out_mp4: str) -> None:
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
        cast_mgr.update_for_frame(fr, quantize_deg=6.0)
        scene.render.filepath = fp
        bpy.ops.render.render(write_still=True)
        if idx == 1 or idx % 15 == 0 or fr == end_frame:
            el = time.perf_counter() - t0
            print(f"[EEVEE Render] Frame {fr:04d}/{end_frame:04d} ({idx*100.0/total_to_do:5.1f}%) | elapsed {el:.1f}s", flush=True)

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
        cmd += ["-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "16", "-preset", "medium"]
        if audio_in:
            cmd += ["-c:a", "aac", "-b:a", "192k", "-shortest"]
        cmd.append(out_mp4)
        print(f"[FFmpeg] Menggabungkan 1.740 frame + audio narasi -> {out_mp4}")
        subprocess.run(cmd, check=True)
        print(f"[DONE] Video final EEVEE Next selesai: {out_mp4}")


def _parse_args() -> argparse.Namespace:
    argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    p = argparse.ArgumentParser(description='Blender EEVEE Next v2 — "Jangan Sampai Kunci Ini Jatuh!"')
    p.add_argument("--mode", choices=("save-blend", "previews", "video"), default="previews")
    p.add_argument("--width", type=int, default=DEFAULT_WIDTH)
    p.add_argument("--height", type=int, default=DEFAULT_HEIGHT)
    p.add_argument("--samples", type=int, default=64)
    p.add_argument("--download-pbr", "--download-assets", dest="download_assets", action="store_true")
    p.add_argument("--pbr-res", default="2k", choices=("1k", "2k"))
    p.add_argument("--blend-in", default="")
    p.add_argument("--start-frame", type=int, default=1)
    p.add_argument("--end-frame", type=int, default=TOTAL_FRAMES)
    p.add_argument("--resume", action="store_true")
    p.add_argument("--out-mp4", default=os.path.join(OUTPUT_DIR, "jangan_sampai_kunci_ini_jatuh_eevee.mp4"))
    return p.parse_args(argv)


def main() -> None:
    ensure_sprite_dependencies()
    args = _parse_args()
    if args.blend_in and os.path.exists(args.blend_in):
        bpy.ops.wm.open_mainfile(filepath=args.blend_in)
        configure_eevee_next(args.width, args.height, samples=args.samples)
        cast_mgr = _rebind_cast_manager_from_loaded_blend(args.width)
    else:
        _, cast_mgr = build_complete_project(
            args.width, args.height, args.samples,
            download_assets=args.download_assets, pbr_res=args.pbr_res,
        )

    if args.mode == "previews":
        render_previews(cast_mgr)
    elif args.mode == "video":
        render_video_sequence(cast_mgr, args.start_frame, args.end_frame, args.resume, args.out_mp4)


if __name__ == "__main__":
    main()
