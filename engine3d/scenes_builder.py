"""
Pembangun Dunia 3D Terpadu — 6 Lokasi Saling Terhubung untuk Continuous One-Take Virtual Camera:
  - Lokasi 1 (00:00-00:09): Bengkel Jam Loteng (y=26, z=0..4.2)
  - Lokasi 2 (00:09-00:18): Pasar Rempah & Buah Bertingkat (y=5..24, z=7..28)
  - Lokasi 3 (00:18-00:26): Gang Kafe & Jemuran Sempit (y=5, z=28..44)
  - [Hidden Wipe Cut 2-frame melalui Jeruji Selokan z=42.5]
  - Lokasi 4 (00:26-00:38): Gorong-Gorong Mesin Jam Kuno (y=-22..-6, z=36..58) + Cerobong Uap (z=62)
  - Lokasi 5 (00:38-00:49): Stasiun Trem Layang Terbuka (y=10, z=60..112)
  - Lokasi 6 (00:49-00:58): Wajah Menara Jam Utama di Dermaga (y=19.5, z=118) + Loop Gears (z=123)
"""

from __future__ import annotations

import math
from typing import Tuple

import numpy as np

from .geometry import (
    MAT_BRASS,
    MAT_COBBLE,
    MAT_EMISSIVE,
    MAT_FABRIC,
    MAT_GLASS,
    MAT_OXIDIZED,
    MAT_PLASTER,
    MAT_PROP,
    MAT_WOOD,
    MeshBuilder,
    hex_rgb,
)


def _build_lokasi_1_bengkel(mb: MeshBuilder) -> None:
    """LOKASI 1: Bengkel Jam Loteng (y=25.0..30.8, z=-4.5..+4.2)."""
    oak = hex_rgb("#8B5A2B")
    oak_dark = hex_rgb("#5A3718")
    plaster_wall = hex_rgb("#C8B8A2")
    peel_teal = hex_rgb("#52858A")
    brass = hex_rgb("#D6A028")
    brass_old = hex_rgb("#9E741A")
    lamp_green = hex_rgb("#1E7B4A")

    # Lantai loteng, langit-langit miring, dinding kiri/kanan/belakang
    mb.add_box((0.0, 24.8, 0.0), (9.0, 0.35, 9.2), oak_dark, MAT_WOOD)
    mb.add_box((0.0, 30.8, 0.0), (9.5, 0.4, 9.6), oak_dark, MAT_WOOD)
    mb.add_box((-4.4, 27.8, 0.0), (0.35, 6.2, 9.2), plaster_wall, MAT_PLASTER)
    mb.add_box((4.4, 27.8, 0.0), (0.35, 6.2, 9.2), plaster_wall, MAT_PLASTER)
    mb.add_box((0.0, 27.8, -4.5), (9.0, 6.2, 0.35), hex_rgb("#5A5164"), MAT_PLASTER)
    # Balok kayu langit-langit
    for bz in (-3.2, -1.0, 1.4, 3.6):
        mb.add_box((0.0, 30.35, bz), (8.8, 0.36, 0.32), oak_dark, MAT_WOOD)

    # Dinding depan jendela terbuka (z=+4.2) dengan bingkai kayu cat mengelupas menghadap kota pesisir!
    mb.add_box((-3.0, 27.8, 4.2), (2.9, 6.2, 0.36), plaster_wall, MAT_PLASTER)
    mb.add_box((3.0, 27.8, 4.2), (2.9, 6.2, 0.36), plaster_wall, MAT_PLASTER)
    mb.add_box((0.0, 25.55, 4.2), (3.4, 1.5, 0.36), plaster_wall, MAT_PLASTER)
    mb.add_box((0.0, 29.85, 4.2), (3.4, 1.8, 0.36), plaster_wall, MAT_PLASTER)
    # Bingkai jendela kayu biru-toska terkelupas + daun jendela terbuka keluar
    mb.add_box((0.0, 26.32, 4.25), (3.35, 0.16, 0.56), peel_teal, MAT_PLASTER)  # ambang jendela
    mb.add_box((0.0, 28.95, 4.25), (3.35, 0.16, 0.46), peel_teal, MAT_PLASTER)
    mb.add_box((-1.62, 27.65, 4.25), (0.16, 2.7, 0.46), peel_teal, MAT_PLASTER)
    mb.add_box((1.62, 27.65, 4.25), (0.16, 2.7, 0.46), peel_teal, MAT_PLASTER)
    # Daun jendela terbuka ke luar kota
    mb.add_box((-2.15, 27.65, 4.82), (0.10, 2.55, 1.15), peel_teal, MAT_WOOD, rot_deg=(0, -34, 0))
    mb.add_box((2.15, 27.65, 4.82), (0.10, 2.55, 1.15), peel_teal, MAT_WOOD, rot_deg=(0, 34, 0))

    # Meja kerja kayu oak penuh goresan (y=26.0, z=0.4..3.6)
    mb.add_box((0.0, 26.0, 2.1), (4.6, 0.18, 3.2), oak, MAT_WOOD)
    for lx in (-2.05, 2.05):
        for lz in (0.75, 3.45):
            mb.add_box((lx, 25.4, lz), (0.18, 1.15, 0.18), oak_dark, MAT_WOOD)

    # Cangkir teh porselen retak (target pantulan Kunci Emas di [CAM 03]!)
    cx, cy, cz = 0.55, 26.10, 1.55
    mb.add_cylinder((cx, cy + 0.02, cz), 0.24, 0.26, 0.035, hex_rgb("#F4EFE6"), MAT_PROP, segments=16)
    mb.add_cylinder((cx, cy + 0.15, cz), 0.14, 0.175, 0.23, hex_rgb("#FAF6EE"), MAT_PROP, segments=16)
    mb.add_cylinder((cx, cy + 0.23, cz), 0.145, 0.145, 0.03, hex_rgb("#7C441E"), MAT_PROP, segments=14)  # isi teh
    mb.add_box((cx + 0.20, cy + 0.16, cz), (0.10, 0.12, 0.04), hex_rgb("#D84A3A"), MAT_PROP)  # pegangan hias

    # Ratusan/puluhan roda gigi kuningan berserakan di meja & dinding
    desk_gears = [
        (-1.25, 26.12, 1.20, 0.24, 10, brass),
        (-0.82, 26.12, 1.75, 0.17, 8, brass_old),
        (-1.45, 26.12, 2.45, 0.30, 12, brass),
        (1.15, 26.12, 2.15, 0.26, 12, brass),
        (0.92, 26.12, 2.85, 0.19, 10, hex_rgb("#C97538")),
        (-0.35, 26.12, 2.95, 0.22, 10, brass),
        (1.55, 26.12, 1.15, 0.28, 12, brass_old),
    ]
    for gx, gy, gz, gr, gt, gc in desk_gears:
        mb.add_cogwheel((gx, gy, gz), gr, 0.055, gc, teeth=gt, mat_id=MAT_BRASS, rot_deg=(90, 0, gx * 40))

    # Obeng warna-warni & kaca pembesar sejajar jalur gulir [CAM 04]
    for ox, oz, col_h, ang_y in [
        (-0.65, 2.20, hex_rgb("#267CE0"), 28),
        (-0.18, 2.58, hex_rgb("#E24432"), -18),
        (0.75, 2.65, hex_rgb("#24A868"), 42),
    ]:
        mb.add_cylinder((ox, 26.14, oz), 0.045, 0.045, 0.24, col_h, MAT_PROP, segments=10, rot_deg=(90, ang_y, 0))
        mb.add_cylinder((ox + 0.18, 26.14, oz + 0.08), 0.014, 0.014, 0.28, hex_rgb("#C6D0DE"), MAT_BRASS, segments=8, rot_deg=(90, ang_y, 0))
    # Kaca pembesar di meja
    mb.add_cylinder((-0.85, 26.14, 2.95), 0.18, 0.18, 0.04, brass, MAT_BRASS, segments=16)
    mb.add_cylinder((-0.85, 26.145, 2.95), 0.145, 0.145, 0.03, hex_rgb("#A8E4F8"), MAT_GLASS, segments=16)
    mb.add_cylinder((-1.15, 26.14, 3.12), 0.032, 0.038, 0.34, oak_dark, MAT_WOOD, segments=8, rot_deg=(90, 60, 0))

    # Toples kaca isi pegas warna-warni di belakang & samping meja
    jar_specs = [
        (-1.82, 26.38, 1.35, hex_rgb("#E84A38")),
        (-1.72, 26.34, 2.05, hex_rgb("#28B5A8")),
        (-1.86, 26.40, 2.85, hex_rgb("#F0B429")),
        (1.88, 26.36, 2.85, hex_rgb("#C84692")),
    ]
    for jx, jy, jz, scol in jar_specs:
        mb.add_cylinder((jx, jy, jz), 0.19, 0.19, 0.48, hex_rgb("#DCEFF4"), MAT_GLASS, segments=14)
        mb.add_cylinder((jx, jy + 0.27, jz), 0.17, 0.17, 0.08, brass_old, MAT_BRASS, segments=12)
        for sy in (-0.12, 0.0, 0.12):
            mb.add_cylinder((jx, jy + sy, jz), 0.12, 0.12, 0.06, scol, MAT_PROP, segments=10)

    # Lampu meja hijau klasik (banker's desk lamp) di sudut kanan meja
    mb.add_cylinder((1.72, 26.14, 1.75), 0.24, 0.16, 0.10, brass, MAT_BRASS, segments=14)
    mb.add_cylinder((1.72, 26.52, 1.75), 0.045, 0.035, 0.72, brass, MAT_BRASS, segments=10)
    mb.add_box((1.55, 26.86, 1.75), (0.56, 0.24, 0.34), lamp_green, MAT_GLASS, rot_deg=(0, 0, 18))
    mb.add_sphere((1.55, 26.76, 1.75), 0.11, hex_rgb("#FFF5BE"), MAT_EMISSIVE, seg_u=8, seg_v=6)

    # Jam dinding kayu cat terkelupas di dinding kiri & rak warna-warni di dinding kanan
    mb.add_box((-4.15, 28.0, 1.6), (0.28, 1.9, 1.15), hex_rgb("#48737A"), MAT_PLASTER)
    mb.add_cylinder((-3.98, 28.35, 1.6), 0.42, 0.42, 0.08, hex_rgb("#F7EFE0"), MAT_GLASS, segments=16, rot_deg=(0, 0, 90))
    mb.add_box((-3.92, 28.50, 1.6), (0.04, 0.30, 0.045), hex_rgb("#1E1822"), MAT_OXIDIZED)
    mb.add_box((-3.92, 28.35, 1.72), (0.04, 0.045, 0.24), hex_rgb("#1E1822"), MAT_OXIDIZED)

    # Rak dinding kanan penuh kotak perkakas warna-warni
    mb.add_box((4.05, 27.6, 1.8), (0.55, 0.12, 4.6), oak, MAT_WOOD)
    for rz, rcol in [(0.4, "#C84232"), (1.2, "#2A8F8D"), (2.1, "#D68E2A"), (3.0, "#3E669E")]:
        mb.add_box((4.0, 27.92, rz), (0.42, 0.50, 0.56), hex_rgb(rcol), MAT_PROP)


def _build_lokasi_2_pasar(mb: MeshBuilder) -> None:
    """LOKASI 2: Pasar Rempah & Buah Bertingkat (y=5.0..25.0, z=6.0..28.0)."""
    stone = hex_rgb("#B8AA96")
    stone_dark = hex_rgb("#8B7D6B")
    wood = hex_rgb("#7A4E2A")

    # Bangunan bertingkat di kiri & kanan (balkon warna-warni melesat ke atas saat [CAM 06]!)
    facades = [
        # Kiri (x = -5.8)
        (-6.2, 20.5, 9.5, 4.2, 17.0, 6.2, "#D67A5A"),
        (-6.4, 15.5, 16.0, 4.4, 15.0, 6.6, "#6EA0A8"),
        (-6.2, 12.0, 22.8, 4.2, 13.5, 6.6, "#DFC28C"),
        # Kanan (x = +5.8)
        (6.2, 20.5, 9.5, 4.2, 17.0, 6.2, "#E3B878"),
        (6.4, 15.5, 16.0, 4.4, 15.0, 6.6, "#C95D4E"),
        (6.2, 12.0, 22.8, 4.2, 13.5, 6.6, "#689B82"),
    ]
    for fx, fy, fz, fw, fh, fd, fcol in facades:
        mb.add_box((fx, fy, fz), (fw, fh, fd), hex_rgb(fcol), MAT_PLASTER)
        # Balkon bertingkat untuk 3D parallax ekstrem di [CAM 06]!
        side_s = 1.0 if fx < 0 else -1.0
        bx = fx + side_s * (fw * 0.5 + 0.55)
        for by in (fy + 4.8, fy + 1.2, fy - 2.4):
            mb.add_box((bx, by, fz), (1.15, 0.18, fd * 0.72), stone_dark, MAT_PLASTER)
            mb.add_box((bx + side_s * 0.52, by + 0.52, fz), (0.09, 0.9, fd * 0.70), hex_rgb("#2C3542"), MAT_OXIDIZED)
            # Pot bunga & kain gantung warna-warni di balkon
            mb.add_box((bx + side_s * 0.42, by + 0.98, fz - 0.9), (0.34, 0.28, 1.3), hex_rgb("#D83268"), MAT_PROP)
            mb.add_box((bx + side_s * 0.42, by + 0.98, fz + 1.0), (0.34, 0.28, 1.2), hex_rgb("#26A69A"), MAT_PROP)

    # Teras batu pasar bertingkat turun dari z=7 (y=14.2) ke z=20 (y=11.0) lalu tangga batu turun ke y=5.0 di z=28
    mb.add_box((0.0, 13.6, 10.5), (10.5, 1.2, 7.0), stone, MAT_COBBLE)
    mb.add_box((0.0, 11.4, 16.5), (10.5, 1.2, 6.2), stone, MAT_COBBLE)

    # Tangga batu kuno (z=19.6..27.6, turun dari y=11.5 ke y=5.0) + rel kayu samping ([CAM 10]!)
    steps = 16
    for i in range(steps):
        u = i / float(steps)
        sy = 11.4 - u * 6.4
        sz = 19.6 + u * 8.0
        mb.add_box((0.0, sy - 0.35, sz), (8.2, 0.7, 0.62), stone if i % 2 == 0 else stone_dark, MAT_COBBLE)
    # Rel kayu meluncur samping tangga (kunci meluncur di rel ini di [CAM 10]!)
    mb.add_box((1.95, 8.95, 23.6), (0.24, 0.18, 10.4), hex_rgb("#966032"), MAT_WOOD, rot_deg=(38.5, 0, 0))
    for pz, py in [(20.2, 11.2), (22.4, 9.5), (24.8, 7.6), (27.0, 5.8)]:
        mb.add_box((1.95, py + 0.45, pz), (0.16, 1.15, 0.16), wood, MAT_WOOD)

    # TENDA-TENDA KAIN PASAR WARNA-WARNI (Merah hero, Toska, Mustard-Okre non-saffron!)
    red_a, red_b = hex_rgb("#D6322C"), hex_rgb("#F7EDE0")
    teal_a, teal_b = hex_rgb("#1E9E9A"), hex_rgb("#F4ECE0")
    ochre_a, ochre_b = hex_rgb("#C98224"), hex_rgb("#F2E5CC")
    plum_a, plum_b = hex_rgb("#8F2E5A"), hex_rgb("#F5E8DC")

    # Hero Red Canopy ([CAM 07] Kunci memantul dari sini!)
    mb.add_market_canopy((0.0, 14.2, 10.8), 3.9, 3.2, 3.2, red_a, red_b, rot_deg=(0, 4, 0))
    # Deretan tenda untuk [CAM 08] Bima melompat + barrel roll!
    mb.add_market_canopy((-2.5, 14.2, 13.8), 3.2, 2.8, 2.9, teal_a, teal_b, rot_deg=(0, -6, 0))
    mb.add_market_canopy((2.4, 12.0, 15.2), 3.4, 3.0, 3.1, ochre_a, ochre_b, rot_deg=(0, 8, 0))
    mb.add_market_canopy((-2.6, 12.0, 18.0), 3.3, 2.9, 2.9, plum_a, plum_b, rot_deg=(0, -5, 0))
    mb.add_market_canopy((2.7, 12.0, 18.6), 3.0, 2.6, 2.8, teal_a, teal_b, rot_deg=(0, 5, 0))

    # Karung goni bubuk kunyit & cabai ([CAM 09]!)
    burlap = hex_rgb("#C4A77D")
    turmeric = hex_rgb("#F2B818")
    chili = hex_rgb("#D42A22")
    paprika = hex_rgb("#D95C1E")
    sacks = [
        (0.25, 12.45, 16.9, turmeric),
        (-0.55, 12.42, 17.3, chili),
        (0.95, 12.42, 17.5, paprika),
        (-1.25, 12.42, 16.5, turmeric),
        (1.55, 12.42, 16.4, chili),
    ]
    for sx, sy, sz, sp_col in sacks:
        mb.add_cylinder((sx, sy, sz), 0.36, 0.31, 0.78, burlap, MAT_FABRIC, segments=12)
        mb.add_sphere((sx, sy + 0.42, sz), 0.30, sp_col, MAT_FABRIC, seg_u=10, seg_v=6, scale=(1.0, 0.65, 1.0))

    # Peti buah warna-warni (jeruk, delima, semangka) + tumpahan jeruk di tangga ([CAM 10]!)
    orange = hex_rgb("#F28218")
    pomeg = hex_rgb("#B81D3A")
    melon = hex_rgb("#2E8540")
    mb.add_fruit_crate((-2.1, 14.2, 11.4), orange, rot_deg=(0, 15, 0), fruit_r=0.14)
    mb.add_fruit_crate((2.1, 14.2, 11.6), melon, rot_deg=(0, -12, 0), fruit_r=0.19)
    mb.add_fruit_crate((-1.8, 12.0, 15.6), pomeg, rot_deg=(0, 22, 0), fruit_r=0.13)
    mb.add_fruit_crate((2.2, 10.6, 20.6), orange, rot_deg=(24, -18, 15), fruit_r=0.14)
    mb.add_fruit_crate((-1.4, 8.8, 22.8), orange, rot_deg=(30, 28, -22), fruit_r=0.14)
    mb.add_fruit_crate((1.5, 7.1, 25.0), pomeg, rot_deg=(20, -25, 12), fruit_r=0.13)
    # Jeruk bergelinding tumpah di foreground tangga!
    for ox, oy, oz in [
        (0.8, 10.2, 21.4), (1.4, 9.6, 22.2), (0.2, 8.7, 23.4), (1.1, 8.0, 24.2),
        (-0.5, 7.2, 25.2), (0.9, 6.4, 26.2), (1.6, 5.7, 27.0), (-0.3, 5.4, 27.4),
    ]:
        mb.add_sphere((ox, oy, oz), 0.14, orange, MAT_PROP, seg_u=8, seg_v=6)

    # Timbangan besi klasik & sepeda tua penuh keranjang bunga
    mb.add_cylinder((-0.6, 12.2, 15.2), 0.22, 0.08, 0.55, hex_rgb("#2C323C"), MAT_OXIDIZED, segments=10)
    mb.add_box((-0.6, 12.48, 15.2), (0.85, 0.05, 0.05), hex_rgb("#D4A138"), MAT_BRASS)
    # Sepeda tua di sisi kiri bawah tangga
    bx, by, bz = -2.6, 5.45, 27.0
    mb.add_cylinder((bx, by, bz - 0.55), 0.42, 0.42, 0.08, hex_rgb("#262A32"), MAT_OXIDIZED, segments=14, rot_deg=(0, 0, 90))
    mb.add_cylinder((bx, by, bz + 0.55), 0.42, 0.42, 0.08, hex_rgb("#262A32"), MAT_OXIDIZED, segments=14, rot_deg=(0, 0, 90))
    mb.add_box((bx, by + 0.22, bz), (0.10, 0.45, 1.1), hex_rgb("#288A8E"), MAT_PROP)
    mb.add_box((bx, by + 0.62, bz + 0.52), (0.38, 0.30, 0.36), hex_rgb("#B5804A"), MAT_FABRIC)
    mb.add_sphere((bx, by + 0.84, bz + 0.52), 0.24, hex_rgb("#E83878"), MAT_PROP, seg_u=8, seg_v=6)


def _build_lokasi_3_gang_kafe(mb: MeshBuilder) -> None:
    """LOKASI 3: Gang Kafe & Jemuran Sempit (y=5.0, z=28.0..45.5)."""
    cobble = hex_rgb("#5A6272")
    # Jalan batu cobblestone basah sepanjang gang
    mb.add_box((0.0, 4.75, 36.8), (7.6, 0.5, 18.2), cobble, MAT_COBBLE)

    # Dinding gang sempit di kiri (x=-3.7) dan kanan (x=+3.7) agar cahaya matahari memotong seperti bilah pisau!
    alley_walls = [
        (-4.5, 10.0, 31.5, 2.0, 11.5, 7.2, "#D88563"),
        (-4.5, 10.6, 39.2, 2.0, 12.6, 8.6, "#698DA6"),
        (4.5, 10.2, 31.5, 2.0, 11.8, 7.2, "#DFC496"),
        (4.5, 10.5, 39.2, 2.0, 12.4, 8.6, "#C4635C"),
    ]
    for wx, wy, wz, ww, wh, wd, wcol in alley_walls:
        mb.add_box((wx, wy, wz), (ww, wh, wd), hex_rgb(wcol), MAT_PLASTER)
        # Jendela berdaun warna kontras di atas gang
        side_s = 1.0 if wx < 0 else -1.0
        for wy_win in (7.8, 10.8):
            mb.add_box((wx + side_s * 1.02, wy_win, wz), (0.14, 1.5, 1.15), hex_rgb("#2A6876"), MAT_WOOD)

    # Meja bistro besi biru langit + teko tembaga + kursi rotan (extreme FG parallax di [CAM 11]!)
    sky_blue = hex_rgb("#4298D8")
    mb.add_bistro_table((-1.9, 5.0, 30.8), sky_blue)
    mb.add_bistro_table((1.95, 5.0, 32.6), sky_blue)
    mb.add_bistro_table((-1.85, 5.0, 34.8), sky_blue)
    mb.add_bistro_table((2.0, 5.0, 37.8), sky_blue)

    # Pot terakota retak isi bunga bougenville magenta (termasuk pot tempat Oren muncul di [CAM 12]!)
    mb.add_potted_bougainvillea((-1.55, 5.0, 36.8))  # Hero pot di dekat Oren!
    mb.add_potted_bougainvillea((2.65, 5.0, 35.4))
    mb.add_potted_bougainvillea((-2.65, 5.0, 40.4))
    mb.add_potted_bougainvillea((2.55, 5.0, 41.2))

    # Kabel jemuran di atas gang penuh baju warna primer berkibar!
    shirt_colors = ["#E53935", "#1E88E5", "#FAFAFA", "#26A69A", "#E91E63", "#43A047"]
    for lz, ly in [(31.2, 8.9), (34.4, 9.2), (37.6, 8.7), (40.8, 9.1)]:
        mb.add_box((0.0, ly, lz), (7.2, 0.04, 0.04), hex_rgb("#26222E"), MAT_OXIDIZED)
        for si, sx in enumerate((-2.3, -1.1, 0.1, 1.3, 2.3)):
            scol = hex_rgb(shirt_colors[(si + int(lz)) % len(shirt_colors)])
            mb.add_box((sx, ly - 0.56, lz), (0.68, 0.95, 0.06), scol, MAT_FABRIC, rot_deg=(12.0, 0.0, (si - 2) * 3.0))

    # JERUJI SELOKAN BESI BERKARAT (z=42.5) — lubang gelap transisi [CAM 15]!
    gx, gy, gz = 0.0, 5.02, 42.5
    rust = hex_rgb("#5A3424")
    mb.add_box((gx, gy - 0.15, gz), (1.75, 0.25, 1.75), hex_rgb("#07060C"), MAT_EMISSIVE)  # lubang gelap
    mb.add_box((gx, gy, gz - 0.85), (1.95, 0.12, 0.18), rust, MAT_OXIDIZED)
    mb.add_box((gx, gy, gz + 0.85), (1.95, 0.12, 0.18), rust, MAT_OXIDIZED)
    mb.add_box((gx - 0.85, gy, gz), (0.18, 0.12, 1.95), rust, MAT_OXIDIZED)
    mb.add_box((gx + 0.85, gy, gz), (0.18, 0.12, 1.95), rust, MAT_OXIDIZED)
    for bi in range(-3, 4):
        mb.add_box((gx + bi * 0.24, gy + 0.02, gz), (0.065, 0.09, 1.68), rust, MAT_OXIDIZED)

    # Dinding penutup ujung gang di belakang selokan (z=45.5)
    mb.add_box((0.0, 10.0, 45.6), (9.5, 11.0, 0.8), hex_rgb("#685A56"), MAT_PLASTER)


def _build_lokasi_4_gorong_gorong(mb: MeshBuilder) -> None:
    """LOKASI 4: Gorong-Gorong Mesin Jam Kuno — THE STORY TURN! (y=-25..-5, z=33..64)."""
    vault_stone = hex_rgb("#262A44")
    copper_ox = hex_rgb("#356E62")
    rust = hex_rgb("#5E3A2B")
    valve_red = hex_rgb("#DE2E26")
    moss = hex_rgb("#267C52")
    furnace = hex_rgb("#FF661A")
    brass = hex_rgb("#C99224")

    # Ruang gua mesin raksasa (lantai, kubah atas, dinding samping & belakang)
    mb.add_box((0.0, -25.0, 45.5), (26.0, 1.0, 26.0), vault_stone, MAT_COBBLE)
    mb.add_box((0.0, -5.0, 45.5), (26.0, 1.0, 24.0), vault_stone, MAT_PLASTER)
    mb.add_box((-12.5, -15.0, 45.5), (1.2, 21.0, 26.0), vault_stone, MAT_PLASTER)
    mb.add_box((12.5, -15.0, 45.5), (1.2, 21.0, 26.0), vault_stone, MAT_PLASTER)
    mb.add_box((0.0, -15.0, 58.0), (26.0, 21.0, 1.2), vault_stone, MAT_PLASTER)
    mb.add_box((0.0, -15.0, 33.0), (26.0, 21.0, 1.2), vault_stone, MAT_PLASTER)

    # Pilar batu & lumut basah mengilap
    for px in (-8.2, 8.2):
        for pz in (38.0, 46.5, 54.0):
            mb.add_box((px, -15.0, pz), (1.8, 20.0, 1.8), vault_stone, MAT_PLASTER)
            mb.add_box((px, -23.6, pz), (2.2, 1.2, 2.2), moss, MAT_COBBLE)

    # Pipa tembaga hijau teroksidasi + katup tekanan merah cerah!
    for py_pipe in (-10.5, -14.2, -20.5):
        mb.add_cylinder((-9.8, py_pipe, 45.5), 0.55, 0.55, 22.0, copper_ox, MAT_OXIDIZED, segments=12, rot_deg=(90, 0, 0))
        mb.add_cylinder((9.8, py_pipe, 45.5), 0.55, 0.55, 22.0, copper_ox, MAT_OXIDIZED, segments=12, rot_deg=(90, 0, 0))
    for vx, vy, vz in [(-8.6, -14.2, 43.0), (8.6, -14.2, 44.5), (-4.6, -18.5, 45.2), (4.6, -18.5, 45.2)]:
        mb.add_cogwheel((vx, vy, vz), 0.72, 0.16, valve_red, teeth=8, mat_id=MAT_PROP, rot_deg=(0, 90 if abs(vx) > 6 else 0, 0))

    # Panel pengukur tekanan kaca retak & rantai besi gantung
    for gx, gy, gz in [(-5.4, -15.2, 44.0), (5.4, -15.2, 44.0)]:
        mb.add_cylinder((gx, gy, gz), 0.85, 0.85, 0.24, brass, MAT_BRASS, segments=14, rot_deg=(90, 0, 0))
        mb.add_cylinder((gx, gy, gz - 0.14), 0.68, 0.68, 0.06, hex_rgb("#E6F4EC"), MAT_GLASS, segments=14, rot_deg=(90, 0, 0))
        mb.add_box((gx + 0.12, gy + 0.15, gz - 0.19), (0.08, 0.52, 0.04), valve_red, MAT_PROP, rot_deg=(0, 0, -32))
    for cx, cz in [(-6.2, 40.5), (6.0, 41.2), (-3.8, 49.0), (4.2, 48.5)]:
        mb.add_cylinder((cx, -14.0, cz), 0.12, 0.12, 16.0, rust, MAT_OXIDIZED, segments=6)

    # TUNGKU INTI BERCAHAYA (Heart of the City Furnace Core di belakang poros utama!)
    mb.add_cylinder((0.0, -21.2, 49.5), 3.6, 2.8, 5.2, rust, MAT_OXIDIZED, segments=16)
    mb.add_sphere((0.0, -18.2, 49.5), 2.35, furnace, MAT_EMISSIVE, seg_u=14, seg_v=10)
    mb.add_box((0.0, -17.0, 44.6), (1.3, 1.3, 2.4), brass, MAT_BRASS)  # soket poros utama [CAM 18]!
    mb.add_cylinder((0.0, -17.0, 43.3), 0.42, 0.42, 0.35, hex_rgb("#14222E"), MAT_OXIDIZED, segments=12, rot_deg=(90, 0, 0))

    # CEROBONG VENTILASI VERTIKAL RAKSASA menuju Stasiun Trem di atas! (z=62, y=-18..+10)
    for ring_y in range(-16, 10, 3):
        mb.add_cogwheel((0.0, float(ring_y), 62.0), 4.6, 0.6, copper_ox, teeth=10, mat_id=MAT_OXIDIZED, rot_deg=(90, 0, ring_y * 12), hollow_ratio=0.72, spokes=0)
    # Pipa dinding silinder cerobong (open cylinder)
    mb.add_cylinder((0.0, -3.5, 62.0), 4.4, 4.4, 26.0, hex_rgb("#223A3E"), MAT_OXIDIZED, segments=14, capped=False)


def _build_lokasi_5_stasiun_trem(mb: MeshBuilder) -> None:
    """LOKASI 5: Stasiun Trem Layang Terbuka (y=10.0, z=58.0..112.0)."""
    timber = hex_rgb("#7A4E2A")
    timber_dark = hex_rgb("#4E3019")
    iron = hex_rgb("#26303E")
    mint = hex_rgb("#5AC4A8")
    ochre = hex_rgb("#C98E2E")  # non-saffron!
    steel = hex_rgb("#9AA6B6")

    # Dek peron kayu layang kiri & kanan + rel baja tengah di atas jembatan viaduct!
    mb.add_box((-4.4, 9.75, 85.0), (5.2, 0.55, 56.0), timber, MAT_WOOD)
    mb.add_box((4.4, 9.75, 85.0), (5.2, 0.55, 56.0), timber, MAT_WOOD)
    mb.add_box((0.0, 9.25, 85.0), (3.8, 0.65, 56.0), hex_rgb("#48464E"), MAT_COBBLE)  # track bed
    # Rel baja kembar + bantalan kayu
    mb.add_box((-0.92, 9.65, 85.0), (0.14, 0.16, 56.0), steel, MAT_BRASS)
    mb.add_box((0.92, 9.65, 85.0), (0.14, 0.16, 56.0), steel, MAT_BRASS)
    for tz in range(60, 112, 2):
        mb.add_box((0.0, 9.58, float(tz)), (2.5, 0.10, 0.28), timber_dark, MAT_WOOD)

    # Kisi ventilasi tempat Bima & kamera menjebol keluar ([CAM 20] di z=62!)
    mb.add_box((0.0, 9.68, 62.0), (2.2, 0.12, 2.2), hex_rgb("#1E3036"), MAT_OXIDIZED)

    # Pilar besi cor peron di foreground kiri & kanan (strong 3D parallax wall untuk [CAM 21]!)
    for pz in range(64, 110, 6):
        for px in (-2.55, 2.55):
            mb.add_cylinder((px, 12.6, float(pz)), 0.20, 0.16, 5.4, iron, MAT_OXIDIZED, segments=10)
            mb.add_box((px, 15.25, float(pz)), (0.65, 0.35, 0.65), hex_rgb("#D49E34"), MAT_BRASS)
        # Lampu gantung stasiun di atas peron
        mb.add_box((-4.4, 15.35, float(pz)), (4.4, 0.22, 6.2), hex_rgb("#354C56"), MAT_OXIDIZED, rot_deg=(0, 0, -8))
        mb.add_box((4.4, 15.35, float(pz)), (4.4, 0.22, 6.2), hex_rgb("#354C56"), MAT_OXIDIZED, rot_deg=(0, 0, 8))

    # Loket tiket warna mint & ochre + papan jadwal split-flap mekanik!
    mb.add_box((-5.2, 11.75, 74.0), (2.6, 3.5, 4.4), mint, MAT_PLASTER)
    mb.add_box((-5.2, 13.7, 74.0), (3.0, 0.45, 4.9), ochre, MAT_WOOD)
    mb.add_box((-3.85, 11.95, 74.0), (0.14, 1.35, 2.2), hex_rgb("#A8DDF0"), MAT_GLASS)
    # Papan jadwal split-flap mekanik di atas peron kiri (z=82)
    mb.add_box((-3.5, 13.6, 82.0), (0.32, 1.85, 3.8), hex_rgb("#1C202B"), MAT_OXIDIZED)
    for row in range(3):
        for col_i in range(6):
            mb.add_box((-3.30, 14.15 - row * 0.55, 80.6 + col_i * 0.55), (0.08, 0.38, 0.42), hex_rgb("#F4EAD6"), MAT_PROP)

    # Bangku besi cor, koper kulit warna-warni & balon melayang mundur!
    suit_cols = ["#9C2B3B", "#2A7A7E", "#8A542C", "#425B84"]
    for bi, bz in enumerate((69.0, 79.0, 89.0, 99.0)):
        mb.add_box((4.1, 10.45, bz), (0.75, 0.14, 2.4), timber, MAT_WOOD)
        mb.add_box((4.45, 10.95, bz), (0.12, 0.85, 2.4), iron, MAT_OXIDIZED)
        # Koper kulit warna-warni di peron (parallax foreground!)
        sc = hex_rgb(suit_cols[bi % len(suit_cols)])
        mb.add_box((-3.2, 10.45, bz + 1.4), (0.45, 0.72, 0.95), sc, MAT_PROP, rot_deg=(0, 18 * bi, 0))
        mb.add_box((3.2, 10.38, bz - 1.5), (0.40, 0.60, 0.82), hex_rgb(suit_cols[(bi + 2) % 4]), MAT_PROP, rot_deg=(0, -14, 0))

    # Balon warna-warni melayang miring mundur di udara stasiun
    for bx, by, bz, bcol in [
        (-3.6, 13.2, 71.0, "#E53935"),
        (3.4, 13.8, 77.5, "#1E88E5"),
        (-3.2, 12.8, 86.5, "#26A69A"),
        (3.6, 14.2, 95.0, "#D81B60"),
    ]:
        mb.add_sphere((bx, by, bz), 0.44, hex_rgb(bcol), MAT_PROP, seg_u=10, seg_v=8, scale=(0.9, 1.15, 0.9))
        mb.add_cylinder((bx, by - 0.95, bz + 0.3), 0.015, 0.015, 1.2, hex_rgb("#F0EAE0"), MAT_FABRIC, segments=6, rot_deg=(22, 0, 0))


def _build_lokasi_6_menara_jam(mb: MeshBuilder) -> None:
    """LOKASI 6: Wajah Menara Jam Utama di Dermaga (y=19.5, z=118.0) + Pelabuhan & Mercusuar Mini."""
    bronze = hex_rgb("#9E702B")
    gold = hex_rgb("#E5B432")
    tower_stone = hex_rgb("#5A566B")
    dial_glass = hex_rgb("#F6ECDA")
    copper = hex_rgb("#B86B38")
    water = hex_rgb("#1C486C")

    # Menara Jam Raksasa (berdiri dari dermaga y=0 sampai puncak lonceng y=34 di z=118..128)
    mb.add_box((0.0, 14.0, 122.5), (14.5, 29.0, 8.8), tower_stone, MAT_PLASTER)
    # Atap runcing menara & ruang lonceng tembaga raksasa di puncak
    mb.add_cylinder((0.0, 31.5, 122.5), 7.8, 1.2, 6.2, hex_rgb("#2C5E62"), MAT_OXIDIZED, segments=8)
    # Lonceng tembaga raksasa di atas wajah jam
    mb.add_cylinder((0.0, 27.6, 118.5), 1.65, 0.85, 2.2, copper, MAT_BRASS, segments=16)

    # WAJAH JAM RAKSASA (berpusat di (0, 19.5, 118.0), menghadap -Z!)
    cx, cy, cz = 0.0, 19.5, 118.0
    # Bingkai perunggu ukir luar (cincin bergerigi & bevel tebal)
    mb.add_cogwheel((cx, cy, cz), 6.8, 0.95, bronze, teeth=24, mat_id=MAT_BRASS, hollow_ratio=0.78, spokes=0)
    # Kaca jam raksasa berpendar lembut
    mb.add_cylinder((cx, cy, cz + 0.15), 5.65, 5.65, 0.25, dial_glass, MAT_GLASS, segments=32, rot_deg=(90, 0, 0))
    # 12 Angka Romawi emas 3D (batang penanda jam emas bervolume tebal)
    for h_i in range(12):
        ang = math.radians(h_i * 30.0)
        rx = cx + math.sin(ang) * 4.55
        ry = cy + math.cos(ang) * 4.55
        is_cardinal = (h_i % 3 == 0)
        mb.add_box(
            (rx, ry, cz - 0.18),
            (0.32 if is_cardinal else 0.18, 1.05 if is_cardinal else 0.72, 0.24),
            gold,
            MAT_BRASS,
            rot_deg=(0, 0, -h_i * 30.0),
        )
    # Lubang kunci pusat jam (pusat putaran jarum di (0, 19.5, 117.35) untuk [CAM 25]!)
    mb.add_cylinder((cx, cy, cz - 0.42), 0.72, 0.56, 0.55, gold, MAT_BRASS, segments=16, rot_deg=(90, 0, 0))
    mb.add_cylinder((cx, cy, cz - 0.72), 0.24, 0.24, 0.12, hex_rgb("#16121C"), MAT_OXIDIZED, segments=12, rot_deg=(90, 0, 0))
    # Balkon pijak sempit di bawah wajah jam (tempat Bima mendarat di [CAM 25]-[CAM 27]!)
    mb.add_box((0.0, 15.2, 116.8), (6.5, 0.45, 2.2), bronze, MAT_BRASS)

    # LAUT, PELABUHAN WARNA-WARNI & MERCUSUAR MINI jauh di bawah (latar megah [CAM 26]!)
    mb.add_box((0.0, 0.0, 115.0), (140.0, 0.4, 140.0), water, MAT_COBBLE)
    # Dermaga kayu & rumah pelabuhan warna-warni di kiri/kanan bawah
    mb.add_box((-18.0, 1.5, 112.0), (14.0, 2.2, 26.0), hex_rgb("#7A5230"), MAT_WOOD)
    mb.add_box((18.0, 1.5, 112.0), (14.0, 2.2, 26.0), hex_rgb("#7A5230"), MAT_WOOD)
    harbor_houses = [
        (-16.0, 4.8, 106.0, "#D95D4E"), (-20.0, 5.2, 112.0, "#2E8A94"), (-15.5, 4.4, 118.0, "#DFB86C"),
        (16.0, 4.6, 105.0, "#3A7A68"), (19.5, 5.5, 113.0, "#C94868"), (15.5, 4.8, 120.0, "#5B7CA6"),
    ]
    for hx, hy, hz, hcol in harbor_houses:
        mb.add_box((hx, hy, hz), (4.6, 5.2, 5.2), hex_rgb(hcol), MAT_PLASTER)
        mb.add_box((hx, hy + 3.0, hz), (5.0, 1.0, 5.6), hex_rgb("#8C3428"), MAT_PLASTER)
    # Mercusuar mini belang merah-putih di ujung dermaga kanan!
    lhx, lhz = 22.0, 96.0
    for li in range(5):
        col_lh = hex_rgb("#D83228") if (li % 2 == 0) else hex_rgb("#F7F3EA")
        mb.add_cylinder((lhx, 2.5 + li * 2.2, lhz), 1.6 - li * 0.14, 1.46 - li * 0.14, 2.2, col_lh, MAT_PLASTER, segments=14)
    mb.add_cylinder((lhx, 13.6, lhz), 0.85, 0.85, 1.5, hex_rgb("#FFF2A8"), MAT_EMISSIVE, segments=12)
    mb.add_cylinder((lhx, 14.9, lhz), 1.15, 0.08, 1.3, hex_rgb("#B82620"), MAT_OXIDIZED, segments=12)


def build_static_world() -> np.ndarray:
    """Bangun seluruh 6 lokasi 3D statis sekaligus dalam satu buffer mesh terpadu."""
    mb = MeshBuilder()
    _build_lokasi_1_bengkel(mb)
    _build_lokasi_2_pasar(mb)
    _build_lokasi_3_gang_kafe(mb)
    _build_lokasi_4_gorong_gorong(mb)
    _build_lokasi_5_stasiun_trem(mb)
    _build_lokasi_6_menara_jam(mb)
    return mb.build()


def build_dynamic_world(t: float) -> Tuple[np.ndarray, float]:
    """
    Bangun elemen 3D bergerak pada detik ke-t:
      - Lokasi 1: Dua roda gigi kuningan gantung di foreground ([CAM 01] heavy parallax!)
      - Lokasi 4: Roda gigi raksasa selebar rumah yang berputar maju -> BERHENTI (KLAK!) -> BERPUTAR MUNDUR!
      - Lokasi 5: Trem merah tua meluncur MUNDUR di atas rel + burung camar terbang mundur!
      - Lokasi 6: Jarum jam besi tempa raksasa berputar mundur -> DONG! -> normal + burung camar membeku lalu terbang!
      - Loop: Dua roda gigi gelap di bawah menara jam ([CAM 28] seamless loop -> [CAM 01]!)

    Mengembalikan (vertices_dynamic, tram_z_pos).
    """
    mb = MeshBuilder()
    brass = hex_rgb("#D6A028")
    brass_dark = hex_rgb("#8C6018")
    steel = hex_rgb("#5A687C")
    iron = hex_rgb("#222630")

    # 1. LOKASI 1: Dua roda gigi gantung di foreground loteng ([CAM 01] heavy 3D parallax!)
    if t < 11.0:
        g_spin = t * 24.0
        mb.add_cogwheel((-1.06, 27.08, -1.10), 0.87, 0.16, brass_dark, teeth=12, mat_id=MAT_BRASS, rot_deg=(0, 8, g_spin))
        mb.add_cogwheel((1.06, 27.26, -1.10), 0.87, 0.16, brass, teeth=12, mat_id=MAT_BRASS, rot_deg=(0, -8, -g_spin * 1.1 + 15.0))
        # Rantai penggantung kedua roda gigi
        mb.add_cylinder((-1.06, 29.2, -1.10), 0.04, 0.04, 2.8, iron, MAT_OXIDIZED, segments=6)
        mb.add_cylinder((1.06, 29.3, -1.10), 0.04, 0.04, 2.8, iron, MAT_OXIDIZED, segments=6)

    # 2. LOKASI 4: Roda gigi raksasa selebar rumah (berhenti di t=31.9s -> berputar MUNDUR di t>32.3s!)
    if 25.0 <= t <= 39.5:
        if t < 31.9:
            gear_ang = (t - 26.0) * 18.0
        elif t < 32.35:
            # Bergetar/macet sejenak saat KLAK!
            gear_ang = (31.9 - 26.0) * 18.0 + math.sin((t - 31.9) * 70.0) * 1.8
        else:
            # Berputar MUNDUR cepat!
            dt_rev = t - 32.35
            gear_ang = (31.9 - 26.0) * 18.0 - (dt_rev ** 1.45) * 68.0

        mb.add_cogwheel((-4.2, -16.5, 45.2), 4.2, 0.72, steel, teeth=16, mat_id=MAT_OXIDIZED, rot_deg=(0, 0, gear_ang))
        mb.add_cogwheel((4.4, -15.8, 45.5), 4.4, 0.76, brass_dark, teeth=16, mat_id=MAT_BRASS, rot_deg=(0, 0, -gear_ang * 0.95 + 11.0))
        mb.add_cogwheel((0.0, -11.2, 48.2), 5.6, 0.85, steel, teeth=20, mat_id=MAT_OXIDIZED, rot_deg=(0, 0, gear_ang * 0.75))
        mb.add_cogwheel((-6.5, -20.5, 42.0), 3.1, 0.55, brass, teeth=14, mat_id=MAT_BRASS, rot_deg=(0, 0, -gear_ang * 1.25))
        mb.add_cogwheel((6.2, -20.8, 41.8), 3.2, 0.55, steel, teeth=14, mat_id=MAT_OXIDIZED, rot_deg=(0, 0, gear_ang * 1.2))

    # 3. LOKASI 5: Trem merah tua meluncur MUNDUR (dari z=104 mundur menuju z=70, lalu tetap terlihat di rel!)
    # Saat [CAM 21]-[CAM 24] (38..50s), trem meluncur mundur di sumbu Z (-Z) sambil Bima berlari maju (+Z) di atapnya!
    tram_z = 96.0
    if t >= 37.5:
        if t < 51.8:
            # Meluncur mundur konstan di rel; melambat 20% saat slow-mo apex leap [CAM 24] (46.2..49.0s)
            if t < 46.2:
                tram_z = 104.0 - (t - 38.0) * 1.65
            else:
                base_z = 104.0 - (46.2 - 38.0) * 1.65
                tram_z = base_z - (t - 46.2) * 0.35
        else:
            # Setelah waktu kembali normal (51.8s), trem bergerak maju lagi!
            base_z = 104.0 - (46.2 - 38.0) * 1.65 - (51.8 - 46.2) * 0.35
            tram_z = base_z + (t - 51.8) * 1.9
        mb.add_vintage_tram((0.0, 9.65, tram_z), rot_deg=(0.0, 0.0, 0.0))

        # Burung camar terbang mundur di Stasiun Trem (Lokasi 5)
        if t < 50.0:
            for bi in range(6):
                bx = -5.5 + (bi % 3) * 5.4 + math.sin(bi * 2.1) * 1.2
                by = 14.5 + (bi // 3) * 2.4 + math.sin(t * 2.5 + bi) * 0.4
                bz = 98.0 - (t - 38.0) * 2.6 - bi * 3.8
                flap = math.sin(-t * 9.0 + bi) * 28.0
                # Menghadap +Z tapi melaju ke -Z (terbang mundur!)
                mb.add_seagull((bx, by, bz), rot_deg=(0.0, 0.0, 0.0), wing_deg=flap, scale=1.1)

    # 4. LOKASI 6: Jarum jam besi tempa raksasa + puluhan burung camar membeku lalu bergerak normal!
    if t >= 46.0:
        cx, cy, cz = 0.0, 19.5, 117.6
        if t < 51.8:
            # Berputar mundur kencang sebelum kunci menancap!
            min_ang = (t - 46.0) * 115.0
            hr_ang = 35.0 + (t - 46.0) * 16.0
        else:
            # DONG! Kembali normal berputar lambat searah jarum jam
            snap_min = (51.8 - 46.0) * 115.0
            snap_hr = 35.0 + (51.8 - 46.0) * 16.0
            min_ang = snap_min - (t - 51.8) * 6.0
            hr_ang = snap_hr - (t - 51.8) * 0.8

        # Jarum menit setinggi pohon (panjang 4.6m)
        m_rad = math.radians(min_ang)
        mb.add_box(
            (cx - math.sin(m_rad) * 2.1, cy + math.cos(m_rad) * 2.1, cz),
            (0.28, 4.4, 0.16),
            iron,
            MAT_OXIDIZED,
            rot_deg=(0, 0, min_ang),
        )
        # Jarum jam (panjang 3.2m)
        h_rad = math.radians(hr_ang)
        mb.add_box(
            (cx - math.sin(h_rad) * 1.4, cy + math.cos(h_rad) * 1.4, cz - 0.18),
            (0.38, 3.0, 0.16),
            iron,
            MAT_OXIDIZED,
            rot_deg=(0, 0, hr_ang),
        )

        # Puluhan burung camar di sekitar wajah jam: MEMBEKU di udara (<51.8s) -> TERBANG NORMAL (>=51.8s)!
        for gi in range(12):
            ang_g = gi * 0.55
            rad_g = 7.2 + (gi % 3) * 3.0
            if t < 51.8:
                fly_t = 0.0
                flap_g = 24.0 * math.sin(gi * 1.7)
            else:
                fly_t = t - 51.8
                flap_g = math.sin(fly_t * 10.0 + gi) * 32.0
            gx = math.cos(ang_g + fly_t * 0.35) * rad_g
            gy = 17.5 + (gi % 4) * 2.3 + math.sin(fly_t * 2.2 + gi) * 0.8
            gz = 111.5 - (gi % 3) * 3.2 + math.sin(ang_g + fly_t * 0.35) * 4.5
            mb.add_seagull((gx, gy, gz), rot_deg=(0.0, math.degrees(ang_g + fly_t * 0.35) + 90.0, 0.0), wing_deg=flap_g, scale=1.25)

        # Twin dark foreground gears di bawah/celah menara jam ([CAM 28] seamless loop -> [CAM 01]!)
        loop_spin = t * 24.0
        mb.add_cogwheel((-1.15, 13.0, 117.0), 1.05, 0.18, brass_dark, teeth=12, mat_id=MAT_BRASS, rot_deg=(0, 8, loop_spin))
        mb.add_cogwheel((1.15, 13.2, 117.0), 1.05, 0.18, brass, teeth=12, mat_id=MAT_BRASS, rot_deg=(0, -8, -loop_spin * 1.1 + 15.0))

    return mb.build(), tram_z
