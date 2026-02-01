import ctypes
from json import loads
import os

lib_path = os.path.dirname(os.path.abspath(__file__))
lib_path = os.path.join(lib_path,"gobridge.so")
lib = ctypes.CDLL(lib_path)

lib.Search_user.argtypes = [ctypes.c_char_p, ctypes.c_int]
lib.Search_user.restype = ctypes.c_void_p

lib.FreeString.argtypes = [ctypes.c_void_p]
lib.FreeString.restype = None

def search_user(username: str, NoFalsePositives: bool):
    NoFalsePositives = 1 if NoFalsePositives else 0
    username = username.encode("utf-8")

    ptr = lib.Search_user(username, NoFalsePositives)
    json_bytes = ctypes.string_at(ptr)
    json_data = json_bytes.decode("utf-8")
    
    lib.FreeString(ptr)
    
    return loads(json_data)