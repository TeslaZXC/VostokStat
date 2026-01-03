import os
import requests
from pathlib import Path
from time import sleep
from datetime import datetime, timedelta

from logic.mission_pars import process_ocap
from config import *

OCAPS_PATH.mkdir(exist_ok=True)
TEMP_PATH.mkdir(exist_ok=True)


def download_new_ocaps(mode="init"):
    today = datetime.today().date()
    older_date = "2099-12-12"

    if mode == "init":
        # Скачиваем вообще всё, игнорируя конфиг
        start_date = datetime(2015, 1, 1).date()
    elif mode == "update":
        start_date = today - timedelta(days=2)
    else:
        raise ValueError("Unknown mode: must be 'init' or 'update'")
        
    params = {
        "newer": start_date.strftime("%Y-%m-%d"),
        "older": older_date
    }
    
    print(f"Запрос миссий: {OCAPS_URL} с параметрами {params}")
    response = requests.get(OCAPS_URL, params=params)
    response.raise_for_status()
    ocaps_list = response.json()

    filtered_ocaps = []
    for o in ocaps_list:
        ocap_date = datetime.strptime(o["date"], "%Y-%m-%d").date()
        if start_date <= ocap_date <= today:
            filtered_ocaps.append(o)

    if not filtered_ocaps:
        if mode == "init":
            print("Миссий за указанный период не найдено.")
        return []
    filtered_ocaps.sort(
        key=lambda x: (datetime.strptime(x["date"], "%Y-%m-%d"), x["filename"]),
        reverse=False
    )
    local_stems = {Path(f).stem for f in os.listdir(OCAPS_PATH)}
    downloaded_files = []

    for ocap in filtered_ocaps:

        orig_filename = Path(ocap["filename"]).stem  
        ext = Path(ocap["filename"]).suffix or ".json"

        mission_name = ocap.get("name") or ocap.get("missionName")
        if mission_name:
            safe_name = "".join(c if c.isalnum() or c in " _-()" else "_" for c in mission_name)
            new_filename = f"{orig_filename}_{safe_name}{ext}"
        else:
            new_filename = f"{orig_filename}{ext}"

        existing_path = None
        for f in os.listdir(OCAPS_PATH):
            if Path(f).stem.startswith(orig_filename):
                existing_path = OCAPS_PATH / f
                break

        if existing_path:
            print(f"Уже скачано (использую существующий файл): {existing_path.name}")
            downloaded_files.append(existing_path)
            continue
        filepath = OCAPS_PATH / new_filename
        try:
            print(f"Скачиваем: {new_filename}")
            r = requests.get(OCAP_URL % ocap["filename"])
            r.raise_for_status()
            filepath.write_text(r.text, encoding="utf-8")
            sleep(1)
            downloaded_files.append(filepath)
        except Exception as ex:
            print(f"Ошибка при скачивании {ocap['filename']}: {ex}")

    return downloaded_files


def main(mode="init"):
    new_ocaps = download_new_ocaps(mode=mode)
    if not new_ocaps:
        return
    for ocap_file in new_ocaps:
        print(f"Обрабатываем: {ocap_file.name}")
        process_ocap(ocap_file)
