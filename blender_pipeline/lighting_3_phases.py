"""
Evolusi Pencahayaan 3 Fase (Production Bible Lighting Progression) — LANGIT CERAH & WARNA VIBRANT SEPERTI PREVIEW 1!

PERBAIKAN UTAMA dari temuan render Colab pertama:
  - TIDAK memasang infinite VolumeScatter pada World Output -> Volume (yang membuat langit berubah hitam pekat di EEVEE Next!).
  - Langit 3-stop cerah + awan tipis bergaya kartun + pendar cakrawala langsung di World Surface (`Strength = 2.35`),
    mempertahankan palet langit cerah persis seperti Preview 1:
      * Fase 1 (00:00–00:26): Biru cerah + cakrawala emas hangat (Low Sun) & Cool Blue Shade
      * Fase 2 (00:26–00:38): Deep Indigo + kabut zamrud lokal di gorong-gorong + sorotan tungku oranye
      * Fase 3A (00:38–00:51.8): Langit Crimson-Magenta-Jingga menyala + matahari crimson raksasa + Electric Blue fill
      * Fase 3B (00:51.8–00:58): Frozen Violet-Gold Twilight cerah berkilau + Crisp Cyan Cel Rim Light!
  - Atmospheric Haze (kabut jarak jauh) ditangani bersih oleh Mist Pass di Compositor sehingga langit tidak pernah gelap!
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
    """Bangun World 3-Stop Sky CERAH (bebas infinite volume black-out!) + lampu 3 fase."""
    scene = bpy.context.scene
    col = get_or_create_collection("Lighting_3Phases")

    # ==================== 1. WORLD: LANGIT 3-STOP CERAH + AWAN HALUS (TANPA INFINITE VOLUME!) ====================
    world = scene.world or bpy.data.worlds.new("World_KunciJatuh")
    scene.world = world
    world.use_nodes = True
    # Konfigurasi Mist Pass untuk kabut atmosfer di Compositor (langit tetap 100% cerah!)
    if hasattr(world, "mist_settings"):
        world.mist_settings.start = 10.0
        world.mist_settings.depth = 135.0
        world.mist_settings.falloff = "QUADRATIC"

    wnodes = world.node_tree.nodes
    wlinks = world.node_tree.links
    wnodes.clear()

    w_out = wnodes.new("ShaderNodeOutputWorld")
    w_out.location = (960, 0)

    tex_c = wnodes.new("ShaderNodeTexCoord")
    tex_c.location = (-860, 120)
    sep = wnodes.new("ShaderNodeSeparateXYZ")
    sep.location = (-640, 120)
    wlinks.new(tex_c.outputs["Generated"], sep.inputs["Vector"])

    sky_hor = wnodes.new("ShaderNodeRGB")
    sky_hor.name = "Sky_Horizon"
    sky_hor.location = (-640, -140)
    sky_mid = wnodes.new("ShaderNodeRGB")
    sky_mid.name = "Sky_Mid"
    sky_mid.location = (-640, -320)
    sky_top = wnodes.new("ShaderNodeRGB")
    sky_top.name = "Sky_Top"
    sky_top.location = (-640, -500)

    # Gradasi vertikal halus persis Preview 1 (horizon terang -> mid -> zenith)
    ramp1 = wnodes.new("ShaderNodeMapRange")
    ramp1.inputs["From Min"].default_value = -0.06
    ramp1.inputs["From Max"].default_value = 0.24
    ramp1.location = (-360, 160)
    wlinks.new(sep.outputs["Z"], ramp1.inputs["Value"])

    ramp2 = wnodes.new("ShaderNodeMapRange")
    ramp2.inputs["From Min"].default_value = 0.18
    ramp2.inputs["From Max"].default_value = 0.68
    ramp2.location = (-360, -20)
    wlinks.new(sep.outputs["Z"], ramp2.inputs["Value"])

    mix_hm = wnodes.new("ShaderNodeMix")
    mix_hm.data_type = "RGBA"
    mix_hm.location = (-80, 100)
    wlinks.new(ramp1.outputs["Result"], mix_hm.inputs[0])
    wlinks.new(sky_hor.outputs[0], mix_hm.inputs[6])
    wlinks.new(sky_mid.outputs[0], mix_hm.inputs[7])

    mix_mt = wnodes.new("ShaderNodeMix")
    mix_mt.data_type = "RGBA"
    mix_mt.location = (140, 100)
    wlinks.new(ramp2.outputs["Result"], mix_mt.inputs[0])
    wlinks.new(mix_hm.outputs[2], mix_mt.inputs[6])
    wlinks.new(sky_top.outputs[0], mix_mt.inputs[7])

    # Awan pita tipis (stylized coastal clouds) yang ikut menyala keemasan/violet!
    c_noise = wnodes.new("ShaderNodeTexNoise")
    c_noise.inputs["Scale"].default_value = 3.2
    c_noise.inputs["Detail"].default_value = 5.0
    c_noise.inputs["Roughness"].default_value = 0.52
    c_noise.location = (-360, -320)
    wlinks.new(tex_c.outputs["Generated"], c_noise.inputs["Vector"])

    c_ramp = wnodes.new("ShaderNodeValToRGB")
    c_ramp.location = (-120, -320)
    c_ramp.color_ramp.elements[0].position = 0.56
    c_ramp.color_ramp.elements[0].color = (0.0, 0.0, 0.0, 1.0)
    c_ramp.color_ramp.elements[1].position = 0.78
    c_ramp.color_ramp.elements[1].color = (0.30, 0.30, 0.30, 1.0)
    wlinks.new(c_noise.outputs["Fac"], c_ramp.inputs["Fac"])

    c_band = wnodes.new("ShaderNodeMapRange")
    c_band.inputs["From Min"].default_value = 0.05
    c_band.inputs["From Max"].default_value = 0.28
    c_band.location = (-120, -520)
    wlinks.new(sep.outputs["Z"], c_band.inputs["Value"])

    c_mul = wnodes.new("ShaderNodeMath")
    c_mul.operation = "MULTIPLY"
    c_mul.location = (140, -340)
    wlinks.new(c_ramp.outputs["Color"], c_mul.inputs[0])
    wlinks.new(c_band.outputs["Result"], c_mul.inputs[1])

    mix_cloud = wnodes.new("ShaderNodeMix")
    mix_cloud.data_type = "RGBA"
    mix_cloud.location = (380, 100)
    wlinks.new(c_mul.outputs["Value"], mix_cloud.inputs[0])
    wlinks.new(mix_mt.outputs[2], mix_cloud.inputs[6])
    wlinks.new(sky_hor.outputs[0], mix_cloud.inputs[7])

    # Pisahkan kekuatan langit untuk kamera (cerah cemerlang!) vs penerangan ambient GI
    lp = wnodes.new("ShaderNodeLightPath")
    lp.location = (380, 320)

    bg_cam = wnodes.new("ShaderNodeBackground")
    bg_cam.name = "World_BG_Cam"
    bg_cam.inputs["Strength"].default_value = 1.95
    bg_cam.location = (580, 140)
    wlinks.new(mix_cloud.outputs[2], bg_cam.inputs["Color"])

    bg_gi = wnodes.new("ShaderNodeBackground")
    bg_gi.name = "World_BG_GI"
    bg_gi.inputs["Strength"].default_value = 0.85
    bg_gi.location = (580, -40)
    wlinks.new(mix_cloud.outputs[2], bg_gi.inputs["Color"])

    mix_bg = wnodes.new("ShaderNodeMixShader")
    mix_bg.location = (780, 80)
    wlinks.new(lp.outputs["Is Camera Ray"], mix_bg.inputs["Fac"])
    wlinks.new(bg_gi.outputs["Background"], mix_bg.inputs[1])
    wlinks.new(bg_cam.outputs["Background"], mix_bg.inputs[2])
    wlinks.new(mix_bg.outputs["Shader"], w_out.inputs["Surface"])

    # ==================== 2. LAMPU UTAMA & LAMPU LOKAL PER FASE ====================
    def make_light(name: str, ltype: str, loc=(0, 0, 10), rot=(0, 0, 0), radius: float = 0.5):
        ld = bpy.data.lights.new(name=name + "_Data", type=ltype)
        if ltype == "SUN":
            ld.angle = math.radians(1.4)
        elif ltype == "POINT":
            ld.shadow_soft_size = radius
        lo = bpy.data.objects.new(name, ld)
        lo.location = Vector(loc)
        lo.rotation_euler = Euler(tuple(math.radians(a) for a in rot), "XYZ")
        link_object(lo, col)
        return lo

    sun_main = make_light("Sun_Main_Low", "SUN", loc=(0, 0, 40), rot=(63.1, 0.0, 150.3))
    sun_fill = make_light("Sun_Fill_Sky", "SUN", loc=(0, 0, 40), rot=(36, -18, -30))
    sun_fill.data.use_shadow = False

    pt_desk = make_light("Point_L1_BankerLamp", "POINT", loc=w_to_b(1.55, 26.72, 1.75), radius=0.25)
    pt_furnace = make_light("Point_L4_FurnaceCore", "POINT", loc=w_to_b(0.0, -18.5, 48.2), radius=1.8)
    pt_furnace_rim = make_light("Point_L4_FurnaceRim", "POINT", loc=w_to_b(-3.5, -21.0, 41.5), radius=1.4)
    pt_emerald_fill = make_light("Point_L4_EmeraldFill", "POINT", loc=w_to_b(0.0, -13.5, 37.5), radius=2.4)
    pt_klak = make_light("Point_L4_KlakSpark", "POINT", loc=w_to_b(0.0, -17.0, 42.6), radius=0.35)
    pt_clock = make_light("Point_L6_ClockGlow", "POINT", loc=w_to_b(0.0, 19.2, 114.5), radius=2.2)

    # ==================== 3. KEYFRAME EVOLUSI PENCAHAYAAN 3 FASE (CERAH & VIBRANT!) ====================
    ng = get_or_create_phase_control_group()
    n_shade = ng.nodes["Phase_Shade_RGB"].outputs[0]
    n_rim = ng.nodes["Phase_Rim_RGB"].outputs[0]
    n_rim_str = ng.nodes["Phase_Rim_Strength"].outputs[0]

    # (t, shade, rim, rim_str, sky_hor, sky_mid, sky_top, bg_str, sun_hex, sun_e, sun_rot, fill_hex, fill_e, desk, furn, klak, clk)
    keyframes = [
        # FASE 1A: Bengkel & Pasar — Matahari di luar jendela (+X,+Y,+Z -> cahaya masuk lewat jendela ke meja kerja!)
        (0.0,  "#3E6AD6", "#FFE082", 0.34, "#FFC26B", "#88B6E8", "#2B68C4", 1.85, "#FFD88A", 6.2, (63.1, 0.0, 150.3), "#6E9CF2", 1.8, 140.0, 0.0, 0.0, 0.0),
        (17.5, "#3E6AD6", "#FFE082", 0.36, "#FFC26B", "#88B6E8", "#2B68C4", 1.85, "#FFD88A", 6.2, (63.1, 0.0, 150.3), "#6E9CF2", 1.8,  20.0, 0.0, 0.0, 0.0),
        # FASE 1B: Gang Kafe (18-25.8s) — Sudut matahari lebih menukik agar masuk celah atap gang kafe tanpa menembus tembok!
        (18.5, "#2C52BE", "#FFD470", 0.42, "#FFB85E", "#76A8DE", "#245BB8", 1.80, "#FFD07A", 6.5, (42.3, 0.0, 147.7), "#5482E0", 1.5,   0.0, 0.0, 0.0, 0.0),
        (25.8, "#2C52BE", "#FFD470", 0.42, "#FFB85E", "#76A8DE", "#245BB8", 1.80, "#FFD07A", 6.5, (42.3, 0.0, 147.7), "#5482E0", 1.5,   0.0, 0.0, 0.0, 0.0),
        # FASE 2: STORY TURN (26.1-37.9s) — Deep Indigo + Emerald Haze + Tungku Oranye Terang!
        (26.1, "#1D2878", "#FF7824", 0.72, "#18765C", "#0F384A", "#0A1030", 1.15, "#FF6E1E", 0.0, (42.3, 0.0, 147.7), "#229E82", 1.6,   0.0, 38000.0, 0.0, 0.0),
        (31.6, "#1D2878", "#FF7824", 0.72, "#18765C", "#0F384A", "#0A1030", 1.15, "#FF6E1E", 0.0, (42.3, 0.0, 147.7), "#229E82", 1.6,   0.0, 38000.0, 0.0, 0.0),
        (32.3, "#1C448A", "#46FFE6", 0.96, "#22967C", "#14485E", "#0C163A", 1.35, "#FF6E1E", 0.0, (42.3, 0.0, 147.7), "#32F2D2", 2.2,   0.0, 42000.0, 8500.0, 0.0),
        (34.0, "#1D2878", "#FF7824", 0.74, "#18765C", "#0F384A", "#0A1030", 1.15, "#FF6E1E", 0.0, (42.3, 0.0, 147.7), "#229E82", 1.6,   0.0, 36000.0, 0.0, 0.0),
        (37.9, "#1D2878", "#FF7824", 0.74, "#18765C", "#0F384A", "#0A1030", 1.15, "#FF6E1E", 0.0, (42.3, 0.0, 147.7), "#229E82", 1.6,   0.0, 28000.0, 0.0, 0.0),
        # FASE 3A: KLIMAKS (38.6-51.7s) — Cahaya datang LANGSUNG DARI Matahari Crimson L6_Crimson_Sun_Orb (-30, 29, 192)!
        (38.6, "#3456E8", "#FF8638", 0.62, "#FF782E", "#CE3A54", "#3B2284", 2.05, "#FF7E3C", 6.8, (81.1, 0.0, -160.3), "#4A72FA", 2.1,   0.0, 0.0, 0.0, 0.0),
        (51.7, "#3456E8", "#FF8638", 0.64, "#FF782E", "#CE3A54", "#3B2284", 2.05, "#FF7E3C", 6.8, (81.1, 0.0, -160.3), "#4A72FA", 2.1,   0.0, 0.0, 0.0, 260.0),
        # FASE 3B: FINALE TWILIGHT (52.6-58.0s) — Cahaya twilight selaras dari cakrawala matahari barat (-30, 29, 192)!
        (52.6, "#4E34A8", "#48F6FF", 0.85, "#FFA862", "#7444B8", "#261E76", 2.05, "#FFD278", 5.8, (78.4, 0.0, -158.7), "#6E58D4", 2.2,   0.0, 0.0, 0.0, 950.0),
        (58.0, "#4E34A8", "#48F6FF", 0.85, "#FFA862", "#7444B8", "#261E76", 2.05, "#FFD278", 5.8, (78.4, 0.0, -158.7), "#6E58D4", 2.2,   0.0, 0.0, 0.0, 950.0),
    ]

    for row in keyframes:
        (t_s, sh_h, rm_h, rm_s, shor, smid, stop, bg_s, sun_h, sun_e, sun_r, fill_h, fill_e, d_e, f_e, k_e, c_e) = row
        fr = sec_to_frame(t_s)
        _kf_color(n_shade, hex_to_linear_rgba(sh_h), fr)
        _kf_color(n_rim, hex_to_linear_rgba(rm_h), fr)
        _kf_float(n_rim_str, rm_s, fr)

        _kf_color(sky_hor.outputs[0], hex_to_linear_rgba(shor), fr)
        _kf_color(sky_mid.outputs[0], hex_to_linear_rgba(smid), fr)
        _kf_color(sky_top.outputs[0], hex_to_linear_rgba(stop), fr)
        _kf_float(bg_cam.inputs["Strength"], bg_s, fr)
        _kf_float(bg_gi.inputs["Strength"], bg_s * 0.55, fr)

        _kf_light(sun_main, sun_h, sun_e, fr, sun_r)
        _kf_light(sun_fill, fill_h, fill_e, fr)
        _kf_light(pt_desk, "#FFD880", d_e, fr)
        _kf_light(pt_furnace, "#FF6218", f_e, fr)
        _kf_light(pt_furnace_rim, "#FF8228", f_e * 0.55, fr)
        _kf_light(pt_emerald_fill, "#26E6B2", f_e * 0.22, fr)
        _kf_light(pt_klak, "#42FFE8", k_e, fr)
        _kf_light(pt_clock, "#FFE0A0", c_e, fr)

    return {
        "sun_main": sun_main,
        "sun_fill": sun_fill,
        "pt_desk": pt_desk,
        "pt_furnace": pt_furnace,
        "pt_klak": pt_klak,
        "pt_clock": pt_clock,
    }
