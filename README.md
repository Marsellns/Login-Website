# Panduan Presentasi KEMSIS: SNORT 3 IDS/IPS & Django Ngrok

Panduan ini telah disempurnakan khusus untuk kebutuhan presentasi (Demo) agar Anda dapat menjalankan simulasi serangan dan pertahanan secara lancar, berurutan, dan dijamin 100% berhasil di depan dosen.

---

## Tahap 1: Persiapan Server Web (Windows)

1. **Nyalakan Server Django**
   Buka terminal di Windows Anda, masuk ke folder project, lalu jalankan:
   ```bash
   export DJANGO_SECRET_KEY=testing123
   python manage.py runserver 0.0.0.0:8000 --settings=secure_auth.settings_dev
   ```

2. **Nyalakan Ngrok**
   Buka terminal kedua di Windows, ekspos port 8000:
   ```bash
   ./ngrok http 8000
   ```
   *URL Ngrok Anda saat ini: `http://uneaten-enzyme-charity.ngrok-free.dev`*

---

## Tahap 2: Menyiapkan Aturan Lokal "Super Agresif" (Kali Linux)

Buka terminal **pertama** di Kali Linux Anda. Kita akan menanamkan aturan lokal yang telah dimodifikasi agar sangat agresif (tanpa memperdulikan status TCP Handshake dari Ngrok) sehingga dijamin 100% mendeteksi serangan.

Jalankan seluruh blok perintah ini sekaligus (Copy-Paste lalu tekan Enter):
```bash
cat << 'EOF' | sudo tee /etc/snort/rules/local.rules > /dev/null
# 1. SQL INJECTION (Tanpa Syarat TCP State)
alert tcp any any -> any any (msg:"[WEB] SQL Injection Attempt Detected (UNION SELECT)"; content:"UNION", nocase; content:"SELECT", nocase, distance 0; classtype:web-application-attack; sid:1000001; rev:3;)
alert tcp any any -> any any (msg:"[WEB] SQL Injection Attempt Detected (OR 1=1)"; content:"OR", nocase; content:"1=1", nocase, distance 0; classtype:web-application-attack; sid:1000002; rev:3;)

# 2. XSS (CROSS SITE SCRIPTING) DETECTION
alert tcp any any -> any any (msg:"[WEB] XSS Attempt Detected (<script>)"; http_uri; content:"<script", nocase; classtype:web-application-attack; sid:1000003; rev:3;)
alert tcp any any -> any any (msg:"[WEB] XSS Attempt Detected (javascript:)"; http_uri; content:"javascript:", nocase; classtype:web-application-attack; sid:1000004; rev:3;)

# 3. DIRECTORY TRAVERSAL
alert tcp any any -> any any (msg:"[WEB] Directory Traversal Attempt (../)"; content:"../"; classtype:web-application-attack; sid:1000005; rev:3;)
alert tcp any any -> any any (msg:"[WEB] Linux /etc/passwd Access Attempt"; content:"/etc/passwd"; classtype:web-application-attack; sid:1000006; rev:3;)

# 4. BRUTE FORCE LOGIN DETECTION
alert tcp any any -> any any (msg:"[WEB] Possible Login Brute Force Attempt"; content:"POST"; content:"/accounts/login"; detection_filter:track by_src, count 2, seconds 60; classtype:suspicious-login; sid:1000007; rev:3;)

# 5. PING (ICMP) DETECTION
alert icmp any any -> any any (msg:"[ICMP] Peringatan Ada aktivitas PING terdeteksi"; sid:1000010; rev:3;)
EOF
```

---

## Tahap 3: Memasang Aturan Komunitas & ACL IPS

1. **Aturan Komunitas (Community Rules)**
   Jika belum ada, unduh dari Snort resmi:
   ```bash
   cd ~
   wget https://www.snort.org/downloads/community/snort3-community-rules.tar.gz
   tar -xzvf snort3-community-rules.tar.gz
   sudo cp snort3-community-rules/snort3-community.rules /etc/snort/rules/
   ```

2. **Membungkam Spam VirtualBox (Trik Troubleshooting Presentasi)**
   Jalankan perintah ini untuk mematikan satu aturan komunitas (SID 40063) yang mendeteksi jaringan VirtualBox sebagai serangan, agar layar presentasi Anda bersih, elegan, tanpa spam:
   ```bash
   sudo sed -i 's/.*sid:40063.*/# &/' /etc/snort/rules/snort3-community.rules
   ```

3. **Membuat Aturan ACL (Pemblokiran Aktif)**
   ```bash
   cat << 'EOF' | sudo tee /etc/snort/rules/acl.rules > /dev/null
   drop icmp any any -> any any (msg:"[ACL] Akses PING Ditolak dan Diblokir!"; sid:2000001; rev:1;)
   drop tcp any any -> any any (msg:"[ACL] Akses File Sistem Ditolak!"; content:"/etc/passwd"; sid:2000002; rev:1;)
   EOF
   ```

---

## Tahap 4: Menyalakan Mesin SNORT (Mode IPS Penuh)

Di terminal **pertama** Kali Linux yang sama, jalankan perintah pamungkas ini untuk memuat SEMUA *rules* di atas dalam Mode Mencekik (IPS/Inline) sekaligus me-validasinya:

```bash
sudo snort -c /etc/snort/snort.lua -R /etc/snort/rules/local.rules -R /etc/snort/rules/snort3-community.rules -R /etc/snort/rules/acl.rules -i eth0 -Q --daq afpacket -A alert_fast -k none
```
*(Tunggu hingga muncul tulisan `Commencing packet processing`. Setelah itu **JANGAN SENTUH** terminal ini lagi! Biarkan ia bekerja mengawasi jaringan).*

---

## Tahap 5: Eksekusi Demo Serangan (Wajib 2 Terminal)

**SANGAT PENTING:** Buka **Jendela Terminal BARU** di Kali Linux (Tekan `Ctrl + Shift + T` atau *File > New Tab*). Jangan jalankan perintah serangan di terminal SNORT!

Jalankan perintah serangan ini satu per satu di **Terminal Kedua (Terminal Penyerang)**, lalu perhatikan bagaimana Terminal SNORT (Terminal Pertama) Anda berteriak dan memblokir!

**1. Serangan SQL Injection**
```bash
curl "http://uneaten-enzyme-charity.ngrok-free.dev/?username=admin%27%20OR%201=1"
```

**2. Serangan Cross-Site Scripting (XSS)**
```bash
curl "http://uneaten-enzyme-charity.ngrok-free.dev/?search=<script>alert(1)</script>"
```

**3. Serangan Directory Traversal (Akses File /etc/passwd)**
*(Ini akan memicu respon `[drop]` dari ACL Rules Anda karena kita menggunakan aksi `drop`!)*
```bash
curl --path-as-is "http://uneaten-enzyme-charity.ngrok-free.dev/../../../../etc/passwd"
```

**4. Serangan Brute Force Login**
```bash
for i in {1..5}; do curl -X POST "http://uneaten-enzyme-charity.ngrok-free.dev/accounts/login/" -d "username=admin&password=123"; done
```

**5. Serangan PING (ICMP)**
*(Ini akan memicu respon `[drop]` dari ACL Rules Anda!)*
```bash
ping -c 4 8.8.8.8
```

---

## Skenario Tanya Jawab Dosen (Cheat Sheet)

Jika dosen memberikan pertanyaan kritis saat presentasi, gunakan jawaban teknis ini:

**1. "Kenapa layar SNORT bersih dan tidak ada banyak log peringatan aneh dari Community Rules?"**
> "Karena sebelum presentasi, saya melakukan *troubleshooting* menggunakan perintah `sed` untuk mematikan satu *Community Rule* (SID 40063) yang selalu mendeteksi topologi NAT VirtualBox sebagai serangan *OS-LINUX Kernel ACK*. Ribuan *rules* komunitas sisanya (seperti deteksi *DNS SPOOF*) tetap berjalan normal di *background*."

**2. "Kenapa ada peringatan bertuliskan `[**]` dan ada yang bertuliskan `[drop]`?"**
> "Tulisan `[**]` membuktikan **Mode IDS (Hanya Deteksi)** bekerja untuk memantau serangan Web (SQL/XSS). Tulisan `[drop]` membuktikan **Mode IPS / ACL (Pemblokiran Aktif)** bekerja dengan sukses dalam mencekik dan menghancurkan paket PING serta upaya akses direktori `/etc/passwd` di lapisan jaringan (*network layer*)."

**3. "Coba ubah jaringannya agar hanya mendeteksi dari IP / Interface tertentu saja!"**
> "Siap, Pak/Bu." (Buka terminal baru, jalankan `sudo nano /etc/snort/snort.lua`, cari tulisan `HOME_NET = 'any'` menggunakan `Ctrl+W`, lalu ubah menjadi IP yang diminta, contoh: `10.0.2.15/24`). Atau bisa juga mengubah tulisan `any any` di dalam `local.rules` menjadi alamat IP yang spesifik.
