import os
import json
from config import *

def ocap_coords(x, y, map_name, display_size=256, trim=0, zoom=8):
    map_data = {"worldSize": 10000, "multiplier": 1}

    map_dir = os.path.join(BASE_MAPS_PATH, map_name)
    if os.path.isdir(map_dir):
        subdirs = [d for d in os.listdir(map_dir) if os.path.isdir(os.path.join(map_dir, d))]
        if len(subdirs) == 1:
            subdir = os.path.join(map_dir, subdirs[0])
            map_file = os.path.join(subdir, "map.json")

            if os.path.isfile(map_file):
                try:
                    with open(map_file, "r", encoding="utf-8") as f:
                        map_data = json.load(f)
                except Exception as e:
                    print(f"⚠ Ошибка чтения {map_file}, используется дефолт: {e}")

    world_size = map_data.get("worldSize", 10000)
    multiplier = map_data.get("multiplier", 1)

    px = (x * multiplier) + trim
    py = (world_size * multiplier - (y * multiplier)) + trim  

    rx = py / (world_size * multiplier) * display_size
    ry = px / (world_size * multiplier) * display_size

    rx = -rx

    return rx, ry
