# Panduan Pengerjaan SNORT 3 di Kali Linux

Berdasarkan sistem Anda, Kali Linux yang digunakan sudah menggunakan **Snort versi 3** (versi modern yang jauh lebih canggih). Format konfigurasinya berbeda dari Snort versi lama (tidak lagi memakai `snort.conf` melainkan `snort.lua`).

Berikut adalah tahapan lengkap khusus untuk Snort 3:

---

## Tahap 1: Instalasi & Cek Interface

1. **Pastikan Snort 3 Terinstal** (Sudah Anda lakukan)
   ```bash
   sudo apt install snort -y
   ```

2. **Cari Tahu Interface Jaringan Anda**
   ```bash
   ip a
   ```
   Perhatikan nama *interface* utama Anda. Dari pengecekan sebelumnya, *interface* Anda adalah **`eth0`** dan IP Range Anda adalah **`10.0.2.0/24`**.

---

## Tahap 2: Konfigurasi Dasar (`snort.lua`)

1. **Edit File Konfigurasi Utama**
   Gunakan editor teks `nano` untuk membuka file konfigurasi Snort 3:
   ```bash
   sudo nano /etc/snort/snort.lua
   ```
   
2. **Ubah variabel `HOME_NET`**
   Di dalam file tersebut, cari baris kode yang mengatur jaringan internal. Ubah nilainya menjadi rentang IP Anda:
   ```lua
   HOME_NET = '10.0.2.0/24'
   ```
   *(Simpan dengan menekan `Ctrl+O`, `Enter`, lalu `Ctrl+X`).*

3. **Verifikasi Konfigurasi**
   Jalankan perintah ini untuk memastikan tidak ada kesalahan ketik di file `.lua` tadi:
   ```bash
   sudo snort -c /etc/snort/snort.lua
   ```
   Jika muncul tulisan "Snort successfully validated the configuration", berarti sudah benar.

---

## Tahap 3: Pembuatan Aturan (Rules) Kustom

Snort 3 membaca file *rules* dengan format yang sama, namun kita akan membuat file khusus untuk mendeteksi ancaman web (Ping, XSS, dan SQL Injection).

1. **Buat/Buka File Rules Lokal**
   ```bash
   sudo nano /etc/snort/rules/local.rules
   ```

2. **Tambahkan Rules Deteksi**
   Salin dan tempel (Paste) 3 baris peringatan berikut ke dalam file tersebut:

   **A. Deteksi Ping (ICMP)**
   ```text
   alert icmp any any -> $HOME_NET any (msg:"Peringatan: Ada aktivitas PING terdeteksi!"; sid:1000001; rev:1;)
   ```

   **B. Deteksi Potensi XSS**
   ```text
   alert tcp any any -> $HOME_NET 8000 (msg:"Peringatan: Potensi XSS <script> terdeteksi!"; content:"<script>"; sid:1000002; rev:1;)
   ```

   **C. Deteksi Potensi SQL Injection**
   ```text
   alert tcp any any -> $HOME_NET 8000 (msg:"Peringatan: Potensi SQL Injection (' OR 1=1)"; content:"' OR 1=1"; sid:1000003; rev:1;)
   ```
   *(Simpan dan keluar: `Ctrl+O`, `Enter`, `Ctrl+X`)*.

---

## Tahap 4: Menjalankan Snort (Mode Pendeteksi Layar)

Untuk menjalankan Snort 3 agar langsung mencetak peringatan berwarna di layar terminal Anda saat ada serangan, gunakan perintah berikut:

```bash
sudo snort -c /etc/snort/snort.lua -R /etc/snort/rules/local.rules -i eth0 -A alert_fast
```
*(Snort akan bersiap dan mendengarkan jaringan. Biarkan terminal ini tetap menyala).*

---

## Tahap 5: Pengujian Serangan

Buka **Terminal Baru** di Kali Linux Anda, dan cobalah lakukan serangan ke diri sendiri untuk memancing alarm Snort:

1. **Uji Coba Ping**
   ```bash
   ping 10.0.2.15
   ```
   👉 *Buka kembali terminal Snort, Anda akan melihat log berteriak "Ada aktivitas PING terdeteksi!"*

2. **Uji Coba Serangan Web (XSS/SQLi)**
   Jika server Django Anda menyala di port 8000, tembak dengan *payload* mematikan menggunakan `curl`:
   ```bash
   curl "http://127.0.0.1:8000/accounts/login/?username=<script>"
   ```
   👉 *Snort akan mendeteksi *string* berbahaya tersebut dan mencetak "Potensi XSS terdeteksi!"*
