"""
Pembangun 6 Lokasi 3D Terpadu Berdetail Halus (Beveled, Lathe, Draped Cloth, Subsurf, Inverted-Hull Ink)
untuk Continuous One-Take Virtual Camera 58 Detik di Blender 4.2+ EEVEE Next.

Koordinat Blender Z-Up (dikonversi konsisten via `w_to_b(x, y_up, z_fwd)`):
  - X = kanan/kiri
  - Y = jalur maju sepanjang 6 lokasi (y = 0 Bengkel -> y = 118 Menara Jam!)
  - Z = ketinggian vertikal (z = 26 Loteng -> z = 5 Gang Kafe -> z = -17 Gorong-Gorong -> z = 19.5 Menara Jam!)
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, List, Tuple

import bpy  # type: ignore
from mathutils import Vector  # type: ignore

from .config import w_to_b
from .mesh_utils import (
    get_or_create_collection,
    link_object,
    make_beveled_box,
    make_cogwheel_3d,
    make_draped_canopy_3d,
    make_helix_spring,
    make_lathe_mesh,
    make_potted_bougainvillea_3d,
    make_seagull_3d,
    make_smooth_cylinder,
    make_smooth_sphere,
    make_spice_sack_3d,
    make_teacup_and_saucer_3d,
    make_vintage_tram_3d,
)


@dataclass
class SceneHandles:
    """Referensi seluruh objek 3D dinamis yang akan dianimasikan di `animation_director.py`."""

    fg_hanging_gears: List["bpy.types.Object"] = field(default_factory=list)
    underground_gears: List[Tuple["bpy.types.Object", float]] = field(default_factory=list)
    tram_root: "bpy.types.Object | None" = None
    clock_minute_hand: "bpy.types.Object | None" = None
    clock_hour_hand: "bpy.types.Object | None" = None
    loop_gears: List["bpy.types.Object"] = field(default_factory=list)
    station_seagulls: List[Tuple["bpy.types.Object", "bpy.types.Object", "bpy.types.Object", int]] = field(default_factory=list)
    harbor_seagulls: List[Tuple["bpy.types.Object", "bpy.types.Object", "bpy.types.Object", int]] = field(default_factory=list)
    turmeric_puffs: List["bpy.types.Object"] = field(default_factory=list)
    emerald_puffs: List["bpy.types.Object"] = field(default_factory=list)
    klak_sparks: List["bpy.types.Object"] = field(default_factory=list)
    silver_sparkle: "bpy.types.Object | None" = None
    crimson_sun_orb: "bpy.types.Object | None" = None


def _build_lokasi_1_bengkel(mats: dict, handles: SceneHandles) -> None:
    col = get_or_create_collection("Loc1_Bengkel_Loteng")
    ink = mats["ink"]

    # Lantai, langit-langit, dinding kiri/kanan/belakang + balok kayu oak
    make_beveled_box("L1_Floor", (9.0, 9.2, 0.35), w_to_b(0, 24.8, 0.0), col, mats["oak_dark"], bevel_width=0.04)
    make_beveled_box("L1_Ceiling", (9.5, 9.6, 0.40), w_to_b(0, 30.8, 0.0), col, mats["oak_dark"], bevel_width=0.04)
    make_beveled_box("L1_Wall_L", (0.35, 9.2, 6.2), w_to_b(-4.4, 27.8, 0.0), col, mats["plaster_warm"], bevel_width=0.04)
    make_beveled_box("L1_Wall_R", (0.35, 9.2, 6.2), w_to_b(4.4, 27.8, 0.0), col, mats["plaster_warm"], bevel_width=0.04)
    make_beveled_box("L1_Wall_Back", (9.0, 0.35, 6.2), w_to_b(0, 27.8, -4.5), col, mats["tower_stone"], bevel_width=0.04)
    for bi, bz in enumerate((-3.2, -1.0, 1.4, 3.6)):
        make_beveled_box(f"L1_Beam_{bi}", (8.8, 0.34, 0.38), w_to_b(0, 30.35, bz), col, mats["oak_dark"], bevel_width=0.03, ink_mat=ink, outline_thickness=0.012)

    # Dinding jendela terbuka menghadap kota pesisir + daun jendela kayu cat biru-toska terkelupas
    make_beveled_box("L1_WinWall_L", (2.9, 0.38, 6.2), w_to_b(-3.0, 27.8, 4.2), col, mats["plaster_warm"], bevel_width=0.03)
    make_beveled_box("L1_WinWall_R", (2.9, 0.38, 6.2), w_to_b(3.0, 27.8, 4.2), col, mats["plaster_warm"], bevel_width=0.03)
    make_beveled_box("L1_WinWall_Bot", (3.4, 0.38, 1.5), w_to_b(0, 25.55, 4.2), col, mats["plaster_warm"], bevel_width=0.03)
    make_beveled_box("L1_WinWall_Top", (3.4, 0.38, 1.8), w_to_b(0, 29.85, 4.2), col, mats["plaster_warm"], bevel_width=0.03)
    make_beveled_box("L1_WinSill", (3.45, 0.62, 0.18), w_to_b(0, 26.32, 4.25), col, mats["plaster_teal"], bevel_width=0.03, ink_mat=ink, outline_thickness=0.012)
    make_beveled_box("L1_WinHeader", (3.45, 0.50, 0.18), w_to_b(0, 28.95, 4.25), col, mats["plaster_teal"], bevel_width=0.03, ink_mat=ink, outline_thickness=0.012)
    make_beveled_box("L1_WinJamb_L", (0.18, 0.50, 2.75), w_to_b(-1.62, 27.65, 4.25), col, mats["plaster_teal"], bevel_width=0.03, ink_mat=ink, outline_thickness=0.012)
    make_beveled_box("L1_WinJamb_R", (0.18, 0.50, 2.75), w_to_b(1.62, 27.65, 4.25), col, mats["plaster_teal"], bevel_width=0.03, ink_mat=ink, outline_thickness=0.012)
    make_beveled_box("L1_Shutter_L", (0.10, 1.15, 2.55), w_to_b(-2.15, 27.65, 4.82), col, mats["plaster_teal"], rotation_deg=(0, 0, 34), bevel_width=0.02, ink_mat=ink, outline_thickness=0.012)
    make_beveled_box("L1_Shutter_R", (0.10, 1.15, 2.55), w_to_b(2.15, 27.65, 4.82), col, mats["plaster_teal"], rotation_deg=(0, 0, -34), bevel_width=0.02, ink_mat=ink, outline_thickness=0.012)

    # Meja kerja kayu oak penuh goresan + kaki meja
    make_beveled_box("L1_Workbench", (4.6, 3.2, 0.18), w_to_b(0, 26.0, 2.1), col, mats["oak_wood"], bevel_width=0.035, ink_mat=ink, outline_thickness=0.010)
    for lx in (-2.05, 2.05):
        for lz in (0.75, 3.45):
            make_beveled_box(f"L1_Leg_{lx:.1f}_{lz:.1f}", (0.18, 0.18, 1.15), w_to_b(lx, 25.4, lz), col, mats["oak_dark"], bevel_width=0.025)

    # Hero Prop Cangkir Teh Porselen + Tatakan (target pantulan [CAM 03]!)
    make_teacup_and_saucer_3d("L1_Hero_Teacup", w_to_b(0.55, 26.09, 1.55), col, mats["porcelain"], mats["tea_liquid"], mats["prop_red"], ink_mat=ink)

    # Roda gigi kuningan berserakan di meja
    desk_gears = [
        (-1.25, 26.12, 1.20, 0.24, 10, mats["brass_gold"]),
        (-0.82, 26.12, 1.75, 0.17, 8, mats["brass_dark"]),
        (-1.45, 26.12, 2.45, 0.30, 12, mats["brass_gold"]),
        (1.15, 26.12, 2.15, 0.26, 12, mats["brass_gold"]),
        (0.92, 26.12, 2.85, 0.19, 10, mats["oren_bell_copper"]),
        (-0.35, 26.12, 2.95, 0.22, 10, mats["brass_gold"]),
        (1.55, 26.12, 1.15, 0.28, 12, mats["brass_dark"]),
    ]
    for gi, (gx, gy, gz, gr, gt, gm) in enumerate(desk_gears):
        make_cogwheel_3d(f"L1_DeskGear_{gi}", gr, 0.055, gt, w_to_b(gx, gy, gz), col, gm, rotation_deg=(90, 0, gx * 40), ink_mat=ink, outline_thickness=0.005)

    # Obeng warna-warni & kaca pembesar sejajar jalur gulir [CAM 04]
    for oi, (ox, oz, omat, oang) in enumerate([
        (-0.65, 2.20, mats["prop_blue"], 28),
        (-0.18, 2.58, mats["prop_red"], -18),
        (0.75, 2.65, mats["prop_green"], 42),
    ]):
        make_smooth_cylinder(f"L1_ScrewHandle_{oi}", 0.042, 0.046, 0.24, w_to_b(ox, 26.14, oz), col, omat, segments=14, rotation_deg=(90, 0, oang), ink_mat=ink, outline_thickness=0.004)
        make_smooth_cylinder(f"L1_ScrewShaft_{oi}", 0.012, 0.012, 0.28, w_to_b(ox + 0.16, 26.14, oz + 0.08), col, mats["steel_bright"], segments=10, rotation_deg=(90, 0, oang))
    # Kaca pembesar
    make_smooth_cylinder("L1_MagRim", 0.18, 0.18, 0.04, w_to_b(-0.85, 26.14, 2.95), col, mats["brass_gold"], segments=24, ink_mat=ink, outline_thickness=0.005)
    make_smooth_cylinder("L1_MagGlass", 0.148, 0.148, 0.025, w_to_b(-0.85, 26.145, 2.95), col, mats["glass_dusty"], segments=22)
    make_smooth_cylinder("L1_MagHandle", 0.030, 0.038, 0.34, w_to_b(-1.14, 26.14, 3.12), col, mats["oak_dark"], segments=12, rotation_deg=(90, 0, 60), ink_mat=ink, outline_thickness=0.005)

    # 4 Toples Kaca berleher lengkung berisi PEGAS SPIRAL 3D warna-warni!
    jar_prof = [(0.17, 0.0), (0.19, 0.05), (0.19, 0.38), (0.15, 0.45), (0.15, 0.50)]
    for ji, (jx, jz, smat) in enumerate([
        (-1.82, 1.35, mats["prop_red"]),
        (-1.72, 2.05, mats["canopy_teal"]),
        (-1.86, 2.85, mats["prop_orange"]),
        (1.88, 2.85, mats["prop_magenta"]),
    ]):
        make_lathe_mesh(f"L1_JarGlass_{ji}", jar_prof, w_to_b(jx, 26.09, jz), col, mats["glass_dusty"], segments=20, cap_bottom=True, cap_top=False, subsurf_levels=1)
        make_smooth_cylinder(f"L1_JarLid_{ji}", 0.165, 0.165, 0.07, w_to_b(jx, 26.61, jz), col, mats["brass_dark"], segments=18, ink_mat=ink, outline_thickness=0.005)
        make_helix_spring(f"L1_JarSpring_{ji}", 0.095, 0.016, 0.34, 4.5, w_to_b(jx, 26.32, jz), col, smat)

    # Lampu Meja Hijau Klasik (Banker's Desk Lamp — kap hijau kaca + bohlam emas menyala!)
    make_lathe_mesh("L1_LampBase", [(0.24, 0.0), (0.21, 0.06), (0.12, 0.10), (0.05, 0.12)], w_to_b(1.72, 26.09, 1.75), col, mats["brass_gold"], segments=20, cap_bottom=True, cap_top=True, ink_mat=ink, outline_thickness=0.006)
    make_smooth_cylinder("L1_LampStem", 0.036, 0.032, 0.72, w_to_b(1.72, 26.52, 1.75), col, mats["brass_gold"], segments=14)
    make_beveled_box("L1_LampShade", (0.56, 0.36, 0.24), w_to_b(1.55, 26.86, 1.75), col, mats["glass_lamp_green"], rotation_deg=(0, -18, 0), bevel_width=0.06, ink_mat=ink, outline_thickness=0.008)
    make_smooth_sphere("L1_LampBulb", 0.10, w_to_b(1.55, 26.75, 1.75), col, mats["emissive_lamp"], subdivisions=2)

    # Jam Dinding Kayu cat terkelupas (kiri) & Rak Perkakas Warna-Warni (kanan)
    make_beveled_box("L1_WallClock", (0.28, 1.15, 1.90), w_to_b(-4.15, 28.0, 1.6), col, mats["plaster_teal"], bevel_width=0.04, ink_mat=ink, outline_thickness=0.012)
    make_smooth_cylinder("L1_WallClockDial", 0.42, 0.42, 0.08, w_to_b(-3.98, 28.35, 1.6), col, mats["clock_dial"], segments=24, rotation_deg=(0, 90, 0))
    make_beveled_box("L1_Shelf", (0.55, 4.6, 0.12), w_to_b(4.05, 27.6, 1.8), col, mats["oak_wood"], bevel_width=0.025)
    for ri, (rz, rmat) in enumerate([(0.4, mats["prop_red"]), (1.2, mats["canopy_teal"]), (2.1, mats["prop_orange"]), (3.0, mats["prop_blue"])]):
        make_beveled_box(f"L1_ToolBox_{ri}", (0.42, 0.56, 0.50), w_to_b(4.0, 27.92, rz), col, rmat, bevel_width=0.04, ink_mat=ink, outline_thickness=0.010)

    # DUA RODA GIGI KUNINGAN GANTUNG FOREGROUND ([CAM 01] Heavy 3D Parallax!)
    g_left = make_cogwheel_3d("L1_FG_Gear_L", 0.90, 0.16, 12, w_to_b(-1.08, 27.08, -1.15), col, mats["brass_dark"], rotation_deg=(0, 0, 8), ink_mat=ink, outline_thickness=0.014)
    g_right = make_cogwheel_3d("L1_FG_Gear_R", 0.90, 0.16, 12, w_to_b(1.08, 27.26, -1.15), col, mats["brass_gold"], rotation_deg=(0, 0, -8), ink_mat=ink, outline_thickness=0.014)
    make_smooth_cylinder("L1_FG_Chain_L", 0.038, 0.038, 2.8, w_to_b(-1.08, 29.2, -1.15), col, mats["iron_dark"], segments=10)
    make_smooth_cylinder("L1_FG_Chain_R", 0.038, 0.038, 2.8, w_to_b(1.08, 29.3, -1.15), col, mats["iron_dark"], segments=10)
    handles.fg_hanging_gears.extend([g_left, g_right])

    # Partikel debu emas berkilau dalam sinar Low Sun
    for di in range(14):
        dx = math.sin(di * 2.1) * 1.8
        dy_up = 26.35 + (di % 5) * 0.52
        dz_fwd = -0.6 + (di * 0.35) % 4.4
        make_smooth_sphere(f"L1_GoldDust_{di}", 0.032, w_to_b(dx, dy_up, dz_fwd), col, mats["fx_gold_dust"], subdivisions=1)


def _build_lokasi_2_pasar(mats: dict, handles: SceneHandles) -> None:
    col = get_or_create_collection("Loc2_Pasar_Rempah")
    ink = mats["ink"]

    # Bangunan pesisir bertingkat warna-warni + balkon besi tempa (3D Parallax ekstrem di [CAM 06]!)
    facades = [
        (-6.2, 20.5, 9.5, 4.2, 17.0, 6.2, mats["plaster_terracotta"]),
        (-6.4, 15.5, 16.0, 4.4, 15.0, 6.6, mats["plaster_teal"]),
        (-6.2, 12.0, 22.8, 4.2, 13.5, 6.6, mats["plaster_ochre"]),
        (6.2, 20.5, 9.5, 4.2, 17.0, 6.2, mats["plaster_ochre"]),
        (6.4, 15.5, 16.0, 4.4, 15.0, 6.6, mats["plaster_coral"]),
        (6.2, 12.0, 22.8, 4.2, 13.5, 6.6, mats["plaster_mint"]),
    ]
    for fi, (fx, fy_up, fz_fwd, fw, fh, fd, fmat) in enumerate(facades):
        make_beveled_box(f"L2_Facade_{fi}", (fw, fd, fh), w_to_b(fx, fy_up, fz_fwd), col, fmat, bevel_width=0.08, ink_mat=ink, outline_thickness=0.022)
        side_s = 1.0 if fx < 0 else -1.0
        bx = fx + side_s * (fw * 0.5 + 0.58)
        for bi, by_up in enumerate((fy_up + 4.8, fy_up + 1.2, fy_up - 2.4)):
            make_beveled_box(f"L2_Balcony_{fi}_{bi}", (1.18, fd * 0.72, 0.20), w_to_b(bx, by_up, fz_fwd), col, mats["stone_step"], bevel_width=0.04, ink_mat=ink, outline_thickness=0.015)
            make_beveled_box(f"L2_Rail_{fi}_{bi}", (0.09, fd * 0.70, 0.90), w_to_b(bx + side_s * 0.52, by_up + 0.52, fz_fwd), col, mats["iron_dark"], bevel_width=0.02)
            make_beveled_box(f"L2_FlowerBoxA_{fi}_{bi}", (0.34, 1.25, 0.28), w_to_b(bx + side_s * 0.42, by_up + 0.98, fz_fwd - 0.9), col, mats["prop_magenta"], bevel_width=0.05, ink_mat=ink, outline_thickness=0.010)
            make_beveled_box(f"L2_FlowerBoxB_{fi}_{bi}", (0.34, 1.15, 0.28), w_to_b(bx + side_s * 0.42, by_up + 0.98, fz_fwd + 1.0), col, mats["canopy_teal"], bevel_width=0.05, ink_mat=ink, outline_thickness=0.010)

    # Teras batu pasar bertingkat + tangga batu kuno + rel kayu samping ([CAM 10]!)
    make_beveled_box("L2_Terrace_Upper", (10.5, 7.0, 1.2), w_to_b(0, 13.6, 10.5), col, mats["stone_step"], bevel_width=0.05)
    make_beveled_box("L2_Terrace_Lower", (10.5, 6.2, 1.2), w_to_b(0, 11.4, 16.5), col, mats["stone_step"], bevel_width=0.05)
    for si in range(16):
        u = si / 16.0
        sy_up = 11.4 - u * 6.4
        sz_fwd = 19.6 + u * 8.0
        make_beveled_box(f"L2_Step_{si}", (8.2, 0.64, 0.72), w_to_b(0, sy_up - 0.35, sz_fwd), col, mats["stone_step"] if si % 2 == 0 else mats["cobble_wet"], bevel_width=0.04)

    # Rel kayu meluncur samping tangga ([CAM 10])
    make_beveled_box("L2_StairRail", (0.24, 10.4, 0.18), w_to_b(1.95, 8.95, 23.6), col, mats["oak_wood"], rotation_deg=(-38.5, 0, 0), bevel_width=0.04, ink_mat=ink, outline_thickness=0.012)
    for pi, (pz, py) in enumerate([(20.2, 11.2), (22.4, 9.5), (24.8, 7.6), (27.0, 5.8)]):
        make_beveled_box(f"L2_RailPost_{pi}", (0.16, 0.16, 1.15), w_to_b(1.95, py + 0.45, pz), col, mats["oak_dark"], bevel_width=0.025)

    # 5 Kanopi Tenda Kain Melengkung & Berkibar (Red Hero [CAM 07], Teal, Ochre, Plum!)
    make_draped_canopy_3d("L2_Canopy_RedHero", 3.9, 3.2, 3.2, w_to_b(0.0, 14.2, 10.8), col, mats["canopy_red"], mats["canopy_cream"], mats["oak_wood"], ink_mat=ink, rotation_deg=(0, 0, 4))
    make_draped_canopy_3d("L2_Canopy_Teal", 3.2, 2.9, 2.8, w_to_b(-2.5, 14.2, 13.8), col, mats["canopy_teal"], mats["canopy_cream"], mats["oak_wood"], ink_mat=ink, rotation_deg=(0, 0, -6))
    make_draped_canopy_3d("L2_Canopy_Ochre", 3.4, 3.1, 3.0, w_to_b(2.4, 12.0, 15.2), col, mats["canopy_ochre"], mats["canopy_cream"], mats["oak_wood"], ink_mat=ink, rotation_deg=(0, 0, 8))
    make_draped_canopy_3d("L2_Canopy_Plum", 3.3, 2.9, 2.9, w_to_b(-2.6, 12.0, 18.0), col, mats["canopy_plum"], mats["canopy_cream"], mats["oak_wood"], ink_mat=ink, rotation_deg=(0, 0, -5))
    make_draped_canopy_3d("L2_Canopy_Teal2", 3.0, 2.8, 2.6, w_to_b(2.7, 12.0, 18.6), col, mats["canopy_teal"], mats["canopy_cream"], mats["oak_wood"], ink_mat=ink, rotation_deg=(0, 0, 5))

    # 5 Karung Goni Organik Bulat Penuh Bubuk Kunyit & Cabai ([CAM 09]!)
    sacks = [
        (0.25, 12.0, 16.9, mats["turmeric_pile"], 1.05),
        (-0.58, 12.0, 17.3, mats["chili_pile"], 0.96),
        (0.98, 12.0, 17.5, mats["prop_orange"], 0.98),
        (-1.28, 12.0, 16.5, mats["turmeric_pile"], 0.94),
        (1.58, 12.0, 16.4, mats["chili_pile"], 0.96),
    ]
    for si, (sx, sy, sz, spm, ssc) in enumerate(sacks):
        make_spice_sack_3d(f"L2_SpiceSack_{si}", w_to_b(sx, sy, sz), col, mats["burlap"], spm, mats["oak_dark"], ink_mat=ink, scale=ssc)

    # Partikel 3D Awan Ledakan Bubuk Kunyit & Cabai (dianimasikan meledak di [CAM 09]!)
    for ci in range(18):
        is_chili = (ci % 5 == 0)
        puff = make_smooth_sphere(
            f"L2_TurmericPuff_{ci}", 0.52 + (ci % 3) * 0.16,
            w_to_b(0.25, 12.8, 16.9), col,
            mats["fx_chili"] if is_chili else mats["fx_turmeric"],
            subdivisions=2,
        )
        handles.turmeric_puffs.append(puff)

    # Peti buah warna-warni + jeruk menggelinding tumpah di tangga ([CAM 10]!)
    crates = [
        (-2.1, 14.2, 11.4, (0, 0, 15), mats["prop_orange"]),
        (2.1, 14.2, 11.6, (0, 0, -12), mats["prop_green"]),
        (-1.8, 12.0, 15.6, (0, 0, 22), mats["prop_red"]),
        (2.2, 10.6, 20.6, (24, 15, -18), mats["prop_orange"]),
        (-1.4, 8.8, 22.8, (30, -22, 28), mats["prop_orange"]),
    ]
    for ci, (cx, cy, cz, crot, fmat) in enumerate(crates):
        make_beveled_box(f"L2_Crate_{ci}", (0.95, 0.65, 0.44), w_to_b(cx, cy + 0.22, cz), col, mats["oak_wood"], rotation_deg=crot, bevel_width=0.03, ink_mat=ink, outline_thickness=0.010)
        for fi in range(4):
            make_smooth_sphere(f"L2_Fruit_{ci}_{fi}", 0.14, w_to_b(cx - 0.24 + fi * 0.16, cy + 0.46, cz), col, fmat, subdivisions=2, ink_mat=ink, outline_thickness=0.006)
    for oi, (ox, oy, oz) in enumerate([
        (0.8, 10.2, 21.4), (1.4, 9.6, 22.2), (0.2, 8.7, 23.4), (1.1, 8.0, 24.2),
        (-0.5, 7.2, 25.2), (0.9, 6.4, 26.2), (1.6, 5.7, 27.0), (-0.3, 5.4, 27.4),
    ]):
        make_smooth_sphere(f"L2_SpilledOrange_{oi}", 0.14, w_to_b(ox, oy, oz), col, mats["prop_orange"], subdivisions=2, ink_mat=ink, outline_thickness=0.006)


def _build_lokasi_3_gang_kafe(mats: dict) -> None:
    col = get_or_create_collection("Loc3_Gang_Kafe")
    ink = mats["ink"]

    # Jalan batu cobblestone basah memantulkan langit
    make_beveled_box("L3_Cobblestone", (7.8, 18.4, 0.50), w_to_b(0, 4.75, 36.8), col, mats["cobble_wet"], bevel_width=0.03)

    # Dinding gang sempit kiri & kanan (cahaya Low Sun memotong tajam 30% + 70% cool blue shade!)
    walls = [
        (-4.5, 10.0, 31.5, 2.0, 11.5, 7.2, mats["plaster_terracotta"]),
        (-4.5, 10.6, 39.2, 2.0, 12.6, 8.6, mats["plaster_teal"]),
        (4.5, 10.2, 31.5, 2.0, 11.8, 7.2, mats["plaster_warm"]),
        (4.5, 10.5, 39.2, 2.0, 12.4, 8.6, mats["plaster_coral"]),
    ]
    for wi, (wx, wy_up, wz_fwd, ww, wh, wd, wmat) in enumerate(walls):
        make_beveled_box(f"L3_Wall_{wi}", (ww, wd, wh), w_to_b(wx, wy_up, wz_fwd), col, wmat, bevel_width=0.06)
        side_s = 1.0 if wx < 0 else -1.0
        for swi, wy_win in enumerate((7.8, 10.8)):
            make_beveled_box(f"L3_Win_{wi}_{swi}", (0.16, 1.15, 1.50), w_to_b(wx + side_s * 1.02, wy_win, wz_fwd), col, mats["plaster_teal"], bevel_width=0.025, ink_mat=ink, outline_thickness=0.012)

    # Meja bistro besi biru langit + teko kopi tembaga + kursi ([CAM 11] kolong meja!)
    for bi, (bx, bz) in enumerate([(-1.9, 30.8), (1.95, 32.6), (-1.85, 34.8), (2.0, 37.8)]):
        make_smooth_cylinder(f"L3_TableTop_{bi}", 0.56, 0.56, 0.06, w_to_b(bx, 5.76, bz), col, mats["bistro_blue"], segments=24, ink_mat=ink, outline_thickness=0.010)
        make_smooth_cylinder(f"L3_TablePed_{bi}", 0.055, 0.045, 0.74, w_to_b(bx, 5.38, bz), col, mats["iron_dark"], segments=12)
        make_lathe_mesh(f"L3_CoffeePot_{bi}", [(0.08, 0.0), (0.11, 0.07), (0.06, 0.19), (0.08, 0.24)], w_to_b(bx + 0.12, 5.79, bz), col, mats["oren_bell_copper"], segments=18, cap_bottom=True, cap_top=True, ink_mat=ink, outline_thickness=0.005)
        make_smooth_cylinder(f"L3_ChairSeat_{bi}", 0.25, 0.25, 0.05, w_to_b(bx + 0.74, 5.44, bz), col, mats["oak_wood"], segments=18, ink_mat=ink, outline_thickness=0.008)
        make_beveled_box(f"L3_ChairBack_{bi}", (0.06, 0.44, 0.52), w_to_b(bx + 0.96, 5.72, bz), col, mats["bistro_blue"], bevel_width=0.02, ink_mat=ink, outline_thickness=0.008)

    # Pot Terakota + Bunga Bougenville Magenta (termasuk Hero Pot di samping "Oren" [CAM 12]!)
    for pi, (px, pz, psc) in enumerate([(-1.62, 36.8, 1.05), (2.65, 35.4, 1.0), (-2.65, 40.4, 1.05), (2.55, 41.2, 1.0)]):
        make_potted_bougainvillea_3d(f"L3_Bougainvillea_{pi}", w_to_b(px, 5.0, pz), col, mats["terracotta_pot"], mats["prop_green"], mats["prop_magenta"], ink_mat=ink, scale=psc)

    # Kabel jemuran di atas gang penuh baju warna primer berkibar angin (Wave modifier!)
    shirt_mats = [mats["prop_red"], mats["prop_blue"], mats["porcelain"], mats["canopy_teal"], mats["prop_magenta"], mats["prop_green"]]
    for li, (lz, ly) in enumerate([(31.2, 8.9), (34.4, 9.2), (37.6, 8.7), (40.8, 9.1)]):
        make_smooth_cylinder(f"L3_Line_{li}", 0.022, 0.022, 7.2, w_to_b(0, ly, lz), col, mats["iron_dark"], segments=8, rotation_deg=(0, 90, 0))
        for si, sx in enumerate((-2.3, -1.1, 0.1, 1.3, 2.3)):
            shirt = make_beveled_box(f"L3_Shirt_{li}_{si}", (0.68, 0.06, 0.95), w_to_b(sx, ly - 0.56, lz), col, shirt_mats[(si + li) % len(shirt_mats)], rotation_deg=(-10, (si - 2) * 3, 0), bevel_width=0.02, ink_mat=ink, outline_thickness=0.010)
            wv = shirt.modifiers.new(name="LaundryBreeze", type="WAVE")
            wv.height = 0.06
            wv.width = 1.2
            wv.speed = 0.14

    # JERUJI SELOKAN BESI BERKARAT (y_fwd = 42.5 -> lubang gelap transisi [CAM 15] Hidden Wipe!)
    make_beveled_box("L3_SewerVoid", (1.75, 1.75, 0.25), w_to_b(0, 4.86, 42.5), col, mats["black_void"], bevel_width=0.01)
    for fi, (fx, fz, fsize) in enumerate([
        (0, 41.65, (1.95, 0.18, 0.12)), (0, 43.35, (1.95, 0.18, 0.12)),
        (-0.85, 42.5, (0.18, 1.95, 0.12)), (0.85, 42.5, (0.18, 1.95, 0.12)),
    ]):
        make_beveled_box(f"L3_GrateFrame_{fi}", fsize, w_to_b(fx, 5.02, fz), col, mats["rust_grate"], bevel_width=0.02, ink_mat=ink, outline_thickness=0.008)
    for bi in range(-3, 4):
        make_beveled_box(f"L3_GrateBar_{bi}", (0.068, 1.68, 0.095), w_to_b(bi * 0.24, 5.04, 42.5), col, mats["rust_grate"], bevel_width=0.015, ink_mat=ink, outline_thickness=0.006)
    make_beveled_box("L3_EndWall", (9.5, 0.8, 11.0), w_to_b(0, 10.0, 45.6), col, mats["tower_stone"], bevel_width=0.05)


def _build_lokasi_4_gorong_gorong(mats: dict, handles: SceneHandles) -> None:
    col = get_or_create_collection("Loc4_Gorong_Gorong_Mesin")
    ink = mats["ink"]

    # Gua mesin bawah tanah raksasa
    make_beveled_box("L4_Floor", (26.0, 26.0, 1.0), w_to_b(0, -25.0, 45.5), col, mats["vault_stone"], bevel_width=0.06)
    make_beveled_box("L4_Ceiling", (26.0, 24.0, 1.0), w_to_b(0, -5.0, 45.5), col, mats["vault_stone"], bevel_width=0.06)
    make_beveled_box("L4_Wall_L", (1.2, 26.0, 21.0), w_to_b(-12.5, -15.0, 45.5), col, mats["vault_stone"], bevel_width=0.06)
    make_beveled_box("L4_Wall_R", (1.2, 26.0, 21.0), w_to_b(12.5, -15.0, 45.5), col, mats["vault_stone"], bevel_width=0.06)
    make_beveled_box("L4_Wall_Back", (26.0, 1.2, 21.0), w_to_b(0, -15.0, 58.0), col, mats["vault_stone"], bevel_width=0.06)
    make_beveled_box("L4_Wall_Front", (26.0, 1.2, 21.0), w_to_b(0, -15.0, 33.0), col, mats["vault_stone"], bevel_width=0.06)

    # Pilar batu lumut basah + pipa tembaga teroksidasi + katup merah cerah + pressure gauge!
    for px in (-8.2, 8.2):
        for pz in (38.0, 46.5, 54.0):
            make_beveled_box(f"L4_Pillar_{px:.0f}_{pz:.0f}", (1.8, 1.8, 20.0), w_to_b(px, -15.0, pz), col, mats["vault_stone"], bevel_width=0.08)
            make_beveled_box(f"L4_Moss_{px:.0f}_{pz:.0f}", (2.2, 2.2, 1.2), w_to_b(px, -23.6, pz), col, mats["moss_wet"], bevel_width=0.14)
    for py_p in (-10.5, -14.2, -20.5):
        make_smooth_cylinder(f"L4_PipeL_{py_p:.1f}", 0.55, 0.55, 22.0, w_to_b(-9.8, py_p, 45.5), col, mats["copper_ox"], segments=18, rotation_deg=(90, 0, 0), ink_mat=ink, outline_thickness=0.025)
        make_smooth_cylinder(f"L4_PipeR_{py_p:.1f}", 0.55, 0.55, 22.0, w_to_b(9.8, py_p, 45.5), col, mats["copper_ox"], segments=18, rotation_deg=(90, 0, 0), ink_mat=ink, outline_thickness=0.025)
    for vi, (vx, vy, vz) in enumerate([(-8.6, -14.2, 43.0), (8.6, -14.2, 44.5), (-4.6, -18.5, 45.2), (4.6, -18.5, 45.2)]):
        make_cogwheel_3d(f"L4_Valve_{vi}", 0.72, 0.16, 8, w_to_b(vx, vy, vz), col, mats["prop_red"], rotation_deg=(0, 0, 90 if abs(vx) > 6 else 0), ink_mat=ink, outline_thickness=0.015)

    # TUNGKU INTI MESIN KOTA BERCAHAYA + SOKET POROS UTAMA ([CAM 18] KLAK!)
    make_smooth_cylinder("L4_FurnaceBody", 3.6, 2.8, 5.2, w_to_b(0, -21.2, 49.5), col, mats["rust_grate"], segments=24, ink_mat=ink, outline_thickness=0.03)
    make_smooth_sphere("L4_FurnaceCore", 2.35, w_to_b(0, -18.2, 49.5), col, mats["emissive_furnace"], subdivisions=3)
    make_beveled_box("L4_AxleHousing", (1.35, 2.4, 1.35), w_to_b(0, -17.0, 44.6), col, mats["brass_gold"], bevel_width=0.08, ink_mat=ink, outline_thickness=0.020)
    make_smooth_cylinder("L4_AxleKeyhole", 0.44, 0.44, 0.35, w_to_b(0, -17.0, 43.3), col, mats["iron_dark"], segments=20, rotation_deg=(90, 0, 0), ink_mat=ink, outline_thickness=0.012)

    # 5 RODA GIGI RAKSASA SELEBAR RUMAH (berputar maju -> MACET -> MUNDUR di `animation_director.py`!)
    colossal_specs = [
        ("L4_GiantGear_L", (-4.2, -16.5, 45.2), 4.2, 0.72, 16, mats["steel_bright"], 1.0),
        ("L4_GiantGear_R", (4.4, -15.8, 45.5), 4.4, 0.76, 16, mats["brass_dark"], -0.95),
        ("L4_GiantGear_Top", (0.0, -11.2, 48.2), 5.6, 0.85, 20, mats["copper_ox"], 0.75),
        ("L4_GiantGear_LowL", (-6.5, -20.5, 42.0), 3.1, 0.55, 14, mats["brass_gold"], -1.25),
        ("L4_GiantGear_LowR", (6.2, -20.8, 41.8), 3.2, 0.55, 14, mats["steel_bright"], 1.20),
    ]
    for gname, gpos, gr, gt_th, gteeth, gmat, gmul in colossal_specs:
        g_obj = make_cogwheel_3d(gname, gr, gt_th, gteeth, w_to_b(*gpos), col, gmat, ink_mat=ink, outline_thickness=0.032)
        handles.underground_gears.append((g_obj, gmul))

    # Cerobong ventilasi vertikal raksasa menuju peron stasiun ([CAM 19] Reverse Spiral Ascent!)
    make_smooth_cylinder("L4_ChimneyShaft", 4.4, 4.4, 26.0, w_to_b(0, -3.5, 62.0), col, mats["iron_dark"], segments=24, cap_ends=False)
    for ry in range(-16, 10, 3):
        make_cogwheel_3d(f"L4_ChimneyRing_{ry}", 4.6, 0.6, 10, w_to_b(0, float(ry), 62.0), col, mats["copper_ox"], rotation_deg=(90, 0, ry * 12), hollow_ratio=0.72, spokes=0)

    # Uap Zamrud 3D & 12 Percikan Berlian Biru-Zamrud ([CAM 18] KLAK!)
    for ei in range(12):
        ep = make_smooth_sphere(f"L4_EmeraldSteam_{ei}", 1.15, w_to_b(math.sin(ei * 1.7) * 3.0, -20.0 + ei * 1.2, 44.5), col, mats["fx_emerald_steam"], subdivisions=2)
        handles.emerald_puffs.append(ep)
    for si in range(12):
        # Bentuk berlian runcing 3D berkilau (bukan garis kotak!)
        sp = make_smooth_sphere(f"L4_KlakSpark_{si}", 0.14, w_to_b(0, -17.0, 42.98), col, mats["emissive_spark_cyan"], scale=(0.35, 0.35, 1.85), subdivisions=1)
        handles.klak_sparks.append(sp)


def _build_lokasi_5_stasiun_trem(mats: dict, handles: SceneHandles) -> None:
    col = get_or_create_collection("Loc5_Stasiun_Trem")
    ink = mats["ink"]

    # Dek peron kayu layang kiri & kanan + track bed + rel baja kembar
    make_beveled_box("L5_Platform_L", (5.2, 56.0, 0.55), w_to_b(-4.4, 9.75, 85.0), col, mats["oak_wood"], bevel_width=0.05)
    make_beveled_box("L5_Platform_R", (5.2, 56.0, 0.55), w_to_b(4.4, 9.75, 85.0), col, mats["oak_wood"], bevel_width=0.05)
    make_beveled_box("L5_TrackBed", (3.8, 56.0, 0.65), w_to_b(0, 9.25, 85.0), col, mats["cobble_wet"], bevel_width=0.04)
    make_beveled_box("L5_Rail_L", (0.14, 56.0, 0.16), w_to_b(-0.92, 9.65, 85.0), col, mats["steel_bright"], bevel_width=0.02)
    make_beveled_box("L5_Rail_R", (0.14, 56.0, 0.16), w_to_b(0.92, 9.65, 85.0), col, mats["steel_bright"], bevel_width=0.02)
    for tz in range(60, 112, 2):
        make_beveled_box(f"L5_Tie_{tz}", (2.5, 0.28, 0.10), w_to_b(0, 9.58, float(tz)), col, mats["oak_dark"], bevel_width=0.015)

    # Kisi ventilasi lantai peron tempat keluar [CAM 20]
    make_beveled_box("L5_VentExit", (2.2, 2.2, 0.12), w_to_b(0, 9.68, 62.0), col, mats["iron_dark"], bevel_width=0.02)

    # Pilar besi cor foreground kiri & kanan ([CAM 21] Parallax Wall!) + kanopi stasiun
    for pz in range(64, 110, 6):
        for px in (-2.55, 2.55):
            make_smooth_cylinder(f"L5_Pillar_{px:.1f}_{pz}", 0.20, 0.16, 5.4, w_to_b(px, 12.6, float(pz)), col, mats["iron_dark"], segments=16, ink_mat=ink, outline_thickness=0.016)
            make_beveled_box(f"L5_PillarCap_{px:.1f}_{pz}", (0.65, 0.65, 0.35), w_to_b(px, 15.25, float(pz)), col, mats["brass_gold"], bevel_width=0.04)
        make_beveled_box(f"L5_Roof_L_{pz}", (4.4, 6.2, 0.22), w_to_b(-4.4, 15.35, float(pz)), col, mats["copper_ox"], rotation_deg=(0, 8, 0), bevel_width=0.04)
        make_beveled_box(f"L5_Roof_R_{pz}", (4.4, 6.2, 0.22), w_to_b(4.4, 15.35, float(pz)), col, mats["copper_ox"], rotation_deg=(0, -8, 0), bevel_width=0.04)

    # Loket tiket warna mint & ochre + papan jadwal split-flap mekanik + bangku + koper + balon!
    make_beveled_box("L5_TicketBooth", (2.6, 4.4, 3.5), w_to_b(-5.2, 11.75, 74.0), col, mats["plaster_mint"], bevel_width=0.08, ink_mat=ink, outline_thickness=0.02)
    make_beveled_box("L5_TicketRoof", (3.0, 4.9, 0.45), w_to_b(-5.2, 13.7, 74.0), col, mats["plaster_ochre"], bevel_width=0.06, ink_mat=ink, outline_thickness=0.02)
    make_beveled_box("L5_SplitFlap", (0.32, 3.8, 1.85), w_to_b(-3.5, 13.6, 82.0), col, mats["iron_dark"], bevel_width=0.04, ink_mat=ink, outline_thickness=0.015)

    suit_mats = [mats["prop_red"], mats["canopy_teal"], mats["bima_leather"], mats["prop_blue"]]
    for bi, bz in enumerate((69.0, 79.0, 89.0, 99.0)):
        make_beveled_box(f"L5_Bench_{bi}", (0.75, 2.4, 0.14), w_to_b(4.1, 10.45, bz), col, mats["oak_wood"], bevel_width=0.03)
        make_beveled_box(f"L5_SuitcaseL_{bi}", (0.45, 0.95, 0.72), w_to_b(-3.2, 10.45, bz + 1.4), col, suit_mats[bi % 4], rotation_deg=(0, 0, 18 * bi), bevel_width=0.05, ink_mat=ink, outline_thickness=0.012)
        make_beveled_box(f"L5_SuitcaseR_{bi}", (0.40, 0.82, 0.60), w_to_b(3.2, 10.38, bz - 1.5), col, suit_mats[(bi + 2) % 4], rotation_deg=(0, 0, -14), bevel_width=0.05, ink_mat=ink, outline_thickness=0.012)

    for bi, (bx, by, bz, bmat) in enumerate([
        (-3.6, 13.2, 71.0, mats["prop_red"]),
        (3.4, 13.8, 77.5, mats["prop_blue"]),
        (-3.2, 12.8, 86.5, mats["canopy_teal"]),
        (3.6, 14.2, 95.0, mats["prop_magenta"]),
    ]):
        make_smooth_sphere(f"L5_Balloon_{bi}", 0.42, w_to_b(bx, by, bz), col, bmat, scale=(0.9, 0.9, 1.18), subdivisions=3, ink_mat=ink, outline_thickness=0.012)
        make_smooth_cylinder(f"L5_BalloonStr_{bi}", 0.014, 0.014, 1.2, w_to_b(bx, by - 0.95, bz + 0.28), col, mats["porcelain"], segments=6, rotation_deg=(-22, 0, 0))

    # TREM MERAH VINTAGE MELUNCUR MUNDUR!
    handles.tram_root = make_vintage_tram_3d("L5_Vintage_Tram", w_to_b(0.0, 9.65, 96.0), col, mats)

    # 6 Burung Camar Stasiun (terbang mundur di [CAM 21]-[CAM 24]!)
    for gi in range(6):
        root_g, wl, wr = make_seagull_3d(f"L5_Seagull_{gi}", w_to_b(-4.5 + (gi % 3) * 4.5, 15.0 + (gi // 3) * 2.2, 96.0 - gi * 3.5), col, mats, scale=1.15)
        handles.station_seagulls.append((root_g, wl, wr, gi))


def _build_lokasi_6_menara_jam(mats: dict, handles: SceneHandles) -> None:
    col = get_or_create_collection("Loc6_Menara_Jam_Dermaga")
    ink = mats["ink"]

    # Menara Jam Raksasa + atap menara tembaga teroksidasi + lonceng perunggu Lathe!
    make_beveled_box("L6_TowerBody", (14.5, 8.8, 29.0), w_to_b(0, 14.0, 122.5), col, mats["tower_stone"], bevel_width=0.18, ink_mat=ink, outline_thickness=0.04)
    make_smooth_cylinder("L6_TowerSteeple", 7.8, 1.0, 6.4, w_to_b(0, 31.6, 122.5), col, mats["copper_ox"], segments=8, ink_mat=ink, outline_thickness=0.04)
    make_lathe_mesh(
        "L6_BronzeBell",
        [(1.70, 0.0), (1.35, 0.45), (1.05, 1.45), (0.85, 2.15), (0.35, 2.35)],
        w_to_b(0, 26.5, 118.5), col, mats["oren_bell_copper"], segments=24, cap_bottom=False, cap_top=True,
        subsurf_levels=1, ink_mat=ink, outline_thickness=0.025,
    )

    # WAJAH JAM RAKSASA (berpusat di x=0, y_up=19.5, z_fwd=118.0!)
    make_cogwheel_3d("L6_ClockBezel", 6.8, 0.95, 24, w_to_b(0, 19.5, 118.0), col, mats["brass_dark"], hollow_ratio=0.78, spokes=0, ink_mat=ink, outline_thickness=0.035)
    make_smooth_cylinder("L6_ClockDial", 5.65, 5.65, 0.25, w_to_b(0, 19.5, 118.15), col, mats["clock_dial"], segments=48, rotation_deg=(90, 0, 0))
    for hi in range(12):
        ang = math.radians(hi * 30.0)
        rx = math.sin(ang) * 4.55
        ry_up = 19.5 + math.cos(ang) * 4.55
        is_card = (hi % 3 == 0)
        make_beveled_box(
            f"L6_Numeral_{hi}",
            (0.32 if is_card else 0.18, 0.24, 1.08 if is_card else 0.72),
            w_to_b(rx, ry_up, 117.82), col, mats["brass_gold"],
            rotation_deg=(0, hi * 30.0, 0), bevel_width=0.03, ink_mat=ink, outline_thickness=0.015,
        )

    # Lubang kunci pusat jam ([CAM 25]) + Balkon pijak sempit tempat Bima mendarat ([CAM 25]-[CAM 27])
    make_smooth_cylinder("L6_CenterHub", 0.72, 0.56, 0.55, w_to_b(0, 19.5, 117.58), col, mats["brass_gold"], segments=24, rotation_deg=(90, 0, 0), ink_mat=ink, outline_thickness=0.018)
    make_smooth_cylinder("L6_CenterKeyhole", 0.24, 0.24, 0.12, w_to_b(0, 19.5, 117.28), col, mats["iron_dark"], segments=16, rotation_deg=(90, 0, 0))
    make_beveled_box("L6_Balcony", (6.5, 2.2, 0.45), w_to_b(0, 15.2, 116.8), col, mats["oak_wood"], bevel_width=0.05, ink_mat=ink, outline_thickness=0.018)

    # JARUM JAM BESI TEMPA RAKSASA (pivot tepat di pusat (0, 117.6, 19.5)!)
    min_piv = bpy.data.objects.new("L6_MinuteHand_Pivot", None)
    min_piv.location = Vector(w_to_b(0.0, 19.5, 117.60))
    link_object(min_piv, col)
    m_blade = make_beveled_box("L6_MinuteHand_Mesh", (0.28, 0.16, 4.5), (0, 0, 2.1), col, mats["iron_dark"], bevel_width=0.03, ink_mat=ink, outline_thickness=0.018)
    m_blade.parent = min_piv
    handles.clock_minute_hand = min_piv

    hr_piv = bpy.data.objects.new("L6_HourHand_Pivot", None)
    hr_piv.location = Vector(w_to_b(0.0, 19.5, 117.42))
    link_object(hr_piv, col)
    h_blade = make_beveled_box("L6_HourHand_Mesh", (0.38, 0.16, 3.1), (0, 0, 1.4), col, mats["iron_dark"], bevel_width=0.035, ink_mat=ink, outline_thickness=0.018)
    h_blade.parent = hr_piv
    handles.clock_hour_hand = hr_piv

    # DUA RODA GIGI GELAP SEAMLESS LOOP di bawah balkon menara ([CAM 28] -> [CAM 01]!)
    lg_l = make_cogwheel_3d("L6_LoopGear_L", 1.05, 0.18, 12, w_to_b(-1.15, 13.0, 117.0), col, mats["brass_dark"], rotation_deg=(0, 0, 8), ink_mat=ink, outline_thickness=0.018)
    lg_r = make_cogwheel_3d("L6_LoopGear_R", 1.05, 0.18, 12, w_to_b(1.15, 13.2, 117.0), col, mats["brass_gold"], rotation_deg=(0, 0, -8), ink_mat=ink, outline_thickness=0.018)
    handles.loop_gears.extend([lg_l, lg_r])

    # Kilau perak tajam di sebelah Kunci Perak ([CAM 27] twist!)
    handles.silver_sparkle = make_smooth_sphere("L6_SilverSparkle", 0.08, w_to_b(-0.44, 16.22, 115.40), col, mats["emissive_spark_silver"], scale=(0.3, 0.3, 1.8), subdivisions=1)

    # LAUT, DERMAGA KAYU, RUMAH PELABUHAN WARNA-WARNI & MERCUSUAR MINI BELANG MERAH-PUTIH!
    make_beveled_box("L6_SeaPlane", (180.0, 180.0, 0.4), w_to_b(0, 0.0, 115.0), col, mats["water_sea"], bevel_width=0.0)
    make_beveled_box("L6_Pier_L", (14.0, 26.0, 2.2), w_to_b(-18.0, 1.5, 112.0), col, mats["oak_wood"], bevel_width=0.08)
    make_beveled_box("L6_Pier_R", (14.0, 26.0, 2.2), w_to_b(18.0, 1.5, 112.0), col, mats["oak_wood"], bevel_width=0.08)
    harbor_houses = [
        (-16.0, 4.8, 106.0, mats["plaster_coral"]), (-20.0, 5.2, 112.0, mats["plaster_teal"]), (-15.5, 4.4, 118.0, mats["plaster_ochre"]),
        (16.0, 4.6, 105.0, mats["plaster_mint"]), (19.5, 5.5, 113.0, mats["plaster_terracotta"]), (15.5, 4.8, 120.0, mats["plaster_teal"]),
    ]
    for hi, (hx, hy, hz, hmat) in enumerate(harbor_houses):
        make_beveled_box(f"L6_House_{hi}", (4.6, 5.2, 5.2), w_to_b(hx, hy, hz), col, hmat, bevel_width=0.10, ink_mat=ink, outline_thickness=0.03)
        make_beveled_box(f"L6_Roof_{hi}", (5.0, 5.6, 1.0), w_to_b(hx, hy + 3.0, hz), col, mats["tram_crimson"], bevel_width=0.08)

    # Mercusuar mini belang merah-putih di ujung dermaga kanan!
    lhx, lhz = 22.0, 96.0
    for li in range(5):
        make_smooth_cylinder(f"L6_Lighthouse_{li}", 1.62 - li * 0.14, 1.48 - li * 0.14, 2.2, w_to_b(lhx, 2.5 + li * 2.2, lhz), col, mats["tram_crimson"] if li % 2 == 0 else mats["porcelain"], segments=22, ink_mat=ink, outline_thickness=0.025)
    make_smooth_cylinder("L6_LighthouseLamp", 0.85, 0.85, 1.5, w_to_b(lhx, 13.6, lhz), col, mats["emissive_lighthouse"], segments=20)
    make_smooth_cylinder("L6_LighthouseDome", 1.15, 0.08, 1.3, w_to_b(lhx, 14.9, lhz), col, mats["tram_crimson"], segments=20)

    # 12 Burung Camar Pelabuhan (membeku di udara -> terbang bebas di Twilight [CAM 26]!)
    for gi in range(12):
        root_g, wl, wr = make_seagull_3d(f"L6_HarborSeagull_{gi}", w_to_b(0, 19.0, 111.0), col, mats, scale=1.30)
        handles.harbor_seagulls.append((root_g, wl, wr, gi))

    # PIRINGAN MATAHARI CRIMSON RAKSASA di cakrawala belakang lompatan Bima ([CAM 24]!)
    handles.crimson_sun_orb = make_smooth_sphere(
        "L6_Crimson_Sun_Orb", 14.0, w_to_b(-34.0, 32.0, 195.0), col, mats["emissive_sun_crimson"], subdivisions=3
    )


def build_all_6_locations(mats: dict) -> SceneHandles:
    """Bangun seluruh 6 lokasi 3D terpadu dan kembalikan handles seluruh elemen dinamis."""
    handles = SceneHandles()
    _build_lokasi_1_bengkel(mats, handles)
    _build_lokasi_2_pasar(mats, handles)
    _build_lokasi_3_gang_kafe(mats)
    _build_lokasi_4_gorong_gorong(mats, handles)
    _build_lokasi_5_stasiun_trem(mats, handles)
    _build_lokasi_6_menara_jam(mats, handles)
    return handles
