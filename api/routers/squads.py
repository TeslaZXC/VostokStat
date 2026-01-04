from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Set
from sqlalchemy.future import select
from sqlalchemy import func, case, desc
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db, MissionSquadStat, GlobalSquad, PlayerStat, Mission
from api.schemas import SquadAggregatedStats, SquadDetailedStats, TotalSquadsResponse
import logging

router = APIRouter(prefix="/squads", tags=["squads"])

async def get_squad_mappings(db: AsyncSession):
    """
    Returns:
      tag_to_canonical: dict[lower_tag -> canonical_name]
      canonical_meta: dict[canonical_name -> {side: str, name: str}]
      canonical_to_tags: dict[canonical_name -> list[str]] # including canonical itself lowerec
    """
    stmt = select(GlobalSquad)
    res = await db.execute(stmt)
    all_squads = res.scalars().all()
    
    tag_to_canonical = {}
    canonical_meta = {}
    canonical_to_tags = {}

    for sq in all_squads:
        if not sq.name:
            continue
        c_name = sq.name.strip() # Strip canonical name
        canonical_meta[c_name] = {"side": sq.side, "name": c_name}
        
        tags = set()
        tags.add(c_name.lower())
        
        if sq.tags:
            for t in sq.tags:
                tags.add(t.strip().lower()) # Strip and lower tags
        
        canonical_to_tags[c_name] = list(tags)
        
        for t in tags:
            tag_to_canonical[t] = c_name
            
    return tag_to_canonical, canonical_meta, canonical_to_tags


@router.get("/total_stats", response_model=TotalSquadsResponse)
async def get_total_squad_stats(db: AsyncSession = Depends(get_db)):
    # 1. Get Mappings
    tag_to_canonical, canonical_meta, _ = await get_squad_mappings(db)
    
    # 2. Fetch ALL MissionSquadStat joined with Mission
    stmt = (
        select(
            MissionSquadStat.squad_tag,
            func.count(MissionSquadStat.mission_id).label("total_missions"),
            func.sum(MissionSquadStat.frags).label("total_frags"),
            func.sum(MissionSquadStat.death).label("total_deaths"),
            MissionSquadStat.side
        )
        .join(Mission, MissionSquadStat.mission_id == Mission.id)
        .where(Mission.duration_time >= 100)
        .group_by(MissionSquadStat.squad_tag)
    )

    result = await db.execute(stmt)
    rows = result.all()

    # 3. Aggregate in Python
    aggregated = {} # valid_name -> {stats}

    for r in rows:
        raw_tag = r.squad_tag
        if not raw_tag:
            continue
            
        lower_tag = raw_tag.strip().lower() # Strip here too just in case
        
        # Decide canonical name
        if lower_tag in tag_to_canonical:
            canon_name = tag_to_canonical[lower_tag]
            side = canonical_meta[canon_name]["side"]
        else:
            # Strictly exclude unmapped squads as per user request
            continue

        if canon_name not in aggregated:
            aggregated[canon_name] = {
                "squad_name": canon_name,
                "total_missions": 0,
                "total_frags": 0,
                "total_deaths": 0,
                "side": side
            }
        
        agg = aggregated[canon_name]
        agg["total_missions"] += r.total_missions
        agg["total_frags"] += (r.total_frags or 0)
        agg["total_deaths"] += (r.total_deaths or 0)
        
        # Prefer side from GlobalSquad if available, else keep first seen
        if lower_tag in tag_to_canonical and canonical_meta[tag_to_canonical[lower_tag]]["side"]:
             agg["side"] = canonical_meta[tag_to_canonical[lower_tag]]["side"]


    # 4. Filter and Format
    west = []
    east = []
    other = []

    for k, v in aggregated.items():
        deaths = v["total_deaths"]
        frags = v["total_frags"]
        kd = round(frags / deaths, 2) if deaths > 0 else frags
        
        item = {
            "squad_name": v["squad_name"],
            "total_missions": v["total_missions"],
            "total_frags": frags,
            "total_deaths": deaths,
            "kd_ratio": kd
        }
        
        side = v["side"]
        if side == "WEST":
            west.append(item)
        elif side == "EAST":
            east.append(item)
        else:
             if v["total_missions"] > 1:
                other.append(item)

    # Sort by KD
    west.sort(key=lambda x: x["kd_ratio"], reverse=True)
    east.sort(key=lambda x: x["kd_ratio"], reverse=True)
    other.sort(key=lambda x: x["kd_ratio"], reverse=True)

    # 5. History
    stmt_hist = (
        select(
            Mission.file_date,
            Mission.mission_name,
            MissionSquadStat.squad_tag,
            MissionSquadStat.frags
        )
        .join(Mission, MissionSquadStat.mission_id == Mission.id)
        .where(Mission.duration_time >= 100)
        .order_by(Mission.file_date)
    )
    hist_res = await db.execute(stmt_hist)
    hist_rows = hist_res.all()
    
    history_map = {} 
    
    for date, m_name, tag, frags in hist_rows:
        if not tag: continue
        key = f"{date}_{m_name}"
        if key not in history_map:
            history_map[key] = {
                "date": date.split(' ')[0], 
                "mission_name": m_name, 
                "west_frags": 0, 
                "east_frags": 0
            }
        
        lower_tag = tag.strip().lower()
        side = None
        if lower_tag in tag_to_canonical:
            c_name = tag_to_canonical[lower_tag]
            side = canonical_meta[c_name]["side"]
        
        if side == "WEST":
            history_map[key]["west_frags"] += (frags or 0)
        elif side == "EAST":
            history_map[key]["east_frags"] += (frags or 0)
            
    return {"west": west, "east": east, "other": other, "history": list(history_map.values())}

@router.get("/top", response_model=List[SquadAggregatedStats])
async def get_top_squads(db: AsyncSession = Depends(get_db)):
    # 1. Get whitelist (Only configured squads)
    tag_to_canonical, canonical_meta, _ = await get_squad_mappings(db)
    
    if not tag_to_canonical:
        return []

    # 2. Fetch stats for ALL tags
    stmt = (
        select(
            MissionSquadStat.squad_tag,
            func.count(MissionSquadStat.mission_id).label("total_missions"),
            func.sum(MissionSquadStat.frags).label("total_frags"),
            func.sum(MissionSquadStat.death).label("total_deaths")
        )
        .join(Mission, MissionSquadStat.mission_id == Mission.id)
        .where(Mission.duration_time >= 100)
        .group_by(MissionSquadStat.squad_tag)
    )
    result = await db.execute(stmt)
    rows = result.all()
    
    # 3. Aggregate only for Whitelisted
    aggregated = {} # canon_name -> stats
    
    for r in rows:
        raw_tag = r.squad_tag
        if not raw_tag: continue
        
        lower_tag = raw_tag.strip().lower()
        if lower_tag in tag_to_canonical:
            c_name = tag_to_canonical[lower_tag]
            
            if c_name not in aggregated:
                aggregated[c_name] = {
                    "squad_name": c_name,
                    "total_missions": 0,
                    "total_frags": 0,
                    "total_deaths": 0
                }
            
            agg = aggregated[c_name]
            agg["total_missions"] += r.total_missions
            agg["total_frags"] += (r.total_frags or 0)
            agg["total_deaths"] += (r.total_deaths or 0)

    output = []
    for k, v in aggregated.items():
        deaths = v["total_deaths"]
        frags = v["total_frags"]
        kd = round(frags / deaths, 2) if deaths > 0 else frags
        
        v["kd_ratio"] = kd
        output.append(v)
        
    output.sort(key=lambda x: x["kd_ratio"], reverse=True)
    return output[:50]

@router.get("/{squad_name}", response_model=SquadDetailedStats)
async def get_squad_stats(squad_name: str, db: AsyncSession = Depends(get_db)):
    tag_to_canonical, canonical_meta, canonical_to_tags = await get_squad_mappings(db)
    
    squad_lower = squad_name.strip().lower()
    
    # --- 1. Resolve to Canonical or Raw ---
    # Case-insensitive match in Python since we have all keys
    target_canonical = None
    target_tags = []

    if squad_lower in tag_to_canonical:
        target_canonical = tag_to_canonical[squad_lower]
        target_tags = canonical_to_tags.get(target_canonical, [])
    else:
        # Try finding canonical by iterating (for mixed case input)
        for c_name in canonical_meta:
            if c_name.lower() == squad_lower:
                target_canonical = c_name
                target_tags = canonical_to_tags.get(c_name, [])
                break
    
    if not target_canonical:
         # Unknown squad: assume specific tag requested
         target_canonical = squad_name # Keep original casing as best guess
         target_tags = [squad_lower]

    # --- 2. Build Search Terms for DB ---
    # Since SQLite lower() breaks on Cyrillic, we must exact match the possible stored values.
    # Stored values are either:
    # A) The Canonical Name (from mapping) -> target_canonical
    # B) The UPPERCASE Tag (if mapping was missing at import time) -> t.upper()
    
    search_terms = set()
    search_terms.add(target_canonical)
    
    # Add UPPER version of canonical just in case
    search_terms.add(target_canonical.upper())
    
    # Add UPPER versions of all aliases
    for t in target_tags:
        search_terms.add(t.upper())
        # Also add capitalized or original if we had them, but we only have lower in target_tags
        # UPPER is the safe fallback for unmapped OCAP tags.

    # --- 3. Aggregate Players ---
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
        .filter(PlayerStat.squad.in_(search_terms)) # Exact match filter
        .filter(Mission.duration_time >= 100)
        .group_by(PlayerStat.name)
        .order_by(desc("total_missions"))
    )
    
    res_players = await db.execute(stmt_players)
    players_rows = res_players.all()
    
    # --- 4. Squad Meta (Missions) ---
    stmt_meta_missions = (
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
        .filter(MissionSquadStat.squad_tag.in_(search_terms)) # Exact match filter
        .filter(Mission.duration_time >= 100)
        .order_by(desc(Mission.file_date))
    )
    
    res_missions = await db.execute(stmt_meta_missions)
    missions_rows = res_missions.all()

    if not missions_rows and not players_rows:
        raise HTTPException(status_code=404, detail="Squad not found")

    # Reuse list for aggregations
    grand_frags = 0
    grand_deaths = 0
    
    # Process Players
    players_list = []
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
        
    # Process Missions
    # Note: A squad might appear multiple times in same mission if it has split tags?
    # e.g. "Alpha" and "[Alpha]" in same mission. 
    # We should aggregate them per mission.
    
    missions_map = {} # mission_id -> data
    
    for m in missions_rows:
        mid = m.id
        if mid not in missions_map:
            missions_map[mid] = {
                "mission_id": m.id,
                "mission_name": m.mission_name,
                "map_name": m.map_name,
                "date": m.file_date,
                "duration_time": m.duration_time,
                "frags": 0,
                "deaths": 0
            }
        
        missions_map[mid]["frags"] += (m.frags or 0)
        missions_map[mid]["deaths"] += (m.death or 0)
        
    final_missions_list = []
    for m in missions_map.values():
        fr = m["frags"]
        d = m["deaths"]
        kd = round(fr / d, 2) if d > 0 else float(fr)
        m["kd"] = kd
        final_missions_list.append(m)
        
    # Sort missions by date descending
    final_missions_list.sort(key=lambda x: x["date"], reverse=True)
    
    squad_kd = round(grand_frags / grand_deaths, 2) if grand_deaths > 0 else float(grand_frags)
    
    return {
        "squad_name": target_canonical,
        "total_missions": len(final_missions_list),
        "total_frags": grand_frags,
        "total_deaths": grand_deaths,
        "kd_ratio": squad_kd,
        "players": players_list,
        "missions": final_missions_list
    }
