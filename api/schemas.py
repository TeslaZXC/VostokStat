from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict

class KillEvent(BaseModel):
    name: str # Victim name (or killer name if death event)
    weapon: str
    distance: float
    killer_name: Optional[str] = None
    kill_type: str
    frame: int
    time: float
    position: Optional[dict] = None
    killer_position: Optional[dict] = None

class DestroyedVehicleEvent(BaseModel):
    name: str
    veh_type: str
    weapon: str
    distance: float
    kill_type: str
    frame: int
    time: float
    killer_position: Optional[dict] = None

class PlayerStats(BaseModel):
    id: int
    name: str
    side: Optional[str]
    squad: Optional[str]
    frags: int
    frags_veh: int
    frags_inf: int
    tk: int
    death: int
    distance: float
    
class PlayerMissionStats(PlayerStats):
    victims_players: List[KillEvent] = []
    destroyed_vehicles: List[DestroyedVehicleEvent] = []
    death_events: List[KillEvent] = [] # Computed field

class SquadMember(BaseModel):
    name: str
    frags: int
    death: int
    tk: int
    distance: float

class SquadStats(BaseModel):
    squad_tag: str
    side: Optional[str]
    frags: int
    death: int
    tk: int
    members: List[SquadMember] = Field(default=[], alias="squad_players")

class MissionSummary(BaseModel):
    id: int
    file: str
    file_date: str
    game_type: str
    duration_frames: int
    duration_time: float
    missionName: str
    worldName: str
    win_side: Optional[str]
    map: str
    players_count: Dict[str, int]

class MissionDetail(MissionSummary):
    players: List[PlayerMissionStats]
    squads: List[SquadStats]

class SquadAggregatedStats(BaseModel):
    squad_name: str
    total_missions: int
    total_frags: int
    total_deaths: int
    kd_ratio: float

class SquadPlayerStats(BaseModel):
    name: str
    total_missions: int
    total_frags: int
    total_frags_veh: int
    total_frags_inf: int
    total_deaths: int
    total_destroyed_vehicles: int
    kd_ratio: float

class MissionPerformance(BaseModel):
    mission_id: int
    mission_name: str
    map_name: str
    date: str
    duration_time: float
    frags: int
    deaths: int
    kd: float
    squad: Optional[str] = None
    side: Optional[str] = None

class PlayerSquadStats(BaseModel):
    squad: str
    total_missions: int
    total_frags: int
    total_frags_veh: int
    total_frags_inf: int
    total_deaths: int
    total_destroyed_vehicles: int
    kd_ratio: float

class TimelineSegment(BaseModel):
    squad: str
    start_date: str
    end_date: str
    days: int
    mission_count: int

class PlayerAggregatedStats(BaseModel):
    name: str
    side: Optional[str] = None
    last_squad: Optional[str] = None # Added for [TAG] Name display
    total_missions: int
    total_frags: int
    total_frags_veh: int
    total_frags_inf: int
    total_deaths: int
    total_destroyed_vehicles: int
    kd_ratio: float
    squads: List[PlayerSquadStats] = []
    missions: List[MissionPerformance] = []
    timeline: List[TimelineSegment] = []

class SideMissionStat(BaseModel):
    date: str
    mission_name: str
    west_frags: int
    east_frags: int

class TotalSquadsResponse(BaseModel):
    west: List[SquadAggregatedStats]
    east: List[SquadAggregatedStats]
    other: List[SquadAggregatedStats] = []
    history: List[SideMissionStat] = []

class SquadDetailedStats(SquadAggregatedStats):
    players: List[SquadPlayerStats]
    missions: List[MissionPerformance] = []

class RotationBase(BaseModel):
    name: str # e.g. "Season 1"
    start_date: str # YYYY-MM-DD
    end_date: str # YYYY-MM-DD
    is_active: bool = False

class RotationCreate(RotationBase):
    squad_ids: List[int] = [] # IDs of GlobalSquads to include

class RotationUpdate(RotationBase):
    squad_ids: Optional[List[int]] = None

class Rotation(RotationBase):
    id: int
    squad_count: int = 0
    squad_ids: List[int] = [] 

    class Config:
        from_attributes = True
