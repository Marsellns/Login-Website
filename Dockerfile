# Gunakan image Python resmi versi 3.11 yang ringan (slim)
FROM python:3.11-slim

# Set environment variables
# Mencegah Python menulis file bytecode (.pyc) ke disk
ENV PYTHONDONTWRITEBYTECODE 1
# Mencegah Python mem-buffer output stdout dan stderr (log langsung muncul)
ENV PYTHONUNBUFFERED 1

# Buat direktori kerja di dalam kontainer
WORKDIR /app

# Install dependensi sistem operasi (dibutuhkan untuk mysqlclient dan argon2)
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Copy file requirements terlebih dahulu untuk memanfaatkan cache Docker
COPY requirements.txt /app/

# Install library Python
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Copy seluruh kode aplikasi ke dalam direktori kerja kontainer
COPY . /app/

# Buka port 8000 agar bisa diakses dari luar kontainer
EXPOSE 8000

# Perintah default saat kontainer dijalankan (menggunakan mode development)
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000", "--settings=secure_auth.settings_dev"]
