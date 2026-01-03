import json
import shutil
import math
from pathlib import Path
from pymongo import MongoClient
import os

from module.ocap_models import OCAP, Vehicle
from logic.name_logic import extract_name_and_squad
from config import *
from module.ConvertPos import ocap_coords
from functools import lru_cache

@lru_cache(maxsize=200000)
def cached_ocap_coords(x, y, map_name):
    return ocap_coords(x, y, map_name)


OCAPS_PATH.mkdir(exist_ok=True)
TEMP_PATH.mkdir(exist_ok=True)


def get_player_position_ocap(ocap: OCAP, player_id: int, frame: int, map_name: str) -> dict | None:
    player = ocap.players.get(player_id)
    if not player or frame >= len(player.positions):
        return None
    pos = player.positions[frame].coordinates
    rx, ry = cached_ocap_coords(pos.x, pos.y, map_name)
    return {"x": rx, "y": ry}


def calculate_distance(x1, y1, x2, y2):
    return math.dist((x1, y1), (x2, y2))


def get_player_distance(player, map_name: str, step: int = 10, tolerance: float = 0.5) -> float:
    total_distance = 0.0
    positions = player.positions
    if not positions or len(positions) < 2:
        return 0.0

    prev = positions[0].coordinates
    prev_x, prev_y = cached_ocap_coords(prev.x, prev.y, map_name)

    for i in range(step, len(positions), step):
        curr = positions[i].coordinates
        curr_x, curr_y = cached_ocap_coords(curr.x, curr.y, map_name)

        dist = math.dist((prev_x, prev_y), (curr_x, curr_y))
        if dist > tolerance:
            total_distance += dist
            prev_x, prev_y = curr_x, curr_y

    return round(total_distance, 2)


def process_ocap(ocap_file: Path):
    stem = ocap_file.stem
    if "__" in stem:
        file_date = stem.split("__")[0]
    else:
        file_date = "_".join(stem.split("_")[0:3])

    with ocap_file.open("r", encoding="utf-8") as f:
        raw_data = json.load(f)
    mission_name = raw_data.get("missionName", "Unknown Mission")

    existing_mission = collection.find_one({
        "missionName": mission_name,
        "file_date": file_date
    })
    if existing_mission:
        print(f"Миссия '{mission_name}' от {file_date} уже есть в БД, пропускаю.")
        return

    ocap = OCAP.from_file(ocap_file)
    world_name = raw_data.get("worldName", "Unknown World")
    map_name = world_name

    last_mission = collection.find_one(sort=[("id", -1)])
    mission_id = (last_mission["id"] + 1) if last_mission else 1

    players_stats: dict[int, dict] = {}
    unique_players: dict[str, dict] = {} # Map Name -> Stats Object (for deduplication)

    for p in ocap.players.values():
        clean_name, squad = extract_name_and_squad(p.name)
        squad_tag = squad.lower() if squad else None
        distance = get_player_distance(p, map_name)

        if clean_name in unique_players:
             # Player reconnected: update existing record
             existing = unique_players[clean_name]
             existing["distance"] += distance
             # Update squad/side if changed? Usually keeps last or first. keeping first is fine.
             players_stats[p.id] = existing
        else:
            new_stats = {
                "id": p.id,
                "name": clean_name,
                "side": p.side,
                "squad": squad_tag,
                "frags": 0,
                "frags_veh": 0,
                "frags_inf": 0,
                "tk": 0,
                "death": 0,
                "victims_players": [],
                "destroyed_vehicles": [],
                "destroyed_veh": 0,
                "distance": distance
            }
            unique_players[clean_name] = new_stats
            players_stats[p.id] = new_stats

    for e in ocap.events:
        killed = getattr(e, "killed", None)
        killer = getattr(e, "killer", None)
        killer_vehicle = getattr(e, "killer_vehicle", None)

        if not killer or killer.id not in players_stats or not killed:
            continue

        killer_stats = players_stats[killer.id]
        weapon_name = killer_vehicle.name if killer_vehicle else getattr(e, "weapon", "unknown")
        distance = getattr(e, "distance", 0)
        frame = getattr(e, "frame", 0)
        time = round(frame / 49, 2)
        is_killed_vehicle = isinstance(killed, Vehicle)

        if is_killed_vehicle:
            killer_stats["destroyed_veh"] += 1
            killer_stats["destroyed_vehicles"].append({
                "name": getattr(killed, "name", "unknown"),
                "veh_type": str(getattr(killed, "vehicle_type", "unknown")),
                "weapon": weapon_name,
                "distance": distance,
                "kill_type": "veh",
                "frame": frame,
                "time": time,
                "killer_position": get_player_position_ocap(ocap, killer.id, frame, map_name),
                "OcapPos": get_player_position_ocap(ocap, killed.id, frame, map_name)
            })
        else:
            same_side = hasattr(killed, "side") and killer.side == getattr(killed, "side", None)
            if same_side:
                continue

            if killer_vehicle:
                kill_type = "veh"
                killer_stats["frags_veh"] += 1
            else:
                kill_type = "kill"
                killer_stats["frags_inf"] += 1

            killer_stats["victims_players"].append({
                "name": getattr(killed, "name", "unknown"),
                "weapon": weapon_name,
                "distance": distance,
                "killer_name": killer_stats["name"],
                "kill_type": kill_type,
                "frame": frame,
                "time": time,
                "position": get_player_position_ocap(ocap, killed.id, frame, map_name),
                "killer_position": get_player_position_ocap(ocap, killer.id, frame, map_name),
                "OcapPos": get_player_position_ocap(ocap, killed.id, frame, map_name)
            })

        if not is_killed_vehicle and hasattr(killed, "id") and killed.id in players_stats:
            players_stats[killed.id]["death"] += 1

    for stats in unique_players.values():
        stats["frags"] = stats["frags_inf"] + stats["frags_veh"] - stats["tk"]

    win_side = None
    for event in raw_data.get("events", []):
        if isinstance(event, list) and len(event) >= 2 and event[1] == "endMission":
            win_side = event[2][0] if len(event) > 2 and isinstance(event[2], list) else None
            break

    squad_map = {}
    # New logic: iterate over all documents in squads collection
    cursor = squads_collection.find({})
    for squad_doc in cursor:
        name = squad_doc.get("name")
        tags = squad_doc.get("tags", [])
        
        # Support legacy objects if they exist temporarily
        if not tags and "tag" in squad_doc:
            tags = [squad_doc["tag"]]

        if name and tags:
            for t in tags:
                squad_map[t.lower()] = name
    
    valid_squads = set(squad_map.values())

    total_players = 0
    side_counts = {"WEST": 0, "EAST": 0, "GUER": 0}

    for player in unique_players.values():
        squad_tag = player["squad"]
        
        # 1. Map to canonical if exists
        if squad_tag and squad_tag in squad_map:
             player["squad"] = squad_map[squad_tag]
        
        # 2. Proceed regardless of whitelist
        total_players += 1
        side = str(player["side"]).upper()
        if side == "WEST":
            side_counts["WEST"] += 1
        elif side == "EAST":
            side_counts["EAST"] += 1
        elif side in ("GUER", "GUERR", "INDEP", "INDEPENDENT"):
            side_counts["GUER"] += 1

    squads_stats: dict[str, dict] = {}
    for player in unique_players.values():
        squad_tag = player["squad"]
        if not squad_tag or squad_tag not in valid_squads:
            continue

        if squad_tag not in squads_stats:
            squads_stats[squad_tag] = {
                "squad_tag": squad_tag,
                "side": player["side"],
                "frags": 0,
                "death": 0,
                "tk": 0,
                "victims_players": [],
                "squad_players": []
            }

        s = squads_stats[squad_tag]
        s["frags"] += player["frags"]
        s["death"] += player["death"]
        s["tk"] += player["tk"]

        for v in player["victims_players"]:
            s["victims_players"].append({
                "name": v["name"],
                "weapon": v["weapon"],
                "distance": v["distance"],
                "killer_name": v["killer_name"],
                "kill_type": v["kill_type"],
                "frame": v["frame"],
                "time": v["time"],
                "position": v.get("position"),
                "killer_position": v.get("killer_position"),
                "OcapPos": v.get("OcapPos")
            })

        s["squad_players"].append({
            "name": player["name"],
            "frags": player["frags"],
            "death": player["death"],
            "tk": player["tk"],
            "distance": player["distance"]
        })

    data = {
        "id": mission_id,
        "file": ocap_file.name,
        "file_date": file_date,
        "game_type": ocap.game_type,
        "duration_frames": ocap.max_frame,
        "duration_time": round(ocap.max_frame / 49, 2),
        "missionName": mission_name,
        "worldName": world_name,
        "win_side": win_side,
        "players": list(unique_players.values()),
        "squads": list(squads_stats.values()),
        "map": map_name,
        "players_count": {
            "total": total_players,
            "WEST": side_counts["WEST"],
            "EAST": side_counts["EAST"],
            "GUER": side_counts["GUER"]
        }
    }

    collection.insert_one(data)
    print(f"Добавлена миссия '{mission_name}' ({file_date}) с id={mission_id}")

    for item in TEMP_PATH.iterdir():
        if item.is_file():
            item.unlink()
        elif item.is_dir():
            shutil.rmtree(item)
