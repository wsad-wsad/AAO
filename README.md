Kalau yang pakai fastapi bisa buka /docs untuk api doc

-> Fungsi folder tests adalah untuk testing code yg akan ditambahkan yang belum diimplementasikan

## Cara ngejalanin
1. download docker/podman
2. ke folder AAO
3. jalanin `docker compose up --build` 
4. cara matiin tinggal `docker compose down` atau ctrl + c

Catatan:
- web tersedia di `http://localhost:8080/`, bila mau ke endpoint docs ada di `/docs`
- bila ngerubah code python langsung saja, nanti bisa langsung terjadi di web.
- error dapat terlihat di terminal tempat ngejalanin
- setiap 30 detik terdapat healthcheck

## endpoint tersedia:
- GET `/` Untuk menampilkan frontend
- GET `/api/invest/<target/prompt>` Untuk melakukan scan pada target, atau bisa melakukannya pakai prompt
- GET `/api/` untuk healthcheck

## SU
cara gunain gosearch:
1. pakai docker untuk jalanin docker-compose.yaml
2. pakai func search_web() di SU.py, bisa lihat input dan outputnya
3. list urlnya bisa dipakai

### SUGW
kalau hanya memakai alur simple seperti:
1. gosearch
2. AI (dengan scraper)
hasilnya kurang memuaskan dan tidak efesien, tetapi bila memakai metode yang ada di flowchart dapat memberikan hasil yang sangat efesien mencapai 80% token effeciency untuk ke summary ai, tetapi masih dalam tahap perkembangan, baru sampai markdown cleaner. serta dapat mengetahui relasi kompleks dengan effesien menggunakan embed model dan vektor db.