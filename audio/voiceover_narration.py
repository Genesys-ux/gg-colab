"""
VoiceoverProducer — Pipeline Narasi Voiceover ElevenLabs untuk "Jangan Sampai Kunci Ini Jatuh!"
Format: YouTube Shorts 58 Detik (6 Segmen Narasi Bahasa Indonesia, Request Stitching + Timeline Assembly).

Konfigurasi kunci API:
  - Membaca ELEVENLABS_API_KEY secara otomatis dari file `.env` (via python-dotenv).
  - Jangan pernah menaruh API key di dalam kode.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from elevenlabs import ElevenLabs, VoiceSettings

# Default mengikuti rekomendasi resmi ElevenLabs TTS Skill:
# - eleven_v4: kualitas tertinggi, 90+ bahasa (termasuk Bahasa Indonesia), dukungan audio tags & request stitching
# - JBFqnCBsd6RMkjVDRZzb (George): pre-made narrative voice, kompatibel di semua paket termasuk Free
DEFAULT_MODEL_ID = "eleven_v4"
DEFAULT_VOICE_ID = "JBFqnCBsd6RMkjVDRZzb"
DEFAULT_OUTPUT_FORMAT = "mp3_44100_128"
TOTAL_DURATION_SEC = 58.0


@dataclass(frozen=True)
class NarrationSegment:
    id: str
    location: str
    start_sec: float
    end_sec: float
    text: str
    expressive_text: str
    stability: float = 0.42
    similarity_boost: float = 0.78
    notes: str = ""

    @property
    def max_duration_sec(self) -> float:
        return max(0.5, self.end_sec - self.start_sec)


NARRATION_SEGMENTS: List[NarrationSegment] = [
    NarrationSegment(
        id="vo_01_hook",
        location="Lokasi 1: Bengkel Jam Loteng (CAM 01-05)",
        start_sec=0.0,
        end_sec=4.2,
        text="Kalau kunci emas ini menyentuh lantai... seluruh kota bakal berhenti bernapas dalam sepuluh detik!",
        expressive_text="[urgent] Kalau kunci emas ini menyentuh lantai... seluruh kota bakal berhenti bernapas dalam sepuluh detik!",
        stability=0.40,
        similarity_boost=0.78,
        notes="Hook cepat & tegang, memuncak di detik ke-4 saat kunci terpeleset.",
    ),
    NarrationSegment(
        id="vo_02_pasar",
        location="Lokasi 2: Pasar Rempah & Buah Bertingkat (CAM 06-10)",
        start_sec=9.0,
        end_sec=17.8,
        text="Bima melompat dari atap—tapi kunci itu jauh lebih cepat! Memantul di tenda pasar, meledakkan bubuk kunyit, dan bikin satu blok pedagang ikut terjungkal!",
        expressive_text="[excited] Bima melompat dari atap—tapi kunci itu jauh lebih cepat! Memantul di tenda pasar, meledakkan bubuk kunyit, dan bikin satu blok pedagang ikut terjungkal!",
        stability=0.38,
        similarity_boost=0.78,
        notes="Tempo enerjik & komedis mengikuti kejar-kejaran di tenda pasar.",
    ),
    NarrationSegment(
        id="vo_03_gang_kucing",
        location="Lokasi 3: Gang Kafe & Jemuran Sempit (CAM 11-15)",
        start_sec=18.0,
        end_sec=25.8,
        text="Satu sentimeter lagi tertangkap! Tapi si kucing kampung ini malah menepisnya lurus ke jeruji besi tua... tunggu—kenapa suaranya bukan dentingan biasa?!",
        expressive_text="[tense] Satu sentimeter lagi tertangkap! Tapi si kucing kampung ini malah menepisnya lurus ke jeruji besi tua... [curious] tunggu—kenapa suaranya bukan dentingan biasa?!",
        stability=0.36,
        similarity_boost=0.78,
        notes="Kontras komedi Oren lalu berubah penasaran menuju hidden wipe cut.",
    ),
    NarrationSegment(
        id="vo_04_twist_gorong",
        location="Lokasi 4: Gorong-Gorong Mesin Jam Kuno — STORY TURN (CAM 16-19)",
        start_sec=26.2,
        end_sec=37.8,
        text="Gawat! Kunci ini nggak jatuh ke selokan biasa—ia mendarat tepat di Jantung Mesin Kota! Dan sekarang... bukan waktu yang berhenti. Tapi seluruh kota mulai berputar MUNDUR!",
        expressive_text="[gasps] Gawat! Kunci ini nggak jatuh ke selokan biasa—ia mendarat tepat di Jantung Mesin Kota! Dan sekarang... bukan waktu yang berhenti. Tapi seluruh kota mulai berputar MUNDUR!",
        stability=0.35,
        similarity_boost=0.80,
        notes="Momen Story Turn dramatis saat lighting berubah ke Indigo & Emerald.",
    ),
    NarrationSegment(
        id="vo_05_stasiun_trem",
        location="Lokasi 5: Stasiun Trem Layang Terbuka (CAM 20-24)",
        start_sec=38.2,
        end_sec=48.8,
        text="Kereta trem melesat mundur! Burung-burung terbang ke belakang! Bima cuma punya satu cara: melompat dari atap trem dan mencabut kembali kunci yang terlempar ke langit!",
        expressive_text="[excited] Kereta trem melesat mundur! Burung-burung terbang ke belakang! Bima cuma punya satu cara: melompat dari atap trem dan mencabut kembali kunci yang terlempar ke langit!",
        stability=0.36,
        similarity_boost=0.78,
        notes="Klimaks kecepatan tinggi menuju slow-mo lompatan di depan matahari crimson.",
    ),
    NarrationSegment(
        id="vo_06_ending_loop",
        location="Lokasi 6: Wajah Menara Jam Utama di Dermaga (CAM 25-28)",
        start_sec=49.2,
        end_sec=57.8,
        text="Waktu kembali normal tepat di detik terakhir... tapi tunggu—kalau kuncinya ada di tangan Bima sekarang... lalu apa yang baru saja jatuh dari sakunya?!",
        expressive_text="[relieved] Waktu kembali normal tepat di detik terakhir... [surprised] tapi tunggu—kalau kuncinya ada di tangan Bima sekarang... lalu apa yang baru saja jatuh dari sakunya?!",
        stability=0.40,
        similarity_boost=0.78,
        notes="Lega sebentar lalu twist komedis Kunci Perak yang menyambung seamless loop ke Hook!",
    ),
]


def _probe_duration_sec(audio_path: Path) -> Optional[float]:
    ffprobe = shutil.which("ffprobe")
    if not ffprobe or not audio_path.exists():
        return None
    try:
        res = subprocess.run(
            [
                ffprobe,
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                str(audio_path),
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        return float(res.stdout.strip())
    except Exception:
        return None


class VoiceoverProducer:
    """
    Generator & assembler narasi voiceover ElevenLabs untuk proyek 'Jangan Sampai Kunci Ini Jatuh!'.
    """

    def __init__(
        self,
        env_path: Optional[str] = None,
        voice_id: str = DEFAULT_VOICE_ID,
        model_id: str = DEFAULT_MODEL_ID,
        output_format: str = DEFAULT_OUTPUT_FORMAT,
        language_code: str = "id",
        output_dir: Optional[str] = None,
    ) -> None:
        project_root = Path(__file__).resolve().parent.parent
        load_dotenv(env_path or str(project_root / ".env"), override=True)
        self.client = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))
        self.voice_id = voice_id
        self.model_id = model_id
        self.output_format = output_format
        self.language_code = language_code
        self.output_dir = Path(output_dir) if output_dir else (project_root / "audio" / "output")

    def list_premade_voices(self) -> List[Dict[str, str]]:
        """Daftar seluruh suara pre-made yang aman dipakai di semua paket ElevenLabs (termasuk Free)."""
        resp = self.client.voices.get_all()
        results: List[Dict[str, str]] = []
        for v in resp.voices:
            if getattr(v, "category", "") == "premade":
                labels = getattr(v, "labels", None) or {}
                results.append(
                    {
                        "voice_id": v.voice_id,
                        "name": v.name,
                        "accent": str(labels.get("accent", "")),
                        "gender": str(labels.get("gender", "")),
                        "use_case": str(labels.get("use_case", "")),
                    }
                )
        return results

    def _build_voice_settings(self, seg: NarrationSegment) -> VoiceSettings:
        # Catatan resmi ElevenLabs: eleven_v4 hanya menerima stability & similarity_boost
        if self.model_id.startswith("eleven_v4"):
            return VoiceSettings(
                stability=seg.stability,
                similarity_boost=seg.similarity_boost,
            )
        return VoiceSettings(
            stability=seg.stability,
            similarity_boost=seg.similarity_boost,
            use_speaker_boost=True,
        )

    def synthesize_segment(
        self,
        segment: NarrationSegment,
        previous_text: Optional[str] = None,
        next_text: Optional[str] = None,
        use_expressive_tags: bool = False,
    ) -> Dict[str, Any]:
        """Generate satu segmen narasi ke file MP3 dengan Request Stitching dan pelacakan karakter."""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        spoken_text = segment.expressive_text if (use_expressive_tags and self.model_id.startswith("eleven_v4")) else segment.text

        kwargs: Dict[str, Any] = {
            "text": spoken_text,
            "voice_id": self.voice_id,
            "model_id": self.model_id,
            "output_format": self.output_format,
            "voice_settings": self._build_voice_settings(segment),
            "apply_text_normalization": "on",
        }
        # language_code didukung di eleven_v4 / eleven_flash_v2_5 (tidak didukung di eleven_multilingual_v2)
        if self.language_code and self.model_id != "eleven_multilingual_v2":
            kwargs["language_code"] = self.language_code
        if previous_text:
            kwargs["previous_text"] = previous_text
        if next_text:
            kwargs["next_text"] = next_text

        out_path = self.output_dir / f"{segment.id}.mp3"
        with self.client.text_to_speech.with_raw_response.convert(**kwargs) as raw_response:
            with open(out_path, "wb") as f:
                for chunk in raw_response.data:
                    if chunk:
                        f.write(chunk)
            char_count = raw_response.headers.get("x-character-count")
            request_id = raw_response.headers.get("request-id")

        duration_sec = _probe_duration_sec(out_path)

        return {
            "id": segment.id,
            "location": segment.location,
            "file": str(out_path),
            "start_sec": segment.start_sec,
            "end_sec": segment.end_sec,
            "slot_duration_sec": round(segment.max_duration_sec, 3),
            "actual_duration_sec": round(duration_sec, 3) if duration_sec is not None else None,
            "characters_billed": int(char_count) if (char_count and char_count.isdigit()) else len(spoken_text),
            "request_id": request_id,
            "text": spoken_text,
        }

    def generate_all_segments(
        self,
        segments: Optional[List[NarrationSegment]] = None,
        use_expressive_tags: bool = False,
        assemble_master: bool = True,
    ) -> Dict[str, Any]:
        """Generate seluruh 6 segmen VO secara berurutan dengan Request Stitching + susun master 58 detik."""
        segs = segments or NARRATION_SEGMENTS
        results: List[Dict[str, Any]] = []
        total_chars = 0

        for idx, seg in enumerate(segs):
            prev_txt = segs[idx - 1].text if idx > 0 else None
            next_txt = segs[idx + 1].text if idx + 1 < len(segs) else None
            info = self.synthesize_segment(
                seg,
                previous_text=prev_txt,
                next_text=next_txt,
                use_expressive_tags=use_expressive_tags,
            )
            total_chars += int(info.get("characters_billed") or 0)
            results.append(info)
            print(
                f"[VO] {seg.id} -> {info['file']} "
                f"(durasi={info['actual_duration_sec']}s / slot={info['slot_duration_sec']}s)"
            )

        manifest: Dict[str, Any] = {
            "title": "Jangan Sampai Kunci Ini Jatuh!",
            "voice_id": self.voice_id,
            "model_id": self.model_id,
            "language_code": self.language_code,
            "total_duration_sec": TOTAL_DURATION_SEC,
            "total_characters_billed": total_chars,
            "segments": results,
            "master_wav": None,
            "master_mp3": None,
        }

        if assemble_master:
            wav_path, mp3_path = self.assemble_master_timeline(results)
            manifest["master_wav"] = str(wav_path) if wav_path else None
            manifest["master_mp3"] = str(mp3_path) if mp3_path else None

        manifest_path = self.output_dir / "vo_manifest.json"
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, ensure_ascii=False, indent=2)
        manifest["manifest_path"] = str(manifest_path)
        return manifest

    def assemble_master_timeline(
        self,
        segment_infos: List[Dict[str, Any]],
        total_duration_sec: float = TOTAL_DURATION_SEC,
    ) -> tuple[Optional[Path], Optional[Path]]:
        """
        Susun seluruh segmen VO ke track master 58 detik menggunakan FFmpeg sesuai timestamp storyboard.
        Jika suatu klip sedikit melebihi slot waktunya, terapkan atempo halus agar tidak menabrak adegan berikutnya.
        """
        ffmpeg = shutil.which("ffmpeg")
        if not ffmpeg or not segment_infos:
            return None, None

        cmd: List[str] = [ffmpeg, "-y", "-v", "error"]
        # Input 0: silence base 58 detik stereo 44.1kHz
        cmd += ["-f", "lavfi", "-t", str(total_duration_sec), "-i", "anullsrc=r=44100:cl=stereo"]

        valid_infos = [s for s in segment_infos if Path(s["file"]).exists()]
        if not valid_infos:
            return None, None

        for info in valid_infos:
            cmd += ["-i", info["file"]]

        filter_parts: List[str] = []
        mix_labels: List[str] = ["[0:a]"]

        for idx, info in enumerate(valid_infos, start=1):
            delay_ms = int(round(float(info["start_sec"]) * 1000.0))
            slot_dur = float(info["slot_duration_sec"])
            act_dur = info.get("actual_duration_sec")

            chain: List[str] = ["aresample=44100", "aformat=channel_layouts=stereo"]
            if act_dur and act_dur > slot_dur * 1.03:
                tempo = min(1.32, act_dur / slot_dur)
                chain.append(f"atempo={tempo:.4f}")
            chain.append(f"adelay={delay_ms}|{delay_ms}")

            lbl = f"[s{idx}]"
            filter_parts.append(f"[{idx}:a]{','.join(chain)}{lbl}")
            mix_labels.append(lbl)

        filter_parts.append(
            f"{''.join(mix_labels)}amix=inputs={len(mix_labels)}:duration=first:normalize=0[mixed]"
        )
        filter_parts.append(f"[mixed]alimiter=limit=0.95,atrim=0:{total_duration_sec}[out]")

        master_wav = self.output_dir / "narration_master_58s.wav"
        master_mp3 = self.output_dir / "narration_master_58s.mp3"

        cmd_wav = cmd + [
            "-filter_complex",
            ";".join(filter_parts),
            "-map",
            "[out]",
            "-c:a",
            "pcm_s16le",
            str(master_wav),
        ]
        subprocess.run(cmd_wav, check=True)

        subprocess.run(
            [ffmpeg, "-y", "-v", "error", "-i", str(master_wav), "-c:a", "libmp3lame", "-b:a", "192k", str(master_mp3)],
            check=True,
        )
        return master_wav, master_mp3


def _main_cli() -> None:
    parser = argparse.ArgumentParser(
        description='ElevenLabs Voiceover Producer — "Jangan Sampai Kunci Ini Jatuh!" (58s Shorts)'
    )
    parser.add_argument("--list-voices", action="store_true", help="Tampilkan daftar suara pre-made yang tersedia")
    parser.add_argument("--all", action="store_true", help="Generate seluruh 6 segmen VO + master 58 detik")
    parser.add_argument("--segment", default=None, help="Generate 1 segmen tertentu (mis. vo_01_hook)")
    parser.add_argument("--voice-id", default=DEFAULT_VOICE_ID, help=f"Voice ID ElevenLabs (default: {DEFAULT_VOICE_ID})")
    parser.add_argument("--model-id", default=DEFAULT_MODEL_ID, help=f"Model ID ElevenLabs (default: {DEFAULT_MODEL_ID})")
    parser.add_argument("--expressive-tags", action="store_true", help="Aktifkan audio tags ekspresif eleven_v4 ([urgent], [excited], dll.)")
    parser.add_argument("--no-master", action="store_true", help="Lewati penggabungan master 58 detik dengan FFmpeg")
    parser.add_argument("--show-script", action="store_true", help="Cetak 6 segmen naskah & timestamp tanpa memanggil API")
    args = parser.parse_args()

    if args.show_script:
        for seg in NARRATION_SEGMENTS:
            print(f"{seg.id} [{seg.start_sec:04.1f}s - {seg.end_sec:04.1f}s] ({seg.location})")
            print(f"  {seg.text}\n")
        return

    producer = VoiceoverProducer(voice_id=args.voice_id, model_id=args.model_id)

    if args.list_voices:
        for v in producer.list_premade_voices():
            print(f"{v['voice_id']}  {v['name']} ({v['gender']}, {v['accent']}, {v['use_case']})")
        return

    if args.segment:
        matches = [s for s in NARRATION_SEGMENTS if s.id == args.segment]
        if not matches:
            valid = ", ".join(s.id for s in NARRATION_SEGMENTS)
            raise SystemExit(f"Segmen '{args.segment}' tidak ditemukan. Pilihan: {valid}")
        idx = NARRATION_SEGMENTS.index(matches[0])
        prev_t = NARRATION_SEGMENTS[idx - 1].text if idx > 0 else None
        next_t = NARRATION_SEGMENTS[idx + 1].text if idx + 1 < len(NARRATION_SEGMENTS) else None
        info = producer.synthesize_segment(
            matches[0],
            previous_text=prev_t,
            next_text=next_t,
            use_expressive_tags=args.expressive_tags,
        )
        print(json.dumps(info, ensure_ascii=False, indent=2))
        return

    if args.all:
        manifest = producer.generate_all_segments(
            use_expressive_tags=args.expressive_tags,
            assemble_master=not args.no_master,
        )
        print(json.dumps(manifest, ensure_ascii=False, indent=2))
        return

    parser.print_help()


if __name__ == "__main__":
    _main_cli()
