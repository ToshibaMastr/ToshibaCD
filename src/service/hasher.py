import hashlib
import json

BSIZE = 8


def generate_hash(data):
    data_str = json.dumps(data, separators=(",", ":"))
    hex_hash = hashlib.md5(data_str.encode("utf-8")).hexdigest()
    splithex = [
        hex_hash[i * BSIZE : i * BSIZE + BSIZE] for i in range(len(hex_hash) // BSIZE)
    ]
    return "-".join(splithex).upper()
