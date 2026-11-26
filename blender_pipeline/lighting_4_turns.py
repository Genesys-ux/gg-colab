"""
Pencahayaan Atmosferik Dinamis 4 Babak Emosi ("Dynamic Story Lighting") — `3d-cinematic-animation-director`
Memenuhi semua aturan wajib:
  - Low Sun + Long Shadow + Blue Shade
  - God Rays (Volumetric cones) & Atmospheric Mist Haze
  - Berubah dinamis mengikuti plot twist cerita:
      * Fase 1 (00:00–00:16.5): Cold Cyan Maglev & Neon Flicker + Blue Shade
      * Fase 2 (00:16.5–00:39.5): Deep Storm Navy + Strobe Lightning + Red/Blue Tactical Contrast
      * Fase 3 (00:39.5–00:46.5): Warm Golden Birthday Candle Glow vs Frozen Crystal Shatter
      * Fase 4 (00:46.5–01:15.0): Melancholic ICU Blue-Warm GI -> Radiant Low-Sun Golden Corridor!
"""
from __future__ import annotations

import math
from typing import Dict, Tuple

import bpy  # type: ignore
from mathutils import Euler  # type: ignore

from .config import CAKE_POS_W, ICU_BED_POS_W, LOC4_FLOOR_Y, LOC5_FLOOR_Y, LOC6_FLOOR_Y, sec_to_frame, w_to_b
from .materials_cel_pbr import get_or_create_story_phase_group, hex_to_linear_rgba
from .mesh_utils import get_or_create_collection, link_object


def _kf_rgba(sock, hex_c: str, frame: int) -> None:
    sock.default_value = hex_to_linear_rgba(hex_c)
    sock.keyframe_insert(data_path="default_value", frame=frame)


def _kf_val(sock, val: float, frame: int) -> None:
    sock.default_value = float(val)
    sock.keyframe_insert(data_path="default_value", frame=frame)


def _kf_light(light_obj, hex_c: str, energy: float, frame: int, rot_deg: Tuple[float, float, float] | None = None) -> None:
    rgba = hex_to_linear_rgba(hex_c)
    light_obj.data.color = rgba[:3]
    light_obj.data.keyframe_insert(data_path="color", frame=frame)
    light_obj.data.energy = float(energy)
    light_obj.data.keyframe_insert(data_path="energy", frame=frame)
    if rot_deg is not None:
        light_obj.rotation_euler = Euler(tuple(math.radians(a) for a in rot_deg), "XYZ")
        light_obj.keyframe_insert(data_path="rotation_euler", frame=frame)


def setup_world_and_story_lights() -> Dict[str, "bpy.types.Object"]:
    scene = bpy.context.scene
    col = get_or_create_collection("Lighting_Dynamic_Story")

    # ==================== 1. WORLD 3-STOP GRADIENT SKY + MIST PASS HAZE ====================
    world = scene.world or bpy.data.worlds.new("World_Detik75")
    scene.world = world
    world.use_nodes = True
    if hasattr(world, "mist_settings"):
        world.mist_settings.start = 6.0
        world.mist_settings.depth = 68.0
        world.mist_settings.falloff = "QUADRATIC"

    wn = world.node_tree.nodes
    wl = world.node_tree.links
    wn.clear()

    w_out = wn.new("ShaderNodeOutputWorld")
    w_out.location = (680, 0)
    tex_c = wn.new("ShaderNodeTexCoord")
    tex_c.location = (-680, 120)
    sep = wn.new("ShaderNodeSeparateXYZ")
    sep.location = (-480, 120)
    wl.new(tex_c.outputs["Generated"], sep.inputs["Vector"])

    sky_hor = wn.new("ShaderNodeRGB")
    sky_hor.location = (-480, -120)
    sky_top = wn.new("ShaderNodeRGB")
    sky_top.location = (-480, -300)

    ramp = wn.new("ShaderNodeMapRange")
    ramp.inputs["From Min"].default_value = -0.05
    ramp.inputs["From Max"].default_value = 0.62
    ramp.location = (-240, 120)
    wl.new(sep.outputs["Z"], ramp.inputs["Value"])

    mix_sky = wn.new("ShaderNodeMix")
    mix_sky.data_type = "RGBA"
    mix_sky.location = (40, 40)
    wl.new(ramp.outputs["Result"], mix_sky.inputs[0])
    wl.new(sky_hor.outputs[0], mix_sky.inputs[6])
    wl.new(sky_top.outputs[0], mix_sky.inputs[7])

    bg = wn.new("ShaderNodeBackground")
    bg.inputs["Strength"].default_value = 1.45
    bg.location = (360, 40)
    wl.new(mix_sky.outputs[2], bg.inputs["Color"])
    wl.new(bg.outputs["Background"], w_out.inputs["Surface"])

    # ==================== 2. LOW SUN (LONG SHADOW) + BLUE SHADE FILL ====================
    sun_data = bpy.data.lights.new("Sun_LowAngle_Main", type="SUN")
    sun_data.angle = math.radians(4.5)  # Long crisp dramatic shadows!
    sun_obj = bpy.data.objects.new("Sun_LowAngle_Main", sun_data)
    link_object(sun_obj, col)

    fill_data = bpy.data.lights.new("Sun_BlueShade_Fill", type="SUN")
    fill_data.angle = math.radians(38.0)
    fill_obj = bpy.data.objects.new("Sun_BlueShade_Fill", fill_data)
    fill_obj.rotation_euler = Euler((math.radians(48.0), math.radians(-30.0), math.radians(150.0)), "XYZ")
    link_object(fill_obj, col)

    # Local Hero Accent Lights per Location
    def _make_point(nm: str, pos_w: Tuple[float, float, float], hex_c: str, energy: float, radius: float = 0.4):
        ld = bpy.data.lights.new(nm, type="POINT")
        ld.color = hex_to_linear_rgba(hex_c)[:3]
        ld.energy = energy
        ld.shadow_soft_size = radius
        lo = bpy.data.objects.new(nm, ld)
        lo.location = w_to_b(*pos_w)
        link_object(lo, col)
        return lo

    maglev_pt1 = _make_point("Pt_Maglev_Cyan", (0.0, 2.35, 6.0), "#38E2FF", 180.0, 0.6)
    maglev_pt2 = _make_point("Pt_Maglev_PortalRed", (0.0, 1.85, 28.5), "#FF2E42", 220.0, 0.5)
    rooftop_storm_pt = _make_point("Pt_Rooftop_Lightning", (2.0, LOC4_FLOOR_Y + 9.5, 58.0), "#9CD6FF", 650.0, 1.5)
    candle_pt = _make_point("Pt_Birthday_Candle", (CAKE_POS_W[0], CAKE_POS_W[1] + 0.38, CAKE_POS_W[2]), "#FFB627", 0.0, 0.18)
    icu_warm_pt = _make_point("Pt_ICU_CorridorWarm", (3.2, LOC5_FLOOR_Y + 2.2, 111.2), "#FFD07B", 260.0, 0.9)
    icu_cool_pt = _make_point("Pt_ICU_MonitorCool", (-1.4, LOC5_FLOOR_Y + 2.1, 111.5), "#6BB8FF", 120.0, 0.8)
    corridor_sun_pt = _make_point("Pt_Golden_Corridor", (8.2, LOC6_FLOOR_Y + 2.8, 113.0), "#FFD470", 820.0, 1.4)

    # ==================== 3. KEYFRAME 4 STORY LIGHTING PHASES ====================
    ng = get_or_create_story_phase_group()
    n_tint = ng.nodes["Story_Tint_RGB"].outputs[0]
    n_rim = ng.nodes["Story_Rim_RGB"].outputs[0]
    n_str = ng.nodes["Story_Rim_Strength"].outputs[0]

    def set_phase(t_sec: float, hor: str, top: str, sun_c: str, sun_e: float, sun_rot: Tuple[float, float, float], fill_c: str, fill_e: float, rim_c: str, rim_s: float) -> None:
        fr = sec_to_frame(t_sec)
        _kf_rgba(sky_hor.outputs[0], hor, fr)
        _kf_rgba(sky_top.outputs[0], top, fr)
        _kf_light(sun_obj, sun_c, sun_e, fr, sun_rot)
        _kf_light(fill_obj, fill_c, fill_e, fr)
        _kf_rgba(n_tint, fill_c, fr)
        _kf_rgba(n_rim, rim_c, fr)
        _kf_val(n_str, rim_s, fr)

    # Fase 1 (00:00–00:16): Cold Cyan Maglev + Blue Shade
    set_phase(0.0, "#143852", "#071322", "#7CE8FF", 2.2, (74.0, 12.0, -25.0), "#1D4E89", 0.95, "#4CE8FF", 0.42)
    set_phase(15.5, "#184262", "#081628", "#9CF0FF", 2.6, (72.0, 10.0, -25.0), "#1D4E89", 1.0, "#FF384C", 0.48)

    # Fase 2 (00:17–00:39): Storm Rooftop — Low Storm Sun + Deep Blue Shade + Lightning Strobe
    set_phase(17.5, "#23395B", "#091122", "#B8DCFF", 3.4, (78.0, -18.0, 35.0), "#1A3C70", 1.15, "#FF2E44", 0.50)
    # Kilatan petir strobe dramatis di detik 20.4 & 29.0
    set_phase(20.2, "#23395B", "#091122", "#B8DCFF", 3.4, (78.0, -18.0, 35.0), "#1A3C70", 1.15, "#FF2E44", 0.50)
    set_phase(20.5, "#9BE2FF", "#3A6EA5", "#FFFFFF", 9.5, (72.0, -15.0, 35.0), "#4EA8DE", 2.40, "#FFFFFF", 0.75)
    set_phase(21.0, "#23395B", "#091122", "#B8DCFF", 3.4, (78.0, -18.0, 35.0), "#1A3C70", 1.15, "#38D6FF", 0.48)
    set_phase(38.5, "#203454", "#081020", "#A8D4FF", 3.0, (78.0, -18.0, 35.0), "#1A3C70", 1.10, "#38D6FF", 0.52)

    # Fase 3 (00:40–00:46): Kejutan Kue Ulang Tahun & Pecahnya Realitas Kaca Putih-Emas!
    set_phase(40.2, "#4A4368", "#181C36", "#FFD27D", 3.8, (80.0, -12.0, 28.0), "#3A5A96", 1.35, "#FFB627", 0.62)
    set_phase(44.8, "#FFF6E5", "#9EC9F2", "#FFF8EB", 6.2, (82.0, -10.0, 24.0), "#6BA4D9", 1.85, "#FFE89E", 0.70)

    # Fase 4A (00:46.5–01:02): Ruang ICU Kamar 404 — Melankolis Blue Shade + Sinar Koridor Hangat
    set_phase(46.6, "#8AA8C7", "#3A5472", "#FFE0A3", 2.8, (79.0, -24.0, -68.0), "#3B6998", 1.15, "#FFD285", 0.34)
    set_phase(62.0, "#8AA8C7", "#3A5472", "#FFE0A3", 2.9, (79.0, -24.0, -68.0), "#3B6998", 1.15, "#FFD285", 0.36)

    # Fase 4B (01:03–01:15): Twist Akhir Koridor Cahaya Keemasan — Low Golden Sun + Long Shadows + Blue Shade!
    set_phase(64.5, "#FFD88A", "#5B82B0", "#FFD166", 5.4, (81.5, -28.0, -76.0), "#4676A8", 1.35, "#FFE58F", 0.60)
    set_phase(73.5, "#FFE4A8", "#6C92BF", "#FFE082", 6.0, (82.5, -28.0, -76.0), "#4676A8", 1.40, "#FFF0B8", 0.65)

    # Animasi cahaya hangat api lilin ulang tahun (menyala saat koper terbuka t=39.2..46.0s)
    _kf_light(candle_pt, "#FFB627", 0.0, sec_to_frame(38.8))
    _kf_light(candle_pt, "#FFB627", 240.0, sec_to_frame(39.6))
    _kf_light(candle_pt, "#FFC94D", 320.0, sec_to_frame(43.5))
    _kf_light(candle_pt, "#FFB627", 0.0, sec_to_frame(46.3))

    return {
        "sun": sun_obj,
        "fill": fill_obj,
        "maglev_pt1": maglev_pt1,
        "maglev_pt2": maglev_pt2,
        "rooftop_storm_pt": rooftop_storm_pt,
        "candle_pt": candle_pt,
        "icu_warm_pt": icu_warm_pt,
        "icu_cool_pt": icu_cool_pt,
        "corridor_sun_pt": corridor_sun_pt,
    }
