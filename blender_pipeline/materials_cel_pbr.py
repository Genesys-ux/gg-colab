"""
Sistem Material Colorful 3D Cel-Shaded + Realistic Procedural Texture (Blender 4.2 LTS)
untuk "DETIK KE-75" — Bekerja konsisten baik di EEVEE Next maupun Cycles!

Memenuhi aturan wajib `3d-cinematic-animation-director`:
  - Colorful 3D Cel-Shaded Props + Realistic Texture (brushed metal, wet concrete puddles,
    rusted water tower steel, carbon-gold briefcase, sterile hospital vinyl, cotton micro-weave,
    warm golden corridor plaster)
  - Inverted-Hull Dark Ink Outline (`MAT_Ink_Outline`) bebas blokir bayangan
  - NodeGroup `NG_StoryLightingPhase` yang berubah dinamis saat cerita berbelok!
"""
from __future__ import annotations

from typing import Dict, Tuple

import bpy  # type: ignore


def hex_to_linear_rgba(hex_str: str, alpha: float = 1.0) -> Tuple[float, float, float, float]:
    h = hex_str.lstrip("#")
    r = int(h[0:2], 16) / 255.0
    g = int(h[2:4], 16) / 255.0
    b = int(h[4:6], 16) / 255.0

    def s2l(c: float) -> float:
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

    return (s2l(r), s2l(g), s2l(b), alpha)


def _set_in(node, names, val) -> None:
    if isinstance(names, str):
        names = (names,)
    for nm in names:
        sock = node.inputs.get(nm)
        if sock is not None:
            sock.default_value = val
            return


def get_or_create_story_phase_group():
    """NodeGroup global untuk mengontrol nuansa bayangan (Blue Shade) & Rim Light per babak."""
    name = "NG_StoryLightingPhase"
    ng = bpy.data.node_groups.get(name)
    if ng is not None:
        return ng

    ng = bpy.data.node_groups.new(name=name, type="ShaderNodeTree")
    if hasattr(ng, "interface"):
        ng.interface.new_socket(name="Tint_Color", in_out="OUTPUT", socket_type="NodeSocketColor")
        ng.interface.new_socket(name="Rim_Color", in_out="OUTPUT", socket_type="NodeSocketColor")
        ng.interface.new_socket(name="Rim_Strength", in_out="OUTPUT", socket_type="NodeSocketFloat")
    else:
        ng.outputs.new("NodeSocketColor", "Tint_Color")
        ng.outputs.new("NodeSocketColor", "Rim_Color")
        ng.outputs.new("NodeSocketFloat", "Rim_Strength")

    nodes = ng.nodes
    links = ng.links
    out_n = nodes.new("NodeGroupOutput")
    out_n.location = (300, 0)

    n_tint = nodes.new("ShaderNodeRGB")
    n_tint.name = "Story_Tint_RGB"
    n_tint.outputs[0].default_value = hex_to_linear_rgba("#1B4F7A")
    n_tint.location = (0, 120)

    n_rim = nodes.new("ShaderNodeRGB")
    n_rim.name = "Story_Rim_RGB"
    n_rim.outputs[0].default_value = hex_to_linear_rgba("#38D6FF")
    n_rim.location = (0, -40)

    n_str = nodes.new("ShaderNodeValue")
    n_str.name = "Story_Rim_Strength"
    n_str.outputs[0].default_value = 0.36
    n_str.location = (0, -200)

    links.new(n_tint.outputs[0], out_n.inputs["Tint_Color"])
    links.new(n_rim.outputs[0], out_n.inputs["Rim_Color"])
    links.new(n_str.outputs[0], out_n.inputs["Rim_Strength"])
    return ng


def get_or_create_ink_outline_material(color_hex: str = "#14101D") -> "bpy.types.Material":
    """Material garis tinta cel-shade Inverted-Hull yang tajam di EEVEE Next maupun Cycles."""
    name = "MAT_Ink_Outline"
    mat = bpy.data.materials.get(name)
    if mat is not None:
        return mat

    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    mat.use_backface_culling = True
    if hasattr(mat, "use_backface_culling_shadow"):
        mat.use_backface_culling_shadow = True
    if hasattr(mat, "surface_render_method"):
        mat.surface_render_method = "DITHERED"

    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    geom = nodes.new("ShaderNodeNewGeometry")
    geom.location = (-600, 120)
    lp = nodes.new("ShaderNodeLightPath")
    lp.location = (-600, -80)

    inv_bf = nodes.new("ShaderNodeMath")
    inv_bf.operation = "SUBTRACT"
    inv_bf.inputs[0].default_value = 1.0
    inv_bf.location = (-380, 120)
    links.new(geom.outputs["Backfacing"], inv_bf.inputs[1])

    gate = nodes.new("ShaderNodeMath")
    gate.operation = "MULTIPLY"
    gate.location = (-180, 60)
    links.new(inv_bf.outputs["Value"], gate.inputs[0])
    links.new(lp.outputs["Is Camera Ray"], gate.inputs[1])

    transp = nodes.new("ShaderNodeBsdfTransparent")
    transp.location = (-180, -100)
    em = nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = hex_to_linear_rgba(color_hex)
    em.inputs["Strength"].default_value = 1.0
    em.location = (-180, -240)

    mix_s = nodes.new("ShaderNodeMixShader")
    mix_s.location = (80, 0)
    links.new(gate.outputs["Value"], mix_s.inputs["Fac"])
    links.new(transp.outputs["BSDF"], mix_s.inputs[1])
    links.new(em.outputs["Emission"], mix_s.inputs[2])

    out_m = nodes.new("ShaderNodeOutputMaterial")
    out_m.location = (300, 0)
    links.new(mix_s.outputs["Shader"], out_m.inputs["Surface"])
    return mat


def make_cel_pbr_material(
    name: str,
    base_hex: str,
    alt_hex: str,
    roughness: float = 0.45,
    metallic: float = 0.0,
    noise_scale: float = 18.0,
    bump_strength: float = 0.14,
    puddle_wetness: float = 0.0,
    emission_hex: str | None = None,
    emission_strength: float = 0.0,
    alpha: float = 1.0,
) -> "bpy.types.Material":
    """
    Bangun material Cel-Shaded + Realistic Surface Texture (bekerja di EEVEE & Cycles):
      - Variasi permukaan mikro prosedural (goresan logam, beton basah, tenunan katun, kayu)
      - Fresnel Cel Rim Light dinamis terhubung ke `NG_StoryLightingPhase`
      - Puddle mask reflektif tinggi bila `puddle_wetness > 0`
    """
    existing = bpy.data.materials.get(name)
    if existing is not None:
        return existing

    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    if alpha < 0.999 and hasattr(mat, "surface_render_method"):
        mat.surface_render_method = "BLENDED"

    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    tex_c = nodes.new("ShaderNodeTexCoord")
    tex_c.location = (-980, 80)

    noise = nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = float(noise_scale)
    noise.inputs["Detail"].default_value = 6.5
    noise.inputs["Roughness"].default_value = 0.58
    noise.location = (-760, 120)
    links.new(tex_c.outputs["Object"], noise.inputs["Vector"])

    # Stepped cel-texture ramp so surface grain reads crisp & colorful!
    ramp = nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.interpolation = "EASE"
    ramp.color_ramp.elements[0].position = 0.30
    ramp.color_ramp.elements[0].color = hex_to_linear_rgba(alt_hex)
    ramp.color_ramp.elements[1].position = 0.72
    ramp.color_ramp.elements[1].color = hex_to_linear_rgba(base_hex)
    ramp.location = (-520, 180)
    links.new(noise.outputs["Fac"], ramp.inputs["Fac"])

    # Fresnel Cel Rim Accent from Story Lighting Phase
    phase_grp = nodes.new("ShaderNodeGroup")
    phase_grp.node_tree = get_or_create_story_phase_group()
    phase_grp.location = (-520, -220)

    fres = nodes.new("ShaderNodeLayerWeight")
    fres.inputs["Blend"].default_value = 0.26
    fres.location = (-520, -60)

    rim_ramp = nodes.new("ShaderNodeValToRGB")
    rim_ramp.color_ramp.interpolation = "CONSTANT"
    rim_ramp.color_ramp.elements[0].position = 0.0
    rim_ramp.color_ramp.elements[0].color = (0.0, 0.0, 0.0, 1.0)
    rim_ramp.color_ramp.elements[1].position = 0.68
    rim_ramp.color_ramp.elements[1].color = (1.0, 1.0, 1.0, 1.0)
    rim_ramp.location = (-300, -60)
    links.new(fres.outputs["Facing"], rim_ramp.inputs["Fac"])

    rim_mul = nodes.new("ShaderNodeMath")
    rim_mul.operation = "MULTIPLY"
    rim_mul.location = (-80, -140)
    links.new(rim_ramp.outputs["Color"], rim_mul.inputs[0])
    links.new(phase_grp.outputs["Rim_Strength"], rim_mul.inputs[1])

    col_mix = nodes.new("ShaderNodeMix")
    col_mix.data_type = "RGBA"
    col_mix.blend_type = "MIX"
    col_mix.clamp_result = True
    col_mix.location = (-120, 160)
    links.new(rim_mul.outputs["Value"], col_mix.inputs[0])
    links.new(ramp.outputs["Color"], col_mix.inputs[6])
    links.new(phase_grp.outputs["Rim_Color"], col_mix.inputs[7])

    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.location = (180, 120)
    _set_in(bsdf, "Metallic", float(metallic))
    _set_in(bsdf, "Alpha", float(alpha))
    links.new(col_mix.outputs[2], bsdf.inputs["Base Color"])

    if puddle_wetness > 0.01:
        # Wet concrete / wet rubber reflection puddle mask
        p_noise = nodes.new("ShaderNodeTexNoise")
        p_noise.inputs["Scale"].default_value = 3.4
        p_noise.inputs["Detail"].default_value = 4.0
        p_noise.location = (-760, -340)
        links.new(tex_c.outputs["Object"], p_noise.inputs["Vector"])

        p_ramp = nodes.new("ShaderNodeValToRGB")
        p_ramp.color_ramp.elements[0].position = 0.44
        p_ramp.color_ramp.elements[0].color = (0.04, 0.04, 0.04, 1.0)  # Mirror-wet puddle!
        p_ramp.color_ramp.elements[1].position = 0.58
        p_ramp.color_ramp.elements[1].color = (roughness, roughness, roughness, 1.0)
        p_ramp.location = (-460, -380)
        links.new(p_noise.outputs["Fac"], p_ramp.inputs["Fac"])
        links.new(p_ramp.outputs["Color"], bsdf.inputs["Roughness"])
    else:
        _set_in(bsdf, "Roughness", float(roughness))

    if bump_strength > 0.001:
        bump = nodes.new("ShaderNodeBump")
        bump.inputs["Strength"].default_value = float(bump_strength)
        bump.inputs["Distance"].default_value = 0.03
        bump.location = (-120, -320)
        links.new(noise.outputs["Fac"], bump.inputs["Height"])
        links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])

    if emission_hex and emission_strength > 0.0:
        _set_in(bsdf, ("Emission Color", "Emission"), hex_to_linear_rgba(emission_hex))
        _set_in(bsdf, "Emission Strength", float(emission_strength))

    out_m = nodes.new("ShaderNodeOutputMaterial")
    out_m.location = (460, 120)
    links.new(bsdf.outputs["BSDF"], out_m.inputs["Surface"])
    return mat


def make_emissive_material(name: str, hex_col: str, strength: float = 4.0, alpha: float = 1.0) -> "bpy.types.Material":
    existing = bpy.data.materials.get(name)
    if existing is not None:
        return existing
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    if alpha < 0.999 and hasattr(mat, "surface_render_method"):
        mat.surface_render_method = "BLENDED"
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    out_m = nodes.new("ShaderNodeOutputMaterial")
    out_m.location = (340, 0)
    em = nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = hex_to_linear_rgba(hex_col)
    em.inputs["Strength"].default_value = float(strength)
    em.location = (0, 60)
    if alpha < 0.999:
        tr = nodes.new("ShaderNodeBsdfTransparent")
        tr.location = (0, -80)
        mx = nodes.new("ShaderNodeMixShader")
        mx.inputs["Fac"].default_value = float(alpha)
        mx.location = (180, 0)
        links.new(tr.outputs["BSDF"], mx.inputs[1])
        links.new(em.outputs["Emission"], mx.inputs[2])
        links.new(mx.outputs["Shader"], out_m.inputs["Surface"])
    else:
        links.new(em.outputs["Emission"], out_m.inputs["Surface"])
    return mat


def create_material_library() -> Dict[str, "bpy.types.Material"]:
    """Kumpulan lengkap material 6 Lokasi & Hero Props 'DETIK KE-75'."""
    get_or_create_story_phase_group()
    ink = get_or_create_ink_outline_material("#120E1B")

    return {
        "ink": ink,
        # Lokasi 1 & 2: Maglev Express 09
        "maglev_wall": make_cel_pbr_material("MAT_Maglev_Wall", "#2B394E", "#1B2536", roughness=0.34, metallic=0.72, noise_scale=28.0, bump_strength=0.10),
        "maglev_floor": make_cel_pbr_material("MAT_Maglev_Floor", "#1A222E", "#101620", roughness=0.42, metallic=0.15, noise_scale=42.0, puddle_wetness=0.65),
        "maglev_seat": make_cel_pbr_material("MAT_Maglev_Seat", "#23496D", "#16304B", roughness=0.55, noise_scale=22.0),
        "chrome_pole": make_cel_pbr_material("MAT_Chrome_Pole", "#DCE6F2", "#8FA2BA", roughness=0.16, metallic=0.92, noise_scale=35.0, bump_strength=0.04),
        "red_portal_door": make_cel_pbr_material("MAT_Red_Portal_Door", "#E02832", "#99151E", roughness=0.28, metallic=0.45, noise_scale=16.0, emission_hex="#FF2E3B", emission_strength=0.35),
        "silhouette_passenger": make_cel_pbr_material("MAT_Silhouette_Mem", "#192334", "#0E1420", roughness=0.75, alpha=0.82),
        "neon_cyan": make_emissive_material("MAT_Neon_Cyan", "#4CE8FF", strength=5.5),
        "neon_white": make_emissive_material("MAT_Neon_White", "#E8F7FF", strength=4.8),
        "tunnel_streak": make_emissive_material("MAT_Tunnel_Streak", "#1AD2FF", strength=4.2),
        "glitch_screen": make_emissive_material("MAT_Glitch_Screen", "#28F0D8", strength=3.4),

        # Hero Props
        "briefcase_carbon": make_cel_pbr_material("MAT_Briefcase_Carbon", "#1A1B24", "#0E0F15", roughness=0.32, metallic=0.55, noise_scale=55.0, bump_strength=0.16),
        "gold_glow": make_cel_pbr_material("MAT_Gold_Glow", "#FFD454", "#C9921E", roughness=0.15, metallic=0.95, emission_hex="#FFCA3A", emission_strength=2.2),
        "laser_red": make_emissive_material("MAT_Laser_Red", "#FF1E38", strength=8.5, alpha=0.72),
        "scanner_blue": make_emissive_material("MAT_Scanner_Blue", "#2BD9FF", strength=7.5, alpha=0.55),
        "cake_sponge": make_cel_pbr_material("MAT_Cake_Sponge", "#FFF3D6", "#F2CE85", roughness=0.68, noise_scale=30.0),
        "cake_icing": make_cel_pbr_material("MAT_Cake_Icing", "#FF8FA3", "#E05C75", roughness=0.38, noise_scale=14.0),
        "candle_flame": make_emissive_material("MAT_Candle_Flame", "#FFB627", strength=11.0),

        # Lokasi 3 & 4: Apex Tower Rooftop & Sniper Water Tower
        "wet_concrete": make_cel_pbr_material("MAT_Wet_Concrete", "#273040", "#171D29", roughness=0.52, noise_scale=14.0, bump_strength=0.22, puddle_wetness=0.85),
        "helipad_yellow": make_cel_pbr_material("MAT_Helipad_Mark", "#E8B938", "#A87E1A", roughness=0.40, noise_scale=18.0, emission_hex="#F2C138", emission_strength=0.25),
        "rusted_steel": make_cel_pbr_material("MAT_Rusted_Steel", "#6B3D2E", "#3B2420", roughness=0.62, metallic=0.68, noise_scale=20.0, bump_strength=0.26),
        "ac_industrial": make_cel_pbr_material("MAT_AC_Unit", "#49566B", "#2D3646", roughness=0.44, metallic=0.55, noise_scale=18.0),
        "city_skyline": make_cel_pbr_material("MAT_City_Skyline", "#141D2E", "#0B101C", roughness=0.65, emission_hex="#3A7CA5", emission_strength=0.45),
        "rain_drop": make_emissive_material("MAT_Rain_Drop", "#A8E4FF", strength=2.6, alpha=0.65),
        "shatter_shard": make_emissive_material("MAT_Shatter_Shard", "#F2FBFF", strength=6.5, alpha=0.88),
        "beacon_red": make_emissive_material("MAT_Beacon_Red", "#FF2438", strength=6.8),

        # Lokasi 5 & 6: ICU Kamar 404 & Koridor Cahaya Keemasan
        "icu_wall": make_cel_pbr_material("MAT_ICU_Wall", "#DCE6F0", "#B8C9DB", roughness=0.58, noise_scale=12.0, bump_strength=0.05),
        "icu_vinyl_floor": make_cel_pbr_material("MAT_ICU_Floor", "#C5D5E4", "#9EB4C9", roughness=0.24, noise_scale=16.0, bump_strength=0.03),
        "cotton_sheet": make_cel_pbr_material("MAT_Cotton_Sheet", "#F5F8FC", "#D5E0EC", roughness=0.78, noise_scale=48.0, bump_strength=0.14),
        "hospital_bed_frame": make_cel_pbr_material("MAT_Bed_Frame", "#7C8EA3", "#526275", roughness=0.35, metallic=0.65),
        "warm_oak": make_cel_pbr_material("MAT_Warm_Oak", "#9C6B43", "#6B4426", roughness=0.48, noise_scale=24.0, bump_strength=0.14),
        "ekg_screen": make_cel_pbr_material("MAT_EKG_Body", "#151922", "#0C0E14", roughness=0.25, metallic=0.4),
        "ekg_red_line": make_emissive_material("MAT_EKG_Line", "#FF293E", strength=7.2),
        "iv_fluid": make_cel_pbr_material("MAT_IV_Fluid", "#E3F6FF", "#A8DCF5", roughness=0.08, alpha=0.55, emission_hex="#C8F0FF", emission_strength=0.5),
        "lily_white": make_cel_pbr_material("MAT_Lily_Petal", "#FAF6EE", "#DDD4C2", roughness=0.62),
        "lily_stem": make_cel_pbr_material("MAT_Lily_Stem", "#4E7A52", "#315236", roughness=0.65),
        "obs_glass": make_cel_pbr_material("MAT_Obs_Glass", "#D8EEFF", "#9AC4E2", roughness=0.06, metallic=0.15, alpha=0.24),
        "corridor_gold_wall": make_cel_pbr_material("MAT_Corridor_Gold", "#FFE6AE", "#E8BA68", roughness=0.45, emission_hex="#FFD275", emission_strength=0.55),
        "corridor_gold_floor": make_cel_pbr_material("MAT_Corridor_Floor", "#F7D996", "#CFA052", roughness=0.22, metallic=0.18, emission_hex="#FFC864", emission_strength=0.35),
        "godray_cone": make_emissive_material("MAT_GodRay_Cone", "#FFE294", strength=2.4, alpha=0.13),
    }
