"""
Pembangun Geometri 3D Halus & Berdetail Tinggi (bmesh + Bevel + Subdivision Surface + Lathe + Inverted-Hull Ink)
untuk Blender 4.2+ EEVEE Next.

Dirancang khusus agar TIDAK ADA lagi bentuk kotak kaku atau permukaan kasar:
  - Setiap balok arsitektur & kayu memiliki Bevel halus penangkap specular highlight
  - Cangkir teh, toples pegas, karung rempah, pot terakota, & lonceng dibuat dengan Lathe (revolve organik)
  - Kanopi pasar melengkung menggembung (catenary drape) + scalloped valance + Wave breeze
  - Roda gigi memiliki gigi bevel, ring berongga, jari-jari, & hub bervolume
  - Trem vintage memiliki atap lengkung, jendela cekung berkaca, lampu depan bulat, & pantograf kuningan
"""

from __future__ import annotations

import math
from typing import Iterable, List, Optional, Sequence, Tuple

import bmesh  # type: ignore
import bpy  # type: ignore
from mathutils import Euler, Matrix, Vector  # type: ignore


def get_or_create_collection(name: str, parent=None):
    col = bpy.data.collections.get(name)
    if col is None:
        col = bpy.data.collections.new(name)
        target = parent if parent is not None else bpy.context.scene.collection
        target.children.link(col)
    return col


def link_object(obj, collection) -> None:
    for c in list(obj.users_collection):
        c.objects.unlink(obj)
    collection.objects.link(obj)


def set_smooth(obj) -> None:
    """Smooth shading aman untuk Blender 4.1 / 4.2+ (tanpa API use_auto_smooth yang sudah dihapus)."""
    mesh = obj.data
    if hasattr(mesh, "polygons") and len(mesh.polygons) > 0:
        mesh.polygons.foreach_set("use_smooth", [True] * len(mesh.polygons))
        mesh.update()


def assign_material(obj, mat, ink_mat=None, outline_thickness: float = 0.0) -> None:
    """Pasang material utama + opsional Inverted-Hull Dark Ink Outline (Solidify backface culling)."""
    obj.data.materials.clear()
    obj.data.materials.append(mat)
    if ink_mat is not None and outline_thickness > 0.0:
        obj.data.materials.append(ink_mat)
        mod = obj.modifiers.new(name="InkOutline", type="SOLIDIFY")
        mod.thickness = -abs(outline_thickness)
        mod.offset = -1.0
        mod.use_flip_normals = True
        mod.use_rim = False
        mod.material_offset = 1


def add_bevel(obj, width: float = 0.025, segments: int = 3) -> None:
    mod = obj.modifiers.new(name="Bevel", type="BEVEL")
    mod.width = width
    mod.segments = segments
    mod.limit_method = "ANGLE"
    mod.angle_limit = math.radians(32.0)


def add_subsurf(obj, levels: int = 2, render_levels: Optional[int] = None) -> None:
    mod = obj.modifiers.new(name="Subsurf", type="SUBSURF")
    mod.levels = levels
    mod.render_levels = render_levels if render_levels is not None else levels


def create_mesh_object(
    name: str,
    bm: "bmesh.types.BMesh",
    collection,
    location=(0.0, 0.0, 0.0),
    rotation_deg=(0.0, 0.0, 0.0),
    scale=(1.0, 1.0, 1.0),
    mat=None,
    ink_mat=None,
    outline_thickness: float = 0.0,
    bevel_width: float = 0.0,
    subsurf_levels: int = 0,
    smooth: bool = True,
):
    mesh = bpy.data.meshes.new(name)
    bm.normal_update()
    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new(name, mesh)
    obj.location = Vector(location)
    obj.rotation_euler = Euler(tuple(math.radians(a) for a in rotation_deg), "XYZ")
    obj.scale = Vector(scale)
    link_object(obj, collection)

    if smooth:
        set_smooth(obj)
    if bevel_width > 0.0:
        add_bevel(obj, width=bevel_width, segments=3)
    if subsurf_levels > 0:
        add_subsurf(obj, levels=subsurf_levels)
    if mat is not None:
        assign_material(obj, mat, ink_mat=ink_mat, outline_thickness=outline_thickness)
    return obj


def make_beveled_box(
    name: str,
    size: Tuple[float, float, float],
    location: Tuple[float, float, float],
    collection,
    mat,
    rotation_deg=(0.0, 0.0, 0.0),
    bevel_width: float = 0.03,
    ink_mat=None,
    outline_thickness: float = 0.0,
):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    sx, sy, sz = size
    for v in bm.verts:
        v.co.x *= sx
        v.co.y *= sy
        v.co.z *= sz
    bw = min(bevel_width, min(sx, sy, sz) * 0.22)
    return create_mesh_object(
        name, bm, collection, location, rotation_deg, (1, 1, 1),
        mat=mat, ink_mat=ink_mat, outline_thickness=outline_thickness,
        bevel_width=bw, smooth=True,
    )


def make_smooth_cylinder(
    name: str,
    radius1: float,
    radius2: float,
    depth: float,
    location: Tuple[float, float, float],
    collection,
    mat,
    segments: int = 24,
    rotation_deg=(0.0, 0.0, 0.0),
    cap_ends: bool = True,
    bevel_width: float = 0.012,
    ink_mat=None,
    outline_thickness: float = 0.0,
):
    bm = bmesh.new()
    bmesh.ops.create_cone(
        bm,
        cap_ends=cap_ends,
        cap_tris=False,
        segments=segments,
        radius1=radius1,
        radius2=radius2,
        depth=depth,
    )
    bw = min(bevel_width, min(max(radius1, radius2), depth) * 0.18) if cap_ends else 0.0
    return create_mesh_object(
        name, bm, collection, location, rotation_deg, (1, 1, 1),
        mat=mat, ink_mat=ink_mat, outline_thickness=outline_thickness,
        bevel_width=bw, smooth=True,
    )


def make_smooth_sphere(
    name: str,
    radius: float,
    location: Tuple[float, float, float],
    collection,
    mat,
    scale=(1.0, 1.0, 1.0),
    rotation_deg=(0.0, 0.0, 0.0),
    subdivisions: int = 3,
    ink_mat=None,
    outline_thickness: float = 0.0,
):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=subdivisions, radius=radius)
    return create_mesh_object(
        name, bm, collection, location, rotation_deg, scale,
        mat=mat, ink_mat=ink_mat, outline_thickness=outline_thickness,
        smooth=True,
    )


def make_lathe_mesh(
    name: str,
    profile_rz: Sequence[Tuple[float, float]],
    location: Tuple[float, float, float],
    collection,
    mat,
    segments: int = 28,
    rotation_deg=(0.0, 0.0, 0.0),
    scale=(1.0, 1.0, 1.0),
    cap_bottom: bool = True,
    cap_top: bool = False,
    subsurf_levels: int = 1,
    ink_mat=None,
    outline_thickness: float = 0.0,
):
    """
    Buat mesh 3D organik melingkar (Lathe / Revolve) dari daftar titik (radius, z).
    Ideal untuk cangkir teh porselen, karung goni bulat terikat, toples kaca, pot terakota, & lonceng!
    """
    bm = bmesh.new()
    rings: List[List["bmesh.types.BMVert"]] = []
    for r, z in profile_rz:
        ring = []
        rr = max(0.001, float(r))
        for si in range(segments):
            ang = (2.0 * math.pi * si) / segments
            v = bm.verts.new((math.cos(ang) * rr, math.sin(ang) * rr, float(z)))
            ring.append(v)
        rings.append(ring)

    for ri in range(len(rings) - 1):
        r0, r1 = rings[ri], rings[ri + 1]
        for si in range(segments):
            sn = (si + 1) % segments
            try:
                bm.faces.new((r0[si], r0[sn], r1[sn], r1[si]))
            except ValueError:
                pass

    if cap_bottom and rings:
        try:
            bm.faces.new(list(reversed(rings[0])))
        except ValueError:
            pass
    if cap_top and rings:
        try:
            bm.faces.new(rings[-1])
        except ValueError:
            pass

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return create_mesh_object(
        name, bm, collection, location, rotation_deg, scale,
        mat=mat, ink_mat=ink_mat, outline_thickness=outline_thickness,
        subsurf_levels=subsurf_levels, smooth=True,
    )


def make_helix_spring(
    name: str,
    radius: float,
    wire_r: float,
    height: float,
    turns: float,
    location: Tuple[float, float, float],
    collection,
    mat,
):
    """Pegas spiral 3D asli di dalam toples kaca bengkel jam!"""
    curve_data = bpy.data.curves.new(name=name + "_Curve", type="CURVE")
    curve_data.dimensions = "3D"
    curve_data.bevel_depth = wire_r
    curve_data.bevel_resolution = 4
    spline = curve_data.splines.new("POLY")
    steps = max(16, int(turns * 14))
    spline.points.add(steps - 1)
    for i in range(steps):
        u = i / float(steps - 1)
        ang = u * turns * 2.0 * math.pi
        spline.points[i].co = (math.cos(ang) * radius, math.sin(ang) * radius, (u - 0.5) * height, 1.0)
    obj = bpy.data.objects.new(name, curve_data)
    obj.location = Vector(location)
    link_object(obj, collection)
    obj.data.materials.append(mat)
    return obj


def make_cogwheel_3d(
    name: str,
    outer_r: float,
    thickness: float,
    teeth: int,
    location: Tuple[float, float, float],
    collection,
    mat,
    rotation_deg=(0.0, 0.0, 0.0),
    hollow_ratio: float = 0.62,
    spokes: int = 6,
    ink_mat=None,
    outline_thickness: float = 0.0,
):
    """
    Roda gigi kuningan / baja 3D ber-bevel halus:
      - Cincin berongga dengan profil gigi trapesium presisi
      - Jari-jari bervolume & hub poros tengah
      - Sumbu putar lokal = sumbu Y (menghadap kamera sepanjang jalan Y) jika rot=(0,0,0) atau Z-axis
        Default dibangun di bidang X-Z (sumbu putar lokal = Y) agar cocok dengan dinding & menara jam!
    """
    bm = bmesh.new()
    inner_r = outer_r * hollow_ratio
    root_r = outer_r * 0.87
    ht = thickness * 0.5
    segs = max(teeth * 4, 24)

    # 1. Cincin bergerigi berongga (sumbu Y adalah ketebalan, bidang X-Z adalah wajah roda gigi!)
    ring_out_f, ring_out_b = [], []
    ring_in_f, ring_in_b = [], []
    for i in range(segs):
        ang = (2.0 * math.pi * i) / segs
        phase = (i % 4)
        # Profil gigi trapesium yang rapi
        r_cur = outer_r if phase in (1, 2) else root_r
        cx, cz = math.cos(ang), math.sin(ang)
        ring_out_f.append(bm.verts.new((cx * r_cur, -ht, cz * r_cur)))
        ring_out_b.append(bm.verts.new((cx * r_cur, +ht, cz * r_cur)))
        ring_in_f.append(bm.verts.new((cx * inner_r, -ht, cz * inner_r)))
        ring_in_b.append(bm.verts.new((cx * inner_r, +ht, cz * inner_r)))

    for i in range(segs):
        j = (i + 1) % segs
        bm.faces.new((ring_in_f[i], ring_out_f[i], ring_out_f[j], ring_in_f[j]))
        bm.faces.new((ring_in_b[j], ring_out_b[j], ring_out_b[i], ring_in_b[i]))
        bm.faces.new((ring_out_f[i], ring_out_b[i], ring_out_b[j], ring_out_f[j]))
        bm.faces.new((ring_in_b[i], ring_in_f[i], ring_in_f[j], ring_in_b[j]))

    # 2. Hub tengah + jari-jari bervolume jika spokes > 0
    if spokes > 0:
        hub_r = outer_r * 0.22
        hub_ret = bmesh.ops.create_cone(
            bm, cap_ends=True, cap_tris=False, segments=18,
            radius1=hub_r, radius2=hub_r, depth=thickness * 1.32,
            matrix=Matrix.Rotation(math.radians(90.0), 4, "X"),
        )
        _ = hub_ret
        spoke_len = inner_r - hub_r * 0.75
        spoke_w = max(0.04, outer_r * 0.085)
        for si in range(spokes):
            ang = (2.0 * math.pi * si) / spokes
            mid_r = hub_r * 0.7 + spoke_len * 0.5
            mat_s = (
                Matrix.Translation((math.cos(ang) * mid_r, 0.0, math.sin(ang) * mid_r))
                @ Matrix.Rotation(-ang, 4, "Y")
                @ Matrix.Scale(spoke_len * 1.06, 4, Vector((1, 0, 0)))
                @ Matrix.Scale(thickness * 0.72, 4, Vector((0, 1, 0)))
                @ Matrix.Scale(spoke_w, 4, Vector((0, 0, 1)))
            )
            bmesh.ops.create_cube(bm, size=1.0, matrix=mat_s)

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return create_mesh_object(
        name, bm, collection, location, rotation_deg, (1, 1, 1),
        mat=mat, ink_mat=ink_mat, outline_thickness=outline_thickness,
        bevel_width=min(0.018, thickness * 0.14), smooth=True,
    )


def make_draped_canopy_3d(
    name: str,
    width: float,
    depth: float,
    height: float,
    location: Tuple[float, float, float],
    collection,
    mat_a,
    mat_b,
    mat_wood,
    ink_mat=None,
    rotation_deg=(0.0, 0.0, 0.0),
    stripes: int = 8,
):
    """
    Kanopi tenda pasar kain melengkung organik (catenary sag + pinggiran gelombang scalloped + Wave breeze),
    duduk di atas tiang kayu oak bundar — jauh lebih hidup daripada papan datar!
    """
    parent = bpy.data.objects.new(name, None)
    parent.location = Vector(location)
    parent.rotation_euler = Euler(tuple(math.radians(a) for a in rotation_deg), "XYZ")
    link_object(parent, collection)

    # 4 Tiang kayu bundar + palang atap
    for px in (-width * 0.46, width * 0.46):
        for py in (-depth * 0.44, depth * 0.44):
            post = make_smooth_cylinder(
                f"{name}_Post_{px:.1f}_{py:.1f}", 0.075, 0.065, height,
                (px, py, height * 0.5), collection, mat_wood, segments=12, bevel_width=0.01,
            )
            post.parent = parent

    # Kain kanopi bergaris melengkung lembut dengan kerutan elastis (subdivided grid + catenary curve)
    stripe_w = width / float(stripes)
    for si in range(stripes):
        bm = bmesh.new()
        nx, ny = 3, 10
        x0 = -width * 0.5 + si * stripe_w
        grid = []
        for iy in range(ny + 1):
            v_y = iy / float(ny)
            row = []
            for ix in range(nx + 1):
                u_x = ix / float(nx)
                px = x0 + u_x * stripe_w
                # Kemiringan atap tenda + lengkung kendur kain alami (catenary sag)
                py = -depth * 0.52 + v_y * depth * 1.04
                slope_z = height + (1.0 - v_y) * 0.48 - math.sin(v_y * math.pi) * 0.14
                # Sedikit gembung di tengah tiap strip kain
                puff = math.sin(u_x * math.pi) * 0.035
                row.append(bm.verts.new((px, py, slope_z + puff)))
            grid.append(row)

        # Rumbai depan menggantung (scalloped valance)
        val_row = []
        for ix in range(nx + 1):
            u_x = ix / float(nx)
            px = x0 + u_x * stripe_w
            scallop = 0.28 + math.sin(u_x * math.pi) * 0.12
            val_row.append(bm.verts.new((px, depth * 0.52, height - scallop)))
        grid.append(val_row)

        for iy in range(len(grid) - 1):
            for ix in range(nx):
                bm.faces.new((grid[iy][ix], grid[iy][ix + 1], grid[iy + 1][ix + 1], grid[iy + 1][ix]))

        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        strip_obj = create_mesh_object(
            f"{name}_Stripe_{si}", bm, collection, (0, 0, 0),
            mat=mat_a if (si % 2 == 0) else mat_b,
            subsurf_levels=1, smooth=True,
        )
        # Solidify ketebalan kain dulu, BARU tambahkan InkOutline & Wave breeze!
        sol = strip_obj.modifiers.new(name="FabricThick", type="SOLIDIFY")
        sol.thickness = 0.028
        if ink_mat is not None:
            assign_material(strip_obj, mat_a if (si % 2 == 0) else mat_b, ink_mat=ink_mat, outline_thickness=0.012)
        wave = strip_obj.modifiers.new(name="BreezeWave", type="WAVE")
        wave.height = 0.04
        wave.width = 1.6
        wave.speed = 0.12
        wave.use_x = False
        wave.use_y = True
        strip_obj.parent = parent

    return parent


def make_spice_sack_3d(
    name: str,
    location: Tuple[float, float, float],
    collection,
    mat_burlap,
    mat_spice,
    mat_rope,
    ink_mat=None,
    scale: float = 1.0,
):
    """Karung goni organik gendut dengan leher terikat tali & gundukan bubuk rempah meluber!"""
    parent = bpy.data.objects.new(name, None)
    parent.location = Vector(location)
    parent.scale = Vector((scale, scale, scale))
    link_object(parent, collection)

    # Profil karung goni gendut melengkung + bibir terlipat keluar
    profile = [
        (0.28, 0.00), (0.38, 0.08), (0.43, 0.24), (0.42, 0.46),
        (0.35, 0.66), (0.29, 0.76), (0.34, 0.84), (0.31, 0.87), (0.27, 0.78),
    ]
    sack = make_lathe_mesh(
        f"{name}_Burlap", profile, (0, 0, 0), collection, mat_burlap,
        segments=24, cap_bottom=True, cap_top=False, subsurf_levels=1,
        ink_mat=ink_mat, outline_thickness=0.014,
    )
    sack.parent = parent

    # Tali rami pengikat leher karung
    bm_t = bmesh.new()
    segs_u, segs_v = 20, 8
    r_maj, r_min = 0.305, 0.025
    rings = []
    for iu in range(segs_u):
        au = 2.0 * math.pi * iu / segs_u
        cu, su = math.cos(au), math.sin(au)
        ring = []
        for iv in range(segs_v):
            av = 2.0 * math.pi * iv / segs_v
            rr = r_maj + math.cos(av) * r_min
            ring.append(bm_t.verts.new((cu * rr, su * rr, 0.75 + math.sin(av) * r_min)))
        rings.append(ring)
    for iu in range(segs_u):
        inext = (iu + 1) % segs_u
        for iv in range(segs_v):
            jnext = (iv + 1) % segs_v
            bm_t.faces.new((rings[iu][iv], rings[inext][iv], rings[inext][jnext], rings[iu][jnext]))
    rope = create_mesh_object(f"{name}_Rope", bm_t, collection, (0, 0, 0), mat=mat_rope, smooth=True)
    rope.parent = parent

    # Gundukan bubuk kunyit / cabai membulat di atas mulut karung
    mound = make_smooth_sphere(
        f"{name}_SpiceMound", 0.31, (0.0, 0.0, 0.82), collection, mat_spice,
        scale=(1.0, 1.0, 0.62), subdivisions=3, ink_mat=ink_mat, outline_thickness=0.010,
    )
    mound.parent = parent
    return parent


def make_teacup_and_saucer_3d(
    name: str,
    location: Tuple[float, float, float],
    collection,
    mat_porcelain,
    mat_tea,
    mat_rim,
    ink_mat=None,
):
    """Cangkir teh porselen klasik + tatakan + isi teh + pegangan lengkung (Hero Prop [CAM 03]!)."""
    parent = bpy.data.objects.new(name, None)
    parent.location = Vector(location)
    link_object(parent, collection)

    saucer_prof = [(0.11, 0.00), (0.16, 0.012), (0.25, 0.042), (0.265, 0.048), (0.24, 0.052), (0.13, 0.025)]
    saucer = make_lathe_mesh(
        f"{name}_Saucer", saucer_prof, (0, 0, 0), collection, mat_porcelain,
        segments=32, cap_bottom=True, cap_top=True, subsurf_levels=1,
        ink_mat=ink_mat, outline_thickness=0.007,
    )
    saucer.parent = parent

    cup_prof = [
        (0.095, 0.032), (0.125, 0.06), (0.155, 0.14), (0.172, 0.23), (0.184, 0.265),
        (0.172, 0.268), (0.156, 0.225), (0.138, 0.135), (0.105, 0.055),
    ]
    cup = make_lathe_mesh(
        f"{name}_Cup", cup_prof, (0, 0, 0), collection, mat_porcelain,
        segments=32, cap_bottom=True, cap_top=False, subsurf_levels=1,
        ink_mat=ink_mat, outline_thickness=0.008,
    )
    cup.parent = parent

    tea = make_smooth_cylinder(
        f"{name}_Tea", 0.156, 0.156, 0.015, (0, 0, 0.215), collection, mat_tea, segments=28, bevel_width=0.003,
    )
    tea.parent = parent

    # Pegangan cangkir melengkung C-shape (curve bevel 3D!)
    c_data = bpy.data.curves.new(f"{name}_HandleCurve", type="CURVE")
    c_data.dimensions = "3D"
    c_data.bevel_depth = 0.018
    c_data.bevel_resolution = 6
    sp = c_data.splines.new("BEZIER")
    pts = [(0.165, 0.0, 0.22), (0.255, 0.0, 0.21), (0.245, 0.0, 0.11), (0.135, 0.0, 0.09)]
    sp.bezier_points.add(len(pts) - 1)
    for i, p in enumerate(pts):
        bp = sp.bezier_points[i]
        bp.co = Vector(p)
        bp.handle_left_type = "AUTO"
        bp.handle_right_type = "AUTO"
    handle = bpy.data.objects.new(f"{name}_Handle", c_data)
    link_object(handle, collection)
    handle.data.materials.append(mat_rim)
    handle.parent = parent
    return parent


def _make_leaf_or_bract_bm(bm: "bmesh.types.BMesh", center: Vector, dir_vec: Vector, length: float, width: float, cup: float = 0.15) -> None:
    """Tambahkan 1 helai daun ovate runcing / bract kertas bougainvillea melengkung ke BMesh."""
    d = dir_vec.normalized() if dir_vec.length > 1e-4 else Vector((0, 1, 0))
    up_ref = Vector((0, 0, 1)) if abs(d.z) < 0.92 else Vector((1, 0, 0))
    side = d.cross(up_ref).normalized()
    nrm = side.cross(d).normalized()

    p_base = center
    p_mid_l = center + d * (length * 0.45) - side * (width * 0.5) + nrm * (length * cup)
    p_mid_c = center + d * (length * 0.52) - nrm * (length * cup * 0.35)
    p_mid_r = center + d * (length * 0.45) + side * (width * 0.5) + nrm * (length * cup)
    p_tip = center + d * length + nrm * (length * cup * 0.4)

    v0 = bm.verts.new(p_base)
    v1 = bm.verts.new(p_mid_l)
    v2 = bm.verts.new(p_mid_c)
    v3 = bm.verts.new(p_mid_r)
    v4 = bm.verts.new(p_tip)
    bm.faces.new((v0, v1, v4, v2))
    bm.faces.new((v0, v2, v4, v3))


def make_potted_bougainvillea_3d(
    name: str,
    location: Tuple[float, float, float],
    collection,
    mat_pot,
    mat_leaf,
    mat_flower,
    ink_mat=None,
    scale: float = 1.0,
    mat_bark=None,
    mat_soil=None,
    mat_cream=None,
):
    """
    Tanaman Bougainvillea BOTANIS NYATA (berdasarkan referensi botani Bougainvillea):
      - Pot terakota beralur + bibir gulung + tanah pot gelap
      - 5 batang kayu melengkung menjuntai (woody arched canes via 3D Bezier curves)
      - Puluhan helai daun ovate runcing berselang-seling (alternate ovate leaves — BUKAN bola!)
      - Gugusan terminal triad 3 bract kertas magenta berbentuk hati + bunga tabung krem mini di tengah!
    """
    parent = bpy.data.objects.new(name, None)
    parent.location = Vector(location)
    parent.scale = Vector((scale, scale, scale))
    link_object(parent, collection)

    # 1. Pot Terakota Mediterania klasik dengan bibir tebal berganda & tanah pot
    pot_prof = [
        (0.22, 0.00), (0.25, 0.05), (0.30, 0.36), (0.33, 0.50),
        (0.37, 0.53), (0.375, 0.62), (0.35, 0.64), (0.31, 0.62), (0.28, 0.50),
    ]
    pot = make_lathe_mesh(
        f"{name}_TerracottaPot", pot_prof, (0, 0, 0), collection, mat_pot,
        segments=28, cap_bottom=True, cap_top=False, subsurf_levels=1,
        ink_mat=ink_mat, outline_thickness=0.011,
    )
    pot.parent = parent

    soil = make_smooth_cylinder(
        f"{name}_Soil", 0.295, 0.295, 0.04, (0, 0, 0.54), collection,
        mat_soil or mat_pot, segments=20, bevel_width=0.006,
    )
    soil.parent = parent

    # 2. 5 Batang Kayu Bougainvillea Melengkung (arching woody canes) + Daun Ovate + Triad Bracts Magenta!
    bm_leaves = bmesh.new()
    bm_bracts = bmesh.new()
    bm_flowers = bmesh.new()

    cane_specs = [
        (0.0, 0.85, 0.42),
        (1.25, 0.92, 0.48),
        (2.45, 0.78, 0.45),
        (3.85, 0.88, 0.50),
        (5.10, 0.72, 0.44),
    ]
    for ci, (az, height_c, reach_c) in enumerate(cane_specs):
        ca, sa = math.cos(az), math.sin(az)
        # Buat kurva batang berkayu melengkung organik
        c_data = bpy.data.curves.new(f"{name}_CaneCurve_{ci}", type="CURVE")
        c_data.dimensions = "3D"
        c_data.bevel_depth = 0.016
        c_data.bevel_resolution = 4
        sp = c_data.splines.new("BEZIER")
        pts = [
            Vector((ca * 0.04, sa * 0.04, 0.54)),
            Vector((ca * (reach_c * 0.35), sa * (reach_c * 0.35), 0.54 + height_c * 0.58)),
            Vector((ca * (reach_c * 0.82), sa * (reach_c * 0.82), 0.54 + height_c * 0.96)),
            Vector((ca * reach_c * 1.12, sa * reach_c * 1.12, 0.54 + height_c * 0.72)),
        ]
        sp.bezier_points.add(len(pts) - 1)
        for pi, p in enumerate(pts):
            bp = sp.bezier_points[pi]
            bp.co = p
            bp.radius = 1.0 - pi * 0.24
            bp.handle_left_type = "AUTO"
            bp.handle_right_type = "AUTO"
        cane_obj = bpy.data.objects.new(f"{name}_Cane_{ci}", c_data)
        link_object(cane_obj, collection)
        cane_obj.data.materials.append(mat_bark or mat_pot)
        cane_obj.parent = parent

        # Distribusikan daun ovate berselang-seling sepanjang batang + gugusan triad 3 bract di ujung!
        for li in range(8):
            u = 0.25 + (li / 8.0) * 0.72
            # Interpolasi kurva kubik sederhana di sepanjang 4 titik
            p01 = pts[0].lerp(pts[1], u)
            p12 = pts[1].lerp(pts[2], u)
            p23 = pts[2].lerp(pts[3], u)
            pos_l = p01.lerp(p12, u).lerp(p12.lerp(p23, u), u)

            side_sign = 1.0 if (li % 2 == 0) else -1.0
            perp = Vector((-sa * side_sign, ca * side_sign, 0.32))
            leaf_dir = (Vector((ca * 0.6, sa * 0.6, 0.35)) + perp * 0.75).normalized()
            _make_leaf_or_bract_bm(bm_leaves, pos_l, leaf_dir, length=0.145, width=0.082, cup=0.14)

            # Gugusan bunga terminal (3 papery magenta bracts + bunga tabung krem) di paruh atas cabang!
            if u > 0.52:
                for bi in range(3):
                    bang = az + li * 0.9 + bi * (2.0 * math.pi / 3.0)
                    bdir = Vector((math.cos(bang) * 0.85, math.sin(bang) * 0.85, 0.45 + (bi % 2) * 0.25))
                    _make_leaf_or_bract_bm(bm_bracts, pos_l + bdir * 0.04, bdir, length=0.125, width=0.095, cup=0.22)
                # Tiny cream true flower tube at center of triad
                bmesh.ops.create_icosphere(
                    bm_flowers, subdivisions=1, radius=0.018,
                    matrix=Matrix.Translation(pos_l + Vector((0, 0, 0.04))),
                )

    leaves_obj = create_mesh_object(f"{name}_Leaves", bm_leaves, collection, (0, 0, 0), mat=mat_leaf, ink_mat=ink_mat, outline_thickness=0.005, smooth=True)
    leaves_obj.parent = parent
    bracts_obj = create_mesh_object(f"{name}_Bracts", bm_bracts, collection, (0, 0, 0), mat=mat_flower, ink_mat=ink_mat, outline_thickness=0.005, smooth=True)
    bracts_obj.parent = parent
    flowers_obj = create_mesh_object(f"{name}_TrueFlowers", bm_flowers, collection, (0, 0, 0), mat=mat_cream or mat_flower, smooth=True)
    flowers_obj.parent = parent
    return parent


def make_mediterranean_building_3d(
    name: str,
    location: Tuple[float, float, float],
    size: Tuple[float, float, float],
    face_side: float,
    collection,
    mat_wall,
    mats: dict,
    shutter_mat=None,
    floors: int = 3,
    with_balconies: bool = True,
):
    """
    Bangunan Pesisir Mediterania NYATA (Referensi: Positano / Cinque Terre / Lisbon Alfama):
      - Dinding stucco bertekstur + cornice batu kapur putih + corner quoins klasik
      - Atap pelana genteng terakota melengkung (coppi) + kasau kayu overhanging (mensole)
      - Jendela cekung berkaca dengan bingkai batu & daun jendela kayu berjeruji (persiane louvers)
      - Balkon besi tempa (wrought-iron vertical spindles & stone corbels) + kotak bunga bougainvillea!
    """
    parent = bpy.data.objects.new(name, None)
    parent.location = Vector(location)
    link_object(parent, collection)

    fw, fd, fh = size
    ink = mats["ink"]
    sh_m = shutter_mat or mats["shutter_green"]

    # Badan bangunan + cornice atas & lis batu kapur pembagi lantai
    body = make_beveled_box(f"{name}_Body", (fw, fd, fh), (0, 0, 0), collection, mat_wall, bevel_width=0.06, ink_mat=ink, outline_thickness=0.020)
    body.parent = parent
    cornice = make_beveled_box(f"{name}_Cornice", (fw + 0.28, fd + 0.28, 0.26), (0, 0, fh * 0.5), collection, mats["limestone_trim"], bevel_width=0.04, ink_mat=ink, outline_thickness=0.015)
    cornice.parent = parent
    plinth = make_beveled_box(f"{name}_Plinth", (fw + 0.16, fd + 0.16, 0.55), (0, 0, -fh * 0.5 + 0.28), collection, mats["stone_step"], bevel_width=0.04)
    plinth.parent = parent

    # Atap miring genteng terakota bergelombang (coppi ridges) + lis kayu kasau!
    roof_h = 1.45
    roof_slope_l = make_beveled_box(f"{name}_RoofL", (fw * 0.62, fd + 0.55, 0.22), (-fw * 0.24, 0, fh * 0.5 + roof_h * 0.45), collection, mats["terracotta_roof"], rotation_deg=(0, -24, 0), bevel_width=0.04, ink_mat=ink, outline_thickness=0.018)
    roof_slope_l.parent = parent
    roof_slope_r = make_beveled_box(f"{name}_RoofR", (fw * 0.62, fd + 0.55, 0.22), (fw * 0.24, 0, fh * 0.5 + roof_h * 0.45), collection, mats["terracotta_roof"], rotation_deg=(0, 24, 0), bevel_width=0.04, ink_mat=ink, outline_thickness=0.018)
    roof_slope_r.parent = parent
    ridge = make_smooth_cylinder(f"{name}_RoofRidge", 0.16, 0.16, fd + 0.60, (0, 0, fh * 0.5 + roof_h * 0.78), collection, mats["terracotta_roof"], segments=12, rotation_deg=(90, 0, 0), ink_mat=ink, outline_thickness=0.014)
    ridge.parent = parent
    # Deretan rusuk genteng terakota (coppi) di sisi menghadap gang
    n_tiles = max(4, int(fd / 0.85))
    for ti in range(n_tiles):
        ty = -fd * 0.44 + (ti / max(1, n_tiles - 1)) * (fd * 0.88)
        tile = make_smooth_cylinder(
            f"{name}_Tile_{ti}", 0.085, 0.085, fw * 0.60,
            (face_side * fw * 0.24, ty, fh * 0.5 + roof_h * 0.52), collection,
            mats["terracotta_roof"], segments=8, rotation_deg=(0, 90 + face_side * 24, 0),
        )
        tile.parent = parent

    # Jendela berdaun persiane + balkon besi tempa di setiap lantai
    fx_face = face_side * (fw * 0.5)
    for fi in range(floors):
        z_fl = -fh * 0.28 + fi * (fh * 0.30)
        # Stringcourse batu tipis tiap lantai
        band = make_beveled_box(f"{name}_Band_{fi}", (fw + 0.14, fd + 0.14, 0.14), (0, 0, z_fl - 0.95), collection, mats["limestone_trim"], bevel_width=0.025)
        band.parent = parent

        for wy_off in (-fd * 0.22, fd * 0.22):
            # Bingkai batu + kaca jendela + palang mullion
            wframe = make_beveled_box(f"{name}_WFrame_{fi}_{wy_off:.1f}", (0.16, 1.18, 1.56), (fx_face + face_side * 0.03, wy_off, z_fl), collection, mats["limestone_trim"], bevel_width=0.025, ink_mat=ink, outline_thickness=0.010)
            wframe.parent = parent
            wglass = make_beveled_box(f"{name}_WGlass_{fi}_{wy_off:.1f}", (0.06, 0.94, 1.32), (fx_face + face_side * 0.06, wy_off, z_fl), collection, mats["glass_dusty"], bevel_width=0.01)
            wglass.parent = parent
            # Daun jendela kayu terbuka (persiane) di kiri & kanan jendela
            for sh_s in (-1.0, 1.0):
                sh = make_beveled_box(f"{name}_Shutter_{fi}_{wy_off:.1f}_{sh_s:.0f}", (0.08, 0.46, 1.44), (fx_face + face_side * 0.11, wy_off + sh_s * 0.72, z_fl), collection, sh_m, rotation_deg=(0, 0, face_side * sh_s * 16), bevel_width=0.018, ink_mat=ink, outline_thickness=0.008)
                sh.parent = parent

        # Balkon besi tempa + corbel batu + kotak tanaman di lantai atas!
        if with_balconies and fi >= 1:
            bx = fx_face + face_side * 0.62
            slab = make_beveled_box(f"{name}_BalcSlab_{fi}", (1.22, fd * 0.72, 0.18), (bx, 0, z_fl - 0.85), collection, mats["limestone_trim"], bevel_width=0.035, ink_mat=ink, outline_thickness=0.014)
            slab.parent = parent
            # Corbel batu penopang bawah balkon
            for cy in (-fd * 0.28, 0.0, fd * 0.28):
                corb = make_beveled_box(f"{name}_Corbel_{fi}_{cy:.1f}", (0.85, 0.18, 0.34), (fx_face + face_side * 0.42, cy, z_fl - 1.10), collection, mats["limestone_trim"], bevel_width=0.04)
                corb.parent = parent
            # Handrail atas & tiang besi tempa vertikal (spindles — bukan tembok solid!)
            rail_x = fx_face + face_side * 1.16
            top_r = make_beveled_box(f"{name}_BalcTopRail_{fi}", (0.07, fd * 0.70, 0.07), (rail_x, 0, z_fl + 0.06), collection, mats["iron_dark"], bevel_width=0.015)
            top_r.parent = parent
            for spi in range(9):
                sy = -fd * 0.33 + (spi / 8.0) * (fd * 0.66)
                spindle = make_smooth_cylinder(f"{name}_Spindle_{fi}_{spi}", 0.022, 0.022, 0.88, (rail_x, sy, z_fl - 0.38), collection, mats["iron_dark"], segments=8)
                spindle.parent = parent
            # Kotak bunga terakota dengan bunga bougainvillea!
            pbox = make_beveled_box(f"{name}_Planter_{fi}", (0.30, 1.35, 0.28), (rail_x - face_side * 0.10, -fd * 0.14, z_fl + 0.16), collection, mats["terracotta_pot"], bevel_width=0.04, ink_mat=ink, outline_thickness=0.010)
            pbox.parent = parent
            pflow = make_smooth_sphere(f"{name}_PlanterFlower_{fi}", 0.26, (rail_x - face_side * 0.06, -fd * 0.14, z_fl + 0.36), collection, mats["boug_bract"], scale=(0.8, 2.2, 0.65), subdivisions=2)
            pflow.parent = parent
    return parent


def make_vintage_tram_3d(
    name: str,
    location: Tuple[float, float, float],
    collection,
    mats: dict,
):
    """
    Trem Vintage Pesisir NYATA (Referensi: Lisbon Tram 28 'Remodelado' Series 541-585):
      - Dimensi proporsional 2.4m x 9.6m, ujung depan-belakang melengkung + cowcatcher besi
      - Atap Clerestory (monitor roof bertingkat) dengan jendela ventilasi transom kecil di sisi atas!
      - Jendela kayu geser multi-panel memperlihatkan bangku kayu interior & tiang pegangan kuningan
      - Lampu depan bulat kuningan tunggal, papan rute atap, bogie 4 roda baja, & half-pantograph kuningan!
    """
    root = bpy.data.objects.new(name, None)
    root.location = Vector(location)
    link_object(root, collection)
    ink = mats["ink"]

    # 1. Bogie & sasis baja sempit (gauge 900mm) + cowcatcher pelindung depan/belakang
    chassis = make_beveled_box(f"{name}_Chassis", (2.30, 9.8, 0.38), (0, 0, 0.46), collection, mats["iron_dark"], bevel_width=0.04, ink_mat=ink, outline_thickness=0.016)
    chassis.parent = root
    for wy in (-2.8, -1.6, 1.6, 2.8):
        for wx in (-0.94, 0.94):
            whl = make_smooth_cylinder(f"{name}_Wheel_{wx:.1f}_{wy:.1f}", 0.36, 0.36, 0.16, (wx, wy, 0.36), collection, mats["steel_bright"], segments=20, rotation_deg=(0, 90, 0))
            whl.parent = root
    for end_s in (-1.0, 1.0):
        cow = make_beveled_box(f"{name}_Cowcatcher_{end_s:.0f}", (2.15, 0.55, 0.22), (0, end_s * 5.05, 0.32), collection, mats["iron_dark"], rotation_deg=(end_s * 18, 0, 0), bevel_width=0.03)
        cow.parent = root

    # 2. Badan bawah panel logam merah tua (crimson) + sabuk trim kuningan + papan kayu interior!
    lower = make_beveled_box(f"{name}_LowerBody", (2.48, 9.9, 1.18), (0, 0, 1.24), collection, mats["tram_crimson"], bevel_width=0.09, ink_mat=ink, outline_thickness=0.022)
    lower.parent = root
    trim_bot = make_beveled_box(f"{name}_TrimBot", (2.54, 9.96, 0.12), (0, 0, 0.72), collection, mats["brass_gold"], bevel_width=0.025)
    trim_bot.parent = root
    trim_mid = make_beveled_box(f"{name}_TrimMid", (2.56, 9.98, 0.14), (0, 0, 1.84), collection, mats["tram_cream"], bevel_width=0.03, ink_mat=ink, outline_thickness=0.012)
    trim_mid.parent = root

    # Interior bangku kayu pernis memanjang & tiang pegangan kuningan (terlihat lewat kaca!)
    for sx in (-0.82, 0.82):
        bench = make_beveled_box(f"{name}_InteriorBench_{sx:.1f}", (0.44, 7.6, 0.10), (sx, 0, 1.38), collection, mats["tram_varnished_wood"], bevel_width=0.02)
        bench.parent = root
    for py in (-2.8, 0.0, 2.8):
        pole = make_smooth_cylinder(f"{name}_BrassPole_{py:.1f}", 0.026, 0.026, 1.95, (0.0, py, 2.15), collection, mats["brass_gold"], segments=10)
        pole.parent = root

    # 3. Kabin jendela geser bingkai kayu gelap (6 jendela samping + kaca depan datar klasik!)
    cab_glass = make_beveled_box(f"{name}_CabGlass", (2.34, 9.2, 1.16), (0, 0, 2.48), collection, mats["glass_dusty"], bevel_width=0.04)
    cab_glass.parent = root
    # Bingkai kayu jendela bawah & atas + 7 pilar jendela kayu vertikal + lengkung atas
    win_sill = make_beveled_box(f"{name}_WinSill", (2.50, 9.65, 0.12), (0, 0, 1.92), collection, mats["tram_varnished_wood"], bevel_width=0.025)
    win_sill.parent = root
    win_top = make_beveled_box(f"{name}_WinHeader", (2.52, 9.75, 0.20), (0, 0, 3.08), collection, mats["tram_cream"], bevel_width=0.035, ink_mat=ink, outline_thickness=0.015)
    win_top.parent = root
    for py in (-4.75, -3.25, -1.75, -0.25, 1.25, 2.75, 4.75):
        for px in (-1.21, 1.21):
            pil = make_beveled_box(f"{name}_WinMullion_{px:.1f}_{py:.1f}", (0.12, 0.18, 1.18), (px, py, 2.50), collection, mats["tram_cream"], bevel_width=0.022, ink_mat=ink, outline_thickness=0.010)
            pil.parent = root

    # 4. ATAP CLERESTORY (MONITOR ROOF BERTINGKAT KHAS LISBON TRAM 28!) + jendela transom ventilasi!
    roof_eave = make_beveled_box(f"{name}_RoofLower", (2.66, 10.2, 0.22), (0, 0, 3.24), collection, mats["tram_cream"], bevel_width=0.07, ink_mat=ink, outline_thickness=0.018)
    roof_eave.parent = root
    # Bagian tengah atap terangkat (clerestory monitor) + kaca transom ventilasi
    clere_body = make_beveled_box(f"{name}_ClerestoryBox", (1.62, 8.2, 0.34), (0, 0, 3.50), collection, mats["tram_varnished_wood"], bevel_width=0.04, ink_mat=ink, outline_thickness=0.015)
    clere_body.parent = root
    clere_cap = make_smooth_cylinder(
        f"{name}_ClerestoryCap", 0.94, 0.94, 8.5, (0, 0, 3.68), collection, mats["tram_cream"],
        segments=20, rotation_deg=(90, 0, 0), bevel_width=0.03, ink_mat=ink, outline_thickness=0.016,
    )
    clere_cap.scale = Vector((1.0, 0.24, 1.0))
    clere_cap.parent = root
    # Jendela transom ventilasi kecil berjejer di sisi clerestory
    for ty in (-3.2, -2.0, -0.8, 0.4, 1.6, 2.8):
        for tx in (-0.83, 0.83):
            tr = make_beveled_box(f"{name}_Transom_{tx:.1f}_{ty:.1f}", (0.04, 0.72, 0.18), (tx, ty, 3.50), collection, mats["emissive_lamp"], bevel_width=0.008)
            tr.parent = root

    # 5. Half-Pantograph kuningan & papan tujuan depan/belakang + lampu depan bulat tunggal!
    for sgn in (-1.0, 1.0):
        arm = make_smooth_cylinder(f"{name}_PantoArm_{sgn:.0f}", 0.032, 0.032, 1.25, (0, sgn * 0.42, 4.22), collection, mats["brass_gold"], segments=10, rotation_deg=(sgn * 34, 0, 0))
        arm.parent = root
    p_shoe = make_beveled_box(f"{name}_PantoShoe", (1.42, 0.12, 0.07), (0, 0, 4.74), collection, mats["brass_dark"], bevel_width=0.02)
    p_shoe.parent = root
    for end_y in (-5.02, 5.02):
        sign = make_beveled_box(f"{name}_DestBoard_{end_y:.1f}", (1.15, 0.14, 0.28), (0, end_y * 0.96, 3.44), collection, mats["iron_dark"], bevel_width=0.02)
        sign.parent = root
        lamp_rim = make_smooth_cylinder(f"{name}_LampRim_{end_y:.1f}", 0.24, 0.20, 0.18, (0, end_y, 1.34), collection, mats["brass_gold"], segments=20, rotation_deg=(90, 0, 0), ink_mat=ink, outline_thickness=0.010)
        lamp_rim.parent = root
        lamp_glow = make_smooth_sphere(f"{name}_LampBulb_{end_y:.1f}", 0.17, (0, end_y + (0.07 if end_y > 0 else -0.07), 1.34), collection, mats["emissive_lamp"], subdivisions=2)
        lamp_glow.parent = root
    return root


def make_venetian_clock_tower_3d(
    location_base: Tuple[float, float, float],
    collection,
    mats: dict,
) -> Tuple["bpy.types.Object", "bpy.types.Object"]:
    """
    Menara Jam Utama di Dermaga NYATA (Referensi: Venice Torre dell'Orologio + Renaissance Campanile):
      - Menara batu bertingkat dengan pilaster klasik, cornice batu kapur, corner quoins & gerbang lengkung bawah
      - Balkon batu berbalustrade klasik (tiang baluster batu & corbel) tempat Bima mendarat ([CAM 25]-[CAM 27])!
      - Wajah Jam Astronomis Venesia: cincin lapis-lazuli biru + piringan krem-emas + angka Romawi 3D + jarum filigree emas
      - Paviliun lonceng terbuka (Terrazza dei Mori) beratap kubah tembaga verdigris & lonceng perunggu!
    Mengembalikan (minute_hand_pivot, hour_hand_pivot).
    """
    ink = mats["ink"]
    bx, by_fwd, bz_base = location_base  # x=0, y_fwd=122.5, z=0

    # 1. Badan Menara Batu + Pilaster Klasik + Cornice Pembagi Tingkat
    make_beveled_box("L6_Tower_Main", (14.4, 8.8, 28.4), (bx, by_fwd, bz_base + 14.2), collection, mats["tower_stone"], bevel_width=0.14, ink_mat=ink, outline_thickness=0.036)
    # 4 Pilaster vertikal batu kapur terang di sudut depan menara (membingkai wajah jam!)
    for px in (-6.85, -4.45, 4.45, 6.85):
        make_beveled_box(f"L6_Pilaster_{px:.1f}", (0.72, 0.55, 27.8), (px, by_fwd - 4.42, bz_base + 14.0), collection, mats["limestone_trim"], bevel_width=0.05, ink_mat=ink, outline_thickness=0.020)
    # Cornice horizontal batu kapur bertingkat
    for ci, cz in enumerate((9.2, 15.0, 26.8, 28.5)):
        make_beveled_box(f"L6_Cornice_{ci}", (15.4 + (0.6 if ci == 3 else 0.0), 9.6 + (0.6 if ci == 3 else 0.0), 0.52), (bx, by_fwd, bz_base + cz), collection, mats["limestone_trim"], bevel_width=0.08, ink_mat=ink, outline_thickness=0.025)
    # Gerbang lengkung batu monumental di dasar menara (Torre dell'Orologio ground archway!)
    make_beveled_box("L6_ArchVoid", (5.4, 1.2, 7.6), (bx, by_fwd - 4.2, bz_base + 3.8), collection, mats["vault_stone"], bevel_width=0.08)
    make_smooth_cylinder("L6_ArchTop", 2.75, 2.75, 1.2, (bx, by_fwd - 4.2, bz_base + 7.4), collection, mats["vault_stone"], segments=24, rotation_deg=(90, 0, 0))

    # 2. WAJAH JAM ASTRONOMIS VENESIA (pusat di x=0, y_fwd=118.0, z=19.5!)
    cy_dial, cz_dial = by_fwd - 4.5, bz_base + 19.5
    # Bingkai batu cetakan luar + cincin roda gigi perunggu berukir
    make_cogwheel_3d("L6_ClockOuterCog", 6.85, 0.90, 24, (bx, cy_dial, cz_dial), collection, mats["brass_dark"], hollow_ratio=0.78, spokes=0, ink_mat=ink, outline_thickness=0.032)
    # Cincin Lapis-Lazuli Biru Venesia (outer ring) + Piringan Krem Antik (inner dial)
    make_smooth_cylinder("L6_ClockLapisRing", 5.68, 5.68, 0.24, (bx, cy_dial + 0.16, cz_dial), collection, mats["lapis_blue"], segments=48, rotation_deg=(90, 0, 0))
    make_smooth_cylinder("L6_ClockCreamInner", 4.15, 4.15, 0.26, (bx, cy_dial + 0.06, cz_dial), collection, mats["clock_dial"], segments=48, rotation_deg=(90, 0, 0))
    make_cogwheel_3d("L6_ClockInnerGoldRing", 4.30, 0.18, 24, (bx, cy_dial - 0.12, cz_dial), collection, mats["brass_gold"], hollow_ratio=0.90, spokes=0, ink_mat=ink, outline_thickness=0.014)

    # 12 Penanda Angka Romawi Emas 3D di atas cincin biru lapis-lazuli!
    for hi in range(12):
        ang = math.radians(hi * 30.0)
        rx = bx + math.sin(ang) * 4.85
        rz = cz_dial + math.cos(ang) * 4.85
        is_card = (hi % 3 == 0)
        make_beveled_box(
            f"L6_RomanBar_{hi}",
            (0.34 if is_card else 0.19, 0.24, 1.12 if is_card else 0.76),
            (rx, cy_dial - 0.18, rz), collection, mats["brass_gold"],
            rotation_deg=(0, hi * 30.0, 0), bevel_width=0.03, ink_mat=ink, outline_thickness=0.014,
        )
    # Lubang kunci pusat jam emas berukir ([CAM 25])
    make_smooth_cylinder("L6_CenterHub", 0.72, 0.56, 0.56, (bx, cy_dial - 0.42, cz_dial), collection, mats["brass_gold"], segments=24, rotation_deg=(90, 0, 0), ink_mat=ink, outline_thickness=0.016)
    make_smooth_cylinder("L6_CenterKeyhole", 0.24, 0.24, 0.14, (bx, cy_dial - 0.72, cz_dial), collection, mats["iron_dark"], segments=16, rotation_deg=(90, 0, 0))

    # 3. BALKON BATU BERBALUSTRADE KLASIK (tempat Bima mendarat di [CAM 25]-[CAM 27]!)
    make_beveled_box("L6_Balcony_Deck", (6.8, 2.35, 0.42), (bx, by_fwd - 5.7, bz_base + 15.20), collection, mats["limestone_trim"], bevel_width=0.06, ink_mat=ink, outline_thickness=0.018)
    make_beveled_box("L6_Balcony_WoodFloor", (6.4, 2.05, 0.08), (bx, by_fwd - 5.7, bz_base + 15.42), collection, mats["oak_wood"], bevel_width=0.02)
    # Corbel batu berukir di bawah balkon + tiang baluster batu kiri/kanan (tengah terbuka agar Bima terlihat utuh di [CAM 27]!)
    for cx in (-2.7, -1.35, 0.0, 1.35, 2.7):
        make_beveled_box(f"L6_BalcCorbel_{cx:.1f}", (0.42, 1.65, 0.78), (cx, by_fwd - 5.2, bz_base + 14.65), collection, mats["limestone_trim"], bevel_width=0.06)
    for side_x in (-3.15, 3.15):
        make_beveled_box(f"L6_BalcPost_{side_x:.1f}", (0.34, 0.34, 0.96), (side_x, by_fwd - 6.72, bz_base + 15.88), collection, mats["limestone_trim"], bevel_width=0.04, ink_mat=ink, outline_thickness=0.012)
        make_smooth_sphere(f"L6_BalcFinial_{side_x:.1f}", 0.18, (side_x, by_fwd - 6.72, bz_base + 16.46), collection, mats["brass_gold"], subdivisions=2)
    # Baluster batu di kiri/kanan luar (tidak menutupi saku & Kunci Perak Bima di x=-0.44..+0.2!)
    for bx_b in (-2.55, -1.95, 1.95, 2.55):
        make_lathe_mesh(f"L6_Baluster_{bx_b:.1f}", [(0.11, 0.0), (0.07, 0.18), (0.12, 0.45), (0.07, 0.72), (0.11, 0.85)], (bx_b, by_fwd - 6.72, bz_base + 15.42), collection, mats["limestone_trim"], segments=12, cap_bottom=True, cap_top=True, subsurf_levels=0)

    # 4. PAVILIUN LONCENG TERBUKA (Terrazza dei Mori) + Kubah Tembaga Verdigris + Lonceng Perunggu!
    for px in (-3.8, 3.8):
        for py in (by_fwd - 2.6, by_fwd + 2.6):
            make_beveled_box(f"L6_BelfryPier_{px:.1f}_{py:.1f}", (0.85, 0.85, 5.2), (px, py, bz_base + 31.2), collection, mats["limestone_trim"], bevel_width=0.06, ink_mat=ink, outline_thickness=0.022)
    make_beveled_box("L6_BelfryRoofBase", (9.2, 7.2, 0.55), (bx, by_fwd, bz_base + 34.0), collection, mats["limestone_trim"], bevel_width=0.08, ink_mat=ink, outline_thickness=0.026)
    make_lathe_mesh(
        "L6_CopperDome",
        [(4.4, 0.0), (4.2, 1.4), (3.4, 3.0), (1.8, 4.4), (0.35, 5.2), (0.12, 6.8)],
        (bx, by_fwd, bz_base + 34.25), collection, mats["copper_ox"], segments=16,
        cap_bottom=True, cap_top=True, subsurf_levels=1, ink_mat=ink, outline_thickness=0.032,
    )
    make_lathe_mesh(
        "L6_BronzeBell",
        [(1.72, 0.0), (1.38, 0.48), (1.06, 1.50), (0.85, 2.20), (0.35, 2.42)],
        (bx, by_fwd - 1.2, bz_base + 29.5), collection, mats["oren_bell_copper"], segments=24,
        cap_bottom=False, cap_top=True, subsurf_levels=1, ink_mat=ink, outline_thickness=0.024,
    )

    # 5. JARUM JAM FILIGREE EMAS & BESI TEMPA (berujung tombak + pemberat ekor bulan!)
    min_piv = bpy.data.objects.new("L6_MinuteHand_Pivot", None)
    min_piv.location = Vector((bx, cy_dial - 0.40, cz_dial))
    link_object(min_piv, collection)
    m_blade = make_beveled_box("L6_MinuteHand_Shaft", (0.26, 0.14, 4.4), (0, 0, 2.0), collection, mats["iron_dark"], bevel_width=0.03, ink_mat=ink, outline_thickness=0.016)
    m_blade.parent = min_piv
    m_tip = make_smooth_cylinder("L6_MinuteHand_Spear", 0.34, 0.02, 0.95, (0, 0, 4.45), collection, mats["brass_gold"], segments=4, bevel_width=0.01, ink_mat=ink, outline_thickness=0.014)
    m_tip.parent = min_piv

    hr_piv = bpy.data.objects.new("L6_HourHand_Pivot", None)
    hr_piv.location = Vector((bx, cy_dial - 0.56, cz_dial))
    link_object(hr_piv, collection)
    h_blade = make_beveled_box("L6_HourHand_Shaft", (0.36, 0.14, 3.0), (0, 0, 1.35), collection, mats["iron_dark"], bevel_width=0.035, ink_mat=ink, outline_thickness=0.016)
    h_blade.parent = hr_piv
    h_sun = make_cogwheel_3d("L6_HourHand_SunCounter", 0.48, 0.12, 10, (0, 0, -0.75), collection, mats["brass_gold"], hollow_ratio=0.45, spokes=4, ink_mat=ink, outline_thickness=0.012)
    h_sun.parent = hr_piv

    return min_piv, hr_piv


def make_coastal_lighthouse_3d(location: Tuple[float, float, float], collection, mats: dict) -> None:
    """Mercusuar Batu Pesisir Eropa NYATA (menara belang merah-putih + galeri besi tempa + ruang kaca Fresnel + kubah tembaga)."""
    ink = mats["ink"]
    lx, ly, lz = location
    make_smooth_cylinder("L6_LH_Plinth", 2.05, 1.80, 1.8, (lx, ly, lz + 0.9), collection, mats["stone_step"], segments=20, ink_mat=ink, outline_thickness=0.025)
    for li in range(5):
        r1 = 1.68 - li * 0.13
        r2 = 1.55 - li * 0.13
        make_smooth_cylinder(f"L6_LH_Band_{li}", r1, r2, 2.2, (lx, ly, lz + 2.8 + li * 2.2), collection, mats["tram_crimson"] if li % 2 == 0 else mats["limestone_trim"], segments=24, ink_mat=ink, outline_thickness=0.024)
    # Galeri batu melingkar + pagar besi tempa + ruang lentera kaca berbingkai + kubah tembaga!
    make_smooth_cylinder("L6_LH_Gallery", 1.55, 1.62, 0.36, (lx, ly, lz + 12.8), collection, mats["limestone_trim"], segments=24, ink_mat=ink, outline_thickness=0.022)
    for ri in range(12):
        ang = ri * (2.0 * math.pi / 12.0)
        make_smooth_cylinder(f"L6_LH_Rail_{ri}", 0.035, 0.035, 0.95, (lx + math.cos(ang) * 1.48, ly + math.sin(ang) * 1.48, lz + 13.45), collection, mats["iron_dark"], segments=8)
    make_smooth_cylinder("L6_LH_LanternGlass", 0.92, 0.92, 1.75, (lx, ly, lz + 13.85), collection, mats["emissive_lighthouse"], segments=20)
    make_lathe_mesh("L6_LH_Cupola", [(1.18, 0.0), (1.02, 0.55), (0.58, 1.10), (0.14, 1.42), (0.04, 2.15)], (lx, ly, lz + 14.72), collection, mats["copper_ox"], segments=18, cap_bottom=True, cap_top=True, ink_mat=ink, outline_thickness=0.020)



def make_seagull_3d(
    name: str,
    location: Tuple[float, float, float],
    collection,
    mats: dict,
    scale: float = 1.0,
):
    """Burung camar 3D halus dengan sayap kiri & kanan terpisah agar bisa mengepak / membeku secara natural!"""
    root = bpy.data.objects.new(name, None)
    root.location = Vector(location)
    root.scale = Vector((scale, scale, scale))
    link_object(root, collection)
    ink = mats["ink"]

    body = make_smooth_sphere(f"{name}_Body", 0.24, (0, 0, 0), collection, mats["seagull_white"], scale=(0.75, 1.95, 0.72), subdivisions=2, ink_mat=ink, outline_thickness=0.012)
    body.parent = root
    head = make_smooth_sphere(f"{name}_Head", 0.15, (0, 0.42, 0.08), collection, mats["seagull_white"], subdivisions=2, ink_mat=ink, outline_thickness=0.010)
    head.parent = root
    beak = make_smooth_cylinder(f"{name}_Beak", 0.045, 0.008, 0.20, (0, 0.62, 0.06), collection, mats["prop_orange"], segments=10, rotation_deg=(90, 0, 0), bevel_width=0.002)
    beak.parent = root

    wings = {}
    for side, sgn in (("L", -1.0), ("R", 1.0)):
        pivot = bpy.data.objects.new(f"{name}_WingPivot_{side}", None)
        pivot.location = Vector((sgn * 0.14, 0.04, 0.06))
        link_object(pivot, collection)
        pivot.parent = root

        inner = make_beveled_box(f"{name}_WingIn_{side}", (0.62, 0.28, 0.045), (sgn * 0.30, 0.0, 0.0), collection, mats["seagull_white"], bevel_width=0.016, ink_mat=ink, outline_thickness=0.010)
        inner.parent = pivot
        tip = make_beveled_box(f"{name}_WingTip_{side}", (0.50, 0.20, 0.036), (sgn * 0.78, -0.04, -0.03), collection, mats["seagull_wingtip"], rotation_deg=(0, sgn * 8, -sgn * 10), bevel_width=0.012, ink_mat=ink, outline_thickness=0.010)
        tip.parent = pivot
        wings[side] = pivot

    return root, wings["L"], wings["R"]
