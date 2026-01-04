import json
import shutil
import math
from pathlib import Path
import os
from datetime import datetime

from module.ocap_models import OCAP, Vehicle
from logic.name_logic import extract_name_and_squad
from module.ConvertPos import ocap_coords
from functools import lru_cache

# Database imports
from database import SyncSessionLocal, Mission, PlayerStat, MissionSquadStat, GlobalSquad, get_app_config_sync
from sqlalchemy import select

@lru_cache(maxsize=200000)
def cached_ocap_coords(x, y, map_name):
    return ocap_coords(x, y, map_name)


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
    session = SyncSessionLocal()
    try:
        stem = ocap_file.stem
        if "__" in stem:
            file_date = stem.split("__")[0]
        else:
            file_date = "_".join(stem.split("_")[0:3])

        with ocap_file.open("r", encoding="utf-8") as f:
            raw_data = json.load(f)
        mission_name = raw_data.get("missionName", "Unknown Mission")

        print(f"Checking existing: {mission_name} / {file_date}")
        existing_mission = session.query(Mission).filter_by(
            mission_name=mission_name,
            file_date=file_date
        ).first()

        if existing_mission:
            print(f"Миссия '{mission_name}' от {file_date} уже есть в БД, пропускаю.")
            return

        ocap = OCAP.from_file(ocap_file)
        world_name = raw_data.get("worldName", "Unknown World")
        map_name = world_name
        
        # --- SQUAD MAPPING INITIALIZATION ---
        global_squads = session.query(GlobalSquad).all()
        squad_map = {}
        for gs in global_squads:
            squad_map[gs.name.lower()] = gs.name
            if gs.tags:
                for tag in gs.tags:
                    squad_map[tag.lower()] = gs.name

        players_stats: dict[int, dict] = {}
        unique_players: dict[str, dict] = {} # Map Name -> Stats Object

        for p in ocap.players.values():
            clean_name, squad = extract_name_and_squad(p.name)
            
            # Normalize and Map Squad
            squad_tag = squad.upper() if squad else None
            if squad_tag:
                lower_tag = squad_tag.lower()
                if lower_tag in squad_map:
                    squad_tag = squad_map[lower_tag]

            distance = get_player_distance(p, map_name)

            if clean_name in unique_players:
                 # Player reconnected: update existing record
                 existing = unique_players[clean_name]
                 existing["distance"] += distance
                 players_stats[p.id] = existing
                 
                 # Simple Update: If this player instance has a squad, update the main record
                 # This handles "Joined as Skala -> Rejoined as 1437". 1437 will overwrite Skala.
                 if squad_tag:
                     existing["squad"] = squad_tag
            else:
                 new_stats = {
                    "id": p.id,
                    "name": clean_name,
                    "side": str(p.side),
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
            distance_kill = getattr(e, "distance", 0)
            frame = getattr(e, "frame", 0)
            kill_time = round(frame / 49, 2)
            is_killed_vehicle = isinstance(killed, Vehicle)

            if is_killed_vehicle:
                killer_stats["destroyed_veh"] += 1
                killer_stats["destroyed_vehicles"].append({
                    "name": getattr(killed, "name", "unknown"),
                    "veh_type": str(getattr(killed, "vehicle_type", "unknown"),),
                    "weapon": weapon_name,
                    "distance": distance_kill,
                    "kill_type": "veh",
                    "frame": frame,
                    "time": kill_time,
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
                    "distance": distance_kill,
                    "killer_name": killer_stats["name"],
                    "kill_type": kill_type,
                    "frame": frame,
                    "time": kill_time,
                    "position": get_player_position_ocap(ocap, killed.id, frame, map_name),
                    "killer_position": get_player_position_ocap(ocap, killer.id, frame, map_name),
                    "OcapPos": get_player_position_ocap(ocap, killed.id, frame, map_name)
                })

            if not is_killed_vehicle and hasattr(killed, "id") and killed.id in players_stats:
                players_stats[killed.id]["death"] += 1

        for stats in unique_players.values():
            stats["frags"] = stats["frags_inf"] + stats["frags_veh"] - stats["tk"]
        
        total_players = 0
        side_counts = {"WEST": 0, "EAST": 0, "GUER": 0}

        # Calculate Squad Stats & Side Counts
        squads_stats: dict[str, dict] = {}
        
        for player in unique_players.values():
            total_players += 1
            side = str(player["side"]).upper()
            if side == "WEST": side_counts["WEST"] += 1
            elif side == "EAST": side_counts["EAST"] += 1
            elif side in ("GUER", "GUERR", "INDEP", "INDEPENDENT"): side_counts["GUER"] += 1
            
            squad_tag = player["squad"]
            if not squad_tag:
                continue

            if squad_tag not in squads_stats:
                squads_stats[squad_tag] = {
                    "squad_tag": squad_tag,
                    "side": player["side"],
                    "frags": 0, "death": 0, "tk": 0,
                    "victims_players": [], "squad_players": []
                }

            s = squads_stats[squad_tag]
            s["frags"] += player["frags"]
            s["death"] += player["death"]
            s["tk"] += player["tk"]

            for v in player["victims_players"]:
                s["victims_players"].append(v)

            s["squad_players"].append({
                "name": player["name"],
                "frags": player["frags"],
                "death": player["death"],
                "tk": player["tk"],
                "distance": player["distance"]
            })

        # --- DB INSERTION ---
        win_side = None
        for event in raw_data.get("events", []):
            if isinstance(event, list) and len(event) >= 2 and event[1] == "endMission":
                win_side = event[2][0] if len(event) > 2 and isinstance(event[2], list) else None
                break

        new_mission = Mission(
            file_name=ocap_file.name, file_date=file_date, mission_name=mission_name,
            world_name=world_name, map_name=map_name, game_type=ocap.game_type,
            duration_frames=ocap.max_frame, duration_time=round(ocap.max_frame / 49, 2),
            win_side=str(win_side) if win_side else None, total_players=total_players,
            west_count=side_counts["WEST"], east_count=side_counts["EAST"], guer_count=side_counts["GUER"]
        )
        session.add(new_mission)
        session.flush()

        # Players
        for p in unique_players.values():
            ps = PlayerStat(
                mission_id=new_mission.id, player_uid=p["id"], name=p["name"], side=str(p["side"]),
                squad=p["squad"], frags=p["frags"], frags_veh=p["frags_veh"], frags_inf=p["frags_inf"],
                death=p["death"], tk=p["tk"], destroyed_veh=p["destroyed_veh"], distance=p["distance"],
                victims_players=p["victims_players"], destroyed_vehicles=p["destroyed_vehicles"]
            )
            session.add(ps)

        # Squads
        for sq in squads_stats.values():
            mss = MissionSquadStat(
                mission_id=new_mission.id, squad_tag=sq["squad_tag"], side=str(sq["side"]),
                frags=sq["frags"], death=sq["death"], tk=sq["tk"],
                victims_players=sq["victims_players"], squad_players=sq["squad_players"]
            )
            session.add(mss)

        session.commit()
        print(f"Добавлена миссия '{mission_name}' ({file_date}) [SQLite]")
        
        temp_path_str = get_app_config_sync("TEMP_PATH_STR", "temp")
        TEMP_PATH = Path(temp_path_str)

        for item in TEMP_PATH.iterdir():
            if item.is_file(): item.unlink()
            elif item.is_dir(): shutil.rmtree(item)
    
    except Exception as e:
        session.rollback()
        print(f"Error processing OCAP: {e}")
        raise e
    finally:
        session.close()
