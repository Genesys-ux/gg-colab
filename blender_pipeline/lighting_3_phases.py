"""
Evolusi Pencahayaan 3 Fase (Production Bible Lighting Progression) untuk Blender 4.2+ EEVEE Next:
  - Fase 1 (00:00–00:26): Warm Low Sun, razor-long shadows, cool blue shade, warm golden volumetric haze
  - Fase 2 (00:26–00:38): Story Turn — Sun off, Deep Indigo shade, emerald volumetric steam, hard furnace-orange rim + KLAK! cyan flash
  - Fase 3A (00:38–00:51.8): Climax — Ultra-low crimson sun, electric blue shade, golden-crimson dust haze
  - Fase 3B (00:51.8–00:58): Frozen Violet-Gold Twilight + Crisp Cyan Fresnel Cel Rim Light!
"""

from __future__ import annotations

import math
from typing import Tuple

import bpy  # type: ignore
from mathutils import Euler, Vector  # type: ignore

from .config import sec_to_frame, w_to_b
from .materials_cel_pbr import get_or_create_phase_control_group, hex_to_linear_rgba
from .mesh_utils import get_or_create_collection, link_object


def _kf_color(sock, rgba: Tuple[float, float, float, float], frame: int) -> None:
    sock.default_value = rgba
    sock.keyframe_insert(data_path="default_value", frame=frame)


def _kf_float(sock, val: float, frame: int) -> None:
    sock.default_value = float(val)
    sock.keyframe_insert(data_path="default_value", frame=frame)


def _kf_light(light_obj, color_hex: str, energy: float, frame: int, rot_deg: Tuple[float, float, float] | None = None) -> None:
    rgba = hex_to_linear_rgba(color_hex)
    light_obj.data.color = rgba[:3]
    light_obj.data.keyframe_insert(data_path="color", frame=frame)
    light_obj.data.energy = float(energy)
    light_obj.data.keyframe_insert(data_path="energy", frame=frame)
    if rot_deg is not None:
        light_obj.rotation_euler = Euler(tuple(math.radians(a) for a in rot_deg), "XYZ")
        light_obj.keyframe_insert(data_path="rotation_euler", frame=frame)


def setup_world_and_lights(mats: dict) -> dict:
    """Bangun World 3-Stop Sky + Volumetric Haze + seluruh lampu 3 fase dan keyframe di 1.740 frame."""
    scene = bpy.context.scene
    col = get_or_create_collection("Lighting_3Phases")

    # ==================== 1. WORLD: 3-STOP GRADIENT SKY + VOLUMETRIC HAZE ====================
    world = scene.world or bpy.data.worlds.new("World_KunciJatuh")
    scene.world = world
    world.use_nodes = True
    wnodes = world.node_tree.nodes
    wlinks = world.node_tree.links
    wnodes.clear()

    w_out = wnodes.new("ShaderNodeOutputWorld")
    w_out.location = (640, 0)

    tex_c = wnodes.new("ShaderNodeTexCoord")
    tex_c.location = (-720, 120)
    sep = wnodes.new("ShaderNodeSeparateXYZ")
    sep.location = (-500, 120)
    wlinks.new(tex_c.outputs["Generated"], sep.inputs["Vector"])

    # Langit 3-stop keyframeable (Horizon -> Mid -> Zenith) menggunakan 2 Mix RGBA
    sky_hor = wnodes.new("ShaderNodeRGB")
    sky_hor.name = "Sky_Horizon"
    sky_hor.location = (-500, -120)
    sky_mid = wnodes.new("ShaderNodeRGB")
    sky_mid.name = "Sky_Mid"
    sky_mid.location = (-500, -300)
    sky_top = wnodes.new("ShaderNodeRGB")
    sky_top.name = "Sky_Top"
    sky_top.location = (-500, -480)

    ramp1 = wnodes.new("ShaderNodeMapRange")
    ramp1.inputs["From Min"].default_value = -0.02
    ramp1.inputs["From Max"].default_value = 0.28
    ramp1.location = (-260, 160)
    wlinks.new(sep.outputs["Z"], ramp1.inputs["Value"])

    ramp2 = wnodes.new("ShaderNodeMapRange")
    ramp2.inputs["From Min"].default_value = 0.24
    ramp2.inputs["From Max"].default_value = 0.78
    ramp2.location = (-260, -20)
    wlinks.new(sep.outputs["Z"], ramp2.inputs["Value"])

    mix_hm = wnodes.new("ShaderNodeMix")
    mix_hm.data_type = "RGBA"
    mix_hm.location = (20, 80)
    wlinks.new(ramp1.outputs["Result"], mix_hm.inputs[0])
    wlinks.new(sky_hor.outputs[0], mix_hm.inputs[6])
    wlinks.new(sky_mid.outputs[0], mix_hm.inputs[7])

    mix_mt = wnodes.new("ShaderNodeMix")
    mix_mt.data_type = "RGBA"
    mix_mt.location = (220, 80)
    wlinks.new(ramp2.outputs["Result"], mix_mt.inputs[0])
    wlinks.new(mix_hm.outputs[2], mix_mt.inputs[6])
    wlinks.new(sky_top.outputs[0], mix_mt.inputs[7])

    bg = wnodes.new("ShaderNodeBackground")
    bg.name = "World_BG"
    bg.inputs["Strength"].default_value = 1.0
    bg.location = (420, 80)
    wlinks.new(mix_mt.outputs[2], bg.inputs["Color"])
    wlinks.new(bg.outputs["Background"], w_out.inputs["Surface"])

    # Volumetric Atmospheric Haze (Golden / Emerald Steam / Crimson Dust / Frozen Twilight!)
    vol = wnodes.new("ShaderNodeVolumeScatter")
    vol.name = "World_Volumetric_Haze"
    vol.inputs["Anisotropy"].default_value = 0.45
    vol.location = (380, -200)
    wlinks.new(vol.outputs["Volume"], w_out.inputs["Volume"])

    # ==================== 2. LAMPU UTAMA & LAMPU LOKAL PER FASE ====================
    def make_light(name: str, ltype: str, loc=(0, 0, 10), rot=(0, 0, 0), radius: float = 0.5):
        ld = bpy.data.lights.new(name=name + "_Data", type=ltype)
        if ltype == "SUN":
            ld.angle = math.radians(1.6)  # bayangan panjang & tegas!
        elif ltype == "POINT":
            ld.shadow_soft_size = radius
        lo = bpy.data.objects.new(name, ld)
        lo.location = Vector(loc)
        lo.rotation_euler = Euler(tuple(math.radians(a) for a in rot), "XYZ")
        link_object(lo, col)
        return lo

    # Matahari Utama (Low Sun -> Off di Gorong-Gorong -> Ultra-Low Crimson -> Frozen Twilight!)
    sun_main = make_light("Sun_Main_Low", "SUN", loc=(0, 0, 40), rot=(72, 12, -40))
    # Fill sejuk (Cool Blue / Deep Indigo / Electric Blue / Violet) agar shadow tidak pernah hitam mati
    sun_fill = make_light("Sun_Fill_Cool", "SUN", loc=(0, 0, 40), rot=(42, -20, 145))
    sun_fill.data.use_shadow = False

    # Lampu Meja Banker's Desk Lamp (Lokasi 1 — cahaya bohlam emas hangat, BUKAN hijau!)
    pt_desk = make_light("Point_L1_BankerLamp", "POINT", loc=w_to_b(1.55, 26.72, 1.75), radius=0.25)
    # Lampu Tungku Mesin Bawah Tanah (Lokasi 4 — sorotan merah-oranye keras dari bawah!)
    pt_furnace = make_light("Point_L4_FurnaceCore", "POINT", loc=w_to_b(0.0, -18.5, 48.2), radius=1.6)
    pt_furnace_rim = make_light("Point_L4_FurnaceRim", "POINT", loc=w_to_b(-3.5, -21.0, 41.5), radius=1.2)
    # Lampu Percikan KLAK! Biru-Zamrud tepat di poros mesin ([CAM 18]!)
    pt_klak = make_light("Point_L4_KlakSpark", "POINT", loc=w_to_b(0.0, -17.0, 42.6), radius=0.35)
    # Cahaya lembut antique gold pada wajah Menara Jam ([CAM 25]-[CAM 28], cyan murni dari rim shader!)
    pt_clock = make_light("Point_L6_ClockGlow", "POINT", loc=w_to_b(0.0, 19.2, 115.6), radius=1.4)

    # ==================== 3. KEYFRAME EVOLUSI PENCAHAYAAN 3 FASE ====================
    ng = get_or_create_phase_control_group()
    n_shade = ng.nodes["Phase_Shade_RGB"].outputs[0]
    n_rim = ng.nodes["Phase_Rim_RGB"].outputs[0]
    n_rim_str = ng.nodes["Phase_Rim_Strength"].outputs[0]

    # Bima Parka Color Response (sesuai Bima.pdf!)
    bima_parka_rgb = mats["bima_parka"].node_tree.nodes.get("Base_Palette_RGB")

    # Daftar checkpoint pencahayaan: (t_sec, shade_hex, rim_hex, rim_str, sky_hor, sky_mid, sky_top, vol_hex, vol_den,
    #   sun_hex, sun_en, sun_rot, fill_hex, fill_en, desk_en, furn_en, klak_en, clk_en, parka_hex)
    keyframes = [
        # FASE 1A: Bengkel & Pasar — Warm Low Sun, Cool Blue Shade, Warm Golden Haze
        (0.0,  "#2A509E", "#FFD670", 0.36, "#FFA852", "#78AEE0", "#2258A8", "#F4BE68", 0.0045, "#FFD280", 4.6, (72, 10, -42), "#4A7CE0", 0.85, 65.0,   0.0,   0.0,  0.0, "#F2B705"),
        (17.5, "#2A509E", "#FFD670", 0.38, "#FFA852", "#78AEE0", "#2258A8", "#F4BE68", 0.0042, "#FFD280", 4.6, (74, 10, -42), "#4A7CE0", 0.85, 10.0,   0.0,   0.0,  0.0, "#F2B705"),
        # FASE 1B: Gang Kafe (18-25.8s) — Kontras lebih kuat (70% Cool Blue Shade + bilah cahaya emas)
        (18.5, "#183276", "#FFCC66", 0.44, "#FFA048", "#6B9ED4", "#1B4A96", "#E8B05C", 0.0055, "#FFCB70", 4.8, (76, 12, -38), "#325EC4", 0.72,  0.0,   0.0,   0.0,  0.0, "#F2B705"),
        (25.8, "#183276", "#FFCC66", 0.44, "#FFA048", "#6B9ED4", "#1B4A96", "#E8B05C", 0.0055, "#FFCB70", 4.8, (76, 12, -38), "#325EC4", 0.72,  0.0,   0.0,   0.0,  0.0, "#F2B705"),
        # FASE 2: STORY TURN (26.1-37.9s) — Matahari mati! Deep Indigo + Emerald Steam + Hard Furnace Orange Rim!
        (26.1, "#12164E", "#FF6E1E", 0.65, "#104A3C", "#0B2432", "#06081E", "#189E7A", 0.0150, "#FF6418", 0.0, (76, 12, -38), "#145A4A", 0.55,  0.0, 22000.0, 0.0,  0.0, "#C99818"),
        (31.6, "#12164E", "#FF6E1E", 0.65, "#104A3C", "#0B2432", "#06081E", "#189E7A", 0.0150, "#FF6418", 0.0, (76, 12, -38), "#145A4A", 0.55,  0.0, 22000.0, 0.0,  0.0, "#C99818"),
        # [CAM 18] KLAK! Percikan biru-zamrud menyala tajam di poros mesin!
        (32.2, "#10285E", "#38FFE0", 0.92, "#125A4C", "#0B2B3C", "#060A22", "#1EB894", 0.0140, "#FF6418", 0.0, (76, 12, -38), "#1CE0BE", 0.90,  0.0, 26000.0, 4200.0, 0.0, "#D4A820"),
        (34.0, "#12164E", "#FF6E1E", 0.68, "#104A3C", "#0B2432", "#06081E", "#189E7A", 0.0145, "#FF6418", 0.0, (76, 12, -38), "#145A4A", 0.58,  0.0, 22000.0, 0.0,  0.0, "#C99818"),
        (37.9, "#12164E", "#FF6E1E", 0.68, "#104A3C", "#0B2432", "#06081E", "#189E7A", 0.0145, "#FF6418", 0.0, (76, 12, -38), "#145A4A", 0.58,  0.0, 18000.0, 0.0,  0.0, "#C99818"),
        # FASE 3A: KLIMAKS (38.6-51.7s) — Ultra-Low Crimson Sun + Electric Blue Fill + Golden-Crimson Haze!
        (38.6, "#1C3CC6", "#FF7828", 0.62, "#FF6422", "#B8283C", "#2A1460", "#E8562E", 0.0052, "#FF6C2E", 5.2, (78, -6, 152), "#2652E8", 1.05,  0.0,   0.0,   0.0,  0.0, "#F09C14"),
        (51.7, "#1C3CC6", "#FF7828", 0.64, "#FF6422", "#B8283C", "#2A1460", "#E8562E", 0.0050, "#FF6C2E", 5.2, (78, -6, 152), "#2652E8", 1.05,  0.0,   0.0,   0.0, 80.0, "#F09C14"),
        # FASE 3B: FINALE TWILIGHT (52.6-58.0s) — Frozen Violet-Gold Twilight + Crisp Cyan Rim Light!
        (52.6, "#361C78", "#3EF4FF", 0.88, "#F29C58", "#5A2C8E", "#16104C", "#522C82", 0.0026, "#FFC86E", 4.0, (74, -8, 146), "#4C2EA8", 0.95,  0.0,   0.0,   0.0, 320.0, "#E4B824"),
        (58.0, "#361C78", "#3EF4FF", 0.88, "#F29C58", "#5A2C8E", "#16104C", "#522C82", 0.0026, "#FFC86E", 4.0, (74, -8, 146), "#4C2EA8", 0.95,  0.0,   0.0,   0.0, 320.0, "#E4B824"),
    ]

    for row in keyframes:
        (
            t_s, sh_h, rm_h, rm_s, shor, smid, stop, vhex, vden,
            sun_h, sun_e, sun_r, fill_h, fill_e, d_e, f_e, k_e, c_e, p_h,
        ) = row
        fr = sec_to_frame(t_s)
        _kf_color(n_shade, hex_to_linear_rgba(sh_h), fr)
        _kf_color(n_rim, hex_to_linear_rgba(rm_h), fr)
        _kf_float(n_rim_str, rm_s, fr)

        _kf_color(sky_hor.outputs[0], hex_to_linear_rgba(shor), fr)
        _kf_color(sky_mid.outputs[0], hex_to_linear_rgba(smid), fr)
        _kf_color(sky_top.outputs[0], hex_to_linear_rgba(stop), fr)
        _kf_color(vol.inputs["Color"], hex_to_linear_rgba(vhex), fr)
        _kf_float(vol.inputs["Density"], vden, fr)

        _kf_light(sun_main, sun_h, sun_e, fr, sun_r)
        _kf_light(sun_fill, fill_h, fill_e, fr)
        _kf_light(pt_desk, "#FFD47A", d_e, fr)
        _kf_light(pt_furnace, "#FF5812", f_e, fr)
        _kf_light(pt_furnace_rim, "#FF7822", f_e * 0.55, fr)
        _kf_light(pt_klak, "#38FFE6", k_e, fr)
        _kf_light(pt_clock, "#FFDA8E", c_e, fr)

        if bima_parka_rgb is not None:
            _kf_color(bima_parka_rgb.outputs[0], hex_to_linear_rgba(p_h), fr)

    return {
        "sun_main": sun_main,
        "sun_fill": sun_fill,
        "pt_desk": pt_desk,
        "pt_furnace": pt_furnace,
        "pt_klak": pt_klak,
        "pt_clock": pt_clock,
    }
