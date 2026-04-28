# Panduan Pengerjaan SNORT di Kali Linux

Snort adalah sistem deteksi intrusi jaringan (Network Intrusion Detection System / NIDS) tipe *open-source*. Berikut adalah tahapan lengkap dari instalasi hingga pembuatan *rules* untuk mendeteksi serangan di Kali Linux.

---

## Tahap 1: Instalasi Snort

1. **Update Repository Kali Linux**
   Buka terminal di Kali Linux dan jalankan perintah:
   ```bash
   sudo apt update && sudo apt upgrade -y
   ```

2. **Install Snort**
   ```bash
   sudo apt install snort -y
   ```
   *Catatan:* Saat proses instalasi, Anda akan diminta memasukkan rentang IP jaringan Anda (Network Range). Misalnya `192.168.1.0/24`. Anda bisa mengecek IP Anda menggunakan perintah `ip a` atau `ifconfig`.

---

## Tahap 2: Konfigurasi Dasar

1. **Cari Tahu Interface Jaringan Anda**
   ```bash
   ip a
   ```
   Perhatikan nama *interface* yang terhubung ke internet/target (biasanya `eth0` atau `wlan0`).

2. **Edit File Konfigurasi Snort (`snort.conf`)**
   Gunakan editor teks seperti `nano`:
   ```bash
   sudo nano /etc/snort/snort.conf
   ```
   Cari baris `ipvar HOME_NET any` dan ubah `any` menjadi rentang IP Anda:
   ```text
   ipvar HOME_NET 192.168.1.0/24
   ```
   *(Simpan dengan menekan `Ctrl+O`, `Enter`, lalu `Ctrl+X`).*

3. **Verifikasi Konfigurasi**
   Pastikan tidak ada error (ganti `eth0` dengan interface Anda):
   ```bash
   sudo snort -T -c /etc/snort/snort.conf -i eth0
   ```
   Jika di akhir muncul tulisan **"Snort successfully validated the configuration!"**, berarti konfigurasi sudah aman.

---

## Tahap 3: Pembuatan Aturan (Rules) Kustom

Snort mendeteksi serangan berdasarkan *rules*. Kita akan membuat *rules* sederhana untuk mendeteksi ping (ICMP) atau serangan XSS/SQL Injection.

1. **Buka File Rules Lokal**
   ```bash
   sudo nano /etc/snort/rules/local.rules
   ```

2. **Tambahkan Rules Sederhana**
   Tambahkan baris berikut di paling bawah file:

   **A. Deteksi Ping (ICMP)**
   ```text
   alert icmp any any -> $HOME_NET any (msg:"Peringatan: Ada aktivitas PING terdeteksi!"; sid:1000001; rev:1;)
   ```

   **B. Deteksi Serangan XSS Sederhana**
   ```text
   alert tcp any any -> $HOME_NET 8000 (msg:"Peringatan: Potensi XSS <script> terdeteksi!"; content:"<script>"; sid:1000002; rev:1;)
   ```

   **C. Deteksi Potensi SQL Injection**
   ```text
   alert tcp any any -> $HOME_NET 8000 (msg:"Peringatan: Potensi SQL Injection (' OR 1=1)"; content:"' OR 1=1"; sid:1000003; rev:1;)
   ```

---

## Tahap 4: Menjalankan Snort (Mode Deteksi)

Sekarang kita akan menyalakan Snort agar ia mendengarkan lalu lintas jaringan dan mencetak peringatan ke layar terminal.

Jalankan perintah ini (ganti `eth0` dengan interface Anda):
```bash
sudo snort -A console -q -c /etc/snort/snort.conf -i eth0
```
*(Snort akan terlihat diam, artinya ia sedang memantau/mendengarkan di latar belakang).*

---

## Tahap 5: Pengujian (Testing) Serangan

Buka **Terminal Baru** di Kali Linux (biarkan terminal Snort tetap menyala), lalu lakukan pengujian:

1. **Uji Coba PING**
   Ping ke IP komputer target Anda:
   ```bash
   ping 192.168.1.X
   ```
   👉 *Lihat ke terminal Snort, seharusnya akan muncul log merah "Peringatan: Ada aktivitas PING terdeteksi!"*

2. **Uji Coba XSS / Serangan Web**
   Jika Anda menjalankan server Django di Kali Linux pada port 8000, Anda bisa mencoba mengirim request HTTP via `curl`:
   ```bash
   curl "http://127.0.0.1:8000/accounts/login/?username=<script>alert('XSS')</script>"
   ```
   👉 *Snort akan langsung berteriak "Peringatan: Potensi XSS terdeteksi!" karena ia melihat ada string `<script>` melintas di jaringan.*

## Kesimpulan Presentasi
Jika ini untuk keperluan presentasi tugas kuliah, Anda bisa menunjukkan:
1. File `local.rules` yang sudah Anda modifikasi.
2. Menyalakan Snort di mode console.
3. Melakukan eksekusi serangan (misal Ping atau Curl payload XSS).
4. Menunjukkan layar bahwa Snort berhasil menangkap paket tersebut secara *Real-Time*.
