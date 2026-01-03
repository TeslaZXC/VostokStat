from fastapi import APIRouter, HTTPException, Body, Depends
from pydantic import BaseModel
from typing import List
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db, GlobalSquad

router = APIRouter(prefix="/admin", tags=["admin"])

class SquadCreate(BaseModel):
    name: str # Canonical Name
    tags: List[str] # List of tags/aliases

@router.post("/squads")
async def add_squad(squad: SquadCreate, db: AsyncSession = Depends(get_db)):
    # Check if squad with this name already exists
    stmt = select(GlobalSquad).where(GlobalSquad.name == squad.name)
    result = await db.execute(stmt)
    existing = result.scalars().first()
    
    if existing:
        # Update existing squad tags
        existing.tags = squad.tags
        await db.commit()
        await db.refresh(existing)
        return {"message": "Squad updated", "squad": existing.name, "tags": existing.tags}
    
    new_squad = GlobalSquad(name=squad.name, tags=squad.tags)
    db.add(new_squad)
    await db.commit()
    await db.refresh(new_squad)
    return {"message": "Squad added", "squad": new_squad.name, "tags": new_squad.tags}

@router.get("/squads")
async def get_squads(db: AsyncSession = Depends(get_db)):
    stmt = select(GlobalSquad).order_by(GlobalSquad.name)
    result = await db.execute(stmt)
    squads = result.scalars().all()
    
    output = []
    for s in squads:
        output.append({
            "name": s.name,
            "tags": s.tags if s.tags else []
        })
    return output

@router.delete("/squads/{name}")
async def delete_squad(name: str, db: AsyncSession = Depends(get_db)):
    stmt = select(GlobalSquad).where(GlobalSquad.name == name)
    result = await db.execute(stmt)
    existing = result.scalars().first()
    
    if not existing:
        raise HTTPException(status_code=404, detail="Squad not found")
        
    await db.delete(existing)
    await db.commit()
    return {"message": "Squad deleted"}
