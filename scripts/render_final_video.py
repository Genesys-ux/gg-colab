"""
Render Video Final 58 Detik (9:16 Vertikal, 30fps = 1.740 Frame) — "Jangan Sampai Kunci Ini Jatuh!"
Menggabungkan 6 Lokasi 3D WebGPU Cel-PBR + 28 Gerakan Kamera Continuous One-Take +
Karakter Rig Terbuka + Audio Narasi Master ElevenLabs (`audio/output/narration_master_58s.wav`).

Contoh pemakaian:
  python scripts/render_final_video.py --width 720 --height 1280 --fps 30 --out output/jangan_sampai_kunci_ini_jatuh.mp4
  python scripts/render_final_video.py --width 1080 --height 1920 --fps 30 --out output/final_1080x1920.mp4
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import time

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

from engine3d.choreography import collect_frame_billboards, evaluate_camera
from engine3d.lighting import evaluate_lighting
from engine3d.math3d import focal_mm_to_vfov_rad, look_at_matrix, perspective_matrix
from engine3d.renderer_wgpu import WgpuCelRenderer
from engine3d.scenes_builder import build_dynamic_world, build_static_world
from engine3d.sprite_cache import SpriteCache


def render_video(
    output_path: str,
    width: int = 720,
    height: int = 1280,
    fps: int = 30,
    duration_sec: float = 58.0,
    audio_path: str | None = None,
) -> str:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("FFmpeg tidak ditemukan di PATH.")

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    renderer = WgpuCelRenderer(width=width, height=height)
    print(f"[Final Render] Adapter: {renderer.adapter_name} | {width}x{height} @ {fps}fps ({duration_sec}s)")

    static_verts = build_static_world()
    renderer.upload_static_world(static_verts)
    sprites = SpriteCache(char_scale=2.2 if width <= 720 else 3.0, prop_scale=2.4 if width <= 720 else 3.0)

    total_frames = int(round(duration_sec * fps))
    use_audio = audio_path if (audio_path and os.path.exists(audio_path)) else None

    cmd = [
        ffmpeg, "-y", "-v", "error",
        "-f", "rawvideo", "-pix_fmt", "rgba",
        "-s", f"{width}x{height}", "-r", str(fps),
        "-i", "-",
    ]
    if use_audio:
        cmd += ["-i", use_audio]
    cmd += ["-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-preset", "medium"]
    if use_audio:
        cmd += ["-c:a", "aac", "-b:a", "192k", "-shortest"]
    cmd.append(output_path)

    t0 = time.perf_counter()
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    assert proc.stdin is not None
    try:
        for f_idx in range(total_frames):
            t_sec = f_idx / float(fps)
            lighting = evaluate_lighting(t_sec)
            dyn_verts, tram_z = build_dynamic_world(t_sec)
            cam = evaluate_camera(t_sec, tram_z)
            bbs = collect_frame_billboards(t_sec, cam, lighting, tram_z, sprites, quantize_deg=8.0)

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
            proc.stdin.write(rgba.tobytes())
            if f_idx % fps == 0 or f_idx == total_frames - 1:
                el = time.perf_counter() - t0
                pct = (f_idx + 1) * 100.0 / total_frames
                print(f"[Render] Frame {f_idx + 1}/{total_frames} ({pct:5.1f}%) | {cam.cam_id} | {el:.1f}s", flush=True)
    finally:
        proc.stdin.close()

    if proc.wait() != 0:
        raise RuntimeError("FFmpeg gagal menulis video final.")
    print(f"Video final selesai: {output_path} ({time.perf_counter() - t0:.1f}s)")
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(description='Render Final 58s 3D Shorts — "Jangan Sampai Kunci Ini Jatuh!"')
    parser.add_argument("--width", type=int, default=720)
    parser.add_argument("--height", type=int, default=1280)
    parser.add_argument("--fps", type=int, default=30)
    parser.add_argument("--duration", type=float, default=58.0)
    parser.add_argument("--audio", default=os.path.join(PROJECT_DIR, "audio", "output", "narration_master_58s.wav"))
    parser.add_argument("--out", default=os.path.join(PROJECT_DIR, "output", "jangan_sampai_kunci_ini_jatuh.mp4"))
    args = parser.parse_args()
    render_video(args.out, args.width, args.height, args.fps, args.duration, args.audio)


if __name__ == "__main__":
    main()
