Kalau yang pakai fastapi bisa buka /docs untuk api doc

## Cara menjalankan
### Development
1. download docker/podman
2. ke folder AAO
3. jalanin `docker compose -f docker-compose-dev.yaml up --build` 
4. cara matiin tinggal `docker compose down` atau ctrl + c
### Production
perbedaannya di no 3 menjadi:
3. jalanin `docker compose up --build`

Catatan:
- web tersedia di `http://localhost:8080/`, bila mau ke endpoint docs ada di `/docs`
- bila ngerubah code python langsung saja, nanti bisa langsung terjadi di web.
- error dapat terlihat di terminal tempat ngejalanin
- setiap 30 detik terdapat healthcheck

## endpoint tersedia:
- GET `/` Untuk menampilkan frontend
- GET `/api/invest/<target/prompt>` Untuk melakukan scan pada target, atau bisa melakukannya pakai prompt
- GET `/api/` untuk healthcheck
