from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import and_
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db, Mission, GlobalSquad, MissionSquadStat, PlayerStat, Rotation, RotationSquad
from api.schemas import MissionSummary, MissionDetail

# We need to adapt schemas or Models to schemas. 
# Pydantic models expect dictionary or object with attributes. ORM objects work fine with from_attributes (orm_mode).

router = APIRouter(prefix="/missions", tags=["missions"])

async def get_rotation_context(db: AsyncSession, rotation_id: Optional[int]):
    if not rotation_id:
        return None, None
        
    stmt = select(Rotation).filter(Rotation.id == rotation_id)
    res = await db.execute(stmt)
    rot = res.scalars().first()
    
    if not rot:
        return None, None
            
    return rot.start_date.replace('-', '_'), rot.end_date.replace('-', '_')

@router.get("/", response_model=List[MissionSummary])
async def get_missions(limit: int = 20, skip: int = 0, rotation_id: Optional[int] = None, db: AsyncSession = Depends(get_db)):
    start_date, end_date = await get_rotation_context(db, rotation_id)
    
    stmt = (
        select(Mission)
        .filter(Mission.duration_time >= 100)
    )
    
    if start_date and end_date:
        stmt = stmt.filter(and_(Mission.file_date >= start_date, Mission.file_date <= end_date + " 23:59:59"))
    
    result = await db.execute(
        stmt.order_by(Mission.id.desc())
        .offset(skip)
        .limit(limit)
    )
    missions = result.scalars().all()
    
    # Map to schema manually or rely on Pydantic's from_attributes if configured
    # Assuming schemas.MissionSummary has ConfigDict(from_attributes=True) or we map manually
    # Let's verify standard response matches schema. 
    # MissionSummary expects: players_count as dict. 
    # Our Model has individual fields. We need a transformation.
    
    response = []
    for m in missions:
        response.append({
            "id": m.id,
            "file": m.file_name,
            "file_date": m.file_date,
            "game_type": m.game_type,
            "duration_frames": m.duration_frames,
            "duration_time": m.duration_time,
            "missionName": m.mission_name,
            "worldName": m.world_name,
            "win_side": m.win_side,
            "map": m.map_name,
            "players_count": {
                "total": m.total_players,
                "WEST": m.west_count,
                "EAST": m.east_count,
                "GUER": m.guer_count
            }
        })
    return response

@router.get("/{mission_id}", response_model=MissionDetail)
async def get_mission(mission_id: int, db: AsyncSession = Depends(get_db)):
    # Fetch mission with relationships
    stmt = (
        select(Mission)
        .options(
            selectinload(Mission.player_stats),
            selectinload(Mission.squad_stats)
        )
        .filter(Mission.id == mission_id)
    )
    result = await db.execute(stmt)
    mission = result.scalars().first()
    
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")
    
    # Filter squads
    # 1. Fetch valid global squads
    sq_result = await db.execute(select(GlobalSquad))
    global_squads = sq_result.scalars().all()
    
    valid_tags = set()
    for gs in global_squads:
        if gs.tags:
            for t in gs.tags:
                valid_tags.add(t.lower())
    
    # 2. Filter session.squad_stats
    final_squads = []
    for sq_stat in mission.squad_stats:
        if sq_stat.squad_tag and sq_stat.squad_tag.lower() in valid_tags:
            # Append full stats
            final_squads.append({
                "squad_tag": sq_stat.squad_tag,
                "side": sq_stat.side,
                "frags": sq_stat.frags,
                "death": sq_stat.death,
                "tk": sq_stat.tk,
                "squad_players": sq_stat.squad_players # JSON
            })
            
    # Prepare Players with Death Events injection
    # In SQLite implementation, we store victims_players in JSON correctly.
    # Logic in previous version was:
    # "Process death events (reverse mapping of kills)"
    # because the OCAP parsing logic only stored "victims_players" (kills made by me).
    # It didn't store "death_events" (times I was killed).
    # But wait, my new parser logic:
    # `killer_stats["victims_players"].append(...)` -> this saves the KILL event in the KILLER's record.
    # The VICTIM's record just increments `death` counter.
    # So `death_events` IS NOT stored in DB. I must re-calculate it here on read, same as before.
    
    players_response = []
    
    # Build death map: VictimName -> [Event, Event...]
    death_map = {}
    
    # Iterate all players to collect kills
    for p in mission.player_stats:
        killer_name = p.name
        # p.victims_players is a JSON list of dicts
        kills = p.victims_players if p.victims_players else []
        for k in kills:
            victim_name = k.get("name")
            if not victim_name: continue
            
            if victim_name not in death_map:
                death_map[victim_name] = []
            
            # Ensure killer_name is present
            if "killer_name" not in k:
                k["killer_name"] = killer_name
            
            death_map[victim_name].append(k)
            
    # Now build response objects
    for p in mission.player_stats:
        p_dict = {
            "id": p.player_uid,
            "name": p.name,
            "side": p.side,
            "squad": p.squad,
            "frags": p.frags,
            "frags_veh": p.frags_veh,
            "frags_inf": p.frags_inf,
            "tk": p.tk,
            "death": p.death,
            "distance": p.distance,
            "victims_players": p.victims_players if p.victims_players else [],
            "destroyed_vehicles": p.destroyed_vehicles if p.destroyed_vehicles else [],
            "death_events": death_map.get(p.name, [])
        }
        players_response.append(p_dict)

    return {
        "id": mission.id,
        "file": mission.file_name,
        "file_date": mission.file_date,
        "game_type": mission.game_type,
        "duration_frames": mission.duration_frames,
        "duration_time": mission.duration_time,
        "missionName": mission.mission_name,
        "worldName": mission.world_name,
        "win_side": mission.win_side,
        "map": mission.map_name,
        "players_count": {
            "total": mission.total_players,
            "WEST": mission.west_count,
            "EAST": mission.east_count,
            "GUER": mission.guer_count
        },
        "players": players_response,
        "squads": final_squads
    }
