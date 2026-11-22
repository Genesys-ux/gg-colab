# Panduan Render 3D Blender EEVEE Next via GitHub + Google Colab GPU

Proyek ini sudah siap dijalankan di **Blender 4.2 LTS + EEVEE Next** menggunakan **GPU NVIDIA T4 gratis di Google Colab** tanpa membebani GPU PC lokal Anda.

---

## Langkah 1 — Push Project ke Repo GitHub (Aman, `.env` Otomatis Terproteksi)

Pastikan Anda berada di folder proyek (`c:\Users\lutfi\Downloads\py nem`), lalu jalankan di PowerShell:

```powershell
git init
git branch -M main
git status   # Pastikan `.env` TIDAK muncul di daftar commit!
git add .
git commit -m "Add Blender 4.2 bpy EEVEE Next pipeline + Google Colab notebook"
git remote add origin https://github.com/USERNAME/REPO_ANDA.git
git push -u origin main
```

> **Keamanan**: File `.env` (API key ElevenLabs) sudah terblokir otomatis di `.gitignore` sehingga tidak ikut ter-push, sementara hasil audio narasi master (`audio/output/narration_master_58s.wav` & `.mp3`) ikut masuk repo agar Colab bisa langsung menggabungkan video + audio secara otomatis.

---

## Langkah 2 — Buka `render_colab.ipynb` di Google Colab (GPU T4 Gratis)

1. Buka [Google Colab](https://colab.research.google.com/) → tab **GitHub** → masukkan URL repo Anda → pilih **`render_colab.ipynb`**.
2. Klik **Runtime → Change runtime type → T4 GPU** → **Save**.
3. Di **Sel 1**, ganti `GITHUB_REPO_URL` dengan URL repo GitHub Anda (dan biarkan `USE_GOOGLE_DRIVE = True` & `DOWNLOAD_POLYHAVEN_PBR = True`).
4. Jalankan **Sel 1 → Sel 2 → Sel 3**:
   - Sel 2 otomatis mengunduh **Blender 4.2 LTS Linux** + library NVIDIA EGL/Xvfb.
   - Sel 3 membangun file `jangan_sampai_kunci_ini_jatuh.blend` (6 lokasi, karakter 3D rig terbuka, 28 gerakan kamera, 3 fase lighting, & shader Cel-PBR) lalu merender **12 screenshot preview 9:16 + 3 Contact Sheet** dan menampilkannya langsung di Colab untuk Anda nilai!
   - File `.blend` juga otomatis disalin ke Google Drive (`MyDrive/KunciJatuh_Blender3D/`) sehingga bisa Anda buka & poles manual di Blender Windows kapan saja.
5. Jika 12 preview sudah memuaskan, jalankan **Sel 4** untuk merender seluruh **1.740 frame (58 detik @ 30fps)** dengan fitur `--resume` (aman jika Colab sempat terputus!) + muxing audio narasi ElevenLabs menjadi file `.mp4` siap upload ke YouTube Shorts!

---

## Menjalankan Secara Lokal di Blender Windows (Opsional, AMD RX 580)

Jika suatu saat Anda meng-install **Blender 4.2 LTS** di Windows, perintah yang sama juga berjalan langsung secara lokal:

```powershell
blender -b -P blender_pipeline/render_eevee.py -- --mode previews --width 720 --height 1280 --samples 32 --download-pbr
blender -b -P blender_pipeline/render_eevee.py -- --mode video --width 1080 --height 1920 --samples 32 --resume
```
