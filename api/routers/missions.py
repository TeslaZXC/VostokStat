from fastapi import APIRouter, Depends, HTTPException
from typing import List
from database import get_mission_collection
from api.schemas import MissionSummary, MissionDetail

router = APIRouter(prefix="/missions", tags=["missions"])

@router.get("/", response_model=List[MissionSummary])
async def get_missions(limit: int = 20, skip: int = 0):
    collection = await get_mission_collection()
    cursor = collection.find({}, {
        "players": 0, "squads": 0 # Exclude heavy fields for list view
    }).sort("id", -1).skip(skip).limit(limit)
    
    missions = await cursor.to_list(length=limit)
    return missions

@router.get("/{mission_id}", response_model=MissionDetail)
async def get_mission(mission_id: int):
    collection = await get_mission_collection()
    mission = await collection.find_one({"id": mission_id})
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")
    
    # Process death events (reverse mapping of kills)
    # Map: victim_name -> list of kill events (where they died)
    death_map = {} 
    
    players = mission.get("players", [])
    
    # First pass: collect all kills and assign to victims
    for p in players:
        # p is a dict from mongodb
        killer_name = p.get("name")
        victims = p.get("victims_players", [])
        
        for kill in victims:
            victim_name = kill.get("name")
            if not victim_name:
                continue
            
            if victim_name not in death_map:
                death_map[victim_name] = []
            
            # We add the kill event to the victim's death list
            # The kill event already contains 'killer_name' (if properly saved)
            # If not, we ensure it's there
            if "killer_name" not in kill:
                kill["killer_name"] = killer_name
                
            death_map[victim_name].append(kill)
            
    # Second pass: assign death_events to players
    for p in players:
        p["death_events"] = death_map.get(p["name"], [])
        
    return mission
