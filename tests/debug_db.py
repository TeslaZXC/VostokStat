import asyncio
from sqlalchemy import select
from database import AsyncSessionLocal, GlobalSquad

async def debug_db():
    async with AsyncSessionLocal() as session:
        print("Checking GlobalSquads...")
        stmt = select(GlobalSquad)
        result = await session.execute(stmt)
        squads = result.scalars().all()
        
        found = False
        for s in squads:
            print(f"Squad: '{s.name}', Tags: {s.tags}")
            if "3" in s.name or "3" in (s.tags or []):
                found = True
                
        if not found:
            print("\nWARNING: Target squad '3 ОБрСпн' or alias '3' NOT found in GlobalSquads!")
        else:
            print("\nTarget squad found in DB.")

if __name__ == "__main__":
    asyncio.run(debug_db())
