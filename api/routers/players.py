from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from sqlalchemy.future import select
from sqlalchemy import func, case, desc
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db, PlayerStat, Mission
from api.schemas import PlayerAggregatedStats

router = APIRouter(prefix="/players", tags=["players"])

@router.get("/search/{name}")
async def search_player(name: str, db: AsyncSession = Depends(get_db)):
    stmt = (
        select(PlayerStat.name)
        .filter(PlayerStat.name.ilike(f"%{name}%"))
        .distinct()
        .limit(10)
    )
    result = await db.execute(stmt)
    return result.scalars().all()

@router.get("/{player_name_or_id}", response_model=PlayerAggregatedStats)
async def get_player_stats(player_name_or_id: str, db: AsyncSession = Depends(get_db)):
    name_lower = player_name_or_id.lower()
    
    # 1. Check if exists and get total stats
    # Group by nothing (aggregate all matches)
    stmt_total = (
        select(
            func.count(PlayerStat.mission_id).label("total_missions"),
            func.sum(PlayerStat.frags).label("total_frags"),
            func.sum(PlayerStat.frags_veh).label("total_frags_veh"),
            func.sum(PlayerStat.frags_inf).label("total_frags_inf"),
            func.sum(PlayerStat.death).label("total_deaths"),
            func.sum(PlayerStat.destroyed_veh).label("total_destroyed_vehicles")
        )
        .join(Mission, PlayerStat.mission_id == Mission.id)
        .filter(func.lower(PlayerStat.name) == name_lower)
        .filter(Mission.duration_time >= 100)
    )
    
    result = await db.execute(stmt_total)
    total_stats = result.one_or_none()
    
    # If count is 0/None, player not found
    if not total_stats or not total_stats.total_missions:
         raise HTTPException(status_code=404, detail="Player not found")
         
    # 2. Get stats per squad
    stmt_squads = (
        select(
            PlayerStat.squad,
            func.count(PlayerStat.mission_id).label("total_missions"),
            func.sum(PlayerStat.frags).label("total_frags"),
            func.sum(PlayerStat.frags_veh).label("total_frags_veh"),
            func.sum(PlayerStat.frags_inf).label("total_frags_inf"),
            func.sum(PlayerStat.death).label("total_deaths"),
            func.sum(PlayerStat.destroyed_veh).label("total_destroyed_vehicles")
        )
        .join(Mission, PlayerStat.mission_id == Mission.id)
        .filter(func.lower(PlayerStat.name) == name_lower)
        .filter(Mission.duration_time >= 100)
        .group_by(PlayerStat.squad)
        .order_by(desc("total_missions"))
    )
    
    squad_results = await db.execute(stmt_squads)
    squads_rows = squad_results.all()
    
    # Process Results
    t_frags = total_stats.total_frags or 0
    t_deaths = total_stats.total_deaths or 0
    kd_ratio = round(t_frags / t_deaths, 2) if t_deaths > 0 else float(t_frags)
    
    squads_list = []
    for r in squads_rows:
        s_frags = r.total_frags or 0
        s_deaths = r.total_deaths or 0
        s_kd = round(s_frags / s_deaths, 2) if s_deaths > 0 else float(s_frags)
        
        squads_list.append({
            "squad": r.squad if r.squad else "No Squad",
            "total_missions": r.total_missions,
            "total_frags": s_frags,
            "total_frags_veh": r.total_frags_veh or 0,
            "total_frags_inf": r.total_frags_inf or 0,
            "total_deaths": s_deaths,
            "total_destroyed_vehicles": r.total_destroyed_vehicles or 0,
            "kd_ratio": s_kd
        })
        
    # 3. Get list of missions played
    stmt_missions = (
        select(
            Mission.id,
            Mission.mission_name,
            Mission.map_name,
            Mission.file_date,
            Mission.duration_time,
            PlayerStat.frags,
            PlayerStat.death
        )
        .join(PlayerStat, PlayerStat.mission_id == Mission.id)
        .filter(func.lower(PlayerStat.name) == name_lower)
        .filter(Mission.duration_time >= 100)
        .order_by(desc(Mission.file_date)) # Most recent first
        # .limit(50) # Optional limit
    )
    
    res_missions = await db.execute(stmt_missions)
    missions_rows = res_missions.all()
    
    missions_list = []
    for m in missions_rows:
        fr = m.frags or 0
        d = m.death or 0
        kd = round(fr / d, 2) if d > 0 else float(fr)
        
        missions_list.append({
            "mission_id": m.id,
            "mission_name": m.mission_name,
            "map_name": m.map_name,
            "date": m.file_date,
            "duration_time": m.duration_time,
            "frags": fr,
            "deaths": d,
            "kd": kd
        })

    return {
        "name": player_name_or_id, # return input name properly cased? Or fetch real name? 
                                   # We query lower(), so original casing might be lost if we don't fetch 'name' column.
                                   # But since we aggregated, we didn't group by name.
                                   # Let's trust the input or we could do select(PlayerStat.name).limit(1)
        "total_missions": total_stats.total_missions,
        "total_frags": t_frags,
        "total_frags_veh": total_stats.total_frags_veh or 0,
        "total_frags_inf": total_stats.total_frags_inf or 0,
        "total_deaths": t_deaths,
        "total_destroyed_vehicles": total_stats.total_destroyed_vehicles or 0,
        "kd_ratio": kd_ratio,
        "squads": squads_list,
        "missions": missions_list
    }

@router.get("/top/", response_model=List[PlayerAggregatedStats])
async def get_top_players(category: str = "general", limit: int = 10, db: AsyncSession = Depends(get_db)):
    
    # Define KD expression
    kd_expr = case(
        (func.sum(PlayerStat.death) > 0, func.sum(PlayerStat.frags) / func.sum(PlayerStat.death)),
        else_=func.sum(PlayerStat.frags)
    ).label("kd_ratio")
    
    query = (
        select(
            PlayerStat.name,
            func.count(PlayerStat.mission_id).label("total_missions"),
            func.sum(PlayerStat.frags).label("total_frags"),
            func.sum(PlayerStat.frags_veh).label("total_frags_veh"),
            func.sum(PlayerStat.frags_inf).label("total_frags_inf"),
            func.sum(PlayerStat.death).label("total_deaths"),
            func.sum(PlayerStat.destroyed_veh).label("total_destroyed_vehicles"),
            kd_expr
        )
        .join(Mission, PlayerStat.mission_id == Mission.id)
        .filter(Mission.duration_time >= 100)
        .group_by(PlayerStat.name)
        .having(func.count(PlayerStat.mission_id) >= 3)
    )
    
    if category == "vehicle":
        query = query.having(func.sum(PlayerStat.frags_veh) >= 5)
    elif category == "infantry":
        query = query.having(func.sum(PlayerStat.frags_inf) >= 5)
        
    # Sort by KD descending
    query = query.order_by(desc("kd_ratio")).limit(limit)
    
    result = await db.execute(query)
    rows = result.all()
    
    output = []
    for r in rows:
        output.append({
            "name": r.name,
            "total_missions": r.total_missions,
            "total_frags": r.total_frags or 0,
            "total_frags_veh": r.total_frags_veh or 0,
            "total_frags_inf": r.total_frags_inf or 0,
            "total_deaths": r.total_deaths or 0,
            "total_destroyed_vehicles": r.total_destroyed_vehicles or 0,
            "kd_ratio": round(r.kd_ratio, 2) if r.kd_ratio else 0.0,
            "squads": []
        })
        
    return output
