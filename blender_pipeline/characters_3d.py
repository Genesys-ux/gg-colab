"""
Karakter 3D Sejati Bervolume Halus & Rigging 100% TERBUKA (Unlocked Armature Pose Bones)
untuk Blender 4.2+ EEVEE Next:
  1. Bima (Protagonis, 13 thn, proporsi 5.5 kepala, chunky extremities +15%, parka kuning saffron + saku robek,
     kacamata loupe kuningan di dahi, syal merah bata 40cm 3-segmen, sabuk alat kulit, freckles + oli pipi kiri)
  2. "Oren" (Kucing kampung bentuk pir gendut, mata zaitun mengantuk/arogan, telinga kanan sobek V,
     kalung toska + lonceng tembaga, cakar lebar dengan paw pads & cakar untuk [CAM 12]-[CAM 13])
  3. Hero Props Micro-PBR 3D: Kunci Emas (kepala roda gigi matahari berongga) & Kunci Perak (bulan sabit dingin)
  4. Figuran 3D Rigged: Pedagang Rempah (siluet bulat, topi jerami) & Penumpang Trem (jangkung, mantel + baret + syal)
"""

from __future__ import annotations

import math
from typing import Dict, List, Optional, Tuple

import bmesh  # type: ignore
import bpy  # type: ignore
from mathutils import Euler, Matrix, Vector  # type: ignore

from .assets_loader import find_custom_model, import_custom_model_into_collection
from .mesh_utils import (
    create_mesh_object,
    get_or_create_collection,
    link_object,
    make_beveled_box,
    make_cogwheel_3d,
    make_lathe_mesh,
    make_smooth_cylinder,
    make_smooth_sphere,
)


def _create_armature_with_bones(
    name: str,
    bone_specs: List[Tuple[str, Tuple[float, float, float], Tuple[float, float, float], Optional[str]]],
    collection,
) -> Tuple["bpy.types.Object", Dict[str, Tuple[Matrix, float]]]:
    """
    Buat Armature Blender dengan seluruh bone 100% TERBUKA (unlocked location/rotation/scale, Euler XYZ).
    Mengembalikan (arm_obj, rest_map[bone_name] = (rest_matrix_local, bone_length)).
    """
    arm_data = bpy.data.armatures.new(name + "_Data")
    arm_obj = bpy.data.objects.new(name, arm_data)
    link_object(arm_obj, collection)

    # Masuk Edit Mode khusus armature ini secara aman di mode headless
    bpy.context.view_layer.objects.active = arm_obj
    bpy.ops.object.mode_set(mode="EDIT")

    ebones = {}
    for bname, head, tail, parent_name in bone_specs:
        eb = arm_data.edit_bones.new(bname)
        eb.head = Vector(head)
        eb.tail = Vector(tail)
        if parent_name and parent_name in ebones:
            eb.parent = ebones[parent_name]
            eb.use_connect = False
        ebones[bname] = eb

    rest_map: Dict[str, Tuple[Matrix, float]] = {}
    for bname, eb in ebones.items():
        rest_map[bname] = (eb.matrix.copy(), float(eb.length))

    bpy.ops.object.mode_set(mode="OBJECT")

    # Pastikan semua PoseBone memakai Euler XYZ dan 100% UNLOCKED!
    for pb in arm_obj.pose.bones:
        pb.rotation_mode = "XYZ"
        pb.lock_location = (False, False, False)
        pb.lock_rotation = (False, False, False)
        pb.lock_scale = (False, False, False)

    return arm_obj, rest_map


def _bind_to_bone(obj, arm_obj, bone_name: str, rest_map: Dict[str, Tuple[Matrix, float]]) -> None:
    """Ikat mesh 3D ke PoseBone secara presisi tanpa geseran rest-pose (nol artefak skin-pinching!)."""
    rest_mat, bone_len = rest_map[bone_name]
    obj.parent = arm_obj
    obj.parent_type = "BONE"
    obj.parent_bone = bone_name
    parent_rest = rest_mat @ Matrix.Translation((0.0, bone_len, 0.0))
    obj.matrix_parent_inverse = parent_rest.inverted()


def build_bima_3d(mats: dict, collection=None) -> "bpy.types.Object":
    """
    Bangun karakter hero 3D Bima (~1.58m, proporsi 5.5 kepala, chunky hands/forearms/boots +15%)
    lengkap dengan Armature `Bima_Rig` 100% terbuka.
    Menghadap +Y lokal (depan karakter ke +Y, atas ke +Z, kanan karakter ke +X).
    """
    col = collection or get_or_create_collection("Characters_Hero")
    ink = mats["ink"]

    # Opsional: jika pengguna menaruh `assets/models/bima.glb`, muat model kustom tersebut
    custom = find_custom_model("bima")
    if custom:
        objs = import_custom_model_into_collection(custom, col.name)
        for o in objs:
            if o.type == "ARMATURE":
                o.name = "Bima_Rig"
                return o

    # 1. Hierarchy Tulang Biomekanik 100% Terbuka (2 segmen lengan + 2 segmen kaki + jambul + syal 3 segmen + wajah!)
    bone_specs = [
        ("Root", (0.0, 0.0, 0.0), (0.0, 0.0, 0.20), None),
        ("Pelvis", (0.0, 0.0, 0.78), (0.0, 0.0, 0.96), "Root"),
        ("Spine", (0.0, 0.0, 0.96), (0.0, 0.0, 1.14), "Pelvis"),
        ("Chest", (0.0, 0.0, 1.14), (0.0, 0.0, 1.28), "Spine"),
        ("Neck", (0.0, 0.0, 1.28), (0.0, 0.0, 1.35), "Chest"),
        ("Head", (0.0, 0.0, 1.35), (0.0, 0.0, 1.62), "Neck"),
        ("Jambul", (0.0, 0.14, 1.60), (0.0, 0.24, 1.68), "Head"),
        ("Brow_L", (-0.065, 0.155, 1.51), (-0.065, 0.18, 1.54), "Head"),
        ("Brow_R", (0.065, 0.155, 1.51), (0.065, 0.18, 1.54), "Head"),
        ("Eyelid_L", (-0.062, 0.155, 1.48), (-0.062, 0.18, 1.49), "Head"),
        ("Eyelid_R", (0.062, 0.155, 1.48), (0.062, 0.18, 1.49), "Head"),
        ("Jaw", (0.0, 0.12, 1.40), (0.0, 0.18, 1.38), "Head"),
        # Syal merah bata 40cm (secondary spring chain!)
        ("Scarf_01", (0.0, -0.10, 1.26), (0.0, -0.24, 1.18), "Chest"),
        ("Scarf_02", (0.0, -0.24, 1.18), (0.0, -0.38, 1.08), "Scarf_01"),
        ("Scarf_03", (0.0, -0.38, 1.08), (0.0, -0.52, 0.98), "Scarf_02"),
        # Lengan Kiri & Kanan (Clavicle -> UpperArm -> Forearm -> Chunky Hand!)
        ("Clavicle_L", (-0.05, 0.0, 1.23), (-0.21, 0.0, 1.22), "Chest"),
        ("UpperArm_L", (-0.21, 0.0, 1.22), (-0.26, 0.0, 0.98), "Clavicle_L"),
        ("Forearm_L", (-0.26, 0.0, 0.98), (-0.28, 0.02, 0.72), "UpperArm_L"),
        ("Hand_L", (-0.28, 0.02, 0.72), (-0.28, 0.04, 0.60), "Forearm_L"),
        ("Clavicle_R", (0.05, 0.0, 1.23), (0.21, 0.0, 1.22), "Chest"),
        ("UpperArm_R", (0.21, 0.0, 1.22), (0.26, 0.0, 0.98), "Clavicle_R"),
        ("Forearm_R", (0.26, 0.0, 0.98), (0.28, 0.02, 0.72), "UpperArm_R"),
        ("Hand_R", (0.28, 0.02, 0.72), (0.28, 0.04, 0.60), "Forearm_R"),
        # Kaki Kiri & Kanan (Thigh -> Shin -> Chunky Work Boot!)
        ("Thigh_L", (-0.10, 0.0, 0.78), (-0.11, 0.0, 0.44), "Pelvis"),
        ("Shin_L", (-0.11, 0.0, 0.44), (-0.11, -0.02, 0.14), "Thigh_L"),
        ("Foot_L", (-0.11, -0.02, 0.14), (-0.11, 0.14, 0.05), "Shin_L"),
        ("Thigh_R", (0.10, 0.0, 0.78), (0.11, 0.0, 0.44), "Pelvis"),
        ("Shin_R", (0.11, 0.0, 0.44), (0.11, -0.02, 0.14), "Thigh_R"),
        ("Foot_R", (0.11, -0.02, 0.14), (0.11, 0.14, 0.05), "Shin_R"),
    ]
    arm_obj, rest_map = _create_armature_with_bones("Bima_Rig", bone_specs, col)

    def part(obj, bone: str):
        _bind_to_bone(obj, arm_obj, bone, rest_map)
        return obj

    # 2. TORSO & JAKET PARKA KUNING KUNYIT (SAFFRON #F2B705 — Layered 3D, bukan kotak datar!)
    part(make_lathe_mesh(
        "Bima_Parka_Torso",
        [(0.18, 0.78), (0.22, 0.86), (0.21, 1.04), (0.20, 1.22), (0.14, 1.29)],
        (0, 0, 0), col, mats["bima_parka"], segments=24, cap_bottom=True, cap_top=True,
        subsurf_levels=1, ink_mat=ink, outline_thickness=0.011,
    ), "Spine")
    # Kerah tinggi jaket parka & lipatan ritsleting depan
    part(make_lathe_mesh(
        "Bima_Parka_Collar",
        [(0.13, 1.24), (0.155, 1.32), (0.145, 1.36), (0.12, 1.34)],
        (0, 0, 0), col, mats["bima_parka"], segments=22, cap_bottom=False, cap_top=False,
        subsurf_levels=1, ink_mat=ink, outline_thickness=0.008,
    ), "Chest")
    part(make_beveled_box("Bima_Parka_Placket", (0.06, 0.04, 0.46), (0.0, 0.195, 1.04), col, mats["bima_parka"], bevel_width=0.012, ink_mat=ink, outline_thickness=0.006), "Spine")
    # Saku Kiri Utuh + Saku Kanan Bawah ROBEK dengan 2 helai benang menjuntai (setup [CAM 27]!)
    part(make_beveled_box("Bima_Pocket_L", (0.11, 0.045, 0.11), (-0.11, 0.19, 0.89), col, mats["bima_parka"], bevel_width=0.014, ink_mat=ink, outline_thickness=0.006), "Pelvis")
    part(make_beveled_box("Bima_Pocket_R_Torn", (0.11, 0.045, 0.10), (0.11, 0.19, 0.89), col, mats["bima_parka"], rotation_deg=(0, 8, 0), bevel_width=0.012, ink_mat=ink, outline_thickness=0.006), "Pelvis")
    # Robekan gelap + 2 helai benang menjuntai di saku kanan
    part(make_beveled_box("Bima_Pocket_TearGap", (0.075, 0.02, 0.025), (0.11, 0.212, 0.842), col, mats["eye_dark"], bevel_width=0.004), "Pelvis")
    for ti, tx in enumerate((0.088, 0.126)):
        part(make_smooth_cylinder(f"Bima_TornThread_{ti}", 0.005, 0.003, 0.075, (tx, 0.214, 0.805), col, mats["bima_laces"], segments=8, rotation_deg=(12, -10 + ti * 22, 0)), "Pelvis")

    # Sabuk kulit tebal + kantong alat (obeng gagang biru, pinset kuningan)
    part(make_smooth_cylinder("Bima_ToolBelt", 0.225, 0.228, 0.075, (0, 0, 0.84), col, mats["bima_leather"], segments=24, bevel_width=0.010, ink_mat=ink, outline_thickness=0.007), "Pelvis")
    part(make_beveled_box("Bima_BeltBuckle", (0.09, 0.04, 0.085), (0.0, 0.222, 0.84), col, mats["brass_gold"], bevel_width=0.012, ink_mat=ink, outline_thickness=0.005), "Pelvis")
    part(make_beveled_box("Bima_ToolPouch", (0.11, 0.08, 0.14), (-0.19, 0.11, 0.79), col, mats["bima_leather"], rotation_deg=(0, 0, -25), bevel_width=0.016, ink_mat=ink, outline_thickness=0.006), "Pelvis")
    part(make_smooth_cylinder("Bima_BlueScrewdriver", 0.016, 0.014, 0.11, (-0.21, 0.12, 0.89), col, mats["prop_blue"], segments=10, rotation_deg=(8, -14, 0)), "Pelvis")
    part(make_beveled_box("Bima_BrassTweezers", (0.016, 0.012, 0.12), (-0.17, 0.13, 0.88), col, mats["brass_gold"], rotation_deg=(-8, 12, 0), bevel_width=0.003), "Pelvis")

    # 3. SYAL TIPIS MERAH BATA (40cm Secondary Motion Chain!)
    part(make_smooth_cylinder("Bima_ScarfNeck", 0.148, 0.155, 0.09, (0, 0.0, 1.29), col, mats["bima_scarf"], segments=22, bevel_width=0.018, ink_mat=ink, outline_thickness=0.009), "Chest")
    part(make_beveled_box("Bima_ScarfTail_1", (0.12, 0.17, 0.032), (0.02, -0.17, 1.22), col, mats["bima_scarf"], rotation_deg=(-28, 0, 6), bevel_width=0.012, ink_mat=ink, outline_thickness=0.008), "Scarf_01")
    part(make_beveled_box("Bima_ScarfTail_2", (0.11, 0.17, 0.028), (0.03, -0.31, 1.13), col, mats["bima_scarf"], rotation_deg=(-32, 0, 10), bevel_width=0.011, ink_mat=ink, outline_thickness=0.008), "Scarf_02")
    part(make_beveled_box("Bima_ScarfTail_3", (0.10, 0.16, 0.024), (0.04, -0.45, 1.03), col, mats["bima_scarf"], rotation_deg=(-25, 0, 14), bevel_width=0.010, ink_mat=ink, outline_thickness=0.008), "Scarf_03")

    # 4. KEPALA, WAJAH EKSPRESIF, RAMBUT RUMPUN CHUNKY, & KACAMATA LOUPE KUNINGAN
    part(make_smooth_cylinder("Bima_Neck", 0.058, 0.062, 0.10, (0, 0, 1.32), col, mats["bima_skin"], segments=16), "Neck")
    # Kepala persegi-membulat dengan tulang pipi tegas
    part(make_smooth_sphere("Bima_Head", 0.165, (0, 0.0, 1.485), col, mats["bima_skin"], scale=(0.98, 0.94, 1.06), subdivisions=3, ink_mat=ink, outline_thickness=0.011), "Head")
    part(make_smooth_sphere("Bima_Ear_L", 0.036, (-0.162, -0.01, 1.475), col, mats["bima_skin"], scale=(0.55, 0.85, 1.15), subdivisions=2, ink_mat=ink, outline_thickness=0.006), "Head")
    part(make_smooth_sphere("Bima_Ear_R", 0.036, (0.162, -0.01, 1.475), col, mats["bima_skin"], scale=(0.55, 0.85, 1.15), subdivisions=2, ink_mat=ink, outline_thickness=0.006), "Head")
    part(make_smooth_sphere("Bima_Nose", 0.024, (0.0, 0.162, 1.462), col, mats["bima_skin"], scale=(0.95, 1.15, 0.85), subdivisions=2, ink_mat=ink, outline_thickness=0.004), "Head")
    # Corengan oli mesin hitam diagonal di pipi kiri + freckles halus di pangkal hidung
    part(make_beveled_box("Bima_OilSmudge", (0.048, 0.010, 0.015), (-0.072, 0.148, 1.435), col, mats["bima_smudge"], rotation_deg=(0, -18, 26), bevel_width=0.004), "Head")
    for fi, fx in enumerate((-0.034, -0.020, 0.020, 0.034)):
        part(make_smooth_sphere(f"Bima_Freckle_{fi}", 0.0055, (fx, 0.156, 1.468 - (fi % 2) * 0.006), col, mats["bima_leather"], subdivisions=1), "Head")

    # Mata 3D, Pupil, Kilau Mata, Kelopak Animasi, & Alis Asimetris
    for side, sgn in (("L", -1.0), ("R", 1.0)):
        ex = sgn * 0.058
        part(make_smooth_sphere(f"Bima_EyeWhite_{side}", 0.030, (ex, 0.140, 1.490), col, mats["eye_white"], scale=(0.95, 0.65, 1.12), subdivisions=2, ink_mat=ink, outline_thickness=0.003), "Head")
        part(make_smooth_sphere(f"Bima_Pupil_{side}", 0.017, (ex, 0.155, 1.490), col, mats["eye_dark"], scale=(0.92, 0.55, 1.08), subdivisions=2), "Head")
        part(make_smooth_sphere(f"Bima_EyeGlint_{side}", 0.0065, (ex + 0.008, 0.163, 1.500), col, mats["emissive_lamp"], subdivisions=1), "Head")
        # Kelopak mata atas yang bisa berkedip / menyipit / bahagia!
        part(make_beveled_box(f"Bima_Eyelid_{side}", (0.064, 0.025, 0.022), (ex, 0.154, 1.515), col, mats["bima_skin"], bevel_width=0.008, ink_mat=ink, outline_thickness=0.003), f"Eyelid_{side}")
        # Alis 3D ekspresif
        part(make_beveled_box(f"Bima_Brow_{side}", (0.064, 0.018, 0.016), (ex, 0.158, 1.535), col, mats["bima_hair"], rotation_deg=(0, sgn * 6, -sgn * 14), bevel_width=0.006), f"Brow_{side}")

    # Mulut 3D ber-rahang (bisa teriak panik, terkatup fokus, atau senyum lega!)
    part(make_smooth_sphere("Bima_Mouth", 0.036, (0.0, 0.146, 1.410), col, mats["mouth_inside"], scale=(1.25, 0.55, 0.72), subdivisions=2, ink_mat=ink, outline_thickness=0.004), "Jaw")

    # Rambut Cokelat Tua Rumpun Chunky Tertiup ke Belakang (sculpted clumps, bukan helm!)
    hair_clumps = [
        (0.0, -0.04, 1.605, 0.155, (1.12, 1.10, 0.76), (12, 0, 0)),
        (-0.11, -0.03, 1.57, 0.095, (0.85, 1.15, 0.95), (16, -18, 12)),
        (0.11, -0.03, 1.57, 0.095, (0.85, 1.15, 0.95), (16, 18, -12)),
        (0.0, -0.14, 1.51, 0.115, (1.18, 0.95, 1.12), (-14, 0, 0)),
        (-0.07, -0.16, 1.58, 0.082, (0.80, 1.45, 0.70), (24, -15, 16)),
        (0.07, -0.16, 1.58, 0.082, (0.80, 1.45, 0.70), (24, 15, -16)),
        (0.0, -0.18, 1.63, 0.075, (0.90, 1.55, 0.65), (30, 0, 0)),
    ]
    for hi, (hx, hy, hz, hr, hsc, hrot) in enumerate(hair_clumps):
        part(make_smooth_sphere(f"Bima_HairClump_{hi}", hr, (hx, hy, hz), col, mats["bima_hair"], scale=hsc, rotation_deg=hrot, subdivisions=2, ink_mat=ink, outline_thickness=0.010), "Head")
    # Jambul Ikonik di Dahi (tulang terpisah agar memantul saat overshoot kamera!)
    part(make_smooth_sphere("Bima_Jambul_Hero", 0.064, (0.01, 0.155, 1.625), col, mats["bima_hair"], scale=(0.85, 1.45, 0.68), rotation_deg=(-22, 0, -10), subdivisions=2, ink_mat=ink, outline_thickness=0.008), "Jambul")

    # Kacamata Loupe Tukang Jam di Dahi (tali kulit + rangka kuningan tergores + 2 lensa kaca pembesar!)
    part(make_smooth_cylinder("Bima_GoggleStrap", 0.172, 0.172, 0.036, (0, -0.005, 1.585), col, mats["bima_leather"], segments=24, bevel_width=0.006, ink_mat=ink, outline_thickness=0.005), "Head")
    for side, sgn, r_loupe in (("L", -1.0, 0.046), ("R", 1.0, 0.056)):  # kanan lebih besar (loupe pembesar tukang jam!)
        gx = sgn * 0.064
        part(make_smooth_cylinder(f"Bima_LoupeRim_{side}", r_loupe, r_loupe, 0.044, (gx, 0.162, 1.592), col, mats["brass_gold"], segments=20, rotation_deg=(82, 0, -sgn * 14), bevel_width=0.006, ink_mat=ink, outline_thickness=0.005), "Head")
        part(make_smooth_cylinder(f"Bima_LoupeGlass_{side}", r_loupe * 0.78, r_loupe * 0.78, 0.016, (gx, 0.180, 1.594), col, mats["glass_dusty"], segments=18, rotation_deg=(82, 0, -sgn * 14)), "Head")

    # 5. LENGAN 2-SEGMEN + TELAPAK TANGAN CHUNKY (+15%)
    for side, sgn in (("L", -1.0), ("R", 1.0)):
        part(make_smooth_sphere(f"Bima_Shoulder_{side}", 0.084, (sgn * 0.21, 0.0, 1.21), col, mats["bima_parka"], subdivisions=2, ink_mat=ink, outline_thickness=0.009), f"UpperArm_{side}")
        part(make_smooth_cylinder(f"Bima_UpperArm_{side}", 0.066, 0.074, 0.25, (sgn * 0.235, 0.0, 1.10), col, mats["bima_parka"], segments=16, rotation_deg=(0, sgn * 12, 0), bevel_width=0.012, ink_mat=ink, outline_thickness=0.009), f"UpperArm_{side}")
        part(make_smooth_sphere(f"Bima_Elbow_{side}", 0.064, (sgn * 0.26, 0.0, 0.98), col, mats["bima_parka"], subdivisions=2), f"Forearm_{side}")
        # Lengan bawah +15% chunky dengan manset jaket
        part(make_smooth_cylinder(f"Bima_Forearm_{side}", 0.072, 0.064, 0.27, (sgn * 0.27, 0.01, 0.85), col, mats["bima_parka"], segments=16, rotation_deg=(4, sgn * 5, 0), bevel_width=0.014, ink_mat=ink, outline_thickness=0.009), f"Forearm_{side}")
        # Telapak tangan chunky +15% dengan ibu jari 3D (dramatis saat meraih kunci!)
        part(make_smooth_sphere(f"Bima_HandPalm_{side}", 0.068, (sgn * 0.28, 0.03, 0.68), col, mats["bima_skin"], scale=(0.95, 0.72, 1.25), subdivisions=2, ink_mat=ink, outline_thickness=0.008), f"Hand_{side}")
        part(make_smooth_sphere(f"Bima_HandThumb_{side}", 0.028, (sgn * 0.22, 0.055, 0.69), col, mats["bima_skin"], scale=(0.85, 0.85, 1.45), rotation_deg=(0, -sgn * 28, 0), subdivisions=2), f"Hand_{side}")

    # 6. CELANA KARGO BIRU DONGKER DIGULUNG + SEPATU BOT KERJA CHUNKY (+15%) BERTALI ORANYE
    part(make_smooth_sphere("Bima_Pelvis_Pants", 0.185, (0.0, 0.0, 0.78), col, mats["bima_navy"], scale=(1.08, 0.92, 0.75), subdivisions=2, ink_mat=ink, outline_thickness=0.010), "Pelvis")
    for side, sgn in (("L", -1.0), ("R", 1.0)):
        part(make_smooth_cylinder(f"Bima_Thigh_{side}", 0.088, 0.098, 0.35, (sgn * 0.105, 0.0, 0.61), col, mats["bima_navy"], segments=16, bevel_width=0.014, ink_mat=ink, outline_thickness=0.009), f"Thigh_{side}")
        part(make_smooth_sphere(f"Bima_Knee_{side}", 0.082, (sgn * 0.11, 0.01, 0.44), col, mats["bima_navy"], subdivisions=2), f"Shin_{side}")
        part(make_smooth_cylinder(f"Bima_Shin_{side}", 0.076, 0.084, 0.28, (sgn * 0.11, -0.01, 0.30), col, mats["bima_navy"], segments=16, bevel_width=0.012, ink_mat=ink, outline_thickness=0.009), f"Shin_{side}")
        # Lipatan celana digulung di mata kaki
        part(make_smooth_cylinder(f"Bima_PantCuff_{side}", 0.088, 0.088, 0.055, (sgn * 0.11, -0.01, 0.19), col, mats["bima_navy"], segments=16, bevel_width=0.014, ink_mat=ink, outline_thickness=0.007), f"Shin_{side}")
        # Sepatu bot kulit cokelat tua chunky +15% + sol tebal + tali sepatu oranye menyala!
        part(make_smooth_cylinder(f"Bima_BootAnkle_{side}", 0.078, 0.082, 0.13, (sgn * 0.11, -0.01, 0.11), col, mats["bima_leather"], segments=16, bevel_width=0.012, ink_mat=ink, outline_thickness=0.008), f"Foot_{side}")
        part(make_smooth_sphere(f"Bima_BootToe_{side}", 0.095, (sgn * 0.11, 0.09, 0.068), col, mats["bima_leather"], scale=(0.95, 1.48, 0.72), subdivisions=2, ink_mat=ink, outline_thickness=0.009), f"Foot_{side}")
        part(make_beveled_box(f"Bima_BootSole_{side}", (0.175, 0.295, 0.042), (sgn * 0.11, 0.06, 0.022), col, mats["iron_dark"], bevel_width=0.012), f"Foot_{side}")
        for li, lz in enumerate((0.09, 0.12, 0.15)):
            part(make_beveled_box(f"Bima_Lace_{side}_{li}", (0.095, 0.028, 0.016), (sgn * 0.11, 0.072 - li * 0.01, lz), col, mats["bima_laces"], bevel_width=0.005), f"Foot_{side}")

    return arm_obj


def build_oren_3d(mats: dict, collection=None) -> "bpy.types.Object":
    """
    Bangun "Oren" — Kucing Kampung Gang Kafe bertubuh pir gendut + bulu rumpun + mata zaitun mengantuk,
    telinga kanan sobek V, kalung toska + lonceng tembaga, cakar depan lebar berpaw-pad, rig 100% terbuka!
    """
    col = collection or get_or_create_collection("Characters_Hero")
    ink = mats["ink"]

    bone_specs = [
        ("Root", (0.0, 0.0, 0.0), (0.0, 0.0, 0.12), None),
        ("Body", (0.0, 0.0, 0.16), (0.0, 0.0, 0.44), "Root"),
        ("Head", (0.0, 0.04, 0.46), (0.0, 0.06, 0.68), "Body"),
        ("Eyelid_L", (-0.062, 0.16, 0.56), (-0.062, 0.19, 0.57), "Head"),
        ("Eyelid_R", (0.062, 0.16, 0.56), (0.062, 0.19, 0.57), "Head"),
        ("RightPaw_Slap", (0.14, 0.10, 0.34), (0.18, 0.22, 0.14), "Body"),
        ("Bell", (0.0, 0.17, 0.41), (0.0, 0.18, 0.34), "Body"),
        ("Tail_01", (0.0, -0.18, 0.16), (0.0, -0.34, 0.24), "Body"),
        ("Tail_02", (0.0, -0.34, 0.24), (0.0, -0.44, 0.40), "Tail_01"),
        ("Tail_03", (0.0, -0.44, 0.40), (0.0, -0.40, 0.56), "Tail_02"),
    ]
    arm_obj, rest_map = _create_armature_with_bones("Oren_Rig", bone_specs, col)

    def part(obj, bone: str):
        _bind_to_bone(obj, arm_obj, bone, rest_map)
        return obj

    # Tubuh gendut seperti buah pir (pear-shaped) + perut krem kotor + belang oranye!
    part(make_lathe_mesh(
        "Oren_PearBody",
        [(0.18, 0.04), (0.26, 0.14), (0.25, 0.28), (0.20, 0.40), (0.16, 0.47)],
        (0, 0, 0), col, mats["oren_fur"], segments=26, cap_bottom=True, cap_top=True,
        subsurf_levels=1, ink_mat=ink, outline_thickness=0.011,
    ), "Body")
    part(make_smooth_sphere("Oren_BellyCream", 0.185, (0.0, 0.10, 0.22), col, mats["oren_belly"], scale=(0.88, 0.72, 1.12), subdivisions=2), "Body")
    # Pola belang punggung oranye gelap
    for bi, bz in enumerate((0.20, 0.30, 0.39)):
        part(make_smooth_cylinder(f"Oren_Stripe_{bi}", 0.245 - bi * 0.025, 0.240 - bi * 0.025, 0.038, (0, -0.02, bz), col, mats["oren_stripe"], segments=22), "Body")

    # Kaki belakang pendek + kaki depan kiri menumpu
    for sx in (-0.15, 0.15):
        part(make_smooth_sphere(f"Oren_HindFoot_{sx:.2f}", 0.085, (sx, 0.04, 0.065), col, mats["oren_belly"], scale=(0.95, 1.35, 0.72), subdivisions=2, ink_mat=ink, outline_thickness=0.008), "Body")
    part(make_smooth_cylinder("Oren_LeftArm", 0.062, 0.056, 0.24, (-0.13, 0.13, 0.18), col, mats["oren_fur"], segments=16, bevel_width=0.012, ink_mat=ink, outline_thickness=0.008), "Body")
    part(make_smooth_sphere("Oren_LeftPaw", 0.072, (-0.13, 0.16, 0.06), col, mats["oren_belly"], scale=(1.1, 1.25, 0.70), subdivisions=2, ink_mat=ink, outline_thickness=0.008), "Body")

    # Cakar Depan Kanan Lebar & Ekspresif (Hero Slap Paw untuk [CAM 12]-[CAM 13]!)
    part(make_smooth_cylinder("Oren_RightArm", 0.064, 0.058, 0.24, (0.15, 0.14, 0.23), col, mats["oren_fur"], segments=16, rotation_deg=(28, 0, -14), bevel_width=0.012, ink_mat=ink, outline_thickness=0.009), "RightPaw_Slap")
    part(make_smooth_sphere("Oren_RightPawWide", 0.082, (0.17, 0.21, 0.12), col, mats["oren_belly"], scale=(1.22, 0.78, 1.10), subdivisions=2, ink_mat=ink, outline_thickness=0.009), "RightPaw_Slap")
    # Bantalan cakar (paw pads merah muda) + 3 kuku tajam di sisi depan telapak
    part(make_smooth_sphere("Oren_MainPad", 0.038, (0.17, 0.258, 0.115), col, mats["oren_nose_pink"], scale=(1.15, 0.45, 0.95), subdivisions=2), "RightPaw_Slap")
    for ti, tx in enumerate((-0.036, 0.0, 0.036)):
        part(make_smooth_sphere(f"Oren_ToePad_{ti}", 0.018, (0.17 + tx, 0.262, 0.158 - abs(tx) * 0.2), col, mats["oren_nose_pink"], scale=(0.9, 0.45, 1.0), subdivisions=1), "RightPaw_Slap")
        part(make_smooth_cylinder(f"Oren_Claw_{ti}", 0.008, 0.001, 0.036, (0.17 + tx, 0.256, 0.186), col, mats["porcelain"], segments=8, rotation_deg=(35, 0, 0)), "RightPaw_Slap")

    # Kepala bulat + rumpun bulu pipi tebal + moncong + hidung merah muda + kumis asimetris
    part(make_smooth_sphere("Oren_Head", 0.165, (0.0, 0.03, 0.56), col, mats["oren_fur"], scale=(1.18, 0.96, 0.92), subdivisions=3, ink_mat=ink, outline_thickness=0.011), "Head")
    for sgn in (-1.0, 1.0):
        part(make_smooth_sphere(f"Oren_CheekFluff_{sgn:.0f}", 0.072, (sgn * 0.165, 0.04, 0.525), col, mats["oren_fur"], scale=(1.25, 0.85, 0.78), subdivisions=2, ink_mat=ink, outline_thickness=0.008), "Head")
    part(make_smooth_sphere("Oren_Muzzle", 0.068, (0.0, 0.152, 0.520), col, mats["oren_belly"], scale=(1.25, 0.75, 0.78), subdivisions=2), "Head")
    part(make_smooth_sphere("Oren_Nose", 0.024, (0.0, 0.196, 0.542), col, mats["oren_nose_pink"], scale=(1.2, 0.8, 0.8), subdivisions=2, ink_mat=ink, outline_thickness=0.004), "Head")

    # Telinga Kiri utuh + Telinga Kanan SOBEK BERBENTUK HURUF V (ciri khas preman gang!)
    part(make_smooth_cylinder("Oren_Ear_L", 0.064, 0.008, 0.145, (-0.115, 0.02, 0.70), col, mats["oren_fur"], segments=12, rotation_deg=(6, -18, 0), bevel_width=0.006, ink_mat=ink, outline_thickness=0.008), "Head")
    part(make_smooth_cylinder("Oren_Ear_R_Base", 0.064, 0.032, 0.095, (0.115, 0.02, 0.68), col, mats["oren_fur"], segments=12, rotation_deg=(6, 18, 0), bevel_width=0.006, ink_mat=ink, outline_thickness=0.008), "Head")
    part(make_smooth_cylinder("Oren_Ear_R_TipA", 0.022, 0.006, 0.055, (0.095, 0.02, 0.74), col, mats["oren_fur"], segments=10, rotation_deg=(6, 4, 0)), "Head")
    part(make_smooth_cylinder("Oren_Ear_R_TipB", 0.018, 0.005, 0.042, (0.142, 0.02, 0.73), col, mats["oren_fur"], segments=10, rotation_deg=(6, 32, 0)), "Head")

    # Mata Hijau Zaitun Setengah Terpejam (heavy-lidded arogan!)
    for side, sgn in (("L", -1.0), ("R", 1.0)):
        ex = sgn * 0.064
        part(make_smooth_sphere(f"Oren_Eye_{side}", 0.034, (ex, 0.148, 0.575), col, mats["oren_eye_olive"], scale=(1.1, 0.65, 1.0), subdivisions=2, ink_mat=ink, outline_thickness=0.004), "Head")
        part(make_smooth_sphere(f"Oren_Pupil_{side}", 0.016, (ex, 0.166, 0.572), col, mats["eye_dark"], scale=(0.48, 0.55, 1.35), subdivisions=2), "Head")
        # Kelopak tebal mengantuk/acuh tak acuh
        part(make_beveled_box(f"Oren_HeavyLid_{side}", (0.078, 0.036, 0.036), (ex, 0.160, 0.594), col, mats["oren_fur"], rotation_deg=(0, sgn * 8, 0), bevel_width=0.010, ink_mat=ink, outline_thickness=0.004), f"Eyelid_{side}")

    # Kumis kaku asimetris
    for side_s, angs in ((-1.0, (-8, 4, 16)), (1.0, (-12, 2, 20))):
        for wi, wang in enumerate(angs):
            part(make_smooth_cylinder(f"Oren_Whisker_{side_s:.0f}_{wi}", 0.0035, 0.0015, 0.14 + wi * 0.01, (side_s * 0.13, 0.16, 0.525 - wi * 0.012), col, mats["porcelain"], segments=6, rotation_deg=(0, 90 + side_s * wang, -side_s * 12)), "Head")

    # Kalung kain biru toska pudar + lonceng tembaga tua penyok!
    part(make_smooth_cylinder("Oren_Collar", 0.175, 0.180, 0.044, (0, 0.02, 0.445), col, mats["oren_collar_teal"], segments=22, bevel_width=0.010, ink_mat=ink, outline_thickness=0.007), "Body")
    part(make_smooth_sphere("Oren_CopperBell", 0.042, (0.0, 0.185, 0.405), col, mats["oren_bell_copper"], scale=(1.05, 0.94, 0.96), subdivisions=2, ink_mat=ink, outline_thickness=0.006), "Bell")

    # Ekor tebal belang 3-segmen (bergoyang malas)
    part(make_smooth_cylinder("Oren_Tail1", 0.052, 0.056, 0.22, (0, -0.26, 0.20), col, mats["oren_fur"], segments=14, rotation_deg=(62, 0, 0), bevel_width=0.012, ink_mat=ink, outline_thickness=0.009), "Tail_01")
    part(make_smooth_cylinder("Oren_Tail2", 0.056, 0.052, 0.22, (0, -0.39, 0.32), col, mats["oren_stripe"], segments=14, rotation_deg=(34, 0, 0), bevel_width=0.012, ink_mat=ink, outline_thickness=0.009), "Tail_02")
    part(make_smooth_sphere("Oren_TailTip", 0.058, (0, -0.42, 0.49), col, mats["oren_fur"], scale=(0.95, 0.95, 1.45), subdivisions=2, ink_mat=ink, outline_thickness=0.009), "Tail_03")

    return arm_obj


def build_golden_key_3d(mats: dict, collection=None) -> "bpy.types.Object":
    """
    Hero Prop #1: KUNCI EMAS (Master Clock Key, kepala roda gigi matahari berongga
    sehingga sinar Low Sun menembus celah tengahnya saat [CAM 01]!).
    """
    col = collection or get_or_create_collection("Hero_Props")
    root = bpy.data.objects.new("Hero_Golden_Key", None)
    link_object(root, col)
    ink = mats["ink"]

    # Kepala kunci: roda gigi matahari berongga + ukiran cincin dalam
    bow = make_cogwheel_3d(
        "GoldKey_SunBow", outer_r=0.145, thickness=0.036, teeth=12,
        location=(0.0, 0.0, 0.145), collection=col, mat=mats["hero_gold_key"],
        hollow_ratio=0.52, spokes=4, ink_mat=ink, outline_thickness=0.006,
    )
    bow.parent = root

    # Leher berundak & batang utama kunci ber-bevel
    collar = make_smooth_cylinder("GoldKey_Collar", 0.044, 0.034, 0.045, (0, 0, -0.01), col, mats["brass_dark"], segments=18, bevel_width=0.006, ink_mat=ink, outline_thickness=0.005)
    collar.parent = root
    shaft = make_smooth_cylinder("GoldKey_Shaft", 0.022, 0.025, 0.30, (0, 0, -0.17), col, mats["hero_gold_key"], segments=18, bevel_width=0.006, ink_mat=ink, outline_thickness=0.005)
    shaft.parent = root
    tip = make_smooth_sphere("GoldKey_Tip", 0.026, (0, 0, -0.32), col, mats["hero_gold_key"], subdivisions=2, ink_mat=ink, outline_thickness=0.004)
    tip.parent = root

    # Gigi kunci mekanis berukir (bit)
    bit_main = make_beveled_box("GoldKey_BitMain", (0.115, 0.028, 0.095), (0.062, 0, -0.255), col, mats["hero_gold_key"], bevel_width=0.006, ink_mat=ink, outline_thickness=0.005)
    bit_main.parent = root
    bit_notch = make_beveled_box("GoldKey_BitNotch", (0.042, 0.032, 0.048), (0.072, 0, -0.228), col, mats["brass_dark"], bevel_width=0.004)
    bit_notch.parent = root
    return root


def build_silver_key_3d(mats: dict, collection=None) -> "bpy.types.Object":
    """
    Hero Prop #2: KUNCI PERAK (Plot Twist Key [CAM 27]-[CAM 28]):
    Lebih ramping, kepala bulan sabit mekanis + gerigi tajam, baja perak dingin kebiruan (#D6E4F0)!
    """
    col = collection or get_or_create_collection("Hero_Props")
    root = bpy.data.objects.new("Hero_Silver_Key", None)
    link_object(root, col)
    ink = mats["ink"]

    # Kepala kunci bulan sabit mekanis (kurva C tebal + roda gigi mini di dalam lengkungan!)
    c_data = bpy.data.curves.new("SilverKey_CrescentCurve", type="CURVE")
    c_data.dimensions = "3D"
    c_data.bevel_depth = 0.024
    c_data.bevel_resolution = 6
    sp = c_data.splines.new("POLY")
    n_pts = 18
    sp.points.add(n_pts - 1)
    for i in range(n_pts):
        ang = math.radians(-125.0 + (250.0 * i) / (n_pts - 1))
        sp.points[i].co = (math.cos(ang) * 0.105, 0.0, 0.115 + math.sin(ang) * 0.105, 1.0)
    crescent = bpy.data.objects.new("SilverKey_CrescentBow", c_data)
    link_object(crescent, col)
    crescent.data.materials.append(mats["hero_silver_key"])
    crescent.parent = root

    inner_cog = make_cogwheel_3d(
        "SilverKey_InnerCog", outer_r=0.055, thickness=0.022, teeth=8,
        location=(-0.032, 0.0, 0.115), collection=col, mat=mats["hero_silver_key"],
        hollow_ratio=0.45, spokes=3, ink_mat=ink, outline_thickness=0.004,
    )
    inner_cog.parent = root

    shaft = make_smooth_cylinder("SilverKey_Shaft", 0.016, 0.018, 0.26, (0, 0, -0.12), col, mats["hero_silver_key"], segments=16, bevel_width=0.004, ink_mat=ink, outline_thickness=0.004)
    shaft.parent = root

    for ti, tz in enumerate((-0.17, -0.21, -0.245)):
        tooth = make_beveled_box(f"SilverKey_Tooth_{ti}", (0.075 - ti * 0.01, 0.020, 0.024), (0.044, 0, tz), col, mats["hero_silver_key"], bevel_width=0.004, ink_mat=ink, outline_thickness=0.004)
        tooth.parent = root
    return root


def build_pedagang_rempah_3d(name: str, mats: dict, collection=None) -> "bpy.types.Object":
    """Figuran Pasar: Pedagang Rempah berbadan bulat ramah, apron goni, topi jerami lebar (bone terpisah!)."""
    col = collection or get_or_create_collection("Characters_Extras")
    ink = mats["ink"]
    bone_specs = [
        ("Root", (0, 0, 0), (0, 0, 0.2), None),
        ("Body", (0, 0, 0.65), (0, 0, 1.25), "Root"),
        ("Head", (0, 0, 1.32), (0, 0, 1.62), "Body"),
        ("Hat", (0, 0, 1.60), (0, 0, 1.82), "Head"),
        ("Arm_L", (-0.34, 0, 1.20), (-0.42, 0, 0.80), "Body"),
        ("Arm_R", (0.34, 0, 1.20), (0.42, 0, 0.80), "Body"),
    ]
    arm_obj, rest_map = _create_armature_with_bones(name, bone_specs, col)

    def part(obj, bone: str):
        _bind_to_bone(obj, arm_obj, bone, rest_map)
        return obj

    # Badan bulat gendut + apron goni + baju merah terakota (NON-SAFFRON!)
    part(make_smooth_sphere(f"{name}_Torso", 0.36, (0, 0, 0.96), col, mats["pedagang_shirt"], scale=(1.08, 0.96, 1.15), subdivisions=2, ink_mat=ink, outline_thickness=0.014), "Body")
    part(make_beveled_box(f"{name}_Apron", (0.42, 0.14, 0.64), (0, 0.27, 0.84), col, mats["burlap"], bevel_width=0.03, ink_mat=ink, outline_thickness=0.010), "Body")
    for sgn in (-1.0, 1.0):
        part(make_smooth_cylinder(f"{name}_Leg_{sgn:.0f}", 0.10, 0.11, 0.58, (sgn * 0.15, 0, 0.32), col, mats["bima_navy"], segments=14, bevel_width=0.012, ink_mat=ink, outline_thickness=0.010), "Body")
        part(make_smooth_cylinder(f"{name}_Arm_{sgn:.0f}", 0.085, 0.075, 0.44, (sgn * 0.39, 0.04, 1.00), col, mats["pedagang_shirt"], segments=14, rotation_deg=(12, sgn * 16, 0), bevel_width=0.012, ink_mat=ink, outline_thickness=0.010), "Arm_L" if sgn < 0 else "Arm_R")
    part(make_smooth_sphere(f"{name}_Head", 0.18, (0, 0, 1.48), col, mats["bima_skin"], subdivisions=2, ink_mat=ink, outline_thickness=0.012), "Head")
    part(make_beveled_box(f"{name}_Mustache", (0.14, 0.04, 0.035), (0, 0.175, 1.44), col, mats["bima_hair"], bevel_width=0.012), "Head")
    # Topi jerami lebar berkubah di bone `Hat` (bisa terangkat kaget saat ledakan kunyit!)
    part(make_lathe_mesh(
        f"{name}_StrawHat",
        [(0.48, 1.60), (0.34, 1.64), (0.21, 1.67), (0.18, 1.80), (0.04, 1.84)],
        (0, 0, 0), col, mats["pedagang_hat"], segments=24, cap_bottom=True, cap_top=True,
        subsurf_levels=1, ink_mat=ink, outline_thickness=0.012,
    ), "Hat")
    return arm_obj


def build_penumpang_trem_3d(name: str, mats: dict, collection=None) -> "bpy.types.Object":
    """Figuran Stasiun Trem: Siluet jangkung, mantel klasik hijau lumut, baret & syal berkibar mundur!"""
    col = collection or get_or_create_collection("Characters_Extras")
    ink = mats["ink"]
    bone_specs = [
        ("Root", (0, 0, 0), (0, 0, 0.2), None),
        ("Body", (0, 0, 0.85), (0, 0, 1.45), "Root"),
        ("Head", (0, 0, 1.54), (0, 0, 1.84), "Body"),
        ("Beret", (0, 0, 1.80), (0, 0, 1.94), "Head"),
        ("Scarf", (0, -0.10, 1.48), (0, -0.45, 1.42), "Body"),
    ]
    arm_obj, rest_map = _create_armature_with_bones(name, bone_specs, col)

    def part(obj, bone: str):
        _bind_to_bone(obj, arm_obj, bone, rest_map)
        return obj

    # Mantel panjang jangkung
    part(make_lathe_mesh(
        f"{name}_Coat",
        [(0.30, 0.42), (0.26, 0.82), (0.22, 1.24), (0.24, 1.46), (0.14, 1.54)],
        (0, 0, 0), col, mats["penumpang_coat"], segments=20, cap_bottom=True, cap_top=True,
        subsurf_levels=1, ink_mat=ink, outline_thickness=0.013,
    ), "Body")
    for sgn in (-1.0, 1.0):
        part(make_smooth_cylinder(f"{name}_Leg_{sgn:.0f}", 0.068, 0.072, 0.48, (sgn * 0.11, 0, 0.24), col, mats["iron_dark"], segments=12, ink_mat=ink, outline_thickness=0.008), "Body")
    part(make_smooth_sphere(f"{name}_Head", 0.155, (0, 0, 1.68), col, mats["bima_skin"], scale=(0.92, 0.95, 1.10), subdivisions=2, ink_mat=ink, outline_thickness=0.011), "Head")
    part(make_smooth_sphere(f"{name}_Beret", 0.195, (0.03, -0.02, 1.83), col, mats["penumpang_beret"], scale=(1.15, 1.08, 0.42), rotation_deg=(-8, 12, 0), subdivisions=2, ink_mat=ink, outline_thickness=0.010), "Beret")
    # Syal melayang mundur & koper kulit klasik
    part(make_beveled_box(f"{name}_ScarfTail", (0.12, 0.42, 0.032), (0.0, -0.26, 1.48), col, mats["penumpang_scarf"], rotation_deg=(12, 0, 0), bevel_width=0.012, ink_mat=ink, outline_thickness=0.008), "Scarf")
    part(make_beveled_box(f"{name}_Suitcase", (0.18, 0.48, 0.34), (0.34, 0.05, 0.48), col, mats["bima_leather"], bevel_width=0.03, ink_mat=ink, outline_thickness=0.010), "Body")
    return arm_obj
