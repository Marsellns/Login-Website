# Menjalankan Aplikasi via Docker

Tiga file konfigurasi utama Docker (`.dockerignore`, `Dockerfile`, dan `docker-compose.yml`) telah berhasil ditambahkan ke dalam proyek Anda. Dengan konfigurasi ini, Anda tidak perlu menginstal Python atau library secara manual lagi.

## Prasyarat
Pastikan aplikasi **Docker Desktop** sudah terinstal dan sedang berjalan (ikon Docker di pojok kanan bawah Windows Anda berwarna hijau).

## Cara Menyalakan Server (Start)
1. Buka terminal di dalam folder proyek Anda.
2. Anda **tidak perlu** mengaktifkan virtual environment (`venv`).
3. Ketik perintah sakti ini:
   ```bash
   docker-compose up --build -d
   ```
   > **Info:** Parameter `--build` memberitahu Docker untuk merakit ulang sistem jika ada perubahan. Parameter `-d` (detach) berfungsi agar server berjalan di latar belakang sehingga terminal Anda tidak terkunci.

4. Tunggu beberapa saat hingga proses pengunduhan selesai.
5. Jika sudah selesai, buka `http://localhost:8000/accounts/login/` di browser web.

## Cara Melihat Log (Memantau Server)
Karena server berjalan di latar belakang, terminal Anda akan terlihat sepi. Untuk melihat aktivitas server (siapa yang login, error, dll), gunakan perintah:
```bash
docker-compose logs -f
```
*(Tekan `Ctrl+C` untuk keluar dari tampilan log).*

## Cara Mematikan Server (Stop)
Jika Anda ingin mematikan aplikasi dan menutup kontainernya secara bersih, cukup ketik:
```bash
docker-compose down
```

> **Tips:** Jika Anda menambahkan library baru di `requirements.txt`, Anda wajib menjalankan ulang perintah `docker-compose up --build -d` agar Docker memperbarui library-nya.
