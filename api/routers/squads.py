from fastapi import APIRouter, HTTPException
from typing import List
from database import get_mission_collection, get_squads_collection
from api.schemas import SquadAggregatedStats, SquadDetailedStats

router = APIRouter(prefix="/squads", tags=["squads"])

@router.get("/top", response_model=List[SquadAggregatedStats])
async def get_top_squads():
    # 1. Get whitelist of current squads (groups)
    squads_col = await get_squads_collection()
    cursor = squads_col.find({}, {"name": 1})
    whitelist_docs = await cursor.to_list(length=1000)
    # The whitelist logic stores keys in lower case in parsing, but here storing canonical Name?
    # In mission_pars.py, we store canonical name in `player['squad']` AND `squads_stats` keys.
    # So we should match against the `name` field from admin panel.
    whitelist = [d.get("name") for d in whitelist_docs if d.get("name")]
    
    if not whitelist:
        return []

    collection = await get_mission_collection()
    
    pipeline = [
        # Pre-filter documents that have at least one valid squad to speed up unwind? 
        # Actually MongoDB optimization might handle it, but explicit match is safe.
        {"$match": {"squads.squad_tag": {"$in": whitelist}}},
        {"$unwind": "$squads"},
        {"$match": {"squads.squad_tag": {"$in": whitelist}}},
        
        {"$group": {
            "_id": "$squads.squad_tag", 
            "total_missions": {"$sum": 1},
            "total_frags": {"$sum": "$squads.frags"},
            "total_deaths": {"$sum": "$squads.death"}
        }},
        
        # Filter out squads with very few games if necessary, e.g. < 3
        # {"$match": {"total_missions": {"$gte": 3}}},

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
        {"$limit": 50}
    ]
    
    cursor = collection.aggregate(pipeline)
    results = await cursor.to_list(length=50)
    
    output = []
    for r in results:
        output.append({
            "squad_name": r["_id"],
            "total_missions": r["total_missions"],
            "total_frags": r["total_frags"],
            "total_deaths": r["total_deaths"],
            "kd_ratio": round(r["kd_ratio"], 2)
        })
        
    return output
        
@router.get("/{squad_name}", response_model=SquadDetailedStats)
async def get_squad_stats(squad_name: str):
    collection = await get_mission_collection()
    squad_lower = squad_name.lower()
    
    pipeline = [
        {"$match": {"players.squad": {"$regex": f"^{squad_lower}$", "$options": "i"}}},
        {"$unwind": "$players"},
        {"$match": {"players.squad": {"$regex": f"^{squad_lower}$", "$options": "i"}}},
        
        {"$group": {
            "_id": "$players.name",
            "total_missions": {"$sum": 1},
            "total_frags": {"$sum": "$players.frags"},
            "total_frags_veh": {"$sum": "$players.frags_veh"},
            "total_frags_inf": {"$sum": "$players.frags_inf"},
            "total_deaths": {"$sum": "$players.death"},
            "total_destroyed_vehicles": {"$sum": "$players.destroyed_veh"}
        }},
        {"$sort": {"total_missions": -1}},
        
        {"$group": {
            "_id": None,
            "total_missions": {"$sum": "$total_missions"}, # This sums member missions, which effectively is total man-missions. 
            # Wait, squad total missions is different from sum of man-missions.
            # But usually for squad stats "missions" means "missions the squad participated in".
            # Aggregating by player loses the unique mission count for the squad itself.
            # But the request says "отдельная статистика отрядов, там будут указываться все игроки отрядов и их статистика".
            # If I want true Squad Missions count, I need a different facet. 
            # But typically sum of frags is correct.
            # For simplicity/correctness of "Squad total missions", we should count unique missions where ANY player of this squad played.
            # But with this pipeline, we have grouped by player.
            # Let's start with just player list aggregation and we can sum up frags/deaths. 
            # For "Squad Total Missions", strictly speaking it's "how many mission files".
            # I can compute that separately or use a facet.
            
            "players": {"$push": {
                "name": "$_id",
                "total_missions": "$total_missions",
                "total_frags": "$total_frags",
                "total_frags_veh": "$total_frags_veh",
                "total_frags_inf": "$total_frags_inf",
                "total_deaths": "$total_deaths",
                "total_destroyed_vehicles": "$total_destroyed_vehicles"
            }},
            "grand_total_frags": {"$sum": "$total_frags"},
            "grand_total_deaths": {"$sum": "$total_deaths"}
        }}
    ]
    
    # We also need the real unique mission count for the squad.
    # Parallel query or FaceT?
    # Let's do a Facet to be clean.
    
    pipeline = [
        {"$match": {"players.squad": {"$regex": f"^{squad_name}$", "$options": "i"}}},
        {"$facet": {
            "squad_meta": [
                {"$count": "count"}
            ],
            "players_agg": [
                {"$unwind": "$players"},
                {"$match": {"players.squad": {"$regex": f"^{squad_name}$", "$options": "i"}}},
                {"$group": {
                    "_id": "$players.name",
                    "total_missions": {"$sum": 1},
                    "total_frags": {"$sum": "$players.frags"},
                    "total_frags_veh": {"$sum": "$players.frags_veh"},
                    "total_frags_inf": {"$sum": "$players.frags_inf"},
                    "total_deaths": {"$sum": "$players.death"},
                    "total_destroyed_vehicles": {"$sum": "$players.destroyed_veh"}
                }},
                {"$sort": {"total_missions": -1}}
            ]
        }}
    ]
    
    cursor = collection.aggregate(pipeline)
    result = await cursor.to_list(length=1)
    
    if not result or (not result[0]["squad_meta"] and not result[0]["players_agg"]):
        raise HTTPException(status_code=404, detail="Squad not found")
        
    data = result[0]
    squad_missions_count = data["squad_meta"][0]["count"] if data["squad_meta"] else 0
    players_data = data["players_agg"]
    
    players_list = []
    grand_frags = 0
    grand_deaths = 0
    
    for p in players_data:
        deaths = p["total_deaths"]
        kd = round(p["total_frags"] / deaths, 2) if deaths > 0 else float(p["total_frags"])
        
        grand_frags += p["total_frags"]
        grand_deaths += deaths
        
        players_list.append({
            "name": p["_id"],
            "total_missions": p["total_missions"],
            "total_frags": p["total_frags"],
            "total_frags_veh": p["total_frags_veh"],
            "total_frags_inf": p["total_frags_inf"],
            "total_deaths": p["total_deaths"],
            "total_destroyed_vehicles": p["total_destroyed_vehicles"],
            "kd_ratio": kd
        })
        
    squad_kd = round(grand_frags / grand_deaths, 2) if grand_deaths > 0 else float(grand_frags)
    
    return {
        "squad_name": squad_name,
        "total_missions": squad_missions_count,
        "total_frags": grand_frags,
        "total_deaths": grand_deaths,
        "kd_ratio": squad_kd,
        "players": players_list
    }
