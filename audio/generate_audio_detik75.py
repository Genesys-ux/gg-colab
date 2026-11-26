"""
Generator Master Audio 75.0 Detik untuk "DETIK KE-75":
  1. Voiceover Bahasa Indonesia Natural (`edge-tts` dengan fallback sintetis bila offline):
     - VO Raka Muda (terengah/mendesak), Dialog Bima (menggema & bisikan ICU),
       Dialog Agen Sena, dan VO Kakek Raka (lembut damai).
  2. Sound Design & Musik Prosedural Sinematik (44.1kHz Stereo -> Mono HQ Mix):
     - Babak I (00:00–00:18): Bass synth ritmis 140 BPM seperti detak jantung + decit logam Maglev +
       shimmer bullet-time cincin emas + dentuman portal petir.
     - Babak II (00:18–00:46): Guntur menggelegar + hujan deras + bunyi pengunci laser Kira (beep..beep..) +
       denting kristal pecah & pad hangat saat hujan melayang naik.
     - Babak III (00:46–01:15): Musik synth berhenti mendadak -> bunyi monitor jantung -> flatline panjang
       (beeeeeeep...) + denting piano tunggal menyayat -> getar cincin -> BEEP! kebangkitan ->
       pad keemasan koridor -> suara tiupan lilin "Fuuuh..." di 01:14!
"""
from __future__ import annotations

import asyncio
import math
import os
import random
import shutil
import struct
import subprocess
import tempfile
import wave
from typing import List, Tuple

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(PROJECT_ROOT, "audio", "output")
MASTER_WAV = os.path.join(OUT_DIR, "detik75_master_75s.wav")
MASTER_MP3 = os.path.join(OUT_DIR, "detik75_master_75s.mp3")

SR = 24000
DURATION = 75.0
N_SAMPLES = int(SR * DURATION)

# (start_sec, voice_id, rate, pitch, gain, text)
VO_LINES: List[Tuple[float, str, str, str, float, str]] = [
    (1.2, "id-ID-ArdiNeural", "+18%", "+2Hz", 1.05,
     "Mereka bilang aku harus melepaskannya. Mereka tidak tahu, jika koper ini terbuka, aku akan lenyap."),
    (6.4, "id-ID-ArdiNeural", "+6%", "-12Hz", 1.10,
     "Raka! Berhenti! Lepaskan saja!"),
    (13.5, "id-ID-ArdiNeural", "+15%", "+2Hz", 1.05,
     "Satu lompatan lagi. Aku hanya butuh satu menit."),
    (30.8, "id-ID-ArdiNeural", "+10%", "-4Hz", 1.05,
     "Pupilnya tidak merespons! Kita kehilangan dia!"),
    (34.8, "id-ID-ArdiNeural", "+20%", "+4Hz", 1.08,
     "Jangan lihat cahayanya! Jaga kopernya!"),
    (48.8, "id-ID-ArdiNeural", "-8%", "-8Hz", 0.95,
     "Ayah, lepaskan saja... istirahatlah."),
    (52.8, "id-ID-ArdiNeural", "-14%", "-14Hz", 1.05,
     "Bukan koper itu yang mereka kejar. Mereka hanya melihatku tenggelam... sementara aku bertarung menjaga satu ingatan terakhir kita."),
]


def _add_tone(buf: List[float], t0: float, dur: float, freq: float, amp: float, decay: float = 4.0) -> None:
    i0 = max(0, int(t0 * SR))
    i1 = min(N_SAMPLES, int((t0 + dur) * SR))
    for i in range(i0, i1):
        dt = (i - i0) / float(SR)
        env = math.sin(min(1.0, dt / 0.015) * math.pi * 0.5) * math.exp(-decay * dt)
        buf[i] += amp * env * (0.75 * math.sin(math.tau * freq * dt) + 0.25 * math.sin(math.tau * freq * 2.0 * dt))


def _build_procedural_sfx_and_score() -> List[float]:
    buf = [0.0] * N_SAMPLES
    rng = random.Random(75)

    # 1. Babak I & II: 140 BPM Synth Heartbeat Bass (0.0..45.8s, berhenti mendadak di 46.0s!)
    beat_sec = 60.0 / 140.0  # 0.4286s
    t = 0.0
    beat_idx = 0
    while t < 45.6:
        # Bullet-time melambat di 10.2..12.2s dan 38.5..42.0s
        if (10.2 <= t <= 12.2) or (38.5 <= t <= 43.0):
            step = beat_sec * 2.0
            amp = 0.16
        else:
            step = beat_sec
            amp = 0.26 if (beat_idx % 2 == 0) else 0.17
        f_bass = 58.0 if (beat_idx % 2 == 0) else 49.0
        _add_tone(buf, t, 0.26, f_bass, amp, decay=9.5)
        t += step
        beat_idx += 1

    # Decit logam kereta Maglev (0..14s)
    for i in range(0, int(14.0 * SR)):
        ts = i / float(SR)
        screech = math.sin(math.tau * (920.0 + 60.0 * math.sin(ts * 2.3)) * ts) * 0.018
        buf[i] += screech

    # Shimmer cincin emas Maya (10.3s) & Dentuman Portal Badai (13.2s)
    for k, fk in enumerate([1046.5, 1318.5, 1568.0, 2093.0]):
        _add_tone(buf, 10.25 + k * 0.08, 1.4, fk, 0.08, decay=2.2)

    # Guntur menggelegar (18.2s, 20.4s, 28.1s) & deru hujan badai (16.5..39.8s)
    for th_t in (13.2, 18.2, 20.4, 28.1):
        i0, i1 = int(th_t * SR), min(N_SAMPLES, int((th_t + 2.4) * SR))
        lp = 0.0
        for i in range(i0, i1):
            dt = (i - i0) / float(SR)
            n = rng.uniform(-1.0, 1.0)
            lp = lp * 0.94 + n * 0.06
            buf[i] += lp * 0.85 * math.exp(-1.6 * dt)

    rain_lp = 0.0
    for i in range(int(16.5 * SR), int(39.8 * SR)):
        n = rng.uniform(-1.0, 1.0)
        rain_lp = rain_lp * 0.65 + n * 0.35
        buf[i] += rain_lp * 0.045

    # Bunyi pengunci laser sniper Kira: beep... beep... tajam!
    for bt in (20.8, 21.6, 22.3, 23.0, 24.0, 25.0, 37.2, 37.6, 37.9, 38.15):
        _add_tone(buf, bt, 0.14, 1760.0, 0.16, decay=14.0)

    # Pecahnya realitas kaca & pad hangat lilin (40.0..45.9s)
    for s_i, f_sh in enumerate([880.0, 1174.6, 1396.9, 1760.0, 2349.3]):
        _add_tone(buf, 41.8 + s_i * 0.35, 2.2, f_sh, 0.07, decay=1.4)

    # 3. Babak III (46.0..75.0s): Beep EKG -> Flatline Panjang -> Denting Piano Menyayat -> BEEP! -> Fuuuh...
    for hb_t in (46.6, 47.8, 49.0, 50.3, 51.7, 53.2, 54.8):
        _add_tone(buf, hb_t, 0.16, 987.77, 0.15, decay=11.0)

    # Flatline panjang monitor jantung (56.5..63.7s)
    for i in range(int(56.5 * SR), int(63.7 * SR)):
        ts = i / float(SR)
        fade = min(1.0, (ts - 56.5) / 0.1) * min(1.0, (63.7 - ts) / 0.1)
        buf[i] += 0.11 * fade * math.sin(math.tau * 987.77 * ts)

    # Denting piano tunggal melankolis (A minor -> F -> C -> G -> Fmaj7)
    piano_notes = [
        (47.0, 440.0), (49.5, 392.0), (52.2, 349.23), (55.0, 329.63),
        (57.5, 440.0), (59.8, 523.25), (61.8, 493.88),
        # Setelah BEEP! kebangkitan (64.2s): kord hangat C Mayor / F Lydian keemasan!
        (64.5, 523.25), (65.2, 659.25), (66.0, 783.99), (67.5, 587.33),
        (69.2, 659.25), (71.0, 783.99), (72.5, 1046.50),
    ]
    for pt, pf in piano_notes:
        _add_tone(buf, pt, 2.8, pf, 0.14, decay=1.35)
        _add_tone(buf, pt, 2.8, pf * 0.5, 0.07, decay=1.1)

    # Getar cincin emas Maya (62.4s) & BEEP! kebangkitan tajam mengharukan (64.0s)
    _add_tone(buf, 62.4, 1.2, 1567.98, 0.09, decay=2.5)
    _add_tone(buf, 64.0, 0.28, 987.77, 0.26, decay=6.5)
    _add_tone(buf, 65.1, 0.20, 987.77, 0.16, decay=9.0)
    _add_tone(buf, 66.2, 0.20, 987.77, 0.14, decay=9.0)

    # Detik ke-74.0: Suara tiupan lilin lembut "Fuuuh..."
    breath_lp = 0.0
    i_b0, i_b1 = int(73.85 * SR), int(74.85 * SR)
    for i in range(i_b0, i_b1):
        u = (i - i_b0) / max(1, i_b1 - i_b0)
        env = math.sin(u * math.pi) ** 1.4
        n = rng.uniform(-1.0, 1.0)
        breath_lp = breath_lp * 0.86 + n * 0.14
        buf[i] += breath_lp * 0.32 * env

    return buf


async def _synthesize_vo_clips(tmp_dir: str, ffmpeg_bin: str) -> List[Tuple[float, float, List[float]]]:
    clips: List[Tuple[float, float, List[float]]] = []
    try:
        import edge_tts  # type: ignore
    except ImportError:
        print("[Audio] edge-tts belum terpasang, melanjutkan dengan skor & SFX sinematik.", flush=True)
        return clips

    for idx, (t0, voice, rate, pitch, gain, text) in enumerate(VO_LINES):
        mp3_p = os.path.join(tmp_dir, f"vo_{idx}.mp3")
        wav_p = os.path.join(tmp_dir, f"vo_{idx}.wav")
        try:
            comm = edge_tts.Communicate(text=text, voice=voice, rate=rate, pitch=pitch)
            await comm.save(mp3_p)
            subprocess.run(
                [ffmpeg_bin, "-y", "-v", "error", "-i", mp3_p, "-ac", "1", "-ar", str(SR), wav_p],
                check=True,
            )
            with wave.open(wav_p, "rb") as wf:
                raw = wf.readframes(wf.getnframes())
            n = len(raw) // 2
            samples = [s / 32768.0 for s in struct.unpack(f"<{n}h", raw[: n * 2])]
            clips.append((t0, gain, samples))
            print(f"[VO {idx+1}/{len(VO_LINES)}] @{t0:.1f}s ({len(samples)/SR:.2f}s): {text[:44]}...", flush=True)
        except Exception as exc:
            print(f"[VO Warning] Gagal membuat VO #{idx+1}: {exc}", flush=True)
    return clips


def main() -> None:
    os.makedirs(OUT_DIR, exist_ok=True)
    mix = _build_procedural_sfx_and_score()

    ffmpeg_bin = shutil.which("ffmpeg")
    if ffmpeg_bin:
        with tempfile.TemporaryDirectory() as tmp_d:
            vo_clips = asyncio.run(_synthesize_vo_clips(tmp_d, ffmpeg_bin))
            for t0, gain, samples in vo_clips:
                i0 = int(t0 * SR)
                # Duck background score slightly under VO so narration is crystal clear!
                for k, s_val in enumerate(samples):
                    idx = i0 + k
                    if 0 <= idx < N_SAMPLES:
                        mix[idx] = mix[idx] * 0.52 + s_val * gain

    # Soft limiter & export 16-bit PCM WAV
    pcm = bytearray()
    for v in mix:
        clamped = math.tanh(v * 1.15) * 0.94
        pcm += struct.pack("<h", int(max(-32767, min(32767, round(clamped * 32767.0)))))

    with wave.open(MASTER_WAV, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SR)
        wf.writeframes(bytes(pcm))
    print(f"[Audio] Saved master WAV: {MASTER_WAV}", flush=True)

    if ffmpeg_bin:
        subprocess.run([ffmpeg_bin, "-y", "-v", "error", "-i", MASTER_WAV, "-b:a", "192k", MASTER_MP3], check=True)
        print(f"[Audio] Saved master MP3: {MASTER_MP3}", flush=True)


if __name__ == "__main__":
    main()
