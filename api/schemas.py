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

class SquadDetailedStats(SquadAggregatedStats):
    players: List[SquadPlayerStats]

class PlayerSquadStats(BaseModel):
    squad: str
    total_missions: int
    total_frags: int
    total_frags_veh: int
    total_frags_inf: int
    total_deaths: int
    total_destroyed_vehicles: int
    kd_ratio: float

class PlayerAggregatedStats(BaseModel):
    name: str
    total_missions: int
    total_frags: int
    total_frags_veh: int
    total_frags_inf: int
    total_deaths: int
    total_destroyed_vehicles: int
    kd_ratio: float
    squads: List[PlayerSquadStats] = []
