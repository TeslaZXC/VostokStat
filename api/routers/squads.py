from fastapi import APIRouter, HTTPException, Depends
from typing import List
from sqlalchemy.future import select
from sqlalchemy import func, case, desc
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db, MissionSquadStat, GlobalSquad, PlayerStat, Mission
from api.schemas import SquadAggregatedStats, SquadDetailedStats, TotalSquadsResponse

router = APIRouter(prefix="/squads", tags=["squads"])

@router.get("/total_stats", response_model=TotalSquadsResponse)
async def get_total_squad_stats(db: AsyncSession = Depends(get_db)):
    # 1. Fetch all GlobalSquads with a side assigned
    stmt_squads = select(GlobalSquad).where(GlobalSquad.side.is_not(None))
    res_squads = await db.execute(stmt_squads)
    squads_map = {s.name: s.side for s in res_squads.scalars().all()}
    
    if not squads_map:
        return {"west": [], "east": [], "other": []}

    # 2. Aggregate stats for these squads
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
        .join(Mission, MissionSquadStat.mission_id == Mission.id)
        .where(MissionSquadStat.squad_tag.in_(squads_map.keys()))
        .where(Mission.duration_time >= 100)
        .group_by(MissionSquadStat.squad_tag)
        .order_by(desc("kd_ratio"))
    )

    result = await db.execute(stmt)
    rows = result.all()

    west = []
    east = []
    other = []

    for r in rows:
        side = squads_map.get(r.squad_tag)
        stat = {
            "squad_name": r.squad_tag,
            "total_missions": r.total_missions,
            "total_frags": r.total_frags,
            "total_deaths": r.total_deaths,
            "kd_ratio": round(r.kd_ratio, 2)
        }
        
        if side == "WEST":
            west.append(stat)
        elif side == "EAST":
            east.append(stat)
        else:
            other.append(stat)

    # 3. Get History (Frags per mission per side)
    # We query all MissionSquadStat for squads in our map, join with Mission to get date
    stmt_hist = (
        select(
            Mission.file_date,
            Mission.mission_name,
            MissionSquadStat.squad_tag,
            MissionSquadStat.frags
        )
        .join(Mission, MissionSquadStat.mission_id == Mission.id)
        .where(MissionSquadStat.squad_tag.in_(squads_map.keys()))
        .where(Mission.duration_time >= 100)
        .order_by(Mission.file_date) # Chronological order
    )

    hist_res = await db.execute(stmt_hist)
    hist_rows = hist_res.all()
    
    # Process history: Group by mission/date
    # Map: date -> {mission_name, west_frags: 0, east_frags: 0}
    history_map = {}
    
    for date, m_name, tag, frags in hist_rows:
        key = f"{date}_{m_name}" # Unique key per mission
        if key not in history_map:
            history_map[key] = {
                "date": date.split(' ')[0], 
                "mission_name": m_name, 
                "west_frags": 0, 
                "east_frags": 0
            }
        
        side = squads_map.get(tag)
        if side == "WEST":
            history_map[key]["west_frags"] += (frags or 0)
        elif side == "EAST":
            history_map[key]["east_frags"] += (frags or 0)
    
    history_list = list(history_map.values())

    return {"west": west, "east": east, "other": other, "history": history_list}

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
        .join(Mission, MissionSquadStat.mission_id == Mission.id)
        .where(MissionSquadStat.squad_tag.in_(whitelist_names))
        .where(Mission.duration_time >= 100)
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
    
    # 1. Resolve alias to canonical name
    # First, try exact match on name (canonical)
    stmt_canonical = select(GlobalSquad).where(func.lower(GlobalSquad.name) == squad_lower)
    result_canonical = await db.execute(stmt_canonical)
    squad_obj = result_canonical.scalars().first()

    canonical_name = squad_name
    if squad_obj:
        canonical_name = squad_obj.name
    else:
        # Try to find if input is a tag
        # Since tags is JSON list, we might need to fetch all and check in python 
        # (assuming table size is manageable, which valid squads usually are)
        # OR use specific JSON query if supported. 
        # Let's fetch all squads with tags and check.
        stmt_all = select(GlobalSquad)
        res_all = await db.execute(stmt_all)
        all_squads = res_all.scalars().all()
        
        for s in all_squads:
            if s.tags:
                # Check case-insensitive
                if any(t.lower() == squad_lower for t in s.tags):
                    canonical_name = s.name
                    break
    
    # Use the resolved canonical name for queries
    # SQLite lower() is ASCII only, causing issues with Cyrillic names like "3 ОБрСпн".
    # Since we normalized data to canonical name, we should use exact match.
    target_squad = canonical_name

    # 2. Aggregate Players
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
        .join(Mission, PlayerStat.mission_id == Mission.id)
        .filter(PlayerStat.squad == target_squad)
        .filter(Mission.duration_time >= 100)
        .group_by(PlayerStat.name)
        .order_by(desc("total_missions"))
    )
    
    res_players = await db.execute(stmt_players)
    players_rows = res_players.all()
    
    # 3. Get Squad Meta (Total missions for squad itself)
    # Count unique missions where this squad appeared
    stmt_meta = (
        select(func.count(MissionSquadStat.id))
        .join(Mission, MissionSquadStat.mission_id == Mission.id)
        .filter(MissionSquadStat.squad_tag == target_squad)
        .filter(Mission.duration_time >= 100)
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
        
    # 4. Get list of missions this squad played in
    stmt_missions = (
        select(
            Mission.id,
            Mission.mission_name,
            Mission.map_name,
            Mission.file_date,
            Mission.duration_time,
            MissionSquadStat.frags,
            MissionSquadStat.death
        )
        .join(Mission, MissionSquadStat.mission_id == Mission.id)
        .filter(MissionSquadStat.squad_tag == target_squad)
        .filter(Mission.duration_time >= 100)
        .order_by(desc(Mission.file_date))
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
        
    squad_kd = round(grand_frags / grand_deaths, 2) if grand_deaths > 0 else float(grand_frags)
    
    return {
        "squad_name": canonical_name, # Return canonical name
        "total_missions": squad_total_missions,
        "total_frags": grand_frags,
        "total_deaths": grand_deaths,
        "kd_ratio": squad_kd,
        "players": players_list,
        "missions": missions_list
    }
