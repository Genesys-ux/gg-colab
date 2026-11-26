"""
Integrasi 10 Karakter Peran Ganda (Shared Engine & Free-Rig) ke Dunia 3D Blender "DETIK KE-75":
  - Menapak presisi di lantai/dek/ranjang 3D tanpa tembus dinding/properti (Strict Anti-Clipping)
  - Pergerakan biomekanik organik: bobot langkah, 2-Bone IK tangan (mendekap koper, meraih cincin,
    menahan sinar biru, membidik sniper, memeriksa penlight medis, menggenggam tangan di ICU),
    kedipan mata natural tidak seragam, lirikan mata (gaze tracking), & viseme dialog!
  - Sistem Morph-Target Aging real-time Raka (26 -> 78 thn) di detik 39.8..45.5!
  - Momen mikro-komedi fisik halus sesuai Global Rule (visor Sena miring saat kereta oleng,
    ekspresi O_o Raka sepersekian detik saat cincin melayang di depannya) tanpa merusak drama!
"""
from __future__ import annotations

import hashlib
import json
import math
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from .camera_28_moves import clamp, eval_camera_world, lerp, smoothstep
from .config import (
    ICU_BED_POS_W,
    ICU_MATTRESS_Y,
    LOC1_FLOOR_Y,
    LOC3_ORIGIN,
    LOC4_FLOOR_Y,
    LOC5_FLOOR_Y,
    LOC6_FLOOR_Y,
    OUTPUT_DIR,
    PORTAL_DOOR_Z,
    TOTAL_FRAMES,
    frame_to_sec,
    w_to_b,
)

SPRITE_CACHE_DIR = os.path.join(OUTPUT_DIR, "blender_sprites_detik75")


@dataclass
class ActorFrameState:
    actor_key: str
    pos_w: Tuple[float, float, float]
    facing_yaw_deg: float  # 0 = menghadap +Z_fwd, 180 = menghadap -Z_fwd, 90 = +X, -90 = -X
    height_m: float = 1.72
    pitch_deg: float = 0.0  # 0 = berdiri vertikal, -78 = berbaring di ranjang ICU
    render_kwargs: Dict[str, Any] = field(default_factory=dict)


def _lipsync_wave(t: float, windows: List[Tuple[float, float]], freq: float = 11.5) -> float:
    for a, b in windows:
        if a <= t <= b:
            env = math.sin(clamp((t - a) / max(0.05, b - a)) * math.pi)
            return round(clamp((0.35 + 0.55 * abs(math.sin(t * freq))) * env), 2)
    return 0.0


def eval_actors_at_time(t: float) -> List[ActorFrameState]:
    """
    Evaluasi posisi 3D & parameter Free-Rig seluruh karakter aktif pada detik `t` (0.0..75.0).
    Fungsi ini murni matematika Python sehingga dapat diaudit otomatis oleh `verify_dry_run.py`!
    """
    states: List[ActorFrameState] = []
    rfy = LOC4_FLOOR_Y
    wx, wy, wz = LOC3_ORIGIN
    bx, by, bz = ICU_BED_POS_W

    # Quantize cycle frame (0..29) so sprite disk cache hits heavily on repeated walk/run cycles
    cyc_frame = int(round(t * 30.0)) % 30

    # =========================================================================
    # BABAK I: KERETA MAGLEV EXPRESS 09 & PORTAL (00:00 – 00:16.2)
    # =========================================================================
    if t < 16.2:
        # 1. RAKA MEMORI (26 thn): Hook -> Lari mendekap koper -> Tangkap cincin -> Lompat portal!
        raka_vo = _lipsync_wave(t, [(1.6, 5.6), (13.6, 15.8)])
        if t < 2.0:
            rz = lerp(4.0, 4.6, t / 2.0)
            states.append(ActorFrameState(
                "raka_memori", (0.0, LOC1_FLOOR_Y, rz), 180.0, 1.72, 0.0,
                {"frame": cyc_frame, "animation": "free", "eyes": "shocked" if t < 1.1 else "focused",
                 "mouth_open": raka_vo, "left_hand_target": (-22, 242, 46), "right_hand_target": (22, 240, 46)},
            ))
        elif t < 10.2:
            u = (t - 2.0) / 8.2
            rz = lerp(4.6, 18.8, u)
            rx = math.sin(t * 3.2) * 0.18  # Tetap di lorong tengah -0.6..+0.6 (bebas tiang & kursi!)
            states.append(ActorFrameState(
                "raka_memori", (rx, LOC1_FLOOR_Y, rz), 0.0, 1.72, 0.0,
                {"frame": cyc_frame, "animation": "run", "arm_pose": "ready", "eyes": "panic" if t > 7.5 else "focused",
                 "mouth_open": raka_vo, "torso_lean_deg": 9.0},
            ))
        elif t < 13.4:
            # Bullet-time menangkap cincin emas Maya (mikro-ekspresi O_o kaget di 10.5..11.1s!) -> tekan tombol pintu merah
            u = (t - 10.2) / 3.2
            rz = lerp(18.8, PORTAL_DOOR_Z - 0.65, smoothstep(u))
            rx = lerp(0.05, 0.35, smoothstep(u))
            eye_mode = "asymmetric" if 10.4 <= t <= 11.1 else "focused"
            states.append(ActorFrameState(
                "raka_memori", (rx, LOC1_FLOOR_Y, rz), 15.0, 1.72, 0.0,
                {"frame": cyc_frame, "animation": "free", "pelvis_y": 8.0, "torso_lean_deg": 8.0,
                 "right_hand_target": (78, 195, 44), "left_hand_target": (-24, 244, 44),
                 "eyes": eye_mode, "mouth_open": raka_vo},
            ))
        else:
            # Melompat keluar menembus pintu portal merah!
            u = clamp((t - 13.4) / 2.8)
            rz = lerp(PORTAL_DOOR_Z - 0.5, PORTAL_DOOR_Z + 2.8, u)
            ry = LOC1_FLOOR_Y + math.sin(u * math.pi) * 0.85
            states.append(ActorFrameState(
                "raka_memori", (0.0, ry, rz), 0.0, 1.72, 0.0,
                {"frame": cyc_frame, "animation": "jump", "eyes": "focused", "mouth_open": raka_vo},
            ))

        # 2. BIMA MEMORI (42 thn): Memblokir pintu sambungan gerbong di z=23.2 (t=5.5..12.8s)
        if 5.2 <= t <= 12.8:
            bima_vo = _lipsync_wave(t, [(6.4, 9.2)], freq=9.0)
            states.append(ActorFrameState(
                "bima_memori", (-0.18, LOC1_FLOOR_Y, 23.2), 180.0, 1.82, 0.0,
                {"frame": cyc_frame, "animation": "free", "pose": "crossed", "eyes": "angry",
                 "mouth": "open_yell" if bima_vo > 0.1 else "grit_teeth", "mouth_open": bima_vo},
            ))

        # 3. SENA MEMORI (35 thn): Mengejar dari belakang sambil mengacungkan pemindai biru
        #    (Mikro-gag halus: saat kereta oleng di t=6.8..8.2s, kepala/visor sedikit miring deadpan!)
        if 5.8 <= t <= 13.5:
            uz = clamp((t - 5.8) / 7.7)
            sz = lerp(9.5, 21.5, uz)
            visor_tilt = 7.0 if 6.8 <= t <= 8.2 else 0.0
            states.append(ActorFrameState(
                "sena_memori", (0.18, LOC1_FLOOR_Y, sz), 0.0, 1.78, 0.0,
                {"frame": cyc_frame, "animation": "run", "arm_pose": "point",
                 "eyes": "deadpan" if visor_tilt > 0 else "focused", "head_tilt_deg": visor_tilt},
            ))

        # 4. NENEK MAYA (75 thn): Duduk tenang di kursi kanan z=17.5 & menjentikkan cincin emas!
        if 6.0 <= t <= 13.2:
            flick = 10.0 <= t <= 11.6
            states.append(ActorFrameState(
                "maya_realitas", (1.12, LOC1_FLOOR_Y, 17.6), -90.0, 1.58, 0.0,
                {"frame": cyc_frame, "animation": "free", "pelvis_y": 14.0,
                 "left_hand_target": (-62, 185, 48) if flick else (-38, 236, 42),
                 "eyes": "happy", "mouth": "smirk", "ring_glow_boost": 1.6 if flick else 1.1},
            ))

    # =========================================================================
    # BABAK II: ATAP BADAI APEX TOWER & MENARA AIR KIRA (00:16.2 – 00:46.0)
    # =========================================================================
    elif t < 46.0:
        # 1. RAKA MEMORI (26 -> 78 thn saat t=39.8..45.8s!)
        raka_vo2 = _lipsync_wave(t, [(34.8, 37.6)])
        if t < 18.2:
            u = clamp((t - 16.2) / 2.0)
            ry = lerp(rfy + 4.2, rfy, u * u)
            states.append(ActorFrameState(
                "raka_memori", (0.0, ry, 58.5), 0.0, 1.72, 0.0,
                {"frame": cyc_frame, "animation": "jump", "eyes": "panic"},
            ))
        elif t < 39.8:
            # Berguling mendarat lalu terpojok di helipad (z=60.5..62.0) menghadapi laser & kepungan
            crouch = 16.0 if t < 20.5 else (10.0 if t > 31.0 else 5.0)
            shield_eyes = 34.5 <= t <= 38.0
            states.append(ActorFrameState(
                "raka_memori", (0.0, rfy, 61.6 if t > 28.5 else 60.4), 180.0, 1.72, 0.0,
                {"frame": cyc_frame, "animation": "free", "pelvis_y": crouch, "torso_lean_deg": 6.0,
                 "left_hand_target": (-42, 172, 48) if shield_eyes else (-26, 240, 44),
                 "right_hand_target": (28, 238, 46),
                 "eyes": "panic" if t > 30.0 else "focused", "mouth_open": raka_vo2},
            ))
        else:
            # KEJUTAN #2 (39.8..46.0s): Meraih lilin kue ulang tahun sambil MENUA REAL-TIME (age 0.0 -> 1.0)!
            age_u = round(clamp((t - 40.2) / 4.8) * 20.0) / 20.0  # Quantized 0.05 steps for fast cache!
            states.append(ActorFrameState(
                "raka_memori", (0.0, rfy, 62.1), 180.0, 1.72 - 0.08 * age_u, 0.0,
                {"frame": cyc_frame, "animation": "free", "age": age_u, "pelvis_y": 14.0,
                 "right_hand_target": (58, 224, 46), "eyes": "shocked" if age_u < 0.6 else "chill",
                 "mouth": "small_o" if age_u < 0.5 else "smirk"},
            ))

        # 2. KIRA MEMORI (30 thn Sniper): Di atas Dek Menara Air Baja (Lokasi 3, y=44.02)
        if 20.5 <= t <= 39.5:
            states.append(ActorFrameState(
                "kira_memori", (wx - 1.05, wy, wz - 0.15), -90.0, 1.68, 0.0,
                {"frame": cyc_frame, "animation": "free", "pelvis_y": 10.0, "torso_lean_deg": 7.0,
                 "left_hand_target": (-52, 206, 46), "right_hand_target": (48, 202, 48),
                 "eyes": "focused", "eyebrows": "worried"},
            ))

        # 3. BIMA & SENA MEMORI: Melompat keluar pintu merah surealis di atap (t >= 28.0s) mengepung Raka!
        if 28.0 <= t <= 41.5:
            u_in = clamp((t - 28.0) / 2.6)
            sena_vo = _lipsync_wave(t, [(31.5, 35.0)])
            bz_pos = lerp(56.6, 59.8, smoothstep(u_in))
            sz_pos = lerp(56.6, 60.1, smoothstep(u_in))
            states.append(ActorFrameState(
                "bima_memori", (-1.05, rfy, bz_pos), 25.0, 1.82, 0.0,
                {"frame": cyc_frame, "animation": "run" if u_in < 0.85 else "free",
                 "pose": "ready", "eyes": "angry", "mouth": "grit_teeth"},
            ))
            states.append(ActorFrameState(
                "sena_memori", (0.85, rfy, sz_pos), -22.0, 1.78, 0.0,
                {"frame": cyc_frame, "animation": "run" if u_in < 0.85 else "free",
                 "right_hand_target": (76, 188, 46), "eyes": "focused", "mouth_open": sena_vo},
            ))

    # =========================================================================
    # BABAK III: RUANG ICU KAMAR 404 & TWIST KORIDOR EMAS (00:46.0 – 01:15.0)
    # =========================================================================
    else:
        # Sebelum 68.4s: Kakek Raka & Keluarga berada di Ruang ICU Kamar 404 (Lokasi 5)
        if t < 68.4:
            revived = t >= 64.2
            raka_old_vo = _lipsync_wave(t, [(53.2, 60.5)], freq=8.0)
            # 1. KAKEK RAKA (78 thn) bersandar semi-Fowler di bantal ranjang ICU (wajah jelas & bebas tembus kasur!)
            states.append(ActorFrameState(
                "raka_realitas", (bx, LOC5_FLOOR_Y + 0.18, bz + 0.34), 180.0, 1.54, 0.0,
                {"frame": cyc_frame, "animation": "free", "pelvis_y": 12.0,
                 "blink": 1.0 if (59.5 <= t < 64.2) else None,
                 "eyes": "happy" if revived else "chill",
                 "mouth": "smirk", "mouth_open": raka_old_vo, "ground_shadow": False},
            ))

            # 2. DOKTER SENA (35 thn): Di kanan atas ranjang memeriksa pupil dengan penlight (46.0..60.0s)
            if t < 61.5:
                states.append(ActorFrameState(
                    "sena_realitas", (bx + 0.78, LOC5_FLOOR_Y, bz + 0.28), -110.0, 1.78, 0.0,
                    {"frame": cyc_frame, "animation": "free", "torso_lean_deg": 5.0,
                     "right_hand_target": (68, 204, 44) if t < 49.0 else (32, 248, 36),
                     "eyes": "chill", "eyebrows": "worried"},
                ))

            # 3. KIRA REALITAS (30 thn Putri Bungsu): Menangis menggenggam tangan Raka di sisi kanan ranjang
            states.append(ActorFrameState(
                "kira_realitas", (bx + 0.74, LOC5_FLOOR_Y, bz - 0.35), -115.0, 1.66, 0.0,
                {"frame": cyc_frame, "animation": "free", "pelvis_y": 8.0, "torso_lean_deg": 6.0,
                 "left_hand_target": (-34, 232, 46), "right_hand_target": (36, 228, 46),
                 "eyes": "happy" if revived else "honey_oval",
                 "mouth": "smirk" if revived else "frown"},
            ))

            # 4. BIMA REALITAS (42 thn Putra Sulung): Di sisi kiri ranjang berbisik lirih "Ayah, lepaskan saja..."
            bima_icu_vo = _lipsync_wave(t, [(49.1, 51.0)], freq=8.5)
            states.append(ActorFrameState(
                "bima_realitas", (bx - 0.78, LOC5_FLOOR_Y, bz + 0.22), 110.0, 1.82, 0.0,
                {"frame": cyc_frame, "animation": "free", "torso_lean_deg": 7.0,
                 "right_hand_target": (52, 232, 44),
                 "eyes": "happy" if revived else "chill",
                 "mouth": "smirk" if revived else "frown", "mouth_open": bima_icu_vo},
            ))

            # 5. NENEK MAYA (75 thn): Menggenggam erat tangan Kakek Raka di sisi kiri dekat nakas
            states.append(ActorFrameState(
                "maya_realitas", (bx - 0.72, LOC5_FLOOR_Y, bz - 0.42), 115.0, 1.58, 0.0,
                {"frame": cyc_frame, "animation": "free",
                 "left_hand_target": (-48, 226, 46),
                 "eyes": "happy", "mouth": "smirk", "ring_glow_boost": 1.6 if revived else 1.15},
            ))

        # 6. TWIST AKHIR KORIDOR CAHAYA KEEMASAN (Lokasi 6, t >= 66.8s):
        #    Raka Muda (26) & Maya Muda (25) bergandengan tangan, menoleh tersenyum, lalu berjalan menjauh!
        if t >= 66.8:
            u_walk = clamp((t - 69.2) / 5.2)
            cz = lerp(111.6, 117.8, smoothstep(u_walk))
            # Saat 66.8..69.6s mereka menoleh ke kamera (yaw ~ -105), lalu berbalik berjalan menjauh (+Z_fwd, yaw ~ 0)!
            turn_u = smoothstep((t - 69.0) / 1.4)
            yaw_raka = lerp(-100.0, -8.0, turn_u)
            yaw_maya = lerp(-85.0, 8.0, turn_u)
            anim_end = "walk" if t >= 69.4 else "free"
            states.append(ActorFrameState(
                "raka_memori", (6.15, LOC6_FLOOR_Y, cz), yaw_raka, 1.74, 0.0,
                {"frame": cyc_frame, "animation": anim_end, "eyes": "happy", "eyebrows": "happy",
                 "mouth": "smirk", "sweat_drop": False,
                 "left_hand_target": (-48, 248, 36) if anim_end == "free" else None},
            ))
            states.append(ActorFrameState(
                "maya_muda", (6.95, LOC6_FLOOR_Y, cz + 0.12), yaw_maya, 1.60, 0.0,
                {"frame": cyc_frame, "animation": anim_end, "eyes": "happy", "eyebrows": "happy",
                 "mouth": "smirk", "ring_glow_boost": 1.65,
                 "right_hand_target": (48, 248, 36) if anim_end == "free" else None},
            ))

    return states


def _camera_relative_sprite_angle(
    actor_pos_w: Tuple[float, float, float],
    actor_facing_deg: float,
    cam_pos_w: Tuple[float, float, float],
) -> float:
    dx = cam_pos_w[0] - actor_pos_w[0]
    dz = cam_pos_w[2] - actor_pos_w[2]
    cam_ang = math.degrees(math.atan2(dx, dz))
    rel = (cam_ang - actor_facing_deg) % 360.0
    # Quantize to 6-degree steps so sprite disk cache stays compact & super fast!
    return float(round(rel / 6.0) * 6.0) % 360.0


class Detik75CharacterCastManager:
    """Render & pasang seluruh 10 varian karakter Shared-Engine ke bidang 3D Alpha-Cutout di Blender."""

    ACTOR_KEYS = [
        "raka_memori", "raka_realitas",
        "sena_memori", "sena_realitas",
        "bima_memori", "bima_realitas",
        "kira_memori", "kira_realitas",
        "maya_realitas", "maya_muda",
    ]

    def __init__(self, sprite_scale: float = 2.5) -> None:
        self.sprite_scale = sprite_scale
        self._char_instances: Dict[str, Any] = {}
        self._bpy_images: Dict[str, Any] = {}
        self.planes: Dict[str, Tuple[Any, Any]] = {}
        os.makedirs(SPRITE_CACHE_DIR, exist_ok=True)

    def _get_char_instance(self, key: str):
        if key not in self._char_instances:
            from characters import (
                BimaMemoriCharacter,
                BimaRealitasCharacter,
                KiraMemoriCharacter,
                KiraRealitasCharacter,
                MayaMudaCharacter,
                MayaRealitasCharacter,
                RakaMemoriCharacter,
                RakaRealitasCharacter,
                SenaMemoriCharacter,
                SenaRealitasCharacter,
            )
            cls_map = {
                "raka_memori": RakaMemoriCharacter,
                "raka_realitas": RakaRealitasCharacter,
                "sena_memori": SenaMemoriCharacter,
                "sena_realitas": SenaRealitasCharacter,
                "bima_memori": BimaMemoriCharacter,
                "bima_realitas": BimaRealitasCharacter,
                "kira_memori": KiraMemoriCharacter,
                "kira_realitas": KiraRealitasCharacter,
                "maya_realitas": MayaRealitasCharacter,
                "maya_muda": MayaMudaCharacter,
            }
            self._char_instances[key] = cls_map[key](scale=self.sprite_scale, fps=30)
        return self._char_instances[key]

    def build_actor_planes(self) -> None:
        import bmesh  # type: ignore
        import bpy  # type: ignore
        from .mesh_utils import get_or_create_collection, link_object

        col = get_or_create_collection("Characters_25D_FreeRig")
        for key in self.ACTOR_KEYS:
            bm = bmesh.new()
            v0 = bm.verts.new((-0.5, 0.0, 0.0))
            v1 = bm.verts.new((0.5, 0.0, 0.0))
            v2 = bm.verts.new((0.5, 0.0, 1.0))
            v3 = bm.verts.new((-0.5, 0.0, 1.0))
            face = bm.faces.new((v0, v1, v2, v3))
            uv_layer = bm.loops.layers.uv.new("UVMap")
            for loop, uv in zip(face.loops, [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]):
                loop[uv_layer].uv = uv

            mesh = bpy.data.meshes.new(f"Mesh_{key}")
            bm.normal_update()
            bm.to_mesh(mesh)
            bm.free()

            obj = bpy.data.objects.new(f"Actor_{key}", mesh)
            link_object(obj, col)

            mat = bpy.data.materials.new(name=f"MAT_Actor_{key}")
            mat.use_nodes = True
            if hasattr(mat, "surface_render_method"):
                mat.surface_render_method = "DITHERED"
            if hasattr(mat, "use_backface_culling"):
                mat.use_backface_culling = False

            nodes = mat.node_tree.nodes
            links = mat.node_tree.links
            nodes.clear()

            tex = nodes.new("ShaderNodeTexImage")
            tex.extension = "CLIP"
            tex.location = (-480, 80)

            gt = nodes.new("ShaderNodeMath")
            gt.operation = "GREATER_THAN"
            gt.inputs[1].default_value = 0.42
            gt.location = (-200, -120)
            links.new(tex.outputs["Alpha"], gt.inputs[0])

            transp = nodes.new("ShaderNodeBsdfTransparent")
            transp.location = (-180, 200)

            em = nodes.new("ShaderNodeEmission")
            em.inputs["Strength"].default_value = 1.04
            em.location = (-180, 40)
            links.new(tex.outputs["Color"], em.inputs["Color"])

            mix_s = nodes.new("ShaderNodeMixShader")
            mix_s.location = (100, 80)
            links.new(gt.outputs["Value"], mix_s.inputs["Fac"])
            links.new(transp.outputs["BSDF"], mix_s.inputs[1])
            links.new(em.outputs["Emission"], mix_s.inputs[2])

            out_m = nodes.new("ShaderNodeOutputMaterial")
            out_m.location = (320, 80)
            links.new(mix_s.outputs["Shader"], out_m.inputs["Surface"])

            obj.data.materials.append(mat)
            obj.hide_render = True
            obj.hide_viewport = True
            self.planes[key] = (obj, tex)

    def _get_or_render_bpy_image(self, key: str, kwargs: Dict[str, Any]):
        import bpy  # type: ignore

        payload = json.dumps([key, kwargs], sort_keys=True, default=str)
        digest = hashlib.md5(payload.encode("utf-8")).hexdigest()[:14]
        cache_id = f"{key}_{digest}"
        if cache_id in self._bpy_images:
            return self._bpy_images[cache_id]

        png_path = os.path.join(SPRITE_CACHE_DIR, f"{cache_id}.png")
        char_inst = self._get_char_instance(key)
        if not os.path.exists(png_path):
            clean_kw = {k: v for k, v in kwargs.items() if v is not None}
            char_inst.save_frame(png_path, **clean_kw)

        img = bpy.data.images.load(png_path, check_existing=True)
        self._bpy_images[cache_id] = img
        return img

    def update_for_frame(self, frame: int) -> None:
        """Update tekstur & transformasi 3D seluruh karakter tepat sebelum me-render `frame`."""
        from mathutils import Euler, Vector  # type: ignore

        t = frame_to_sec(frame)
        cam_pos_w, _, _, _, _ = eval_camera_world(t)
        cb = w_to_b(*cam_pos_w)

        active_states = {st.actor_key: st for st in eval_actors_at_time(t)}

        for key, (obj, tex_node) in self.planes.items():
            st = active_states.get(key)
            if st is None:
                obj.hide_render = True
                obj.hide_viewport = True
                continue

            obj.hide_render = False
            obj.hide_viewport = False

            sprite_ang = _camera_relative_sprite_angle(st.pos_w, st.facing_yaw_deg, cam_pos_w)
            kw = dict(st.render_kwargs)
            kw["angle"] = sprite_ang

            bpy_img = self._get_or_render_bpy_image(key, kw)
            tex_node.image = bpy_img
            aspect = float(bpy_img.size[0]) / max(1.0, float(bpy_img.size[1]))

            ab = w_to_b(*st.pos_w)
            obj.location = Vector(ab)

            # Cylindrical world-up billboard facing camera horizontally (+ optional bed pitch!)
            rot_z = math.atan2(cb[0] - ab[0], ab[1] - cb[1])
            rot_x = math.radians(st.pitch_deg)
            obj.rotation_euler = Euler((rot_x, 0.0, rot_z), "XYZ")
            obj.scale = Vector((st.height_m * aspect, 1.0, st.height_m))
