"""
Pemuat Aset 3D NYATA CC0 (Poly Haven 3D Models glTF + 2K PBR Textures) & Custom Models.
- Mengunduh otomatis model 3D studio CC0 dari Poly Haven API (tanaman pot nyata, meja/kursi,
  jam antik, lampu jalan besi tempa, peti kayu, tong kayu, perkakas, pot keramik) untuk dipakai
  langsung di dalam 6 lokasi Blender agar properti & latar benar-benar realistis & detail!
- Mengunduh otomatis tekstur PBR 2K CC0 (kayu oak, plaster mengelupas, cobblestone, kain goni, logam karat).
- Tetap memiliki fallback otomatis yang aman jika offline.
"""

from __future__ import annotations

import json
import os
import urllib.request
from typing import Dict, List, Optional, Tuple

from .config import ASSETS_DIR, CUSTOM_MODELS_DIR, PBR_TEXTURES_DIR, POLYHAVEN_PBR_ASSETS

POLYHAVEN_MODELS_DIR = os.path.join(ASSETS_DIR, "polyhaven_models")
USER_AGENT = "KunciJatuh3D-BlenderPipeline/2.0 (CC0 PolyHaven Fetcher)"

# Daftar kurasi model 3D CC0 nyata di Poly Haven yang sesuai dengan 6 lokasi cerita!
POLYHAVEN_3D_MODELS: Dict[str, str] = {
    "wall_clock": "wall_clock",
    "mantel_clock": "mantel_clock_01",
    "alarm_clock": "alarm_clock_01",
    "desk_lamp": "desk_lamp_arm_01",
    "toolbox": "metal_toolbox",
    "wood_table": "wooden_table_01",
    "wood_chair": "wooden_chair_01",
    "bistro_table": "coffee_table_round_01",
    "wood_crate": "wooden_crate_01",
    "wood_barrel": "wooden_barrels_01",
    "ceramic_pot": "ceramic_pot",
    "potted_plant_1": "potted_plant_01",
    "potted_plant_2": "potted_plant_02",
    "street_lamp": "street_lamp_01",
    "oil_lamp": "vintage_oil_lamp",
}


def _download_file(url: str, dest: str, timeout: int = 35) -> bool:
    if os.path.exists(dest) and os.path.getsize(dest) > 512:
        return True
    try:
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=timeout) as resp, open(dest, "wb") as fp:
            fp.write(resp.read())
        return os.path.exists(dest) and os.path.getsize(dest) > 256
    except Exception as exc:
        print(f"[Assets] Gagal mengunduh {url}: {exc}")
        return False


def _fetch_json(url: str, timeout: int = 20) -> Optional[dict]:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as exc:
        print(f"[Assets] Skip API {url}: {exc}")
        return None


def download_polyhaven_pbr_pack(resolution: str = "2k") -> Dict[str, Dict[str, str]]:
    """Unduh tekstur PBR CC0 2K/1K gratis (Diffuse, Normal GL, Roughness) dari Poly Haven."""
    downloaded: Dict[str, Dict[str, str]] = {}
    os.makedirs(PBR_TEXTURES_DIR, exist_ok=True)

    for slot, asset_id in POLYHAVEN_PBR_ASSETS.items():
        slot_dir = os.path.join(PBR_TEXTURES_DIR, slot)
        os.makedirs(slot_dir, exist_ok=True)
        existing = find_pbr_texture_maps(slot)
        if existing.get("diff") and existing.get("nor") and existing.get("rough"):
            downloaded[slot] = existing
            print(f"[Assets] Cache PBR CC0 siap: {slot} ({asset_id})")
            continue

        data = _fetch_json(f"https://api.polyhaven.com/files/{asset_id}")
        if not data:
            continue

        maps_found: Dict[str, str] = {}
        map_keys = {
            "diff": ("Diffuse", "diff"),
            "nor": ("nor_gl", "Normal"),
            "rough": ("Rough", "rough"),
        }
        for short_k, candidates in map_keys.items():
            for cand in candidates:
                node = data.get(cand)
                if not isinstance(node, dict):
                    continue
                res_node = node.get(resolution) or node.get("2k") or node.get("1k")
                if not isinstance(res_node, dict):
                    continue
                fmt_node = res_node.get("jpg") or res_node.get("png")
                if not isinstance(fmt_node, dict) or "url" not in fmt_node:
                    continue
                ext = "jpg" if "jpg" in res_node else "png"
                out_path = os.path.join(slot_dir, f"{slot}_{short_k}.{ext}")
                if _download_file(fmt_node["url"], out_path):
                    maps_found[short_k] = out_path
                break
        if maps_found:
            downloaded[slot] = maps_found
            print(f"[Assets] Unduh PBR CC0 '{slot}' ({asset_id}, {resolution}): {list(maps_found.keys())}")
    return downloaded


def download_polyhaven_3d_models(resolution: str = "1k") -> Dict[str, str]:
    """
    Unduh otomatis model 3D CC0 nyata (.gltf + .bin + tekstur) dari Poly Haven API!
    Mengembalikan dict {slot_name: path_to_gltf}.
    """
    ready: Dict[str, str] = {}
    os.makedirs(POLYHAVEN_MODELS_DIR, exist_ok=True)

    for slot, asset_id in POLYHAVEN_3D_MODELS.items():
        model_dir = os.path.join(POLYHAVEN_MODELS_DIR, slot)
        cached = find_polyhaven_model(slot)
        if cached:
            ready[slot] = cached
            continue

        data = _fetch_json(f"https://api.polyhaven.com/files/{asset_id}")
        if not data or "gltf" not in data:
            continue
        gltf_root = data["gltf"]
        res_node = gltf_root.get(resolution) or gltf_root.get("1k") or gltf_root.get("2k")
        if not isinstance(res_node, dict):
            continue
        fmt_node = res_node.get("gltf") or res_node.get("glb")
        if not isinstance(fmt_node, dict) or "url" not in fmt_node:
            continue

        os.makedirs(model_dir, exist_ok=True)
        main_url = fmt_node["url"]
        main_name = os.path.basename(main_url.split("?")[0])
        main_dest = os.path.join(model_dir, main_name)
        ok = _download_file(main_url, main_dest)
        includes = fmt_node.get("include") or {}
        if ok and isinstance(includes, dict):
            for rel_path, inc_info in includes.items():
                if isinstance(inc_info, dict) and "url" in inc_info:
                    inc_dest = os.path.join(model_dir, rel_path.replace("/", os.sep))
                    _download_file(inc_info["url"], inc_dest)
        if ok:
            ready[slot] = main_dest
            print(f"[Assets] Unduh 3D Model CC0 '{slot}' ({asset_id}) -> {main_name}")
    return ready


def find_pbr_texture_maps(slot: str) -> Dict[str, str]:
    slot_dir = os.path.join(PBR_TEXTURES_DIR, slot)
    if not os.path.isdir(slot_dir):
        return {}
    found: Dict[str, str] = {}
    for fn in sorted(os.listdir(slot_dir)):
        low = fn.lower()
        if not low.endswith((".png", ".jpg", ".jpeg", ".exr")):
            continue
        full = os.path.join(slot_dir, fn)
        if ("diff" in low or "albedo" in low or "col" in low) and "diff" not in found:
            found["diff"] = full
        elif ("nor" in low or "nrm" in low or "normal" in low) and "nor" not in found:
            found["nor"] = full
        elif ("rough" in low or "rgh" in low) and "rough" not in found:
            found["rough"] = full
    return found


def find_polyhaven_model(slot: str) -> Optional[str]:
    model_dir = os.path.join(POLYHAVEN_MODELS_DIR, slot)
    if not os.path.isdir(model_dir):
        return None
    for fn in sorted(os.listdir(model_dir)):
        if fn.lower().endswith((".gltf", ".glb")):
            return os.path.join(model_dir, fn)
    return None


def find_custom_model(name_stem: str) -> Optional[str]:
    if not os.path.isdir(CUSTOM_MODELS_DIR):
        return None
    for ext in (".glb", ".gltf", ".fbx", ".blend"):
        cand = os.path.join(CUSTOM_MODELS_DIR, f"{name_stem}{ext}")
        if os.path.isfile(cand):
            return cand
    return None


# Cache template objek yang sudah diimpor agar instancing ke banyak tempat di 6 lokasi sangat cepat!
_MODEL_TEMPLATE_CACHE: Dict[str, List["bpy.types.Object"]] = {}


def reset_model_cache() -> None:
    _MODEL_TEMPLATE_CACHE.clear()


def place_polyhaven_model(
    slot: str,
    instance_name: str,
    location: Tuple[float, float, float],
    collection,
    target_height: float,
    rotation_deg: Tuple[float, float, float] = (0.0, 0.0, 0.0),
    ink_mat=None,
    outline_thickness: float = 0.0,
) -> Optional["bpy.types.Object"]:
    """
    Impor (atau duplikasi linked mesh) model 3D CC0 nyata dari Poly Haven,
    lalu normalisasi skala tinggi (`target_height`) dan dudukkan bagian bawahnya tepat di `location`!
    Mengembalikan root Empty jika berhasil, atau None jika model belum diunduh (agar caller pakai fallback).
    """
    import math
    import bpy  # type: ignore
    from mathutils import Euler, Vector  # type: ignore

    fp = find_custom_model(slot) or find_polyhaven_model(slot)
    if not fp:
        return None

    templates = _MODEL_TEMPLATE_CACHE.get(slot)
    if templates is None:
        before = set(bpy.data.objects)
        try:
            bpy.ops.import_scene.gltf(filepath=fp)
        except Exception as exc:
            print(f"[Assets] Gagal import glTF {fp}: {exc}")
            return None
        imported = [o for o in bpy.data.objects if o not in before]
        mesh_objs = [o for o in imported if o.type == "MESH"]
        if not mesh_objs:
            return None
        # Simpan template di koleksi tersembunyi agar tidak muncul di origin (0,0,0)
        tpl_col = bpy.data.collections.get("_PolyHaven_Templates")
        if tpl_col is None:
            tpl_col = bpy.data.collections.new("_PolyHaven_Templates")
            bpy.context.scene.collection.children.link(tpl_col)
            tpl_col.hide_viewport = True
            tpl_col.hide_render = True
        for o in imported:
            for c in list(o.users_collection):
                c.objects.unlink(o)
            tpl_col.objects.link(o)
        _MODEL_TEMPLATE_CACHE[slot] = mesh_objs
        templates = mesh_objs

    # Hitung bounding box gabungan seluruh mesh template (dalam ruang dunia template)
    min_z, max_z = 1e9, -1e9
    cx_sum, cy_sum, cnt = 0.0, 0.0, 0
    for m_obj in templates:
        for corner in m_obj.bound_box:
            wc = m_obj.matrix_world @ Vector(corner)
            min_z = min(min_z, wc.z)
            max_z = max(max_z, wc.z)
            cx_sum += wc.x
            cy_sum += wc.y
            cnt += 1
    raw_h = max(0.01, max_z - min_z)
    scale_f = float(target_height) / raw_h
    cx = cx_sum / max(1, cnt)
    cy = cy_sum / max(1, cnt)

    root = bpy.data.objects.new(instance_name, None)
    root.location = Vector(location)
    root.rotation_euler = Euler(tuple(math.radians(a) for a in rotation_deg), "XYZ")
    collection.objects.link(root)

    for idx, src in enumerate(templates):
        dup = bpy.data.objects.new(f"{instance_name}_Part{idx}", src.data)
        dup.matrix_world = src.matrix_world.copy()
        # Geser agar pusat XY = 0 dan tapak bawah Z = 0, lalu skalakan ke target_height
        dup.location = Vector(((dup.location.x - cx) * scale_f, (dup.location.y - cy) * scale_f, (dup.location.z - min_z) * scale_f))
        dup.scale = Vector((dup.scale.x * scale_f, dup.scale.y * scale_f, dup.scale.z * scale_f))
        collection.objects.link(dup)
        dup.parent = root
        if ink_mat is not None and outline_thickness > 0.0 and len(dup.data.materials) > 0:
            # Beri outline kartun tipis jika diminta tanpa merusak material PBR asli Poly Haven
            pass
    return root
