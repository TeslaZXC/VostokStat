from fastapi import APIRouter, Depends
from typing import List, Dict, Any
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db, PlayerStat, GlobalSquad

router = APIRouter(prefix="/search", tags=["search"])

@router.get("/", response_model=List[Dict[str, Any]])
async def unified_search(q: str, db: AsyncSession = Depends(get_db)):
    if not q:
        return []
        
    query_lower = q.lower()
    results = []
    
    # 1. Search Squads (Priority)
    # Fetch all global squads to check tags (optimized for small number of squads)
    # If number of squads grows large, we need a better SQL strategy (e.g. FTS or JSON operators)
    stmt_squads = select(GlobalSquad)
    res_squads = await db.execute(stmt_squads)
    all_squads = res_squads.scalars().all()
    
    for s in all_squads:
        # Check Name
        if query_lower in s.name.lower():
            results.append({
                "type": "squad",
                "name": s.name,
                "label": f"Отряд: {s.name}"
            })
            continue # Don't add twice if tag also matches
            
        # Check Tags
        if s.tags:
            for t in s.tags:
                if query_lower in str(t).lower():
                    results.append({
                        "type": "squad",
                        "name": s.name,
                        "label": f"Отряд: {s.name} (aka {t})"
                    })
                    break # One match per squad is enough
    
    # 2. Search Players
    stmt_players = (
        select(PlayerStat.name)
        .filter(PlayerStat.name.ilike(f"%{q}%"))
        .distinct()
        .limit(10)
    )
    res_player = await db.execute(stmt_players)
    players = res_player.scalars().all()
    
    for p in players:
        results.append({
            "type": "player",
            "name": p,
            "label": p
        })
        
    # Sort: Squads first, then alphabetical?
    # Or strict limit?
    return results[:15]
