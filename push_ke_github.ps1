Write-Host "Memulai proses push ke GitHub..." -ForegroundColor Cyan

# 1. Inisialisasi Git
Write-Host "[1/5] Inisialisasi Git..." -ForegroundColor Yellow
git init

# 2. Menghubungkan ke GitHub Marsellns
Write-Host "[2/5] Menghubungkan ke repository GitHub..." -ForegroundColor Yellow
git remote add origin https://github.com/Marsellns/Login-Website.git

# 3. Menambahkan semua file yang aman
Write-Host "[3/5] Menambahkan file ke antrean commit..." -ForegroundColor Yellow
git add .

# 4. Membuat Commit
Write-Host "[4/5] Membuat commit pertama..." -ForegroundColor Yellow
git commit -m "Update: SNORT IDS/IPS + ACL Integration & Dashboard"

# 5. Push ke GitHub
Write-Host "[5/5] Mengupload ke GitHub (Branch Main)..." -ForegroundColor Yellow
git branch -M main
git push -u origin main

Write-Host "✅ SELESAI! Silakan cek https://github.com/Marsellns/Login-Website" -ForegroundColor Green
