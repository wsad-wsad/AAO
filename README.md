Kalau yang pakai fastapi bisa buka /docs untuk api doc

-> Fungsi folder tests adalah untuk testing code yg akan ditambahkan yang belum diimplementasikan

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

## SU
cara gunain gosearch:
1. pakai docker untuk jalanin docker-compose.yaml
2. pakai func `search_web()` di SU.py, bisa lihat input dan outputnya
3. list urlnya bisa dipakai

### SUGW
kalau hanya memakai alur simple seperti:
1. gosearch
2. AI (dengan scraper)
hasilnya kurang memuaskan dan tidak efesien, tetapi bila memakai metode yang ada di flowchart dapat memberikan hasil yang sangat efesien mencapai 80% token effeciency untuk ke summary ai, tetapi masih dalam tahap perkembangan, baru sampai markdown cleaner. serta dapat mengetahui relasi kompleks dengan effesien menggunakan embed model dan vektor db.

## response

dari pada response api gak teratur pakai structure response kayak gini:

```python
def response(status, data):
    return {
  "status": "success",
  "data": {
    "message": "Hello, World!"
  }
}
```
mending pake func `response()`:
```python
return response(valueSatu, valueDua, valueTiga)
```
- valueSatu berisi status misal 200 (wajib integer)
- valueDua berisi data (bisa diisi apa aja bahkan fungsi)
- valueTiga berisi message (wajib string)

- note: Gak semua harus pake `response()`. func `response()` dipake jika response api perlu mengembalikan response data yang kompleks

`Contoh :`
```python
@flapp.get("/test/endpoint")
def test_endpoint():
    return response(200, "Hello, World!", "Success")
```
output:

```json
{
  "status": "success",
  "data": "Hello, World!",
  "message": "Success",
  "meta": {
    "timestamp": "2023-07-25T12:34:56Z",
    "version": "1.0.0"
  }
}
```
