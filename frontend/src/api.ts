
const API_BASE = '/api';

export interface MissionPerformance {
    mission_id: number;
    mission_name: string;
    map_name: string;
    date: string;
    duration_time: number;
    frags: number;
    deaths: number;
    kd: number;
}

export interface PlayerAggregatedStats {
    name: string;
    total_missions: number;
    total_frags: number;
    total_frags_veh: number;
    total_frags_inf: number;
    total_deaths: number;
    total_destroyed_vehicles: number;
    kd_ratio: number;
    squads: {
        squad: string;
        total_missions: number;
        total_frags: number;
        total_frags_veh: number;
        total_frags_inf: number;
        total_deaths: number;
        total_destroyed_vehicles: number;
        kd_ratio: number;
    }[];
    missions?: MissionPerformance[];
}

export interface SquadMember {
    name: string;
    total_missions: number;
    total_frags: number;
    total_frags_veh: number;
    total_frags_inf: number;
    total_deaths: number;
    total_destroyed_vehicles: number;
    kd_ratio: number;
}

export interface SquadStats {
    squad_name: string;
    total_missions: number;
    total_frags: number;
    total_deaths: number;
    kd_ratio: number;
    players: SquadMember[];
    missions?: MissionPerformance[];
}


export const fetchMissions = async (limit: number = 20, skip: number = 0) => {
    const response = await fetch(`${API_BASE}/missions/?limit=${limit}&skip=${skip}`);
    if (!response.ok) throw new Error('Failed to fetch missions');
    return response.json();
};

export const fetchMissionDetails = async (id: number) => {
    const response = await fetch(`${API_BASE}/missions/${id}`);
    if (!response.ok) throw new Error('Failed to fetch mission details');
    return response.json();
};

export const fetchTopSquads = async () => {
    const response = await fetch(`${API_BASE}/squads/top`);
    if (!response.ok) throw new Error('Failed to fetch top squads');
    return response.json();
};

export const fetchTopPlayers = async (category: string = 'general') => {
    const response = await fetch(`${API_BASE}/players/top/?category=${category}`);
    if (!response.ok) throw new Error('Failed to fetch top players');
    return response.json();
};

export const searchPlayer = async (name: string) => {
    // Legacy support or alias to general? Let's keep it but ideally deprecate
    const response = await fetch(`${API_BASE}/players/search/${name}`);
    if (!response.ok) throw new Error('Failed to search player');
    return response.json();
};

export interface SearchResult {
    type: 'player' | 'squad';
    name: string;
    label: string;
}

export const searchGeneral = async (query: string): Promise<SearchResult[]> => {
    const response = await fetch(`${API_BASE}/search/?q=${encodeURIComponent(query)}`);
    if (!response.ok) throw new Error('Failed to search');
    return response.json();
};

export const fetchPlayerProfile = async (name: string) => {
    const response = await fetch(`${API_BASE}/players/${name}`);
    if (!response.ok) throw new Error('Failed to fetch player profile');
    return response.json();
};

export const fetchSquadProfile = async (name: string) => {
    const response = await fetch(`${API_BASE}/squads/${name}`);
    if (!response.ok) throw new Error('Failed to fetch squad profile');
    return response.json();
};

// Squad Total Stats
export interface SideMissionStat {
    date: string;
    mission_name: string;
    west_frags: number;
    east_frags: number;
}

export interface TotalSquadsResponse {
    west: SquadStats[];
    east: SquadStats[];
    other: SquadStats[];
    history: SideMissionStat[];
}

export const fetchTotalSquadStats = async (): Promise<TotalSquadsResponse> => {
    try {
        const response = await fetch(`${API_BASE}/squads/total_stats`);
        if (!response.ok) throw new Error('Failed to fetch total squad stats');
        return response.json();
    } catch (error) {
        console.error("Error fetching total squad stats:", error);
        throw error;
    }
};
