# 🛡️ SNORT IDS/IPS & ACL Integration Guide (Kali Linux)

Direktori ini berisi seluruh konfigurasi yang dibutuhkan untuk mengintegrasikan SNORT dan ACL (iptables) guna melindungi Web Server Django Anda.

## 📁 Struktur Direktori
- `snort.conf` : Konfigurasi utama engine SNORT.
- `rules/` : Kumpulan rule pendeteksi (SQLi, XSS, Brute Force, ICMP, Port Scan).
- `update_rules.sh` : Script Bash untuk update dan memvalidasi rule (mirip dengan PulledPork).
- `acl/iptables_rules.sh` : Script Bash untuk Access Control List pada level jaringan.

---

## 🚀 Cara Implementasi di Kali Linux VM

### 1. Instalasi SNORT
Jika belum terinstall di Kali Linux:
```bash
sudo apt update
sudo apt install snort
```
*(Saat diminta nama interface, isikan interface jaringan Anda, misal `eth0`)*

### 2. Copy Konfigurasi ke Sistem
Copy folder `rules` dan file `snort.conf` ke direktori instalasi SNORT di Kali Linux:
```bash
# Backup config bawaan
sudo cp /etc/snort/snort.conf /etc/snort/snort.conf.backup

# Copy config dan rule buatan kita
sudo cp snort.conf /etc/snort/
sudo cp rules/*.rules /etc/snort/rules/
```

### 3. Eksekusi ACL (IPTables)
Script ini akan langsung menerapkan firewall untuk melindungi Nginx, Django, dan MySQL.
```bash
cd acl
sudo chmod +x iptables_rules.sh
sudo ./iptables_rules.sh
```

### 4. Uji Coba Rule Manual & Update
Jika Anda merubah rule ICMP atau Port, jalankan script update:
```bash
sudo chmod +x update_rules.sh
sudo ./update_rules.sh
```

### 5. Jalankan SNORT
Jalankan SNORT dalam mode IDS (Intrusion Detection System) dengan logging ke `/var/log/snort/`:
```bash
sudo snort -A fast -c /etc/snort/snort.conf -i eth0 -D
```
*(Ganti `eth0` dengan interface yang sesuai di Kali VM Anda)*

### 6. Simulasi Serangan (Testing)
Dari komputer host atau VM lain, cobalah lakukan serangan:

- **Nmap Scan:** `nmap -sS <IP_KALI>`
- **Ping Flood:** `ping -f <IP_KALI>`
- **SQLi Web:** Buka browser dan arahkan ke login dengan payload `UNION SELECT`
- **Brute Force:** Coba login salah berkali-kali dengan cepat

Lalu pantau log di Django Web Dashboard Anda!
