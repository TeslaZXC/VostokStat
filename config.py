from pathlib import Path
from pymongo import MongoClient

OCAPS_URL = 'http://185.236.20.167:5000/api/v1/operations'
OCAP_URL = 'http://185.236.20.167:5000/data/%s'

OCAPS_PATH = Path("ocaps")
TEMP_PATH = Path("temp")
SQUAD_FILE = Path("data/squad.json")

mongo_client = MongoClient("mongodb://localhost:27017")  
db = mongo_client["stats"]      
collection = db["mission_stat"]
squads_collection = db["squads"]

DOWNLOAD_DATE = "2025-01-01"

BASE_MAPS_PATH = "maps"