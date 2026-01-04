from fastapi import APIRouter, HTTPException, Depends
from typing import List
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db, Rotation, RotationSquad, GlobalSquad
from api.schemas import Rotation as RotationSchema, RotationCreate, RotationUpdate
from api.routers.admin import get_current_admin # Security

router = APIRouter(prefix="/admin/rotations", tags=["admin_rotations"])

@router.get("/", response_model=List[RotationSchema])
async def get_rotations(db: AsyncSession = Depends(get_db), admin=Depends(get_current_admin)):
    stmt = select(Rotation).options(selectinload(Rotation.squads))
    result = await db.execute(stmt)
    rows = result.scalars().all()
    
    # Transform to schema
    output = []
    for r in rows:
        sq_ids = [rs.squad_id for rs in r.squads]
        output.append(RotationSchema(
            id=r.id,
            name=r.name,
            start_date=r.start_date,
            end_date=r.end_date,
            is_active=bool(r.is_active),
            squad_count=len(sq_ids),
            squad_ids=sq_ids
        ))
    return output

@router.post("/", response_model=RotationSchema)
async def create_rotation(rot: RotationCreate, db: AsyncSession = Depends(get_db), admin=Depends(get_current_admin)):
    # Check name unique
    stmt = select(Rotation).filter(Rotation.name == rot.name)
    res = await db.execute(stmt)
    if res.scalars().first():
        raise HTTPException(status_code=400, detail="Rotation name already exists")
        
    db_rot = Rotation(
        name=rot.name,
        start_date=rot.start_date,
        end_date=rot.end_date,
        is_active=1 if rot.is_active else 0
    )
    db.add(db_rot)
    await db.commit()
    await db.refresh(db_rot)
    
    # Add squads
    if rot.squad_ids:
        for sid in rot.squad_ids:
            rs = RotationSquad(rotation_id=db_rot.id, squad_id=sid)
            db.add(rs)
        await db.commit()
        
    return RotationSchema(
        id=db_rot.id,
        name=db_rot.name,
        start_date=db_rot.start_date,
        end_date=db_rot.end_date,
        is_active=bool(db_rot.is_active),
        squad_count=len(rot.squad_ids),
        squad_ids=rot.squad_ids
    )

@router.put("/{rot_id}", response_model=RotationSchema)
async def update_rotation(rot_id: int, rot: RotationUpdate, db: AsyncSession = Depends(get_db), admin=Depends(get_current_admin)):
    stmt = select(Rotation).filter(Rotation.id == rot_id).options(selectinload(Rotation.squads))
    res = await db.execute(stmt)
    db_rot = res.scalars().first()
    
    if not db_rot:
        raise HTTPException(status_code=404, detail="Rotation not found")
        
    db_rot.name = rot.name
    db_rot.start_date = rot.start_date
    db_rot.end_date = rot.end_date
    db_rot.is_active = 1 if rot.is_active else 0
    
    # Update squads if provided
    if rot.squad_ids is not None:
        # Remove old
        stmt_del = select(RotationSquad).filter(RotationSquad.rotation_id == rot_id)
        res_del = await db.execute(stmt_del)
        for d in res_del.scalars().all():
            await db.delete(d)
            
        # Add new
        for sid in rot.squad_ids:
            rs = RotationSquad(rotation_id=rot_id, squad_id=sid)
            db.add(rs)
            
    await db.commit()
    await db.refresh(db_rot) # Note: squads rel might need reloading but for schema we can just use input
    
    return RotationSchema(
        id=db_rot.id,
        name=db_rot.name,
        start_date=db_rot.start_date,
        end_date=db_rot.end_date,
        is_active=bool(db_rot.is_active),
        squad_count=len(rot.squad_ids) if rot.squad_ids is not None else 0, # Simplify
        squad_ids=rot.squad_ids if rot.squad_ids is not None else []
    )

@router.delete("/{rot_id}")
async def delete_rotation(rot_id: int, db: AsyncSession = Depends(get_db), admin=Depends(get_current_admin)):
    stmt = select(Rotation).filter(Rotation.id == rot_id)
    res = await db.execute(stmt)
    db_rot = res.scalars().first()
    
    if not db_rot:
        raise HTTPException(status_code=404, detail="Rotation not found")
        
    await db.delete(db_rot)
    await db.commit()
    return {"status": "deleted"}
