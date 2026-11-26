"""
Utilitas Geometri 3D Halus & Bervolume (bmesh + Bevel + Inverted-Hull Ink Outline)
untuk Blender 4.2 LTS — Bebas bentuk kotak tajam kasar!
"""
from __future__ import annotations

import math
from typing import Optional, Sequence, Tuple

import bmesh  # type: ignore
import bpy  # type: ignore
from mathutils import Euler, Vector  # type: ignore


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
    mesh = obj.data
    if hasattr(mesh, "polygons") and len(mesh.polygons) > 0:
        mesh.polygons.foreach_set("use_smooth", [True] * len(mesh.polygons))
        mesh.update()


def assign_material(obj, mat, ink_mat=None, outline_thickness: float = 0.0) -> None:
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


def add_bevel(obj, width: float = 0.02, segments: int = 3) -> None:
    mod = obj.modifiers.new(name="Bevel", type="BEVEL")
    mod.width = width
    mod.segments = segments
    mod.limit_method = "ANGLE"
    mod.angle_limit = math.radians(32.0)


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
        add_bevel(obj, width=bevel_width, segments=2)
    if mat is not None:
        assign_material(obj, mat, ink_mat=ink_mat, outline_thickness=outline_thickness)
    return obj


def make_box(
    name: str,
    size: Tuple[float, float, float],
    location: Tuple[float, float, float],
    collection,
    mat,
    rotation_deg=(0.0, 0.0, 0.0),
    bevel_width: float = 0.025,
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
    bw = min(bevel_width, min(sx, sy, sz) * 0.20) if bevel_width > 0 else 0.0
    return create_mesh_object(
        name, bm, collection, location=location, rotation_deg=rotation_deg,
        mat=mat, ink_mat=ink_mat, outline_thickness=outline_thickness, bevel_width=bw,
    )


def make_cyl(
    name: str,
    r1: float,
    r2: float,
    depth: float,
    location: Tuple[float, float, float],
    collection,
    mat,
    segments: int = 20,
    rotation_deg=(0.0, 0.0, 0.0),
    bevel_width: float = 0.008,
    ink_mat=None,
    outline_thickness: float = 0.0,
):
    bm = bmesh.new()
    bmesh.ops.create_cone(
        bm, cap_ends=True, cap_tris=False, segments=segments,
        radius1=r1, radius2=r2, depth=depth,
    )
    return create_mesh_object(
        name, bm, collection, location=location, rotation_deg=rotation_deg,
        mat=mat, ink_mat=ink_mat, outline_thickness=outline_thickness, bevel_width=bevel_width,
    )


def make_sphere(
    name: str,
    radius: float,
    location: Tuple[float, float, float],
    collection,
    mat,
    scale=(1.0, 1.0, 1.0),
    ink_mat=None,
    outline_thickness: float = 0.0,
):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=20, v_segments=14, radius=radius)
    return create_mesh_object(
        name, bm, collection, location=location, scale=scale,
        mat=mat, ink_mat=ink_mat, outline_thickness=outline_thickness,
    )


def make_torus_ring(
    name: str,
    major_r: float,
    minor_r: float,
    location: Tuple[float, float, float],
    collection,
    mat,
    rotation_deg=(0.0, 0.0, 0.0),
):
    """Buat cincin kawin emas 3D mulus (major_r, minor_r)."""
    bm = bmesh.new()
    u_seg, v_seg = 28, 14
    grid = []
    for i in range(u_seg):
        u = (i / u_seg) * math.tau
        cu, su = math.cos(u), math.sin(u)
        ring = []
        for j in range(v_seg):
            v = (j / v_seg) * math.tau
            cv, sv = math.cos(v), math.sin(v)
            rr = major_r + minor_r * cv
            ring.append(bm.verts.new((rr * cu, rr * su, minor_r * sv)))
        grid.append(ring)
    for i in range(u_seg):
        ni = (i + 1) % u_seg
        for j in range(v_seg):
            nj = (j + 1) % v_seg
            bm.faces.new((grid[i][j], grid[ni][j], grid[ni][nj], grid[i][nj]))
    return create_mesh_object(name, bm, collection, location=location, rotation_deg=rotation_deg, mat=mat)


def make_curve_cable(
    name: str,
    points_b: Sequence[Tuple[float, float, float]],
    radius: float,
    collection,
    mat,
):
    curve = bpy.data.curves.new(name=name + "_Curve", type="CURVE")
    curve.dimensions = "3D"
    curve.bevel_depth = radius
    curve.bevel_resolution = 3
    sp = curve.splines.new("POLY")
    sp.points.add(len(points_b) - 1)
    for idx, (x, y, z) in enumerate(points_b):
        sp.points[idx].co = (x, y, z, 1.0)
    obj = bpy.data.objects.new(name, curve)
    obj.data.materials.append(mat)
    link_object(obj, collection)
    return obj
