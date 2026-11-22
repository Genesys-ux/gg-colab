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
SPRITE_CACHE_VER = "v3"


def _lighting_phase_at(t: float) -> str:
    if t < 26.0:
        return "phase1"
    if t < 38.0:
        return "phase2"
    if t < 51.8:
        return "phase3_crimson"
    return "phase3_twilight"


def _natural_blink(t: float, period: float = 3.1, offset: float = 0.4) -> float:
    """Kedipan mata berkala yang natural (tidak seragam antarkarakter) dengan durasi ~0.16 detik."""
    phase = (t + offset) % period
    if phase < 0.08:
        return round(smoothstep(phase / 0.08), 1)
    if phase < 0.16:
        return round(1.0 - smoothstep((phase - 0.08) / 0.08), 1)
    return 0.0


def _gaze_toward(
    actor_pos: Tuple[float, float, float],
    target_pos: Tuple[float, float, float],
    eye_h: float = 1.35,
) -> Tuple[float, float]:
    """Hitung arah lirikan mata (gaze_x, gaze_y) relatif dari karakter menuju objek hero (Kunci Emas)."""
    dx = target_pos[0] - actor_pos[0]
    dy = target_pos[1] - (actor_pos[1] + eye_h)
    dz = target_pos[2] - actor_pos[2]
    horiz = max(0.35, math.hypot(dx, dz))
    gx = clamp(dx / horiz * 1.15, -0.65, 0.65)
    gy = clamp(-dy / max(0.6, horiz) * 0.95, -0.55, 0.55)
    return round(gx, 1), round(gy, 1)


def eval_bima_world_pos(t: float) -> Optional[Tuple[float, float, float]]:
    """
    Evaluasi posisi 3D Bima (x, y_up, z_fwd) yang 100% BEBAS TEMBUS DINDING / MEJA / TANGGA / TREM
    di seluruh 6 lokasi (0..58 detik). Dipakai oleh ExactCharacterCastManager & audit tabrakan otomatis.
    """
    tram_z = eval_tram_z_fwd(t)
    if t < 8.5:
        # Lokasi 1: Berdiri mantap di atas pijakan kayu tukang jam (top y=25.32) di BELAKANG meja oak (z=0.70..2.40)!
        recoil = math.sin(clamp((t - 4.2) / 3.2) * math.pi) * 0.08
        return (-0.10 + recoil, 25.32, 2.68)
    if 11.2 <= t < 18.2:
        # Lokasi 2: Jalur parkour bertingkat (Kanopi Merah -> Kanopi Teal -> Teras -> Tangga diagonal -> Gang)
        if t < 12.8:
            u = (t - 11.2) / 1.6
            return (lerp(-0.35, -0.55, u), 17.55 + math.sin(u * math.pi) * 1.65, lerp(10.2, 12.4, u))
        if t < 14.6:
            u = (t - 12.8) / 1.8
            return (lerp(-0.55, -0.65, u), lerp(17.15, 12.02, u * u) + math.sin(u * math.pi) * 1.15, lerp(12.4, 16.0, u))
        if t < 15.8:
            u = (t - 14.6) / 1.2
            stride = abs(math.sin(t * 14.0)) * 0.12
            return (lerp(-0.65, -0.35, u), 12.02 + stride, lerp(16.0, 19.6, u))
        u = (t - 15.8) / 2.4
        stride = abs(math.sin(t * 14.0)) * 0.10
        return (lerp(-0.35, 0.18, u), lerp(11.45, 5.02, u) + stride, lerp(19.6, 27.6, u))
    if 18.2 <= t < 25.2:
        # Lokasi 3: Koridor cobblestone terbuka (x=-1.2..+1.2, y=5.00), bebas pot bunga & Oren (-0.82, 36.85)
        u = clamp((t - 18.2) / 6.5)
        stride = 0.0 if t >= 22.8 else abs(math.sin(t * 14.5)) * 0.09
        return (lerp(0.18, -0.06, u), 5.00 + stride, lerp(28.0, 39.2, u))
    if 33.8 <= t < 38.2:
        # Lokasi 4: 2-tahap bebas dinding — melewati portal lorong (z=58) lalu melesat naik di dalam cerobong terbuka (z=62)
        if t < 35.3:
            u1 = (t - 33.8) / 1.5
            return (lerp(-0.45, -0.65, u1), lerp(-16.2, -15.2, smoothstep(u1)), lerp(47.0, 62.0, smoothstep(u1)))
        u2 = (t - 35.3) / 2.9
        return (-0.65 + math.sin(u2 * 5.0) * 0.25, lerp(-15.2, 10.6, u2), 62.0)
    if 40.6 <= t < 49.2:
        # Lokasi 5: Lari menapak tepat di atas atap clerestory Trem Lisbon 28 (top y=13.53) -> lompatan slow-mo ke balkon!
        if t < 46.2:
            u = (t - 40.6) / 5.6
            stride = abs(math.sin(t * 15.0)) * 0.14
            return (0.0, 13.56 + stride, tram_z + lerp(-4.2, 4.4, u))
        u = exp_ease_in_out((t - 46.2) / 3.0, 4.2)
        return (lerp(0.0, -0.15, u), lerp(13.60, 15.46, u) + math.sin(u * math.pi) * 4.5, lerp(tram_z + 4.4, 116.25, u))
    if t >= 49.2:
        # Lokasi 6: Berdiri mantap di lantai balkon kayu Menara Jam Venesia (y=15.46, z=115.77..117.82)
        return (-0.15, 15.46, 116.25)
    return None


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
                fp = os.path.join(SPRITE_DISK_DIR, f"{SPRITE_CACHE_VER}_{safe_name}.png")
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
        squash_x: float = 1.0,
        squash_z: float = 1.0,
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
        obj.scale = Vector((height_m * aspect * squash_x, 1.0, height_m * squash_z))

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
        key_p_now, k_yaw, k_roll = eval_golden_key_world(t)
        if t < 56.2:
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
            self._place_actor("Actor_GoldenKey", key_p_now, k_h, asp, cam_pos_b, cam_fwd_b, cam_right_b, cam_up_b)
        else:
            self._hide_actor("Actor_GoldenKey")

        # ==================== 2. KUNCI PERAK ([CAM 27]-[CAM 28] — Beat Komedi Mengintip -> Jeda -> Jatuh!) ====================
        if t >= 55.25:
            # Beat komedi: 55.25..55.55 mengintip + jeda singkat menggantung, lalu 55.55..58.0 jatuh cepat!
            if t < 55.55:
                u_p = smoothstep((t - 55.25) / 0.30)
                sp = (-0.42, lerp(16.18, 16.06, u_p), 115.92)
                s_yaw, s_roll = 18.0 + u_p * 12.0, 22.0 + math.sin(t * 24.0) * 6.0
            else:
                u_s = clamp((t - 55.55) / 2.45)
                sp = (lerp(-0.42, 0.0, u_s), lerp(16.06, 12.2, u_s * u_s), lerp(115.92, 117.6, u_s))
                s_yaw, s_roll = 30.0 + u_s * 240.0, 28.0 + u_s * 180.0
            s_rig = KeyPropRig(yaw_deg=q_ang(s_yaw), roll_deg=round(s_roll / 6.0) * 6.0)
            s_tag = f"silver_{int(s_rig.yaw_deg)}_{int(s_rig.roll_deg)}"
            s_img, _ = sprites.render_silver_key(s_rig, cache_tag=s_tag)
            asp = self._assign_pil_sprite(self.actors["Actor_SilverKey"][1], s_img, s_tag)
            self._place_actor("Actor_SilverKey", sp, 0.56, asp, cam_pos_b, cam_fwd_b, cam_right_b, cam_up_b)
        else:
            self._hide_actor("Actor_SilverKey")

        # ==================== 3. BIMA (100% DESAIN ASLI PREVIEW 1 + RIG TERBUKA + AKTING NATURAL!) ====================
        bima_pos = eval_bima_world_pos(t)
        bima_facing = 180.0
        bima_rig = None
        bima_anim = "static"
        bima_roll = 0.0
        bima_h = 1.65
        bima_sq_x, bima_sq_z = 1.0, 1.0
        bima_tag = f"bima_f{frame}"

        if bima_pos is not None:
            gx, gy = _gaze_toward(bima_pos, key_p_now, eye_h=1.35)
            blink_b = _natural_blink(t, period=3.3, offset=0.6)

            if t < 8.5:
                # Berdiri bebas-tabrakan di BELAKANG meja oak (z=2.68), tangan kanan aktif menyambar mengikuti tinggi Kunci Emas!
                bima_facing = 180.0
                bima_h = 1.72
                reach_u = clamp((t - 1.5) / 5.0)
                hand_y = int(round(lerp(174, 218, reach_u) / 8.0) * 8)
                scarf_s = round(-10.0 - reach_u * 12.0 + math.sin(t * 7.0) * 3.0, 0)
                jambul_s = round(-6.0 + math.sin(t * 8.0) * 4.0, 0)
                # CATATAN: head_tilt pada Bima/Oren dalam satuan RADIAN (maks ~±0.12 rad = ±7°)!
                htilt = round(lerp(-0.07, 0.09, reach_u), 2)
                bima_sq_x = 1.0 - math.sin(reach_u * math.pi) * 0.04
                bima_sq_z = 1.0 + math.sin(reach_u * math.pi) * 0.05
                bima_rig = HumanoidRig(
                    eyes="panic" if t > 1.4 else "shocked",
                    eyebrows="worried",
                    mouth="open_yell",
                    sweat_drop=(t > 0.8),
                    blink=0.0 if t > 1.2 else blink_b,
                    eye_gaze_x=gx,
                    eye_gaze_y=gy,
                    head_tilt=htilt,
                    torso_lean_z=round(0.08 + reach_u * 0.12, 2),
                    right_hand_target=(88, hand_y, 44),
                    left_hand_target=(-68, 224, 30),
                    scarf_sway=scarf_s,
                    jambul_sway=jambul_s,
                )
                bima_tag = f"bima_loc1_{int(t > 1.4)}_h{hand_y}_g{int(gx*10)}_{int(gy*10)}_{phase}"
            elif 11.2 <= t < 18.2:
                bima_facing = 0.0
                if t < 14.6:
                    # Parkour kanopi merah -> kanopi teal -> mendarat ke teras dengan squash-and-stretch natural!
                    u_arc = ((t - 11.2) / 1.6) if t < 12.8 else ((t - 12.8) / 1.8)
                    if u_arc < 0.18:
                        bima_sq_x, bima_sq_z = 0.92, 1.10  # stretch saat tolakan lompat
                    elif u_arc > 0.84:
                        bima_sq_x, bima_sq_z = 1.10, 0.90  # squash lembut saat mendarat
                    bima_anim = "jump"
                    bima_roll = round(lerp(-7.0, 7.0, u_arc), 1)
                    bima_rig = HumanoidRig(
                        eyes="focused",
                        eyebrows="angry",
                        mouth="grit_teeth",
                        eye_gaze_x=gx,
                        eye_gaze_y=gy,
                        head_tilt=round(lerp(-0.08, 0.08, u_arc), 2),
                        scarf_sway=-28.0,
                        jambul_sway=10.0,
                    )
                    bima_tag = f"bima_loc2j_{int(u_arc*8)}_{int(gx*5)}_{phase}"
                else:
                    bima_anim = "run"
                    bima_roll = 4.0 if t >= 15.8 else 0.0
                    bima_rig = HumanoidRig(
                        eyes="shocked",
                        eyebrows="worried",
                        mouth="open_yell",
                        sweat_drop=True,
                        eye_gaze_x=gx,
                        eye_gaze_y=gy,
                        scarf_sway=-24.0,
                        jambul_sway=-8.0,
                    )
                    bima_tag = f"bima_loc2r_{frame % 12}_{phase}"
            elif 18.2 <= t < 25.2:
                bima_facing = 0.0
                if t >= 22.8:
                    # Transisi mulus ke knee-slide mengejar Kunci Emas di gang cobblestone basah!
                    u_sl = clamp((t - 22.8) / 0.55)
                    bima_roll = lerp(0.0, -18.0, smoothstep(u_sl))
                    bima_sq_x = lerp(1.0, 1.08, u_sl)
                    bima_sq_z = lerp(1.0, 0.92, u_sl)
                    bima_rig = HumanoidRig(
                        torso_lean_z=round(lerp(0.08, 0.18, u_sl), 2),
                        eyes="panic",
                        eyebrows="worried",
                        mouth="grit_teeth",
                        sweat_drop=True,
                        eye_gaze_x=gx,
                        eye_gaze_y=gy,
                        head_tilt=0.09,
                        right_hand_target=(96, 198, 44),
                        left_hand_target=(-64, 245, 22),
                        scarf_sway=-34.0,
                        jambul_sway=-10.0,
                    )
                    bima_tag = f"bima_slide_{int(u_sl*4)}_{phase}"
                else:
                    bima_anim = "run"
                    bima_rig = HumanoidRig(
                        eyes="focused",
                        eyebrows="angry",
                        mouth="grit_teeth",
                        eye_gaze_x=gx,
                        eye_gaze_y=gy,
                        scarf_sway=-26.0,
                    )
                    bima_tag = f"bima_loc3run_{frame % 12}_{phase}"
            elif 33.8 <= t < 38.2:
                u = (t - 33.8) / 4.4
                bima_facing = 180.0
                bima_roll = math.sin(u * 8.0) * 16.0
                bima_sq_x, bima_sq_z = 0.90, 1.12  # melesat vertikal stretch oleh uap cerobong!
                bima_rig = HumanoidRig(
                    eyes="asymmetric",
                    eyebrows="raised",
                    mouth="open_yell",
                    sweat_drop=True,
                    head_tilt=round(math.sin(u * 6.0) * 0.11, 2),
                    right_hand_target=(86, 154, 34),
                    left_hand_target=(-84, 158, 34),
                    scarf_sway=28.0,
                    jambul_sway=14.0,
                )
                bima_tag = f"bima_chimney_{int(u*6)}_{phase}"
            elif 40.6 <= t < 49.2:
                if t < 46.2:
                    bima_facing = 0.0
                    bima_anim = "run"
                    bima_rig = HumanoidRig(
                        eyes="focused",
                        eyebrows="angry",
                        mouth="grit_teeth",
                        eye_gaze_x=gx,
                        eye_gaze_y=gy,
                        scarf_sway=-36.0,
                        jambul_sway=-12.0,
                    )
                    bima_tag = f"bima_tramrun_{frame % 12}_{phase}"
                else:
                    u = exp_ease_in_out((t - 46.2) / 3.0, 4.2)
                    bima_facing = -115.0
                    bima_roll = lerp(-10.0, 14.0, u)
                    if u < 0.20:
                        bima_sq_x, bima_sq_z = 0.91, 1.11  # stretch tolakan lompatan epik
                    elif u > 0.86:
                        bima_sq_x, bima_sq_z = 1.12, 0.89  # squash mendarat mantap di balkon
                    bima_rig = HumanoidRig(
                        pelvis_y=-24.0,
                        head_bob_y=-26.0,
                        jump_height=38.0,
                        torso_lean_z=0.12,
                        eyes="focused",
                        eyebrows="raised",
                        mouth="open_yell",
                        eye_gaze_x=gx,
                        eye_gaze_y=gy,
                        head_tilt=round(lerp(-0.07, 0.09, u), 2),
                        right_hand_target=(96, 158, 42),
                        left_hand_target=(-74, 198, 22),
                        left_foot_target=(-26, 404, -22),
                        right_foot_target=(38, 412, 24),
                        scarf_sway=-38.0,
                        jambul_sway=12.0,
                    )
                    bima_tag = f"bima_leap_{int(u*6)}_{phase}"
            elif t >= 49.2:
                bima_facing = 0.0 if t < 53.0 else 180.0
                if t < 52.2:
                    # Memutar Kunci Emas di lubang jam dengan gerakan torsi bahu & tangan yang nyata!
                    u_turn = smoothstep((t - 49.2) / 2.6)
                    hand_rx = int(round(lerp(74, 92, u_turn) / 6.0) * 6)
                    hand_ry = int(round(lerp(174, 156, u_turn) / 6.0) * 6)
                    bima_roll = lerp(3.0, -4.0, u_turn)
                    bima_rig = HumanoidRig(
                        eyes="focused",
                        eyebrows="raised",
                        mouth="grit_teeth",
                        torso_lean_z=0.10,
                        head_tilt=round(lerp(-0.05, 0.06, u_turn), 2),
                        right_hand_target=(hand_rx, hand_ry, 44),
                        left_hand_target=(-52, 235, 24),
                        scarf_sway=-14.0,
                    )
                    bima_tag = f"bima_turnkey_{hand_rx}_{phase}"
                else:
                    # Bernapas lega & menepuk dada santai di balkon Menara Jam (napas halus + benang saku melambai!)
                    breath = math.sin((t - 52.2) * 3.2)
                    bima_sq_x = 1.0 - breath * 0.015
                    bima_sq_z = 1.0 + breath * 0.018
                    pat_y = int(round((246.0 + math.sin((t - 52.2) * 5.0) * 8.0) / 4.0) * 4)
                    tsway = round(math.sin(t * 6.0) * 3.5, 0)
                    ssway = round(math.sin(t * 2.5) * 6.0, 0)
                    bima_rig = HumanoidRig(
                        eyes="happy",
                        eyebrows="happy",
                        mouth="happy_open",
                        head_tilt=round(math.sin(t * 2.2) * 0.05, 2),
                        right_hand_target=(16, pat_y, 44),
                        left_hand_target=(-52, 280, 20),
                        silver_key_peek=(54.2 <= t <= 55.6),
                        thread_sway=tsway,
                        scarf_sway=ssway,
                    )
                    bima_tag = f"bima_happy_{int(54.2 <= t <= 55.6)}_p{pat_y}_s{int(ssway)}_{phase}"

        if bima_pos is not None and bima_rig is not None:
            rel_yaw = q_ang(_camera_relative_yaw_deg(bima_pos, bima_facing, cam_spec.eye_w))
            bima_rig.angle = rel_yaw
            full_tag = f"{bima_tag}_y{int(rel_yaw)}"
            b_img, _ = sprites.render_bima(bima_rig, lighting_phase=phase, animation=bima_anim, frame=frame, cache_tag=full_tag)
            asp = self._assign_pil_sprite(self.actors["Actor_Bima"][1], b_img, full_tag)
            self._place_actor(
                "Actor_Bima", bima_pos, bima_h, asp, cam_pos_b, cam_fwd_b, cam_right_b, cam_up_b,
                roll_deg=bima_roll, squash_x=bima_sq_x, squash_z=bima_sq_z,
            )
        else:
            self._hide_actor("Actor_Bima")

        # ==================== 4. OREN (100% DESAIN ASLI PREVIEW 1 + AKTING ANTISIPASI & TEPISAN!) ====================
        if 17.5 <= t <= 25.5:
            oren_pos = (-0.82, 5.00, 36.85)
            oren_yaw = q_ang(_camera_relative_yaw_deg(oren_pos, 155.0, cam_spec.eye_w))
            # Antisipasi cakar terangkat (20.3..21.35) -> tepisan cepat (21.45..21.85) -> santai kembali!
            if t < 20.3:
                slap_amt = 0.0
                paw_rot = 0.25
                o_sq_x, o_sq_z = 1.0, 1.0
            elif t < 21.45:
                u_ant = smoothstep((t - 20.3) / 1.15)
                slap_amt = round(u_ant * 0.95, 1)
                paw_rot = round(lerp(0.25, -0.35, u_ant), 1)
                o_sq_x, o_sq_z = 1.0 + u_ant * 0.04, 1.0 - u_ant * 0.04
            elif t < 22.15:
                u_sw = smoothstep((t - 21.45) / 0.35)
                slap_amt = 1.0
                paw_rot = round(lerp(-0.35, 0.75, u_sw), 1)
                o_sq_x, o_sq_z = 0.94, 1.06
            else:
                u_rec = smoothstep((t - 22.15) / 1.0)
                slap_amt = round(1.0 - u_rec, 1)
                paw_rot = round(lerp(0.75, 0.25, u_rec), 1)
                o_sq_x, o_sq_z = 1.0, 1.0
            # Lirikan mata Oren aktif melacak Kunci Emas + kedipan arogan lambat!
            o_gx = round(clamp((key_p_now[0] - oren_pos[0]) * 0.45, -0.45, 0.55), 1)
            o_blink = _natural_blink(t, period=2.9, offset=0.8) if t < 21.1 else 0.0
            bell_sw = round(math.sin((t - 21.45) * 14.0) * math.exp(-max(0.0, t - 21.45) * 2.5) * 9.0, 0) if t >= 21.45 else round(slap_amt * 4.0, 0)
            o_rig = OrenRig(
                angle=oren_yaw,
                body_lean=round(-0.08 * slap_amt, 2),
                head_tilt=round(o_gx * 0.14, 2),  # RADIAN (±0.07 rad = ±4° miring arogan!)
                ear_left_twitch=round(math.sin(t * 4.5) * 0.12 if slap_amt > 0.2 else 0.0, 1),
                eyelid_level=0.56,
                blink=o_blink,
                gaze_x=o_gx,
                mouth_style="smug",
                right_paw_raised=slap_amt,
                right_paw_rot=paw_rot,
                show_paw_pads=(slap_amt > 0.35),
                claws_out=round(slap_amt * 0.9, 1),
                tail_sway=round(math.sin(t * 3.2) * 18.0 + slap_amt * 12.0, 0),
                bell_sway=bell_sw,
            )
            o_tag = f"oren_y{int(oren_yaw)}_s{int(slap_amt*10)}_p{int(paw_rot*10)}_g{int(o_gx*10)}_b{int(o_blink*5)}_t{int(o_rig.tail_sway/4)}"
            o_img, _ = sprites.render_oren(o_rig, cache_tag=o_tag)
            asp = self._assign_pil_sprite(self.actors["Actor_Oren"][1], o_img, o_tag)
            self._place_actor(
                "Actor_Oren", oren_pos, 0.82, asp, cam_pos_b, cam_fwd_b, cam_right_b, cam_up_b,
                squash_x=o_sq_x, squash_z=o_sq_z,
            )
        else:
            self._hide_actor("Actor_Oren")

        # ==================== 5. FIGURAN PASAR (Pedagang Rempah — AKTING TERJUNGKAL MULUS & BEBAS TABRAKAN!) ====================
        if 8.5 <= t <= 18.5:
            # Posisi teras bawah bersih dari karung kunyit hero (0.25, 16.9) & koridor Bima (-0.65)
            merchants = [
                ((-1.32, 12.00, 17.6), 25.0, -18.0, 14.65),
                ((1.35, 12.00, 17.8), -35.0, 20.0, 14.78),
                ((-2.45, 14.20, 12.0), 40.0, 0.0, 99.0),
            ]
            for mi, (mp, mface, target_roll, t_react) in enumerate(merchants):
                myaw = q_ang(_camera_relative_yaw_deg(mp, mface, cam_spec.eye_w))
                u_p = smoothstep((t - t_react) / 0.55) if t > t_react else 0.0
                panicking = (u_p > 0.05)
                mroll = target_roll * u_p
                hat_pop = round(math.sin(min(1.0, u_p) * math.pi * 0.85) * 16.0, 0) if panicking else 0.0
                m_blink = 0.0 if panicking else _natural_blink(t, period=3.5 + mi * 0.4, offset=mi * 1.1)
                mrig = HumanoidRig(
                    angle=myaw,
                    pose="panic" if panicking else "ready",
                    eyes="shocked" if panicking else "chill",
                    eyebrows="worried" if panicking else "happy",
                    mouth="open_yell" if panicking else "smirk",
                    blink=m_blink,
                    sweat_drop=panicking,
                    hat_lift_y=hat_pop,
                    hat_tilt=round(-16.0 * u_p, 0),
                )
                m_tag = f"merch_{mi}_y{int(myaw)}_p{int(u_p*4)}_b{int(m_blink*5)}"
                m_img, _ = sprites.render_pedagang(mrig, cache_tag=m_tag)
                asp = self._assign_pil_sprite(self.actors[f"Actor_Pedagang_{mi}"][1], m_img, m_tag)
                m_sq_x = 1.0 + math.sin(u_p * math.pi) * 0.07
                m_sq_z = 1.0 - math.sin(u_p * math.pi) * 0.06
                self._place_actor(
                    f"Actor_Pedagang_{mi}", mp, 1.82, asp, cam_pos_b, cam_fwd_b, cam_right_b, cam_up_b,
                    roll_deg=mroll, squash_x=m_sq_x, squash_z=m_sq_z,
                )
        else:
            for mi in range(3):
                self._hide_actor(f"Actor_Pedagang_{mi}")

        # ==================== 6. FIGURAN STASIUN (Penumpang Trem — BEBAS PILAR/KOPER + LANGKAH MUNDUR NATURAL!) ====================
        if 37.8 <= t <= 50.0:
            # Posisi peron bersih dari pilar besi (x=±2.55), koper (x=±3.2, z=70.4/80.4/90.4/97.5), & bangku (x=4.1)
            u_back = smoothstep((t - 39.2) / 6.5) if t > 39.2 else 0.0
            passengers = [
                ((-3.55, 10.03, 73.6 - u_back * 1.05), 80.0),
                ((3.45, 10.03, 83.8 - u_back * 1.05), -85.0),
                ((-3.55, 10.03, 96.2 - u_back * 1.05), 115.0),
                ((3.45, 10.03, 93.2 - u_back * 1.05), -110.0),
            ]
            for pi, (pp, pface) in enumerate(passengers):
                pyaw = q_ang(_camera_relative_yaw_deg(pp, pface, cam_spec.eye_w))
                wind_osc = math.sin(t * 7.5 + pi * 1.4)
                p_scarf = round(30.0 + wind_osc * 7.0, 0)
                p_hat = round(9.0 + abs(wind_osc) * 4.0, 0)
                p_bob = abs(math.sin(t * 6.0 + pi)) * 0.05 * u_back
                prig = HumanoidRig(
                    angle=pyaw,
                    eyes="asymmetric",
                    eyebrows="raised",
                    mouth="small_o",
                    blink=_natural_blink(t, period=3.2 + pi * 0.35, offset=pi * 0.9),
                    prop="scroll" if pi % 2 == 0 else "none",
                    hat_lift_y=p_hat,
                    hat_tilt=round(-14.0 - wind_osc * 4.0, 0),
                    scarf_sway=p_scarf,
                    sweat_drop=True,
                )
                p_tag = f"pass_{pi}_y{int(pyaw)}_w{int(p_scarf/4)}"
                p_img, _ = sprites.render_penumpang(prig, cache_tag=p_tag)
                asp = self._assign_pil_sprite(self.actors[f"Actor_Penumpang_{pi}"][1], p_img, p_tag)
                self._place_actor(
                    f"Actor_Penumpang_{pi}", (pp[0], pp[1] + p_bob, pp[2]), 1.96, asp,
                    cam_pos_b, cam_fwd_b, cam_right_b, cam_up_b,
                    roll_deg=round(-2.5 * u_back * (1 if pi % 2 == 0 else -1), 1),
                )
        else:
            for pi in range(4):
                self._hide_actor(f"Actor_Penumpang_{pi}")
