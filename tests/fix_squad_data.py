import asyncio
from sqlalchemy import select, update
from database import AsyncSessionLocal, GlobalSquad, PlayerStat, MissionSquadStat, init_db

async def fix_squad_aliases():
    async with AsyncSessionLocal() as session:
        print("Starting squad alias normalization...")
        
        # 1. Ensure "3 ОБрСпн" exists and has tags
        target_name = "3 ОБрСпн"
        stmt = select(GlobalSquad).where(GlobalSquad.name == target_name)
        result = await session.execute(stmt)
        squad_3 = result.scalars().first()
        
        target_tags = ["3", "3 ОБрСпн", "3 обрспн"]
        
        if not squad_3:
            print(f"Creating squad {target_name}...")
            squad_3 = GlobalSquad(name=target_name, tags=target_tags)
            session.add(squad_3)
        else:
            print(f"Updating tags for {target_name}...")
            # Union existing tags with new ones to avoid data loss
            current_tags = set(squad_3.tags) if squad_3.tags else set()
            current_tags.update(target_tags)
            squad_3.tags = list(current_tags)
        
        await session.commit()
        
        # 2. Fetch ALL squads to normalize everything
        stmt_all = select(GlobalSquad)
        result_all = await session.execute(stmt_all)
        all_squads = result_all.scalars().all()
        
        updates_count = 0
        
        for squad in all_squads:
            if not squad.tags:
                continue
                
            canonical = squad.name
            tags = [t for t in squad.tags if t != canonical] # Filter out self
            
            if not tags:
                continue
                
            print(f"Normalizing '{canonical}' with aliases: {tags}")
            
            # Update PlayerStat
            stmt_p = (
                update(PlayerStat)
                .where(PlayerStat.squad.in_(tags))
                .values(squad=canonical)
            )
            res_p = await session.execute(stmt_p)
            if res_p.rowcount > 0:
                print(f"  - Updated {res_p.rowcount} player entries")
                updates_count += res_p.rowcount
            
            # Update MissionSquadStat
            stmt_m = (
                update(MissionSquadStat)
                .where(MissionSquadStat.squad_tag.in_(tags))
                .values(squad_tag=canonical)
            )
            res_m = await session.execute(stmt_m)
            if res_m.rowcount > 0:
                print(f"  - Updated {res_m.rowcount} squad stats entries")
                updates_count += res_m.rowcount
                
        await session.commit()
        print(f"Normalization complete. Total records updated: {updates_count}")

if __name__ == "__main__":
    asyncio.run(fix_squad_aliases())
