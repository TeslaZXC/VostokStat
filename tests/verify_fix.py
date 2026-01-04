import asyncio
from sqlalchemy import select, func, desc
from database import AsyncSessionLocal, PlayerStat, Mission

async def verify_fix():
    async with AsyncSessionLocal() as session:
        target = "3 ОБрСпн"
        print(f"Simulating query for: '{target}' with Duration filter")
        
        stmt = (
            select(
                PlayerStat.name,
                func.count(PlayerStat.mission_id).label("total_missions")
            )
            .join(Mission, PlayerStat.mission_id == Mission.id)
            .filter(PlayerStat.squad == target)
            .filter(Mission.duration_time >= 100)
            .group_by(PlayerStat.name)
            .order_by(desc("total_missions"))
        )
        
        result = await session.execute(stmt)
        rows = result.all()
        print(f"Query returned {len(rows)} players.")
        if rows:
            print(f"Top player: {rows[0].name} ({rows[0].total_missions} missions)")

if __name__ == "__main__":
    asyncio.run(verify_fix())
