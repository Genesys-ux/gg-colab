# Folder Aset 3D Kustom (`assets/models/`)

Opsional: jika Anda ingin mengganti karakter atau properti bawaan dengan model 3D hasil *sculpting* dari Blender / Sketchfab CC0 / GitHub, cukup letakkan file `.glb`, `.gltf`, atau `.fbx` di folder ini dengan nama berikut:

- `bima.glb` — menggantikan model + armature 3D Bima bawaan secara otomatis saat pipeline `blender_pipeline/render_eevee.py` dijalankan.

Tekstur PBR CC0 dari Poly Haven otomatis diunduh ke `assets/textures/` saat opsi `DOWNLOAD_POLYHAVEN_PBR = True` diaktifkan di `render_colab.ipynb` (atau flag `--download-pbr`).
