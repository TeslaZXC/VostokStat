import asyncio
from api.routers.search import unified_search
from database import AsyncSessionLocal

async def test_search(query):
    async with AsyncSessionLocal() as session:
        print(f"Testing search for: '{query}'")
        try:
            results = await unified_search(q=query, db=session)
            print(f"Found {len(results)} results:")
            for r in results:
                print(f" - [{r['type'].upper()}] {r['name']} (Label: {r['label']})")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_search("3"))
    asyncio.run(test_search("Artyrka"))
