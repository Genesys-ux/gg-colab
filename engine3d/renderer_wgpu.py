"""
True 3D WebGPU (wgpu / DirectX 12 / Vulkan) Cel-Shaded + Procedural PBR Renderer.

Pipeline 3-Pass GPU per frame:
  1. Shadow Map Pass (1536x1536 depth32float) -> bayangan panjang tajam dari Low Sun / Tungku / Crimson Sun
  2. 3D Scene Pass (HDR rgba16float + GBuffer normal/depth + depth32float):
       - Langit gradien 3-stop + piringan matahari & kabut atmosfer
       - Mesh 3D Cel-Shaded 3-tingkat + tekstur PBR prosedural (kayu retak, cat terkelupas,
         kuningan tergores, tenun kasar, kaca berdebu, cobblestone basah, tembaga teroksidasi)
       - Depth-tested 3D Alpha Billboards (Bima, Oren, Kunci Emas/Perak, Figuran, Partikel 3D)
  3. Post-Process Pass (rgba8unorm):
       - Distance-mapped Adaptive Dark Ink Outlines (Sobel normal + depth)
       - Clean Directional Motion Blur (whip-pan & speed-ramp plunge)
       - Radial Shockwave Ring ([CAM 18] & [CAM 26]) + Filmic Cartoon Tone-Map + Hidden Wipe Cut
"""

from __future__ import annotations

import struct
from dataclasses import dataclass
from typing import List, Optional, Tuple

import numpy as np
import wgpu
from PIL import Image

from .lighting import LightingState
from .math3d import look_at_matrix, normalize, ortho_matrix

SHADOW_SIZE = 1536

SHADOW_WGSL = """
struct ShadowUniforms {
    light_vp: mat4x4<f32>,
};
@group(0) @binding(0) var<uniform> u: ShadowUniforms;

struct VertIn {
    @location(0) pos: vec3<f32>,
    @location(1) nrm: vec3<f32>,
    @location(2) uv: vec2<f32>,
    @location(3) col: vec3<f32>,
    @location(4) mat_id: f32,
};

@vertex
fn vs_main(v: VertIn) -> @builtin(position) vec4<f32> {
    return u.light_vp * vec4<f32>(v.pos, 1.0);
}
"""

SKY_WGSL = """
struct SceneUniforms {
    vp: mat4x4<f32>,
    inv_vp: mat4x4<f32>,
    light_vp: mat4x4<f32>,
    cam_pos: vec4<f32>,
    sun_dir_int: vec4<f32>,
    sun_col_disc: vec4<f32>,
    shade_col_pad: vec4<f32>,
    ambient_col_pad: vec4<f32>,
    rim_col_int: vec4<f32>,
    fog_col_den: vec4<f32>,
    sky_top: vec4<f32>,
    sky_mid: vec4<f32>,
    sky_hor: vec4<f32>,
    sun_disc_col: vec4<f32>,
    pt_pos_int: vec4<f32>,
    pt_col_pad: vec4<f32>,
    time_flags: vec4<f32>,
};
@group(0) @binding(0) var<uniform> u: SceneUniforms;

struct VsOut {
    @builtin(position) clip_pos: vec4<f32>,
    @location(0) ndc: vec2<f32>,
};

@vertex
fn vs_main(@builtin(vertex_index) vi: u32) -> VsOut {
    var pts = array<vec2<f32>, 3>(
        vec2<f32>(-1.0, -1.0),
        vec2<f32>( 3.0, -1.0),
        vec2<f32>(-1.0,  3.0)
    );
    var out: VsOut;
    out.ndc = pts[vi];
    out.clip_pos = vec4<f32>(pts[vi], 0.9999, 1.0);
    return out;
}

struct FsOut {
    @location(0) color: vec4<f32>,
    @location(1) gbuf: vec4<f32>,
};

@fragment
fn fs_main(in: VsOut) -> FsOut {
    let p_far = u.inv_vp * vec4<f32>(in.ndc, 1.0, 1.0);
    let world_dir = normalize(p_far.xyz / p_far.w - u.cam_pos.xyz);
    let y = clamp(world_dir.y, -0.35, 1.0);

    let sky_hor_lin = pow(max(u.sky_hor.rgb, vec3<f32>(0.0)), vec3<f32>(2.2));
    let sky_mid_lin = pow(max(u.sky_mid.rgb, vec3<f32>(0.0)), vec3<f32>(2.2));
    let sky_top_lin = pow(max(u.sky_top.rgb, vec3<f32>(0.0)), vec3<f32>(2.2));
    let fog_lin = pow(max(u.fog_col_den.rgb, vec3<f32>(0.0)), vec3<f32>(2.2));

    var sky = mix(sky_hor_lin, sky_mid_lin, smoothstep(-0.02, 0.28, y));
    sky = mix(sky, sky_top_lin, smoothstep(0.24, 0.78, y));
    // Warm/cool haze below horizon
    sky = mix(fog_lin * 0.75, sky, smoothstep(-0.22, 0.02, y));

    // Stylized cloud ribbons in upper sky
    let cloud_u = world_dir.x * 3.5 + u.time_flags.x * 0.015;
    let cloud_v = world_dir.z * 2.2;
    let cwave = sin(cloud_u * 2.1 + sin(cloud_v * 1.7)) * cos(cloud_v * 2.3 - cloud_u * 0.9);
    let cloud_mask = smoothstep(0.32, 0.72, cwave) * smoothstep(0.06, 0.25, y) * (1.0 - smoothstep(0.45, 0.82, y));
    let cloud_col = mix(sky_hor_lin, vec3<f32>(1.0, 0.90, 0.72), 0.35);
    sky = mix(sky, cloud_col, cloud_mask * 0.24);

    // Glowing low sun disc & volumetric halo
    let sun_dir = normalize(u.sun_dir_int.xyz);
    let disc_sz = u.sun_col_disc.w;
    if (disc_sz > 0.001) {
        let dot_s = max(dot(world_dir, sun_dir), 0.0);
        let halo = pow(dot_s, 10.0) * 0.60 + pow(dot_s, 44.0) * 1.1;
        let ang = acos(clamp(dot_s, -1.0, 1.0));
        let disc = 1.0 - smoothstep(disc_sz * 0.84, disc_sz, ang);
        let disc_lin = pow(max(u.sun_disc_col.rgb, vec3<f32>(0.0)), vec3<f32>(2.2));
        sky = sky + disc_lin * (halo * 0.75 + disc * 2.2);
    }

    var out: FsOut;
    out.color = vec4<f32>(sky, 1.0);
    // Sentinel depth = 500.0 menandakan langit (tidak digarisi ink outline)
    out.gbuf = vec4<f32>(0.0, 0.0, 1.0, 500.0);
    return out;
}
"""

MESH_WGSL = """
struct SceneUniforms {
    vp: mat4x4<f32>,
    inv_vp: mat4x4<f32>,
    light_vp: mat4x4<f32>,
    cam_pos: vec4<f32>,
    sun_dir_int: vec4<f32>,
    sun_col_disc: vec4<f32>,
    shade_col_pad: vec4<f32>,
    ambient_col_pad: vec4<f32>,
    rim_col_int: vec4<f32>,
    fog_col_den: vec4<f32>,
    sky_top: vec4<f32>,
    sky_mid: vec4<f32>,
    sky_hor: vec4<f32>,
    sun_disc_col: vec4<f32>,
    pt_pos_int: vec4<f32>,
    pt_col_pad: vec4<f32>,
    time_flags: vec4<f32>,
};
@group(0) @binding(0) var<uniform> u: SceneUniforms;
@group(0) @binding(1) var shadow_tex: texture_depth_2d;

struct VertIn {
    @location(0) pos: vec3<f32>,
    @location(1) nrm: vec3<f32>,
    @location(2) uv: vec2<f32>,
    @location(3) col: vec3<f32>,
    @location(4) mat_id: f32,
};

struct VsOut {
    @builtin(position) clip_pos: vec4<f32>,
    @location(0) world_pos: vec3<f32>,
    @location(1) world_nrm: vec3<f32>,
    @location(2) uv: vec2<f32>,
    @location(3) col: vec3<f32>,
    @location(4) mat_id: f32,
    @location(5) shadow_pos: vec4<f32>,
};

@vertex
fn vs_main(v: VertIn) -> VsOut {
    var out: VsOut;
    out.clip_pos = u.vp * vec4<f32>(v.pos, 1.0);
    out.world_pos = v.pos;
    out.world_nrm = v.nrm;
    out.uv = v.uv;
    out.col = v.col;
    out.mat_id = v.mat_id;
    out.shadow_pos = u.light_vp * vec4<f32>(v.pos + v.nrm * 0.04, 1.0);
    return out;
}

fn hash21(p: vec2<f32>) -> f32 {
    let p3 = fract(vec3<f32>(p.x, p.y, p.x) * 0.1031);
    let q = p3 + dot(p3, p3.yzx + 33.33);
    return fract((q.x + q.y) * q.z);
}

fn vnoise(p: vec2<f32>) -> f32 {
    let i = floor(p);
    let f = fract(p);
    let u2 = f * f * (3.0 - 2.0 * f);
    let a = hash21(i);
    let b = hash21(i + vec2<f32>(1.0, 0.0));
    let c = hash21(i + vec2<f32>(0.0, 1.0));
    let d = hash21(i + vec2<f32>(1.0, 1.0));
    return mix(mix(a, b, u2.x), mix(c, d, u2.x), u2.y);
}

fn sample_shadow(sh_pos: vec4<f32>) -> f32 {
    let proj = sh_pos.xyz / max(sh_pos.w, 0.0001);
    let uv = vec2<f32>(proj.x * 0.5 + 0.5, 0.5 - proj.y * 0.5);
    if (uv.x < 0.01 || uv.x > 0.99 || uv.y < 0.01 || uv.y > 0.99 || proj.z < 0.0 || proj.z > 1.0) {
        return 1.0;
    }
    let dims = vec2<f32>(textureDimensions(shadow_tex));
    let base_px = vec2<i32>(uv * dims);
    let bias = 0.0022;
    var lit = 0.0;
    for (var ox: i32 = -1; ox <= 1; ox = ox + 1) {
        for (var oy: i32 = -1; oy <= 1; oy = oy + 1) {
            let p = clamp(base_px + vec2<i32>(ox, oy), vec2<i32>(0, 0), vec2<i32>(dims) - vec2<i32>(1, 1));
            let d = textureLoad(shadow_tex, p, 0);
            if (proj.z - bias <= d) {
                lit = lit + 1.0;
            }
        }
    }
    return lit / 9.0;
}

struct FsOut {
    @location(0) color: vec4<f32>,
    @location(1) gbuf: vec4<f32>,
};

@fragment
fn fs_main(in: VsOut) -> FsOut {
    let N = normalize(in.world_nrm);
    let V = normalize(u.cam_pos.xyz - in.world_pos);
    let L = normalize(u.sun_dir_int.xyz);
    let mat = i32(in.mat_id + 0.5);

    // Konversi warna sRGB -> Linear agar kontras cel-shading & warna properti kaya (tidak pucat!)
    var albedo = pow(max(in.col, vec3<f32>(0.0)), vec3<f32>(2.2));
    let sun_col_lin = pow(max(u.sun_col_disc.rgb, vec3<f32>(0.0)), vec3<f32>(2.2));
    let shade_col_lin = pow(max(u.shade_col_pad.rgb, vec3<f32>(0.0)), vec3<f32>(2.2));
    let ambient_col_lin = pow(max(u.ambient_col_pad.rgb, vec3<f32>(0.0)), vec3<f32>(2.2));
    let rim_col_lin = pow(max(u.rim_col_int.rgb, vec3<f32>(0.0)), vec3<f32>(2.2));
    let fog_col_lin = pow(max(u.fog_col_den.rgb, vec3<f32>(0.0)), vec3<f32>(2.2));
    let pt_col_lin = pow(max(u.pt_col_pad.rgb, vec3<f32>(0.0)), vec3<f32>(2.2));
    let sky_mid_lin = pow(max(u.sky_mid.rgb, vec3<f32>(0.0)), vec3<f32>(2.2));

    var spec_strength = 0.16;
    var spec_power = 28.0;
    var bump = 0.0;

    // Procedural PBR Micro-Surface Detail (digabungkan dengan Cel-Shading!)
    let wp = in.world_pos;
    let tp = in.uv;
    if (mat == 0) {
        // 0: Cracked Oak Wood — serat kayu & sambungan papan
        let grain = sin(tp.x * 26.0 + vnoise(tp * 5.0) * 6.0) * 0.5 + 0.5;
        let plank = smoothstep(0.03, 0.07, fract(tp.y * 2.2));
        let crack = smoothstep(0.84, 0.93, vnoise(tp * 14.0));
        albedo = albedo * mix(0.68, 1.12, grain) * mix(0.45, 1.0, plank) * mix(1.0, 0.42, crack);
        spec_strength = 0.22;
        spec_power = 22.0;
        bump = (grain - 0.5) * 0.16;
    } else if (mat == 1) {
        // 1: Peeling Painted Plaster / Stone — cat mengelupas & retak dinding
        let n1 = vnoise(wp.xy * 1.8 + wp.zz * 1.4);
        let n2 = vnoise(wp.xz * 7.5 + wp.yy * 5.0);
        let peel = smoothstep(0.68, 0.74, n1);
        albedo = mix(albedo * mix(0.84, 1.08, n2), vec3<f32>(0.24, 0.14, 0.09), peel * 0.46);
        spec_strength = 0.08;
        bump = (n2 - 0.5) * 0.22;
    } else if (mat == 2) {
        // 2: Scratched Brass / Antique Gold Metal — goresan logam & patina lekukan
        let scratch = vnoise(vec2<f32>(tp.x * 38.0, tp.y * 5.0));
        let patina = vnoise(wp.xy * 3.5 + wp.z * 2.5);
        albedo = albedo * mix(0.72, 1.18, scratch) * mix(0.68, 1.06, patina);
        spec_strength = 0.95;
        spec_power = 42.0;
        bump = (scratch - 0.5) * 0.14;
    } else if (mat == 3) {
        // 3: Coarse Woven Fabric / Awning / Burlap — serat tenun silang
        let wx = sin(tp.x * 58.0) * 0.5 + 0.5;
        let wy = sin(tp.y * 58.0) * 0.5 + 0.5;
        let weave = (wx + wy) * 0.5;
        albedo = albedo * mix(0.78, 1.10, weave);
        spec_strength = 0.05;
        bump = (weave - 0.5) * 0.18;
    } else if (mat == 4) {
        // 4: Dusty Glass / Clock Dial — kaca berdebu + kilau Fresnel
        let dust = vnoise(tp * 9.0);
        let fres = pow(1.0 - max(dot(N, V), 0.0), 3.0);
        albedo = mix(albedo, vec3<f32>(0.88, 0.84, 0.72), dust * 0.16 + fres * 0.42);
        spec_strength = 0.95;
        spec_power = 64.0;
    } else if (mat == 5) {
        // 5: Wet Cobblestone — grid batu basah memantulkan langit
        let gx = fract(wp.x * 2.6 + floor(wp.z * 2.6) * 0.5);
        let gz = fract(wp.z * 2.6);
        let joint = smoothstep(0.05, 0.12, gx) * smoothstep(0.05, 0.12, gz) * smoothstep(0.05, 0.12, 1.0 - gx) * smoothstep(0.05, 0.12, 1.0 - gz);
        let wet = vnoise(wp.xz * 1.4);
        albedo = albedo * mix(0.36, 1.06, joint);
        albedo = mix(albedo, sky_mid_lin * 0.85, wet * 0.28 * max(N.y, 0.0));
        spec_strength = mix(0.32, 0.96, wet);
        spec_power = 48.0;
        bump = (1.0 - joint) * -0.25;
    } else if (mat == 6) {
        // 6: Oxidized Copper / Rusted Iron — patina hijau verdigris & karat
        let ox = vnoise(wp.xy * 2.4 + wp.zz * 2.0);
        let streak = vnoise(vec2<f32>(wp.x * 6.0, wp.y * 1.4));
        albedo = mix(albedo, vec3<f32>(0.04, 0.30, 0.22), smoothstep(0.55, 0.78, ox * streak * 1.5) * 0.58);
        spec_strength = 0.48;
        spec_power = 30.0;
    } else if (mat == 7) {
        // 7: Emissive Furnace / Lamp / Glowing Core — menyala penuh
        let pulse = 0.92 + 0.08 * sin(u.time_flags.x * 7.5 + wp.y * 2.0);
        var out_e: FsOut;
        out_e.color = vec4<f32>(albedo * 2.8 * pulse, 1.0);
        out_e.gbuf = vec4<f32>(N, length(u.cam_pos.xyz - wp));
        return out_e;
    } else {
        // 8: Vibrant Painted Prop / Fruit / Ceramic
        let fine = vnoise(tp * 10.0);
        albedo = albedo * mix(0.90, 1.06, fine);
        spec_strength = 0.36;
        spec_power = 36.0;
    }

    // 3-Tier Stepped Cel-Shading + Real 3D Shadow Map!
    let ndotl_raw = dot(N, L) + bump * 0.35;
    let shadow = sample_shadow(in.shadow_pos);
    let lit_val = ndotl_raw * mix(0.14, 1.0, shadow);

    var cel_band = 0.0;
    if (lit_val > 0.40) {
        cel_band = 1.0;
    } else if (lit_val > 0.07) {
        cel_band = 0.50;
    } else {
        cel_band = 0.0;
    }
    cel_band = mix(
        smoothstep(0.04, 0.10, lit_val) * 0.50 + smoothstep(0.37, 0.44, lit_val) * 0.50,
        cel_band,
        0.65
    );

    let lit_color = albedo * sun_col_lin * u.sun_dir_int.w;
    let shade_color = albedo * mix(shade_col_lin, ambient_col_lin, 0.32) * 1.35;
    var color = mix(shade_color, lit_color, cel_band);

    // Pita Specular Cel-Shaded tegas
    let H = normalize(L + V);
    let sp = pow(max(dot(N, H), 0.0), spec_power);
    let cel_spec = smoothstep(0.28, 0.40, sp) * spec_strength * shadow;
    color = color + sun_col_lin * cel_spec * 0.95;

    // Local Point Light (Tungku Bawah Tanah / Lampu Meja / Percikan Kunci / Pusat Jam!)
    let pt_vec = u.pt_pos_int.xyz - wp;
    let pt_dist = length(pt_vec);
    let pt_att = u.pt_pos_int.w / (1.0 + 0.032 * pt_dist * pt_dist);
    let pt_ndotl = smoothstep(-0.08, 0.32, dot(N, pt_vec / max(pt_dist, 0.001)));
    color = color + albedo * pt_col_lin * pt_ndotl * pt_att * 1.65;

    // Fresnel Rim Light tegas mengikuti Fase Pencahayaan (Warm Gold / Furnace Orange / Crisp Cyan!)
    let fresnel = pow(1.0 - max(dot(N, V), 0.0), 3.0);
    let rim_gate = smoothstep(0.34, 0.62, fresnel) * (0.40 + 0.60 * max(dot(N, L) * 0.5 + 0.5, 0.25));
    color = color + rim_col_lin * rim_gate * u.rim_col_int.w * 0.72;

    // Volumetric Atmospheric Haze (Golden / Emerald Steam / Golden-Crimson / Twilight)
    let dist = length(u.cam_pos.xyz - wp);
    let fog_amt = 1.0 - exp(-dist * u.fog_col_den.w);
    color = mix(color, fog_col_lin, clamp(fog_amt * 0.80, 0.0, 0.84));

    var out: FsOut;
    out.color = vec4<f32>(color, 1.0);
    out.gbuf = vec4<f32>(N, dist);
    return out;
}
"""

BILLBOARD_WGSL = """
struct SceneUniforms {
    vp: mat4x4<f32>,
    inv_vp: mat4x4<f32>,
    light_vp: mat4x4<f32>,
    cam_pos: vec4<f32>,
    sun_dir_int: vec4<f32>,
    sun_col_disc: vec4<f32>,
    shade_col_pad: vec4<f32>,
    ambient_col_pad: vec4<f32>,
    rim_col_int: vec4<f32>,
    fog_col_den: vec4<f32>,
    sky_top: vec4<f32>,
    sky_mid: vec4<f32>,
    sky_hor: vec4<f32>,
    sun_disc_col: vec4<f32>,
    pt_pos_int: vec4<f32>,
    pt_col_pad: vec4<f32>,
    time_flags: vec4<f32>,
};
struct BillboardUniforms {
    tint: vec4<f32>,      // rgb tint + alpha mult
    fog_mult: vec4<f32>,  // x = fog scale, y = emissive boost
};
@group(0) @binding(0) var<uniform> u: SceneUniforms;
@group(1) @binding(0) var<uniform> b: BillboardUniforms;
@group(1) @binding(1) var sprite_tex: texture_2d<f32>;
@group(1) @binding(2) var sprite_samp: sampler;

struct VertIn {
    @location(0) pos: vec3<f32>,
    @location(1) uv: vec2<f32>,
};

struct VsOut {
    @builtin(position) clip_pos: vec4<f32>,
    @location(0) world_pos: vec3<f32>,
    @location(1) uv: vec2<f32>,
};

@vertex
fn vs_main(v: VertIn) -> VsOut {
    var out: VsOut;
    out.clip_pos = u.vp * vec4<f32>(v.pos, 1.0);
    out.world_pos = v.pos;
    out.uv = v.uv;
    return out;
}

struct FsOut {
    @location(0) color: vec4<f32>,
    @location(1) gbuf: vec4<f32>,
};

@fragment
fn fs_main(in: VsOut) -> FsOut {
    let texel = textureSample(sprite_tex, sprite_samp, in.uv);
    let alpha_cut = b.fog_mult.z;
    if (texel.a < alpha_cut) {
        discard;
    }
    let dist = length(u.cam_pos.xyz - in.world_pos);
    let fog_amt = (1.0 - exp(-dist * u.fog_col_den.w)) * b.fog_mult.x;
    let fog_lin = pow(max(u.fog_col_den.rgb, vec3<f32>(0.0)), vec3<f32>(2.2));
    var rgb = texel.rgb * b.tint.rgb * (1.0 + b.fog_mult.y);
    rgb = mix(rgb, fog_lin, clamp(fog_amt, 0.0, 0.72));

    var out: FsOut;
    out.color = vec4<f32>(rgb, texel.a * b.tint.a);
    // Tandai depth = 499.0 agar Sobel mesh outline tidak menggandakan garis ink karakter!
    out.gbuf = vec4<f32>(0.0, 0.0, 1.0, 499.0);
    return out;
}
"""

POST_WGSL = """
struct PostUniforms {
    blur_vec_sw: vec4<f32>,    // xy = directional motion blur UV vector, z = shockwave radius, w = shockwave alpha
    sw_col_exp: vec4<f32>,     // rgb = shockwave color, w = exposure
    flags: vec4<f32>,          // x = black_wipe (0..1), y = outline_strength, z = aspect (w/h), w = time
};
@group(0) @binding(0) var<uniform> p: PostUniforms;
@group(0) @binding(1) var color_tex: texture_2d<f32>;
@group(0) @binding(2) var gbuf_tex: texture_2d<f32>;
@group(0) @binding(3) var lin_samp: sampler;

struct VsOut {
    @builtin(position) clip_pos: vec4<f32>,
    @location(0) uv: vec2<f32>,
};

@vertex
fn vs_main(@builtin(vertex_index) vi: u32) -> VsOut {
    var pts = array<vec2<f32>, 3>(
        vec2<f32>(-1.0, -1.0),
        vec2<f32>( 3.0, -1.0),
        vec2<f32>(-1.0,  3.0)
    );
    var out: VsOut;
    out.clip_pos = vec4<f32>(pts[vi], 0.0, 1.0);
    out.uv = vec2<f32>(pts[vi].x * 0.5 + 0.5, 0.5 - pts[vi].y * 0.5);
    return out;
}

@fragment
fn fs_main(in: VsOut) -> @location(0) vec4<f32> {
    let dims = vec2<f32>(textureDimensions(color_tex));
    let px = 1.0 / dims;

    // 1. Clean Directional Motion Blur (whip-pan & high-speed plunge!)
    let bv = p.blur_vec_sw.xy;
    let b_len = length(bv);
    var col = vec3<f32>(0.0);
    if (b_len > 0.0005) {
        let samples: i32 = 7;
        for (var i: i32 = 0; i < samples; i = i + 1) {
            let f = (f32(i) / f32(samples - 1)) - 0.5;
            let suv = clamp(in.uv + bv * f, vec2<f32>(0.001), vec2<f32>(0.999));
            col = col + textureSampleLevel(color_tex, lin_samp, suv, 0.0).rgb;
        }
        col = col / f32(samples);
    } else {
        col = textureSampleLevel(color_tex, lin_samp, in.uv, 0.0).rgb;
    }

    // 2. Distance-Mapped Adaptive Dark Ink Outlines (tipis saat close-up, tegas di midground!)
    let gc = textureSampleLevel(gbuf_tex, lin_samp, in.uv, 0.0);
    if (gc.w < 400.0 && p.flags.y > 0.01) {
        let close_fade = smoothstep(0.65, 3.8, gc.w);  // menipis otomatis saat snappy dolly-in!
        let far_fade = 1.0 - smoothstep(45.0, 115.0, gc.w);
        let step_px = px * mix(0.85, 1.35, close_fade);

        let gL = textureSampleLevel(gbuf_tex, lin_samp, in.uv - vec2<f32>(step_px.x, 0.0), 0.0);
        let gR = textureSampleLevel(gbuf_tex, lin_samp, in.uv + vec2<f32>(step_px.x, 0.0), 0.0);
        let gU = textureSampleLevel(gbuf_tex, lin_samp, in.uv - vec2<f32>(0.0, step_px.y), 0.0);
        let gD = textureSampleLevel(gbuf_tex, lin_samp, in.uv + vec2<f32>(0.0, step_px.y), 0.0);

        let d_edge = abs(log(max(gL.w, 0.05)) - log(max(gR.w, 0.05)))
                   + abs(log(max(gU.w, 0.05)) - log(max(gD.w, 0.05)));
        let n_edge = length(gL.xyz - gR.xyz) + length(gU.xyz - gD.xyz);

        // Jangan outline batas dengan billboard karakter (sentinel 499.0)
        let near_billboard = (gL.w > 495.0 && gL.w < 499.5) || (gR.w > 495.0 && gR.w < 499.5)
                          || (gU.w > 495.0 && gU.w < 499.5) || (gD.w > 495.0 && gD.w < 499.5);
        if (!near_billboard) {
            let ink_edge = max(smoothstep(0.22, 0.55, d_edge), smoothstep(0.68, 1.35, n_edge));
            let ink_amt = ink_edge * p.flags.y * (0.28 + 0.58 * close_fade) * far_fade;
            let ink_col = vec3<f32>(0.09, 0.07, 0.13);
            col = mix(col, ink_col, clamp(ink_amt, 0.0, 0.78));
        }
    }

    // 3. Radial Blue-Gold Shockwave Ring ([CAM 18] & [CAM 26]!)
    let sw_r = p.blur_vec_sw.z;
    let sw_a = p.blur_vec_sw.w;
    if (sw_a > 0.005) {
        let centered = (in.uv - vec2<f32>(0.5, 0.44)) * vec2<f32>(p.flags.z, 1.0);
        let dist_c = length(centered);
        let outer_ring = exp(-pow((dist_c - sw_r * 0.56) * 18.0, 2.0));
        let inner_ring = exp(-pow((dist_c - sw_r * 0.46) * 24.0, 2.0));
        let core_flash = exp(-dist_c * 4.2) * sw_a * 0.28;
        let gold_ring_col = vec3<f32>(1.0, 0.78, 0.30);
        col = col + p.sw_col_exp.rgb * (outer_ring * sw_a * 1.65 + core_flash) + gold_ring_col * (inner_ring * sw_a * 0.95);
    }

    // 4. Subtle Filmic Cartoon Tone-Mapping + Crisp Vignette
    col = col * p.sw_col_exp.w;
    col = (col * (2.51 * col + 0.03)) / (col * (2.43 * col + 0.59) + 0.14);
    let vig = 1.0 - smoothstep(0.55, 1.18, length((in.uv - vec2<f32>(0.5, 0.5)) * vec2<f32>(1.1, 1.0))) * 0.22;
    col = col * vig;
    col = pow(clamp(col, vec3<f32>(0.0), vec3<f32>(1.0)), vec3<f32>(1.0 / 2.2));

    // 5. Hidden 2-frame black grate wipe cut ([CAM 15])
    col = col * (1.0 - clamp(p.flags.x, 0.0, 1.0));

    return vec4<f32>(col, 1.0);
}
"""


@dataclass
class BillboardDraw:
    """Satu quad alpha 3D (karakter Bima, Oren, Kunci Emas/Perak, Figuran, atau Partikel 3D)."""

    center: np.ndarray            # posisi tengah bawah/pusat di dunia 3D
    width: float                  # lebar dunia 3D (meter)
    height: float                 # tinggi dunia 3D (meter)
    rgba_image: Image.Image       # sprite RGBA transparan
    anchor_bottom: bool = True    # True = center adalah titik tapak kaki/bawah
    roll_deg: float = 0.0         # rotasi bidang quad (mis. melompat / terbang)
    tint: Tuple[float, float, float, float] = (1.0, 1.0, 1.0, 1.0)
    fog_scale: float = 0.45
    emissive_boost: float = 0.0
    cache_key: Optional[str] = None
    is_fx: bool = False           # True = soft particle tanpa depth-write (uap, debu, percikan)


class WgpuCelRenderer:
    """Mesin render 3D WebGPU (D3D12 / Vulkan) siap 9:16 YouTube Shorts."""

    def __init__(self, width: int = 720, height: int = 1280) -> None:
        self.width = int(width)
        self.height = int(height)
        adapter = wgpu.gpu.request_adapter_sync(power_preference="high-performance")
        if adapter is None:
            raise RuntimeError("Tidak ditemukan adapter WGPU (DirectX12/Vulkan/WARP).")
        self.adapter_name = f"{adapter.info.get('device', 'GPU')} ({adapter.info.get('backend_type', '')})"
        self.device = adapter.request_device_sync()

        # Render targets
        self.shadow_tex = self.device.create_texture(
            size=(SHADOW_SIZE, SHADOW_SIZE, 1),
            format=wgpu.TextureFormat.depth32float,
            usage=wgpu.TextureUsage.RENDER_ATTACHMENT | wgpu.TextureUsage.TEXTURE_BINDING,
        )
        self.scene_color_tex = self.device.create_texture(
            size=(self.width, self.height, 1),
            format=wgpu.TextureFormat.rgba16float,
            usage=wgpu.TextureUsage.RENDER_ATTACHMENT | wgpu.TextureUsage.TEXTURE_BINDING,
        )
        self.gbuf_tex = self.device.create_texture(
            size=(self.width, self.height, 1),
            format=wgpu.TextureFormat.rgba16float,
            usage=wgpu.TextureUsage.RENDER_ATTACHMENT | wgpu.TextureUsage.TEXTURE_BINDING,
        )
        self.scene_depth_tex = self.device.create_texture(
            size=(self.width, self.height, 1),
            format=wgpu.TextureFormat.depth32float,
            usage=wgpu.TextureUsage.RENDER_ATTACHMENT,
        )
        self.out_tex = self.device.create_texture(
            size=(self.width, self.height, 1),
            format=wgpu.TextureFormat.rgba8unorm,
            usage=wgpu.TextureUsage.RENDER_ATTACHMENT | wgpu.TextureUsage.COPY_SRC,
        )

        self.linear_sampler = self.device.create_sampler(
            mag_filter="linear",
            min_filter="linear",
            address_mode_u="clamp-to-edge",
            address_mode_v="clamp-to-edge",
        )

        # Uniform buffers
        self.shadow_ubo = self.device.create_buffer(size=64, usage=wgpu.BufferUsage.UNIFORM | wgpu.BufferUsage.COPY_DST)
        self.scene_ubo = self.device.create_buffer(size=416, usage=wgpu.BufferUsage.UNIFORM | wgpu.BufferUsage.COPY_DST)
        self.post_ubo = self.device.create_buffer(size=48, usage=wgpu.BufferUsage.UNIFORM | wgpu.BufferUsage.COPY_DST)

        self._build_pipelines()
        self._gpu_tex_cache: dict[str, tuple[wgpu.GPUTexture, wgpu.GPUTextureView]] = {}
        self._static_vbo: Optional[wgpu.GPUBuffer] = None
        self._static_vcount: int = 0

    def _build_pipelines(self) -> None:
        v_layout_mesh = [
            {
                "array_stride": 48,
                "step_mode": wgpu.VertexStepMode.vertex,
                "attributes": [
                    {"format": wgpu.VertexFormat.float32x3, "offset": 0, "shader_location": 0},
                    {"format": wgpu.VertexFormat.float32x3, "offset": 12, "shader_location": 1},
                    {"format": wgpu.VertexFormat.float32x2, "offset": 24, "shader_location": 2},
                    {"format": wgpu.VertexFormat.float32x3, "offset": 32, "shader_location": 3},
                    {"format": wgpu.VertexFormat.float32, "offset": 44, "shader_location": 4},
                ],
            }
        ]

        # 1. Shadow pipeline
        sh_mod = self.device.create_shader_module(code=SHADOW_WGSL)
        self.shadow_pipe = self.device.create_render_pipeline(
            layout="auto",
            vertex={"module": sh_mod, "entry_point": "vs_main", "buffers": v_layout_mesh},
            primitive={"topology": wgpu.PrimitiveTopology.triangle_list, "cull_mode": wgpu.CullMode.none},
            depth_stencil={"format": wgpu.TextureFormat.depth32float, "depth_write_enabled": True, "depth_compare": wgpu.CompareFunction.less},
        )
        self.shadow_bg = self.device.create_bind_group(
            layout=self.shadow_pipe.get_bind_group_layout(0),
            entries=[{"binding": 0, "resource": {"buffer": self.shadow_ubo, "offset": 0, "size": 64}}],
        )

        # 2. Sky pipeline
        sky_mod = self.device.create_shader_module(code=SKY_WGSL)
        self.sky_pipe = self.device.create_render_pipeline(
            layout="auto",
            vertex={"module": sky_mod, "entry_point": "vs_main"},
            fragment={
                "module": sky_mod,
                "entry_point": "fs_main",
                "targets": [
                    {"format": wgpu.TextureFormat.rgba16float},
                    {"format": wgpu.TextureFormat.rgba16float},
                ],
            },
            primitive={"topology": wgpu.PrimitiveTopology.triangle_list},
            depth_stencil={"format": wgpu.TextureFormat.depth32float, "depth_write_enabled": False, "depth_compare": wgpu.CompareFunction.always},
        )
        self.sky_bg = self.device.create_bind_group(
            layout=self.sky_pipe.get_bind_group_layout(0),
            entries=[{"binding": 0, "resource": {"buffer": self.scene_ubo, "offset": 0, "size": 416}}],
        )

        # 3. 3D Cel-PBR Mesh pipeline
        mesh_mod = self.device.create_shader_module(code=MESH_WGSL)
        self.mesh_pipe = self.device.create_render_pipeline(
            layout="auto",
            vertex={"module": mesh_mod, "entry_point": "vs_main", "buffers": v_layout_mesh},
            fragment={
                "module": mesh_mod,
                "entry_point": "fs_main",
                "targets": [
                    {"format": wgpu.TextureFormat.rgba16float},
                    {"format": wgpu.TextureFormat.rgba16float},
                ],
            },
            primitive={"topology": wgpu.PrimitiveTopology.triangle_list, "cull_mode": wgpu.CullMode.none},
            depth_stencil={"format": wgpu.TextureFormat.depth32float, "depth_write_enabled": True, "depth_compare": wgpu.CompareFunction.less},
        )
        self.mesh_bg = self.device.create_bind_group(
            layout=self.mesh_pipe.get_bind_group_layout(0),
            entries=[
                {"binding": 0, "resource": {"buffer": self.scene_ubo, "offset": 0, "size": 416}},
                {"binding": 1, "resource": self.shadow_tex.create_view()},
            ],
        )

        # 4. 3D Depth-Tested Alpha Billboard pipeline
        bb_mod = self.device.create_shader_module(code=BILLBOARD_WGSL)
        v_layout_bb = [
            {
                "array_stride": 20,
                "step_mode": wgpu.VertexStepMode.vertex,
                "attributes": [
                    {"format": wgpu.VertexFormat.float32x3, "offset": 0, "shader_location": 0},
                    {"format": wgpu.VertexFormat.float32x2, "offset": 12, "shader_location": 1},
                ],
            }
        ]
        self.bb_pipe = self.device.create_render_pipeline(
            layout="auto",
            vertex={"module": bb_mod, "entry_point": "vs_main", "buffers": v_layout_bb},
            fragment={
                "module": bb_mod,
                "entry_point": "fs_main",
                "targets": [
                    {
                        "format": wgpu.TextureFormat.rgba16float,
                        "blend": {
                            "color": {"src_factor": "src-alpha", "dst_factor": "one-minus-src-alpha", "operation": "add"},
                            "alpha": {"src_factor": "one", "dst_factor": "one-minus-src-alpha", "operation": "add"},
                        },
                    },
                    {"format": wgpu.TextureFormat.rgba16float},
                ],
            },
            primitive={"topology": wgpu.PrimitiveTopology.triangle_list, "cull_mode": wgpu.CullMode.none},
            depth_stencil={"format": wgpu.TextureFormat.depth32float, "depth_write_enabled": True, "depth_compare": wgpu.CompareFunction.less},
        )
        # Pipeline khusus FX partikel lembut (uap zamrud, bubuk kunyit, debu, percikan): depth-tested TANPA depth-write!
        self.bb_fx_pipe = self.device.create_render_pipeline(
            layout="auto",
            vertex={"module": bb_mod, "entry_point": "vs_main", "buffers": v_layout_bb},
            fragment={
                "module": bb_mod,
                "entry_point": "fs_main",
                "targets": [
                    {
                        "format": wgpu.TextureFormat.rgba16float,
                        "blend": {
                            "color": {"src_factor": "src-alpha", "dst_factor": "one-minus-src-alpha", "operation": "add"},
                            "alpha": {"src_factor": "one", "dst_factor": "one-minus-src-alpha", "operation": "add"},
                        },
                    },
                    {"format": wgpu.TextureFormat.rgba16float, "write_mask": 0},
                ],
            },
            primitive={"topology": wgpu.PrimitiveTopology.triangle_list, "cull_mode": wgpu.CullMode.none},
            depth_stencil={"format": wgpu.TextureFormat.depth32float, "depth_write_enabled": False, "depth_compare": wgpu.CompareFunction.less},
        )
        self.bb_scene_bg = self.device.create_bind_group(
            layout=self.bb_pipe.get_bind_group_layout(0),
            entries=[{"binding": 0, "resource": {"buffer": self.scene_ubo, "offset": 0, "size": 416}}],
        )
        self.bb_fx_scene_bg = self.device.create_bind_group(
            layout=self.bb_fx_pipe.get_bind_group_layout(0),
            entries=[{"binding": 0, "resource": {"buffer": self.scene_ubo, "offset": 0, "size": 416}}],
        )

        # 5. Post-process pipeline
        post_mod = self.device.create_shader_module(code=POST_WGSL)
        self.post_pipe = self.device.create_render_pipeline(
            layout="auto",
            vertex={"module": post_mod, "entry_point": "vs_main"},
            fragment={
                "module": post_mod,
                "entry_point": "fs_main",
                "targets": [{"format": wgpu.TextureFormat.rgba8unorm}],
            },
            primitive={"topology": wgpu.PrimitiveTopology.triangle_list},
        )
        self.post_bg = self.device.create_bind_group(
            layout=self.post_pipe.get_bind_group_layout(0),
            entries=[
                {"binding": 0, "resource": {"buffer": self.post_ubo, "offset": 0, "size": 48}},
                {"binding": 1, "resource": self.scene_color_tex.create_view()},
                {"binding": 2, "resource": self.gbuf_tex.create_view()},
                {"binding": 3, "resource": self.linear_sampler},
            ],
        )

    def upload_static_world(self, vertices: np.ndarray) -> None:
        """Upload seluruh geometri 3D statis (6 lokasi lengkap) sekali ke VRAM."""
        arr = np.ascontiguousarray(vertices, dtype=np.float32)
        self._static_vcount = int(arr.shape[0])
        if self._static_vcount == 0:
            self._static_vbo = None
            return
        self._static_vbo = self.device.create_buffer_with_data(data=arr.tobytes(), usage=wgpu.BufferUsage.VERTEX)

    def _get_or_upload_sprite_view(self, img: Image.Image, cache_key: Optional[str]) -> wgpu.GPUTextureView:
        if cache_key and cache_key in self._gpu_tex_cache:
            return self._gpu_tex_cache[cache_key][1]
        rgba = img.convert("RGBA")
        w, h = rgba.size
        tex = self.device.create_texture(
            size=(w, h, 1),
            format=wgpu.TextureFormat.rgba8unorm_srgb,
            usage=wgpu.TextureUsage.TEXTURE_BINDING | wgpu.TextureUsage.COPY_DST,
        )
        self.device.queue.write_texture(
            {"texture": tex},
            rgba.tobytes(),
            {"bytes_per_row": w * 4, "rows_per_image": h},
            (w, h, 1),
        )
        view = tex.create_view()
        if cache_key:
            # Batasi cache agar hemat memori saat render 1740 frame
            if len(self._gpu_tex_cache) > 120:
                old_k = next(iter(self._gpu_tex_cache))
                del self._gpu_tex_cache[old_k]
            self._gpu_tex_cache[cache_key] = (tex, view)
        return view

    def render_frame(
        self,
        cam_pos: np.ndarray,
        cam_target: np.ndarray,
        view_mat: np.ndarray,
        proj_mat: np.ndarray,
        lighting: LightingState,
        dynamic_vertices: Optional[np.ndarray] = None,
        billboards: Optional[List[BillboardDraw]] = None,
        motion_blur_uv: Tuple[float, float] = (0.0, 0.0),
        outline_strength: float = 0.85,
        time_sec: float = 0.0,
        shadow_center: Optional[np.ndarray] = None,
        shadow_radius: float = 28.0,
    ) -> np.ndarray:
        """Render satu frame 3D penuh ke array NumPy RGBA uint8 (H, W, 4)."""
        vp = (proj_mat @ view_mat).astype(np.float32)
        try:
            inv_vp = np.linalg.inv(vp).astype(np.float32)
        except np.linalg.LinAlgError:
            inv_vp = np.eye(4, dtype=np.float32)

        # Hitung shadow light matrix berpusat di sekitar target kamera
        sh_focus = shadow_center if shadow_center is not None else (cam_pos * 0.35 + cam_target * 0.65)
        sun_dir = normalize(np.array(lighting.sun_dir, dtype=np.float32))
        light_eye = sh_focus + sun_dir * (shadow_radius * 1.9)
        light_view = look_at_matrix(light_eye, sh_focus)
        light_proj = ortho_matrix(
            -shadow_radius, shadow_radius, -shadow_radius, shadow_radius, 0.5, shadow_radius * 4.5
        )
        light_vp = (light_proj @ light_view).astype(np.float32)

        # Upload uniform buffers (transpose -> column-major WGSL!)
        self.device.queue.write_buffer(self.shadow_ubo, 0, light_vp.T.astype(np.float32).tobytes())

        scene_bytes = bytearray()
        scene_bytes += vp.T.astype(np.float32).tobytes()
        scene_bytes += inv_vp.T.astype(np.float32).tobytes()
        scene_bytes += light_vp.T.astype(np.float32).tobytes()
        scene_bytes += struct.pack(
            "4f4f4f4f4f4f4f4f4f4f4f4f4f4f",
            float(cam_pos[0]), float(cam_pos[1]), float(cam_pos[2]), 1.0,
            float(sun_dir[0]), float(sun_dir[1]), float(sun_dir[2]), float(lighting.sun_intensity),
            lighting.sun_color[0], lighting.sun_color[1], lighting.sun_color[2], float(lighting.sun_disc_size),
            lighting.shade_color[0], lighting.shade_color[1], lighting.shade_color[2], 0.0,
            lighting.ambient_color[0], lighting.ambient_color[1], lighting.ambient_color[2], 0.0,
            lighting.rim_color[0], lighting.rim_color[1], lighting.rim_color[2], float(lighting.rim_intensity),
            lighting.fog_color[0], lighting.fog_color[1], lighting.fog_color[2], float(lighting.fog_density),
            lighting.sky_top[0], lighting.sky_top[1], lighting.sky_top[2], 0.0,
            lighting.sky_mid[0], lighting.sky_mid[1], lighting.sky_mid[2], 0.0,
            lighting.sky_horizon[0], lighting.sky_horizon[1], lighting.sky_horizon[2], 0.0,
            lighting.sun_disc_color[0], lighting.sun_disc_color[1], lighting.sun_disc_color[2], 0.0,
            lighting.point_light_pos[0], lighting.point_light_pos[1], lighting.point_light_pos[2], float(lighting.point_light_intensity),
            lighting.point_light_color[0], lighting.point_light_color[1], lighting.point_light_color[2], 0.0,
            float(time_sec), 0.0, 0.0, 0.0,
        )
        self.device.queue.write_buffer(self.scene_ubo, 0, bytes(scene_bytes))

        sw_col = (0.35, 0.92, 1.0) if lighting.phase_name == "phase3_twilight" else (0.28, 0.96, 0.80)
        post_bytes = struct.pack(
            "4f4f4f",
            float(motion_blur_uv[0]), float(motion_blur_uv[1]), float(lighting.shockwave_radius), float(lighting.shockwave_alpha),
            sw_col[0], sw_col[1], sw_col[2], float(lighting.exposure),
            float(lighting.black_wipe), float(outline_strength), self.width / float(self.height), float(time_sec),
        )
        self.device.queue.write_buffer(self.post_ubo, 0, post_bytes)

        dyn_vbo = None
        dyn_vcount = 0
        if dynamic_vertices is not None and dynamic_vertices.shape[0] > 0:
            arr_d = np.ascontiguousarray(dynamic_vertices, dtype=np.float32)
            dyn_vcount = int(arr_d.shape[0])
            dyn_vbo = self.device.create_buffer_with_data(data=arr_d.tobytes(), usage=wgpu.BufferUsage.VERTEX)

        # Siapkan billboard 3D (pisahkan karakter/prop cutout vs partikel FX lembut tanpa depth-write!)
        bb_char_items = []
        bb_fx_items = []
        if billboards:
            cam_right = view_mat[0, :3]
            cam_up = view_mat[1, :3]
            world_up = np.array([0.0, 1.0, 0.0], dtype=np.float32)
            sorted_bbs = sorted(
                billboards,
                key=lambda b: float(np.dot(b.center - cam_pos, b.center - cam_pos)),
                reverse=True,
            )
            for bb in sorted_bbs:
                if bb.anchor_bottom:
                    # Cylindrical world-up billboard: karakter selalu berdiri tegak di atas lantai 3D
                    # meski kamera melakukan 360° barrel roll ([CAM 08]) atau inverted skim ([CAM 14])!
                    horiz = np.array([bb.center[0] - cam_pos[0], 0.0, bb.center[2] - cam_pos[2]], dtype=np.float32)
                    if float(np.linalg.norm(horiz)) < 1e-4:
                        horiz = np.array([-view_mat[2, 0], 0.0, -view_mat[2, 2]], dtype=np.float32)
                    f_h = normalize(horiz)
                    base_r = normalize(np.cross(f_h, world_up))
                    base_u = world_up
                else:
                    base_r = cam_right
                    base_u = cam_up

                r_vec = base_r
                u_vec = base_u
                if abs(bb.roll_deg) > 1e-3:
                    rad = np.radians(bb.roll_deg)
                    cr, sr = float(np.cos(rad)), float(np.sin(rad))
                    r_vec = base_r * cr + base_u * sr
                    u_vec = -base_r * sr + base_u * cr
                hw = bb.width * 0.5
                if bb.anchor_bottom:
                    p_bl = bb.center - r_vec * hw
                    p_br = bb.center + r_vec * hw
                    p_tr = bb.center + r_vec * hw + u_vec * bb.height
                    p_tl = bb.center - r_vec * hw + u_vec * bb.height
                else:
                    hh = bb.height * 0.5
                    p_bl = bb.center - r_vec * hw - u_vec * hh
                    p_br = bb.center + r_vec * hw - u_vec * hh
                    p_tr = bb.center + r_vec * hw + u_vec * hh
                    p_tl = bb.center - r_vec * hw + u_vec * hh

                quad = np.array(
                    [
                        [p_bl[0], p_bl[1], p_bl[2], 0.0, 1.0],
                        [p_br[0], p_br[1], p_br[2], 1.0, 1.0],
                        [p_tr[0], p_tr[1], p_tr[2], 1.0, 0.0],
                        [p_bl[0], p_bl[1], p_bl[2], 0.0, 1.0],
                        [p_tr[0], p_tr[1], p_tr[2], 1.0, 0.0],
                        [p_tl[0], p_tl[1], p_tl[2], 0.0, 0.0],
                    ],
                    dtype=np.float32,
                )
                vbo = self.device.create_buffer_with_data(data=quad.tobytes(), usage=wgpu.BufferUsage.VERTEX)
                alpha_cut = 0.02 if bb.is_fx else 0.42
                ubo_bytes = struct.pack(
                    "4f4f",
                    bb.tint[0], bb.tint[1], bb.tint[2], bb.tint[3],
                    float(bb.fog_scale), float(bb.emissive_boost), alpha_cut, 0.0,
                )
                ubo = self.device.create_buffer_with_data(data=ubo_bytes, usage=wgpu.BufferUsage.UNIFORM)
                tex_view = self._get_or_upload_sprite_view(bb.rgba_image, bb.cache_key)
                target_pipe = self.bb_fx_pipe if bb.is_fx else self.bb_pipe
                bg = self.device.create_bind_group(
                    layout=target_pipe.get_bind_group_layout(1),
                    entries=[
                        {"binding": 0, "resource": {"buffer": ubo, "offset": 0, "size": 32}},
                        {"binding": 1, "resource": tex_view},
                        {"binding": 2, "resource": self.linear_sampler},
                    ],
                )
                if bb.is_fx:
                    bb_fx_items.append((vbo, bg))
                else:
                    bb_char_items.append((vbo, bg))

        enc = self.device.create_command_encoder()

        # PASS 1: Shadow Map
        sh_pass = enc.begin_render_pass(
            color_attachments=[],
            depth_stencil_attachment={
                "view": self.shadow_tex.create_view(),
                "depth_load_op": "clear",
                "depth_store_op": "store",
                "depth_clear_value": 1.0,
            },
        )
        sh_pass.set_pipeline(self.shadow_pipe)
        sh_pass.set_bind_group(0, self.shadow_bg)
        if self._static_vbo is not None and self._static_vcount > 0:
            sh_pass.set_vertex_buffer(0, self._static_vbo)
            sh_pass.draw(self._static_vcount, 1, 0, 0)
        if dyn_vbo is not None and dyn_vcount > 0:
            sh_pass.set_vertex_buffer(0, dyn_vbo)
            sh_pass.draw(dyn_vcount, 1, 0, 0)
        sh_pass.end()

        # PASS 2: Sky + 3D Cel-PBR Meshes + Depth-Tested 3D Billboards
        sc_pass = enc.begin_render_pass(
            color_attachments=[
                {"view": self.scene_color_tex.create_view(), "load_op": "clear", "store_op": "store", "clear_value": (0.0, 0.0, 0.0, 1.0)},
                {"view": self.gbuf_tex.create_view(), "load_op": "clear", "store_op": "store", "clear_value": (0.0, 0.0, 1.0, 500.0)},
            ],
            depth_stencil_attachment={
                "view": self.scene_depth_tex.create_view(),
                "depth_load_op": "clear",
                "depth_store_op": "store",
                "depth_clear_value": 1.0,
            },
        )
        # 2a. Sky
        sc_pass.set_pipeline(self.sky_pipe)
        sc_pass.set_bind_group(0, self.sky_bg)
        sc_pass.draw(3, 1, 0, 0)

        # 2b. 3D Meshes
        sc_pass.set_pipeline(self.mesh_pipe)
        sc_pass.set_bind_group(0, self.mesh_bg)
        if self._static_vbo is not None and self._static_vcount > 0:
            sc_pass.set_vertex_buffer(0, self._static_vbo)
            sc_pass.draw(self._static_vcount, 1, 0, 0)
        if dyn_vbo is not None and dyn_vcount > 0:
            sc_pass.set_vertex_buffer(0, dyn_vbo)
            sc_pass.draw(dyn_vcount, 1, 0, 0)

        # 2c. Depth-tested 3D Alpha Billboards (karakter & hero props dulu, lalu partikel FX lembut!)
        if bb_char_items:
            sc_pass.set_pipeline(self.bb_pipe)
            sc_pass.set_bind_group(0, self.bb_scene_bg)
            for vbo, bg in bb_char_items:
                sc_pass.set_bind_group(1, bg)
                sc_pass.set_vertex_buffer(0, vbo)
                sc_pass.draw(6, 1, 0, 0)
        if bb_fx_items:
            sc_pass.set_pipeline(self.bb_fx_pipe)
            sc_pass.set_bind_group(0, self.bb_fx_scene_bg)
            for vbo, bg in bb_fx_items:
                sc_pass.set_bind_group(1, bg)
                sc_pass.set_vertex_buffer(0, vbo)
                sc_pass.draw(6, 1, 0, 0)
        sc_pass.end()

        # PASS 3: Post-Process (Adaptive Ink Outlines + Motion Blur + Shockwave + Filmic Tone-Map)
        p_pass = enc.begin_render_pass(
            color_attachments=[
                {"view": self.out_tex.create_view(), "load_op": "clear", "store_op": "store", "clear_value": (0.0, 0.0, 0.0, 1.0)},
            ],
        )
        p_pass.set_pipeline(self.post_pipe)
        p_pass.set_bind_group(0, self.post_bg)
        p_pass.draw(3, 1, 0, 0)
        p_pass.end()

        self.device.queue.submit([enc.finish()])

        raw = self.device.queue.read_texture(
            {"texture": self.out_tex},
            {"bytes_per_row": self.width * 4, "rows_per_image": self.height},
            (self.width, self.height, 1),
        )
        return np.frombuffer(raw, dtype=np.uint8).reshape((self.height, self.width, 4)).copy()
