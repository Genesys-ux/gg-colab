"""
Audit Otomatis Pra-Render ("Dry-Run Validator") untuk "DETIK KE-75":
  1. Validasi kompilasi sintaks seluruh file Python pipeline & audio
  2. Validasi 28 gerakan kamera virtual (0.0..75.0s = 2.250 frame) bebas NaN / jarak nol
  3. Validasi Strict Anti-Clipping & Ground Contact seluruh aktor di 6 lokasi (2.250 frame)
  4. Uji rasterisasi PNG nyata seluruh 10 varian karakter Shared-Engine & Free-Rig
"""
from __future__ import annotations

import math
import os
import py_compile
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from blender_pipeline.camera_28_moves import CAMERA_28_SHOTS, eval_camera_world
from blender_pipeline.characters_cast_25d import eval_actors_at_time
from blender_pipeline.config import (
    ICU_BED_POS_W,
    LOC1_FLOOR_Y,
    LOC3_ORIGIN,
    LOC4_FLOOR_Y,
    LOC5_FLOOR_Y,
    LOC6_FLOOR_Y,
    TOTAL_FRAMES,
    frame_to_sec,
)
from characters import CHARACTER_REGISTRY


def main() -> None:
    # 1. Syntax compile check all Python files
    py_dirs = [
        os.path.join(PROJECT_ROOT, "blender_pipeline"),
        os.path.join(PROJECT_ROOT, "audio"),
        os.path.join(PROJECT_ROOT, "characters"),
    ]
    compiled = 0
    for d in py_dirs:
        for fn in os.listdir(d):
            if fn.endswith(".py"):
                py_compile.compile(os.path.join(d, fn), doraise=True)
                compiled += 1
    print(f"[Check 1/4] Syntax compile LULUS ({compiled} modul Python bersih).")

    # 2. Check > 25 Camera Movements & > 5 Locations
    assert len(CAMERA_28_SHOTS) >= 26, f"Jumlah kamera kurang dari >25: {len(CAMERA_28_SHOTS)}"
    seen_cams = set()
    for fr in range(1, TOTAL_FRAMES + 1):
        t = frame_to_sec(fr)
        pos, tgt, lens, roll, cid = eval_camera_world(t)
        seen_cams.add(cid)
        dist = math.dist(pos, tgt)
        assert dist > 0.15, f"Kamera terlalu dekat target pada frame {fr} (t={t:.2f}s): {dist}"
        assert 14.0 <= lens <= 35.0, f"Lensa di luar rentang wide-cinematic pada frame {fr}: {lens}"
    print(f"[Check 2/4] Kamera Virtual 3D LULUS ({len(seen_cams)} shot aktif melintasi 2.250 frame).")

    # 3. Strict Anti-Clipping & Ground Contact across all 2,250 frames
    bx, _, bz = ICU_BED_POS_W
    wx, wy, wz = LOC3_ORIGIN
    for fr in range(1, TOTAL_FRAMES + 1):
        t = frame_to_sec(fr)
        actors = eval_actors_at_time(t)
        for st in actors:
            x, y, z = st.pos_w
            if t < 16.2:
                assert y >= LOC1_FLOOR_Y - 1e-4, f"Clipping lantai Maglev {st.actor_key} @ t={t:.2f}s: y={y}"
                assert abs(x) <= 1.30, f"Clipping dinding Maglev {st.actor_key} @ t={t:.2f}s: x={x}"
                if st.actor_key != "maya_realitas":
                    assert abs(x) <= 0.65, f"Clipping tiang/kursi lorong Maglev {st.actor_key} @ t={t:.2f}s: x={x}"
            elif t < 46.0:
                if st.actor_key == "kira_memori":
                    assert abs(y - wy) < 0.05 and abs(x - (wx - 1.05)) < 1.5, f"Kira keluar dek Menara Air @ t={t:.2f}s"
                else:
                    assert y >= LOC4_FLOOR_Y - 1e-4, f"Clipping lantai Atap {st.actor_key} @ t={t:.2f}s: y={y}"
                    assert abs(x) <= 7.2 and 47.0 <= z <= 73.2, f"Keluar parapet Atap {st.actor_key} @ t={t:.2f}s"
            else:
                if st.actor_key in ("raka_memori", "maya_muda") and x > 3.65:
                    assert abs(y - LOC6_FLOOR_Y) < 0.05 and 3.8 <= x <= 10.5, f"Clipping Koridor Emas {st.actor_key}"
                elif st.actor_key == "raka_realitas":
                    assert y >= LOC5_FLOOR_Y, f"Clipping ranjang ICU Raka Tua @ t={t:.2f}s"
                else:
                    assert abs(y - LOC5_FLOOR_Y) < 0.05, f"Kaki melayang/tembus lantai ICU {st.actor_key} @ t={t:.2f}s"
                    assert -3.9 <= x <= 3.3 and 104.4 <= z <= 116.5, f"Clipping dinding ICU {st.actor_key}"
                    assert abs(x - bx) >= 0.62, f"Clipping kasur ICU {st.actor_key} @ t={t:.2f}s: x={x} vs bed={bx}"
    print("[Check 3/4] Audit Anti-Clipping & Kontak Lantai 6 Lokasi LULUS (0 pelanggaran di 2.250 frame).")

    # 4. Smoke-test all unique character classes in registry
    unique_cls = set(CHARACTER_REGISTRY.values())
    for cls in unique_cls:
        inst = cls(scale=1.5, fps=30)
        png_bytes = inst.render_png_bytes(frame=5, animation="free", angle=15.0)
        assert len(png_bytes) > 1500, f"Sprite kosong untuk {cls.__name__}"
    print(f"[Check 4/4] Rasterisasi {len(unique_cls)} kelas karakter Shared-Engine & Free-Rig LULUS.")


if __name__ == "__main__":
    main()
