"""
Pemuat Aset 3D Eksternal & Tekstur PBR CC0 (Poly Haven / GitHub / Custom .glb/.blend).
- Jika tekstur PBR CC0 sudah diunduh di `assets/textures/<slot>/`, otomatis dihubungkan ke shader Cel-PBR.
- Jika belum/offline, pipeline tetap 100% berjalan memakai node PBR prosedural berlapis di Blender!
- Mendukung substitusi model 3D `.glb`/`.gltf`/`.fbx`/`.blend` kustom di `assets/models/`.
"""

from __future__ import annotations

import json
import os
import urllib.request
from typing import Dict, Optional

from .config import CUSTOM_MODELS_DIR, PBR_TEXTURES_DIR, POLYHAVEN_PBR_ASSETS


def _download_file(url: str, dest: str, timeout: int = 30) -> bool:
    try:
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        req = urllib.request.Request(url, headers={"User-Agent": "BlenderPipeline-KunciJatuh/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp, open(dest, "wb") as fp:
            fp.write(resp.read())
        return os.path.exists(dest) and os.path.getsize(dest) > 1024
    except Exception as exc:
        print(f"[Assets] Gagal mengunduh {url}: {exc}")
        return False


def download_polyhaven_pbr_pack(resolution: str = "1k") -> Dict[str, Dict[str, str]]:
    """
    Unduh otomatis paket tekstur PBR CC0 gratis (Diffuse, Normal GL, Roughness) dari Poly Haven API.
    Dipanggil opsional di Google Colab agar material kayu, plaster, cobblestone, kain goni, & besi karat
    punya detail micro-PBR foto-realistis di bawah Cel-Shading EEVEE Next!
    """
    downloaded: Dict[str, Dict[str, str]] = {}
    os.makedirs(PBR_TEXTURES_DIR, exist_ok=True)

    for slot, asset_id in POLYHAVEN_PBR_ASSETS.items():
        slot_dir = os.path.join(PBR_TEXTURES_DIR, slot)
        os.makedirs(slot_dir, exist_ok=True)
        existing = find_pbr_texture_maps(slot)
        if existing.get("diff") and existing.get("nor") and existing.get("rough"):
            downloaded[slot] = existing
            print(f"[Assets] Cache PBR CC0 sudah siap: {slot} ({asset_id})")
            continue

        api_url = f"https://api.polyhaven.com/files/{asset_id}"
        try:
            req = urllib.request.Request(api_url, headers={"User-Agent": "BlenderPipeline-KunciJatuh/1.0"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except Exception as exc:
            print(f"[Assets] Skip Poly Haven '{asset_id}' (offline/rate-limit): {exc}")
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
                res_node = node.get(resolution) or node.get("1k") or node.get("2k")
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
            print(f"[Assets] Berhasil unduh PBR CC0 '{slot}' ({asset_id}): {list(maps_found.keys())}")
    return downloaded


def find_pbr_texture_maps(slot: str) -> Dict[str, str]:
    """Cari peta tekstur (diff, nor, rough) di `assets/textures/<slot>/` jika tersedia."""
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


def find_custom_model(name_stem: str) -> Optional[str]:
    """Cari file 3D kustom (.glb/.gltf/.fbx/.blend) di `assets/models/` bila pengguna ingin menimpa model bawaan."""
    if not os.path.isdir(CUSTOM_MODELS_DIR):
        return None
    for ext in (".glb", ".gltf", ".fbx", ".blend"):
        cand = os.path.join(CUSTOM_MODELS_DIR, f"{name_stem}{ext}")
        if os.path.isfile(cand):
            return cand
    return None


def import_custom_model_into_collection(filepath: str, collection_name: str):
    """Impor model eksternal (.glb/.gltf/.fbx) ke koleksi Blender secara bersih."""
    import bpy  # type: ignore

    ext = os.path.splitext(filepath)[1].lower()
    before = set(bpy.data.objects)
    if ext in (".glb", ".gltf"):
        bpy.ops.import_scene.gltf(filepath=filepath)
    elif ext == ".fbx":
        bpy.ops.import_scene.fbx(filepath=filepath)
    else:
        return []
    imported = [obj for obj in bpy.data.objects if obj not in before]
    col = bpy.data.collections.get(collection_name) or bpy.data.collections.new(collection_name)
    if col.name not in bpy.context.scene.collection.children:
        bpy.context.scene.collection.children.link(col)
    for obj in imported:
        for old_c in list(obj.users_collection):
            old_c.objects.unlink(obj)
        col.objects.link(obj)
    return imported
