"""
Matematika 3D, Lensa Wide-Angle 18-22mm, Kurva Gerak Kamera Sinematik
(Exponential Ease-In-Out, Speed-Ramp, Smooth Deceleration with Subtle Overshoot),
dan Fisika Pegas Sekunder.
"""

from __future__ import annotations

import math
from typing import Sequence, Tuple

import numpy as np


def vec3(x: float, y: float, z: float) -> np.ndarray:
    return np.array([float(x), float(y), float(z)], dtype=np.float32)


def normalize(v: np.ndarray) -> np.ndarray:
    n = float(np.linalg.norm(v))
    if n < 1e-8:
        return np.array([0.0, 1.0, 0.0], dtype=np.float32)
    return (v / n).astype(np.float32)


def clamp(v: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, float(v)))


def lerp(a: float, b: float, t: float) -> float:
    return float(a + (b - a) * t)


def lerp_vec(a: np.ndarray, b: np.ndarray, t: float) -> np.ndarray:
    return (a + (b - a) * float(t)).astype(np.float32)


def smoothstep(t: float) -> float:
    u = clamp(t)
    return u * u * (3.0 - 2.0 * u)


def exp_ease_in_out(t: float, power: float = 7.5) -> float:
    """Kurva exponential ease-in-out sesuai Production Bible."""
    u = clamp(t)
    if u <= 0.0:
        return 0.0
    if u >= 1.0:
        return 1.0
    if u < 0.5:
        return 0.5 * math.pow(2.0, power * (2.0 * u - 1.0))
    return 1.0 - 0.5 * math.pow(2.0, -power * (2.0 * u - 1.0))


def snappy_dolly_overshoot(t: float, overshoot: float = 0.045) -> float:
    """Snappy speed-ramped dolly-in dengan smooth deceleration & subtle overshoot halus."""
    u = clamp(t)
    if u <= 0.0:
        return 0.0
    if u >= 1.0:
        return 1.0
    # Fast exponential ramp + critically slightly underdamped settle
    base = 1.0 - math.exp(-7.2 * u)
    base_norm = base / (1.0 - math.exp(-7.2))
    ring = math.sin(u * math.pi * 1.45) * math.exp(-4.6 * u) * overshoot * 4.2
    return base_norm + ring * (1.0 - u)


def whip_curve(t: float) -> float:
    """Kurva whip-pan sangat cepat di tengah dengan akselerasi/deselerasi mulus."""
    return exp_ease_in_out(t, power=9.5)


def focal_mm_to_vfov_rad(focal_mm: float, sensor_height_mm: float = 36.0) -> float:
    """
    Konversi lensa wide-angle 18-22mm (format 9:16 vertikal full-frame portrait:
    tinggi sensor 36mm, lebar 20.25mm) ke vertical FOV radian.
    """
    return 2.0 * math.atan(sensor_height_mm / (2.0 * max(10.0, float(focal_mm))))


def perspective_matrix(vfov_rad: float, aspect: float, near: float, far: float) -> np.ndarray:
    """Matriks proyeksi perspektif RH untuk WebGPU/Vulkan/D3D12 (NDC Z: 0..1)."""
    f = 1.0 / math.tan(vfov_rad * 0.5)
    m = np.zeros((4, 4), dtype=np.float32)
    m[0, 0] = f / aspect
    m[1, 1] = f
    m[2, 2] = far / (near - far)
    m[2, 3] = (far * near) / (near - far)
    m[3, 2] = -1.0
    return m


def ortho_matrix(left: float, right: float, bottom: float, top: float, near: float, far: float) -> np.ndarray:
    """Matriks proyeksi ortografis RH untuk shadow map (NDC Z: 0..1)."""
    m = np.eye(4, dtype=np.float32)
    m[0, 0] = 2.0 / (right - left)
    m[1, 1] = 2.0 / (top - bottom)
    m[2, 2] = 1.0 / (near - far)
    m[0, 3] = -(right + left) / (right - left)
    m[1, 3] = -(top + bottom) / (top - bottom)
    m[2, 3] = near / (near - far)
    return m


def look_at_matrix(
    eye: np.ndarray,
    target: np.ndarray,
    up_hint: np.ndarray = np.array([0.0, 1.0, 0.0], dtype=np.float32),
    roll_deg: float = 0.0,
) -> np.ndarray:
    """Matriks view RH dengan dukungan penuh Dutch-tilt & 360° barrel roll."""
    f = normalize(target - eye)
    up = normalize(up_hint)
    if abs(float(np.dot(f, up))) > 0.992:
        up = np.array([0.0, 0.0, 1.0], dtype=np.float32)
    r = normalize(np.cross(f, up))
    u = normalize(np.cross(r, f))

    if abs(roll_deg) > 1e-4:
        rad = math.radians(roll_deg)
        cr, sr = math.cos(rad), math.sin(rad)
        r_rot = r * cr + u * sr
        u_rot = -r * sr + u * cr
        r, u = r_rot, u_rot

    m = np.eye(4, dtype=np.float32)
    m[0, :3] = r
    m[1, :3] = u
    m[2, :3] = -f
    m[0, 3] = -float(np.dot(r, eye))
    m[1, 3] = -float(np.dot(u, eye))
    m[2, 3] = float(np.dot(f, eye))
    return m


def mat4_trs(
    pos: Sequence[float] = (0.0, 0.0, 0.0),
    rot_deg: Sequence[float] = (0.0, 0.0, 0.0),
    scale: Sequence[float] = (1.0, 1.0, 1.0),
) -> np.ndarray:
    """Matriks model 4x4 (Translate * Rz * Ry * Rx * Scale)."""
    rx, ry, rz = [math.radians(float(a)) for a in rot_deg]
    cx, sx = math.cos(rx), math.sin(rx)
    cy, sy = math.cos(ry), math.sin(ry)
    cz, sz = math.cos(rz), math.sin(rz)

    mx = np.array([[1, 0, 0, 0], [0, cx, -sx, 0], [0, sx, cx, 0], [0, 0, 0, 1]], dtype=np.float32)
    my = np.array([[cy, 0, sy, 0], [0, 1, 0, 0], [-sy, 0, cy, 0], [0, 0, 0, 1]], dtype=np.float32)
    mz = np.array([[cz, -sz, 0, 0], [sz, cz, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]], dtype=np.float32)

    ms = np.diag([float(scale[0]), float(scale[1]), float(scale[2]), 1.0]).astype(np.float32)
    mt = np.eye(4, dtype=np.float32)
    mt[0, 3], mt[1, 3], mt[2, 3] = float(pos[0]), float(pos[1]), float(pos[2])
    return (mt @ mz @ my @ mx @ ms).astype(np.float32)


def catmull_rom(p0: np.ndarray, p1: np.ndarray, p2: np.ndarray, p3: np.ndarray, t: float) -> np.ndarray:
    u = clamp(t)
    u2 = u * u
    u3 = u2 * u
    return (
        0.5
        * (
            (2.0 * p1)
            + (-p0 + p2) * u
            + (2.0 * p0 - 5.0 * p1 + 4.0 * p2 - p3) * u2
            + (-p0 + 3.0 * p1 - 3.0 * p2 + p3) * u3
        )
    ).astype(np.float32)


def camera_relative_yaw_deg(
    char_pos: np.ndarray,
    char_facing_deg: float,
    cam_pos: np.ndarray,
) -> float:
    """
    Hitung sudut putar relatif kamera terhadap karakter (0° = menghadap kamera,
    90° = tampak samping, 180° = tampak belakang) agar karakter 2.5D berotasi mulus 360°
    mengikuti orbit virtual camera!
    """
    dx = float(cam_pos[0] - char_pos[0])
    dz = float(cam_pos[2] - char_pos[2])
    cam_az = math.degrees(math.atan2(dx, dz))
    return (cam_az - char_facing_deg) % 360.0
