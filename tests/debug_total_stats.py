import asyncio
from sqlalchemy import select, func
from database import AsyncSessionLocal, GlobalSquad, MissionSquadStat

async def debug_total_stats():
    async with AsyncSessionLocal() as session:
        print("--- GlobalSquads with side set ---")
        stmt_squads = select(GlobalSquad).where(GlobalSquad.side.is_not(None))
        res_squads = await session.execute(stmt_squads)
        squads = res_squads.scalars().all()
        squad_names = []
        for s in squads:
            print(f"ID: {s.id}, Name: '{s.name}', Side: '{s.side}', Tags: {s.tags}")
            squad_names.append(s.name)
        
        if not squad_names:
            print("NO SQUADS WITH SIDE SET!")
        
        print("\n--- MissionSquadStat Samples ---")
        # Check if we have stats for these squads
        if squad_names:
            stmt_stats = select(MissionSquadStat.squad_tag, func.count(MissionSquadStat.id))\
                .where(MissionSquadStat.squad_tag.in_(squad_names))\
                .group_by(MissionSquadStat.squad_tag)
            res_stats = await session.execute(stmt_stats)
            stats = res_stats.all()
            if stats:
                for tag, count in stats:
                    print(f"Found stats for '{tag}': {count} entries")
            else:
                print("No stats found matching exact names.")
                
                # Check what IS in MissionSquadStat
                print("Top 10 Squad Tags in Stats:")
                stmt_top = select(MissionSquadStat.squad_tag, func.count(MissionSquadStat.id))\
                    .group_by(MissionSquadStat.squad_tag)\
                    .order_by(func.count(MissionSquadStat.id).desc())\
                    .limit(10)
                res_top = await session.execute(stmt_top)
                for tag, count in res_top.all():
                    print(f"Tag: '{tag}', entries: {count}")

if __name__ == "__main__":
    asyncio.run(debug_total_stats())
