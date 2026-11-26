"""
detik75_rig_addons.py — Addon 3D Projection, Morph-Target Aging & Hand-Tracked Props
untuk Karakter "DETIK KE-75" di atas Shared Engine (character_engine_25d.py).

Tetap menjaga 100% kompatibilitas dengan BaseCharacter25D & Free-Rig terbuka:
  1. Proyeksi silinder 3D untuk customLayers ('head' & 'torso') agar detail wajah
     (bekas luka alis kiri Raka, kantung mata Bima, rambut bob basah & kelopak mata
     menangis Kira, helai rambut lepas Maya, badge dokter Sena) berputar mulus 0..360
     derajat dan otomatis tersembunyi saat menghadap belakang (180 derajat).
  2. Hand/Wrist-Tracked 3D Props di layer 'front'/'back':
     - Cincin emas Maya dengan emissive glow halus yang menempel pada sendi tangan IK.
     - Jam tangan layar merah Kira & gelang pasien ICU Raka yang mengikuti pergelangan.
  3. Sistem Morph-Target Aging real-time (age=0.0..1.0) pada Raka (26 thn -> 78 thn):
     - Shader rambut memutih real-time (#1A1C26 -> #E4E8F0)
     - Blendshapes kerutan dinamis (dahi, kantung mata, garis pipi)
     - Penyusutan bahu & postur membungkuk halus (squash_x, pelvis_y, torso_lean_deg)
"""
from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Tuple

from character_engine_25d import BaseCharacter25D, OX, SvgCanvas2D


def _hex_to_rgb(h: str) -> Tuple[int, int, int]:
    s = h.lstrip("#")
    if len(s) != 6:
        return (200, 200, 200)
    return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16))


def lerp_hex(c1: str, c2: str, t: float) -> str:
    u = max(0.0, min(1.0, float(t)))
    r1, g1, b1 = _hex_to_rgb(c1)
    r2, g2, b2 = _hex_to_rgb(c2)
    r = int(round(r1 + (r2 - r1) * u))
    g = int(round(g1 + (g2 - g1) * u))
    b = int(round(b1 + (b2 - b1) * u))
    return f"#{r:02X}{g:02X}{b:02X}"


def _rot3d_pt(lx: float, y: float, lz: float, s: float, c: float) -> Tuple[float, float, float]:
    return (OX + lx * c + lz * s, y, -lx * s + lz * c)


def project_custom_layers_3d(
    raw_layers: Optional[List[Dict[str, Any]]],
    angle_deg: float,
) -> List[Dict[str, Any]]:
    """
    Proyeksikan customLayers secara silindris berdasarkan sudut kamera 0..360 derajat
    agar bekas luka, kerutan, lanyard, dan detail dada tidak bocor ke punggung/belakang kepala.
    """
    if not raw_layers:
        return []
    deg = ((float(angle_deg) % 360.0) + 360.0) % 360.0
    rad = math.radians(deg)
    s = math.sin(rad)
    c = math.cos(rad)

    out: List[Dict[str, Any]] = []
    for item in raw_layers:
        if not item:
            continue
        side = item.get("facing", "front")  # 'front' | 'back' | 'both'
        if side == "front" and c <= -0.08:
            continue
        if side == "back" and c >= 0.08:
            continue

        vis_alpha = 1.0
        if side == "front":
            vis_alpha = min(1.0, (c + 0.08) * 2.8)
        elif side == "back":
            vis_alpha = min(1.0, (-c + 0.08) * 2.8)

        pivot_x = 104.0
        z_depth = float(item.get("z_offset", 44.0 if item.get("layer") == "torso" else 48.0))
        scale_x = max(0.18, abs(c)) if side != "both" else 1.0
        shift_x = z_depth * s if side != "both" else 0.0

        cloned = dict(item)
        base_op = float(cloned.get("opacity", 1.0))
        cloned["opacity"] = round(base_op * vis_alpha, 4)

        def _tx(x_val: float) -> float:
            if side == "both":
                return x_val
            return round(pivot_x + (x_val - pivot_x) * c + shift_x, 2)

        t = cloned.get("type")
        if t in ("circle", "ellipse"):
            cloned["x"] = _tx(float(cloned.get("x", 104.0)))
            if t == "ellipse" and "rx" in cloned and side != "both":
                cloned["rx"] = max(0.8, round(float(cloned["rx"]) * scale_x, 2))
            elif t == "circle" and "r" in cloned and side != "both" and abs(c) < 0.65:
                cloned["type"] = "ellipse"
                r_val = float(cloned.pop("r"))
                cloned["rx"] = max(0.8, round(r_val * scale_x, 2))
                cloned["ry"] = r_val
                cloned["rot"] = 0.0
        elif t == "rect":
            orig_x = float(cloned.get("x", 90.0))
            orig_w = float(cloned.get("w", 20.0))
            cx = orig_x + orig_w * 0.5
            new_w = orig_w * scale_x if side != "both" else orig_w
            new_cx = _tx(cx)
            cloned["x"] = round(new_cx - new_w * 0.5, 2)
            cloned["w"] = max(1.2, round(new_w, 2))
        elif t == "line":
            cloned["x"] = _tx(float(cloned.get("x", 90.0)))
            cloned["x2"] = _tx(float(cloned.get("x2", 110.0)))

        out.append(cloned)
    return out


def build_raka_aging_layers(age: float) -> List[Dict[str, Any]]:
    """Blendshape garis kerutan dinamis Raka untuk age 0.0 (26 thn) -> 1.0 (78 thn)."""
    u = max(0.0, min(1.0, float(age)))
    if u <= 0.03:
        return []
    op_main = round(0.58 * u, 3)
    op_soft = round(0.40 * u, 3)
    return [
        # Garis kerutan dahi lansia
        {"layer": "head", "facing": "front", "z_offset": 46, "type": "line", "x": 85, "y": 98, "x2": 116, "y2": 97, "stroke": "#8C6D63", "lineWidth": 1.5, "opacity": op_main},
        {"layer": "head", "facing": "front", "z_offset": 46, "type": "line", "x": 89, "y": 102.5, "x2": 112, "y2": 101.8, "stroke": "#8C6D63", "lineWidth": 1.25, "opacity": op_soft},
        # Kantung mata & kerutan bawah mata
        {"layer": "head", "facing": "front", "z_offset": 49, "type": "line", "x": 75, "y": 150.5, "x2": 91, "y2": 151.5, "stroke": "#7E5D55", "lineWidth": 1.6, "opacity": op_main},
        {"layer": "head", "facing": "front", "z_offset": 49, "type": "line", "x": 110, "y": 148.2, "x2": 126, "y2": 149.2, "stroke": "#7E5D55", "lineWidth": 1.6, "opacity": op_main},
        # Garis lipatan nasolabial / pipi menua
        {"layer": "head", "facing": "front", "z_offset": 48, "type": "line", "x": 79, "y": 157, "x2": 72, "y2": 173, "stroke": "#8A685E", "lineWidth": 1.55, "opacity": op_main},
        {"layer": "head", "facing": "front", "z_offset": 48, "type": "line", "x": 124, "y": 155, "x2": 131, "y2": 171, "stroke": "#8A685E", "lineWidth": 1.55, "opacity": op_main},
    ]


class Detik75CharacterBase(BaseCharacter25D):
    """
    Subclass ringan di atas BaseCharacter25D yang mendukung:
      - Proyeksi 3D customLayers otomatis di semua sudut 0..360 derajat
      - Properti tangan/pergelangan 3D berbasis IK:
          *RING_GLOW_HAND*  : 'left' | 'right' | None (Cincin emas Maya dengan emissive glow)
          *WRIST_WATCH_RED* : bool (Jam tangan layar merah Kira)
          *ICU_WRISTBAND*   : bool (Gelang identitas pasien ICU Kakek Raka)
      - Morph-Target Aging real-time (`age=0.0..1.0`) khusus karakter Raka (`SUPPORTS_AGING=True`)
    """

    SUPPORTS_AGING: bool = False
    RING_GLOW_HAND: Optional[str] = None
    WRIST_WATCH_RED: bool = False
    ICU_WRISTBAND: bool = False

    def get_aged_config(self, age: float) -> Dict[str, Any]:
        """Kembalikan dict config hasil morph-target aging (0.0 = 26 thn, 1.0 = 78 thn)."""
        u = max(0.0, min(1.0, float(age)))
        cfg = dict(self.config)
        cfg["hairColor"] = lerp_hex("#1A1C26", "#E4E8F0", u)
        cfg["skinColor"] = lerp_hex("#F6DFC8", "#EDE5DF", u)
        cfg["blushColor"] = lerp_hex("#DFB4A2", "#CFB8B4", u)
        if u > 0.72:
            cfg["backHair"] = "short"
        base_layers = list(cfg.get("customLayers") or [])
        cfg["customLayers"] = base_layers + build_raka_aging_layers(u)
        return cfg

    def _build_hand_tracked_layers(
        self,
        pose: Any,
        angle_deg: float,
        time_sec: float,
        ring_glow_boost: float = 1.0,
    ) -> List[Dict[str, Any]]:
        if not (self.RING_GLOW_HAND or self.WRIST_WATCH_RED or self.ICU_WRISTBAND):
            return []

        deg = ((float(angle_deg) % 360.0) + 360.0) % 360.0
        rad = math.radians(deg)
        s = math.sin(rad)
        c = math.cos(rad)
        lean_sin = math.sin(float(pose.torsoLeanZ))
        lean_cos = math.cos(float(pose.torsoLeanZ))
        sh_dx = 110.0 * lean_sin
        sh_dy = 110.0 * (1.0 - lean_cos)

        la_elb = _rot3d_pt(pose.laElb.x, pose.laElb.y, pose.laElb.z, s, c)
        la_hnd = _rot3d_pt(pose.laHnd.x, pose.laHnd.y, pose.laHnd.z, s, c)
        la_elb = (la_elb[0] + sh_dx * 0.65, la_elb[1] + sh_dy * 0.65, la_elb[2])
        la_hnd = (la_hnd[0] + sh_dx * 0.35, la_hnd[1] + sh_dy * 0.35, la_hnd[2])
        la_depth = 0.5 * (la_elb[2] + la_hnd[2])

        ra_elb = _rot3d_pt(pose.raElb.x, pose.raElb.y, pose.raElb.z, s, c)
        ra_hnd = _rot3d_pt(pose.raHnd.x, pose.raHnd.y, pose.raHnd.z, s, c)
        ra_elb = (ra_elb[0] + sh_dx * 0.65, ra_elb[1] + sh_dy * 0.65, ra_elb[2])
        ra_hnd = (ra_hnd[0] + sh_dx * 0.35, ra_hnd[1] + sh_dy * 0.35, ra_hnd[2])
        ra_depth = 0.5 * (ra_elb[2] + ra_hnd[2])

        extras: List[Dict[str, Any]] = []

        # 1) Cincin Kawin Emas Maya (Emissive Glow Halus Berdenyut)
        if self.RING_GLOW_HAND:
            use_left = self.RING_GLOW_HAND == "left"
            hx, hy, _ = la_hnd if use_left else ra_hnd
            depth = la_depth if use_left else ra_depth
            target_layer = "front" if depth >= -4.0 else "back"
            pulse = (0.78 + 0.22 * math.sin(time_sec * 3.6)) * max(0.0, float(ring_glow_boost))
            extras.extend([
                {"layer": target_layer, "facing": "both", "type": "circle", "x": round(hx + 2.0, 2), "y": round(hy + 2.5, 2), "r": 11.5, "fill": "#FFD966", "opacity": round(0.22 * pulse, 3)},
                {"layer": target_layer, "facing": "both", "type": "circle", "x": round(hx + 2.0, 2), "y": round(hy + 2.5, 2), "r": 6.8, "fill": "#FFE885", "opacity": round(0.42 * pulse, 3)},
                {"layer": target_layer, "facing": "both", "type": "ellipse", "x": round(hx + 2.0, 2), "y": round(hy + 2.5, 2), "rx": 4.2, "ry": 2.6, "rot": 0.35, "fill": "#FFF6C4", "stroke": "#D49B27", "lineWidth": 1.8, "opacity": 0.98},
            ])

        # 2) Jam Tangan Pintar Layar Merah Kira (Pergelangan Kiri)
        if self.WRIST_WATCH_RED:
            wx = la_elb[0] * 0.26 + la_hnd[0] * 0.74
            wy = la_elb[1] * 0.26 + la_hnd[1] * 0.74
            target_layer = "front" if la_depth >= -4.0 else "back"
            extras.extend([
                {"layer": target_layer, "facing": "both", "type": "circle", "x": round(wx, 2), "y": round(wy, 2), "r": 8.5, "fill": "#FF2A3C", "opacity": 0.24},
                {"layer": target_layer, "facing": "both", "type": "rect", "x": round(wx - 5.5, 2), "y": round(wy - 4.0, 2), "w": 11.0, "h": 8.0, "radius": 2.5, "fill": "#19161F", "stroke": "#100D14", "lineWidth": 1.5, "opacity": 0.98},
                {"layer": target_layer, "facing": "both", "type": "rect", "x": round(wx - 3.6, 2), "y": round(wy - 2.3, 2), "w": 7.2, "h": 4.6, "radius": 1.5, "fill": "#FF3347", "opacity": 0.95},
            ])

        # 3) Gelang Identitas Pasien Rumah Sakit ICU Kakek Raka (Pergelangan Kanan)
        if self.ICU_WRISTBAND:
            wx = ra_elb[0] * 0.25 + ra_hnd[0] * 0.75
            wy = ra_elb[1] * 0.25 + ra_hnd[1] * 0.75
            target_layer = "front" if ra_depth >= -4.0 else "back"
            extras.extend([
                {"layer": target_layer, "facing": "both", "type": "ellipse", "x": round(wx, 2), "y": round(wy, 2), "rx": 6.2, "ry": 3.2, "rot": -0.2, "fill": "#E8F4FD", "stroke": "#3B7BB8", "lineWidth": 1.5, "opacity": 0.95},
            ])

        return extras

    def _render_ctx(
        self,
        frame: int = 0,
        time_sec: Optional[float] = None,
        fps: Optional[int] = None,
        angle: Optional[float] = None,
        animation: Optional[Any] = None,
        scale: Optional[float] = None,
        flip_x: bool = False,
        hide_hat: bool = False,
        config_overrides: Optional[Dict[str, Any]] = None,
        age: Optional[float] = None,
        ring_glow_boost: float = 1.0,
        **override_kwargs: Any,
    ) -> Tuple[SvgCanvas2D, Any]:
        active_fps = int(fps or self.fps)
        t = float(time_sec) if time_sec is not None else (float(frame) / max(1, active_fps))
        active_angle = self.default_angle if angle is None else float(angle)

        # 1) Apply Morph-Target Aging jika diminta (khusus Raka 26 -> 78 thn)
        merged_cfg = dict(self.get_aged_config(age) if (self.SUPPORTS_AGING and age is not None) else self.config)
        if config_overrides:
            merged_cfg.update(config_overrides)

        if self.SUPPORTS_AGING and age is not None:
            u = max(0.0, min(1.0, float(age)))
            override_kwargs.setdefault("squash_x", 1.02 - 0.12 * u)
            override_kwargs.setdefault("squash_y", 1.01 - 0.04 * u)
            override_kwargs.setdefault("pelvis_y", float(override_kwargs.get("pelvis_y") or 0.0) + 9.0 * u)
            override_kwargs.setdefault("torso_lean_deg", float(override_kwargs.get("torso_lean_deg") or 0.0) + 4.5 * u)

        # 2) Proyeksikan customLayers 3D sesuai sudut kamera
        projected_layers = project_custom_layers_3d(merged_cfg.get("customLayers"), active_angle)

        # 3) Hitung pose sendi IK terlebih dahulu bila karakter memiliki cincin/jam/gelang 3D
        if self.RING_GLOW_HAND or self.WRIST_WATCH_RED or self.ICU_WRISTBAND:
            pose_preview = self.compute_pose(
                frame=frame,
                time_sec=t,
                fps=active_fps,
                animation=animation,
                config_overrides=merged_cfg,
                **override_kwargs,
            )
            projected_layers.extend(
                self._build_hand_tracked_layers(pose_preview, active_angle, t, ring_glow_boost=ring_glow_boost)
            )

        merged_cfg["customLayers"] = projected_layers

        return super()._render_ctx(
            frame=frame,
            time_sec=t,
            fps=active_fps,
            angle=active_angle,
            animation=animation,
            scale=scale,
            flip_x=flip_x,
            hide_hat=hide_hat,
            config_overrides=merged_cfg,
            **override_kwargs,
        )
