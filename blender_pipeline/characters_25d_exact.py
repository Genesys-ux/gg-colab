"""
Integrasi Karakter & Hero Props 100% IDENTIK DENGAN PREVIEW PERTAMA ke dalam Dunia 3D Blender EEVEE Next!
Menggunakan seluruh kelas karakter RIG TERBUKA asli dari folder `characters/`:
  - BimaHeroCharacter (Bima + 4 fase lighting PDF + saku robek + jambul + syal + loupe)
  - OrenCharacter ("Oren" kucing kampung + paw pads + cakar + telinga sobek V)
  - GoldenKeyProp & SilverKeyProp
  - Pedagang Rempah & Penumpang Trem

Setiap karakter dirender resolusi tinggi (PNG RGBA transparan) dan ditempatkan pada bidang 3D depth-tested
ber-alpha-cutout (cast shadow nyata, 3D occlusion nyata, Depth of Field & Motion Blur EEVEE Next!) dengan
orientasi cylindrical world-up agar tidak pernah terbalik ke bawah tanah saat 360° barrel roll / inverted skim!
"""

from __future__ import annotations

import math
import os
from typing import Dict, List, Optional, Tuple

import bmesh  # type: ignore
import bpy  # type: ignore
from mathutils import Matrix, Vector  # type: ignore

from .camera_28_moves import (
    clamp,
    eval_camera_world,
    eval_golden_key_world,
    eval_tram_z_fwd,
    exp_ease_in_out,
    lerp,
    smoothstep,
)
from .config import OUTPUT_DIR, frame_to_sec, w_to_b
from .mesh_utils import get_or_create_collection, link_object

SPRITE_DISK_DIR = os.path.join(OUTPUT_DIR, "blender_sprites_exact")


def _lighting_phase_at(t: float) -> str:
    if t < 26.0:
        return "phase1"
    if t < 38.0:
        return "phase2"
    if t < 51.8:
        return "phase3_crimson"
    return "phase3_twilight"


def _camera_relative_yaw_deg(
    actor_pos_w: Tuple[float, float, float],
    actor_facing_deg: float,
    cam_pos_w: Tuple[float, float, float],
) -> float:
    """Hitung sudut putar karakter relatif terhadap posisi kamera 3D (0=depan, 180=belakang)."""
    dx = cam_pos_w[0] - actor_pos_w[0]
    dz = cam_pos_w[2] - actor_pos_w[2]
    cam_ang = math.degrees(math.atan2(dx, dz))
    return (cam_ang - actor_facing_deg) % 360.0


def _create_cutout_plane(name: str, anchor_bottom: bool, collection) -> Tuple["bpy.types.Object", "bpy.types.ShaderNodeTexImage"]:
    """Buat quad 3D ber-UV tepat (0..1) + shader Alpha-Cutout Emission EEVEE Next."""
    bm = bmesh.new()
    z0, z1 = (0.0, 1.0) if anchor_bottom else (-0.5, 0.5)
    v0 = bm.verts.new((-0.5, 0.0, z0))
    v1 = bm.verts.new((0.5, 0.0, z0))
    v2 = bm.verts.new((0.5, 0.0, z1))
    v3 = bm.verts.new((-0.5, 0.0, z1))
    face = bm.faces.new((v0, v1, v2, v3))
    uv_layer = bm.loops.layers.uv.new("UVMap")
    uvs = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]
    for loop, uv in zip(face.loops, uvs):
        loop[uv_layer].uv = uv

    mesh = bpy.data.meshes.new(name + "_Mesh")
    bm.normal_update()
    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new(name, mesh)
    link_object(obj, collection)

    mat = bpy.data.materials.new(name=f"MAT_{name}")
    mat.use_nodes = True
    if hasattr(mat, "surface_render_method"):
        mat.surface_render_method = "DITHERED"
    if hasattr(mat, "use_backface_culling"):
        mat.use_backface_culling = False

    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    tex = nodes.new("ShaderNodeTexImage")
    tex.name = "Sprite_Tex"
    tex.extension = "CLIP"
    tex.location = (-520, 80)

    # Alpha Cutout tegas (> 0.42) supaya garis ink tajam & tidak ada halo blur!
    gt = nodes.new("ShaderNodeMath")
    gt.operation = "GREATER_THAN"
    gt.inputs[1].default_value = 0.42
    gt.location = (-200, -140)
    links.new(tex.outputs["Alpha"], gt.inputs[0])

    transp = nodes.new("ShaderNodeBsdfTransparent")
    transp.location = (-160, 220)

    em = nodes.new("ShaderNodeEmission")
    em.inputs["Strength"].default_value = 1.06
    em.location = (-160, 40)
    links.new(tex.outputs["Color"], em.inputs["Color"])

    mix_sh = nodes.new("ShaderNodeMixShader")
    mix_sh.location = (120, 80)
    links.new(gt.outputs["Value"], mix_sh.inputs["Fac"])
    links.new(transp.outputs["BSDF"], mix_sh.inputs[1])
    links.new(em.outputs["Emission"], mix_sh.inputs[2])

    out_n = nodes.new("ShaderNodeOutputMaterial")
    out_n.location = (360, 80)
    links.new(mix_sh.outputs["Shader"], out_n.inputs["Surface"])

    obj.data.materials.append(mat)
    return obj, tex


class ExactCharacterCastManager:
    """
    Mengelola seluruh aktor 2.5D asli (Bima, Oren, Kunci Emas/Perak, 3 Pedagang, 4 Penumpang)
    di dalam dunia 3D Blender EEVEE Next dengan desain 100% IDENTIK seperti Preview Pertama!
    """

    def __init__(self, char_scale: float = 3.0, prop_scale: float = 3.2) -> None:
        self.char_scale = char_scale
        self.prop_scale = prop_scale
        self._sprite_cache = None
        self._disk_cache: Dict[str, str] = {}
        self._bpy_img_cache: Dict[str, "bpy.types.Image"] = {}
        self.actors: Dict[str, Tuple["bpy.types.Object", "bpy.types.ShaderNodeTexImage", bool]] = {}
        os.makedirs(SPRITE_DISK_DIR, exist_ok=True)

    def _ensure_sprite_cache(self):
        if self._sprite_cache is None:
            from engine3d.sprite_cache import SpriteCache

            self._sprite_cache = SpriteCache(char_scale=self.char_scale, prop_scale=self.prop_scale)
        return self._sprite_cache

    def build_actor_planes(self) -> None:
        col = get_or_create_collection("Characters_Exact_25D")
        specs = [
            ("Actor_Bima", True),
            ("Actor_Oren", True),
            ("Actor_GoldenKey", False),
            ("Actor_SilverKey", False),
            ("Actor_Pedagang_0", True),
            ("Actor_Pedagang_1", True),
            ("Actor_Pedagang_2", True),
            ("Actor_Penumpang_0", True),
            ("Actor_Penumpang_1", True),
            ("Actor_Penumpang_2", True),
            ("Actor_Penumpang_3", True),
        ]
        for nm, anchor_b in specs:
            obj, tex = _create_cutout_plane(nm, anchor_b, col)
            obj.hide_render = True
            obj.hide_viewport = True
            self.actors[nm] = (obj, tex, anchor_b)

    def _assign_pil_sprite(self, tex_node, pil_img, cache_key: str) -> float:
        """Simpan sprite RGBA ke cache disk & pasang ke Image Texture Blender. Kembalikan aspect (w/h)."""
        bpy_img = self._bpy_img_cache.get(cache_key)
        if bpy_img is None:
            fp = self._disk_cache.get(cache_key)
            if fp is None or not os.path.exists(fp):
                safe_name = "".join(c if (c.isalnum() or c in "_-") else "_" for c in cache_key)
                fp = os.path.join(SPRITE_DISK_DIR, f"{safe_name}.png")
                pil_img.save(fp, format="PNG")
                self._disk_cache[cache_key] = fp
            bpy_img = bpy.data.images.load(fp, check_existing=True)
            if hasattr(bpy_img, "colorspace_settings"):
                bpy_img.colorspace_settings.name = "sRGB"
            self._bpy_img_cache[cache_key] = bpy_img
        tex_node.image = bpy_img
        return pil_img.width / float(max(1, pil_img.height))

    def _place_actor(
        self,
        name: str,
        pos_w: Tuple[float, float, float],
        height_m: float,
        aspect: float,
        cam_pos_b: Vector,
        cam_fwd_b: Vector,
        cam_right_b: Vector,
        cam_up_b: Vector,
        roll_deg: float = 0.0,
    ) -> None:
        obj, _, anchor_b = self.actors[name]
        obj.hide_render = False
        obj.hide_viewport = False
        pos_b = Vector(w_to_b(*pos_w))
        world_up = Vector((0.0, 0.0, 1.0))

        if anchor_b:
            horiz = Vector((pos_b.x - cam_pos_b.x, pos_b.y - cam_pos_b.y, 0.0))
            if horiz.length < 1e-4:
                horiz = Vector((cam_fwd_b.x, cam_fwd_b.y, 0.0))
            f_vec = horiz.normalized()
            base_r = f_vec.cross(world_up).normalized()
            base_u = world_up
        else:
            f_vec = cam_fwd_b
            base_r = cam_right_b
            base_u = cam_up_b

        rrad = math.radians(roll_deg)
        cr, sr = math.cos(rrad), math.sin(rrad)
        r_vec = base_r * cr + base_u * sr
        u_vec = -base_r * sr + base_u * cr

        rot_mat = Matrix((
            (r_vec.x, f_vec.x, u_vec.x),
            (r_vec.y, f_vec.y, u_vec.y),
            (r_vec.z, f_vec.z, u_vec.z),
        ))
        obj.rotation_mode = "QUATERNION"
        obj.rotation_quaternion = rot_mat.to_quaternion()
        obj.location = pos_b
        obj.scale = Vector((height_m * aspect, 1.0, height_m))

    def _hide_actor(self, name: str) -> None:
        obj, _, _ = self.actors[name]
        obj.hide_render = True
        obj.hide_viewport = True

    def update_for_frame(self, frame: int, quantize_deg: float = 5.0) -> None:
        """Perbarui posisi, ekspresi, sudut kamera, & sprite RGBA seluruh aktor asli untuk frame ke-`frame`."""
        from characters import HumanoidRig, KeyPropRig, OrenRig

        t = frame_to_sec(frame)
        phase = _lighting_phase_at(t)
        tram_z = eval_tram_z_fwd(t)
        cam_spec = eval_camera_world(t)
        sprites = self._ensure_sprite_cache()

        cam_pos_b = Vector(w_to_b(*cam_spec.eye_w))
        cam_tgt_b = Vector(w_to_b(*cam_spec.tgt_w))
        world_up = Vector((0.0, 0.0, 1.0))
        cam_fwd_b = (cam_tgt_b - cam_pos_b).normalized()
        up_ref = world_up if abs(cam_fwd_b.dot(world_up)) < 0.992 else Vector((0.0, 1.0, 0.0))
        cam_r0 = cam_fwd_b.cross(up_ref).normalized()
        cam_u0 = cam_r0.cross(cam_fwd_b).normalized()
        rrad_c = math.radians(cam_spec.roll_deg)
        ccr, csr = math.cos(rrad_c), math.sin(rrad_c)
        cam_right_b = cam_r0 * ccr + cam_u0 * csr
        cam_up_b = -cam_r0 * csr + cam_u0 * ccr

        def q_ang(deg: float) -> float:
            return round((deg % 360.0) / quantize_deg) * quantize_deg

        # ==================== 1. KUNCI EMAS ====================
        if t < 56.2:
            kp, k_yaw, k_roll = eval_golden_key_world(t)
            k_rig = KeyPropRig(
                yaw_deg=q_ang(k_yaw),
                roll_deg=round(k_roll / 6.0) * 6.0,
                sun_glow=(t < 10.0 or t > 41.0),
                lighting_phase=phase,  # type: ignore[arg-type]
            )
            k_tag = f"gold_{int(k_rig.yaw_deg)}_{int(k_rig.roll_deg)}_{int(k_rig.sun_glow)}_{phase}"
            k_img, _ = sprites.render_golden_key(k_rig, cache_tag=k_tag)
            asp = self._assign_pil_sprite(self.actors["Actor_GoldenKey"][1], k_img, k_tag)
            k_h = 0.72 if (31.4 <= t <= 34.0) else (0.44 if t < 5.0 else 0.56)
            self._place_actor("Actor_GoldenKey", kp, k_h, asp, cam_pos_b, cam_fwd_b, cam_right_b, cam_up_b)
        else:
            self._hide_actor("Actor_GoldenKey")

        # ==================== 2. KUNCI PERAK ([CAM 27]-[CAM 28]) ====================
        if t >= 55.4:
            u_s = clamp((t - 55.4) / 2.6)
            sp = (lerp(-0.44, 0.0, u_s), lerp(16.12, 12.2, u_s * u_s), lerp(115.48, 117.6, u_s))
            s_rig = KeyPropRig(yaw_deg=q_ang(18.0 + u_s * 240.0), roll_deg=round((26.0 + u_s * 160.0) / 6.0) * 6.0)
            s_tag = f"silver_{int(s_rig.yaw_deg)}_{int(s_rig.roll_deg)}"
            s_img, _ = sprites.render_silver_key(s_rig, cache_tag=s_tag)
            asp = self._assign_pil_sprite(self.actors["Actor_SilverKey"][1], s_img, s_tag)
            self._place_actor("Actor_SilverKey", sp, 0.56, asp, cam_pos_b, cam_fwd_b, cam_right_b, cam_up_b)
        else:
            self._hide_actor("Actor_SilverKey")

        # ==================== 3. BIMA (100% DESAIN ASLI PREVIEW 1 + RIG TERBUKA!) ====================
        bima_pos = None
        bima_facing = 180.0
        bima_rig = None
        bima_anim = "static"
        bima_roll = 0.0
        bima_tag = f"bima_f{frame}"

        if t < 8.5:
            bima_pos = (-0.08, 25.35, 1.85)
            bima_facing = 180.0
            bima_rig = HumanoidRig(
                eyes="panic" if t > 1.2 else "shocked",
                eyebrows="worried",
                mouth="open_yell",
                sweat_drop=True,
                eye_gaze_x=0.35,
                eye_gaze_y=0.25,
                right_hand_target=(88, 192, 42),
                left_hand_target=(-68, 224, 30),
                scarf_sway=-12.0,
                jambul_sway=-8.0,
            )
            bima_tag = f"bima_loc1_{int(t > 1.2)}_{phase}"
        elif 11.2 <= t < 18.2:
            if t < 14.6:
                u = (t - 11.2) / 3.4
                bima_pos = (lerp(-0.4, 0.1, u), lerp(18.0, 15.2, u) + abs(math.sin(u * math.pi * 2)) * 1.4, lerp(10.6, 15.4, u))
                bima_anim = "jump"
                bima_rig = HumanoidRig(eyes="focused", eyebrows="angry", mouth="grit_teeth", scarf_sway=-28.0, jambul_sway=10.0)
            else:
                u = (t - 14.6) / 3.6
                bima_pos = (lerp(0.1, 0.3, u), lerp(12.2, 5.4, u), lerp(16.0, 26.8, u))
                bima_anim = "run"
                bima_rig = HumanoidRig(eyes="shocked", eyebrows="worried", mouth="open_yell", sweat_drop=True, scarf_sway=-24.0)
            bima_facing = 0.0
            bima_tag = f"bima_loc2_{bima_anim}_{frame % 12}_{phase}"
        elif 18.2 <= t < 25.2:
            u = clamp((t - 18.2) / 6.5)
            bima_pos = (lerp(0.2, -0.15, u), 5.05, lerp(28.5, 39.2, u))
            bima_facing = 0.0
            if t >= 22.8:
                bima_roll = -18.0
                bima_rig = HumanoidRig(
                    torso_lean_z=0.16,
                    eyes="panic",
                    eyebrows="worried",
                    mouth="grit_teeth",
                    sweat_drop=True,
                    right_hand_target=(95, 200, 44),
                    left_hand_target=(-64, 245, 22),
                    scarf_sway=-34.0,
                )
                bima_tag = f"bima_slide_{phase}"
            else:
                bima_anim = "run"
                bima_rig = HumanoidRig(eyes="focused", eyebrows="angry", mouth="grit_teeth", scarf_sway=-26.0)
                bima_tag = f"bima_loc3run_{frame % 12}_{phase}"
        elif 33.8 <= t < 38.2:
            u = (t - 33.8) / 4.4
            bima_pos = (-0.9, lerp(-16.0, 9.8, u), lerp(50.0, 61.8, clamp(u * 1.4)))
            bima_facing = 180.0
            bima_roll = math.sin(u * 8.0) * 16.0
            bima_rig = HumanoidRig(
                eyes="asymmetric",
                eyebrows="raised",
                mouth="open_yell",
                sweat_drop=True,
                right_hand_target=(86, 154, 34),
                left_hand_target=(-84, 158, 34),
                scarf_sway=28.0,
                jambul_sway=14.0,
            )
            bima_tag = f"bima_chimney_{phase}"
        elif 40.6 <= t < 49.2:
            if t < 46.2:
                u = (t - 40.6) / 5.6
                bima_pos = (0.0, 13.38, tram_z + lerp(-4.4, 4.6, u))
                bima_facing = 0.0
                bima_anim = "run"
                bima_rig = HumanoidRig(eyes="focused", eyebrows="angry", mouth="grit_teeth", scarf_sway=-36.0, jambul_sway=-12.0)
                bima_tag = f"bima_tramrun_{frame % 12}_{phase}"
            else:
                u = exp_ease_in_out((t - 46.2) / 2.8, 4.5)
                bima_pos = (0.0, 14.5 + math.sin(u * math.pi) * 4.4, lerp(tram_z + 5.2, 110.5, u))
                bima_facing = -115.0
                bima_roll = lerp(-10.0, 14.0, u)
                bima_rig = HumanoidRig(
                    pelvis_y=-24.0,
                    head_bob_y=-26.0,
                    jump_height=38.0,
                    torso_lean_z=0.12,
                    eyes="focused",
                    eyebrows="raised",
                    mouth="open_yell",
                    right_hand_target=(96, 158, 42),
                    left_hand_target=(-74, 198, 22),
                    left_foot_target=(-26, 404, -22),
                    right_foot_target=(38, 412, 24),
                    scarf_sway=-38.0,
                    jambul_sway=12.0,
                )
                bima_tag = f"bima_leap_{phase}"
        elif t >= 49.2:
            bima_pos = (-0.15, 15.42, 115.85)
            bima_facing = 0.0 if t < 53.0 else 180.0
            if t < 52.2:
                bima_rig = HumanoidRig(
                    eyes="focused",
                    eyebrows="raised",
                    mouth="grit_teeth",
                    right_hand_target=(82, 165, 42),
                    left_hand_target=(-52, 235, 24),
                    scarf_sway=-14.0,
                )
                bima_tag = f"bima_turnkey_{phase}"
            else:
                bima_rig = HumanoidRig(
                    eyes="happy",
                    eyebrows="happy",
                    mouth="happy_open",
                    right_hand_target=(16, 246, 44),
                    left_hand_target=(-52, 280, 20),
                    silver_key_peek=(54.2 <= t <= 56.6),
                    thread_sway=round(math.sin(t * 6.0) * 3.5, 1),
                    scarf_sway=round(math.sin(t * 2.5) * 6.0, 1),
                )
                bima_tag = f"bima_happy_{int(54.2 <= t <= 56.6)}_{phase}"

        if bima_pos is not None and bima_rig is not None:
            rel_yaw = q_ang(_camera_relative_yaw_deg(bima_pos, bima_facing, cam_spec.eye_w))
            bima_rig.angle = rel_yaw
            full_tag = f"{bima_tag}_y{int(rel_yaw)}"
            b_img, _ = sprites.render_bima(bima_rig, lighting_phase=phase, animation=bima_anim, frame=frame, cache_tag=full_tag)
            asp = self._assign_pil_sprite(self.actors["Actor_Bima"][1], b_img, full_tag)
            self._place_actor("Actor_Bima", bima_pos, 1.65, asp, cam_pos_b, cam_fwd_b, cam_right_b, cam_up_b, roll_deg=bima_roll)
        else:
            self._hide_actor("Actor_Bima")

        # ==================== 4. OREN (100% DESAIN ASLI PREVIEW 1!) ====================
        if 17.5 <= t <= 25.5:
            oren_pos = (-0.82, 5.02, 36.85)
            oren_yaw = q_ang(_camera_relative_yaw_deg(oren_pos, 155.0, cam_spec.eye_w))
            slap_amt = round(clamp((t - 20.3) / 0.7) if t < 22.4 else clamp(1.0 - (t - 22.4) / 0.8), 1)
            o_rig = OrenRig(
                angle=oren_yaw,
                body_lean=-0.07 * slap_amt,
                eyelid_level=0.56,
                gaze_x=0.42,
                mouth_style="smug",
                right_paw_raised=slap_amt,
                show_paw_pads=(slap_amt > 0.35),
                claws_out=slap_amt * 0.9,
                tail_sway=round(math.sin(t * 3.2) * 18.0 + slap_amt * 12.0, 0),
                bell_sway=round(slap_amt * 6.0, 0),
            )
            o_tag = f"oren_y{int(oren_yaw)}_s{int(slap_amt*10)}_t{int(o_rig.tail_sway)}"
            o_img, _ = sprites.render_oren(o_rig, cache_tag=o_tag)
            asp = self._assign_pil_sprite(self.actors["Actor_Oren"][1], o_img, o_tag)
            self._place_actor("Actor_Oren", oren_pos, 0.82, asp, cam_pos_b, cam_fwd_b, cam_right_b, cam_up_b)
        else:
            self._hide_actor("Actor_Oren")

        # ==================== 5. FIGURAN PASAR (Pedagang Rempah — DESAIN ASLI PREVIEW 1!) ====================
        if 8.5 <= t <= 18.5:
            merchants = [
                ((-0.98, 12.0, 17.6), 25.0, -18.0 if t > 14.8 else 0.0),
                ((1.12, 12.0, 17.8), -35.0, 20.0 if t > 14.9 else 0.0),
                ((-2.4, 14.2, 12.0), 40.0, 0.0),
            ]
            for mi, (mp, mface, mroll) in enumerate(merchants):
                myaw = q_ang(_camera_relative_yaw_deg(mp, mface, cam_spec.eye_w))
                panicking = (t > 14.6)
                mrig = HumanoidRig(
                    angle=myaw,
                    pose="panic" if panicking else "ready",
                    eyes="shocked" if panicking else "chill",
                    eyebrows="worried" if panicking else "happy",
                    mouth="open_yell" if panicking else "smirk",
                    sweat_drop=panicking,
                    hat_lift_y=12.0 if panicking else 0.0,
                    hat_tilt=-14.0 if panicking else 0.0,
                )
                m_tag = f"merch_{mi}_y{int(myaw)}_p{int(panicking)}"
                m_img, _ = sprites.render_pedagang(mrig, cache_tag=m_tag)
                asp = self._assign_pil_sprite(self.actors[f"Actor_Pedagang_{mi}"][1], m_img, m_tag)
                self._place_actor(f"Actor_Pedagang_{mi}", mp, 1.82, asp, cam_pos_b, cam_fwd_b, cam_right_b, cam_up_b, roll_deg=mroll)
        else:
            for mi in range(3):
                self._hide_actor(f"Actor_Pedagang_{mi}")

        # ==================== 6. FIGURAN STASIUN (Penumpang Trem — DESAIN ASLI PREVIEW 1!) ====================
        if 37.8 <= t <= 50.0:
            passengers = [
                ((-3.2, 10.05, 76.0), 80.0),
                ((3.3, 10.05, 83.5), -85.0),
                ((-3.3, 10.05, 96.5), 115.0),
                ((3.3, 10.05, 99.5), -110.0),
            ]
            for pi, (pp, pface) in enumerate(passengers):
                pyaw = q_ang(_camera_relative_yaw_deg(pp, pface, cam_spec.eye_w))
                prig = HumanoidRig(
                    angle=pyaw,
                    eyes="asymmetric",
                    eyebrows="raised",
                    mouth="small_o",
                    prop="scroll" if pi % 2 == 0 else "none",
                    hat_lift_y=11.0,
                    hat_tilt=-16.0,
                    scarf_sway=34.0,
                    sweat_drop=True,
                )
                p_tag = f"pass_{pi}_y{int(pyaw)}"
                p_img, _ = sprites.render_penumpang(prig, cache_tag=p_tag)
                asp = self._assign_pil_sprite(self.actors[f"Actor_Penumpang_{pi}"][1], p_img, p_tag)
                self._place_actor(f"Actor_Penumpang_{pi}", pp, 1.96, asp, cam_pos_b, cam_fwd_b, cam_right_b, cam_up_b)
        else:
            for pi in range(4):
                self._hide_actor(f"Actor_Penumpang_{pi}")
