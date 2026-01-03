from fastapi import APIRouter, HTTPException, Depends
from typing import List
from sqlalchemy.future import select
from sqlalchemy import func, case, desc
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db, MissionSquadStat, GlobalSquad, PlayerStat
from api.schemas import SquadAggregatedStats, SquadDetailedStats

router = APIRouter(prefix="/squads", tags=["squads"])

@router.get("/top", response_model=List[SquadAggregatedStats])
async def get_top_squads(db: AsyncSession = Depends(get_db)):
    # 1. Get whitelist of valid squads
    stmt_whitelist = select(GlobalSquad)
    res_whitelist = await db.execute(stmt_whitelist)
    all_qs = res_whitelist.scalars().all()
    
    # Flatten names/tags to a set for filtering
    whitelist_names = set()
    for s in all_qs:
        if s.name:
            whitelist_names.add(s.name)
            # Should we add tags? MissionSquadStat uses tags if canonical?
            # mission_pars logic: if tag is known, it saves canonical name in 'squad_tag'?
            # Wait, `squads_stats[squad_tag]` where `squad_tag` comes from player['squad'].
            # And player['squad'] is mapped to canonical name if found.
            # So `MissionSquadStat.squad_tag` SHOULD hold the canonical Name.
    
    if not whitelist_names:
        return []

    # 2. Aggregate MissionSquadStat
    # Filter by squad_tag IN whitelist
    
    kd_expr = case(
        (func.sum(MissionSquadStat.death) > 0, func.sum(MissionSquadStat.frags) / func.sum(MissionSquadStat.death)),
        else_=func.sum(MissionSquadStat.frags)
    ).label("kd_ratio")

    stmt = (
        select(
            MissionSquadStat.squad_tag,
            func.count(MissionSquadStat.mission_id).label("total_missions"),
            func.sum(MissionSquadStat.frags).label("total_frags"),
            func.sum(MissionSquadStat.death).label("total_deaths"),
            kd_expr
        )
        .where(MissionSquadStat.squad_tag.in_(whitelist_names))
        .group_by(MissionSquadStat.squad_tag)
        .order_by(desc("kd_ratio"))
        .limit(50)
    )
    
    result = await db.execute(stmt)
    rows = result.all()
    
    output = []
    for r in rows:
        output.append({
            "squad_name": r.squad_tag,
            "total_missions": r.total_missions,
            "total_frags": r.total_frags,
            "total_deaths": r.total_deaths,
            "kd_ratio": round(r.kd_ratio, 2)
        })
        
    return output

@router.get("/{squad_name}", response_model=SquadDetailedStats)
async def get_squad_stats(squad_name: str, db: AsyncSession = Depends(get_db)):
    # To get detailed stats, we want to aggregate PLAYERS who played in this squad.
    # PlayerStat has 'squad' column which is canonical name (if mapped) or tag.
    
    squad_lower = squad_name.lower()
    
    # 1. Aggregate Players
    stmt_players = (
        select(
            PlayerStat.name,
            func.count(PlayerStat.mission_id).label("total_missions"),
            func.sum(PlayerStat.frags).label("total_frags"),
            func.sum(PlayerStat.frags_veh).label("total_frags_veh"),
            func.sum(PlayerStat.frags_inf).label("total_frags_inf"),
            func.sum(PlayerStat.death).label("total_deaths"),
            func.sum(PlayerStat.destroyed_veh).label("total_destroyed_vehicles")
        )
        .filter(func.lower(PlayerStat.squad) == squad_lower)
        .group_by(PlayerStat.name)
        .order_by(desc("total_missions"))
    )
    
    res_players = await db.execute(stmt_players)
    players_rows = res_players.all()
    
    if not players_rows:
        # Check if squad exists in GlobalSquads just to be sure or return 404?
        # Or check if there are any MissionSquadStat for summary?
        # If no players found, maybe it's empty stats.
        pass

    # 2. Get Squad Meta (Total missions for squad itself)
    # Count unique missions where this squad appeared
    stmt_meta = (
        select(func.count(MissionSquadStat.id))
        .filter(func.lower(MissionSquadStat.squad_tag) == squad_lower)
    )
    res_meta = await db.execute(stmt_meta)
    squad_total_missions = res_meta.scalar_one()
    
    if squad_total_missions == 0 and not players_rows:
        raise HTTPException(status_code=404, detail="Squad not found")

    players_list = []
    grand_frags = 0
    grand_deaths = 0
    
    for p in players_rows:
        deaths = p.total_deaths or 0
        kd = round(p.total_frags / deaths, 2) if deaths > 0 else float(p.total_frags)
        
        grand_frags += p.total_frags or 0
        grand_deaths += deaths
        
        players_list.append({
            "name": p.name,
            "total_missions": p.total_missions,
            "total_frags": p.total_frags,
            "total_frags_veh": p.total_frags_veh or 0,
            "total_frags_inf": p.total_frags_inf or 0,
            "total_deaths": deaths,
            "total_destroyed_vehicles": p.total_destroyed_vehicles or 0,
            "kd_ratio": kd
        })
        
    squad_kd = round(grand_frags / grand_deaths, 2) if grand_deaths > 0 else float(grand_frags)
    
    return {
        "squad_name": squad_name,
        "total_missions": squad_total_missions,
        "total_frags": grand_frags,
        "total_deaths": grand_deaths,
        "kd_ratio": squad_kd,
        "players": players_list
    }
