"""
Unlocked Rig Controls — Semua rigging karakter & properti dibiarkan 100% TERBUKA (tidak terkunci)
agar bebas disesuaikan dengan kebutuhan koreografi di setiap adegan.

Default mode selalu `animation="static"` (pose desain netral tanpa animasi paksa),
namun seluruh sendi (IK target maupun FK raw joint), ekspresi wajah, dan tulang sekunder
(syal, jambul, benang saku, topi, ekor, lonceng, cakar) dapat dikontrol bebas per frame.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from typing import Any, Dict, Literal, Optional, Sequence, Tuple, Union

Vec3Input = Union[Tuple[float, float], Tuple[float, float, float], Dict[str, float]]


def _to_vec3(v: Vec3Input, default_z: float = 0.0, attr_dict_cls: Any = dict) -> Any:
    if isinstance(v, dict):
        return attr_dict_cls({
            "x": float(v.get("x", 0.0)),
            "y": float(v.get("y", 0.0)),
            "z": float(v.get("z", default_z)),
        })
    if len(v) == 2:
        return attr_dict_cls({"x": float(v[0]), "y": float(v[1]), "z": float(default_z)})
    return attr_dict_cls({"x": float(v[0]), "y": float(v[1]), "z": float(v[2])})


@dataclass
class HumanoidRig:
    """
    Rig 100% terbuka untuk karakter humanoid berbasis generator.html
    (Bima, Pedagang Rempah, Penumpang Trem).
    Semua field bersifat opsional (None = pakai nilai netral desain dasar).
    """

    # Arah & transformasi dasar
    angle: Optional[float] = None
    flip_x: Optional[bool] = None
    hide_hat: Optional[bool] = None
    ground_shadow: Optional[bool] = None

    # Mode animasi opsional: default "static" (tidak mengunci gerakan apa pun!)
    animation: Optional[str] = None
    pose: Optional[str] = None
    prop: Optional[str] = None

    # Root, Torso & Squash-Stretch
    pelvis_y: Optional[float] = None
    jump_height: Optional[float] = None
    torso_lean_z: Optional[float] = None
    squash_x: Optional[float] = None
    squash_y: Optional[float] = None

    # Kepala & Ekspresi Wajah (bebas diubah per adegan/frame)
    head_bob_y: Optional[float] = None
    head_tilt: Optional[float] = None
    eyes: Optional[str] = None
    eyebrows: Optional[str] = None
    mouth: Optional[str] = None
    mouth_open: Optional[float] = None
    blink: Optional[float] = None
    eye_gaze_x: Optional[float] = None
    eye_gaze_y: Optional[float] = None
    sweat_drop: Optional[bool] = None
    blush: Optional[bool] = None
    anger_vein: Optional[bool] = None
    dizzy_stars: Optional[float] = None

    # Topi & Secondary Spring Bones (100% manual-overridable oleh fisika adegan!)
    hat_tilt: Optional[float] = None
    hat_lift_y: Optional[float] = None
    scarf_sway: Optional[float] = None
    jambul_sway: Optional[float] = None
    braid_sway: Optional[float] = None
    thread_sway: Optional[float] = None

    # Target IK 2-Tulang (bebas posisikan tangan & kaki ke koordinat adegan!)
    left_hand_target: Optional[Vec3Input] = None
    right_hand_target: Optional[Vec3Input] = None
    left_foot_target: Optional[Vec3Input] = None
    right_foot_target: Optional[Vec3Input] = None
    left_elbow_bend: Tuple[float, float] = (-1.0, 0.25)
    right_elbow_bend: Tuple[float, float] = (1.0, 0.25)

    # Override FK Langsung per Sendi (mis. {"laSh": (...), "laElb": (...), "laHnd": (...),
    # "raSh": (...), "raElb": (...), "raHnd": (...), "lHip": (...), "lKnee": (...),
    # "lAnkle": (...), "lToe": (...), "rHip": (...), "rKnee": (...), "rAnkle": (...), "rToe": (...)})
    joints: Dict[str, Vec3Input] = field(default_factory=dict)

    # Kontrol Khusus Adegan Bima / Pencahayaan
    lighting_phase: Optional[str] = None
    silver_key_peek: Optional[bool] = None
    config_overrides: Dict[str, Any] = field(default_factory=dict)


@dataclass
class OrenRig:
    """
    Rig 100% terbuka untuk karakter 'Oren' (Kucing Kampung Gang Kafe).
    Tidak ada animasi terkunci — semua sendi, cakar, kelopak mata, ekor, dan lonceng bebas diatur per adegan.
    """

    angle: float = 0.0
    body_bob: float = 0.0
    body_lean: float = 0.0
    squash_x: float = 1.0
    squash_y: float = 1.0
    ground_shadow: bool = True

    # Kepala, Telinga & Ekspresi
    head_offset_x: float = 0.0
    head_offset_y: float = 0.0
    head_tilt: float = 0.0
    ear_left_twitch: float = 0.0
    ear_right_twitch: float = 0.0
    eyelid_level: float = 0.52  # 0.0 = melotot lebar, 0.52 = heavy-lidded arogan, 1.0 = terpejam
    blink: float = 0.0
    gaze_x: float = 0.0
    gaze_y: float = 0.0
    mouth_style: Literal["smug", "neutral", "open_meow", "hiss"] = "smug"

    # Cakar Depan Kiri & Kanan (bebas digerakkan untuk [CAM 12]-[CAM 13] atau adegan lain!)
    left_paw_offset: Tuple[float, float] = (0.0, 0.0)
    right_paw_raised: float = 0.0  # 0.0 = duduk netral, >0.0 = mengangkat cakar menepis
    right_paw_target: Optional[Tuple[float, float]] = None  # koordinat kanvas langsung (opsional)
    right_paw_rot: float = 0.30
    right_paw_scale: float = 1.0
    show_paw_pads: bool = False
    claws_out: float = 0.0  # 0.0 = tersimpan, 1.0 = cakar keluar penuh

    # Tulang Sekunder (ekor pegas, lonceng penyok, kumis)
    tail_sway: float = 0.0
    tail_curl: float = 0.0
    bell_sway: float = 0.0
    whisker_droop: float = 0.0

    # Pencahayaan
    rim_intensity: float = 1.15
    rim_color: str = "#FFE4A0"


@dataclass
class KeyPropRig:
    """Kontrol 3D terbuka untuk Kunci Emas & Kunci Perak di setiap gerakan kamera."""

    yaw_deg: float = 0.0
    pitch_deg: float = 0.0
    roll_deg: float = 0.0
    sun_glow: bool = True
    glow_intensity: float = 1.0
    sparkle_alpha: float = 1.0
    extrude_depth: float = 1.0
    lighting_phase: Literal["phase1", "phase2", "phase3_crimson", "phase3_twilight"] = "phase1"


def apply_humanoid_rig_to_pose(
    pose_obj: Any,
    rig: Optional[HumanoidRig],
    anim_mode: str,
    eng_module: Any,
) -> Any:
    """
    Terapkan override HumanoidRig secara langsung ke pose skeleton generator.html.
    Pada mode 'static', matikan auto-blink / auto-drift agar desain 100% bebas kunci.
    """
    if anim_mode == "static":
        pose_obj.blink = 0.0

    if rig is None:
        return pose_obj

    if rig.pelvis_y is not None:
        dy = float(rig.pelvis_y) - float(pose_obj.pelvisY)
        pose_obj.pelvisY = float(rig.pelvis_y)
        pose_obj.lHip.y += dy
        pose_obj.rHip.y += dy
        pose_obj.laSh.y += dy
        pose_obj.raSh.y += dy
    if rig.jump_height is not None:
        pose_obj.jumpHeight = float(rig.jump_height)
    if rig.torso_lean_z is not None:
        pose_obj.torsoLeanZ = float(rig.torso_lean_z)
    if rig.head_bob_y is not None:
        pose_obj.headBobY = float(rig.head_bob_y)
    if rig.head_tilt is not None:
        pose_obj.headTilt = float(rig.head_tilt)
    if rig.squash_x is not None:
        pose_obj.squashX = float(rig.squash_x)
    if rig.squash_y is not None:
        pose_obj.squashY = float(rig.squash_y)
    if rig.mouth_open is not None:
        pose_obj.mouthOpen = max(0.0, min(1.0, float(rig.mouth_open)))
    if rig.blink is not None:
        pose_obj.blink = max(0.0, min(1.0, float(rig.blink)))
    if rig.eye_gaze_x is not None:
        pose_obj.gazeX = float(rig.eye_gaze_x)
    if rig.eye_gaze_y is not None:
        pose_obj.gazeY = float(rig.eye_gaze_y)
    if rig.dizzy_stars is not None:
        pose_obj.dizzyStars = max(0.0, min(1.0, float(rig.dizzy_stars)))

    # Secondary spring bones (100% terbuka!)
    if rig.scarf_sway is not None:
        pose_obj.capeSway = float(rig.scarf_sway)
    if rig.jambul_sway is not None:
        pose_obj.featherSway = float(rig.jambul_sway)
    if rig.braid_sway is not None:
        pose_obj.braidSway = float(rig.braid_sway)

    # IK Targets dengan bend direction fleksibel
    if rig.left_hand_target is not None:
        t_l = _to_vec3(rig.left_hand_target, 26.0, eng_module._AttrDict)
        pose_obj.laSh = eng_module._AttrDict({
            "x": pose_obj.laSh.x + (t_l.x - pose_obj.laSh.x) * 0.12,
            "y": pose_obj.laSh.y + (t_l.y - pose_obj.laSh.y) * 0.10,
            "z": pose_obj.laSh.z + (t_l.z - pose_obj.laSh.z) * 0.10,
        })
        pose_obj.laHnd = t_l
        pose_obj.laElb = eng_module.solveArmIK(
            pose_obj.laSh, pose_obj.laHnd, 52, 50, rig.left_elbow_bend[0], rig.left_elbow_bend[1]
        )

    if rig.right_hand_target is not None:
        t_r = _to_vec3(rig.right_hand_target, 26.0, eng_module._AttrDict)
        pose_obj.raSh = eng_module._AttrDict({
            "x": pose_obj.raSh.x + (t_r.x - pose_obj.raSh.x) * 0.12,
            "y": pose_obj.raSh.y + (t_r.y - pose_obj.raSh.y) * 0.10,
            "z": pose_obj.raSh.z + (t_r.z - pose_obj.raSh.z) * 0.10,
        })
        pose_obj.raHnd = t_r
        pose_obj.raElb = eng_module.solveArmIK(
            pose_obj.raSh, pose_obj.raHnd, 52, 50, rig.right_elbow_bend[0], rig.right_elbow_bend[1]
        )

    if rig.left_foot_target is not None:
        t_lf = _to_vec3(rig.left_foot_target, -8.0, eng_module._AttrDict)
        pose_obj.lAnkle = t_lf
        pose_obj.lToe = eng_module._AttrDict({"x": t_lf.x - 14.0, "y": t_lf.y + 5.5, "z": t_lf.z + 18.0})
        pose_obj.lKnee = eng_module.solveLegIK(pose_obj.lHip, pose_obj.lAnkle, 72, 76, -5)

    if rig.right_foot_target is not None:
        t_rf = _to_vec3(rig.right_foot_target, 10.0, eng_module._AttrDict)
        pose_obj.rAnkle = t_rf
        pose_obj.rToe = eng_module._AttrDict({"x": t_rf.x - 15.0, "y": t_rf.y + 5.5, "z": t_rf.z + 18.0})
        pose_obj.rKnee = eng_module.solveLegIK(pose_obj.rHip, pose_obj.rAnkle, 74, 78, 4)

    # Override FK langsung per sendi (100% kendali manual!)
    valid_joints = {
        "lHip", "lKnee", "lAnkle", "lToe",
        "rHip", "rKnee", "rAnkle", "rToe",
        "laSh", "laElb", "laHnd",
        "raSh", "raElb", "raHnd",
    }
    for jname, jval in (rig.joints or {}).items():
        if jname in valid_joints:
            pose_obj[jname] = _to_vec3(jval, 0.0, eng_module._AttrDict)

    return pose_obj


def rig_to_render_kwargs(rig: Optional[HumanoidRig], extra_kwargs: Dict[str, Any]) -> Dict[str, Any]:
    """Konversi HumanoidRig ke kwargs render_svg/render_pil tanpa mengunci parameter."""
    out = dict(extra_kwargs)
    if rig is None:
        return out
    mapping = {
        "angle": rig.angle,
        "animation": rig.animation,
        "pose": rig.pose,
        "prop": rig.prop,
        "eyes": rig.eyes,
        "eyebrows": rig.eyebrows,
        "mouth": rig.mouth,
        "mouth_open": rig.mouth_open,
        "blink": rig.blink,
        "eye_gaze_x": rig.eye_gaze_x,
        "eye_gaze_y": rig.eye_gaze_y,
        "sweat_drop": rig.sweat_drop,
        "blush": rig.blush,
        "anger_vein": rig.anger_vein,
        "hat_tilt": rig.hat_tilt,
        "hat_lift_y": rig.hat_lift_y,
        "head_tilt": rig.head_tilt,
        "squash_x": rig.squash_x,
        "squash_y": rig.squash_y,
        "ground_shadow": rig.ground_shadow,
        "flip_x": rig.flip_x,
        "hide_hat": rig.hide_hat,
    }
    for k, v in mapping.items():
        if v is not None and k not in out:
            out[k] = v
    return out


class UnlockedHumanoidCharacter:
    """
    Adapter 100% terbuka untuk karakter ekspor generator.html mana pun
    (mis. PedagangRempahCharacter, PenumpangTremCharacter, atau BimaCharacter murni).
    Default selalu 'static' (desain netral) dan menerima `rig=HumanoidRig(...)` untuk setiap adegan.
    """

    def __init__(
        self,
        eng_module: Any,
        char_cls_name: str,
        scale: float = 3.0,
        fps: int = 30,
        config_overrides: Optional[Dict[str, Any]] = None,
    ) -> None:
        self._mod = eng_module
        self._cls = getattr(eng_module, char_cls_name)
        self.scale = float(scale)
        self.fps = int(fps)
        self.base_config = copy.deepcopy(eng_module.CHARACTER_CONFIG)
        if config_overrides:
            self.base_config.update(config_overrides)

    def render_svg(
        self,
        frame: int = 0,
        angle: float = 0.0,
        animation: str = "static",
        rig: Optional[HumanoidRig] = None,
        **kwargs: Any,
    ) -> str:
        cfg = copy.deepcopy(self.base_config)
        if rig and rig.config_overrides:
            cfg.update(rig.config_overrides)
        merged_kw = rig_to_render_kwargs(rig, kwargs)
        active_anim = merged_kw.pop("animation", animation) or "static"
        active_angle = merged_kw.pop("angle", angle)

        orig_pose = self._mod.computeSkeletonPose

        def hooked_pose(c_cfg: Any, animMode: str, rawT: float, overrides: Any = None) -> Any:
            p = orig_pose(c_cfg, animMode, rawT, overrides)
            return apply_humanoid_rig_to_pose(p, rig, animMode, self._mod)

        self._mod.computeSkeletonPose = hooked_pose
        try:
            char = self._cls(scale=self.scale, fps=self.fps, default_animation="static", config_overrides=cfg)
            return char.render_svg(frame=frame, angle=active_angle, animation=active_anim, **merged_kw)
        finally:
            self._mod.computeSkeletonPose = orig_pose

    def render_pil(
        self,
        frame: int = 0,
        angle: float = 0.0,
        animation: str = "static",
        rig: Optional[HumanoidRig] = None,
        **kwargs: Any,
    ) -> Any:
        import io
        import resvg_py
        from PIL import Image

        svg_str = self.render_svg(frame=frame, angle=angle, animation=animation, rig=rig, **kwargs)
        png_bytes = resvg_py.svg_to_bytes(svg_string=svg_str, skip_system_fonts=True)
        return Image.open(io.BytesIO(png_bytes)).convert("RGBA")
