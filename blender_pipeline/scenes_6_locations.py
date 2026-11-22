"""
Pembangun 6 Lokasi 3D Terpadu Berbasis Referensi Nyata + Model 3D CC0 Asli dari Poly Haven:
  - Lokasi 1 (Bengkel Jam Loteng): Referensi bengkel horologis Swiss + Poly Haven wall_clock, mantel_clock,
    alarm_clock, metal_toolbox, desk_lamp, + meja kerja bertopi pengaman sekrup & cangkir porselen!
  - Lokasi 2 (Pasar Rempah): Referensi rumah teras Mediterania (Positano / Cinque Terre) beratap genteng
    terakota (coppi), jendela persiane, balkon besi tempa + Poly Haven wooden_crate_01, wooden_barrels_01, ceramic_pot!
  - Lokasi 3 (Gang Kafe): Referensi gang Alfama Lisbon + Tanaman Bougainvillea BOTANIS nyata (batang berkayu,
    daun ovate, triad bract magenta) + Poly Haven potted_plant_01/02, coffee_table_round_01, wooden_chair_01, street_lamp_01!
  - Lokasi 4 (Gorong-Gorong Mesin): Referensi ruang mesin uap Victoria dengan kubah lengkung batu (barrel vault),
    pipa tembaga berflensa, katup merah, tungku bercahaya, & 5 roda gigi raksasa!
  - Lokasi 5 (Stasiun Trem): Referensi Lisbon Tram 28 'Remodelado' (atap clerestory, jendela transom, bangku kayu,
    pantograf + kabel listrik catenary 600V) + lampu jalan besi tempa Eropa!
  - Lokasi 6 (Menara Jam Utama & Pelabuhan): Referensi Venice Torre dell'Orologio (gerbang lengkung, pilaster,
    balkon balustrade batu klasik, wajah jam lapis-lazuli & emas, paviliun lonceng berkubah tembaga) + Mercusuar Eropa!
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import List, Tuple

import bpy  # type: ignore
from mathutils import Vector  # type: ignore

from .assets_loader import place_polyhaven_model
from .config import w_to_b
from .mesh_utils import (
    get_or_create_collection,
    link_object,
    make_beveled_box,
    make_coastal_hills_backdrop_3d,
    make_coastal_lighthouse_3d,
    make_cogwheel_3d,
    make_draped_canopy_3d,
    make_helix_spring,
    make_lathe_mesh,
    make_mediterranean_building_3d,
    make_potted_bougainvillea_3d,
    make_seagull_3d,
    make_smooth_cylinder,
    make_smooth_sphere,
    make_spice_sack_3d,
    make_sunlight_beam_3d,
    make_teacup_and_saucer_3d,
    make_venetian_clock_tower_3d,
    make_vintage_tram_3d,
)


@dataclass
class SceneHandles:
    """Referensi seluruh objek 3D dinamis & properti reaktif yang dianimasikan di `animation_director.py`."""

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
    # Properti interaktif yang bereaksi fisik saat tersentuh kunci/karakter!
    hero_teacup: "bpy.types.Object | None" = None
    hero_red_canopy: "bpy.types.Object | None" = None
    hero_turmeric_sack: "bpy.types.Object | None" = None
    crimson_beams: List["bpy.types.Object"] = field(default_factory=list)
    twilight_beams: List["bpy.types.Object"] = field(default_factory=list)


def _build_lokasi_1_bengkel(mats: dict, handles: SceneHandles) -> None:
    col = get_or_create_collection("Loc1_Bengkel_Loteng")
    ink = mats["ink"]

    # Lantai papan oak, kuda-kuda atap kayu miring (truss), & dinding plaster hangat bengkel horologis Swiss
    make_beveled_box("L1_Floor", (9.0, 9.2, 0.35), w_to_b(0, 24.8, 0.0), col, mats["oak_dark"], bevel_width=0.04)
    make_beveled_box("L1_Ceiling", (9.5, 9.6, 0.40), w_to_b(0, 30.8, 0.0), col, mats["oak_dark"], bevel_width=0.04)
    make_beveled_box("L1_Wall_L", (0.35, 9.2, 6.2), w_to_b(-4.4, 27.8, 0.0), col, mats["plaster_warm"], bevel_width=0.04)
    make_beveled_box("L1_Wall_R", (0.35, 9.2, 6.2), w_to_b(4.4, 27.8, 0.0), col, mats["plaster_warm"], bevel_width=0.04)
    make_beveled_box("L1_Wall_Back", (9.0, 0.35, 6.2), w_to_b(0, 27.8, -4.5), col, mats["tower_stone"], bevel_width=0.04)
    for bi, bz in enumerate((-3.2, -1.0, 1.4, 3.6)):
        make_beveled_box(f"L1_Beam_{bi}", (8.8, 0.34, 0.38), w_to_b(0, 30.35, bz), col, mats["oak_dark"], bevel_width=0.03, ink_mat=ink, outline_thickness=0.012)
        for sgn in (-1.0, 1.0):
            make_beveled_box(f"L1_Brace_{bi}_{sgn:.0f}", (1.35, 0.22, 0.22), w_to_b(sgn * 3.7, 29.7, bz), col, mats["oak_dark"], rotation_deg=(0, sgn * 42, 0), bevel_width=0.025)

    # Dinding jendela loteng + ambang kayu tua + daun jendela berpanel terbuka ke kota pesisir
    make_beveled_box("L1_WinWall_L", (2.9, 0.38, 6.2), w_to_b(-3.0, 27.8, 4.2), col, mats["plaster_warm"], bevel_width=0.03)
    make_beveled_box("L1_WinWall_R", (2.9, 0.38, 6.2), w_to_b(3.0, 27.8, 4.2), col, mats["plaster_warm"], bevel_width=0.03)
    make_beveled_box("L1_WinWall_Bot", (3.4, 0.38, 1.5), w_to_b(0, 25.55, 4.2), col, mats["plaster_warm"], bevel_width=0.03)
    make_beveled_box("L1_WinWall_Top", (3.4, 0.38, 1.8), w_to_b(0, 29.85, 4.2), col, mats["plaster_warm"], bevel_width=0.03)
    make_beveled_box("L1_WinSill", (3.55, 0.68, 0.20), w_to_b(0, 26.32, 4.25), col, mats["shutter_blue"], bevel_width=0.03, ink_mat=ink, outline_thickness=0.012)
    make_beveled_box("L1_WinHeader", (3.55, 0.52, 0.20), w_to_b(0, 28.95, 4.25), col, mats["shutter_blue"], bevel_width=0.03, ink_mat=ink, outline_thickness=0.012)
    make_beveled_box("L1_WinJamb_L", (0.18, 0.52, 2.75), w_to_b(-1.62, 27.65, 4.25), col, mats["shutter_blue"], bevel_width=0.03, ink_mat=ink, outline_thickness=0.012)
    make_beveled_box("L1_WinJamb_R", (0.18, 0.52, 2.75), w_to_b(1.62, 27.65, 4.25), col, mats["shutter_blue"], bevel_width=0.03, ink_mat=ink, outline_thickness=0.012)
    make_beveled_box("L1_Shutter_L", (0.10, 1.15, 2.55), w_to_b(-2.15, 27.65, 4.82), col, mats["shutter_blue"], rotation_deg=(0, 0, 34), bevel_width=0.02, ink_mat=ink, outline_thickness=0.012)
    make_beveled_box("L1_Shutter_R", (0.10, 1.15, 2.55), w_to_b(2.15, 27.65, 4.82), col, mats["shutter_blue"], rotation_deg=(0, 0, -34), bevel_width=0.02, ink_mat=ink, outline_thickness=0.012)

    # Meja kerja tukang jam asli (kedalaman 1.70m: z_fwd=0.70..2.40 -> ruang berdiri Bima di belakang z=2.68 100% BEBAS TEMBUS!)
    make_beveled_box("L1_Workbench", (4.6, 1.70, 0.18), w_to_b(0, 26.0, 1.55), col, mats["oak_wood"], bevel_width=0.035, ink_mat=ink, outline_thickness=0.010)
    make_beveled_box("L1_BenchRail_L", (0.08, 1.70, 0.08), w_to_b(-2.26, 26.13, 1.55), col, mats["oak_dark"], bevel_width=0.015)
    make_beveled_box("L1_BenchRail_R", (0.08, 1.70, 0.08), w_to_b(2.26, 26.13, 1.55), col, mats["oak_dark"], bevel_width=0.015)
    for di, dx in enumerate((-1.2, 0.0, 1.2)):
        make_beveled_box(f"L1_Drawer_{di}", (1.05, 0.12, 0.34), w_to_b(dx, 25.72, 0.72), col, mats["oak_dark"], bevel_width=0.02)
        make_smooth_sphere(f"L1_DrawerPull_{di}", 0.038, w_to_b(dx, 25.72, 0.64), col, mats["brass_gold"], subdivisions=2)
    for lx in (-2.05, 2.05):
        for lz in (0.85, 2.25):
            make_beveled_box(f"L1_Leg_{lx:.1f}_{lz:.1f}", (0.18, 0.18, 1.15), w_to_b(lx, 25.4, lz), col, mats["oak_dark"], bevel_width=0.025)
    # Pijakan papan oak tukang jam di belakang meja (top y=25.32) agar dada, syal & tangan Bima tampil gagah di atas meja!
    make_beveled_box("L1_WatchmakerStep", (1.40, 0.62, 0.34), w_to_b(-0.10, 25.15, 2.72), col, mats["oak_dark"], bevel_width=0.03, ink_mat=ink, outline_thickness=0.010)

    # Hero Prop Cangkir Teh Porselen + Tatakan (reaktif bergetar saat kunci memantul di [CAM 03]!)
    handles.hero_teacup = make_teacup_and_saucer_3d("L1_Hero_Teacup", w_to_b(0.55, 26.09, 1.55), col, mats["porcelain"], mats["tea_liquid"], mats["prop_red"], ink_mat=ink)

    # Roda gigi kuningan berserakan di meja + obeng + kaca pembesar (semua rapi di atas z_fwd=0.95..2.28!)
    desk_gears = [
        (-1.25, 26.12, 1.05, 0.24, 10, mats["brass_gold"]),
        (-0.82, 26.12, 1.55, 0.17, 8, mats["brass_dark"]),
        (-1.45, 26.12, 2.05, 0.28, 12, mats["brass_gold"]),
        (1.15, 26.12, 1.90, 0.26, 12, mats["brass_gold"]),
        (0.92, 26.12, 2.20, 0.19, 10, mats["oren_bell_copper"]),
        (-0.35, 26.12, 2.18, 0.22, 10, mats["brass_gold"]),
        (1.55, 26.12, 1.12, 0.28, 12, mats["brass_dark"]),
    ]
    for gi, (gx, gy, gz, gr, gt, gm) in enumerate(desk_gears):
        make_cogwheel_3d(f"L1_DeskGear_{gi}", gr, 0.055, gt, w_to_b(gx, gy, gz), col, gm, rotation_deg=(90, 0, gx * 40), ink_mat=ink, outline_thickness=0.005)

    for oi, (ox, oz, omat, oang) in enumerate([
        (-0.65, 1.88, mats["prop_blue"], 28),
        (-0.18, 2.12, mats["prop_red"], -18),
        (0.75, 2.15, mats["prop_green"], 42),
    ]):
        make_smooth_cylinder(f"L1_ScrewHandle_{oi}", 0.042, 0.046, 0.24, w_to_b(ox, 26.14, oz), col, omat, segments=14, rotation_deg=(90, 0, oang), ink_mat=ink, outline_thickness=0.004)
        make_smooth_cylinder(f"L1_ScrewShaft_{oi}", 0.012, 0.012, 0.28, w_to_b(ox + 0.16, 26.14, oz + 0.08), col, mats["steel_bright"], segments=10, rotation_deg=(90, 0, oang))
    make_smooth_cylinder("L1_MagRim", 0.18, 0.18, 0.04, w_to_b(-0.85, 26.14, 2.18), col, mats["brass_gold"], segments=24, ink_mat=ink, outline_thickness=0.005)
    make_smooth_cylinder("L1_MagGlass", 0.148, 0.148, 0.025, w_to_b(-0.85, 26.145, 2.18), col, mats["glass_dusty"], segments=22)
    make_smooth_cylinder("L1_MagHandle", 0.030, 0.038, 0.34, w_to_b(-1.14, 26.14, 2.28), col, mats["oak_dark"], segments=12, rotation_deg=(90, 0, 60), ink_mat=ink, outline_thickness=0.005)

    # 4 Toples kaca + pegas spiral 3D warna-warni (rapi di sisi kiri & kanan meja!)
    jar_prof = [(0.17, 0.0), (0.19, 0.05), (0.19, 0.38), (0.15, 0.45), (0.15, 0.50)]
    for ji, (jx, jz, smat) in enumerate([
        (-1.82, 1.05, mats["prop_red"]),
        (-1.72, 1.62, mats["canopy_teal"]),
        (-1.86, 2.15, mats["prop_orange"]),
        (1.88, 2.12, mats["prop_magenta"]),
    ]):
        make_lathe_mesh(f"L1_JarGlass_{ji}", jar_prof, w_to_b(jx, 26.09, jz), col, mats["glass_dusty"], segments=20, cap_bottom=True, cap_top=False, subsurf_levels=1)
        make_smooth_cylinder(f"L1_JarLid_{ji}", 0.165, 0.165, 0.07, w_to_b(jx, 26.61, jz), col, mats["brass_dark"], segments=18, ink_mat=ink, outline_thickness=0.005)
        make_helix_spring(f"L1_JarSpring_{ji}", 0.095, 0.016, 0.34, 4.5, w_to_b(jx, 26.32, jz), col, smat)

    # ASET 3D NYATA CC0 POLY HAVEN di Lokasi 1 (otomatis terpasang jika tersedia, fallback mulus!)
    if not place_polyhaven_model("desk_lamp", "L1_PH_DeskLamp", w_to_b(1.72, 26.09, 1.55), col, target_height=0.82, rotation_deg=(0, 0, -145)):
        make_lathe_mesh("L1_LampBase", [(0.24, 0.0), (0.21, 0.06), (0.12, 0.10), (0.05, 0.12)], w_to_b(1.72, 26.09, 1.55), col, mats["brass_gold"], segments=20, cap_bottom=True, cap_top=True, ink_mat=ink, outline_thickness=0.006)
        make_smooth_cylinder("L1_LampStem", 0.036, 0.032, 0.72, w_to_b(1.72, 26.52, 1.55), col, mats["brass_gold"], segments=14)
        make_beveled_box("L1_LampShade", (0.56, 0.36, 0.24), w_to_b(1.55, 26.86, 1.55), col, mats["glass_lamp_green"], rotation_deg=(0, -18, 0), bevel_width=0.06, ink_mat=ink, outline_thickness=0.008)
        make_smooth_sphere("L1_LampBulb", 0.10, w_to_b(1.55, 26.75, 1.55), col, mats["emissive_lamp"], subdivisions=2)

    place_polyhaven_model("mantel_clock", "L1_PH_MantelClock", w_to_b(-1.35, 26.09, 2.22), col, target_height=0.44, rotation_deg=(0, 0, 165))
    place_polyhaven_model("alarm_clock", "L1_PH_AlarmClock", w_to_b(1.22, 26.09, 2.18), col, target_height=0.28, rotation_deg=(0, 0, -155))
    place_polyhaven_model("toolbox", "L1_PH_Toolbox", w_to_b(2.0, 24.98, 2.6), col, target_height=0.45, rotation_deg=(0, 0, 28))
    if not place_polyhaven_model("wall_clock", "L1_PH_WallClock", w_to_b(-4.12, 27.6, 1.6), col, target_height=1.05, rotation_deg=(0, 0, 90)):
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

    for di in range(14):
        make_smooth_sphere(f"L1_GoldDust_{di}", 0.032, w_to_b(math.sin(di * 2.1) * 1.8, 26.35 + (di % 5) * 0.52, -0.6 + (di * 0.35) % 4.4), col, mats["fx_gold_dust"], subdivisions=1)


def _build_lokasi_2_pasar(mats: dict, handles: SceneHandles) -> None:
    col = get_or_create_collection("Loc2_Pasar_Rempah")
    ink = mats["ink"]

    # 6 BANGUNAN PESISIR MEDITERANIA NYATA (Positano / Cinque Terre: genteng terakota coppi, jendela persiane, balkon besi tempa!)
    facades = [
        (-6.2, 20.5, 9.5, 4.2, 6.2, 16.5, 1.0, mats["plaster_terracotta"], mats["shutter_green"]),
        (-6.4, 15.5, 16.0, 4.4, 6.6, 14.5, 1.0, mats["plaster_teal"], mats["shutter_blue"]),
        (-6.2, 12.0, 22.8, 4.2, 6.6, 13.0, 1.0, mats["plaster_ochre"], mats["shutter_green"]),
        (6.2, 20.5, 9.5, 4.2, 6.2, 16.5, -1.0, mats["plaster_ochre"], mats["shutter_blue"]),
        (6.4, 15.5, 16.0, 4.4, 6.6, 14.5, -1.0, mats["plaster_coral"], mats["shutter_green"]),
        (6.2, 12.0, 22.8, 4.2, 6.6, 13.0, -1.0, mats["plaster_mint"], mats["shutter_blue"]),
    ]
    for fi, (fx, fy_up, fz_fwd, fw, fd, fh, fside, fmat, shmat) in enumerate(facades):
        make_mediterranean_building_3d(
            f"L2_MedHouse_{fi}", w_to_b(fx, fy_up, fz_fwd), (fw, fd, fh),
            fside, col, fmat, mats, shutter_mat=shmat, floors=3, with_balconies=True,
        )

    # Teras batu pasar bertingkat + tangga batu kuno + rel kayu samping ([CAM 10]!)
    make_beveled_box("L2_Terrace_Upper", (10.5, 7.0, 1.2), w_to_b(0, 13.6, 10.5), col, mats["stone_step"], bevel_width=0.05)
    make_beveled_box("L2_Terrace_Lower", (10.5, 6.2, 1.2), w_to_b(0, 11.4, 16.5), col, mats["stone_step"], bevel_width=0.05)
    for si in range(16):
        u = si / 16.0
        make_beveled_box(f"L2_Step_{si}", (8.2, 0.64, 0.72), w_to_b(0, 11.4 - u * 6.4 - 0.35, 19.6 + u * 8.0), col, mats["stone_step"] if si % 2 == 0 else mats["cobble_wet"], bevel_width=0.04)

    make_beveled_box("L2_StairRail", (0.24, 10.4, 0.18), w_to_b(1.95, 8.95, 23.6), col, mats["oak_wood"], rotation_deg=(-38.5, 0, 0), bevel_width=0.04, ink_mat=ink, outline_thickness=0.012)
    for pi, (pz, py) in enumerate([(20.2, 11.2), (22.4, 9.5), (24.8, 7.6), (27.0, 5.8)]):
        make_beveled_box(f"L2_RailPost_{pi}", (0.16, 0.16, 1.15), w_to_b(1.95, py + 0.45, pz), col, mats["oak_dark"], bevel_width=0.025)

    # 5 Kanopi tenda kain pasar melengkung & berkibar (Hero Red Canopy reaktif memantul di [CAM 07]!)
    handles.hero_red_canopy = make_draped_canopy_3d("L2_Canopy_RedHero", 3.9, 3.2, 3.2, w_to_b(0.0, 14.2, 10.8), col, mats["canopy_red"], mats["canopy_cream"], mats["oak_wood"], ink_mat=ink, rotation_deg=(0, 0, 4))
    make_draped_canopy_3d("L2_Canopy_Teal", 3.2, 2.9, 2.8, w_to_b(-2.5, 14.2, 13.8), col, mats["canopy_teal"], mats["canopy_cream"], mats["oak_wood"], ink_mat=ink, rotation_deg=(0, 0, -6))
    make_draped_canopy_3d("L2_Canopy_Ochre", 3.4, 3.1, 3.0, w_to_b(2.4, 12.0, 15.2), col, mats["canopy_ochre"], mats["canopy_cream"], mats["oak_wood"], ink_mat=ink, rotation_deg=(0, 0, 8))
    make_draped_canopy_3d("L2_Canopy_Plum", 3.3, 2.9, 2.9, w_to_b(-2.6, 12.0, 18.0), col, mats["canopy_plum"], mats["canopy_cream"], mats["oak_wood"], ink_mat=ink, rotation_deg=(0, 0, -5))
    make_draped_canopy_3d("L2_Canopy_Teal2", 3.0, 2.8, 2.6, w_to_b(2.7, 12.0, 18.6), col, mats["canopy_teal"], mats["canopy_cream"], mats["oak_wood"], ink_mat=ink, rotation_deg=(0, 0, 5))

    # 5 Karung goni bulat terikat tali + bubuk kunyit & cabai (karung tengah reaktif penyok saat dihantam kunci [CAM 09]!)
    sacks = [
        (0.25, 12.0, 16.9, mats["turmeric_pile"], 1.05),
        (-0.58, 12.0, 17.3, mats["chili_pile"], 0.96),
        (0.98, 12.0, 17.5, mats["prop_orange"], 0.98),
        (-1.28, 12.0, 16.5, mats["turmeric_pile"], 0.94),
        (1.58, 12.0, 16.4, mats["chili_pile"], 0.96),
    ]
    for si, (sx, sy, sz, spm, ssc) in enumerate(sacks):
        sack_obj = make_spice_sack_3d(f"L2_SpiceSack_{si}", w_to_b(sx, sy, sz), col, mats["burlap"], spm, mats["oak_dark"], ink_mat=ink, scale=ssc)
        if si == 0:
            handles.hero_turmeric_sack = sack_obj

    # ASET 3D NYATA CC0 POLY HAVEN di Pasar (tong kayu, peti kayu asli, pot keramik!)
    place_polyhaven_model("wood_barrel", "L2_PH_Barrel_L", w_to_b(-2.4, 12.0, 15.0), col, target_height=0.95, rotation_deg=(0, 0, 20))
    place_polyhaven_model("wood_barrel", "L2_PH_Barrel_R", w_to_b(2.45, 12.0, 16.2), col, target_height=0.92, rotation_deg=(0, 0, -35))
    place_polyhaven_model("ceramic_pot", "L2_PH_Pot_1", w_to_b(-1.95, 14.2, 10.6), col, target_height=0.62)
    place_polyhaven_model("ceramic_pot", "L2_PH_Pot_2", w_to_b(2.15, 14.2, 12.5), col, target_height=0.58)

    for ci in range(18):
        puff = make_smooth_sphere(f"L2_TurmericPuff_{ci}", 0.52 + (ci % 3) * 0.16, w_to_b(0.25, 12.8, 16.9), col, mats["fx_chili"] if (ci % 5 == 0) else mats["fx_turmeric"], subdivisions=2)
        handles.turmeric_puffs.append(puff)

    crates = [
        (-2.1, 14.2, 11.4, (0, 0, 15), mats["prop_orange"]),
        (2.1, 14.2, 11.6, (0, 0, -12), mats["prop_green"]),
        (-1.8, 12.0, 15.6, (0, 0, 22), mats["prop_red"]),
        (2.2, 10.6, 20.6, (24, 15, -18), mats["prop_orange"]),
        (-1.4, 8.8, 22.8, (30, -22, 28), mats["prop_orange"]),
    ]
    for ci, (cx, cy, cz, crot, fmat) in enumerate(crates):
        if not place_polyhaven_model("wood_crate", f"L2_PH_Crate_{ci}", w_to_b(cx, cy, cz), col, target_height=0.52, rotation_deg=crot):
            make_beveled_box(f"L2_Crate_{ci}", (0.95, 0.65, 0.44), w_to_b(cx, cy + 0.22, cz), col, mats["oak_wood"], rotation_deg=crot, bevel_width=0.03, ink_mat=ink, outline_thickness=0.010)
        for fi in range(4):
            make_smooth_sphere(f"L2_Fruit_{ci}_{fi}", 0.14, w_to_b(cx - 0.24 + fi * 0.16, cy + 0.48, cz), col, fmat, subdivisions=2, ink_mat=ink, outline_thickness=0.006)
    for oi, (ox, oy, oz) in enumerate([
        (0.8, 10.2, 21.4), (1.4, 9.6, 22.2), (0.2, 8.7, 23.4), (1.1, 8.0, 24.2),
        (-0.5, 7.2, 25.2), (0.9, 6.4, 26.2), (1.6, 5.7, 27.0), (-0.3, 5.4, 27.4),
    ]):
        make_smooth_sphere(f"L2_SpilledOrange_{oi}", 0.14, w_to_b(ox, oy, oz), col, mats["prop_orange"], subdivisions=2, ink_mat=ink, outline_thickness=0.006)


def _build_lokasi_3_gang_kafe(mats: dict) -> None:
    col = get_or_create_collection("Loc3_Gang_Kafe")
    ink = mats["ink"]

    make_beveled_box("L3_Cobblestone", (7.8, 18.4, 0.50), w_to_b(0, 4.75, 36.8), col, mats["cobble_wet"], bevel_width=0.03)

    # 4 Bangunan Gang Kafe Mediterania nyata (jendela persiane, cornice batu, atap genteng!)
    alley_buildings = [
        (-4.8, 10.2, 31.5, 2.4, 7.2, 11.2, 1.0, mats["plaster_terracotta"], mats["shutter_green"]),
        (-4.8, 10.6, 39.2, 2.4, 8.6, 12.0, 1.0, mats["plaster_teal"], mats["shutter_blue"]),
        (4.8, 10.2, 31.5, 2.4, 7.2, 11.4, -1.0, mats["plaster_warm"], mats["shutter_blue"]),
        (4.8, 10.5, 39.2, 2.4, 8.6, 12.0, -1.0, mats["plaster_coral"], mats["shutter_green"]),
    ]
    for wi, (wx, wy_up, wz_fwd, ww, wd, wh, wside, wmat, shmat) in enumerate(alley_buildings):
        make_mediterranean_building_3d(
            f"L3_AlleyHouse_{wi}", w_to_b(wx, wy_up, wz_fwd), (ww, wd, wh),
            wside, col, wmat, mats, shutter_mat=shmat, floors=2, with_balconies=False,
        )

    # Meja & Kursi Kafe + Lampu Jalan Besi Tempa Eropa (Poly Haven CC0 3D models dengan fallback mulus!)
    for bi, (bx, bz) in enumerate([(-1.9, 30.8), (1.95, 32.6), (-1.85, 34.8), (2.0, 37.8)]):
        if not place_polyhaven_model("bistro_table", f"L3_PH_Table_{bi}", w_to_b(bx, 5.0, bz), col, target_height=0.78):
            make_smooth_cylinder(f"L3_TableTop_{bi}", 0.56, 0.56, 0.06, w_to_b(bx, 5.76, bz), col, mats["bistro_blue"], segments=24, ink_mat=ink, outline_thickness=0.010)
            make_smooth_cylinder(f"L3_TablePed_{bi}", 0.055, 0.045, 0.74, w_to_b(bx, 5.38, bz), col, mats["iron_dark"], segments=12)
        if not place_polyhaven_model("wood_chair", f"L3_PH_Chair_{bi}", w_to_b(bx + (0.82 if bx < 0 else -0.82), 5.0, bz), col, target_height=0.88, rotation_deg=(0, 0, -90 if bx < 0 else 90)):
            make_smooth_cylinder(f"L3_ChairSeat_{bi}", 0.25, 0.25, 0.05, w_to_b(bx + 0.74, 5.44, bz), col, mats["oak_wood"], segments=18, ink_mat=ink, outline_thickness=0.008)
        make_lathe_mesh(f"L3_CoffeePot_{bi}", [(0.08, 0.0), (0.11, 0.07), (0.06, 0.19), (0.08, 0.24)], w_to_b(bx + 0.12, 5.79, bz), col, mats["oren_bell_copper"], segments=18, cap_bottom=True, cap_top=True, ink_mat=ink, outline_thickness=0.005)

    # TANAMAN BOUGAINVILLEA BOTANIS NYATA (batang berkayu + daun ovate + triad bract magenta!) + Tanaman Pot Poly Haven CC0!
    for pi, (px, pz, psc) in enumerate([(-1.62, 36.8, 1.08), (2.65, 35.4, 1.02), (-2.65, 40.4, 1.08), (2.55, 41.2, 1.02)]):
        make_potted_bougainvillea_3d(
            f"L3_BotanicalBougainvillea_{pi}", w_to_b(px, 5.0, pz), col,
            mats["terracotta_pot"], mats["boug_leaf"], mats["boug_bract"],
            ink_mat=ink, scale=psc, mat_bark=mats["boug_bark"],
            mat_soil=mats["soil_dark"], mat_cream=mats["boug_flower_cream"],
        )
    place_polyhaven_model("potted_plant_1", "L3_PH_Plant_A", w_to_b(-2.7, 5.0, 32.8), col, target_height=0.95)
    place_polyhaven_model("potted_plant_2", "L3_PH_Plant_B", w_to_b(2.75, 5.0, 39.2), col, target_height=0.90)
    place_polyhaven_model("street_lamp", "L3_PH_StreetLamp", w_to_b(3.1, 5.0, 34.0), col, target_height=3.6, rotation_deg=(0, 0, -90))

    # Kabel jemuran warna primer berkibar angin
    shirt_mats = [mats["prop_red"], mats["prop_blue"], mats["porcelain"], mats["canopy_teal"], mats["prop_magenta"], mats["prop_green"]]
    for li, (lz, ly) in enumerate([(31.2, 8.9), (34.4, 9.2), (37.6, 8.7), (40.8, 9.1)]):
        make_smooth_cylinder(f"L3_Line_{li}", 0.022, 0.022, 7.2, w_to_b(0, ly, lz), col, mats["iron_dark"], segments=8, rotation_deg=(0, 90, 0))
        for si, sx in enumerate((-2.3, -1.1, 0.1, 1.3, 2.3)):
            shirt = make_beveled_box(f"L3_Shirt_{li}_{si}", (0.68, 0.06, 0.95), w_to_b(sx, ly - 0.56, lz), col, shirt_mats[(si + li) % len(shirt_mats)], rotation_deg=(-10, (si - 2) * 3, 0), bevel_width=0.02, ink_mat=ink, outline_thickness=0.010)
            wv = shirt.modifiers.new(name="LaundryBreeze", type="WAVE")
            wv.height = 0.06
            wv.width = 1.2
            wv.speed = 0.14

    # Jeruji selokan besi berkarat (lubang transisi [CAM 15] Hidden Wipe!)
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

    # Ruang mesin bawah tanah Victoria berkubah batu rusuk (barrel vault ribs!)
    make_beveled_box("L4_Floor", (26.0, 26.0, 1.0), w_to_b(0, -25.0, 45.5), col, mats["vault_stone"], bevel_width=0.06)
    make_beveled_box("L4_Ceiling", (26.0, 24.0, 1.0), w_to_b(0, -5.0, 45.5), col, mats["vault_stone"], bevel_width=0.06)
    make_beveled_box("L4_Wall_L", (1.2, 26.0, 21.0), w_to_b(-12.5, -15.0, 45.5), col, mats["vault_stone"], bevel_width=0.06)
    make_beveled_box("L4_Wall_R", (1.2, 26.0, 21.0), w_to_b(12.5, -15.0, 45.5), col, mats["vault_stone"], bevel_width=0.06)
    # Dinding belakang berlorong terbuka (portal z=58 -> cerobong z=62) agar Bima & kunci TIDAK menembus tembok di [CAM 19]!
    make_beveled_box("L4_Wall_Back_L", (8.8, 1.2, 21.0), w_to_b(-8.6, -15.0, 58.0), col, mats["vault_stone"], bevel_width=0.06)
    make_beveled_box("L4_Wall_Back_R", (8.8, 1.2, 21.0), w_to_b(8.6, -15.0, 58.0), col, mats["vault_stone"], bevel_width=0.06)
    make_beveled_box("L4_Wall_Back_Top", (8.6, 1.2, 6.2), w_to_b(0.0, -7.8, 58.0), col, mats["vault_stone"], bevel_width=0.06)
    make_beveled_box("L4_ChimneyDuctFloor", (8.2, 6.0, 0.8), w_to_b(0.0, -19.8, 59.5), col, mats["iron_dark"], bevel_width=0.06)
    make_beveled_box("L4_Wall_Front", (26.0, 1.2, 21.0), w_to_b(0, -15.0, 33.0), col, mats["vault_stone"], bevel_width=0.06)

    for pz in (38.0, 46.5, 54.0):
        # Rusuk lengkung atap kubah Victoria
        make_cogwheel_3d(f"L4_VaultRib_{pz:.0f}", 11.8, 1.1, 16, w_to_b(0, -14.0, pz), col, mats["iron_dark"], hollow_ratio=0.86, spokes=0)
        for px in (-8.2, 8.2):
            make_beveled_box(f"L4_Pillar_{px:.0f}_{pz:.0f}", (1.8, 1.8, 20.0), w_to_b(px, -15.0, pz), col, mats["vault_stone"], bevel_width=0.08)
            make_beveled_box(f"L4_Moss_{px:.0f}_{pz:.0f}", (2.2, 2.2, 1.2), w_to_b(px, -23.6, pz), col, mats["moss_wet"], bevel_width=0.14)

    for py_p in (-10.5, -14.2, -20.5):
        make_smooth_cylinder(f"L4_PipeL_{py_p:.1f}", 0.55, 0.55, 22.0, w_to_b(-9.8, py_p, 45.5), col, mats["copper_ox"], segments=18, rotation_deg=(90, 0, 0), ink_mat=ink, outline_thickness=0.025)
        make_smooth_cylinder(f"L4_PipeR_{py_p:.1f}", 0.55, 0.55, 22.0, w_to_b(9.8, py_p, 45.5), col, mats["copper_ox"], segments=18, rotation_deg=(90, 0, 0), ink_mat=ink, outline_thickness=0.025)
        # Flensa sambungan pipa baut-tembaga
        for fz in (38.0, 45.5, 53.0):
            make_smooth_cylinder(f"L4_FlangeL_{py_p:.0f}_{fz:.0f}", 0.72, 0.72, 0.22, w_to_b(-9.8, py_p, fz), col, mats["brass_dark"], segments=16, rotation_deg=(90, 0, 0))
            make_smooth_cylinder(f"L4_FlangeR_{py_p:.0f}_{fz:.0f}", 0.72, 0.72, 0.22, w_to_b(9.8, py_p, fz), col, mats["brass_dark"], segments=16, rotation_deg=(90, 0, 0))
    for vi, (vx, vy, vz) in enumerate([(-8.6, -14.2, 43.0), (8.6, -14.2, 44.5), (-4.6, -18.5, 45.2), (4.6, -18.5, 45.2)]):
        make_cogwheel_3d(f"L4_Valve_{vi}", 0.72, 0.16, 8, w_to_b(vx, vy, vz), col, mats["prop_red"], rotation_deg=(0, 0, 90 if abs(vx) > 6 else 0), ink_mat=ink, outline_thickness=0.015)

    # TUNGKU INTI MESIN + SOKET POROS UTAMA ([CAM 18] KLAK!)
    make_smooth_cylinder("L4_FurnaceBody", 3.6, 2.8, 5.2, w_to_b(0, -21.2, 49.5), col, mats["rust_grate"], segments=24, ink_mat=ink, outline_thickness=0.03)
    make_smooth_sphere("L4_FurnaceCore", 2.35, w_to_b(0, -18.2, 49.5), col, mats["emissive_furnace"], subdivisions=3)
    make_beveled_box("L4_AxleHousing", (1.42, 2.4, 1.42), w_to_b(0, -17.0, 44.6), col, mats["brass_gold"], bevel_width=0.09, ink_mat=ink, outline_thickness=0.020)
    make_smooth_cylinder("L4_AxleKeyhole", 0.46, 0.46, 0.35, w_to_b(0, -17.0, 43.3), col, mats["iron_dark"], segments=22, rotation_deg=(90, 0, 0), ink_mat=ink, outline_thickness=0.012)

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

    make_smooth_cylinder("L4_ChimneyShaft", 4.4, 4.4, 26.0, w_to_b(0, -3.5, 62.0), col, mats["iron_dark"], segments=24, cap_ends=False)
    for ry in range(-16, 10, 3):
        make_cogwheel_3d(f"L4_ChimneyRing_{ry}", 4.6, 0.6, 10, w_to_b(0, float(ry), 62.0), col, mats["copper_ox"], rotation_deg=(90, 0, ry * 12), hollow_ratio=0.72, spokes=0)

    for ei in range(12):
        ep = make_smooth_sphere(f"L4_EmeraldSteam_{ei}", 1.15, w_to_b(math.sin(ei * 1.7) * 3.0, -20.0 + ei * 1.2, 44.5), col, mats["fx_emerald_steam"], subdivisions=2)
        handles.emerald_puffs.append(ep)
    for si in range(12):
        sp = make_smooth_sphere(f"L4_KlakSpark_{si}", 0.14, w_to_b(0, -17.0, 42.98), col, mats["emissive_spark_cyan"], scale=(0.35, 0.35, 1.85), subdivisions=1)
        handles.klak_sparks.append(sp)


def _build_lokasi_5_stasiun_trem(mats: dict, handles: SceneHandles) -> None:
    col = get_or_create_collection("Loc5_Stasiun_Trem")
    ink = mats["ink"]

    # Dek peron kayu layang + rel baja sempit 900mm (Lisbon Tram 28!) + kabel catenary 600V di atas!
    make_beveled_box("L5_Platform_L", (5.2, 56.0, 0.55), w_to_b(-4.4, 9.75, 85.0), col, mats["oak_wood"], bevel_width=0.05)
    make_beveled_box("L5_Platform_R", (5.2, 56.0, 0.55), w_to_b(4.4, 9.75, 85.0), col, mats["oak_wood"], bevel_width=0.05)
    make_beveled_box("L5_TrackBed", (3.8, 56.0, 0.65), w_to_b(0, 9.25, 85.0), col, mats["cobble_wet"], bevel_width=0.04)
    make_beveled_box("L5_Rail_L", (0.14, 56.0, 0.16), w_to_b(-0.92, 9.65, 85.0), col, mats["steel_bright"], bevel_width=0.02)
    make_beveled_box("L5_Rail_R", (0.14, 56.0, 0.16), w_to_b(0.92, 9.65, 85.0), col, mats["steel_bright"], bevel_width=0.02)
    # Kabel listrik overhead catenary 600V tepat di atas pantograf trem!
    make_smooth_cylinder("L5_CatenaryWire", 0.028, 0.028, 56.0, w_to_b(0.0, 14.42, 85.0), col, mats["iron_dark"], segments=8, rotation_deg=(90, 0, 0))
    for tz in range(60, 112, 2):
        make_beveled_box(f"L5_Tie_{tz}", (2.5, 0.28, 0.10), w_to_b(0, 9.58, float(tz)), col, mats["oak_dark"], bevel_width=0.015)

    make_beveled_box("L5_VentExit", (2.2, 2.2, 0.12), w_to_b(0, 9.68, 62.0), col, mats["iron_dark"], bevel_width=0.02)

    # Pilar besi cor ber-flensa & kanopi stasiun Eropa + palang gantung kabel catenary!
    for pz in range(64, 110, 6):
        for px in (-2.55, 2.55):
            make_smooth_cylinder(f"L5_Pillar_{px:.1f}_{pz}", 0.20, 0.15, 5.4, w_to_b(px, 12.6, float(pz)), col, mats["iron_dark"], segments=16, ink_mat=ink, outline_thickness=0.015)
            make_smooth_cylinder(f"L5_PillarBase_{px:.1f}_{pz}", 0.34, 0.22, 0.45, w_to_b(px, 10.15, float(pz)), col, mats["iron_dark"], segments=14)
            make_beveled_box(f"L5_PillarCap_{px:.1f}_{pz}", (0.65, 0.65, 0.35), w_to_b(px, 15.25, float(pz)), col, mats["brass_gold"], bevel_width=0.04)
        make_smooth_cylinder(f"L5_CrossWire_{pz}", 0.02, 0.02, 5.2, w_to_b(0.0, 14.50, float(pz)), col, mats["iron_dark"], segments=6, rotation_deg=(0, 90, 0))
        make_beveled_box(f"L5_Roof_L_{pz}", (4.4, 6.2, 0.22), w_to_b(-4.4, 15.35, float(pz)), col, mats["copper_ox"], rotation_deg=(0, 8, 0), bevel_width=0.04)
        make_beveled_box(f"L5_Roof_R_{pz}", (4.4, 6.2, 0.22), w_to_b(4.4, 15.35, float(pz)), col, mats["copper_ox"], rotation_deg=(0, -8, 0), bevel_width=0.04)

    # Lampu jalan besi tempa Eropa (Poly Haven CC0) sepanjang peron stasiun!
    for lz in (72.0, 88.0, 104.0):
        place_polyhaven_model("street_lamp", f"L5_PH_LampL_{lz:.0f}", w_to_b(-5.2, 10.02, lz), col, target_height=4.0, rotation_deg=(0, 0, 90))
        place_polyhaven_model("street_lamp", f"L5_PH_LampR_{lz:.0f}", w_to_b(5.2, 10.02, lz), col, target_height=4.0, rotation_deg=(0, 0, -90))

    make_beveled_box("L5_TicketBooth", (2.6, 4.4, 3.5), w_to_b(-5.2, 11.75, 74.0), col, mats["plaster_mint"], bevel_width=0.08, ink_mat=ink, outline_thickness=0.02)
    make_beveled_box("L5_TicketRoof", (3.0, 4.9, 0.45), w_to_b(-5.2, 13.7, 74.0), col, mats["terracotta_roof"], bevel_width=0.06, ink_mat=ink, outline_thickness=0.02)
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

    # TREM LISBON 28 'REMODELADO' NYATA MELUNCUR MUNDUR!
    handles.tram_root = make_vintage_tram_3d("L5_Lisbon_Tram28", w_to_b(0.0, 9.65, 96.0), col, mats)

    for gi in range(6):
        root_g, wl, wr = make_seagull_3d(f"L5_Seagull_{gi}", w_to_b(-4.5 + (gi % 3) * 4.5, 15.0 + (gi // 3) * 2.2, 96.0 - gi * 3.5), col, mats, scale=1.15)
        handles.station_seagulls.append((root_g, wl, wr, gi))


def _build_lokasi_6_menara_jam(mats: dict, handles: SceneHandles) -> None:
    col = get_or_create_collection("Loc6_Menara_Jam_Dermaga")
    ink = mats["ink"]

    # MENARA JAM UTAMA VENESIA NYATA (Torre dell'Orologio: gerbang lengkung, pilaster, balkon batu balustrade,
    # wajah jam lapis-lazuli & krem emas, paviliun lonceng berkubah tembaga verdigris!)
    min_piv, hr_piv = make_venetian_clock_tower_3d(w_to_b(0.0, 0.0, 122.5), col, mats)
    handles.clock_minute_hand = min_piv
    handles.clock_hour_hand = hr_piv

    # DUA RODA GIGI SEAMLESS LOOP di bawah balkon batu menara ([CAM 28] -> [CAM 01]!)
    lg_l = make_cogwheel_3d("L6_LoopGear_L", 1.05, 0.18, 12, w_to_b(-1.15, 13.0, 117.0), col, mats["brass_dark"], rotation_deg=(0, 0, 8), ink_mat=ink, outline_thickness=0.018)
    lg_r = make_cogwheel_3d("L6_LoopGear_R", 1.05, 0.18, 12, w_to_b(1.15, 13.2, 117.0), col, mats["brass_gold"], rotation_deg=(0, 0, -8), ink_mat=ink, outline_thickness=0.018)
    handles.loop_gears.extend([lg_l, lg_r])

    handles.silver_sparkle = make_smooth_sphere("L6_SilverSparkle", 0.08, w_to_b(-0.44, 16.22, 115.40), col, mats["emissive_spark_silver"], scale=(0.3, 0.3, 1.8), subdivisions=1)

    # LAUT, DERMAGA BATU & KAYU, RUMAH PELABUHAN MEDITERANIA & MERCUSUAR BATU EROPA!
    make_beveled_box("L6_SeaPlane", (220.0, 220.0, 0.4), w_to_b(0, 0.0, 115.0), col, mats["water_sea"], bevel_width=0.0)
    make_beveled_box("L6_Pier_L", (14.0, 26.0, 2.2), w_to_b(-18.0, 1.5, 112.0), col, mats["stone_step"], bevel_width=0.08)
    make_beveled_box("L6_Pier_R", (14.0, 26.0, 2.2), w_to_b(18.0, 1.5, 112.0), col, mats["stone_step"], bevel_width=0.08)

    harbor_houses = [
        (-16.0, 5.2, 106.0, 1.0, mats["plaster_coral"], mats["shutter_green"]),
        (-20.0, 5.6, 112.0, 1.0, mats["plaster_teal"], mats["shutter_blue"]),
        (-15.5, 4.9, 118.0, 1.0, mats["plaster_ochre"], mats["shutter_green"]),
        (16.0, 5.0, 105.0, -1.0, mats["plaster_mint"], mats["shutter_blue"]),
        (19.5, 5.8, 113.0, -1.0, mats["plaster_terracotta"], mats["shutter_green"]),
        (15.5, 5.2, 120.0, -1.0, mats["plaster_teal"], mats["shutter_blue"]),
    ]
    for hi, (hx, hy_up, hz_fwd, hside, hmat, shmat) in enumerate(harbor_houses):
        make_mediterranean_building_3d(
            f"L6_HarborHouse_{hi}", w_to_b(hx, hy_up, hz_fwd), (4.6, 5.2, 5.4),
            hside, col, hmat, mats, shutter_mat=shmat, floors=2, with_balconies=False,
        )

    # Tong & Peti Kargo Pelabuhan CC0 Poly Haven + Mercusuar Batu Eropa Nyata!
    place_polyhaven_model("wood_barrel", "L6_PH_HarborBarrel", w_to_b(-12.2, 2.6, 104.0), col, target_height=1.1)
    place_polyhaven_model("wood_crate", "L6_PH_HarborCrate", w_to_b(12.2, 2.6, 104.0), col, target_height=0.95)
    make_coastal_lighthouse_3d(w_to_b(22.0, 1.0, 96.0), col, mats)

    for gi in range(12):
        root_g, wl, wr = make_seagull_3d(f"L6_HarborSeagull_{gi}", w_to_b(0, 19.0, 111.0), col, mats, scale=1.30)
        handles.harbor_seagulls.append((root_g, wl, wr, gi))

    # PIRINGAN MATAHARI CRIMSON RAKSASA di langit belakang lompatan Bima ([CAM 24]!)
    handles.crimson_sun_orb = make_smooth_sphere(
        "L6_Crimson_Sun_Orb", 16.5, w_to_b(-30.0, 29.0, 192.0), col, mats["emissive_sun_crimson"], subdivisions=3
    )


def _build_cinematic_sunbeams(mats: dict, handles: SceneHandles) -> None:
    """
    Bangun Cinematic Volumetric Sunlight Beams (God Rays lembut seperti semula) yang:
      1. 100% SEARAH dengan vektor Matahari tiap fase (`Sun_Main_Low` & `L6_Crimson_Sun_Orb`!)
      2. 100% BEBAS TEMBUS DINDING / ATAP / MEJA / TREM / MENARA JAM (mulai tepat di bukaan jendela,
         tepi langit terbuka di atas atap bangunan, atau langsung dari piringan Matahari Crimson!)
    """
    col = get_or_create_collection("Atmosphere_Sunbeams_Hills")

    # 1. Lokasi 1 — Masuk TEPAT dari bukaan jendela loteng (x=-1.53..+1.53, y=26.42..28.85, z=4.10)
    #    mengikuti vektor Matahari Fase 1A (-0.442, -0.452, -0.774), berhenti bersih di atas meja kerja (y>=26.20)!
    make_sunlight_beam_3d("Beam_L1_WinA", w_to_b(0.85, 28.15, 4.10), w_to_b(-0.48, 26.79, 1.78), 0.44, 0.64, col, mats["beam_low_sun"])
    make_sunlight_beam_3d("Beam_L1_WinB", w_to_b(-0.20, 28.15, 4.10), w_to_b(-1.53, 26.79, 1.78), 0.34, 0.52, col, mats["beam_low_sun"])

    # 2. Lokasi 2 — Turun dari langit terbuka di atas atap kanan pasar, mengikuti vektor Matahari Fase 1A
    #    di tengah ngarai jalan (x in [-4.1, +4.1]), 100% bebas tembus fasad bangunan & kanopi!
    make_sunlight_beam_3d("Beam_L2_MarketA", w_to_b(3.60, 25.20, 16.50), w_to_b(-1.48, 20.00, 7.60), 0.95, 1.65, col, mats["beam_low_sun"])
    make_sunlight_beam_3d("Beam_L2_MarketB", w_to_b(3.40, 21.80, 22.50), w_to_b(-1.46, 16.83, 13.99), 0.90, 1.55, col, mats["beam_low_sun"])

    # 3. Lokasi 3 — Turun menukik tepat di celah langit terbuka gang kafe (x in [-3.25, +3.25], tembok di ±3.6!)
    #    mengikuti vektor Matahari Fase 1B (-0.360, -0.739, -0.569), berhenti bersih di atas cobblestone!
    make_sunlight_beam_3d("Beam_L3_AlleyA", w_to_b(2.60, 17.50, 41.20), w_to_b(-2.08, 7.89, 33.80), 0.65, 1.15, col, mats["beam_low_sun"])
    make_sunlight_beam_3d("Beam_L3_AlleyB", w_to_b(2.60, 17.60, 44.40), w_to_b(-1.79, 8.58, 37.46), 0.60, 1.05, col, mats["beam_low_sun"])

    # 4. Lokasi 4 — Sorotan cahaya hangat naik langsung dari inti tungku (0, -18.0, 49.0) di dalam ruang kubah!
    make_sunlight_beam_3d("Beam_L4_FurnaceA", w_to_b(0.0, -18.0, 49.0), w_to_b(-3.8, -10.5, 42.5), 1.10, 2.40, col, mats["beam_furnace"])
    make_sunlight_beam_3d("Beam_L4_FurnaceB", w_to_b(0.0, -18.0, 49.0), w_to_b(3.8, -10.5, 42.5), 1.10, 2.40, col, mats["beam_furnace"])

    # 5. Lokasi 5 — Memancar LANGSUNG dari piringan Matahari Crimson (-30, 29, 192) sepanjang vektor (+0.332, -0.155, -0.930)
    #    hanya di ruang langit terbuka kiri/belakang Menara Jam & di atas atap stasiun (NOL tembus menara/trem/atap!)
    for ci, (orig, tgt, r0, r1) in enumerate([
        (w_to_b(-27.0, 28.2, 184.0), w_to_b(-10.4, 20.5, 137.5), 2.6, 4.6),
        (w_to_b(-39.0, 32.5, 186.0), w_to_b(-13.8, 20.7, 115.3), 2.5, 4.2),
        (w_to_b(-28.0, 28.5, 140.0), w_to_b(-13.4, 21.7, 99.1), 2.0, 3.6),
    ]):
        cb = make_sunlight_beam_3d(f"Beam_L5_Crimson_{ci}", orig, tgt, r0, r1, col, mats["beam_crimson"])
        handles.crimson_beams.append(cb)

    # 6. Lokasi 6 — Sinar Frozen Twilight lembut dari cakrawala matahari barat (+0.356, -0.201, -0.913)
    #    hanya di ruang langit terbuka kiri & atas Menara Jam (100% bebas tembus Menara Jam & balkon Bima [CAM 27]!)
    for ti, (orig, tgt, r0, r1) in enumerate([
        (w_to_b(-38.5, 32.0, 185.0), w_to_b(-14.3, 18.3, 122.9), 2.6, 4.8),
        (w_to_b(-28.0, 46.5, 182.0), w_to_b(-9.5, 36.0, 134.5), 2.6, 4.6),
    ]):
        tb = make_sunlight_beam_3d(f"Beam_L6_Twilight_{ti}", orig, tgt, r0, r1, col, mats["beam_twilight"])
        handles.twilight_beams.append(tb)

    # Lanskap Perbukitan Pesisir Berlapis + Kabut Lembah mengisi seluruh latar horizon!
    make_coastal_hills_backdrop_3d(col, mats)


def build_all_6_locations(mats: dict) -> SceneHandles:
    """Bangun seluruh 6 lokasi 3D terpadu berbasis referensi nyata + Poly Haven CC0 + Perbukitan + Sunbeams."""
    handles = SceneHandles()
    _build_lokasi_1_bengkel(mats, handles)
    _build_lokasi_2_pasar(mats, handles)
    _build_lokasi_3_gang_kafe(mats)
    _build_lokasi_4_gorong_gorong(mats, handles)
    _build_lokasi_5_stasiun_trem(mats, handles)
    _build_lokasi_6_menara_jam(mats, handles)
    _build_cinematic_sunbeams(mats, handles)
    return handles
