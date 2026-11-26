"""
Entry Point Headless Blender 4.2 LTS untuk "DETIK KE-75":
Mendukung 3 Mode Eksekusi:
  1. `--mode keyframes` : Render 12 keyframe resolusi tinggi + 3 Contact Sheet Evaluasi (Babak I, II, III)
  2. `--mode clip --clip-index N` (atau `--start-sec X --end-sec Y --out file.mp4`) :
     Render klip video animasi scene tertentu @ 30fps + mux potongan audio master!
  3. `--mode full --out detik_ke_75_final.mp4` : Render penuh 75 detik (2.250 frame)
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import time
from typing import List, Tuple

import bpy  # type: ignore

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_THIS_DIR)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from blender_pipeline.animation_props import update_dynamic_props_for_frame
from blender_pipeline.camera_28_moves import build_and_animate_camera, clamp
from blender_pipeline.characters_cast_25d import Detik75CharacterCastManager
from blender_pipeline.config import (
    AUDIO_MASTER_WAV,
    DEFAULT_HEIGHT,
    DEFAULT_WIDTH,
    EVAL_RENDERS_DIR,
    EVAL_SCENE_CLIPS,
    FPS,
    HERO_EVAL_KEYFRAMES,
    OUTPUT_DIR,
    TOTAL_FRAMES,
    sec_to_frame,
)
from blender_pipeline.lighting_4_turns import setup_world_and_story_lights
from blender_pipeline.materials_cel_pbr import create_material_library, hex_to_linear_rgba
from blender_pipeline.scenes_6_locations import build_all_6_locations


def configure_blender_render(engine_name: str, width: int, height: int, samples: int) -> None:
    scene = bpy.context.scene
    scene.render.resolution_x = int(width)
    scene.render.resolution_y = int(height)
    scene.render.resolution_percentage = 100
    scene.render.fps = FPS
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"
    if hasattr(scene.render.image_settings, "compression"):
        scene.render.image_settings.compression = 15

    if hasattr(scene, "view_layers") and len(scene.view_layers) > 0:
        vl = scene.view_layers[0]
        if hasattr(vl, "use_pass_mist"):
            vl.use_pass_mist = True

    if hasattr(scene.render, "use_persistent_data"):
        scene.render.use_persistent_data = True
    scene.render.use_motion_blur = False

    eng = engine_name.upper()
    if eng == "CYCLES":
        scene.render.engine = "CYCLES"
        cyc = scene.cycles
        cyc.samples = int(samples)
        if hasattr(cyc, "use_adaptive_sampling"):
            cyc.use_adaptive_sampling = True
            cyc.adaptive_threshold = 0.05
        if hasattr(cyc, "use_denoising"):
            cyc.use_denoising = True
        if hasattr(cyc, "denoiser"):
            try:
                cyc.denoiser = "OPENIMAGEDENOISE"
            except Exception:
                pass
        if hasattr(cyc, "max_bounces"):
            cyc.max_bounces = 3
            cyc.diffuse_bounces = 2
            cyc.glossy_bounces = 2
            cyc.transmission_bounces = 2
            cyc.transparent_max_bounces = 6
            cyc.volume_bounces = 0
        cyc.device = "CPU"
        try:
            prefs = bpy.context.preferences.addons["cycles"].preferences
            for dt in ("OPTIX", "CUDA"):
                try:
                    prefs.compute_device_type = dt
                    prefs.get_devices()
                    devs = [d for d in prefs.devices if d.type == dt]
                    if devs:
                        for d in prefs.devices:
                            d.use = (d.type == dt)
                        cyc.device = "GPU"
                        break
                except Exception:
                    continue
        except Exception:
            pass
        print(f"[Render] Cycles ({cyc.device}, {samples} samples + OIDN)", flush=True)
    else:
        avail = [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items]
        scene.render.engine = "BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in avail else "BLENDER_EEVEE"
        eevee = scene.eevee
        if hasattr(eevee, "taa_render_samples"):
            eevee.taa_render_samples = min(16, int(samples))
        if hasattr(eevee, "use_shadows"):
            eevee.use_shadows = True
        if hasattr(eevee, "use_raytracing"):
            eevee.use_raytracing = False
        if hasattr(eevee, "use_gtao"):
            eevee.use_gtao = True
        print(f"[Render] EEVEE ({scene.render.engine}, {min(16, int(samples))} samples)", flush=True)

    vs = scene.view_settings
    for vt in ("Filmic", "Standard", "AgX"):
        try:
            vs.view_transform = vt
            break
        except Exception:
            continue
    for lk in ("Medium High Contrast", "None"):
        try:
            vs.look = lk
            break
        except Exception:
            continue
    vs.exposure = 0.25


def setup_compositor() -> None:
    """Kompositor: Mist Haze per babak + Fog Glow Bloom + Reality Shatter Flash + End Fade-Out."""
    scene = bpy.context.scene
    scene.use_nodes = True
    tree = scene.node_tree
    nodes = tree.nodes
    links = tree.links
    nodes.clear()

    rl = nodes.new("CompositorNodeRLayers")
    rl.location = (-780, 0)

    haze_mix = nodes.new("CompositorNodeMixRGB")
    haze_mix.blend_type = "MIX"
    haze_mix.inputs[2].default_value = hex_to_linear_rgba("#38D6FF")
    haze_mix.location = (-480, 40)

    mist_mul = nodes.new("CompositorNodeMath")
    mist_mul.operation = "MULTIPLY"
    mist_mul.use_clamp = True
    mist_mul.inputs[1].default_value = 0.22
    mist_mul.location = (-640, -180)
    if rl.outputs.get("Mist") is not None:
        links.new(rl.outputs["Mist"], mist_mul.inputs[0])
        links.new(mist_mul.outputs["Value"], haze_mix.inputs[0])
    else:
        haze_mix.inputs[0].default_value = 0.0
    links.new(rl.outputs["Image"], haze_mix.inputs[1])

    def kf_haze(t_s: float, col: str, fac: float) -> None:
        fr = sec_to_frame(t_s)
        haze_mix.inputs[2].default_value = hex_to_linear_rgba(col)
        haze_mix.inputs[2].keyframe_insert(data_path="default_value", frame=fr)
        mist_mul.inputs[1].default_value = fac
        mist_mul.inputs[1].keyframe_insert(data_path="default_value", frame=fr)

    kf_haze(0.0, "#2BC8FF", 0.18)
    kf_haze(16.0, "#2BC8FF", 0.22)
    kf_haze(17.5, "#1E3A6E", 0.34)
    kf_haze(40.0, "#FFB627", 0.24)
    kf_haze(45.5, "#FFFFFF", 0.55)
    kf_haze(46.5, "#B8D4EC", 0.14)
    kf_haze(64.5, "#FFD470", 0.28)

    glare = nodes.new("CompositorNodeGlare")
    glare.glare_type = "FOG_GLOW"
    glare.quality = "MEDIUM"
    glare.threshold = 1.05
    glare.size = 7
    glare.location = (-220, 40)
    links.new(haze_mix.outputs["Image"], glare.inputs["Image"])

    # White shatter flash at t=45.85s + Fade-to-black at t=73.8..75.0s
    flash_mix = nodes.new("CompositorNodeMixRGB")
    flash_mix.blend_type = "MIX"
    flash_mix.inputs[0].default_value = 0.0
    flash_mix.inputs[2].default_value = (1.0, 1.0, 1.0, 1.0)
    flash_mix.location = (40, 40)
    links.new(glare.outputs["Image"], flash_mix.inputs[1])

    for t_s, fac, col_v in [
        (0.0, 0.0, (1.0, 1.0, 1.0, 1.0)),
        (45.4, 0.0, (1.0, 1.0, 1.0, 1.0)),
        (45.95, 0.88, (1.0, 1.0, 1.0, 1.0)),
        (46.25, 0.0, (1.0, 1.0, 1.0, 1.0)),
        (73.6, 0.0, (0.0, 0.0, 0.0, 1.0)),
        (74.2, 1.0, (0.0, 0.0, 0.0, 1.0)),
        (75.0, 1.0, (0.0, 0.0, 0.0, 1.0)),
    ]:
        fr = sec_to_frame(t_s)
        flash_mix.inputs[0].default_value = clamp(fac)
        flash_mix.inputs[0].keyframe_insert(data_path="default_value", frame=fr)
        flash_mix.inputs[2].default_value = col_v
        flash_mix.inputs[2].keyframe_insert(data_path="default_value", frame=fr)

    comp = nodes.new("CompositorNodeComposite")
    comp.location = (300, 40)
    links.new(flash_mix.outputs["Image"], comp.inputs["Image"])


def _build_contact_sheets(kf_dir: str) -> None:
    from PIL import Image, ImageDraw, ImageFont

    try:
        f_hd = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
        f_lb = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 16)
        f_sb = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
    except Exception:
        f_hd = f_lb = f_sb = ImageFont.load_default()

    groups = [
        ("sheet_1_babak1_maglev.png", "BABAK I — KERETA MAGLEV EXPRESS 09 & PORTAL BADAI (00:00–00:18)", HERO_EVAL_KEYFRAMES[0:4]),
        ("sheet_2_babak2_atap_badai.png", "BABAK II — ATAP APEX TOWER, SNIPER KIRA & KUE LILIN (00:18–00:46)", HERO_EVAL_KEYFRAMES[4:8]),
        ("sheet_3_babak3_icu_twist.png", "BABAK III — MATCH-CUT ICU 404 & TWIST KORIDOR EMAS (00:46–01:15)", HERO_EVAL_KEYFRAMES[8:12]),
    ]
    for out_name, banner, items in groups:
        cw, ch = 360, 640
        sheet = Image.new("RGB", (cw * 4 + 50, ch + 130), (16, 15, 24))
        dr = ImageDraw.Draw(sheet)
        dr.text((25, 18), f"DETIK KE-75 • {banner}", fill=(255, 224, 130), font=f_hd)
        for i, (fn, _, tag, desc) in enumerate(items):
            p = os.path.join(kf_dir, fn)
            if not os.path.exists(p):
                continue
            im = Image.open(p).convert("RGB").resize((cw - 12, ch - 12), Image.Resampling.LANCZOS)
            x0 = 22 + i * cw
            sheet.paste(im, (x0, 62))
            dr.text((x0 + 4, 62 + ch - 4), tag, fill=(115, 225, 255), font=f_lb)
            dr.text((x0 + 4, 62 + ch + 18), desc[:48], fill=(220, 225, 238), font=f_sb)
        out_p = os.path.join(kf_dir, out_name)
        sheet.save(out_p, quality=94)
        print(f"[Sheet] Saved {out_p}", flush=True)


def _encode_clip_mp4(frames_dir: str, out_mp4: str, start_sec: float, end_sec: float) -> None:
    ffmpeg_bin = shutil.which("ffmpeg")
    if not ffmpeg_bin:
        raise RuntimeError("FFmpeg tidak ditemukan di PATH!")
    os.makedirs(os.path.dirname(os.path.abspath(out_mp4)), exist_ok=True)
    dur = max(0.2, end_sec - start_sec)

    # Jika klip mencakup detik >= 74.0, tambahkan kartu judul "DETIK KE-75" di frame akhir via PIL!
    from PIL import Image, ImageDraw, ImageFont
    frame_files = sorted(f for f in os.listdir(frames_dir) if f.endswith(".png"))
    for idx, fn in enumerate(frame_files):
        t_cur = start_sec + idx / float(FPS)
        if t_cur >= 73.9:
            fp = os.path.join(frames_dir, fn)
            im = Image.open(fp).convert("RGB")
            dr = ImageDraw.Draw(im)
            try:
                f_big = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 52)
            except Exception:
                f_big = ImageFont.load_default()
            txt = "DETIK KE-75"
            bb = dr.textbbox((0, 0), txt, font=f_big)
            tw, th = bb[2] - bb[0], bb[3] - bb[1]
            dr.text(((im.width - tw) // 2, (im.height - th) // 2), txt, fill=(255, 232, 175), font=f_big)
            im.save(fp)

    cmd = [
        ffmpeg_bin, "-y", "-v", "error",
        "-framerate", str(FPS),
        "-i", os.path.join(frames_dir, "f_%05d.png"),
    ]
    if os.path.exists(AUDIO_MASTER_WAV):
        cmd += ["-ss", f"{start_sec:.3f}", "-t", f"{dur:.3f}", "-i", AUDIO_MASTER_WAV]
    cmd += ["-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "19", "-preset", "fast"]
    if os.path.exists(AUDIO_MASTER_WAV):
        cmd += ["-c:a", "aac", "-b:a", "192k", "-shortest"]
    cmd.append(out_mp4)
    subprocess.run(cmd, check=True)
    print(f"[MP4] Saved {out_mp4}", flush=True)


def parse_cli_args() -> argparse.Namespace:
    argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    p = argparse.ArgumentParser(description="Headless Blender 4.2 Renderer — DETIK KE-75")
    p.add_argument("--mode", choices=["keyframes", "clip", "full"], default="keyframes")
    p.add_argument("--engine", choices=["CYCLES", "EEVEE"], default="CYCLES")
    p.add_argument("--width", type=int, default=DEFAULT_WIDTH)
    p.add_argument("--height", type=int, default=DEFAULT_HEIGHT)
    p.add_argument("--samples", type=int, default=16)
    p.add_argument("--clip-index", type=int, default=-1)
    p.add_argument("--start-sec", type=float, default=0.0)
    p.add_argument("--end-sec", type=float, default=5.0)
    p.add_argument("--out", default="")
    return p.parse_args(argv)


def main() -> None:
    args = parse_cli_args()
    t0 = time.time()

    bpy.ops.wm.read_factory_settings(use_empty=True)
    configure_blender_render(args.engine, args.width, args.height, args.samples)

    mats = create_material_library()
    dyn_props = build_all_6_locations(mats)
    setup_world_and_story_lights()
    setup_compositor()

    cast = Detik75CharacterCastManager(sprite_scale=2.4)
    cast.build_actor_planes()

    scene = bpy.context.scene

    if args.mode == "keyframes":
        build_and_animate_camera(1, TOTAL_FRAMES)
        kf_dir = args.out or os.path.join(EVAL_RENDERS_DIR, "keyframes")
        os.makedirs(kf_dir, exist_ok=True)
        for idx, (fname, t_sec, tag, _) in enumerate(HERO_EVAL_KEYFRAMES):
            fr = sec_to_frame(t_sec)
            scene.frame_set(fr)
            update_dynamic_props_for_frame(dyn_props, fr)
            cast.update_for_frame(fr)
            out_p = os.path.join(kf_dir, fname)
            scene.render.filepath = out_p
            bpy.ops.render.render(write_still=True)
            print(f"[Keyframe {idx+1}/12] {tag} -> {out_p} ({time.time() - t0:.1f}s)", flush=True)
        _build_contact_sheets(kf_dir)
        return

    # Mode clip / full
    if args.mode == "full":
        s_sec, e_sec = 0.0, 75.0
        out_mp4 = args.out or os.path.join(OUTPUT_DIR, "detik_ke_75_full.mp4")
    else:
        if 0 <= args.clip_index < len(EVAL_SCENE_CLIPS):
            spec = EVAL_SCENE_CLIPS[args.clip_index]
            s_sec = float(spec["start_sec"])
            e_sec = float(spec["end_sec"])
            out_mp4 = args.out or os.path.join(EVAL_RENDERS_DIR, "clips", f"{spec['id']}.mp4")
        else:
            s_sec, e_sec = args.start_sec, args.end_sec
            out_mp4 = args.out or os.path.join(EVAL_RENDERS_DIR, "clips", "custom_clip.mp4")

    f_start = sec_to_frame(s_sec)
    f_end = sec_to_frame(e_sec)
    build_and_animate_camera(f_start, f_end)

    tmp_frames = os.path.join(OUTPUT_DIR, f"tmp_frames_{f_start}_{f_end}")
    shutil.rmtree(tmp_frames, ignore_errors=True)
    os.makedirs(tmp_frames, exist_ok=True)

    total_f = f_end - f_start + 1
    for i, fr in enumerate(range(f_start, f_end + 1)):
        scene.frame_set(fr)
        update_dynamic_props_for_frame(dyn_props, fr)
        cast.update_for_frame(fr)
        # Twist akhir ranjang kosong di pantulan kaca (t >= 68.4s)
        t_cur = (fr - 1) / float(FPS)
        for bp in dyn_props.get("icu_bed_parts", []):
            bp.hide_render = (t_cur >= 68.4)

        scene.render.filepath = os.path.join(tmp_frames, f"f_{i:05d}.png")
        bpy.ops.render.render(write_still=True)
        if i % 10 == 0 or i == total_f - 1:
            print(f"[Clip] Frame {i+1}/{total_f} (global {fr}) elapsed={time.time()-t0:.1f}s", flush=True)

    _encode_clip_mp4(tmp_frames, out_mp4, s_sec, e_sec)
    shutil.rmtree(tmp_frames, ignore_errors=True)


if __name__ == "__main__":
    main()
