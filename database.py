from sqlalchemy import Column, Integer, String, Float, ForeignKey, JSON
from sqlalchemy.orm import declarative_base, relationship, sessionmaker, Session
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy import create_engine
from sqlalchemy.future import select
import os

DATABASE_URL = "sqlite+aiosqlite:///./vostokstat.db"
SYNC_DATABASE_URL = "sqlite:///./vostokstat.db"

# Async for FastAPI
engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# Sync for background parser
sync_engine = create_engine(SYNC_DATABASE_URL, echo=False)
SyncSessionLocal = sessionmaker(sync_engine, class_=Session, expire_on_commit=False)

Base = declarative_base()

# --- Models ---

class Mission(Base):
    __tablename__ = "missions"

    id = Column(Integer, primary_key=True, index=True) # This is our internal incremental ID
    file_name = Column(String, unique=True, index=True)
    file_date = Column(String, index=True)
    mission_name = Column(String, index=True)
    world_name = Column(String)
    map_name = Column(String)
    game_type = Column(String)
    duration_frames = Column(Integer)
    duration_time = Column(Float)
    win_side = Column(String, nullable=True)
    
    # Player counts
    total_players = Column(Integer, default=0)
    west_count = Column(Integer, default=0)
    east_count = Column(Integer, default=0)
    guer_count = Column(Integer, default=0)

    # Relationships
    player_stats = relationship("PlayerStat", back_populates="mission", cascade="all, delete-orphan")
    squad_stats = relationship("MissionSquadStat", back_populates="mission", cascade="all, delete-orphan")

    def __str__(self):
        return f"{self.mission_name} ({self.file_date})"


class PlayerStat(Base):
    __tablename__ = "player_stats"

    id = Column(Integer, primary_key=True, index=True)
    mission_id = Column(Integer, ForeignKey("missions.id"))
    
    player_uid = Column(Integer) # Original Arma Player ID if needed, or just rely on name
    name = Column(String, index=True)
    side = Column(String)
    squad = Column(String, index=True, nullable=True)
    
    frags = Column(Integer, default=0)
    frags_veh = Column(Integer, default=0)
    frags_inf = Column(Integer, default=0)
    death = Column(Integer, default=0)
    tk = Column(Integer, default=0)
    destroyed_veh = Column(Integer, default=0)
    distance = Column(Float, default=0.0)

    # JSON blobs for detailed events
    victims_players = Column(JSON, default=list) # List of kill events
    destroyed_vehicles = Column(JSON, default=list) # List of vehicle destruction events
    
    mission = relationship("Mission", back_populates="player_stats")

    def __str__(self):
        return f"{self.name} [{self.squad or ''}]"


class MissionSquadStat(Base):
    __tablename__ = "mission_squad_stats"

    id = Column(Integer, primary_key=True, index=True)
    mission_id = Column(Integer, ForeignKey("missions.id"))
    
    squad_tag = Column(String, index=True)
    side = Column(String)
    
    frags = Column(Integer, default=0)
    death = Column(Integer, default=0)
    tk = Column(Integer, default=0)

    # JSON blobs
    victims_players = Column(JSON, default=list)
    squad_players = Column(JSON, default=list) # List of members in this mission

    mission = relationship("Mission", back_populates="squad_stats")

    def __str__(self):
        return f"Squad {self.squad_tag} ({self.side})"


class GlobalSquad(Base):
    ''' Registry of known squads '''
    __tablename__ = "squads"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True) # Canonical name
    tags = Column(JSON, default=list) # List of aliases/tags
    side = Column(String, nullable=True) # Main side (WEST/EAST)

    def __str__(self):
        return self.name

class AdminUser(Base):
    __tablename__ = "admin_users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password_hash = Column(String)

    def __str__(self):
        return self.username

class AppConfig(Base):
    __tablename__ = "app_config"
    
    key = Column(String, primary_key=True, index=True)
    value = Column(String)

    def __str__(self):
        return f"{self.key}: {self.value}"

# --- Dependencies ---

def get_app_config_sync(key: str, default: str) -> str:
    """Synchronously get config value for background tasks"""
    with SyncSessionLocal() as session:
        config = session.query(AppConfig).filter(AppConfig.key == key).first()
        if config:
            return config.value
        return default

async def init_db():
    async with engine.begin() as conn:
        # await conn.run_sync(Base.metadata.drop_all) # WARNING: Uncomment only for full reset
        await conn.run_sync(Base.metadata.create_all)
        
        # Initialize default config if not exists
        async with AsyncSessionLocal() as session:
            # Check if defaults exist
            defaults = {
                "OCAPS_URL": "http://185.236.20.167:5000/api/v1/operations",
                "OCAP_URL": "http://185.236.20.167:5000/data/%s",
                "OCAPS_PATH_STR": "ocaps",
                "TEMP_PATH_STR": "temp",
                "BASE_MAPS_PATH": "maps"
            }
            
            for key, default_value in defaults.items():
                stmt = select(AppConfig).filter(AppConfig.key == key)
                result = await session.execute(stmt)
                obj = result.scalars().first()
                if not obj:
                    new_config = AppConfig(key=key, value=default_value)
                    session.add(new_config)
            
            # Create default admin user if not exists
            stmt_user = select(AdminUser).filter(AdminUser.username == "admin")
            result_user = await session.execute(stmt_user)
            admin_user = result_user.scalars().first()
            if not admin_user:
                # Password: Fhnehh123ZOV
                # Hash generated: $2b$12$0EBPLo8jdoosdnIkXtyYq.Po3Pv/iyVDZTdfxvBIHuoz4b.iNLsk6
                default_admin = AdminUser(
                    username="admin",
                    password_hash="$2b$12$0EBPLo8jdoosdnIkXtyYq.Po3Pv/iyVDZTdfxvBIHuoz4b.iNLsk6"
                )
                session.add(default_admin)

            await session.commit()

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
