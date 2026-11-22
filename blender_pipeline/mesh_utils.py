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


def make_potted_bougainvillea_3d(
    name: str,
    location: Tuple[float, float, float],
    collection,
    mat_pot,
    mat_leaf,
    mat_flower,
    ink_mat=None,
    scale: float = 1.0,
):
    """Pot terakota organik berbibir + rimbunan daun & gugusan bunga bougenville magenta."""
    parent = bpy.data.objects.new(name, None)
    parent.location = Vector(location)
    parent.scale = Vector((scale, scale, scale))
    link_object(parent, collection)

    pot_prof = [(0.24, 0.00), (0.31, 0.42), (0.34, 0.56), (0.37, 0.58), (0.37, 0.66), (0.31, 0.66), (0.28, 0.54)]
    pot = make_lathe_mesh(
        f"{name}_Pot", pot_prof, (0, 0, 0), collection, mat_pot,
        segments=24, cap_bottom=True, cap_top=True, subsurf_levels=1,
        ink_mat=ink_mat, outline_thickness=0.012,
    )
    pot.parent = parent

    # Rimbunan semak organik berlapis
    bush_specs = [
        (0.0, 0.0, 0.86, 0.38, (1.1, 1.05, 0.92)),
        (-0.22, 0.14, 0.78, 0.26, (1.0, 1.0, 0.9)),
        (0.24, -0.10, 0.82, 0.28, (1.05, 0.95, 0.95)),
        (0.04, 0.22, 1.04, 0.24, (1.1, 0.9, 0.85)),
    ]
    for idx, (bx, by, bz, br, bsc) in enumerate(bush_specs):
        b = make_smooth_sphere(
            f"{name}_Leaf_{idx}", br, (bx, by, bz), collection, mat_leaf,
            scale=bsc, subdivisions=2, ink_mat=ink_mat, outline_thickness=0.012,
        )
        b.parent = parent

    # Gugusan bunga bougenville magenta cerah
    flower_specs = [
        (-0.24, -0.18, 1.08, 0.18),
        (0.26, -0.16, 1.12, 0.19),
        (0.02, -0.26, 0.94, 0.16),
        (-0.14, 0.24, 1.18, 0.16),
        (0.18, 0.18, 1.02, 0.15),
    ]
    for idx, (fx, fy, fz, fr) in enumerate(flower_specs):
        f = make_smooth_sphere(
            f"{name}_Flower_{idx}", fr, (fx, fy, fz), collection, mat_flower,
            scale=(1.15, 0.95, 0.88), subdivisions=2, ink_mat=ink_mat, outline_thickness=0.010,
        )
        f.parent = parent
    return parent


def make_vintage_tram_3d(
    name: str,
    location: Tuple[float, float, float],
    collection,
    mats: dict,
):
    """
    Trem pesisir vintage merah tua berdetail halus (atap melengkung, jendela kaca cekung,
    bingkai krem, lampu depan kuningan menyala, roda baja & pantograf atas).
    """
    root = bpy.data.objects.new(name, None)
    root.location = Vector(location)
    link_object(root, collection)
    ink = mats["ink"]

    # Sasis baja & 4 pasang roda trem
    chassis = make_beveled_box(f"{name}_Chassis", (2.46, 10.6, 0.42), (0, 0, 0.48), collection, mats["iron_dark"], bevel_width=0.05, ink_mat=ink, outline_thickness=0.018)
    chassis.parent = root
    for wy in (-3.6, -2.2, 2.2, 3.6):
        for wx in (-0.98, 0.98):
            whl = make_smooth_cylinder(f"{name}_Wheel_{wx:.1f}_{wy:.1f}", 0.36, 0.36, 0.18, (wx, wy, 0.36), collection, mats["steel_bright"], segments=18, rotation_deg=(0, 90, 0))
            whl.parent = root

    # Badan bawah merah tua melengkung & sabuk emas
    lower = make_beveled_box(f"{name}_LowerBody", (2.68, 10.8, 1.28), (0, 0, 1.30), collection, mats["tram_crimson"], bevel_width=0.08, ink_mat=ink, outline_thickness=0.022)
    lower.parent = root
    stripe = make_beveled_box(f"{name}_GoldTrim", (2.74, 10.86, 0.14), (0, 0, 1.90), collection, mats["brass_gold"], bevel_width=0.03)
    stripe.parent = root

    # Kabin jendela krem & pilar jendela
    cab_glass = make_beveled_box(f"{name}_WindowGlass", (2.52, 10.1, 1.15), (0, 0, 2.54), collection, mats["glass_dusty"], bevel_width=0.04)
    cab_glass.parent = root
    for py in (-5.1, -3.4, -1.7, 0.0, 1.7, 3.4, 5.1):
        for px in (-1.28, 1.28):
            pil = make_beveled_box(f"{name}_Pillar_{px:.1f}_{py:.1f}", (0.14, 0.20, 1.22), (px, py, 2.54), collection, mats["tram_cream"], bevel_width=0.025, ink_mat=ink, outline_thickness=0.012)
            pil.parent = root

    # Atap lengkung khas trem Eropa pesisir (clere-story curved roof)
    roof_main = make_smooth_cylinder(
        f"{name}_RoofMain", 1.38, 1.38, 11.1, (0, 0, 3.16), collection, mats["tram_cream"],
        segments=24, rotation_deg=(90, 0, 0), bevel_width=0.04, ink_mat=ink, outline_thickness=0.020,
    )
    roof_main.scale = Vector((1.0, 0.30, 1.0))
    roof_main.parent = root

    roof_deck = make_beveled_box(f"{name}_RoofWalkway", (1.65, 9.6, 0.18), (0, 0, 3.60), collection, mats["oak_wood"], bevel_width=0.04, ink_mat=ink, outline_thickness=0.015)
    roof_deck.parent = root

    # Pantograf kuningan lipat di atas atap
    for sgn in (-1.0, 1.0):
        arm = make_smooth_cylinder(f"{name}_Pantograph_{sgn:.0f}", 0.035, 0.035, 1.35, (0, sgn * 0.45, 4.15), collection, mats["brass_gold"], segments=10, rotation_deg=(sgn * 34, 0, 0))
        arm.parent = root
    p_bar = make_beveled_box(f"{name}_PantographBar", (1.45, 0.10, 0.08), (0, 0, 4.72), collection, mats["brass_dark"], bevel_width=0.02)
    p_bar.parent = root

    # Lampu depan bulat menyala hangat di kedua ujung trem
    for end_y in (-5.44, 5.44):
        lamp_housing = make_smooth_cylinder(f"{name}_LampRim_{end_y:.1f}", 0.24, 0.20, 0.16, (0, end_y, 1.35), collection, mats["brass_gold"], segments=18, rotation_deg=(90, 0, 0))
        lamp_housing.parent = root
        lamp_bulb = make_smooth_sphere(f"{name}_LampGlow_{end_y:.1f}", 0.18, (0, end_y + (0.06 if end_y > 0 else -0.06), 1.35), collection, mats["emissive_lamp"], subdivisions=2)
        lamp_bulb.parent = root
    return root


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
