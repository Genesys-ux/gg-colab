name: 3d-cinematic-animation-director
description: Panduan dan aturan standar untuk produksi animasi 3D sinematik berbasis kombinasi karakter (Python) dan environment 3D (Blender) dengan gaya cel-shaded colorful, pergerakan natural & realistis, kamera kontinu yang dinamis, sinkronisasi narasi ketat, dan pencahayaan atmosferik.

# 3D Cinematic Animation & Direction Skill

File ini berisi aturan wajib (strict rules) yang harus diikuti dalam merancang storyboard, skrip Python, animasi karakter, dan arahan kamera di Blender untuk produksi video animasi 3D.

## 1. Aturan Inti (Core Animation Rules)

Setiap adegan **WAJIB** mematuhi hukum fisika visual dan sinkronisasi berikut:

* **Sinkronisasi Narasi (Narrative Sync):** Animasi, aksi karakter, dan ritme visual harus berjalan selaras 100% dengan narasi atau *voiceover* yang sedang berjalan.
* **Fokus Dinamis (Emphasis Zoom):** Lakukan *Zoom In* atau *Zoom Out* secara spesifik pada objek, ekspresi, atau detail penting yang sedang dibahas dalam narasi.
* **Anti-Clipping (Strict Collision):** Karakter **dilarang keras** menembus dinding, lantai, atau properti apa pun (*no clipping*).
* **Interaksi Properti (Prop Interaction):** Karakter harus berinteraksi secara nyata dan natural dengan properti di sekitarnya (memegang, menyentuh, menggeser, duduk, dll.).

## 2. Integrasi Karakter (Python) & Environment 3D (Blender)

Karena animasi karakter dikendalikan melalui skrip **Python** di dalam *environment* **Blender**, gerakan yang dihasilkan **WAJIB terasa natural, organik, dan realistis seperti gerakan manusia/makhluk asli** (hindari kesan kaku atau robotik):

* **Biomekanika & Berat Tubuh (Weight & Physics):** Gerakan karakter hasil skrip Python harus memperhitungkan gravitasi, pusat massa (*center of gravity*), momentum, dan *follow-through* agar setiap langkah, tolakan, atau ayunan tangan terasa memiliki bobot nyata.
* **Kontak Permukaan Presisi (Ground & Surface Contact):** Kaki karakter harus menapak sempurna di atas *mesh* lantai/tanah Blender (tidak melayang/*floating* dan tidak selip/*foot sliding*).
* **Interaksi Fisik Realistis:** Saat karakter (Python) berinteraksi dengan objek/properti di Blender (misalnya membuka pintu, mengangkat barang, bersandar), koordinat *bone/rig* harus tersinkronisasi akurat dengan posisi dan *bounding box* objek 3D tersebut, lengkap dengan reaksi fisik yang wajar.
* **Kurva Gerak Organik (Non-Linear Motion):** Hindari interpolasi linear yang kaku. Gunakan kurva *easing*, *anticipation* (ancang-ancang), dan *micro-movements* (gerakan halus seperti bernapas, berkedip, atau pergeseran postur kecil saat diam) agar karakter terasa hidup.

## 3. Struktur Video & Pacing

* **2-Second Hook:** Berikan *hook* visual dan/atau audio yang sangat menarik pada **2 detik pertama** video sebelum masuk ke cerita utama untuk langsung mengunci perhatian penonton.
* **Variasi Lokasi:** Video harus memiliki **lebih dari 5 lokasi *shoot* yang berbeda** (> 5 locations) untuk menjaga dinamika visual.
* **Dinamika Kamera:** Gunakan **lebih dari 25 gerakan kamera** (> 25 camera movements) sepanjang video agar alur terasa hidup dan tidak statis.

## 4. Arah Visual, Properti & Environment (Art Direction)

* **Style:** *Colorful 3D Cel-Shaded Props* (gaya 3D *cel-shading* yang kaya warna dan cerah).
* **Tekstur:** *Realistic texture* (memadukan estetika *cel-shade* dengan detail tekstur permukaan yang realistis).
* **Set Dressing:** Lingkungan harus penuh detail (*full background props* dan *rich set dressing*). Hindari latar belakang yang kosong atau terasa hampa.

## 5. Gaya Kamera (Camera Style & Motion)

Gunakan pendekatan kamera virtual 3D yang mengalir mulus dan energik:

* **Aliran Kamera:** *Continuous 3D virtual camera* dengan *very few cuts* (minim potongan kasar; utamakan transisi menyambung).
* **Tipe Pergerakan:** *Travel Camera* yang menjelajahi ruang 3D dengan efek *strong 3D parallax*.
* **Transisi & Kecepatan:**
  * *Snappy speed-ramped dolly-in* dan *whip-pan transitions*.
  * *Zoom Transition* (*Zoom In* / *Zoom Out*) untuk berpindah fokus atau adegan.
* **Kurva Gerak (Motion Curves):**
  * *Exponential ease-in-out motion*.
  * *Smooth deceleration with subtle overshoot* (perlambatan halus dengan sedikit ayunan/overshoot di akhir gerakan agar terasa organik).
* **Optik & Efek:**
  * *Wide-angle lens* untuk menangkap skala ruang dan *parallax* yang kuat.
  * *Clean motion blur* khusus saat kamera melakukan sapuan cepat (*fast sweeps*).

## 6. Pencahayaan & Atmosfer (Lighting & Mood)

Pencahayaan berperan penting dalam membangun suasana cerita:

* **Setup Dasar:**
  * *Low Sun* (posisi matahari rendah untuk nuansa dramatis).
  * *Long shadow* (bayangan memanjang).
  * *Blue shade* (nuansa warna biru pada area bayangan).
* **Efek Atmosferik:**
  * *God rays* (*volumetric lighting*) yang menembus celah lingkungan.
  * *Haze* (kabut tipis atmosferik untuk kedalaman ruang/*depth*).
* **Dynamic Story Lighting:** Pencahayaan dan warna atmosfer **harus berubah secara dinamis mengikuti *plot twist* atau perubahan emosi cerita** (*it changes when the story turns*).

## 7. Checklist Validasi Sebelum Output

* [ ] Apakah 2 detik pertama sudah memiliki *hook* yang kuat?
* [ ] Apakah gerakan animasi sudah sinkron dengan narasi?
* [ ] Apakah gerakan karakter (Python) di *environment* Blender sudah natural, memiliki bobot, tidak kaku/robotik, dan tidak *foot sliding*?
* [ ] Apakah karakter berinteraksi secara presisi dengan properti Blender tanpa menembus (*no clipping*)?
* [ ] Apakah ada lebih dari 5 lokasi dan lebih dari 25 gerakan kamera?
* [ ] Apakah gaya kamera menggunakan *continuous 3D camera*, *speed-ramp*, *overshoot*, dan *wide-angle*?
* [ ] Apakah pencahayaan (*low sun*, *god rays*, *haze*) berubah saat alur cerita berbelok?