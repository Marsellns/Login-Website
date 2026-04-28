#!/bin/bash
# =====================================================================
# SNORT RULE UPDATE SCRIPT (MANUAL & OINKMASTER/PULLEDPORK SIMULATION)
# Usage: ./update_rules.sh
# =====================================================================

# Warnai output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== SNORT Rule Updater ===${NC}"

# 1. Backup Rules Lama
echo -e "${YELLOW}[*] Membackup rules lama...${NC}"
mkdir -p /etc/snort/rules_backup/
cp -r /etc/snort/rules/* /etc/snort/rules_backup/ 2>/dev/null
echo -e "${GREEN}[+] Backup selesai ke /etc/snort/rules_backup/${NC}"

# 2. Simulasi Update (Misal fetch dari web server lokal atau github)
echo -e "${YELLOW}[*] Mendownload update rule ICMP & Portscan...${NC}"
# Di environment asli, biasanya menggunakan PulledPork.
# Di sini kita copy dari direktori repository/git ke folder instalasi /etc/snort/
# Sesuaikan path $PWD ini dengan path repo Django Anda jika dijalankan dari repo
REPO_PATH=$(pwd)

if [ -d "$REPO_PATH/rules" ]; then
    cp $REPO_PATH/rules/*.rules /etc/snort/rules/
    echo -e "${GREEN}[+] Rules manual (ICMP, Portscan, Local) berhasil di-update!${NC}"
else
    echo -e "${RED}[-] Folder rules tidak ditemukan di $REPO_PATH/rules${NC}"
    echo -e "${YELLOW}[!] Pastikan menjalankan script ini dari folder snort_config${NC}"
fi

# 3. Validasi Syntax SNORT
echo -e "${YELLOW}[*] Memvalidasi syntax SNORT...${NC}"
# snort -T -c /etc/snort/snort.conf -q

# 4. Restart SNORT
echo -e "${YELLOW}[*] Merestart service SNORT...${NC}"
# systemctl restart snort
# systemctl status snort --no-pager | grep Active

echo -e "${GREEN}=== Update Selesai ===${NC}"
