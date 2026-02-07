Untuk jalanin web appnya jalanin:
- `uvicorn main:fast_app`
- bisa pakai `--reload` untuk ganti api secara instant bila save file

Kalau yang pakai fastapi bisa buka /docs untuk api doc

-> Fungsi folder tests adalah untuk testing code yg akan ditambahkan yang belum diimplementasikan

## endpoint tersedia:
  - GET `/` Untuk menampilkan status server
  - GET `/api/invest/<target/prompt>` Untuk melakukan scan pada target, atau bisa melakukannya pakai prompt
