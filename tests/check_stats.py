import asyncio
from sqlalchemy import select, func
from database import AsyncSessionLocal, PlayerStat, MissionSquadStat

async def check_stats():
    async with AsyncSessionLocal() as session:
        target = "3 ОБрСпн"
        print(f"Checking existing stats for: '{target}'")
        
        # Check PlayerStat
        stmt_p = select(func.count(PlayerStat.id)).where(PlayerStat.squad == target)
        count_p = await session.scalar(stmt_p)
        print(f"PlayerStat rows for exact match: {count_p}")
        
        stmt_p_lower = select(func.count(PlayerStat.id)).where(func.lower(PlayerStat.squad) == target.lower())
        count_p_lower = await session.scalar(stmt_p_lower)
        print(f"PlayerStat rows for case-insensitive match: {count_p_lower}")

        # Check MissionSquadStat
        stmt_m = select(func.count(MissionSquadStat.id)).where(MissionSquadStat.squad_tag == target)
        count_m = await session.scalar(stmt_m)
        print(f"MissionSquadStat rows for exact match: {count_m}")

if __name__ == "__main__":
    asyncio.run(check_stats())
