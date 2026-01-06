import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import time


from api.routers import missions, players, squads, admin
from logic.download_mission import main as download_main
from database import init_db


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
    await init_db()
    
    # Scheduler
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    from logic.backup import run_backup_task
    from database import get_app_config_sync
    
    scheduler = AsyncIOScheduler(timezone="Europe/Moscow")
    
    # Wednesday and Sunday at 23:30 (MSK)
    scheduler.add_job(run_backup_task, 'cron', day_of_week='wed,sun', hour=23, minute=30, args=[get_app_config_sync])
    
    scheduler.start()
    
    task = asyncio.create_task(background_mission_updater())
    yield
    # Shutdown
    task.cancel()
    scheduler.shutdown()
    try:
        await task
    except asyncio.CancelledError:
        print("Background updater cancelled.")

app = FastAPI(title="VostokStat API", lifespan=lifespan)

# Admin Interface
# Legacy HTML admin removed.
from starlette.middleware.sessions import SessionMiddleware
import os

# Add Session Middleware for Auth (Required for api/routers/admin.py)
app.add_middleware(SessionMiddleware, secret_key="vostok-secret-key-secure")

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
from api.routers import admin, squads, players, missions, admin_rotations, search
app.include_router(search.router)
app.include_router(admin.router)
app.include_router(admin_rotations.router)



@app.get("/")
async def root():
    return {"message": "Welcome to VostokStat API"}
