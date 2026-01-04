import asyncio
from sqlalchemy import select, func
from database import AsyncSessionLocal, GlobalSquad
from api.routers.squads import get_squad_stats

# Mocking the request context isn't easy without running the server.
# Instead, let's replicate the logic from squads.py exactly in a script.

async def test_logic(input_name):
    async with AsyncSessionLocal() as session:
        print(f"Testing input: '{input_name}'")
        squad_lower = input_name.lower()
        
        # 1. Resolve alias
        stmt_canonical = select(GlobalSquad).where(func.lower(GlobalSquad.name) == squad_lower)
        result_canonical = await session.execute(stmt_canonical)
        squad_obj = result_canonical.scalars().first()

        canonical_name = input_name
        if squad_obj:
            print(f"  Direct match found: {squad_obj.name}")
            canonical_name = squad_obj.name
        else:
            print("  No direct match. Searching tags...")
            stmt_all = select(GlobalSquad)
            res_all = await session.execute(stmt_all)
            all_squads = res_all.scalars().all()
            
            for s in all_squads:
                if s.tags:
                    # Debug print tags
                    # print(f"    Checking {s.name} tags: {s.tags}")
                    if any(str(t).lower() == squad_lower for t in s.tags):
                        print(f"    Match found in tags of: {s.name}")
                        canonical_name = s.name
                        break
        
        print(f"Resolved canonical name: '{canonical_name}'")
        
        if canonical_name == input_name and not squad_obj:
             print("FAILED to resolve alias (if expected).")

if __name__ == "__main__":
    asyncio.run(test_logic("3"))
    asyncio.run(test_logic("3 ОБрСпн"))
