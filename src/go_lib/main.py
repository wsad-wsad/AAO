import ctypes
import os
from json import loads

# ambil gobridge.so (file gobridge.go yang sudah dicompile biar bisa di python juga)
lib_path = os.path.dirname(os.path.abspath(__file__))
lib_path = os.path.join(lib_path, "gobridge.so")
lib = ctypes.CDLL(lib_path)

# gunanya untuk kasih tipe data C
lib.Search_user.argtypes = [ctypes.c_char_p, ctypes.c_int]
lib.Search_user.restype = ctypes.c_void_p

lib.FreeString.argtypes = [ctypes.c_void_p]
lib.FreeString.restype = None

"""
- Search_user yang ada di gobridge (file go yang isinya hanya untuk transfer ke python).
- Search_user itu menerima input username (ini diubah jadi binary makanya ada encode dan decode utf-8)
  sedangkan kalau NoFalsePositives itu diubah jadi int karena C mengubah semua bool jadi int 1/0
- Search_user itu return pointer supaya tidak memakai memori terlalu besar.
- pointer itu diganti ke bytes kemudian di decode ke json dan terakhir di loads supaya jadi array
- pointer yang tadi itu harus dihapus/free supaya tidak terjadi memory leaks (banyak variable yang terus menumpuk tanpa dihapus)
"""
def search_user(username: str, NoFalsePositives: bool):
    NoFalsePositives = 1 if NoFalsePositives else 0
    username = username.encode("utf-8")

    ptr = lib.Search_user(username, NoFalsePositives)
    json_bytes = ctypes.string_at(ptr)
    json_data = json_bytes.decode("utf-8")

    lib.FreeString(ptr)

    return loads(json_data)
