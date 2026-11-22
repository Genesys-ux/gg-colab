"""
Procedural 3D Mesh Builder (12 floats/vertex: pos3, normal3, uv2, color3, mat_id1).

Material IDs (ditafsirkan langsung oleh procedural PBR + Cel-Shade WGSL fragment shader):
  0.0 = Cracked Oak Wood (serat kayu, sambungan papan, retak halus)
  1.0 = Peeling Plaster / Painted Wall / Stone (cat terkelupas & tekstur batu)
  2.0 = Scratched Brass / Antique Gold Metal (goresan mikro & pita specular tajam)
  3.0 = Coarse Woven Fabric / Awning / Burlap (anyaman kain kasar)
  4.0 = Dusty Glass / Clock Dial (kilau kaca Fresnel + debu halus)
  5.0 = Wet Cobblestone / Masonry (batu jalan basah memantulkan langit)
  6.0 = Oxidized Copper / Rusted Iron (patina hijau verdigris & karat)
  7.0 = Emissive Core / Furnace / Lamp / Spark (bercahaya penuh, bebas bayangan)
  8.0 = Painted Vibrant Prop / Fruit / Ceramic (cel-shade cerah dgn highlight halus)
"""

from __future__ import annotations

import math
from typing import List, Sequence, Tuple

import numpy as np

from .math3d import mat4_trs

MAT_WOOD = 0.0
MAT_PLASTER = 1.0
MAT_BRASS = 2.0
MAT_FABRIC = 3.0
MAT_GLASS = 4.0
MAT_COBBLE = 5.0
MAT_OXIDIZED = 6.0
MAT_EMISSIVE = 7.0
MAT_PROP = 8.0


def hex_rgb(h: str) -> Tuple[float, float, float]:
    s = h.lstrip("#")
    return (int(s[0:2], 16) / 255.0, int(s[2:4], 16) / 255.0, int(s[4:6], 16) / 255.0)


class MeshBuilder:
    """Mengumpulkan ribuan segitiga 3D berwarna menjadi satu array NumPy siap upload ke WGPU."""

    def __init__(self) -> None:
        self._chunks: List[np.ndarray] = []

    def add_triangles(
        self,
        positions: np.ndarray,
        normals: np.ndarray,
        uvs: np.ndarray,
        color: Tuple[float, float, float],
        mat_id: float,
        transform: np.ndarray | None = None,
    ) -> None:
        n = positions.shape[0]
        if n == 0:
            return
        pos = positions.astype(np.float32)
        nrm = normals.astype(np.float32)
        if transform is not None:
            rot3 = transform[:3, :3]
            pos = (pos @ rot3.T) + transform[:3, 3]
            # Normal matrix (inverse transpose of upper 3x3 for non-uniform scale safety)
            try:
                nmat = np.linalg.inv(rot3).T.astype(np.float32)
            except np.linalg.LinAlgError:
                nmat = rot3
            nrm = nrm @ nmat.T
            lens = np.linalg.norm(nrm, axis=1, keepdims=True)
            nrm = nrm / np.maximum(lens, 1e-6)

        v = np.empty((n, 12), dtype=np.float32)
        v[:, 0:3] = pos
        v[:, 3:6] = nrm
        v[:, 6:8] = uvs.astype(np.float32)
        v[:, 8] = color[0]
        v[:, 9] = color[1]
        v[:, 10] = color[2]
        v[:, 11] = float(mat_id)
        self._chunks.append(v)

    def build(self) -> np.ndarray:
        if not self._chunks:
            return np.zeros((0, 12), dtype=np.float32)
        return np.ascontiguousarray(np.vstack(self._chunks), dtype=np.float32)

    def add_box(
        self,
        pos: Sequence[float],
        size: Sequence[float],
        color: Tuple[float, float, float],
        mat_id: float = MAT_PROP,
        rot_deg: Sequence[float] = (0.0, 0.0, 0.0),
    ) -> None:
        sx, sy, sz = float(size[0]) * 0.5, float(size[1]) * 0.5, float(size[2]) * 0.5
        faces = [
            # (+Z)
            ([(-sx, -sy, sz), (sx, -sy, sz), (sx, sy, sz), (-sx, sy, sz)], (0, 0, 1), (size[0], size[1])),
            # (-Z)
            ([(sx, -sy, -sz), (-sx, -sy, -sz), (-sx, sy, -sz), (sx, sy, -sz)], (0, 0, -1), (size[0], size[1])),
            # (+X)
            ([(sx, -sy, sz), (sx, -sy, -sz), (sx, sy, -sz), (sx, sy, sz)], (1, 0, 0), (size[2], size[1])),
            # (-X)
            ([(-sx, -sy, -sz), (-sx, -sy, sz), (-sx, sy, sz), (-sx, sy, -sz)], (-1, 0, 0), (size[2], size[1])),
            # (+Y)
            ([(-sx, sy, sz), (sx, sy, sz), (sx, sy, -sz), (-sx, sy, -sz)], (0, 1, 0), (size[0], size[2])),
            # (-Y)
            ([(-sx, -sy, -sz), (sx, -sy, -sz), (sx, -sy, sz), (-sx, -sy, sz)], (0, -1, 0), (size[0], size[2])),
        ]
        p_list, n_list, u_list = [], [], []
        for quad, nrm, (uw, uh) in faces:
            q0, q1, q2, q3 = quad
            p_list.extend([q0, q1, q2, q0, q2, q3])
            n_list.extend([nrm] * 6)
            u_list.extend([(0, 0), (uw, 0), (uw, uh), (0, 0), (uw, uh), (0, uh)])
        tr = mat4_trs(pos=pos, rot_deg=rot_deg)
        self.add_triangles(
            np.array(p_list, dtype=np.float32),
            np.array(n_list, dtype=np.float32),
            np.array(u_list, dtype=np.float32),
            color,
            mat_id,
            tr,
        )

    def add_cylinder(
        self,
        pos: Sequence[float],
        r_bot: float,
        r_top: float,
        height: float,
        color: Tuple[float, float, float],
        mat_id: float = MAT_PROP,
        segments: int = 16,
        rot_deg: Sequence[float] = (0.0, 0.0, 0.0),
        capped: bool = True,
    ) -> None:
        h2 = height * 0.5
        p_list, n_list, u_list = [], [], []
        slope = (r_bot - r_top) / max(1e-5, height)
        for i in range(segments):
            a0 = (2.0 * math.pi * i) / segments
            a1 = (2.0 * math.pi * (i + 1)) / segments
            c0, s0 = math.cos(a0), math.sin(a0)
            c1, s1 = math.cos(a1), math.sin(a1)
            b0 = (c0 * r_bot, -h2, s0 * r_bot)
            b1 = (c1 * r_bot, -h2, s1 * r_bot)
            t0 = (c0 * r_top, h2, s0 * r_top)
            t1 = (c1 * r_top, h2, s1 * r_top)
            n0 = (c0, slope, s0)
            n1 = (c1, slope, s1)
            u0, u1 = i / segments * 2.0, (i + 1) / segments * 2.0
            # Side quad (CCW outward)
            p_list.extend([b0, t0, t1, b0, t1, b1])
            n_list.extend([n0, n0, n1, n0, n1, n1])
            u_list.extend([(u0, 0), (u0, height), (u1, height), (u0, 0), (u1, height), (u1, 0)])
            if capped:
                if r_top > 1e-4:
                    p_list.extend([(0, h2, 0), t1, t0])
                    n_list.extend([(0, 1, 0)] * 3)
                    u_list.extend([(0.5, 0.5), (c1 * 0.5 + 0.5, s1 * 0.5 + 0.5), (c0 * 0.5 + 0.5, s0 * 0.5 + 0.5)])
                if r_bot > 1e-4:
                    p_list.extend([(0, -h2, 0), b0, b1])
                    n_list.extend([(0, -1, 0)] * 3)
                    u_list.extend([(0.5, 0.5), (c0 * 0.5 + 0.5, s0 * 0.5 + 0.5), (c1 * 0.5 + 0.5, s1 * 0.5 + 0.5)])
        tr = mat4_trs(pos=pos, rot_deg=rot_deg)
        self.add_triangles(
            np.array(p_list, dtype=np.float32),
            np.array(n_list, dtype=np.float32),
            np.array(u_list, dtype=np.float32),
            color,
            mat_id,
            tr,
        )

    def add_sphere(
        self,
        pos: Sequence[float],
        radius: float,
        color: Tuple[float, float, float],
        mat_id: float = MAT_PROP,
        seg_u: int = 14,
        seg_v: int = 10,
        scale: Sequence[float] = (1.0, 1.0, 1.0),
    ) -> None:
        p_list, n_list, u_list = [], [], []
        for iv in range(seg_v):
            v0 = math.pi * iv / seg_v
            v1 = math.pi * (iv + 1) / seg_v
            sv0, cv0 = math.sin(v0), math.cos(v0)
            sv1, cv1 = math.sin(v1), math.cos(v1)
            for iu in range(seg_u):
                u0 = 2.0 * math.pi * iu / seg_u
                u1 = 2.0 * math.pi * (iu + 1) / seg_u
                cu0, su0 = math.cos(u0), math.sin(u0)
                cu1, su1 = math.cos(u1), math.sin(u1)

                n00 = (sv0 * cu0, cv0, sv0 * su0)
                n10 = (sv0 * cu1, cv0, sv0 * su1)
                n01 = (sv1 * cu0, cv1, sv1 * su0)
                n11 = (sv1 * cu1, cv1, sv1 * su1)

                p00 = (n00[0] * radius, n00[1] * radius, n00[2] * radius)
                p10 = (n10[0] * radius, n10[1] * radius, n10[2] * radius)
                p01 = (n01[0] * radius, n01[1] * radius, n01[2] * radius)
                p11 = (n11[0] * radius, n11[1] * radius, n11[2] * radius)

                p_list.extend([p00, p10, p11, p00, p11, p01])
                n_list.extend([n00, n10, n11, n00, n11, n01])
                u_list.extend([(iu / seg_u, iv / seg_v)] * 6)
        tr = mat4_trs(pos=pos, scale=scale)
        self.add_triangles(
            np.array(p_list, dtype=np.float32),
            np.array(n_list, dtype=np.float32),
            np.array(u_list, dtype=np.float32),
            color,
            mat_id,
            tr,
        )

    def add_cogwheel(
        self,
        pos: Sequence[float],
        outer_r: float,
        thickness: float,
        color: Tuple[float, float, float],
        teeth: int = 12,
        mat_id: float = MAT_BRASS,
        rot_deg: Sequence[float] = (0.0, 0.0, 0.0),
        hollow_ratio: float = 0.42,
        spokes: int = 4,
    ) -> None:
        """Roda gigi 3D berongga (cincin luar + gigi + jari-jari + hub tengah)."""
        tr = mat4_trs(pos=pos, rot_deg=rot_deg)
        t2 = thickness * 0.5
        rim_in = outer_r * max(0.30, min(0.76, hollow_ratio + 0.16))
        rim_out = outer_r * 0.84
        hub_r = outer_r * max(0.14, hollow_ratio * 0.45)

        p_list, n_list, u_list = [], [], []
        segs = max(teeth * 2, 16)
        # Cincin roda gigi (ring depan, belakang, dinding luar & dalam)
        for i in range(segs):
            a0 = (2.0 * math.pi * i) / segs
            a1 = (2.0 * math.pi * (i + 1)) / segs
            c0, s0 = math.cos(a0), math.sin(a0)
            c1, s1 = math.cos(a1), math.sin(a1)
            # Front ring (+Z)
            o0f, o1f = (c0 * rim_out, s0 * rim_out, t2), (c1 * rim_out, s1 * rim_out, t2)
            i0f, i1f = (c0 * rim_in, s0 * rim_in, t2), (c1 * rim_in, s1 * rim_in, t2)
            p_list.extend([i0f, o0f, o1f, i0f, o1f, i1f])
            n_list.extend([(0, 0, 1)] * 6)
            u_list.extend([(c0, s0), (c0 * 1.4, s0 * 1.4), (c1 * 1.4, s1 * 1.4), (c0, s0), (c1 * 1.4, s1 * 1.4), (c1, s1)])
            # Back ring (-Z)
            o0b, o1b = (c0 * rim_out, s0 * rim_out, -t2), (c1 * rim_out, s1 * rim_out, -t2)
            i0b, i1b = (c0 * rim_in, s0 * rim_in, -t2), (c1 * rim_in, s1 * rim_in, -t2)
            p_list.extend([i0b, o1b, o0b, i0b, i1b, o1b])
            n_list.extend([(0, 0, -1)] * 6)
            u_list.extend([(c0, s0)] * 6)
            # Outer wall
            p_list.extend([o0b, o1b, o1f, o0b, o1f, o0f])
            n_list.extend([(c0, s0, 0), (c1, s1, 0), (c1, s1, 0), (c0, s0, 0), (c1, s1, 0), (c0, s0, 0)])
            u_list.extend([(i / segs, 0), ((i + 1) / segs, 0), ((i + 1) / segs, 1), (i / segs, 0), ((i + 1) / segs, 1), (i / segs, 1)])
            # Inner wall
            p_list.extend([i0f, i1f, i1b, i0f, i1b, i0b])
            n_list.extend([(-c0, -s0, 0), (-c1, -s1, 0), (-c1, -s1, 0), (-c0, -s0, 0), (-c1, -s1, 0), (-c0, -s0, 0)])
            u_list.extend([(i / segs, 0)] * 6)

        self.add_triangles(
            np.array(p_list, dtype=np.float32),
            np.array(n_list, dtype=np.float32),
            np.array(u_list, dtype=np.float32),
            color,
            mat_id,
            tr,
        )

        # Gigi roda di sekeliling cincin
        tooth_w = (2.0 * math.pi * rim_out) / (teeth * 2.15)
        tooth_h = outer_r - rim_out + outer_r * 0.04
        for i in range(teeth):
            ang_deg = (360.0 * i) / teeth
            a = math.radians(ang_deg)
            r_mid = rim_out + tooth_h * 0.36
            local_tr = tr @ mat4_trs(pos=(math.cos(a) * r_mid, math.sin(a) * r_mid, 0.0), rot_deg=(0.0, 0.0, ang_deg))
            # Tambahkan kotak gigi dalam ruang lokal roda gigi
            self._add_box_with_tr((tooth_h, tooth_w, thickness * 0.96), color, mat_id, local_tr)

        # Jari-jari & hub tengah
        spoke_w = max(0.05, outer_r * 0.11)
        for i in range(spokes):
            ang_deg = (180.0 * i) / max(1, spokes)
            local_tr = tr @ mat4_trs(rot_deg=(0.0, 0.0, ang_deg))
            self._add_box_with_tr((rim_in * 2.04, spoke_w, thickness * 0.72), color, mat_id, local_tr)

        hub_tr = tr @ mat4_trs(rot_deg=(90.0, 0.0, 0.0))
        self._add_cyl_with_tr(hub_r, hub_r, thickness * 1.35, color, mat_id, 12, hub_tr)

    def _add_box_with_tr(
        self,
        size: Sequence[float],
        color: Tuple[float, float, float],
        mat_id: float,
        tr: np.ndarray,
    ) -> None:
        sx, sy, sz = float(size[0]) * 0.5, float(size[1]) * 0.5, float(size[2]) * 0.5
        faces = [
            ([(-sx, -sy, sz), (sx, -sy, sz), (sx, sy, sz), (-sx, sy, sz)], (0, 0, 1)),
            ([(sx, -sy, -sz), (-sx, -sy, -sz), (-sx, sy, -sz), (sx, sy, -sz)], (0, 0, -1)),
            ([(sx, -sy, sz), (sx, -sy, -sz), (sx, sy, -sz), (sx, sy, sz)], (1, 0, 0)),
            ([(-sx, -sy, -sz), (-sx, -sy, sz), (-sx, sy, sz), (-sx, sy, -sz)], (-1, 0, 0)),
            ([(-sx, sy, sz), (sx, sy, sz), (sx, sy, -sz), (-sx, sy, -sz)], (0, 1, 0)),
            ([(-sx, -sy, -sz), (sx, -sy, -sz), (sx, -sy, sz), (-sx, -sy, sz)], (0, -1, 0)),
        ]
        p_list, n_list, u_list = [], [], []
        for (q0, q1, q2, q3), nrm in faces:
            p_list.extend([q0, q1, q2, q0, q2, q3])
            n_list.extend([nrm] * 6)
            u_list.extend([(0, 0), (1, 0), (1, 1), (0, 0), (1, 1), (0, 1)])
        self.add_triangles(
            np.array(p_list, dtype=np.float32),
            np.array(n_list, dtype=np.float32),
            np.array(u_list, dtype=np.float32),
            color,
            mat_id,
            tr,
        )

    def _add_cyl_with_tr(
        self,
        r_bot: float,
        r_top: float,
        height: float,
        color: Tuple[float, float, float],
        mat_id: float,
        segments: int,
        tr: np.ndarray,
    ) -> None:
        h2 = height * 0.5
        p_list, n_list, u_list = [], [], []
        for i in range(segments):
            a0, a1 = (2.0 * math.pi * i) / segments, (2.0 * math.pi * (i + 1)) / segments
            c0, s0, c1, s1 = math.cos(a0), math.sin(a0), math.cos(a1), math.sin(a1)
            b0, b1 = (c0 * r_bot, -h2, s0 * r_bot), (c1 * r_bot, -h2, s1 * r_bot)
            t0, t1 = (c0 * r_top, h2, s0 * r_top), (c1 * r_top, h2, s1 * r_top)
            p_list.extend([b0, t0, t1, b0, t1, b1, (0, h2, 0), t1, t0, (0, -h2, 0), b0, b1])
            n_list.extend([(c0, 0, s0), (c0, 0, s0), (c1, 0, s1), (c0, 0, s0), (c1, 0, s1), (c1, 0, s1), (0, 1, 0), (0, 1, 0), (0, 1, 0), (0, -1, 0), (0, -1, 0), (0, -1, 0)])
            u_list.extend([(i / segments, 0)] * 12)
        self.add_triangles(
            np.array(p_list, dtype=np.float32),
            np.array(n_list, dtype=np.float32),
            np.array(u_list, dtype=np.float32),
            color,
            mat_id,
            tr,
        )

    def add_market_canopy(
        self,
        pos: Sequence[float],
        width: float,
        depth: float,
        height: float,
        color_a: Tuple[float, float, float],
        color_b: Tuple[float, float, float],
        rot_deg: Sequence[float] = (0.0, 0.0, 0.0),
    ) -> None:
        """Tenda pasar kain tenun bergaris warna-warni (merah / toska / mustard-okre) + tiang kayu."""
        tr = mat4_trs(pos=pos, rot_deg=rot_deg)
        wood = hex_rgb("#6E4728")
        # 4 tiang penyangga kayu
        for sx in (-width * 0.45, width * 0.45):
            for sz in (-depth * 0.44, depth * 0.44):
                p_tr = tr @ mat4_trs(pos=(sx, height * 0.5, sz))
                self._add_cyl_with_tr(0.08, 0.07, height, wood, MAT_WOOD, 8, p_tr)
        # Strip kain atap miring bergaris
        stripes = 6
        sw = width / stripes
        for i in range(stripes):
            cx = -width * 0.5 + (i + 0.5) * sw
            col = color_a if (i % 2 == 0) else color_b
            roof_tr = tr @ mat4_trs(pos=(cx, height + 0.14, 0.0), rot_deg=(12.0, 0.0, 0.0))
            self._add_box_with_tr((sw * 1.01, 0.09, depth * 1.08), col, MAT_FABRIC, roof_tr)
            # Valance depan menjuntai
            val_tr = tr @ mat4_trs(pos=(cx, height - 0.14, depth * 0.53))
            self._add_box_with_tr((sw * 0.96, 0.34, 0.06), col, MAT_FABRIC, val_tr)

    def add_fruit_crate(
        self,
        pos: Sequence[float],
        fruit_color: Tuple[float, float, float],
        rot_deg: Sequence[float] = (0.0, 0.0, 0.0),
        fruit_r: float = 0.15,
    ) -> None:
        """Peti kayu pasar penuh buah 3D warna cerah (jeruk, delima, semangka)."""
        tr = mat4_trs(pos=pos, rot_deg=rot_deg)
        wood = hex_rgb("#9B6B3E")
        dark_w = hex_rgb("#6B4624")
        # Dinding peti
        self._add_box_with_tr((1.1, 0.1, 0.78), dark_w, MAT_WOOD, tr @ mat4_trs(pos=(0, 0.05, 0)))
        self._add_box_with_tr((1.1, 0.52, 0.08), wood, MAT_WOOD, tr @ mat4_trs(pos=(0, 0.26, 0.36)))
        self._add_box_with_tr((1.1, 0.52, 0.08), wood, MAT_WOOD, tr @ mat4_trs(pos=(0, 0.26, -0.36)))
        self._add_box_with_tr((0.08, 0.52, 0.76), wood, MAT_WOOD, tr @ mat4_trs(pos=(-0.52, 0.26, 0)))
        self._add_box_with_tr((0.08, 0.52, 0.76), wood, MAT_WOOD, tr @ mat4_trs(pos=(0.52, 0.26, 0)))
        # Tumpukan buah 3D
        for ix in (-0.32, 0.0, 0.32):
            for iz in (-0.16, 0.16):
                p_world = (tr @ np.array([ix, 0.52, iz, 1.0], dtype=np.float32))[:3]
                self.add_sphere(p_world, fruit_r, fruit_color, MAT_PROP, seg_u=10, seg_v=8)
        for ix in (-0.16, 0.16):
            p_world = (tr @ np.array([ix, 0.52 + fruit_r * 1.15, 0.0, 1.0], dtype=np.float32))[:3]
            self.add_sphere(p_world, fruit_r, fruit_color, MAT_PROP, seg_u=10, seg_v=8)

    def add_bistro_table(
        self,
        pos: Sequence[float],
        table_color: Tuple[float, float, float] = (0.32, 0.66, 0.88),
    ) -> None:
        """Meja bistro besi biru langit + teko kopi tembaga + kursi rotan (Lokasi 3)."""
        px, py, pz = float(pos[0]), float(pos[1]), float(pos[2])
        iron = hex_rgb("#263547")
        rattan = hex_rgb("#C99658")
        copper = hex_rgb("#C86D38")
        # Meja bistro
        self.add_cylinder((px, py + 0.86, pz), 0.58, 0.58, 0.06, table_color, MAT_PROP, segments=16)
        self.add_cylinder((px, py + 0.43, pz), 0.06, 0.05, 0.86, iron, MAT_OXIDIZED, segments=10)
        self.add_cylinder((px, py + 0.04, pz), 0.34, 0.14, 0.08, iron, MAT_OXIDIZED, segments=12)
        # Teko kopi tembaga di atas meja
        self.add_cylinder((px + 0.12, py + 1.04, pz - 0.08), 0.11, 0.075, 0.28, copper, MAT_BRASS, segments=12)
        self.add_sphere((px + 0.12, py + 1.20, pz - 0.08), 0.05, copper, MAT_BRASS, seg_u=8, seg_v=6)
        # Cangkir kopi putih
        self.add_cylinder((px - 0.18, py + 0.95, pz + 0.12), 0.065, 0.075, 0.11, hex_rgb("#F7F3EA"), MAT_PROP, segments=10)
        # 2 kursi rotan mengapit meja
        for side in (-1.0, 1.0):
            cx = px + side * 0.92
            self.add_cylinder((cx, py + 0.50, pz), 0.28, 0.28, 0.07, rattan, MAT_FABRIC, segments=12)
            self.add_box((cx + side * 0.24, py + 0.82, pz), (0.07, 0.56, 0.46), rattan, MAT_FABRIC)
            for lx in (-0.18, 0.18):
                for lz in (-0.18, 0.18):
                    self.add_cylinder((cx + lx, py + 0.25, pz + lz), 0.028, 0.028, 0.50, iron, MAT_OXIDIZED, segments=6)

    def add_potted_bougainvillea(self, pos: Sequence[float]) -> None:
        """Pot terakota retak berisi bunga bougenville magenta menyala (Lokasi 3)."""
        px, py, pz = float(pos[0]), float(pos[1]), float(pos[2])
        terra = hex_rgb("#C45D3A")
        leaf = hex_rgb("#2C6E42")
        magenta = hex_rgb("#D8267E")
        self.add_cylinder((px, py + 0.34, pz), 0.24, 0.34, 0.68, terra, MAT_PLASTER, segments=12)
        self.add_cylinder((px, py + 0.66, pz), 0.37, 0.37, 0.10, terra, MAT_PLASTER, segments=12)
        self.add_sphere((px, py + 0.94, pz), 0.44, leaf, MAT_FABRIC, seg_u=10, seg_v=8, scale=(1.1, 0.85, 1.1))
        for bx, by, bz in [(-0.26, 1.12, 0.18), (0.24, 1.22, -0.10), (0.0, 1.32, 0.22), (0.28, 0.98, 0.24), (-0.18, 1.24, -0.22)]:
            self.add_sphere((px + bx, py + by, pz + bz), 0.20, magenta, MAT_PROP, seg_u=8, seg_v=6)

    def add_vintage_tram(
        self,
        pos: Sequence[float],
        rot_deg: Sequence[float] = (0.0, 0.0, 0.0),
    ) -> None:
        """Trem merah tua bertekstur cat tergores (Lokasi 5 — meluncur mundur di atas rel baja!)."""
        tr = mat4_trs(pos=pos, rot_deg=rot_deg)
        red = hex_rgb("#A82328")
        red_dark = hex_rgb("#6D151B")
        cream = hex_rgb("#EFE2C6")
        brass = hex_rgb("#D4A138")
        roof = hex_rgb("#484E5A")
        glass = hex_rgb("#6EB5D9")
        iron = hex_rgb("#262B35")

        # Badan bawah merah tua (panjang 11.5m di sumbu Z, lebar 2.8m di X)
        self._add_box_with_tr((2.75, 1.45, 11.4), red, MAT_PLASTER, tr @ mat4_trs(pos=(0, 1.38, 0)))
        # Sabuk bumper kuningan & besi bawah
        self._add_box_with_tr((2.86, 0.22, 11.6), red_dark, MAT_OXIDIZED, tr @ mat4_trs(pos=(0, 0.72, 0)))
        self._add_box_with_tr((2.82, 0.12, 11.46), brass, MAT_BRASS, tr @ mat4_trs(pos=(0, 2.12, 0)))
        # Sabuk jendela krem
        self._add_box_with_tr((2.68, 1.15, 11.1), cream, MAT_PLASTER, tr @ mat4_trs(pos=(0, 2.72, 0)))
        # Kaca jendela samping & depan/belakang
        self._add_box_with_tr((2.74, 0.84, 9.8), glass, MAT_GLASS, tr @ mat4_trs(pos=(0, 2.75, 0)))
        self._add_box_with_tr((2.15, 0.86, 11.18), glass, MAT_GLASS, tr @ mat4_trs(pos=(0, 2.75, 0)))
        # Pilar jendela vertikal
        for iz in (-4.4, -2.6, -0.8, 1.0, 2.8, 4.4):
            self._add_box_with_tr((2.80, 1.18, 0.22), cream, MAT_WOOD, tr @ mat4_trs(pos=(0, 2.72, iz)))
        # Atap melengkung & dek lari Bima di atap trem!
        self._add_box_with_tr((2.86, 0.26, 11.6), roof, MAT_OXIDIZED, tr @ mat4_trs(pos=(0, 3.42, 0)))
        self._add_box_with_tr((2.15, 0.22, 9.6), hex_rgb("#5A3E2A"), MAT_WOOD, tr @ mat4_trs(pos=(0, 3.62, 0)))
        # Pantograf listrik atas
        self._add_box_with_tr((1.35, 0.12, 0.14), brass, MAT_BRASS, tr @ mat4_trs(pos=(0, 4.45, -2.2)))
        self._add_box_with_tr((0.12, 0.90, 0.12), iron, MAT_OXIDIZED, tr @ mat4_trs(pos=(-0.5, 4.02, -2.2), rot_deg=(18, 0, 0)))
        self._add_box_with_tr((0.12, 0.90, 0.12), iron, MAT_OXIDIZED, tr @ mat4_trs(pos=(0.5, 4.02, -2.2), rot_deg=(18, 0, 0)))
        # Lampu depan kuningan menyala di kedua ujung trem
        for z_end in (-5.78, 5.78):
            self._add_cyl_with_tr(0.28, 0.28, 0.18, brass, MAT_BRASS, 12, tr @ mat4_trs(pos=(0, 1.48, z_end), rot_deg=(90, 0, 0)))
            self._add_cyl_with_tr(0.21, 0.21, 0.20, hex_rgb("#FFF3B0"), MAT_EMISSIVE, 12, tr @ mat4_trs(pos=(0, 1.48, z_end), rot_deg=(90, 0, 0)))
        # Roda baja bogie
        for wz in (-3.8, -2.4, 2.4, 3.8):
            for wx in (-1.22, 1.22):
                self._add_cyl_with_tr(0.46, 0.46, 0.18, iron, MAT_OXIDIZED, 12, tr @ mat4_trs(pos=(wx, 0.46, wz), rot_deg=(0, 0, 90)))

    def add_seagull(
        self,
        pos: Sequence[float],
        rot_deg: Sequence[float] = (0.0, 0.0, 0.0),
        wing_deg: float = 18.0,
        scale: float = 1.0,
    ) -> None:
        """Burung camar 3D stylized (terbang mundur di Lokasi 5 & membeku lalu hidup kembali di Lokasi 6!)."""
        tr = mat4_trs(pos=pos, rot_deg=rot_deg, scale=(scale, scale, scale))
        white = hex_rgb("#F6F4EE")
        wing_tip = hex_rgb("#3C4A5E")
        beak = hex_rgb("#E88B28")
        # Badan + kepala + paruh
        self._add_box_with_tr((0.24, 0.20, 0.62), white, MAT_PROP, tr)
        self._add_box_with_tr((0.10, 0.08, 0.22), beak, MAT_PROP, tr @ mat4_trs(pos=(0, 0.02, 0.38)))
        # Sayap kiri & kanan terentang
        for side in (-1.0, 1.0):
            w_tr = tr @ mat4_trs(pos=(side * 0.42, 0.08, 0.0), rot_deg=(0.0, 0.0, side * wing_deg))
            self._add_box_with_tr((0.76, 0.05, 0.26), white, MAT_PROP, w_tr)
            wt_tr = w_tr @ mat4_trs(pos=(side * 0.48, -0.04, -0.02), rot_deg=(0.0, 0.0, -side * 16.0))
            self._add_box_with_tr((0.32, 0.045, 0.20), wing_tip, MAT_PROP, wt_tr)
