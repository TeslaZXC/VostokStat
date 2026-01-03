import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import time

from fastapi.staticfiles import StaticFiles
from api.routers import missions, players, squads, admin
from logic.download_mission import main as download_main


# Background task to run the download logic
async def background_mission_updater():
    print("Background mission updater started.")
    # Initial run might take time, so we delay it slightly to let server start
    await asyncio.sleep(5) 
    
    print("=== Initial mission sync (init mode) ===")
    try:
        # Run init first to backfill any missing missions based on config
        await asyncio.to_thread(download_main, mode="init")
    except Exception as e:
        print(f"Error in initial sync: {e}")

    while True:
        try:
            print("=== Creating task for mission update ===")
            # Run the synchronous download/process logic in a separate thread
            await asyncio.to_thread(download_main, mode="update")
            print("=== Update finished. Sleeping... ===")
        except Exception as e:
            print(f"Error in background update: {e}")
        
        await asyncio.sleep(20)  # Check every 20 seconds

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    task = asyncio.create_task(background_mission_updater())
    yield
    # Shutdown
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        print("Background updater cancelled.")

app = FastAPI(title="VostokStat API", lifespan=lifespan)

# CORS configuration
origins = [
    "http://localhost",
    "http://localhost:3000",
    "http://localhost:8000",
    "*", # Adjust for production
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(missions.router)
app.include_router(players.router)
app.include_router(squads.router)
app.include_router(admin.router)

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def root():
    return {"message": "Welcome to VostokStat API"}
