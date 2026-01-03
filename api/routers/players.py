from fastapi import APIRouter, HTTPException
from typing import List, Optional
from database import get_mission_collection
from api.schemas import PlayerAggregatedStats

router = APIRouter(prefix="/players", tags=["players"])

@router.get("/search/{name}")
async def search_player(name: str):
    # This is a bit expensive if not indexed properly, ideally we'd have a separate players collection
    collection = await get_mission_collection()
    pipeline = [
        {"$unwind": "$players"},
        {"$match": {"players.name": {"$regex": name, "$options": "i"}}},
        {"$group": {"_id": "$players.name"}},
        {"$limit": 10}
    ]
    cursor = collection.aggregate(pipeline)
    result = await cursor.to_list(length=10)
    return [r["_id"] for r in result]

@router.get("/{player_name_or_id}", response_model=PlayerAggregatedStats)
async def get_player_stats(player_name_or_id: str):
    collection = await get_mission_collection()
    name_lower = player_name_or_id.lower()
    
    match_stage = {"players.name": name_lower}
    
    pipeline = [
        {"$match": match_stage},
        {"$unwind": "$players"},
        {"$match": {"players.name": name_lower}},
        
        # 1. Group by Squad first
        {
            "$group": {
                "_id": {
                    "name": "$players.name",
                    "squad": "$players.squad"
                },
                "total_missions": {"$sum": 1},
                "total_frags": {"$sum": "$players.frags"},
                "total_frags_veh": {"$sum": "$players.frags_veh"},
                "total_frags_inf": {"$sum": "$players.frags_inf"},
                "total_deaths": {"$sum": "$players.death"},
                "total_destroyed_vehicles": {"$sum": "$players.destroyed_veh"}
            }
        },
        
        # 2. Group by Player to aggregate totals and build valid squad list
        {
            "$group": {
                "_id": "$_id.name",
                "total_missions": {"$sum": "$total_missions"},
                "total_frags": {"$sum": "$total_frags"},
                "total_frags_veh": {"$sum": "$total_frags_veh"},
                "total_frags_inf": {"$sum": "$total_frags_inf"},
                "total_deaths": {"$sum": "$total_deaths"},
                "total_destroyed_vehicles": {"$sum": "$total_destroyed_vehicles"},
                "squads": {
                    "$push": {
                        "squad": "$_id.squad",
                        "total_missions": "$total_missions",
                        "total_frags": "$total_frags",
                        "total_frags_veh": "$total_frags_veh",
                        "total_frags_inf": "$total_frags_inf",
                        "total_deaths": "$total_deaths",
                        "total_destroyed_vehicles": "$total_destroyed_vehicles",
                    }
                }
            }
        }
    ]
    
    cursor = collection.aggregate(pipeline)
    result = await cursor.to_list(length=1)
    
    if not result:
        raise HTTPException(status_code=404, detail="Player not found")
        
    stats = result[0]
    total_deaths = stats["total_deaths"]
    kd_ratio = round(stats["total_frags"] / total_deaths, 2) if total_deaths > 0 else float(stats["total_frags"])
    
    # Process squads to add KD and handle None squads if any
    squads_list = []
    for s in stats.get("squads", []):
        s_deaths = s["total_deaths"]
        s_kd = round(s["total_frags"] / s_deaths, 2) if s_deaths > 0 else float(s["total_frags"])
        
        squads_list.append({
            "squad": s["squad"] if s["squad"] else "No Squad",
            "total_missions": s["total_missions"],
            "total_frags": s["total_frags"],
            "total_frags_veh": s["total_frags_veh"],
            "total_frags_inf": s["total_frags_inf"],
            "total_deaths": s["total_deaths"],
            "total_destroyed_vehicles": s["total_destroyed_vehicles"],
            "kd_ratio": s_kd
        })

    # Sort squads by most missions or frags? Let's sort by missions desc
    squads_list.sort(key=lambda x: x["total_missions"], reverse=True)

    return {
        "name": stats["_id"],
        "total_missions": stats["total_missions"],
        "total_frags": stats["total_frags"],
        "total_frags_veh": stats["total_frags_veh"],
        "total_frags_inf": stats["total_frags_inf"],
        "total_deaths": total_deaths,
        "total_destroyed_vehicles": stats["total_destroyed_vehicles"],
        "kd_ratio": kd_ratio,
        "squads": squads_list
    }

@router.get("/top/", response_model=List[PlayerAggregatedStats])
async def get_top_players(category: str = "general", limit: int = 10):
    collection = await get_mission_collection()
    
    # Initial aggregation
    pipeline = [
        {"$unwind": "$players"},
        {
            "$group": {
                "_id": "$players.name",
                "total_missions": {"$sum": 1},
                "total_frags": {"$sum": "$players.frags"},
                "total_frags_veh": {"$sum": "$players.frags_veh"},
                "total_frags_inf": {"$sum": "$players.frags_inf"},
                "total_deaths": {"$sum": "$players.death"},
                "total_destroyed_vehicles": {"$sum": "$players.destroyed_veh"}
            }
        },
        # Filter for minimal activity to avoid plotting 1-kill/0-death outliers
        {"$match": {"total_missions": {"$gte": 3}}}
    ]
    
    if category == "vehicle":
        # Must have significant vehicle kills to be in vehicle top
        pipeline.append({"$match": {"total_frags_veh": {"$gte": 5}}})
    elif category == "infantry":
        pipeline.append({"$match": {"total_frags_inf": {"$gte": 5}}})
        
    pipeline.extend([
        # Compute KD directly in pipeline for sorting
        {
            "$addFields": {
                "kd_ratio": {
                    "$cond": [
                        {"$gt": ["$total_deaths", 0]},
                        {"$divide": ["$total_frags", "$total_deaths"]},
                        "$total_frags"
                    ]
                }
            }
        },
        {"$sort": {"kd_ratio": -1}},
        {"$limit": limit}
    ])
    
    cursor = collection.aggregate(pipeline)
    result = await cursor.to_list(length=limit)
    
    output = []
    for r in result:
        output.append({
            "name": r["_id"],
            "total_missions": r["total_missions"],
            "total_frags": r["total_frags"],
            "total_frags_veh": r["total_frags_veh"],
            "total_frags_inf": r["total_frags_inf"],
            "total_deaths": r["total_deaths"],
            "total_destroyed_vehicles": r["total_destroyed_vehicles"],
            "kd_ratio": round(r["kd_ratio"], 2),
            "squads": [] # Omit squads detail for top list
        })
        
    return output
