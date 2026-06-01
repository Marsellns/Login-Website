# Panduan Pengerjaan SNORT 3 di Kali Linux & Integrasi Django Ngrok

Panduan ini berisi langkah-langkah detail untuk mendemonstrasikan sistem Deteksi Intrusi (IDS) menggunakan **Snort 3** pada Kali Linux yang dihubungkan dengan website Django yang diekspos melalui **Ngrok**.

---

## Tahap 1: Persiapan Server Web (Django & Ngrok)

1. **Nyalakan Server Django**
   Buka terminal pertama di Kali Linux atau Windows Anda, masuk ke folder project, lalu jalankan server:
   ```bash
   export DJANGO_SECRET_KEY=testing123
   python manage.py runserver 0.0.0.0:8000 --settings=secure_auth.settings_dev
   ```

2. **Nyalakan Ngrok**
   Buka terminal kedua, arahkan ke port 8000 menggunakan Ngrok untuk mendapatkan URL publik:
   ```bash
   ./ngrok http 8000
   ```
   *Catat URL Ngrok yang muncul (misalnya: `http://uneaten-enzyme-charity.ngrok-free.dev`). Pastikan Anda menggunakan awalan `http://` (bukan https) saat melakukan simulasi penyerangan agar payload tidak terenkripsi dan bisa dibaca oleh SNORT.*

---

## Tahap 2: Konfigurasi Rules SNORT (Super Agresif)

Kita akan membuat aturan (rules) SNORT 3 yang bersifat "Super Agresif" (`any any -> any any`) agar SNORT dapat menangkap semua serangan yang keluar-masuk, terlepas dari konfigurasi alamat IP `$HOME_NET` Anda.

1. **Perbarui File Rules**
   Buka terminal di Kali Linux, salin dan jalankan seluruh perintah di bawah ini sekaligus untuk menimpa file `local.rules`:

   ```bash
   cat << 'EOF' | sudo tee /etc/snort/rules/local.rules > /dev/null
   # 1. SQL INJECTION DETECTION
   alert tcp any any -> any any (msg:"[WEB] SQL Injection Attempt Detected (UNION SELECT)"; flow:established,to_server; content:"UNION", nocase; content:"SELECT", nocase, distance 0; classtype:web-application-attack; sid:1000001; rev:2;)
   alert tcp any any -> any any (msg:"[WEB] SQL Injection Attempt Detected (OR 1=1)"; flow:established,to_server; content:"OR", nocase; content:"1=1", nocase, distance 0; classtype:web-application-attack; sid:1000002; rev:2;)

   # 2. XSS (CROSS SITE SCRIPTING) DETECTION
   alert tcp any any -> any any (msg:"[WEB] XSS Attempt Detected (<script>)"; flow:established,to_server; http_uri; content:"<script", nocase; classtype:web-application-attack; sid:1000003; rev:2;)
   alert tcp any any -> any any (msg:"[WEB] XSS Attempt Detected (javascript:)"; flow:established,to_server; http_uri; content:"javascript:", nocase; classtype:web-application-attack; sid:1000004; rev:2;)

   # 3. DIRECTORY TRAVERSAL (Mode Super Agresif)
   alert tcp any any -> any any (msg:"[WEB] Directory Traversal Attempt (../)"; content:"../"; classtype:web-application-attack; sid:1000005; rev:2;)
   alert tcp any any -> any any (msg:"[WEB] Linux /etc/passwd Access Attempt"; content:"/etc/passwd"; classtype:web-application-attack; sid:1000006; rev:2;)

   # 4. BRUTE FORCE LOGIN DETECTION (Batas: 2 kali)
   alert tcp any any -> any any (msg:"[WEB] Possible Login Brute Force Attempt"; content:"POST"; content:"/accounts/login"; detection_filter:track by_src, count 2, seconds 60; classtype:suspicious-login; sid:1000007; rev:2;)

   # 5. PING (ICMP) DETECTION
   alert icmp any any -> any any (msg:"[ICMP] Peringatan Ada aktivitas PING terdeteksi"; sid:1000010; rev:2;)
   EOF
   ```

---

## Tahap 3: Menjalankan Sang Penjaga (SNORT)

Karena serangan Anda menggunakan target URL Ngrok di internet, SNORT harus memantau *interface* jaringan utama yang mengarah ke luar (biasanya `eth0`). 

Jalankan perintah ini di Kali Linux untuk memulai pantauan *real-time* di layar terminal:

```bash
sudo snort -c /etc/snort/snort.lua -R /etc/snort/rules/local.rules -i eth0 -A alert_fast -k none
```

*Catatan Tambahan: Jika Anda juga ingin SNORT menulis ke file log agar bisa dibaca/ditampilkan oleh halaman Dashboard Website secara live, tambahkan opsi `-l /var/log/snort` sebelum tulisan `-k none`.*

Biarkan terminal ini terbuka setelah muncul pesan `Commencing packet processing ++ [0] eth0`.

---

## Tahap 4: Eksekusi Serangan (Demonstrasi)

Buka **Terminal Baru (Sang Penyerang)** di Kali Linux. Pastikan Anda mengganti bagian `URL_NGROK_ANDA` di bawah ini dengan URL `http://` Ngrok asli Anda (contoh: `uneaten-enzyme-charity.ngrok-free.dev`). Jalankan perintah ini secara berurutan:

**1. SQL Injection**
```bash
curl "http://URL_NGROK_ANDA/?username=admin%27%20OR%201=1"
```

**2. Cross-Site Scripting (XSS)**
```bash
curl "http://URL_NGROK_ANDA/?search=<script>alert(1)</script>"
```

**3. Directory Traversal**
*(Parameter `--path-as-is` mencegah curl menghapus `../` secara otomatis sebelum dikirim)*
```bash
curl --path-as-is "http://URL_NGROK_ANDA/../../../../etc/passwd"
```

**4. Brute Force Login**
*(Melakukan rentetan serangan POST dalam waktu singkat untuk melampaui batas deteksi)*
```bash
for i in {1..5}; do curl -X POST "http://URL_NGROK_ANDA/accounts/login/" -d "username=admin&password=123"; done
```

**5. Serangan Ping (ICMP)**
*(Diarahkan secara sengaja ke DNS Google agar paket melewati antarmuka `eth0`)*
```bash
ping -c 4 8.8.8.8
```

Segera setelah Anda mengeksekusi perintah-perintah di atas, lihatlah Terminal SNORT Anda. Anda akan melihat seluruh serangan tertangkap dan tercatat secara *real-time* dalam bentuk log berwarna merah.

---

## Tahap 5: Mengunduh Rule Komunitas (Community Rules)

Untuk memenuhi spesifikasi tugas yang mensyaratkan penggunaan *Community Rules* resmi dari Snort, Anda dapat mengunduh database aturan global dengan langkah berikut:

1. Buka terminal di Kali Linux, unduh dan ekstrak file aturan komunitas:
   ```bash
   cd ~
   wget https://www.snort.org/downloads/community/snort3-community-rules.tar.gz
   tar -xzvf snort3-community-rules.tar.gz
   ```
2. Pindahkan file tersebut ke direktori rules SNORT:
   ```bash
   sudo cp snort3-community-rules/snort3-community.rules /etc/snort/rules/
   ```

---

## Tahap 6: Implementasi ACL (Access Control List - Mode IPS)

Untuk memenuhi spesifikasi **SNORT + ACL**, SNORT harus dikonfigurasi untuk tidak hanya memberi peringatan (IDS), tetapi secara aktif memblokir (*drop*) lalu lintas berbahaya (Mode IPS / *Intrusion Prevention System*).

1. **Buat File ACL Rules**
   Salin dan jalankan perintah ini untuk membuat aturan pemblokiran (*drop*):
   ```bash
   cat << 'EOF' | sudo tee /etc/snort/rules/acl.rules > /dev/null
   # ACL 1: Memblokir semua lalu lintas PING yang masuk/keluar
   drop icmp any any -> any any (msg:"[ACL] Akses PING Ditolak dan Diblokir!"; sid:2000001; rev:1;)
   
   # ACL 2: Memblokir Akses File Sistem
   drop tcp any any -> any any (msg:"[ACL] Akses File Sistem Ditolak!"; content:"/etc/passwd"; sid:2000002; rev:1;)
   EOF
   ```

# Panduan Pengerjaan SNORT 3 di Kali Linux & Integrasi Django Ngrok

Panduan ini berisi langkah-langkah detail untuk mendemonstrasikan sistem Deteksi Intrusi (IDS) menggunakan **Snort 3** pada Kali Linux yang dihubungkan dengan website Django yang diekspos melalui **Ngrok**.

---

## Tahap 1: Persiapan Server Web (Django & Ngrok)

1. **Nyalakan Server Django**
   Buka terminal pertama di Kali Linux atau Windows Anda, masuk ke folder project, lalu jalankan server:
   ```bash
   export DJANGO_SECRET_KEY=testing123
   python manage.py runserver 0.0.0.0:8000 --settings=secure_auth.settings_dev
   ```

2. **Nyalakan Ngrok**
   Buka terminal kedua, arahkan ke port 8000 menggunakan Ngrok untuk mendapatkan URL publik:
   ```bash
   ./ngrok http 8000
   ```
   *Catat URL Ngrok yang muncul (misalnya: `http://uneaten-enzyme-charity.ngrok-free.dev`). Pastikan Anda menggunakan awalan `http://` (bukan https) saat melakukan simulasi penyerangan agar payload tidak terenkripsi dan bisa dibaca oleh SNORT.*

---

## Tahap 2: Konfigurasi Rules SNORT (Super Agresif)

Kita akan membuat aturan (rules) SNORT 3 yang bersifat "Super Agresif" (`any any -> any any`) agar SNORT dapat menangkap semua serangan yang keluar-masuk, terlepas dari konfigurasi alamat IP `$HOME_NET` Anda.

1. **Perbarui File Rules**
   Buka terminal di Kali Linux, salin dan jalankan seluruh perintah di bawah ini sekaligus untuk menimpa file `local.rules`:

   ```bash
   cat << 'EOF' | sudo tee /etc/snort/rules/local.rules > /dev/null
   # 1. SQL INJECTION DETECTION
   alert tcp any any -> any any (msg:"[WEB] SQL Injection Attempt Detected (UNION SELECT)"; flow:established,to_server; content:"UNION", nocase; content:"SELECT", nocase, distance 0; classtype:web-application-attack; sid:1000001; rev:2;)
   alert tcp any any -> any any (msg:"[WEB] SQL Injection Attempt Detected (OR 1=1)"; flow:established,to_server; content:"OR", nocase; content:"1=1", nocase, distance 0; classtype:web-application-attack; sid:1000002; rev:2;)

   # 2. XSS (CROSS SITE SCRIPTING) DETECTION
   alert tcp any any -> any any (msg:"[WEB] XSS Attempt Detected (<script>)"; flow:established,to_server; http_uri; content:"<script", nocase; classtype:web-application-attack; sid:1000003; rev:2;)
   alert tcp any any -> any any (msg:"[WEB] XSS Attempt Detected (javascript:)"; flow:established,to_server; http_uri; content:"javascript:", nocase; classtype:web-application-attack; sid:1000004; rev:2;)

   # 3. DIRECTORY TRAVERSAL (Mode Super Agresif)
   alert tcp any any -> any any (msg:"[WEB] Directory Traversal Attempt (../)"; content:"../"; classtype:web-application-attack; sid:1000005; rev:2;)
   alert tcp any any -> any any (msg:"[WEB] Linux /etc/passwd Access Attempt"; content:"/etc/passwd"; classtype:web-application-attack; sid:1000006; rev:2;)

   # 4. BRUTE FORCE LOGIN DETECTION (Batas: 2 kali)
   alert tcp any any -> any any (msg:"[WEB] Possible Login Brute Force Attempt"; content:"POST"; content:"/accounts/login"; detection_filter:track by_src, count 2, seconds 60; classtype:suspicious-login; sid:1000007; rev:2;)

   # 5. PING (ICMP) DETECTION
   alert icmp any any -> any any (msg:"[ICMP] Peringatan Ada aktivitas PING terdeteksi"; sid:1000010; rev:2;)
   EOF
   ```

---

## Tahap 3: Menjalankan Sang Penjaga (SNORT)

Karena serangan Anda menggunakan target URL Ngrok di internet, SNORT harus memantau *interface* jaringan utama yang mengarah ke luar (biasanya `eth0`). 

Jalankan perintah ini di Kali Linux untuk memulai pantauan *real-time* di layar terminal:

```bash
sudo snort -c /etc/snort/snort.lua -R /etc/snort/rules/local.rules -i eth0 -A alert_fast -k none
```

*Catatan Tambahan: Jika Anda juga ingin SNORT menulis ke file log agar bisa dibaca/ditampilkan oleh halaman Dashboard Website secara live, tambahkan opsi `-l /var/log/snort` sebelum tulisan `-k none`.*

Biarkan terminal ini terbuka setelah muncul pesan `Commencing packet processing ++ [0] eth0`.

---

## Tahap 4: Eksekusi Serangan (Demonstrasi)

Buka **Terminal Baru (Sang Penyerang)** di Kali Linux. Pastikan Anda mengganti bagian `URL_NGROK_ANDA` di bawah ini dengan URL `http://` Ngrok asli Anda (contoh: `uneaten-enzyme-charity.ngrok-free.dev`). Jalankan perintah ini secara berurutan:

**1. SQL Injection**
```bash
curl "http://URL_NGROK_ANDA/?username=admin%27%20OR%201=1"
```

**2. Cross-Site Scripting (XSS)**
```bash
curl "http://URL_NGROK_ANDA/?search=<script>alert(1)</script>"
```

**3. Directory Traversal**
*(Parameter `--path-as-is` mencegah curl menghapus `../` secara otomatis sebelum dikirim)*
```bash
curl --path-as-is "http://URL_NGROK_ANDA/../../../../etc/passwd"
```

**4. Brute Force Login**
*(Melakukan rentetan serangan POST dalam waktu singkat untuk melampaui batas deteksi)*
```bash
for i in {1..5}; do curl -X POST "http://URL_NGROK_ANDA/accounts/login/" -d "username=admin&password=123"; done
```

**5. Serangan Ping (ICMP)**
*(Diarahkan secara sengaja ke DNS Google agar paket melewati antarmuka `eth0`)*
```bash
ping -c 4 8.8.8.8
```

Segera setelah Anda mengeksekusi perintah-perintah di atas, lihatlah Terminal SNORT Anda. Anda akan melihat seluruh serangan tertangkap dan tercatat secara *real-time* dalam bentuk log berwarna merah.

---

## Tahap 5: Mengunduh Rule Komunitas (Community Rules)

Untuk memenuhi spesifikasi tugas yang mensyaratkan penggunaan *Community Rules* resmi dari Snort, Anda dapat mengunduh database aturan global dengan langkah berikut:

1. Buka terminal di Kali Linux, unduh dan ekstrak file aturan komunitas:
   ```bash
   cd ~
   wget https://www.snort.org/downloads/community/snort3-community-rules.tar.gz
   tar -xzvf snort3-community-rules.tar.gz
   ```
2. Pindahkan file tersebut ke direktori rules SNORT:
   ```bash
   sudo cp snort3-community-rules/snort3-community.rules /etc/snort/rules/
   ```

---

## Tahap 6: Implementasi ACL (Access Control List - Mode IPS)

Untuk memenuhi spesifikasi **SNORT + ACL**, SNORT harus dikonfigurasi untuk tidak hanya memberi peringatan (IDS), tetapi secara aktif memblokir (*drop*) lalu lintas berbahaya (Mode IPS / *Intrusion Prevention System*).

1. **Buat File ACL Rules**
   Salin dan jalankan perintah ini untuk membuat aturan pemblokiran (*drop*):
   ```bash
   cat << 'EOF' | sudo tee /etc/snort/rules/acl.rules > /dev/null
   # ACL 1: Memblokir semua lalu lintas PING yang masuk/keluar
   drop icmp any any -> any any (msg:"[ACL] Akses PING Ditolak dan Diblokir!"; sid:2000001; rev:1;)
   
   # ACL 2: Memblokir Akses File Sistem
   drop tcp any any -> any any (msg:"[ACL] Akses File Sistem Ditolak!"; content:"/etc/passwd"; sid:2000002; rev:1;)
   EOF
   ```

2. **Jalankan SNORT dalam Mode IPS (Inline)**
   Matikan SNORT yang sedang berjalan, lalu jalankan SNORT dengan memuat semua aturan (Lokal, Komunitas, dan ACL) menggunakan DAQ `afpacket` dalam mode antrean (`-Q`):
   ```bash
   sudo snort -c /etc/snort/snort.lua -R /etc/snort/rules/local.rules -R /etc/snort/rules/snort3-community.rules -R /etc/snort/rules/acl.rules -i eth0 -Q --daq afpacket -A alert_fast -k none
   ```

**Cara Pembuktian ACL:**
Saat SNORT mode IPS berjalan, sistem Kali Linux Anda (atau jika Anda melakukan PING ke 8.8.8.8) akan otomatis diblokir. Di terminal SNORT, Anda akan melihat log diawali dengan tanda **`[drop]`** alih-alih `[**]`. Ini membuktikan bahwa paket tersebut berhasil dicekik dan dihancurkan oleh ACL SNORT Anda! Ambil tangkapan layar ini sebagai bukti penyelesaian tugas akhir KEMSIS Anda.

---

## Tahap 7: Skenario Demo Penggantian IP Spesifik (Opsional)

Jika saat demo dosen Anda meminta untuk mengubah *rule* agar SNORT hanya mendeteksi serangan dari IP tertentu (tidak menggunakan `any`), berikut adalah cara memodifikasi aturannya:

1. Buka file *rules* Anda menggunakan editor `nano`:
   ```bash
   sudo nano /etc/snort/rules/local.rules
   ```

2. Cari baris aturan yang ingin diubah. Perhatikan rumus strukturnya:
   `[Aksi] [Protokol] [IP SUMBER] [Port Sumber] -> [IP TUJUAN] [Port Tujuan] (msg:"...");`

3. Hapus tulisan `any any -> any any` dan ganti menjadi IP yang spesifik.
   **Contoh:** Jika dosen meminta hanya mendeteksi Ping dari IP Kali Linux Anda (misal `10.0.2.15`), maka ubah aturannya menjadi:
   ```text
   alert icmp 10.0.2.15 any -> any any (msg:"[ICMP] Peringatan Ada aktivitas PING terdeteksi"; sid:1000010; rev:2;)
   ```

4. Simpan dengan menekan `Ctrl+O`, `Enter`, lalu keluar dengan `Ctrl+X`.
5. **Restart SNORT Anda** untuk memuat aturan IP yang baru.

**Trik Demo *Negative Test* (Untuk Nilai Plus):**
Buktikan kepada dosen bahwa *rule* tersebut benar-benar berfungsi dengan memasukkan **IP Palsu** (misal `192.168.1.99`) di file `local.rules`. Saat Anda melakukan Ping dari Kali Linux, SNORT akan DIAM SAJA. Lalu ubah kembali menjadi IP Kali asli Anda (`10.0.2.15`), dan saat Anda Ping lagi, SNORT akan LANGSUNG BERTERIAK. Ini membuktikan bahwa sistem filter IP Anda 100% akurat!
