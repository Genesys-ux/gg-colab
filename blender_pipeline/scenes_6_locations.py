"""
Pembangun 6 Lokasi Shoot 3D + Hero Props + Rich Set Dressing untuk "DETIK KE-75":
  1. Lokasi 1: Gerbong Kereta Maglev Bawah Tanah ("Express 09" Cabin)
  2. Lokasi 2: Sambungan Gerbong & Pintu Darurat Merah (Non-Euclidean Portal Vestibule)
  3. Lokasi 3: Menara Air Baja Berkarat Seberang (Kira Sniper Perch)
  4. Lokasi 4: Atap Gedung Pencakar Langit Brutalist ("Apex Tower Helipad Rooftop")
  5. Lokasi 5: Ruang Perawatan Intensif ("ICU Kamar 404")
  6. Lokasi 6: Koridor Cahaya Keemasan ("Golden Afterlife Corridor" di balik kaca ICU)
"""
from __future__ import annotations

import math
import random
from typing import Any, Dict, List

import bpy  # type: ignore

from .config import (
    CAKE_POS_W,
    ICU_BED_POS_W,
    ICU_GLASS_X,
    ICU_MATTRESS_Y,
    LOC1_FLOOR_Y,
    LOC3_ORIGIN,
    LOC4_FLOOR_Y,
    LOC5_FLOOR_Y,
    LOC6_FLOOR_Y,
    PORTAL_DOOR_Z,
    ROOFTOP_DOOR_Z,
    w_to_b,
)
from .mesh_utils import (
    get_or_create_collection,
    make_box,
    make_curve_cable,
    make_cyl,
    make_sphere,
    make_torus_ring,
)


def build_all_6_locations(mats: Dict[str, Any]) -> Dict[str, Any]:
    """Bangun seluruh 6 lokasi & kembalikan referensi objek dinamis untuk dianimasikan."""
    ink = mats["ink"]
    dyn: Dict[str, Any] = {
        "straps": [],
        "tunnel_streaks": [],
        "rain_drops": [],
        "shatter_shards": [],
        "ac_fans": [],
        "icu_bed_parts": [],
    }
    rng = random.Random(752026)

    # =========================================================================
    # LOKASI 1 & 2: GERBONG MAGLEV "EXPRESS 09" & VESTIBULE PINTU MERAH (Z=-4..31, Y=0)
    # =========================================================================
    col_mag = get_or_create_collection("Loc1_2_Maglev_Express09")

    # Lantai karet basah reflektif & atap melengkung aerodinamis
    make_box("Maglev_Floor", (3.8, 36.0, 0.14), w_to_b(0.0, -0.05, 13.5), col_mag, mats["maglev_floor"], bevel_width=0.02)
    make_box("Maglev_Ceiling", (3.7, 36.0, 0.18), w_to_b(0.0, 2.72, 13.5), col_mag, mats["maglev_wall"], bevel_width=0.03)

    # Dinding samping melengkung + kaca jendela kondensasi + garis terowongan luar
    for side in (-1.0, 1.0):
        tag = "L" if side < 0 else "R"
        make_box(f"Maglev_WallLower_{tag}", (0.16, 35.0, 0.98), w_to_b(side * 1.84, 0.49, 13.5), col_mag, mats["maglev_wall"], ink_mat=ink, outline_thickness=0.012)
        make_box(f"Maglev_WallUpper_{tag}", (0.18, 35.0, 0.72), w_to_b(side * 1.78, 2.34, 13.5), col_mag, mats["maglev_wall"], rotation_deg=(0.0, side * -12.0, 0.0), ink_mat=ink, outline_thickness=0.012)
        make_box(f"Maglev_WindowGlass_{tag}", (0.04, 26.0, 0.96), w_to_b(side * 1.82, 1.46, 10.0), col_mag, mats["obs_glass"], bevel_width=0.0)

        # Neon cyan & putih memanjang di langit-langit lorong kereta
        make_box(f"Maglev_NeonStrip_{tag}", (0.09, 32.0, 0.05), w_to_b(side * 0.92, 2.58, 13.0), col_mag, mats["neon_cyan"], bevel_width=0.01)

        # Garis cahaya terowongan luar yang melesat cepat (motion streak bars)
        for si in range(9):
            sz = -2.0 + si * 3.6
            sy = 0.8 + (si % 3) * 0.55
            st = make_box(f"Tunnel_Streak_{tag}_{si}", (0.06, 2.2, 0.07), w_to_b(side * 2.45, sy, sz), col_mag, mats["tunnel_streak"], bevel_width=0.01)
            dyn["tunnel_streaks"].append((st, sz))

    # Lampu neon putih berkedip di tengah plafon
    for ni in range(8):
        nz = -1.0 + ni * 3.8
        make_box(f"Maglev_CenterFluoro_{ni}", (0.46, 1.45, 0.05), w_to_b(0.0, 2.61, nz), col_mag, mats["neon_white"], bevel_width=0.01)

    # Kursi penumpang, siluet penumpang tanpa wajah, tiang vertikal & pegangan tangan berayun
    for row_i in range(6):
        rz = 0.5 + row_i * 3.4
        for side in (-1.0, 1.0):
            tag = "L" if side < 0 else "R"
            # Bangku samping kereta (x = ±1.42 -> lorong tengah -0.80..+0.80 bebas 100%!)
            make_box(f"Maglev_Bench_{tag}_{row_i}", (0.62, 2.2, 0.44), w_to_b(side * 1.44, 0.22, rz), col_mag, mats["maglev_seat"], ink_mat=ink, outline_thickness=0.01)
            # Tiang pegangan vertikal krom (x = ±0.88)
            make_cyl(f"Maglev_Pole_{tag}_{row_i}", 0.028, 0.028, 2.62, w_to_b(side * 0.88, 1.31, rz + 1.1), col_mag, mats["chrome_pole"])

            # Pegangan tangan menggantung yang berayun liar
            strap = make_torus_ring(f"Maglev_Strap_{tag}_{row_i}", 0.075, 0.016, w_to_b(side * 0.68, 2.18, rz + 0.4), col_mag, mats["helipad_yellow"], rotation_deg=(90.0, 0.0, 0.0))
            dyn["straps"].append((strap, row_i * 0.7 + (0.0 if side < 0 else 1.5)))

            # Siluet penumpang statis/buram tanpa wajah (kecuali kursi Maya di kanan z=17.5!)
            is_maya_seat = (side > 0 and row_i == 5)
            if not is_maya_seat and (row_i + (0 if side < 0 else 1)) % 2 == 0:
                make_box(f"MemPassenger_Torso_{tag}_{row_i}", (0.36, 0.42, 0.62), w_to_b(side * 1.38, 0.74, rz), col_mag, mats["silhouette_passenger"], bevel_width=0.08)
                make_sphere(f"MemPassenger_Head_{tag}_{row_i}", 0.16, w_to_b(side * 1.36, 1.22, rz), col_mag, mats["silhouette_passenger"], scale=(0.9, 0.95, 1.12))

    # Tas belanjaan tergeletak di bangku & layar rute digital glitch (1974 - 1998 - 2026)
    make_box("Maglev_ShoppingBag", (0.28, 0.34, 0.36), w_to_b(-1.32, 0.60, 7.4), col_mag, mats["helipad_yellow"], rotation_deg=(12.0, -18.0, 8.0), ink_mat=ink, outline_thickness=0.008)
    for di, dz in enumerate((6.0, 14.5, 22.2)):
        make_box(f"Maglev_RouteFrame_{di}", (1.35, 0.10, 0.28), w_to_b(0.0, 2.32, dz), col_mag, mats["briefcase_carbon"], ink_mat=ink, outline_thickness=0.008)
        make_box(f"Maglev_RouteScreen_{di}", (1.22, 0.12, 0.19), w_to_b(0.0, 2.32, dz), col_mag, mats["glitch_screen"], bevel_width=0.0)

    # Sekat Sambungan Gerbong (Lokasi 2, z=22.4) & Pintu Darurat Merah (z=29.8)
    for side in (-1.0, 1.0):
        tag = "L" if side < 0 else "R"
        make_box(f"Vestibule_Arch_{tag}", (0.72, 0.36, 2.68), w_to_b(side * 1.48, 1.34, 22.4), col_mag, mats["briefcase_carbon"], ink_mat=ink, outline_thickness=0.012)
        make_box(f"Portal_Wall_{tag}", (1.10, 0.28, 2.72), w_to_b(side * 1.35, 1.36, PORTAL_DOOR_Z), col_mag, mats["maglev_wall"], ink_mat=ink, outline_thickness=0.012)

    door_l = make_box("Portal_RedDoor_L", (0.84, 0.12, 2.36), w_to_b(-0.42, 1.18, PORTAL_DOOR_Z), col_mag, mats["red_portal_door"], ink_mat=ink, outline_thickness=0.012)
    door_r = make_box("Portal_RedDoor_R", (0.84, 0.12, 2.36), w_to_b(0.42, 1.18, PORTAL_DOOR_Z), col_mag, mats["red_portal_door"], ink_mat=ink, outline_thickness=0.012)
    dyn["portal_door_l"] = door_l
    dyn["portal_door_r"] = door_r

    # Tombol darurat merah menyala di kusen kanan pintu & backdrop cahaya badai di balik portal
    make_box("Emergency_Button_Box", (0.16, 0.14, 0.24), w_to_b(0.92, 1.24, PORTAL_DOOR_Z - 0.18), col_mag, mats["briefcase_carbon"], ink_mat=ink, outline_thickness=0.008)
    make_cyl("Emergency_Red_Btn", 0.055, 0.055, 0.08, w_to_b(0.92, 1.24, PORTAL_DOOR_Z - 0.25), col_mag, mats["beacon_red"], rotation_deg=(90.0, 0.0, 0.0))
    portal_glow = make_box("Portal_Storm_Void", (2.6, 0.10, 2.8), w_to_b(0.0, 1.35, PORTAL_DOOR_Z + 0.95), col_mag, mats["shatter_shard"], bevel_width=0.0)
    dyn["portal_glow"] = portal_glow

    # Hero Prop: Cincin Kawin Emas Maya (Bullet-Time di udara)
    flying_ring = make_torus_ring("Prop_Flying_GoldRing", 0.065, 0.016, w_to_b(0.45, 1.35, 18.2), col_mag, mats["gold_glow"])
    dyn["flying_ring"] = flying_ring

    # =========================================================================
    # LOKASI 3: MENARA AIR BAJA SEBERANG — KIRA SNIPER PERCH (Origin: 18, 44, 64)
    # =========================================================================
    col_wt = get_or_create_collection("Loc3_Sniper_WaterTower")
    wx, wy, wz = LOC3_ORIGIN

    # Dek baja tempat Kira membidik + pagar pengaman
    make_box("WT_SniperDeck", (4.6, 4.6, 0.22), w_to_b(wx, wy - 0.10, wz), col_wt, mats["rusted_steel"], ink_mat=ink, outline_thickness=0.014)
    for lx in (-1.9, 1.9):
        for lz in (-1.9, 1.9):
            make_cyl(f"WT_Leg_{lx}_{lz}", 0.14, 0.18, 12.0, w_to_b(wx + lx, wy - 6.0, wz + lz), col_wt, mats["rusted_steel"], ink_mat=ink, outline_thickness=0.012)
    make_box("WT_Railing_Front", (4.4, 0.08, 0.88), w_to_b(wx - 2.15, wy + 0.44, wz), col_wt, mats["rusted_steel"], rotation_deg=(0.0, 0.0, 90.0))

    # Tangki silinder menara air baja berkarat + atap kerucut + antena berkedip merah
    make_cyl("WT_Tank_Body", 1.85, 1.85, 3.6, w_to_b(wx + 0.8, wy + 2.8, wz + 0.8), col_wt, mats["rusted_steel"], segments=24, ink_mat=ink, outline_thickness=0.016)
    make_cyl("WT_Tank_Roof", 2.05, 0.08, 1.35, w_to_b(wx + 0.8, wy + 5.25, wz + 0.8), col_wt, mats["rusted_steel"], segments=24, ink_mat=ink, outline_thickness=0.014)
    make_cyl("WT_Antenna_Mast", 0.05, 0.02, 3.8, w_to_b(wx - 1.5, wy + 1.9, wz + 1.6), col_wt, mats["chrome_pole"])
    beacon = make_sphere("WT_Beacon_Red", 0.14, w_to_b(wx - 1.5, wy + 3.85, wz + 1.6), col_wt, mats["beacon_red"])
    dyn["tower_beacon"] = beacon

    # Senapan Sniper Laser Kira di atas bipod pagar menara
    make_box("Kira_Sniper_Rifle", (1.25, 0.10, 0.16), w_to_b(wx - 1.75, wy + 0.98, wz - 0.35), col_wt, mats["briefcase_carbon"], rotation_deg=(0.0, 12.0, -14.0), ink_mat=ink, outline_thickness=0.008)
    make_cyl("Kira_Sniper_Scope", 0.045, 0.055, 0.36, w_to_b(wx - 1.62, wy + 1.11, wz - 0.35), col_wt, mats["red_portal_door"], rotation_deg=(0.0, 102.0, -14.0))

    # =========================================================================
    # LOKASI 4: ATAP GEDUNG PENCAKAR LANGIT "APEX TOWER" (Z=46..74, Y=38.0)
    # =========================================================================
    col_roof = get_or_create_collection("Loc4_Apex_Storm_Rooftop")

    # Pelat beton brutalist basah penuh genangan + parapet keliling
    make_box("Apex_Roof_Slab", (16.5, 29.0, 0.60), w_to_b(0.0, LOC4_FLOOR_Y - 0.30, 60.0), col_roof, mats["wet_concrete"], bevel_width=0.04)
    make_torus_ring("Apex_Helipad_Ring", 4.4, 0.14, w_to_b(0.0, LOC4_FLOOR_Y + 0.01, 60.5), col_roof, mats["helipad_yellow"])
    make_box("Apex_Helipad_H1", (0.28, 2.6, 0.02), w_to_b(-0.95, LOC4_FLOOR_Y + 0.015, 60.5), col_roof, mats["helipad_yellow"], bevel_width=0.0)
    make_box("Apex_Helipad_H2", (0.28, 2.6, 0.02), w_to_b(0.95, LOC4_FLOOR_Y + 0.015, 60.5), col_roof, mats["helipad_yellow"], bevel_width=0.0)
    make_box("Apex_Helipad_HBar", (1.9, 0.28, 0.02), w_to_b(0.0, LOC4_FLOOR_Y + 0.015, 60.5), col_roof, mats["helipad_yellow"], bevel_width=0.0)

    # Parapet beton rendah di sekeliling tepi jurang
    for side in (-1.0, 1.0):
        make_box(f"Apex_Parapet_Side_{side}", (0.42, 28.6, 0.72), w_to_b(side * 8.0, LOC4_FLOOR_Y + 0.36, 60.0), col_roof, mats["wet_concrete"], ink_mat=ink, outline_thickness=0.015)
    make_box("Apex_Parapet_Back", (16.4, 0.42, 0.72), w_to_b(0.0, LOC4_FLOOR_Y + 0.36, 74.1), col_roof, mats["wet_concrete"], ink_mat=ink, outline_thickness=0.015)

    # Pintu Merah Kereta berdiri bebas secara surealis di tengah beton atap!
    make_box("Apex_Surreal_Frame_L", (0.18, 0.22, 2.48), w_to_b(-0.92, LOC4_FLOOR_Y + 1.24, ROOFTOP_DOOR_Z), col_roof, mats["red_portal_door"], ink_mat=ink, outline_thickness=0.012)
    make_box("Apex_Surreal_Frame_R", (0.18, 0.22, 2.48), w_to_b(0.92, LOC4_FLOOR_Y + 1.24, ROOFTOP_DOOR_Z), col_roof, mats["red_portal_door"], ink_mat=ink, outline_thickness=0.012)
    make_box("Apex_Surreal_Frame_Top", (2.02, 0.24, 0.20), w_to_b(0.0, LOC4_FLOOR_Y + 2.44, ROOFTOP_DOOR_Z), col_roof, mats["red_portal_door"], ink_mat=ink, outline_thickness=0.012)
    rdoor_l = make_box("Apex_Surreal_Door_L", (0.82, 0.12, 2.34), w_to_b(-0.42, LOC4_FLOOR_Y + 1.17, ROOFTOP_DOOR_Z), col_roof, mats["red_portal_door"], ink_mat=ink, outline_thickness=0.012)
    rdoor_r = make_box("Apex_Surreal_Door_R", (0.82, 0.12, 2.34), w_to_b(0.42, LOC4_FLOOR_Y + 1.17, ROOFTOP_DOOR_Z), col_roof, mats["red_portal_door"], ink_mat=ink, outline_thickness=0.012)
    dyn["rooftop_door_l"] = rdoor_l
    dyn["rooftop_door_r"] = rdoor_r

    # Unit pendingin AC industri raksasa + kipas berputar + kabel berserakan + papan peringatan
    for idx, ax in enumerate((-5.6, 5.8)):
        az = 66.5 if idx == 0 else 52.8
        make_box(f"Apex_AC_Housing_{idx}", (2.2, 1.8, 1.65), w_to_b(ax, LOC4_FLOOR_Y + 0.82, az), col_roof, mats["ac_industrial"], ink_mat=ink, outline_thickness=0.014)
        fan = make_box(f"Apex_AC_Fan_{idx}", (1.35, 0.18, 0.06), w_to_b(ax, LOC4_FLOOR_Y + 1.68, az), col_roof, mats["chrome_pole"])
        dyn["ac_fans"].append(fan)

    make_curve_cable("Apex_Cable_1", [w_to_b(-5.2, LOC4_FLOOR_Y + 0.04, 65.2), w_to_b(-2.8, LOC4_FLOOR_Y + 0.03, 63.0), w_to_b(-0.8, LOC4_FLOOR_Y + 0.03, 56.2)], 0.035, col_roof, mats["briefcase_carbon"])
    make_curve_cable("Apex_Cable_2", [w_to_b(5.4, LOC4_FLOOR_Y + 0.04, 53.6), w_to_b(3.1, LOC4_FLOOR_Y + 0.03, 57.4), w_to_b(1.0, LOC4_FLOOR_Y + 0.03, 56.1)], 0.035, col_roof, mats["briefcase_carbon"])
    wind_sign = make_box("Apex_Warning_Sign", (0.75, 0.06, 0.55), w_to_b(-6.8, LOC4_FLOOR_Y + 1.15, 59.5), col_roof, mats["helipad_yellow"], ink_mat=ink, outline_thickness=0.01)
    dyn["wind_sign"] = wind_sign

    # Siluet kota metropolitan di kejauhan bawah awan badai
    skyline_coords = [(-22, 84, 34), (-14, 88, 41), (-5, 92, 38), (6, 90, 43), (16, 86, 36), (25, 82, 39)]
    for bi, (bx, bz, bh) in enumerate(skyline_coords):
        make_box(f"Metro_Tower_{bi}", (5.2, 5.2, bh), w_to_b(bx, LOC4_FLOOR_Y - 16.0 + bh * 0.5, bz), col_roof, mats["city_skyline"], bevel_width=0.08)

    # Hero Props Babak II: Koper Baja Hitam-Emas, Kue Ulang Tahun Kecil + Api Lilin Hangat, Laser Merah & Scanner Biru
    bc_base = make_box("Prop_Briefcase_Base", (0.52, 0.38, 0.09), w_to_b(*CAKE_POS_W), col_roof, mats["briefcase_carbon"], ink_mat=ink, outline_thickness=0.008)
    bc_gold = make_box("Prop_Briefcase_GoldTrim", (0.54, 0.40, 0.025), w_to_b(CAKE_POS_W[0], CAKE_POS_W[1] + 0.045, CAKE_POS_W[2]), col_roof, mats["gold_glow"])
    bc_lid = make_box("Prop_Briefcase_Lid", (0.52, 0.38, 0.07), w_to_b(CAKE_POS_W[0], CAKE_POS_W[1] + 0.18, CAKE_POS_W[2] + 0.16), col_roof, mats["briefcase_carbon"], rotation_deg=(-72.0, 0.0, 0.0), ink_mat=ink, outline_thickness=0.008)
    dyn["briefcase_base"] = bc_base
    dyn["briefcase_gold"] = bc_gold
    dyn["briefcase_lid"] = bc_lid

    cake_body = make_cyl("Prop_Birthday_Cake", 0.13, 0.13, 0.11, w_to_b(CAKE_POS_W[0], CAKE_POS_W[1] + 0.10, CAKE_POS_W[2]), col_roof, mats["cake_sponge"], ink_mat=ink, outline_thickness=0.006)
    cake_top = make_cyl("Prop_Birthday_Icing", 0.136, 0.136, 0.035, w_to_b(CAKE_POS_W[0], CAKE_POS_W[1] + 0.155, CAKE_POS_W[2]), col_roof, mats["cake_icing"])
    candle = make_cyl("Prop_Candle_Stick", 0.014, 0.014, 0.09, w_to_b(CAKE_POS_W[0], CAKE_POS_W[1] + 0.21, CAKE_POS_W[2]), col_roof, mats["cotton_sheet"])
    flame = make_sphere("Prop_Candle_Flame", 0.028, w_to_b(CAKE_POS_W[0], CAKE_POS_W[1] + 0.275, CAKE_POS_W[2]), col_roof, mats["candle_flame"], scale=(0.75, 0.75, 1.65))
    dyn["cake_parts"] = [cake_body, cake_top, candle, flame]
    dyn["candle_flame"] = flame

    # Volumetric Red Sniper Laser Beam & Sena's Blue Scanner Cone
    laser_beam = make_cyl("Prop_Red_Laser_Beam", 0.016, 0.016, 22.0, w_to_b(8.0, 41.2, 62.5), col_roof, mats["laser_red"], rotation_deg=(0.0, 74.0, 12.0), bevel_width=0.0)
    scanner_cone = make_cyl("Prop_Blue_Scanner_Cone", 0.42, 0.03, 2.4, w_to_b(-0.6, LOC4_FLOOR_Y + 1.35, 59.8), col_roof, mats["scanner_blue"], rotation_deg=(90.0, 0.0, -25.0), bevel_width=0.0)
    dyn["laser_beam"] = laser_beam
    dyn["scanner_cone"] = scanner_cone

    # 56 Partikel Hujan 3D (turun deras lalu berbalik naik ke langit saat t=40..46s!)
    for ri in range(56):
        rx = rng.uniform(-6.5, 6.5)
        rz = rng.uniform(51.0, 69.0)
        ry_seed = rng.uniform(0.0, 8.5)
        rd = make_cyl(f"Rain_Streak_{ri}", 0.010, 0.010, 0.42, w_to_b(rx, LOC4_FLOOR_Y + ry_seed, rz), col_roof, mats["rain_drop"], bevel_width=0.0)
        dyn["rain_drops"].append((rd, rx, ry_seed, rz))

    # 32 Serpihan Kaca Kristal Putih (saat gedung & realitas pecah di t=42..46s!)
    for si in range(32):
        ang = (si / 32.0) * math.tau
        rad_d = rng.uniform(1.2, 5.8)
        sx = math.cos(ang) * rad_d
        sz = 61.0 + math.sin(ang) * rad_d
        sy = rng.uniform(0.6, 4.4)
        sh = make_box(f"Reality_Shard_{si}", (0.28, 0.03, 0.38), w_to_b(sx, LOC4_FLOOR_Y + sy, sz), col_roof, mats["shatter_shard"], rotation_deg=(rng.uniform(0, 180), rng.uniform(0, 180), rng.uniform(0, 180)), bevel_width=0.005)
        dyn["shatter_shards"].append((sh, sx, sy, sz))

    # =========================================================================
    # LOKASI 5: RUANG PERAWATAN INTENSIF "ICU KAMAR 404" (X=-4.2..3.55, Z=104..117, Y=12.0)
    # =========================================================================
    col_icu = get_or_create_collection("Loc5_ICU_Room_404")

    make_box("ICU_Floor", (8.0, 13.5, 0.16), w_to_b(-0.3, LOC5_FLOOR_Y - 0.08, 110.5), col_icu, mats["icu_vinyl_floor"], bevel_width=0.02)
    make_box("ICU_Ceiling", (8.0, 13.5, 0.18), w_to_b(-0.3, LOC5_FLOOR_Y + 3.45, 110.5), col_icu, mats["icu_wall"], bevel_width=0.02)
    make_box("ICU_Wall_Left", (0.20, 13.5, 3.5), w_to_b(-4.2, LOC5_FLOOR_Y + 1.75, 110.5), col_icu, mats["icu_wall"])
    make_box("ICU_Wall_Back", (8.0, 0.20, 3.5), w_to_b(-0.3, LOC5_FLOOR_Y + 1.75, 117.0), col_icu, mats["icu_wall"])
    make_box("ICU_Wall_Front", (8.0, 0.20, 3.5), w_to_b(-0.3, LOC5_FLOOR_Y + 1.75, 104.0), col_icu, mats["icu_wall"])

    # Dinding kanan dengan JENDELA KACA OBSERVASI BESAR menghadap Koridor Cahaya Keemasan!
    make_box("ICU_Wall_Right_Low", (0.18, 13.5, 0.92), w_to_b(ICU_GLASS_X, LOC5_FLOOR_Y + 0.46, 110.5), col_icu, mats["icu_wall"], ink_mat=ink, outline_thickness=0.01)
    make_box("ICU_Wall_Right_Top", (0.18, 13.5, 0.68), w_to_b(ICU_GLASS_X, LOC5_FLOOR_Y + 3.12, 110.5), col_icu, mats["icu_wall"], ink_mat=ink, outline_thickness=0.01)
    make_box("ICU_Obs_Window_Glass", (0.04, 8.8, 1.88), w_to_b(ICU_GLASS_X, LOC5_FLOOR_Y + 1.86, 111.0), col_icu, mats["obs_glass"], bevel_width=0.0)

    # Ranjang Pasien ICU + Kasur Katun Putih + Bantal (disembunyikan saat twist ranjang kosong t>=68.4s!)
    bx, by, bz = ICU_BED_POS_W
    bed_frame = make_box("ICU_Bed_Frame", (1.18, 2.24, 0.56), w_to_b(bx, by + 0.34, bz), col_icu, mats["hospital_bed_frame"], ink_mat=ink, outline_thickness=0.01)
    mattress = make_box("ICU_Bed_Mattress", (1.10, 2.12, 0.24), w_to_b(bx, ICU_MATTRESS_Y - 0.12, bz), col_icu, mats["cotton_sheet"], bevel_width=0.06, ink_mat=ink, outline_thickness=0.008)
    pillow = make_box("ICU_Bed_Pillow", (0.76, 0.46, 0.16), w_to_b(bx, ICU_MATTRESS_Y + 0.08, bz + 0.72), col_icu, mats["cotton_sheet"], bevel_width=0.06, rotation_deg=(14.0, 0.0, 0.0))
    blanket = make_box("ICU_Bed_Blanket", (1.14, 1.32, 0.26), w_to_b(bx, ICU_MATTRESS_Y + 0.04, bz - 0.34), col_icu, mats["cotton_sheet"], bevel_width=0.07, ink_mat=ink, outline_thickness=0.008)
    dyn["icu_bed_parts"] = [bed_frame, mattress, pillow, blanket]

    # Monitor EKG & Tanda Vital (Layar hitam + gelombang merah tajam / flatline)
    make_cyl("ICU_EKG_Stand", 0.04, 0.05, 1.35, w_to_b(bx + 0.98, by + 0.68, bz + 0.68), col_icu, mats["hospital_bed_frame"])
    make_box("ICU_EKG_Monitor", (0.56, 0.18, 0.42), w_to_b(bx + 0.98, by + 1.48, bz + 0.68), col_icu, mats["ekg_screen"], rotation_deg=(0.0, -24.0, 0.0), ink_mat=ink, outline_thickness=0.008)
    ekg_wave = make_box("Prop_EKG_PulseWave", (0.44, 0.02, 0.11), w_to_b(bx + 0.94, by + 1.49, bz + 0.58), col_icu, mats["ekg_red_line"], rotation_deg=(0.0, -24.0, 0.0), bevel_width=0.0)
    ekg_flat = make_box("Prop_EKG_Flatline", (0.46, 0.02, 0.018), w_to_b(bx + 0.94, by + 1.49, bz + 0.58), col_icu, mats["ekg_red_line"], rotation_deg=(0.0, -24.0, 0.0), bevel_width=0.0)
    dyn["ekg_wave"] = ekg_wave
    dyn["ekg_flat"] = ekg_flat

    # Tiang Infus & Tetesan Cairan Bening (jembatan match-cut dari hujan badai!)
    make_cyl("ICU_IV_Pole", 0.022, 0.028, 1.95, w_to_b(bx - 0.85, by + 0.98, bz + 0.55), col_icu, mats["chrome_pole"])
    make_box("ICU_IV_Bag", (0.14, 0.08, 0.24), w_to_b(bx - 0.85, by + 1.82, bz + 0.55), col_icu, mats["iv_fluid"], bevel_width=0.03)
    iv_drop = make_sphere("Prop_IV_Droplet", 0.024, w_to_b(bx - 0.85, by + 1.56, bz + 0.55), col_icu, mats["iv_fluid"], scale=(0.8, 0.8, 1.4))
    dyn["iv_drop"] = iv_drop

    # Meja Nakas Kayu + Foto Pernikahan Raka-Maya + Kue Mika + Bunga Lili Layu + Cincin Emas Bergetar
    nx, nz = bx - 1.15, bz - 0.15
    make_box("ICU_Nightstand", (0.56, 0.52, 0.72), w_to_b(nx, by + 0.36, nz), col_icu, mats["warm_oak"], ink_mat=ink, outline_thickness=0.009)
    make_box("ICU_Wedding_Frame", (0.18, 0.04, 0.23), w_to_b(nx + 0.10, by + 0.84, nz + 0.08), col_icu, mats["gold_glow"], rotation_deg=(-12.0, 22.0, 0.0), ink_mat=ink, outline_thickness=0.005)
    make_box("ICU_Mica_CakeBox", (0.18, 0.18, 0.15), w_to_b(nx - 0.12, by + 0.80, nz - 0.08), col_icu, mats["obs_glass"], bevel_width=0.01)
    make_cyl("ICU_Mini_Cake", 0.065, 0.065, 0.065, w_to_b(nx - 0.12, by + 0.76, nz - 0.08), col_icu, mats["cake_sponge"])
    make_cyl("ICU_Lily_Vase", 0.055, 0.042, 0.20, w_to_b(nx - 0.14, by + 0.82, nz + 0.14), col_icu, mats["iv_fluid"])
    make_sphere("ICU_Drooping_Lily", 0.075, w_to_b(nx - 0.08, by + 0.95, nz + 0.14), col_icu, mats["lily_white"], scale=(1.2, 0.7, 0.8))

    icu_ring = make_torus_ring("Prop_ICU_GoldRing", 0.048, 0.013, w_to_b(nx + 0.14, by + 0.74, nz - 0.12), col_icu, mats["gold_glow"])
    dyn["icu_ring"] = icu_ring

    # Kursi lipat keluarga & Jam Dinding Analog (jarum detik menyentuh angka 15 di detik ke-75!)
    make_box("ICU_Chair_1", (0.48, 0.48, 0.46), w_to_b(bx + 1.05, by + 0.23, bz - 0.35), col_icu, mats["hospital_bed_frame"], ink_mat=ink, outline_thickness=0.008)
    make_cyl("ICU_Wall_Clock", 0.26, 0.26, 0.05, w_to_b(-1.8, LOC5_FLOOR_Y + 2.55, 116.85), col_icu, mats["cotton_sheet"], rotation_deg=(90.0, 0.0, 0.0), ink_mat=ink, outline_thickness=0.008)
    clock_sec = make_box("Prop_Clock_SecHand", (0.016, 0.02, 0.20), w_to_b(-1.8, LOC5_FLOOR_Y + 2.55, 116.80), col_icu, mats["red_portal_door"], bevel_width=0.0)
    dyn["clock_sec"] = clock_sec

    # =========================================================================
    # LOKASI 6: KORIDOR CAHAYA KEEMASAN (X=3.65..11.5, Z=102..124, Y=12.0)
    # =========================================================================
    col_cor = get_or_create_collection("Loc6_Golden_Corridor")

    make_box("Corridor_Floor", (7.8, 22.0, 0.16), w_to_b(7.5, LOC6_FLOOR_Y - 0.08, 113.0), col_cor, mats["corridor_gold_floor"], bevel_width=0.02)
    make_box("Corridor_Ceiling", (7.8, 22.0, 0.18), w_to_b(7.5, LOC6_FLOOR_Y + 3.85, 113.0), col_cor, mats["corridor_gold_wall"])
    make_box("Corridor_FarWall", (0.24, 22.0, 3.9), w_to_b(11.3, LOC6_FLOOR_Y + 1.95, 113.0), col_cor, mats["corridor_gold_wall"])

    # Pilar koridor & berkas Volumetric God Rays keemasan miring (Low Sun + Long Shadows!)
    for pi in range(5):
        pz = 105.0 + pi * 4.2
        make_box(f"Corridor_Pillar_{pi}", (0.36, 0.36, 3.8), w_to_b(10.8, LOC6_FLOOR_Y + 1.9, pz), col_cor, mats["corridor_gold_wall"], ink_mat=ink, outline_thickness=0.012)
        make_cyl(f"Corridor_GodRay_{pi}", 0.95, 0.32, 6.2, w_to_b(8.2, LOC6_FLOOR_Y + 2.1, pz + 1.2), col_cor, mats["godray_cone"], rotation_deg=(0.0, -52.0, 0.0), bevel_width=0.0)

    # Koper bersinar hangat yang dibawa Raka Muda di Koridor Emas
    cor_case = make_box("Prop_Corridor_Briefcase", (0.48, 0.16, 0.34), w_to_b(6.6, LOC6_FLOOR_Y + 0.72, 112.0), col_cor, mats["gold_glow"], ink_mat=ink, outline_thickness=0.008)
    dyn["corridor_briefcase"] = cor_case

    return dyn
