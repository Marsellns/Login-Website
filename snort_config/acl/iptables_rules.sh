#!/bin/bash
# =====================================================================
# IPTABLES ACL SCRIPT FOR DJANGO WEB SERVER
# Description: Mengatur Access Control List menggunakan iptables
# =====================================================================

# Flushing existing rules
iptables -F
iptables -X

# 1. DEFAULT POLICIES (Drop all incoming by default, allow outgoing)
iptables -P INPUT DROP
iptables -P FORWARD DROP
iptables -P OUTPUT ACCEPT

# 2. ALLOW LOCALHOST (Loopback)
# Diperlukan untuk komunikasi Nginx <-> Gunicorn <-> MySQL
iptables -A INPUT -i lo -j ACCEPT
iptables -A OUTPUT -o lo -j ACCEPT

# 3. ALLOW ESTABLISHED & RELATED CONNECTIONS
iptables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT

# 4. ALLOW SSH (Bisa dibatasi per IP Admin)
# Ubah x.x.x.x dengan IP spesifik jika perlu, misal: -s 192.168.1.10
iptables -A INPUT -p tcp --dport 22 -j ACCEPT

# 5. ALLOW HTTP & HTTPS (Untuk Nginx Reverse Proxy)
iptables -A INPUT -p tcp --dport 80 -j ACCEPT
iptables -A INPUT -p tcp --dport 443 -j ACCEPT

# 6. MYSQL ACL (Hanya allow dari localhost)
# Mencegah akses database dari luar server
iptables -A INPUT -p tcp --dport 3306 -s 127.0.0.1 -j ACCEPT
iptables -A INPUT -p tcp --dport 3306 -j DROP

# 7. RATE LIMITING (Anti-DDoS / Brute Force)
# Batasi koneksi HTTP baru (max 20 koneksi per IP per menit)
iptables -A INPUT -p tcp --dport 80 -m conntrack --ctstate NEW -m recent --set
iptables -A INPUT -p tcp --dport 80 -m conntrack --ctstate NEW -m recent --update --seconds 60 --hitcount 20 -j DROP

# Batasi Ping (ICMP) untuk mencegah Ping Flood
iptables -A INPUT -p icmp --icmp-type echo-request -m limit --limit 1/s --limit-burst 5 -j ACCEPT
iptables -A INPUT -p icmp --icmp-type echo-request -j DROP

# 8. LOG DROPPED PACKETS
# Simpan log paket yang didrop di syslog/messages (berguna untuk audit)
iptables -A INPUT -j LOG --log-prefix "IPTABLES-DROP: " --log-level 4

echo "IPTables ACL rules applied successfully!"
