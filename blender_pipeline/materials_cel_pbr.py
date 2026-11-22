"""
Studio NPR Cel-Shaded + Realistic PBR Material System untuk Blender 4.2+ EEVEE Next.

Arsitektur Shader:
  1. Global NodeGroup `NG_PhaseLightingControl` (dianimasikan di `lighting_3_phases.py`):
     - `Shade_Color` : Cool Blue (Fase 1) -> Deep Indigo (Fase 2) -> Electric Blue (Fase 3A) -> Frozen Violet (Fase 3B)
     - `Rim_Color`   : Warm Gold (Fase 1) -> Furnace Orange (Fase 2) -> Crimson Gold (Fase 3A) -> Crisp Cyan (Fase 3B)
     - `Rim_Strength`: Intensitas Fresnel Cel Rim Light per fase
  2. Setiap material menggabungkan:
     - `Principled BSDF` bermuatan tekstur PBR asli (Poly Haven CC0 jika ada) atau multi-layer procedural PBR
       (serat kayu retak, cat mengelupas, kuningan tergores, kain tenun kasar, cobblestone basah, bulu micro-fur)
     - `Shader to RGB` -> 3-Band Stepped Cel ColorRamp (bayangan bertingkat tegas + tekstur PBR tetap terbaca!)
     - `Ambient Occlusion` crevice darkening (sudut & lipatan tidak pernah melayang!)
     - `Fresnel Cel Rim Light` tegas mengikuti fase pencahayaan
  3. Material `MAT_Ink_Outline` (Inverted-Hull Backface Culling) untuk subtle dark ink outlines
     yang menerima Depth of Field & Motion Blur EEVEE Next secara native!
"""

from __future__ import annotations

from typing import Dict, Optional, Tuple

import bpy  # type: ignore

from .assets_loader import find_pbr_texture_maps


def hex_to_linear_rgba(hex_str: str, alpha: float = 1.0) -> Tuple[float, float, float, float]:
    h = hex_str.lstrip("#")
    r = int(h[0:2], 16) / 255.0
    g = int(h[2:4], 16) / 255.0
    b = int(h[4:6], 16) / 255.0

    def s2l(c: float) -> float:
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

    return (s2l(r), s2l(g), s2l(b), alpha)


def _new_mix_rgba(nodes, blend_type: str = "MIX", clamp_result: bool = True, loc=(0, 0)):
    """Buat ShaderNodeMix mode RGBA secara aman untuk Blender 4.0–4.4+."""
    n = nodes.new("ShaderNodeMix")
    n.data_type = "RGBA"
    n.blend_type = blend_type
    n.clamp_result = clamp_result
    n.location = loc
    return n


def _set_input(node, names, value) -> None:
    if isinstance(names, str):
        names = (names,)
    for nm in names:
        sock = node.inputs.get(nm)
        if sock is not None:
            sock.default_value = value
            return


def get_or_create_phase_control_group():
    """
    Buat NodeGroup global `NG_PhaseLightingControl` agar seluruh material di 6 lokasi
    otomatis merespons transisi pencahayaan Fase 1 -> Fase 2 -> Fase 3A -> Fase 3B!
    """
    name = "NG_PhaseLightingControl"
    ng = bpy.data.node_groups.get(name)
    if ng is not None:
        return ng

    ng = bpy.data.node_groups.new(name=name, type="ShaderNodeTree")
    # Blender 4.0+ interface API
    if hasattr(ng, "interface"):
        ng.interface.new_socket(name="Shade_Color", in_out="OUTPUT", socket_type="NodeSocketColor")
        ng.interface.new_socket(name="Rim_Color", in_out="OUTPUT", socket_type="NodeSocketColor")
        ng.interface.new_socket(name="Rim_Strength", in_out="OUTPUT", socket_type="NodeSocketFloat")
    else:
        ng.outputs.new("NodeSocketColor", "Shade_Color")
        ng.outputs.new("NodeSocketColor", "Rim_Color")
        ng.outputs.new("NodeSocketFloat", "Rim_Strength")

    nodes = ng.nodes
    links = ng.links
    out_node = nodes.new("NodeGroupOutput")
    out_node.location = (320, 0)

    n_shade = nodes.new("ShaderNodeRGB")
    n_shade.name = "Phase_Shade_RGB"
    n_shade.outputs[0].default_value = hex_to_linear_rgba("#2B529E")
    n_shade.location = (0, 140)

    n_rim = nodes.new("ShaderNodeRGB")
    n_rim.name = "Phase_Rim_RGB"
    n_rim.outputs[0].default_value = hex_to_linear_rgba("#FFD67A")
    n_rim.location = (0, -40)

    n_rim_str = nodes.new("ShaderNodeValue")
    n_rim_str.name = "Phase_Rim_Strength"
    n_rim_str.outputs[0].default_value = 0.42
    n_rim_str.location = (0, -220)

    links.new(n_shade.outputs[0], out_node.inputs["Shade_Color"])
    links.new(n_rim.outputs[0], out_node.inputs["Rim_Color"])
    links.new(n_rim_str.outputs[0], out_node.inputs["Rim_Strength"])
    return ng


def get_or_create_ink_outline_material(color_hex: str = "#161120") -> "bpy.types.Material":
    """
    Material dark ink outline (Inverted-Hull Solidify) yang bekerja 100% IDENTIK di Cycles OptiX & EEVEE Next!
    - Menggunakan `Geometry.Backfacing * LightPath.IsCameraRay` -> hanya terlihat di sisi tepi belakang kamera,
      TIDAK menghalangi cahaya matahari dan TIDAK pernah membuat objek hitam di Cycles!
    """
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
    geom.location = (-660, 140)
    lp = nodes.new("ShaderNodeLightPath")
    lp.location = (-660, -80)

    # Solidify dengan thickness negatif & use_flip_normals=True membuat sisi DEPAN menjadi Backfacing=1
    # dan sisi BELAKANG (pinggiran siluet) menjadi Backfacing=0!
    # Maka ink HARUS tampil saat (1.0 - Backfacing) * IsCameraRay (HANYA tepi siluet luar!).
    inv_bf = nodes.new("ShaderNodeMath")
    inv_bf.operation = "SUBTRACT"
    inv_bf.inputs[0].default_value = 1.0
    inv_bf.location = (-420, 140)
    links.new(geom.outputs["Backfacing"], inv_bf.inputs[1])

    gate = nodes.new("ShaderNodeMath")
    gate.operation = "MULTIPLY"
    gate.location = (-200, 80)
    links.new(inv_bf.outputs["Value"], gate.inputs[0])
    links.new(lp.outputs["Is Camera Ray"], gate.inputs[1])

    transp = nodes.new("ShaderNodeBsdfTransparent")
    transp.location = (-180, -140)

    em = nodes.new("ShaderNodeEmission")
    em.location = (-180, -300)
    em.inputs["Color"].default_value = hex_to_linear_rgba(color_hex)
    em.inputs["Strength"].default_value = 1.0

    mix_sh = nodes.new("ShaderNodeMixShader")
    mix_sh.location = (80, 0)
    links.new(gate.outputs["Value"], mix_sh.inputs["Fac"])
    links.new(transp.outputs["BSDF"], mix_sh.inputs[1])
    links.new(em.outputs["Emission"], mix_sh.inputs[2])

    out_n = nodes.new("ShaderNodeOutputMaterial")
    out_n.location = (320, 0)
    links.new(mix_sh.outputs["Shader"], out_n.inputs["Surface"])
    return mat


def _build_pbr_micro_detail(
    nodes,
    links,
    base_rgba: Tuple[float, float, float, float],
    pbr_kind: str,
    pbr_slot: Optional[str],
    uv_scale: float,
    bump_strength: float,
):
    """
    Bangun cabang PBR (Albedo bertekstur, Roughness, dan Bump Normal) dari file Poly Haven CC0 jika tersedia,
    atau prosedural berlapis berkualitas tinggi untuk setiap jenis permukaan Production Bible.
    """
    tex_coord = nodes.new("ShaderNodeTexCoord")
    tex_coord.location = (-1350, 100)
    mapping = nodes.new("ShaderNodeMapping")
    mapping.location = (-1140, 100)
    mapping.inputs["Scale"].default_value = (uv_scale, uv_scale, uv_scale)
    links.new(tex_coord.outputs["Object"], mapping.inputs["Vector"])

    base_rgb_node = nodes.new("ShaderNodeRGB")
    base_rgb_node.name = "Base_Palette_RGB"
    base_rgb_node.outputs[0].default_value = base_rgba
    base_rgb_node.location = (-920, 420)

    # Cek apakah tekstur gambar PBR CC0 dari Poly Haven tersedia
    img_maps = find_pbr_texture_maps(pbr_slot) if pbr_slot else {}

    albedo_out = base_rgb_node.outputs[0]
    rough_out = None
    normal_out = None

    if img_maps.get("diff"):
        try:
            img_diff = bpy.data.images.load(img_maps["diff"], check_existing=True)
            t_diff = nodes.new("ShaderNodeTexImage")
            t_diff.image = img_diff
            t_diff.projection = "BOX"
            t_diff.projection_blend = 0.25
            t_diff.location = (-920, 180)
            links.new(mapping.outputs["Vector"], t_diff.inputs["Vector"])

            # Campur tekstur PBR realistis dengan palet warna kartun agar palet Production Bible tetap terjaga!
            mix_albedo = _new_mix_rgba(nodes, "MULTIPLY", True, loc=(-620, 300))
            mix_albedo.inputs[0].default_value = 0.58
            links.new(base_rgb_node.outputs[0], mix_albedo.inputs[6])
            links.new(t_diff.outputs["Color"], mix_albedo.inputs[7])
            albedo_out = mix_albedo.outputs[2]
        except Exception:
            pass

    if img_maps.get("rough"):
        try:
            img_r = bpy.data.images.load(img_maps["rough"], check_existing=True)
            img_r.colorspace_settings.name = "Non-Color"
            t_r = nodes.new("ShaderNodeTexImage")
            t_r.image = img_r
            t_r.projection = "BOX"
            t_r.projection_blend = 0.25
            t_r.location = (-920, -100)
            links.new(mapping.outputs["Vector"], t_r.inputs["Vector"])
            rough_out = t_r.outputs["Color"]
        except Exception:
            pass

    if img_maps.get("nor"):
        try:
            img_n = bpy.data.images.load(img_maps["nor"], check_existing=True)
            img_n.colorspace_settings.name = "Non-Color"
            t_n = nodes.new("ShaderNodeTexImage")
            t_n.image = img_n
            t_n.projection = "BOX"
            t_n.projection_blend = 0.25
            t_n.location = (-920, -380)
            links.new(mapping.outputs["Vector"], t_n.inputs["Vector"])
            nmap = nodes.new("ShaderNodeNormalMap")
            nmap.inputs["Strength"].default_value = min(1.0, bump_strength * 2.2)
            nmap.location = (-620, -380)
            links.new(t_n.outputs["Color"], nmap.inputs["Color"])
            normal_out = nmap.outputs["Normal"]
        except Exception:
            pass

    # Jika tidak ada image PBR (atau untuk memperkaya material khusus), bangun prosedural PBR kaya detail!
    if normal_out is None:
        bump_n = nodes.new("ShaderNodeBump")
        bump_n.inputs["Strength"].default_value = bump_strength
        bump_n.inputs["Distance"].default_value = 0.04
        bump_n.location = (-600, -320)

        if pbr_kind == "oak_wood":
            wave = nodes.new("ShaderNodeTexWave")
            wave.wave_type = "BANDS"
            wave.bands_direction = "X"
            wave.inputs["Scale"].default_value = 4.2
            wave.inputs["Distortion"].default_value = 7.5
            wave.inputs["Detail"].default_value = 8.0
            wave.location = (-920, -220)
            links.new(mapping.outputs["Vector"], wave.inputs["Vector"])
            links.new(wave.outputs["Fac"], bump_n.inputs["Height"])

            if not img_maps.get("diff"):
                mix_w = _new_mix_rgba(nodes, "MULTIPLY", True, loc=(-620, 260))
                mix_w.inputs[0].default_value = 0.42
                links.new(base_rgb_node.outputs[0], mix_w.inputs[6])
                ramp_w = nodes.new("ShaderNodeValToRGB")
                ramp_w.location = (-780, 120)
                ramp_w.color_ramp.elements[0].position = 0.15
                ramp_w.color_ramp.elements[0].color = (0.42, 0.30, 0.22, 1.0)
                ramp_w.color_ramp.elements[1].position = 0.85
                ramp_w.color_ramp.elements[1].color = (1.0, 0.94, 0.86, 1.0)
                links.new(wave.outputs["Fac"], ramp_w.inputs["Fac"])
                links.new(ramp_w.outputs["Color"], mix_w.inputs[7])
                albedo_out = mix_w.outputs[2]
            normal_out = bump_n.outputs["Normal"]

        elif pbr_kind == "peeling_plaster":
            noise1 = nodes.new("ShaderNodeTexNoise")
            noise1.inputs["Scale"].default_value = 3.2
            noise1.inputs["Detail"].default_value = 9.0
            noise1.inputs["Roughness"].default_value = 0.68
            noise1.location = (-920, -220)
            links.new(mapping.outputs["Vector"], noise1.inputs["Vector"])
            links.new(noise1.outputs["Fac"], bump_n.inputs["Height"])

            if not img_maps.get("diff"):
                ramp_p = nodes.new("ShaderNodeValToRGB")
                ramp_p.location = (-780, 140)
                ramp_p.color_ramp.elements[0].position = 0.62
                ramp_p.color_ramp.elements[0].color = (0.0, 0.0, 0.0, 1.0)
                ramp_p.color_ramp.elements[1].position = 0.72
                ramp_p.color_ramp.elements[1].color = (1.0, 1.0, 1.0, 1.0)
                links.new(noise1.outputs["Fac"], ramp_p.inputs["Fac"])

                mix_p = _new_mix_rgba(nodes, "MIX", True, loc=(-620, 280))
                links.new(ramp_p.outputs["Color"], mix_p.inputs[0])
                links.new(base_rgb_node.outputs[0], mix_p.inputs[6])
                mix_p.inputs[7].default_value = hex_to_linear_rgba("#6E4632")
                albedo_out = mix_p.outputs[2]
            normal_out = bump_n.outputs["Normal"]

        elif pbr_kind == "scratched_brass":
            noise_s = nodes.new("ShaderNodeTexNoise")
            noise_s.inputs["Scale"].default_value = 18.0
            noise_s.inputs["Detail"].default_value = 10.0
            noise_s.inputs["Roughness"].default_value = 0.72
            noise_s.location = (-920, -220)
            links.new(mapping.outputs["Vector"], noise_s.inputs["Vector"])
            links.new(noise_s.outputs["Fac"], bump_n.inputs["Height"])
            normal_out = bump_n.outputs["Normal"]

        elif pbr_kind == "woven_fabric":
            wx = nodes.new("ShaderNodeTexWave")
            wx.wave_type = "BANDS"
            wx.bands_direction = "X"
            wx.inputs["Scale"].default_value = 26.0
            wx.inputs["Distortion"].default_value = 1.2
            wx.location = (-940, -180)
            links.new(mapping.outputs["Vector"], wx.inputs["Vector"])

            wy = nodes.new("ShaderNodeTexWave")
            wy.wave_type = "BANDS"
            wy.bands_direction = "Y"
            wy.inputs["Scale"].default_value = 26.0
            wy.inputs["Distortion"].default_value = 1.2
            wy.location = (-940, -380)
            links.new(mapping.outputs["Vector"], wy.inputs["Vector"])

            m_weave = nodes.new("ShaderNodeMath")
            m_weave.operation = "MULTIPLY"
            m_weave.location = (-740, -260)
            links.new(wx.outputs["Fac"], m_weave.inputs[0])
            links.new(wy.outputs["Fac"], m_weave.inputs[1])
            links.new(m_weave.outputs["Value"], bump_n.inputs["Height"])
            normal_out = bump_n.outputs["Normal"]

        elif pbr_kind == "wet_cobblestone":
            vor = nodes.new("ShaderNodeTexVoronoi")
            vor.feature = "DISTANCE_TO_EDGE"
            vor.inputs["Scale"].default_value = 4.2
            vor.location = (-920, -240)
            links.new(mapping.outputs["Vector"], vor.inputs["Vector"])

            ramp_c = nodes.new("ShaderNodeValToRGB")
            ramp_c.location = (-760, -240)
            ramp_c.color_ramp.elements[0].position = 0.02
            ramp_c.color_ramp.elements[0].color = (0.0, 0.0, 0.0, 1.0)
            ramp_c.color_ramp.elements[1].position = 0.14
            ramp_c.color_ramp.elements[1].color = (1.0, 1.0, 1.0, 1.0)
            links.new(vor.outputs["Distance"], ramp_c.inputs["Fac"])
            links.new(ramp_c.outputs["Color"], bump_n.inputs["Height"])

            if not img_maps.get("diff"):
                mix_c = _new_mix_rgba(nodes, "MULTIPLY", True, loc=(-620, 280))
                mix_c.inputs[0].default_value = 0.65
                links.new(base_rgb_node.outputs[0], mix_c.inputs[6])
                links.new(ramp_c.outputs["Color"], mix_c.inputs[7])
                albedo_out = mix_c.outputs[2]
            normal_out = bump_n.outputs["Normal"]

        elif pbr_kind == "micro_fur":
            nf = nodes.new("ShaderNodeTexNoise")
            nf.inputs["Scale"].default_value = 42.0
            nf.inputs["Detail"].default_value = 12.0
            nf.inputs["Roughness"].default_value = 0.80
            nf.location = (-920, -220)
            links.new(mapping.outputs["Vector"], nf.inputs["Vector"])
            links.new(nf.outputs["Fac"], bump_n.inputs["Height"])
            normal_out = bump_n.outputs["Normal"]

        elif pbr_kind == "oxidized_copper":
            nox = nodes.new("ShaderNodeTexNoise")
            nox.inputs["Scale"].default_value = 5.5
            nox.inputs["Detail"].default_value = 10.0
            nox.location = (-920, -220)
            links.new(mapping.outputs["Vector"], nox.inputs["Vector"])
            links.new(nox.outputs["Fac"], bump_n.inputs["Height"])

            if not img_maps.get("diff"):
                ramp_ox = nodes.new("ShaderNodeValToRGB")
                ramp_ox.location = (-780, 140)
                ramp_ox.color_ramp.elements[0].position = 0.54
                ramp_ox.color_ramp.elements[0].color = (0.0, 0.0, 0.0, 1.0)
                ramp_ox.color_ramp.elements[1].position = 0.68
                ramp_ox.color_ramp.elements[1].color = (1.0, 1.0, 1.0, 1.0)
                links.new(nox.outputs["Fac"], ramp_ox.inputs["Fac"])

                mix_ox = _new_mix_rgba(nodes, "MIX", True, loc=(-620, 280))
                links.new(ramp_ox.outputs["Color"], mix_ox.inputs[0])
                links.new(base_rgb_node.outputs[0], mix_ox.inputs[6])
                mix_ox.inputs[7].default_value = hex_to_linear_rgba("#248C72")
                albedo_out = mix_ox.outputs[2]
            normal_out = bump_n.outputs["Normal"]

        else:
            nf = nodes.new("ShaderNodeTexNoise")
            nf.inputs["Scale"].default_value = 12.0
            nf.inputs["Detail"].default_value = 6.0
            nf.location = (-920, -220)
            links.new(mapping.outputs["Vector"], nf.inputs["Vector"])
            links.new(nf.outputs["Fac"], bump_n.inputs["Height"])
            normal_out = bump_n.outputs["Normal"]

    # Ambient Occlusion crevice darkening ringan (2 samples -> super cepat di GPU & tidak bikin lag!)
    ao = nodes.new("ShaderNodeAmbientOcclusion")
    ao.samples = 2
    ao.inputs["Distance"].default_value = 0.45
    ao.location = (-600, 520)
    links.new(albedo_out, ao.inputs["Color"])

    ramp_ao = nodes.new("ShaderNodeValToRGB")
    ramp_ao.location = (-400, 520)
    ramp_ao.color_ramp.elements[0].position = 0.15
    ramp_ao.color_ramp.elements[0].color = (0.48, 0.45, 0.55, 1.0)
    ramp_ao.color_ramp.elements[1].position = 0.90
    ramp_ao.color_ramp.elements[1].color = (1.0, 1.0, 1.0, 1.0)
    links.new(ao.outputs["AO"], ramp_ao.inputs["Fac"])

    mix_ao = _new_mix_rgba(nodes, "MULTIPLY", True, loc=(-200, 380))
    mix_ao.inputs[0].default_value = 0.65
    links.new(albedo_out, mix_ao.inputs[6])
    links.new(ramp_ao.outputs["Color"], mix_ao.inputs[7])

    return mix_ao.outputs[2], rough_out, normal_out


def create_cel_pbr_material(
    name: str,
    color_hex: str,
    pbr_kind: str = "painted",
    pbr_slot: Optional[str] = None,
    metallic: float = 0.0,
    roughness: float = 0.52,
    uv_scale: float = 1.0,
    bump_strength: float = 0.22,
    rim_boost: float = 1.0,
    cel_bands: Tuple[float, float, float] = (0.14, 0.44, 0.80),
    render_engine: str = "CYCLES",
) -> "bpy.types.Material":
    """
    Buat material 3D Kartun Stylized + PBR Realistis untuk Blender 4.2+:
      - Mode `CYCLES` (Default Colab Pro L4/A100 OptiX — 150x lebih cepat & kualitas film!):
        Principled BSDF PBR 2K penuh + AO crevice + Fresnel Cel Rim Light per fase + Ink Outlines!
      - Mode `EEVEE`:
        Principled BSDF -> Shader to RGB -> 3-Band Stepped Cel ColorRamp + Rim Light per fase!
    """
    existing = bpy.data.materials.get(name)
    if existing is not None:
        return existing

    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    base_rgba = hex_to_linear_rgba(color_hex)
    albedo_sock, rough_sock, normal_sock = _build_pbr_micro_detail(
        nodes, links, base_rgba, pbr_kind, pbr_slot, uv_scale, bump_strength
    )

    # Cabang Global Phase Control & Fresnel Cel Rim Light (dipakai bersama di Cycles & EEVEE!)
    phase_grp = nodes.new("ShaderNodeGroup")
    phase_grp.node_tree = get_or_create_phase_control_group()
    phase_grp.location = (520, -240)

    lw = nodes.new("ShaderNodeLayerWeight")
    lw.inputs["Blend"].default_value = 0.30
    lw.location = (520, -440)

    ramp_rim = nodes.new("ShaderNodeValToRGB")
    ramp_rim.location = (740, -440)
    ramp_rim.color_ramp.elements[0].position = 0.60
    ramp_rim.color_ramp.elements[0].color = (0.0, 0.0, 0.0, 1.0)
    ramp_rim.color_ramp.elements[1].position = 0.74
    ramp_rim.color_ramp.elements[1].color = (1.0, 1.0, 1.0, 1.0)
    links.new(lw.outputs["Facing"], ramp_rim.inputs["Fac"])

    rim_str_mul = nodes.new("ShaderNodeMath")
    rim_str_mul.operation = "MULTIPLY"
    rim_str_mul.location = (940, -360)
    links.new(phase_grp.outputs["Rim_Strength"], rim_str_mul.inputs[0])
    rim_str_mul.inputs[1].default_value = rim_boost * (0.55 if render_engine == "CYCLES" else 1.0)

    rim_gate = nodes.new("ShaderNodeMath")
    rim_gate.operation = "MULTIPLY"
    rim_gate.location = (1140, -360)
    links.new(ramp_rim.outputs["Color"], rim_gate.inputs[0])
    links.new(rim_str_mul.outputs["Value"], rim_gate.inputs[1])

    # ==================== MODE CYCLES OPTIX (STYLIZED PIXAR/SPIDER-VERSE PBR!) ====================
    if render_engine.upper() == "CYCLES":
        bsdf = nodes.new("ShaderNodeBsdfPrincipled")
        bsdf.location = (1380, 120)
        links.new(albedo_sock, bsdf.inputs["Base Color"])
        _set_input(bsdf, "Metallic", metallic * 0.85)
        _set_input(bsdf, "Roughness", roughness)
        _set_input(bsdf, ("Specular IOR Level", "Specular"), 0.55 if metallic < 0.5 else 0.88)
        if rough_sock is not None:
            links.new(rough_sock, bsdf.inputs["Roughness"])
        if normal_sock is not None:
            links.new(normal_sock, bsdf.inputs["Normal"])
        # Fresnel Rim Light tegas mengikuti Fase 1 Gold / Fase 2 Furnace / Fase 3A Crimson / Fase 3B Cyan!
        em_col_sock = bsdf.inputs.get("Emission Color") or bsdf.inputs.get("Emission")
        if em_col_sock is not None:
            links.new(phase_grp.outputs["Rim_Color"], em_col_sock)
        em_str_sock = bsdf.inputs.get("Emission Strength")
        if em_str_sock is not None:
            links.new(rim_gate.outputs["Value"], em_str_sock)

        out_n = nodes.new("ShaderNodeOutputMaterial")
        out_n.location = (1720, 120)
        links.new(bsdf.outputs["BSDF"], out_n.inputs["Surface"])
        return mat

    # ==================== MODE EEVEE NEXT (3-BAND STEPPED CEL-SHADING + PBR!) ====================
    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.location = (40, 120)
    _set_input(bsdf, "Base Color", (0.95, 0.95, 0.95, 1.0))
    _set_input(bsdf, "Metallic", metallic * 0.45)
    _set_input(bsdf, "Roughness", roughness)
    _set_input(bsdf, ("Specular IOR Level", "Specular"), 0.55 if metallic < 0.5 else 0.85)
    if rough_sock is not None:
        links.new(rough_sock, bsdf.inputs["Roughness"])
    if normal_sock is not None:
        links.new(normal_sock, bsdf.inputs["Normal"])

    s2rgb = nodes.new("ShaderNodeShaderToRGB")
    s2rgb.location = (340, 120)
    links.new(bsdf.outputs["BSDF"], s2rgb.inputs["Shader"])

    rgb2bw = nodes.new("ShaderNodeRGBToBW")
    rgb2bw.location = (540, 160)
    links.new(s2rgb.outputs["Color"], rgb2bw.inputs["Color"])

    ramp = nodes.new("ShaderNodeValToRGB")
    ramp.location = (740, 180)
    cr = ramp.color_ramp
    cr.interpolation = "LINEAR"
    b0, b1, b2 = cel_bands
    cr.elements[0].position = max(0.02, b0 - 0.03)
    cr.elements[0].color = (0.0, 0.0, 0.0, 1.0)
    cr.elements[1].position = min(0.95, b0 + 0.03)
    cr.elements[1].color = (0.48, 0.48, 0.48, 1.0)
    e2 = cr.elements.new(min(0.96, b1 - 0.03))
    e2.color = (0.50, 0.50, 0.50, 1.0)
    e3 = cr.elements.new(min(0.97, b1 + 0.03))
    e3.color = (0.94, 0.94, 0.94, 1.0)
    e4 = cr.elements.new(min(0.98, b2))
    e4.color = (1.0, 1.0, 1.0, 1.0)
    links.new(rgb2bw.outputs["Val"], ramp.inputs["Fac"])

    shade_mul = _new_mix_rgba(nodes, "MULTIPLY", True, loc=(760, -60))
    shade_mul.inputs[0].default_value = 0.72
    links.new(albedo_sock, shade_mul.inputs[6])
    links.new(phase_grp.outputs["Shade_Color"], shade_mul.inputs[7])

    shade_lift = _new_mix_rgba(nodes, "ADD", True, loc=(920, -60))
    shade_lift.inputs[0].default_value = 0.20
    links.new(shade_mul.outputs[2], shade_lift.inputs[6])
    links.new(albedo_sock, shade_lift.inputs[7])

    lit_mul = _new_mix_rgba(nodes, "MULTIPLY", False, loc=(820, 360))
    lit_mul.inputs[0].default_value = 0.34
    links.new(albedo_sock, lit_mul.inputs[6])
    links.new(s2rgb.outputs["Color"], lit_mul.inputs[7])

    lit_boost = _new_mix_rgba(nodes, "ADD", False, loc=(960, 360))
    lit_boost.inputs[0].default_value = 0.22
    links.new(lit_mul.outputs[2], lit_boost.inputs[6])
    links.new(albedo_sock, lit_boost.inputs[7])

    cel_mix = _new_mix_rgba(nodes, "MIX", False, loc=(1140, 180))
    links.new(ramp.outputs["Color"], cel_mix.inputs[0])
    links.new(shade_lift.outputs[2], cel_mix.inputs[6])
    links.new(lit_boost.outputs[2], cel_mix.inputs[7])

    spec_add = cel_mix.outputs[2]
    if metallic > 0.25 or roughness < 0.35:
        ramp_sp = nodes.new("ShaderNodeValToRGB")
        ramp_sp.location = (740, 440)
        ramp_sp.color_ramp.elements[0].position = 0.78
        ramp_sp.color_ramp.elements[0].color = (0.0, 0.0, 0.0, 1.0)
        ramp_sp.color_ramp.elements[1].position = 0.85
        ramp_sp.color_ramp.elements[1].color = (1.0, 1.0, 1.0, 1.0)
        links.new(rgb2bw.outputs["Val"], ramp_sp.inputs["Fac"])

        mix_sp = _new_mix_rgba(nodes, "ADD", False, loc=(1280, 260))
        mix_sp.inputs[0].default_value = 0.55 if metallic > 0.5 else 0.32
        links.new(cel_mix.outputs[2], mix_sp.inputs[6])
        links.new(ramp_sp.outputs["Color"], mix_sp.inputs[7])
        spec_add = mix_sp.outputs[2]

    final_add = _new_mix_rgba(nodes, "ADD", False, loc=(1500, 120))
    links.new(rim_gate.outputs["Value"], final_add.inputs[0])
    links.new(spec_add, final_add.inputs[6])
    links.new(phase_grp.outputs["Rim_Color"], final_add.inputs[7])

    em_final = nodes.new("ShaderNodeEmission")
    em_final.inputs["Strength"].default_value = 1.0
    em_final.location = (1720, 120)
    links.new(final_add.outputs[2], em_final.inputs["Color"])

    out_n = nodes.new("ShaderNodeOutputMaterial")
    out_n.location = (1940, 120)
    links.new(em_final.outputs["Emission"], out_n.inputs["Surface"])
    return mat


def create_emissive_material(name: str, color_hex: str, strength: float = 4.0) -> "bpy.types.Material":
    existing = bpy.data.materials.get(name)
    if existing is not None:
        return existing
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    out_n = nodes.new("ShaderNodeOutputMaterial")
    out_n.location = (260, 0)
    em = nodes.new("ShaderNodeEmission")
    em.location = (0, 0)
    em.inputs["Color"].default_value = hex_to_linear_rgba(color_hex)
    em.inputs["Strength"].default_value = strength
    links.new(em.outputs[0], out_n.inputs["Surface"])
    return mat


def create_dusty_glass_material(name: str, tint_hex: str = "#CBEBF4", alpha: float = 0.32) -> "bpy.types.Material":
    """Kaca berdebu transparan berkilau Fresnel untuk toples pegas, jendela trem, & lensa kacamata Bima."""
    existing = bpy.data.materials.get(name)
    if existing is not None:
        return existing
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    if hasattr(mat, "surface_render_method"):
        mat.surface_render_method = "DITHERED"
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.location = (0, 0)
    _set_input(bsdf, "Base Color", hex_to_linear_rgba(tint_hex))
    _set_input(bsdf, "Roughness", 0.14)
    _set_input(bsdf, "Alpha", alpha)
    _set_input(bsdf, ("Specular IOR Level", "Specular"), 0.92)
    out_n = nodes.new("ShaderNodeOutputMaterial")
    out_n.location = (300, 0)
    links.new(bsdf.outputs["BSDF"], out_n.inputs["Surface"])
    return mat


def create_soft_cloud_material(name: str, color_hex: str, density_alpha: float = 0.55, glow: float = 0.45) -> "bpy.types.Material":
    """
    Material awan partikel 3D lembut & bertekstur kabut (3D Noise * Facing^2.4 * IsCameraRay)
    sehingga uap zamrud & awan bubuk kunyit terlihat seperti kepulan asap/debu lembut (BUKAN bola padat!).
    """
    existing = bpy.data.materials.get(name)
    if existing is not None:
        return existing
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    if hasattr(mat, "surface_render_method"):
        mat.surface_render_method = "BLENDED"
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    lw = nodes.new("ShaderNodeLayerWeight")
    lw.inputs["Blend"].default_value = 0.35
    lw.location = (-820, 40)

    inv = nodes.new("ShaderNodeMath")
    inv.operation = "SUBTRACT"
    inv.inputs[0].default_value = 1.0
    inv.use_clamp = True
    inv.location = (-620, 40)
    links.new(lw.outputs["Facing"], inv.inputs[1])

    # Jatuhan tepi lembut (^2.4) agar tidak ada tepi bola tajam!
    pw = nodes.new("ShaderNodeMath")
    pw.operation = "POWER"
    pw.inputs[1].default_value = 2.4
    pw.use_clamp = True
    pw.location = (-440, 40)
    links.new(inv.outputs["Value"], pw.inputs[0])

    # Noise 3D untuk tekstur gumpalan uap / bubuk organik
    tc = nodes.new("ShaderNodeTexCoord")
    tc.location = (-820, -220)
    ns = nodes.new("ShaderNodeTexNoise")
    ns.inputs["Scale"].default_value = 3.8
    ns.inputs["Detail"].default_value = 6.0
    ns.inputs["Roughness"].default_value = 0.65
    ns.location = (-620, -220)
    links.new(tc.outputs["Object"], ns.inputs["Vector"])

    mul_n = nodes.new("ShaderNodeMath")
    mul_n.operation = "MULTIPLY"
    mul_n.use_clamp = True
    mul_n.location = (-240, -40)
    links.new(pw.outputs["Value"], mul_n.inputs[0])
    links.new(ns.outputs["Fac"], mul_n.inputs[1])

    mul_d = nodes.new("ShaderNodeMath")
    mul_d.operation = "MULTIPLY"
    mul_d.inputs[1].default_value = density_alpha * 0.65
    mul_d.use_clamp = True
    mul_d.location = (-60, -40)
    links.new(mul_n.outputs["Value"], mul_d.inputs[0])

    lp = nodes.new("ShaderNodeLightPath")
    lp.location = (-240, -260)
    cam_only = nodes.new("ShaderNodeMath")
    cam_only.operation = "MULTIPLY"
    cam_only.use_clamp = True
    cam_only.location = (120, -100)
    links.new(mul_d.outputs["Value"], cam_only.inputs[0])
    links.new(lp.outputs["Is Camera Ray"], cam_only.inputs[1])

    transp = nodes.new("ShaderNodeBsdfTransparent")
    transp.location = (120, 180)
    em = nodes.new("ShaderNodeEmission")
    em.location = (120, 40)
    em.inputs["Color"].default_value = hex_to_linear_rgba(color_hex)
    em.inputs["Strength"].default_value = 1.0 + glow

    mix_sh = nodes.new("ShaderNodeMixShader")
    mix_sh.location = (360, 80)
    links.new(cam_only.outputs["Value"], mix_sh.inputs["Fac"])
    links.new(transp.outputs["BSDF"], mix_sh.inputs[1])
    links.new(em.outputs["Emission"], mix_sh.inputs[2])

    out_n = nodes.new("ShaderNodeOutputMaterial")
    out_n.location = (580, 80)
    links.new(mix_sh.outputs["Shader"], out_n.inputs["Surface"])
    return mat


def create_sunbeam_material(name: str, color_hex: str, intensity: float = 0.24, glow: float = 1.8) -> "bpy.types.Material":
    """
    Material Cinematic Volumetric Sunlight Beam (God Ray) super cepat di Cycles OPTIX:
      - Tepi radial lembut via (1 - Facing)^3.0 (nol tepi kerucut keras!)
      - Pudar memanjang lembut dari sumber cahaya ke ujung sinar via Generated.Z
      - Hanya terlihat pada Camera Ray (nol bayangan palsu & nol beban GI bounce!)
    """
    existing = bpy.data.materials.get(name)
    if existing is not None:
        return existing
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    if hasattr(mat, "surface_render_method"):
        mat.surface_render_method = "BLENDED"
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    lw = nodes.new("ShaderNodeLayerWeight")
    lw.inputs["Blend"].default_value = 0.42
    lw.location = (-860, 140)
    inv_f = nodes.new("ShaderNodeMath")
    inv_f.operation = "SUBTRACT"
    inv_f.inputs[0].default_value = 1.0
    inv_f.use_clamp = True
    inv_f.location = (-660, 140)
    links.new(lw.outputs["Facing"], inv_f.inputs[1])

    edge_pw = nodes.new("ShaderNodeMath")
    edge_pw.operation = "POWER"
    edge_pw.inputs[1].default_value = 2.8
    edge_pw.use_clamp = True
    edge_pw.location = (-460, 140)
    links.new(inv_f.outputs["Value"], edge_pw.inputs[0])

    # Pudar halus sepanjang batang sinar (terang dekat sumber atas Z=1 -> pudar habis di ujung Z=0)
    tc = nodes.new("ShaderNodeTexCoord")
    tc.location = (-860, -140)
    sep = nodes.new("ShaderNodeSeparateXYZ")
    sep.location = (-660, -140)
    links.new(tc.outputs["Generated"], sep.inputs["Vector"])

    # Ramp longitudinal lembut (pudar di kedua ujung agar tidak terpotong tajam)
    l_ramp = nodes.new("ShaderNodeValToRGB")
    l_ramp.location = (-460, -140)
    cr = l_ramp.color_ramp
    cr.elements[0].position = 0.0
    cr.elements[0].color = (0.0, 0.0, 0.0, 1.0)
    cr.elements[1].position = 0.82
    cr.elements[1].color = (1.0, 1.0, 1.0, 1.0)
    e_top = cr.elements.new(1.0)
    e_top.color = (0.15, 0.15, 0.15, 1.0)
    links.new(sep.outputs["Z"], l_ramp.inputs["Fac"])

    mul_1 = nodes.new("ShaderNodeMath")
    mul_1.operation = "MULTIPLY"
    mul_1.use_clamp = True
    mul_1.location = (-220, 40)
    links.new(edge_pw.outputs["Value"], mul_1.inputs[0])
    links.new(l_ramp.outputs["Color"], mul_1.inputs[1])

    mul_2 = nodes.new("ShaderNodeMath")
    mul_2.operation = "MULTIPLY"
    mul_2.inputs[1].default_value = intensity
    mul_2.use_clamp = True
    mul_2.location = (-40, 40)
    links.new(mul_1.outputs["Value"], mul_2.inputs[0])

    lp = nodes.new("ShaderNodeLightPath")
    lp.location = (-220, -220)
    cam_gate = nodes.new("ShaderNodeMath")
    cam_gate.operation = "MULTIPLY"
    cam_gate.use_clamp = True
    cam_gate.location = (140, -20)
    links.new(mul_2.outputs["Value"], cam_gate.inputs[0])
    links.new(lp.outputs["Is Camera Ray"], cam_gate.inputs[1])

    transp = nodes.new("ShaderNodeBsdfTransparent")
    transp.location = (140, 200)
    em = nodes.new("ShaderNodeEmission")
    em.location = (140, 80)
    em.inputs["Color"].default_value = hex_to_linear_rgba(color_hex)
    em.inputs["Strength"].default_value = glow

    mix_sh = nodes.new("ShaderNodeMixShader")
    mix_sh.location = (380, 100)
    links.new(cam_gate.outputs["Value"], mix_sh.inputs["Fac"])
    links.new(transp.outputs["BSDF"], mix_sh.inputs[1])
    links.new(em.outputs["Emission"], mix_sh.inputs[2])

    out_n = nodes.new("ShaderNodeOutputMaterial")
    out_n.location = (600, 100)
    links.new(mix_sh.outputs["Shader"], out_n.inputs["Surface"])
    return mat


def create_material_library(render_engine: str = "CYCLES") -> Dict[str, "bpy.types.Material"]:
    """Bangun pustaka lengkap material Stylized PBR / Cel-Shaded untuk seluruh 6 lokasi & cast."""
    get_or_create_phase_control_group()
    eng = render_engine.upper()

    def mcel(*args, **kwargs):
        kwargs["render_engine"] = eng
        return create_cel_pbr_material(*args, **kwargs)

    lib: Dict[str, "bpy.types.Material"] = {
        "ink": get_or_create_ink_outline_material("#15101F"),
        # --- Lingkungan PBR + Stylized/Cel ---
        "oak_wood": mcel("MAT_Oak_Wood", "#8F5A2B", "oak_wood", "oak_wood", 0.0, 0.56, 1.4, 0.28, 0.85),
        "oak_dark": mcel("MAT_Oak_Dark", "#543218", "oak_wood", "oak_wood", 0.0, 0.62, 1.2, 0.30, 0.70),
        "plaster_warm": mcel("MAT_Plaster_Warm", "#D8C5A8", "peeling_plaster", "peeling_plaster", 0.0, 0.78, 0.7, 0.24, 0.65),
        "plaster_terracotta": mcel("MAT_Plaster_Terracotta", "#D67757", "peeling_plaster", "peeling_plaster", 0.0, 0.76, 0.6, 0.24, 0.75),
        "plaster_teal": mcel("MAT_Plaster_Teal", "#538A90", "peeling_plaster", "peeling_plaster", 0.0, 0.72, 0.8, 0.26, 0.75),
        "plaster_ochre": mcel("MAT_Plaster_Ochre", "#DFB36E", "peeling_plaster", "peeling_plaster", 0.0, 0.76, 0.6, 0.24, 0.72),
        "plaster_coral": mcel("MAT_Plaster_Coral", "#C95A4E", "peeling_plaster", "peeling_plaster", 0.0, 0.75, 0.6, 0.24, 0.75),
        "plaster_mint": mcel("MAT_Plaster_Mint", "#5AC4A8", "peeling_plaster", "peeling_plaster", 0.0, 0.72, 0.8, 0.22, 0.75),
        "tower_stone": mcel("MAT_Tower_Stone", "#5A556E", "peeling_plaster", "peeling_plaster", 0.0, 0.80, 0.5, 0.28, 1.05),
        "vault_stone": mcel("MAT_Vault_Stone", "#242A48", "wet_cobblestone", "cobblestone", 0.0, 0.65, 0.5, 0.32, 1.10),
        "cobble_wet": mcel("MAT_Cobble_Wet", "#586274", "wet_cobblestone", "cobblestone", 0.0, 0.22, 1.2, 0.34, 1.05),
        "stone_step": mcel("MAT_Stone_Step", "#B2A490", "wet_cobblestone", "cobblestone", 0.0, 0.70, 0.9, 0.26, 0.70),
        "brass_gold": mcel("MAT_Brass_Gold", "#E0AA28", "scratched_brass", None, 0.85, 0.26, 2.5, 0.18, 1.25),
        "brass_dark": mcel("MAT_Brass_Dark", "#8E621C", "scratched_brass", None, 0.82, 0.34, 2.2, 0.22, 1.10),
        "copper_ox": mcel("MAT_Copper_Ox", "#357266", "oxidized_copper", "oxidized_metal", 0.72, 0.42, 1.2, 0.28, 1.20),
        "iron_dark": mcel("MAT_Iron_Dark", "#252B38", "oxidized_copper", "oxidized_metal", 0.78, 0.44, 1.5, 0.26, 1.15),
        "steel_bright": mcel("MAT_Steel_Bright", "#8E9CAD", "scratched_brass", None, 0.88, 0.24, 2.5, 0.16, 1.15),
        "rust_grate": mcel("MAT_Rust_Grate", "#5E3624", "oxidized_copper", "oxidized_metal", 0.65, 0.54, 2.0, 0.32, 0.95),
        "porcelain": mcel("MAT_Porcelain", "#FAF5EC", "painted", None, 0.0, 0.16, 2.0, 0.06, 0.85),
        "tea_liquid": mcel("MAT_Tea_Liquid", "#7C421C", "painted", None, 0.0, 0.10, 2.0, 0.04, 0.60),
        "burlap": mcel("MAT_Burlap", "#C4A476", "woven_fabric", "woven_fabric", 0.0, 0.88, 3.0, 0.34, 0.70),
        "canopy_red": mcel("MAT_Canopy_Red", "#D83028", "woven_fabric", "woven_fabric", 0.0, 0.82, 2.5, 0.26, 0.90),
        "canopy_cream": mcel("MAT_Canopy_Cream", "#F7EEE0", "woven_fabric", "woven_fabric", 0.0, 0.82, 2.5, 0.24, 0.80),
        "canopy_teal": mcel("MAT_Canopy_Teal", "#1C9E9A", "woven_fabric", "woven_fabric", 0.0, 0.82, 2.5, 0.26, 0.85),
        "canopy_ochre": mcel("MAT_Canopy_Ochre", "#C67E20", "woven_fabric", "woven_fabric", 0.0, 0.82, 2.5, 0.26, 0.85),
        "canopy_plum": mcel("MAT_Canopy_Plum", "#8E2D5A", "woven_fabric", "woven_fabric", 0.0, 0.82, 2.5, 0.26, 0.85),
        "bistro_blue": mcel("MAT_Bistro_Blue", "#3E98DC", "painted", None, 0.20, 0.34, 2.0, 0.12, 0.90),
        "tram_crimson": mcel("MAT_Tram_Crimson", "#B82220", "painted", None, 0.25, 0.26, 1.8, 0.14, 1.25),
        "tram_cream": mcel("MAT_Tram_Cream", "#F2E5C8", "painted", None, 0.08, 0.32, 1.8, 0.12, 1.05),
        "water_sea": mcel("MAT_Water_Sea", "#18466C", "wet_cobblestone", None, 0.0, 0.12, 0.4, 0.18, 1.15),
        "prop_red": mcel("MAT_Prop_Red", "#DE3428", "painted", None, 0.0, 0.32, 2.0, 0.10, 0.90),
        "prop_orange": mcel("MAT_Prop_Orange", "#F28218", "painted", None, 0.0, 0.38, 2.0, 0.14, 0.90),
        "prop_green": mcel("MAT_Prop_Green", "#268C48", "painted", None, 0.0, 0.40, 2.0, 0.14, 0.85),
        "prop_magenta": mcel("MAT_Prop_Magenta", "#D82874", "painted", None, 0.0, 0.48, 2.0, 0.16, 0.90),
        "prop_blue": mcel("MAT_Prop_Blue", "#247CE0", "painted", None, 0.0, 0.34, 2.0, 0.10, 0.90),
        "terracotta_pot": mcel("MAT_Terracotta_Pot", "#B65232", "peeling_plaster", None, 0.0, 0.76, 2.4, 0.26, 0.85),
        "moss_wet": mcel("MAT_Moss_Wet", "#248052", "micro_fur", None, 0.0, 0.55, 2.2, 0.30, 0.95),
        "turmeric_pile": mcel("MAT_Turmeric_Pile", "#F2B614", "woven_fabric", None, 0.0, 0.92, 4.0, 0.30, 0.85),
        "chili_pile": mcel("MAT_Chili_Pile", "#D6261E", "woven_fabric", None, 0.0, 0.92, 4.0, 0.30, 0.85),
        "clock_dial": mcel("MAT_Clock_Dial", "#FAF2DF", "painted", None, 0.0, 0.24, 1.0, 0.08, 0.95),
        # --- Referensi Arsitektur Mediterania, Trem Lisbon, Menara Venesia & Botani Bougainvillea ---
        "terracotta_roof": mcel("MAT_Terracotta_Roof", "#C65A34", "peeling_plaster", "peeling_plaster", 0.0, 0.72, 1.6, 0.30, 0.90),
        "limestone_trim": mcel("MAT_Limestone_Trim", "#ECE4D4", "peeling_plaster", "peeling_plaster", 0.0, 0.74, 1.2, 0.20, 0.85),
        "lapis_blue": mcel("MAT_Lapis_Clock_Blue", "#1D448E", "peeling_plaster", None, 0.12, 0.34, 1.5, 0.14, 1.15),
        "shutter_green": mcel("MAT_Shutter_Green", "#2E7864", "oak_wood", "oak_wood", 0.0, 0.64, 2.2, 0.24, 0.85),
        "shutter_blue": mcel("MAT_Shutter_Blue", "#34729E", "oak_wood", "oak_wood", 0.0, 0.64, 2.2, 0.24, 0.85),
        "boug_bark": mcel("MAT_Boug_Bark", "#6A5442", "oak_wood", None, 0.0, 0.88, 3.5, 0.36, 0.65),
        "boug_leaf": mcel("MAT_Boug_Leaf", "#2B7A3E", "painted", None, 0.0, 0.38, 3.0, 0.14, 0.95),
        "boug_bract": mcel("MAT_Boug_Bract_Magenta", "#E02878", "woven_fabric", None, 0.0, 0.62, 4.0, 0.16, 1.20),
        "boug_flower_cream": mcel("MAT_Boug_Flower_Cream", "#FFF4CC", "painted", None, 0.0, 0.45, 2.0, 0.04, 0.85),
        "soil_dark": mcel("MAT_Soil_Dark", "#3B2A1E", "wet_cobblestone", None, 0.0, 0.95, 5.0, 0.40, 0.30),
        "tram_varnished_wood": mcel("MAT_Tram_Varnished_Wood", "#7E441E", "oak_wood", "oak_wood", 0.0, 0.24, 2.0, 0.18, 0.95),
        # --- Glass & Emissives ---
        "glass_dusty": create_dusty_glass_material("MAT_Glass_Dusty", "#D0EEF6", 0.34),
        "glass_lamp_green": create_dusty_glass_material("MAT_Glass_Lamp_Green", "#1B8A4E", 0.84),
        "emissive_lamp": create_emissive_material("MAT_Emissive_Lamp", "#FFE69C", 5.5),
        "emissive_furnace": create_emissive_material("MAT_Emissive_Furnace", "#FF5A12", 12.0),
        "emissive_sun_crimson": create_emissive_material("MAT_Emissive_Sun_Crimson", "#FF6828", 16.0),
        "emissive_spark_cyan": create_emissive_material("MAT_Emissive_Spark_Cyan", "#48FFE4", 18.0),
        "emissive_spark_silver": create_emissive_material("MAT_Emissive_Spark_Silver", "#D6F2FF", 14.0),
        "emissive_lighthouse": create_emissive_material("MAT_Emissive_Lighthouse", "#FFF2A4", 10.0),
        "black_void": create_emissive_material("MAT_Black_Void", "#040308", 0.0),
        # --- Soft 3D Particle Clouds & Cinematic Sunlight Beams ---
        "fx_turmeric": create_soft_cloud_material("MAT_FX_Turmeric", "#F8BE18", 0.72, 0.45),
        "fx_chili": create_soft_cloud_material("MAT_FX_Chili", "#E03824", 0.64, 0.25),
        "fx_emerald_steam": create_soft_cloud_material("MAT_FX_Emerald_Steam", "#2AE2A4", 0.48, 0.95),
        "fx_gold_dust": create_soft_cloud_material("MAT_FX_Gold_Dust", "#FFE89A", 0.78, 1.8),
        "fx_valley_mist": create_soft_cloud_material("MAT_FX_Valley_Mist", "#F6E8D8", 0.36, 0.55),
        "beam_low_sun": create_sunbeam_material("MAT_Beam_LowSun", "#FFE296", 0.24, 2.2),
        "beam_furnace": create_sunbeam_material("MAT_Beam_Furnace", "#FF7E30", 0.22, 2.4),
        "beam_crimson": create_sunbeam_material("MAT_Beam_Crimson", "#FF8C46", 0.24, 2.4),
        "beam_twilight": create_sunbeam_material("MAT_Beam_Twilight", "#8EEAFF", 0.20, 2.1),
        # --- Perbukitan Pesisir Mediterania Berlapis (Background) ---
        "hill_olive": mcel("MAT_Hill_Olive", "#5A7A4A", "peeling_plaster", None, 0.0, 0.88, 0.15, 0.28, 0.65),
        "hill_terracotta": mcel("MAT_Hill_Terracotta", "#8E7A56", "peeling_plaster", None, 0.0, 0.90, 0.12, 0.28, 0.60),
        "hill_distant": mcel("MAT_Hill_Distant_Mist", "#627A9E", "peeling_plaster", None, 0.0, 0.92, 0.08, 0.18, 0.50),
        "cypress_green": mcel("MAT_Cypress_Green", "#265838", "micro_fur", None, 0.0, 0.82, 2.0, 0.24, 0.60),
        # --- BIMA & CAST MATERIALS ---
        "bima_skin": mcel("MAT_Bima_Skin", "#F2BE96", "painted", None, 0.0, 0.56, 3.0, 0.05, 0.90),
        "bima_hair": mcel("MAT_Bima_Hair", "#3E261A", "micro_fur", None, 0.0, 0.48, 3.0, 0.14, 1.05),
        "bima_parka": mcel("MAT_Bima_Parka_Saffron", "#F2B705", "woven_fabric", "woven_fabric", 0.0, 0.78, 3.2, 0.22, 1.25),
        "bima_scarf": mcel("MAT_Bima_Scarf_Terracotta", "#C84B31", "woven_fabric", "woven_fabric", 0.0, 0.84, 3.5, 0.24, 1.15),
        "bima_navy": mcel("MAT_Bima_Cargo_Navy", "#2B3A55", "woven_fabric", "woven_fabric", 0.0, 0.82, 3.0, 0.22, 0.95),
        "bima_leather": mcel("MAT_Bima_Leather", "#5A341C", "oak_wood", None, 0.0, 0.44, 3.5, 0.18, 0.95),
        "bima_laces": mcel("MAT_Bima_Laces_Orange", "#FF6A14", "woven_fabric", None, 0.0, 0.70, 4.0, 0.12, 1.0),
        "bima_smudge": mcel("MAT_Bima_Oil_Smudge", "#242228", "painted", None, 0.0, 0.50, 2.0, 0.05, 0.30),
        "eye_white": mcel("MAT_Eye_White", "#FAF8F4", "painted", None, 0.0, 0.12, 1.0, 0.01, 0.35),
        "eye_dark": mcel("MAT_Eye_Dark", "#16121C", "painted", None, 0.0, 0.08, 1.0, 0.01, 0.25),
        "mouth_inside": mcel("MAT_Mouth_Inside", "#8C2232", "painted", None, 0.0, 0.60, 1.0, 0.02, 0.20),
        "oren_fur": mcel("MAT_Oren_Fur", "#E67E22", "micro_fur", None, 0.0, 0.72, 4.0, 0.28, 1.45),
        "oren_stripe": mcel("MAT_Oren_Stripe", "#A84A10", "micro_fur", None, 0.0, 0.76, 4.0, 0.28, 1.25),
        "oren_belly": mcel("MAT_Oren_Belly", "#F5E6CA", "micro_fur", None, 0.0, 0.78, 4.0, 0.26, 1.30),
        "oren_eye_olive": mcel("MAT_Oren_Eye_Olive", "#8AA832", "painted", None, 0.0, 0.10, 1.0, 0.02, 0.60),
        "oren_nose_pink": mcel("MAT_Oren_Nose_Pink", "#E28B92", "painted", None, 0.0, 0.62, 4.0, 0.12, 0.75),
        "oren_collar_teal": mcel("MAT_Oren_Collar_Teal", "#4F9DA6", "woven_fabric", "woven_fabric", 0.0, 0.84, 5.0, 0.26, 1.05),
        "oren_bell_copper": mcel("MAT_Oren_Bell_Copper", "#C87438", "scratched_brass", None, 0.84, 0.30, 4.0, 0.18, 1.30),
        "hero_gold_key": mcel("MAT_Hero_Golden_Key", "#F0BE32", "scratched_brass", None, 0.92, 0.20, 4.0, 0.14, 1.55),
        "hero_silver_key": mcel("MAT_Hero_Silver_Key", "#D6E4F0", "scratched_brass", None, 0.94, 0.18, 4.5, 0.12, 1.65),
        "pedagang_shirt": mcel("MAT_Pedagang_Shirt", "#C44536", "woven_fabric", "woven_fabric", 0.0, 0.84, 3.0, 0.22, 0.95),
        "pedagang_hat": mcel("MAT_Pedagang_Hat", "#D4B47C", "woven_fabric", "woven_fabric", 0.0, 0.86, 4.0, 0.30, 0.90),
        "penumpang_coat": mcel("MAT_Penumpang_Coat", "#3F5E4E", "woven_fabric", "woven_fabric", 0.0, 0.80, 3.0, 0.24, 1.05),
        "penumpang_beret": mcel("MAT_Penumpang_Beret", "#7B283C", "woven_fabric", None, 0.0, 0.84, 3.0, 0.20, 1.05),
        "penumpang_scarf": mcel("MAT_Penumpang_Scarf", "#2E7D8C", "woven_fabric", None, 0.0, 0.84, 3.0, 0.22, 1.05),
        "seagull_white": mcel("MAT_Seagull_White", "#F4F6FA", "micro_fur", None, 0.0, 0.62, 2.0, 0.10, 1.30),
        "seagull_wingtip": mcel("MAT_Seagull_Wingtip", "#2C3848", "micro_fur", None, 0.0, 0.64, 2.0, 0.10, 1.15),
    }
    return lib
