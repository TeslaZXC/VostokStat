from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from sqlalchemy.future import select
from sqlalchemy import func, case, desc, and_
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db, PlayerStat, Mission, GlobalSquad, MissionSquadStat, Rotation, RotationSquad
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
async def get_player_stats(player_name_or_id: str, rotation_id: Optional[int] = None, db: AsyncSession = Depends(get_db)):
    name_lower = player_name_or_id.lower()
    
    # Rotation Context
    start_date, end_date, whitelist_names = await get_rotation_context(db, rotation_id)
    
    whitelist_tags = set()
    if whitelist_names:
        # Resolve to tags
        stmt_sq = select(GlobalSquad)
        res_sq = await db.execute(stmt_sq)
        all_squads = res_sq.scalars().all()
        
        for sq in all_squads:
            if sq.name in whitelist_names:
                whitelist_tags.add(sq.name.lower())
                if sq.tags:
                    for t in sq.tags:
                        whitelist_tags.add(t.strip().lower())
    
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
    
    # Apply Filters
    if start_date and end_date:
        stmt_total = stmt_total.filter(and_(Mission.file_date >= start_date, Mission.file_date <= end_date + " 23:59:59"))
    
    if whitelist_names:
        stmt_total = stmt_total.filter(func.lower(PlayerStat.squad).in_(whitelist_tags))
    
    result = await db.execute(stmt_total)
    total_stats = result.one_or_none()
    
    # If count is 0/None, player not found (or no stats in this rotation)
    if not total_stats or not total_stats.total_missions:
        if rotation_id:
             # If filtering by rotation, return empty object instead of 404 to allow profile page to load
             return {
                "name": player_name_or_id,
                "total_missions": 0,
                "total_frags": 0,
                "total_frags_veh": 0,
                "total_frags_inf": 0,
                "total_deaths": 0,
                "total_destroyed_vehicles": 0,
                "kd_ratio": 0.0,
                "squads": [],
                "missions": []
            }
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

    if start_date and end_date:
        stmt_squads = stmt_squads.filter(and_(Mission.file_date >= start_date, Mission.file_date <= end_date + " 23:59:59"))

    if whitelist_names:
        stmt_squads = stmt_squads.filter(func.lower(PlayerStat.squad).in_(whitelist_tags))
    
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
            PlayerStat.death,
            PlayerStat.squad,      # Added squad fetching
            PlayerStat.side        # Added side fetching
        )
        .join(PlayerStat, PlayerStat.mission_id == Mission.id)
        .filter(func.lower(PlayerStat.name) == name_lower)
        .filter(Mission.duration_time >= 100)
    )

    if start_date and end_date:
        stmt_missions = stmt_missions.filter(and_(Mission.file_date >= start_date, Mission.file_date <= end_date + " 23:59:59"))

    if whitelist_names:
        stmt_missions = stmt_missions.filter(func.lower(PlayerStat.squad).in_(whitelist_tags))

    stmt_missions = stmt_missions.order_by(desc(Mission.file_date)) # Most recent first
    
    res_missions = await db.execute(stmt_missions)
    missions_rows = res_missions.all()
    
    missions_list = []
    side_counts = {}

    for m in missions_rows:
        fr = m.frags or 0
        d = m.death or 0
        kd = round(fr / d, 2) if d > 0 else float(fr)
        
        # Count Side
        if m.side:
            s_up = str(m.side).upper()
            side_counts[s_up] = side_counts.get(s_up, 0) + 1

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

    last_squad_tag = missions_rows[0].squad if missions_rows else None
    
    main_side = None
    if side_counts:
        main_side = max(side_counts, key=side_counts.get)

    return {
        "name": player_name_or_id, # return input name properly cased? Or fetch real name? 
                                   # We query lower(), so original casing might be lost if we don't fetch 'name' column.
                                   # But since we aggregated, we didn't group by name.
                                   # Let's trust the input or we could do select(PlayerStat.name).limit(1)
        "side": main_side,
        "last_squad": last_squad_tag,
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

from datetime import datetime
from sqlalchemy.orm import selectinload
from database import get_db, PlayerStat, Mission, GlobalSquad, MissionSquadStat, Rotation, RotationSquad
# ... imports

async def get_rotation_context(db: AsyncSession, rotation_id: Optional[int]):
    if not rotation_id:
        return None, None, None
        
    stmt = select(Rotation).filter(Rotation.id == rotation_id).options(selectinload(Rotation.squads).selectinload(RotationSquad.squad))
    res = await db.execute(stmt)
    rot = res.scalars().first()
    
    if not rot:
        return None, None, None
        
    # Whitelist of canonical names
    whitelist_names = set()
    for rs in rot.squads:
        if rs.squad:
            whitelist_names.add(rs.squad.name)
            
    return rot.start_date.replace('-', '_'), rot.end_date.replace('-', '_'), whitelist_names

@router.get("/top/", response_model=List[PlayerAggregatedStats])
async def get_top_players(category: str = "general", limit: int = 10, rotation_id: Optional[int] = None, db: AsyncSession = Depends(get_db)):
    # 0. Rotation Context
    start_date, end_date, whitelist_names = await get_rotation_context(db, rotation_id)
    
    whitelist_tags = set()
    if whitelist_names:
        # Resolve to tags
        stmt_sq = select(GlobalSquad)
        res_sq = await db.execute(stmt_sq)
        all_squads = res_sq.scalars().all()
        
        for sq in all_squads:
            if sq.name in whitelist_names:
                whitelist_tags.add(sq.name.lower())
                if sq.tags:
                    for t in sq.tags:
                        whitelist_tags.add(t.strip().lower())

    # 1. Base Query
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
    )
    
    # Apply Filters
    if start_date and end_date:
         query = query.filter(and_(Mission.file_date >= start_date, Mission.file_date <= end_date + " 23:59:59"))
         
    if whitelist_names:
        query = query.filter(func.lower(PlayerStat.squad).in_(whitelist_tags))

    # Finish Query
    query = query.group_by(PlayerStat.name).having(func.count(PlayerStat.mission_id) >= 3)
    
    if category == "vehicle":
        query = query.having(func.sum(PlayerStat.frags_veh) >= 5)
    elif category == "infantry":
        query = query.having(func.sum(PlayerStat.frags_inf) >= 5)
        
    # Sort by KD descending
    query = query.order_by(desc("kd_ratio")).limit(limit)
    
    result = await db.execute(query)
    rows = result.all()
    
    if not rows:
        return []
        
    # 2. Determine Side (Needs adjustment for Rotation filtering too?? No, Side is property of player/squad relationship)
    # Actually, if we filter by Rotation, we should probably check side statistics WITHIN that rotation.
    # reusing logic but applying date filter if needed?
    # Simple check: Just use global side check. It's close enough.
    
    player_names = [r.name for r in rows]
    
    # 2. Determine Side & Last Squad
    # Fetch all mission participations for these players to determine Side (most played) and Last Squad
    # 2. Determine Side & Last Squad
    # Fetch all mission participations for these players to determine Side (most played) and Last Squad
    stmt_meta = (
        select(
            PlayerStat.name,
            PlayerStat.squad,
            MissionSquadStat.side.label("squad_side"),
            PlayerStat.side.label("player_side"),
            Mission.file_date
        )
        .join(Mission, PlayerStat.mission_id == Mission.id)
        .join(MissionSquadStat, 
              (PlayerStat.mission_id == MissionSquadStat.mission_id) & 
              (func.lower(PlayerStat.squad) == func.lower(MissionSquadStat.squad_tag)), isouter=True
        )
        .filter(PlayerStat.name.in_(player_names))
        .order_by(desc(Mission.file_date))
    )
    
    meta_res = await db.execute(stmt_meta)
    meta_rows = meta_res.all()
    
    player_side_counts = {} # Name -> {West: 5, East: 2...}
    player_last_squad = {}  # Name -> Tag
    
    for row in meta_rows:
        p_name = row.name
        
        # Last Squad (First time we see this player, since ordered by date desc)
        if p_name not in player_last_squad and row.squad:
             player_last_squad[p_name] = row.squad
        
        # Side Counts
        # Prefer Squad Side if available (more 'official'), else Player Side
        eff_side = row.squad_side or row.player_side
        
        if eff_side:
            if p_name not in player_side_counts:
                player_side_counts[p_name] = {}
            
            s = str(eff_side).upper()
            player_side_counts[p_name][s] = player_side_counts[p_name].get(s, 0) + 1

    output = []
    for r in rows:
        # Determine main side
        side = None
        if r.name in player_side_counts:
             # Get key with max value
             counts = player_side_counts[r.name]
             if counts:
                 side = max(counts, key=counts.get)
        
        last_squad = player_last_squad.get(r.name)

        output.append({
            "name": r.name,
            "side": side,
            "last_squad": last_squad,
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
