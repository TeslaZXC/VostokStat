from motor.motor_asyncio import AsyncIOMotorClient
from config import mongo_client, db, collection, squads_collection


MONGO_URI = "mongodb://localhost:27017"
client = AsyncIOMotorClient(MONGO_URI)
database = client["stats"]
mission_collection = database["mission_stat"]
squads_collection_async = database["squads"]

async def get_mission_collection():
    return mission_collection

async def get_squads_collection():
    return squads_collection_async
