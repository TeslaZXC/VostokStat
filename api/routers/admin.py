from fastapi import APIRouter, HTTPException, Body, Depends, Request, Response, Query, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from sqlalchemy.future import select
from sqlalchemy import delete, update, func, desc, or_
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db, GlobalSquad, AdminUser, AsyncSessionLocal, Mission, PlayerStat, AppConfig, engine, get_app_config_sync
import bcrypt
import os
from logic.download_mission import main as download_main
from logic.backup import create_backup_zip, run_backup_task

router = APIRouter(prefix="/admin", tags=["admin"])

# ... (rest of imports/auth)


# --- Auth Dependency ---

async def get_current_admin(request: Request):
    user = request.session.get("token")
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return user

async def get_current_root_admin(request: Request):
    user = request.session.get("token")
    if user != "admin": # Hardcoded root admin for now
         raise HTTPException(status_code=403, detail="Forbidden: Root access required")
    return user

# --- Auth Routes ---

class LoginRequest(BaseModel):
    username: str
    password: str

@router.post("/auth/login")
async def login(request: Request, login_data: LoginRequest):
    async with AsyncSessionLocal() as session:
        stmt = select(AdminUser).filter(AdminUser.username == login_data.username)
        result = await session.execute(stmt)
        user = result.scalars().first()
    
    if not user:
         raise HTTPException(status_code=401, detail="Invalid credentials")
         
    # Check password
    try:
        if bcrypt.checkpw(login_data.password.encode("utf-8"), user.password_hash.encode("utf-8")):
            request.session.update({"token": user.username})
            return {"message": "Logged in", "username": user.username}
    except Exception:
         pass
         
    raise HTTPException(status_code=401, detail="Invalid credentials")

@router.post("/auth/logout")
async def logout(request: Request):
    request.session.clear()
    return {"message": "Logged out"}

@router.get("/auth/me")
async def get_me(user: str = Depends(get_current_admin)):
    return {"username": user}

# --- Missions Management ---

class MissionUpdate(BaseModel):
    mission_name: Optional[str] = None
    map_name: Optional[str] = None
    file_date: Optional[str] = None
    total_players: Optional[int] = None
    win_side: Optional[str] = None

@router.get("/missions")
async def list_missions(
    skip: int = 0, 
    limit: int = 50, 
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db), 
    admin: str = Depends(get_current_admin)
):
    query = select(Mission)
    if search:
        query = query.filter(Mission.mission_name.ilike(f"%{search}%"))
    
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query)
    
    # Sort by date desc
    query = query.order_by(desc(Mission.file_date)).offset(skip).limit(limit)
    
    result = await db.execute(query)
    missions = result.scalars().all()
    return {"items": missions, "total": total}

@router.put("/missions/{id}")
async def update_mission(id: int, data: MissionUpdate, db: AsyncSession = Depends(get_db), admin: str = Depends(get_current_admin)):
    mission = await db.get(Mission, id)
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")
    
    if data.mission_name is not None: mission.mission_name = data.mission_name
    if data.map_name is not None: mission.map_name = data.map_name
    if data.file_date is not None: mission.file_date = data.file_date
    if data.total_players is not None: mission.total_players = data.total_players
    if data.win_side is not None: mission.win_side = data.win_side
    
    await db.commit()
    await db.refresh(mission)
    return mission

@router.delete("/missions/all")
async def delete_all_missions(background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db), admin: str = Depends(get_current_admin)):
    # Explicitly clear all tables to ensure no orphans remain
    await db.execute(delete(MissionSquadStat))
    await db.execute(delete(PlayerStat))
    await db.execute(delete(Mission))
    await db.commit()
    
    # Trigger full rebuild
    background_tasks.add_task(download_main, mode="init")
    return {"message": "All missions deleted. Database cleared. Reloading started in background..."}

@router.delete("/missions/{id}")
async def delete_mission(id: int, db: AsyncSession = Depends(get_db), admin: str = Depends(get_current_admin)):
    stmt = select(Mission).where(Mission.id == id)
    result = await db.execute(stmt)
    obj = result.scalars().first()
    if not obj:
        raise HTTPException(status_code=404, detail="Mission not found")
    
    await db.delete(obj)
    await db.commit()
    return {"message": "Mission deleted"}

# --- Players Management ---

@router.get("/players")
async def list_players(
    skip: int = 0, 
    limit: int = 50, 
    search: Optional[str] = None,
    mission_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db), 
    admin: str = Depends(get_current_admin)
):
    query = select(PlayerStat)
    if search:
        query = query.filter(PlayerStat.name.ilike(f"%{search}%"))
    if mission_id:
        query = query.filter(PlayerStat.mission_id == mission_id)
    
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query)

    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    players = result.scalars().all()
    return {"items": players, "total": total}

class PlayerUpdate(BaseModel):
    name: Optional[str] = None
    squad: Optional[str] = None
    side: Optional[str] = None
    mission_id: Optional[int] = None

@router.put("/players/{id}")
async def update_player(id: int, data: PlayerUpdate, db: AsyncSession = Depends(get_db), admin: str = Depends(get_current_admin)):
    player = await db.get(PlayerStat, id)
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    
    if data.name is not None: player.name = data.name
    if data.squad is not None: player.squad = data.squad
    if data.side is not None: player.side = data.side
    if data.mission_id is not None: player.mission_id = data.mission_id
    
    await db.commit()
    await db.refresh(player)
    return player

class MergeRequest(BaseModel):
    source_name: str
    target_name: str

@router.post("/players/merge")
async def merge_players(data: MergeRequest, db: AsyncSession = Depends(get_db), admin: str = Depends(get_current_admin)):
    if data.source_name == data.target_name:
        raise HTTPException(status_code=400, detail="Source and target must be different")
        
    stmt = (
        update(PlayerStat)
        .where(PlayerStat.name == data.source_name)
        .values(name=data.target_name)
    )
    result = await db.execute(stmt)
    await db.commit()
    
    if result.rowcount == 0:
        return {"message": "No records found for source player", "merged": 0}
        
    return {"message": "Merged", "merged_count": result.rowcount}

# --- Mission Squad Stats ---

from database import MissionSquadStat

@router.get("/mission_squad_stats")
async def list_mission_squad_stats(
    skip: int = 0, 
    limit: int = 50, 
    search: Optional[str] = None,
    mission_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db), 
    admin: str = Depends(get_current_admin)
):
    query = select(MissionSquadStat)
    if search:
        query = query.filter(MissionSquadStat.squad_tag.ilike(f"%{search}%"))
    if mission_id:
        query = query.filter(MissionSquadStat.mission_id == mission_id)
    
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query)
        
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    stats = result.scalars().all()
    return {"items": stats, "total": total}

class MissionSquadStatUpdate(BaseModel):
    squad_tag: Optional[str] = None
    side: Optional[str] = None
    frags: Optional[int] = None
    death: Optional[int] = None
    mission_id: Optional[int] = None

@router.put("/mission_squad_stats/{id}")
async def update_mission_squad_stat(id: int, data: MissionSquadStatUpdate, db: AsyncSession = Depends(get_db), admin: str = Depends(get_current_admin)):
    stat = await db.get(MissionSquadStat, id)
    if not stat:
        raise HTTPException(status_code=404, detail="Stat not found")

    if data.squad_tag is not None: stat.squad_tag = data.squad_tag
    if data.side is not None: stat.side = data.side
    if data.frags is not None: stat.frags = data.frags
    if data.death is not None: stat.death = data.death
    if data.mission_id is not None: stat.mission_id = data.mission_id

    await db.commit()
    await db.refresh(stat)
    return stat

# --- Squads Management ---

class SquadCreate(BaseModel):
    name: str # Canonical Name
    tags: List[str] # List of tags/aliases

@router.post("/squads")
async def add_squad(squad: SquadCreate, db: AsyncSession = Depends(get_db), admin: str = Depends(get_current_admin)):
    stmt = select(GlobalSquad).where(GlobalSquad.name == squad.name)
    result = await db.execute(stmt)
    existing = result.scalars().first()
    
    if existing:
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
async def get_squads(
    skip: int = 0, 
    limit: int = 50, 
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db), 
    admin: str = Depends(get_current_admin)
):
    query = select(GlobalSquad)
    if search:
        query = query.filter(GlobalSquad.name.ilike(f"%{search}%"))
        
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query)

    query = query.order_by(GlobalSquad.name).offset(skip).limit(limit)
    result = await db.execute(query)
    squads = result.scalars().all()
    
    output = []
    for s in squads:
        output.append({
            "id": s.id,
            "name": s.name,
            "tags": s.tags if s.tags else []
        })
    return {"items": output, "total": total}

@router.delete("/squads/{name}")
async def delete_squad(name: str, db: AsyncSession = Depends(get_db), admin: str = Depends(get_current_admin)):
    stmt = select(GlobalSquad).where(GlobalSquad.name == name)
    result = await db.execute(stmt)
    existing = result.scalars().first()
    
    if not existing:
        raise HTTPException(status_code=404, detail="Squad not found")
        
    await db.delete(existing)
    await db.commit()
    return {"message": "Squad deleted"}

# --- App Config ---

class ConfigItem(BaseModel):
    key: str
    value: str

@router.get("/config")
async def list_config(db: AsyncSession = Depends(get_db), admin: str = Depends(get_current_admin)):
    result = await db.execute(select(AppConfig))
    return result.scalars().all()

@router.post("/config")
async def update_config(item: ConfigItem, db: AsyncSession = Depends(get_db), admin: str = Depends(get_current_admin)):
    stmt = select(AppConfig).where(AppConfig.key == item.key)
    result = await db.execute(stmt)
    existing = result.scalars().first()
    
    if existing:
        existing.value = item.value
    else:
        db.add(AppConfig(key=item.key, value=item.value))
    
    await db.commit()
    return {"message": "Config updated"}

@router.delete("/config/{key}")
async def delete_config(key: str, db: AsyncSession = Depends(get_db), admin: str = Depends(get_current_admin)):
    stmt = select(AppConfig).where(AppConfig.key == key)
    result = await db.execute(stmt)
    existing = result.scalars().first()
    if existing:
        await db.delete(existing)
        await db.commit()
    return {"message": "Config deleted"}

# --- Admin Users (Root only) ---

class AdminUserCreate(BaseModel):
    username: str
    password: str

class AdminUserUpdate(BaseModel):
    password: Optional[str] = None

@router.get("/users")
async def list_users(db: AsyncSession = Depends(get_db), admin: str = Depends(get_current_root_admin)):
    result = await db.execute(select(AdminUser))
    users = result.scalars().all()
    # Don't return hashes in full to client ideally, but for now ok
    return [{"id": u.id, "username": u.username} for u in users]

@router.post("/users")
async def create_user(user: AdminUserCreate, db: AsyncSession = Depends(get_db), admin: str = Depends(get_current_root_admin)):
    hashed = bcrypt.hashpw(user.password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    new_user = AdminUser(username=user.username, password_hash=hashed)
    db.add(new_user)
    try:
        await db.commit()
    except Exception:
        raise HTTPException(status_code=400, detail="Username likely exists")
    return {"message": "User created"}

@router.delete("/users/{id}")
async def delete_user(id: int, db: AsyncSession = Depends(get_db), admin: str = Depends(get_current_root_admin)):
    stmt = select(AdminUser).where(AdminUser.id == id)
    result = await db.execute(stmt)
    existing = result.scalars().first()
    
    if not existing:
         raise HTTPException(status_code=404, detail="User not found")
    
    if existing.username == "admin":
        raise HTTPException(status_code=400, detail="Cannot delete root admin")

    await db.delete(existing)
    await db.commit()
    return {"message": "User deleted"}

@router.put("/users/{id}")
async def update_user(id: int, user: AdminUserUpdate, db: AsyncSession = Depends(get_db), admin: str = Depends(get_current_root_admin)):
    stmt = select(AdminUser).where(AdminUser.id == id)
    result = await db.execute(stmt)
    existing = result.scalars().first()
    
    if not existing:
         raise HTTPException(status_code=404, detail="User not found")
         
    if user.password:
        hashed = bcrypt.hashpw(user.password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        existing.password_hash = hashed
        
    await db.commit()
    return {"message": "User updated"}


# --- Backup Management ---
BACKUP_DIR = "backups"

@router.get("/backups")
async def list_backups(admin: str = Depends(get_current_admin)):
    if not os.path.exists(BACKUP_DIR):
        return []
    
    files = []
    for f in os.listdir(BACKUP_DIR):
        if f.endswith(".zip"):
            path = os.path.join(BACKUP_DIR, f)
            stat = os.stat(path)
            files.append({
                "name": f,
                "size": stat.st_size,
                "created": stat.st_mtime
            })
    
    # Sort by creation time desc
    files.sort(key=lambda x: x["created"], reverse=True)
    return files

@router.post("/backups/trigger")
async def trigger_backup(background_tasks: BackgroundTasks, admin: str = Depends(get_current_admin)):
    """Manually trigger backup and send to telegram"""
    background_tasks.add_task(run_backup_task, get_app_config_sync)
    return {"message": "Backup task started in background"}

@router.get("/backups/download/{filename}")
async def download_backup(filename: str, admin: str = Depends(get_current_admin)):
    file_path = os.path.join(BACKUP_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Backup not found")
    
    return FileResponse(file_path, filename=filename)
