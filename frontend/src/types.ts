export interface MissionSummary {
    id: number;
    file: string;
    file_date: string;
    game_type: string;
    duration_frames: number;
    duration_time: number;
    missionName: string;
    worldName: string;
    win_side: string | null;
    map: string;
    players_count: Record<string, number>;
}

export interface KillEvent {
    name: string;
    weapon: string;
    distance: number;
    killer_name?: string;
    time: number;
}

export interface DestroyedVehicleEvent {
    name: string;
    veh_type: string;
    weapon: string;
}

export interface PlayerStats {
    id: number;
    name: string;
    side: string | null;
    squad: string | null;
    frags: number;
    frags_veh: number;
    frags_inf: number;
    tk: number;
    death: number;
    distance: number;
    victims_players?: KillEvent[];
    destroyed_vehicles?: DestroyedVehicleEvent[];
    death_events?: KillEvent[];
}

export interface SquadMember {
    name: string;
    frags: number;
    death: number;
    tk: number;
    distance: number;
}

export interface SquadStats {
    squad_tag: string;
    side: string | null;
    frags: number;
    death: number;
    tk: number;
    members: SquadMember[];
    squad_players?: SquadMember[]; // Possible backend alias
}

export interface MissionDetail extends MissionSummary {
    players: PlayerStats[];
    squads: SquadStats[];
}

// New Types for Pro Features

export interface SquadAggregatedStats {
    squad_name: string;
    total_missions: number;
    total_frags: number;
    total_deaths: number;
    kd_ratio: number;
}

export interface PlayerAggregatedStats {
    name: string;
    side?: string;
    total_missions: number;
    total_frags: number;
    total_frags_veh: number;
    total_frags_inf: number;
    total_deaths: number;
    total_destroyed_vehicles: number;
    kd_ratio: number;
    squads?: PlayerSquadStats[];
}

export interface PlayerSquadStats {
    squad: string;
    total_missions: number;
    total_frags: number;
    total_frags_veh: number;
    total_frags_inf: number;
    total_deaths: number;
    total_destroyed_vehicles: number;
    kd_ratio: number;
}
