"""
Evolusi Pencahayaan 3 Fase (Production Bible Lighting Progression):
  - Fase 1 (00:00–00:26): Warm Low Sun, razor-long shadows, cool blue shade, warm golden haze
  - Fase 2 (00:27–00:38): Story Turn — Deep Indigo shade, eerie emerald steam haze, hard furnace-orange rim
  - Fase 3A (00:39–00:52): Climax — Ultra-low crimson sun, electric blue shade, thick golden-crimson haze
  - Fase 3B (00:53–00:58): Frozen Violet-Gold Twilight + crisp cyan cel-shade rim light + shockwave flash
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Tuple

import numpy as np

from .math3d import clamp, lerp, smoothstep


@dataclass
class LightingState:
    phase_name: str  # "phase1" | "phase2" | "phase3_crimson" | "phase3_twilight"
    sun_dir: Tuple[float, float, float]
    sun_color: Tuple[float, float, float]
    sun_intensity: float
    shade_color: Tuple[float, float, float]  # cool blue / deep indigo / electric blue / violet
    ambient_color: Tuple[float, float, float]
    rim_color: Tuple[float, float, float]
    rim_intensity: float
    fog_color: Tuple[float, float, float]
    fog_density: float
    sky_top: Tuple[float, float, float]
    sky_mid: Tuple[float, float, float]
    sky_horizon: Tuple[float, float, float]
    sun_disc_color: Tuple[float, float, float]
    sun_disc_size: float
    point_light_pos: Tuple[float, float, float]
    point_light_color: Tuple[float, float, float]
    point_light_intensity: float
    shockwave_radius: float = 0.0
    shockwave_alpha: float = 0.0
    exposure: float = 1.05
    black_wipe: float = 0.0


def _lerp3(a: Tuple[float, float, float], b: Tuple[float, float, float], u: float) -> Tuple[float, float, float]:
    return (lerp(a[0], b[0], u), lerp(a[1], b[1], u), lerp(a[2], b[2], u))


def _blend_lighting(a: LightingState, b: LightingState, u: float, phase_name: str) -> LightingState:
    t = smoothstep(u)
    sd = np.array(_lerp3(a.sun_dir, b.sun_dir, t), dtype=np.float32)
    n = float(np.linalg.norm(sd)) or 1.0
    sd /= n
    return LightingState(
        phase_name=phase_name,
        sun_dir=(float(sd[0]), float(sd[1]), float(sd[2])),
        sun_color=_lerp3(a.sun_color, b.sun_color, t),
        sun_intensity=lerp(a.sun_intensity, b.sun_intensity, t),
        shade_color=_lerp3(a.shade_color, b.shade_color, t),
        ambient_color=_lerp3(a.ambient_color, b.ambient_color, t),
        rim_color=_lerp3(a.rim_color, b.rim_color, t),
        rim_intensity=lerp(a.rim_intensity, b.rim_intensity, t),
        fog_color=_lerp3(a.fog_color, b.fog_color, t),
        fog_density=lerp(a.fog_density, b.fog_density, t),
        sky_top=_lerp3(a.sky_top, b.sky_top, t),
        sky_mid=_lerp3(a.sky_mid, b.sky_mid, t),
        sky_horizon=_lerp3(a.sky_horizon, b.sky_horizon, t),
        sun_disc_color=_lerp3(a.sun_disc_color, b.sun_disc_color, t),
        sun_disc_size=lerp(a.sun_disc_size, b.sun_disc_size, t),
        point_light_pos=_lerp3(a.point_light_pos, b.point_light_pos, t),
        point_light_color=_lerp3(a.point_light_color, b.point_light_color, t),
        point_light_intensity=lerp(a.point_light_intensity, b.point_light_intensity, t),
        exposure=lerp(a.exposure, b.exposure, t),
    )


PHASE1_LOW_SUN = LightingState(
    phase_name="phase1",
    sun_dir=(0.74, 0.28, 0.61),  # low sun angle -> super long shadows!
    sun_color=(1.0, 0.84, 0.52),
    sun_intensity=1.95,
    shade_color=(0.18, 0.34, 0.66),  # cool blue shade!
    ambient_color=(0.30, 0.44, 0.70),
    rim_color=(1.0, 0.88, 0.52),
    rim_intensity=0.95,
    fog_color=(0.98, 0.78, 0.46),  # warm golden atmospheric haze
    fog_density=0.013,
    sky_top=(0.16, 0.40, 0.76),
    sky_mid=(0.54, 0.70, 0.88),
    sky_horizon=(1.0, 0.76, 0.42),
    sun_disc_color=(1.0, 0.94, 0.68),
    sun_disc_size=0.065,
    point_light_pos=(1.6, 26.8, 1.75),
    point_light_color=(1.0, 0.84, 0.48),  # warm golden tungsten glow from banker's desk lamp
    point_light_intensity=0.80,
    exposure=1.18,
)

PHASE2_UNDERGROUND = LightingState(
    phase_name="phase2",
    sun_dir=(-0.45, -0.25, 0.85),  # hard furnace up-angle rim light!
    sun_color=(1.0, 0.44, 0.14),   # fierce furnace orange
    sun_intensity=1.85,
    shade_color=(0.10, 0.13, 0.42),  # deep indigo shade!
    ambient_color=(0.08, 0.38, 0.32),  # eerie emerald bounce
    rim_color=(1.0, 0.48, 0.14),
    rim_intensity=1.35,
    fog_color=(0.06, 0.52, 0.40),  # emerald steam haze!
    fog_density=0.032,
    sky_top=(0.03, 0.05, 0.18),
    sky_mid=(0.05, 0.18, 0.24),
    sky_horizon=(0.08, 0.38, 0.30),
    sun_disc_color=(1.0, 0.42, 0.12),
    sun_disc_size=0.0,
    point_light_pos=(0.0, -19.5, 48.0),  # blazing furnace heart of the city!
    point_light_color=(1.0, 0.46, 0.12),
    point_light_intensity=6.2,
    exposure=1.18,
)

PHASE3_CRIMSON = LightingState(
    phase_name="phase3_crimson",
    sun_dir=(-0.44, 0.24, 0.865),  # giant crimson sun peeking right past the clock tower beside Bima's leap!
    sun_color=(1.0, 0.44, 0.22),
    sun_intensity=2.15,
    shade_color=(0.14, 0.28, 0.76),  # electric blue fill shadow!
    ambient_color=(0.24, 0.26, 0.64),
    rim_color=(1.0, 0.58, 0.24),
    rim_intensity=1.32,
    fog_color=(0.94, 0.34, 0.20),  # thick golden-crimson dust haze!
    fog_density=0.015,
    sky_top=(0.18, 0.10, 0.42),
    sky_mid=(0.74, 0.20, 0.26),
    sky_horizon=(1.0, 0.44, 0.16),
    sun_disc_color=(1.0, 0.58, 0.22),
    sun_disc_size=0.16,  # gigantic blazing crimson sun for [CAM 24]!
    point_light_pos=(0.0, 12.0, 92.0),
    point_light_color=(1.0, 0.55, 0.22),
    point_light_intensity=1.0,
    exposure=1.16,
)

PHASE3_TWILIGHT = LightingState(
    phase_name="phase3_twilight",
    sun_dir=(-0.38, 0.26, 0.89),
    sun_color=(1.0, 0.80, 0.44),  # golden twilight highlight
    sun_intensity=1.82,
    shade_color=(0.22, 0.12, 0.52),  # deep frozen violet shadow!
    ambient_color=(0.26, 0.20, 0.56),
    rim_color=(0.30, 0.96, 1.0),  # crisp cyan cel-shade rim light!
    rim_intensity=1.65,
    fog_color=(0.34, 0.18, 0.54),  # crystal-clear violet-gold twilight
    fog_density=0.0085,
    sky_top=(0.10, 0.08, 0.34),
    sky_mid=(0.36, 0.18, 0.56),
    sky_horizon=(0.96, 0.64, 0.36),
    sun_disc_color=(0.68, 0.96, 1.0),
    sun_disc_size=0.06,
    point_light_pos=(0.0, 19.2, 116.4),
    point_light_color=(1.0, 0.86, 0.58),  # warm antique gold glow on dial (cyan stays pure rim light!)
    point_light_intensity=0.72,
    exposure=1.18,
)


def evaluate_lighting(t: float) -> LightingState:
    """Evaluasi lighting lengkap pada detik ke-t (0.0 .. 58.0)."""
    # Hidden black wipe cut 2 frame di [CAM 15] (~25.92s - 26.05s)
    black_wipe = 0.0
    if 25.88 <= t <= 26.12:
        # 2-frame pure black peak at t=26.00s
        dist = abs(t - 26.0)
        if dist < 0.045:
            black_wipe = 1.0
        else:
            black_wipe = clamp(1.0 - (dist - 0.045) / 0.075)

    if t < 26.0:
        st = LightingState(**vars(PHASE1_LOW_SUN))
        # Gang kafe (Lokasi 3, 18-26s): lebih kontras (70% area teduh biru + cahaya bilah emas!)
        if t >= 18.0:
            u = smoothstep((t - 18.0) / 1.5)
            st.shade_color = _lerp3(PHASE1_LOW_SUN.shade_color, (0.11, 0.22, 0.48), u)
            st.fog_density = lerp(0.015, 0.020, u)
            st.point_light_intensity = lerp(0.65, 0.15, u)
        st.black_wipe = black_wipe
        return st

    if t < 38.0:
        st = LightingState(**vars(PHASE2_UNDERGROUND))
        # Percikan biru-zamrud saat kunci menancap di poros mesin ([CAM 18] ~31.8-33.5s)
        if 31.6 <= t <= 34.0:
            spark = clamp(1.0 - abs(t - 32.25) / 1.2)
            st.point_light_color = _lerp3((1.0, 0.44, 0.14), (0.20, 0.96, 0.86), spark * 0.72)
            st.point_light_intensity = lerp(5.2, 6.4, spark)
            st.shockwave_radius = clamp((t - 31.9) / 1.1) * 1.15
            st.shockwave_alpha = spark * 0.34 if t >= 31.9 else 0.0
        st.black_wipe = black_wipe
        return st

    if t < 51.8:
        # Transisi cepat keluar dari kisi ventilasi ke langit crimson ([CAM 20] 38.0-38.7s)
        if t < 38.8:
            st = _blend_lighting(PHASE2_UNDERGROUND, PHASE3_CRIMSON, (t - 38.0) / 0.8, "phase3_crimson")
        else:
            st = LightingState(**vars(PHASE3_CRIMSON))
        return st

    # [CAM 25]-[CAM 28] (51.8-58.0s): Shockwave radial biru-emas membekukan langit jadi Twilight Violet-Gold + Cyan Rim!
    u_tw = clamp((t - 51.8) / 1.15)
    st = _blend_lighting(PHASE3_CRIMSON, PHASE3_TWILIGHT, u_tw, "phase3_twilight")
    if 51.8 <= t <= 54.6:
        sw_u = clamp((t - 51.8) / 2.6)
        st.shockwave_radius = 0.25 + sw_u * 1.35
        st.shockwave_alpha = math.sin(sw_u * math.pi) * 0.95 if sw_u < 1.0 else 0.0
    # Transisi seamless loop menjelang akhir [CAM 28] (57.2-58.0s) menuju gelap celah roda gigi [CAM 01]
    if t >= 57.4:
        loop_u = clamp((t - 57.4) / 0.6)
        st.exposure = lerp(st.exposure, 0.55, loop_u)
    return st
