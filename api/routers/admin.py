from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel
from database import get_squads_collection
from typing import List

router = APIRouter(prefix="/admin", tags=["admin"])

class SquadCreate(BaseModel):
    name: str
    tags: List[str]

@router.post("/squads")
async def add_squad(squad: SquadCreate):
    collection = await get_squads_collection()
    
    # Check if squad with this name already exists
    existing = await collection.find_one({"name": squad.name})
    if existing:
        # Update existing squad tags
        await collection.update_one(
            {"name": squad.name},
            {"$set": {"tags": squad.tags}}
        )
        return {"message": "Squad updated", "squad": squad.name, "tags": squad.tags}
    
    await collection.insert_one({
        "name": squad.name,
        "tags": squad.tags
    })
    return {"message": "Squad added", "squad": squad.name, "tags": squad.tags}

@router.get("/squads")
async def get_squads():
    collection = await get_squads_collection()
    cursor = collection.find({}, {"_id": 0})
    squads = await cursor.to_list(length=1000)
    return squads

@router.delete("/squads/{name}")
async def delete_squad(name: str):
    collection = await get_squads_collection()
    result = await collection.delete_one({"name": name})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Squad not found")
    return {"message": "Squad deleted"}
