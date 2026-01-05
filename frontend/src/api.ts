
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
    side?: string;
    last_squad?: string; // [TAG] Name support
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


export const fetchMissions = async (limit: number = 20, skip: number = 0, rotationId?: number | null) => {
    let url = `${API_BASE}/missions/?limit=${limit}&skip=${skip}`;
    if (rotationId) url += `&rotation_id=${rotationId}`;
    const response = await fetch(url);
    if (!response.ok) throw new Error('Failed to fetch missions');
    return response.json();
};

export const fetchMissionDetails = async (id: number) => {
    const response = await fetch(`${API_BASE}/missions/${id}`);
    if (!response.ok) throw new Error('Failed to fetch mission details');
    return response.json();
};

export const fetchTopSquads = async (rotationId?: number | null) => {
    let url = `${API_BASE}/squads/top`;
    if (rotationId) url += `?rotation_id=${rotationId}`;
    const response = await fetch(url);
    if (!response.ok) throw new Error('Failed to fetch top squads');
    return response.json();
};

export const fetchTopPlayers = async (category: string = 'general', rotationId?: number | null) => {
    let url = `${API_BASE}/players/top/?category=${category}`;
    if (rotationId) url += `&rotation_id=${rotationId}`;
    const response = await fetch(url);
    if (!response.ok) throw new Error('Failed to fetch top players');
    return response.json();
};

// ... searchPlayer ...

export const searchPlayer = async (name: string) => {
    // Legacy support or alias to general? Let's keep it but ideally deprecate
    const response = await fetch(`${API_BASE}/players/search/${name}`);
    if (!response.ok) throw new Error('Failed to search player');
    return response.json();
};

// ... (skip down to total stats) ...

export const fetchTotalSquadStats = async (rotationId?: number | null): Promise<TotalSquadsResponse> => {
    try {
        let url = `${API_BASE}/squads/total_stats`;
        if (rotationId) url += `?rotation_id=${rotationId}`;
        const response = await fetch(url);
        if (!response.ok) throw new Error('Failed to fetch total squad stats');
        return response.json();
    } catch (error) {
        console.error("Error fetching total squad stats:", error);
        throw error;
    }
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

export const fetchPlayerProfile = async (name: string, rotationId?: number | null) => {
    const enc = encodeURIComponent(name);
    let url = `${API_BASE}/players/${enc}`;
    if (rotationId) url += `?rotation_id=${rotationId}`;
    const response = await fetch(url);
    if (!response.ok) throw new Error('Failed to fetch player profile');
    return response.json();
};

export const fetchSquadProfile = async (name: string, rotationId?: number | null) => {
    const enc = encodeURIComponent(name);
    let url = `${API_BASE}/squads/${enc}`;
    if (rotationId) url += `?rotation_id=${rotationId}`;
    const response = await fetch(url);
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

// (Deleted duplicated fetchTotalSquadStats)

// --- Admin API ---

export const adminLogin = async (username: string, password: string) => {
    const response = await fetch(`${API_BASE}/admin/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
    });
    if (!response.ok) throw new Error("Login failed");
    return response.json();
};

export const adminLogout = async () => {
    await fetch(`${API_BASE}/admin/auth/logout`, { method: 'POST' });
};

export const checkAdminAuth = async () => {
    const response = await fetch(`${API_BASE}/admin/auth/me`);
    if (!response.ok) throw new Error("Not authenticated");
    return response.json();
};

export const getAdminSquads = async (skip = 0, limit = 50, search = '') => {
    const response = await fetch(`${API_BASE}/admin/squads?skip=${skip}&limit=${limit}&search=${encodeURIComponent(search)}`);
    if (!response.ok) throw new Error("Fetch squads failed");
    return response.json(); // Returns {items, total}
};

export const addAdminSquad = async (name: string, tags: string[]) => {
    const response = await fetch(`${API_BASE}/admin/squads`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, tags })
    });
    if (!response.ok) throw new Error("Add squad failed");
    return response.json();
};

export const deleteAdminSquad = async (name: string) => {
    const response = await fetch(`${API_BASE}/admin/squads/${name}`, {
        method: 'DELETE'
    });
    if (!response.ok) throw new Error("Delete squad failed");
    return response.json();
};

export const getAdminMissions = async (skip = 0, limit = 50, search = '') => {
    const response = await fetch(`${API_BASE}/admin/missions?skip=${skip}&limit=${limit}&search=${encodeURIComponent(search)}`);
    if (!response.ok) throw new Error("Fetch missions failed");
    return response.json(); // Returns {items, total}
};

export const updateAdminMission = async (id: number, data: any) => {
    const response = await fetch(`${API_BASE}/admin/missions/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    });
    if (!response.ok) throw new Error("Update mission failed");
    return response.json();
};

export const deleteAdminMission = async (id: number) => {
    const response = await fetch(`${API_BASE}/admin/missions/${id}`, { method: 'DELETE' });
    if (!response.ok) throw new Error("Delete mission failed");
    return response.json();
};

export const deleteAllMissions = async () => {
    const response = await fetch(`${API_BASE}/admin/missions/all`, { method: 'DELETE' });
    if (!response.ok) throw new Error("Delete all missions failed");
    return response.json();
};

export const getAdminConfig = async () => {
    const response = await fetch(`${API_BASE}/admin/config`);
    if (!response.ok) throw new Error("Fetch config failed");
    return response.json();
};

export const updateAdminConfig = async (key: string, value: string) => {
    const response = await fetch(`${API_BASE}/admin/config`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ key, value })
    });
    if (!response.ok) throw new Error("Update config failed");
    return response.json();
};

export const deleteAdminConfig = async (key: string) => {
    const response = await fetch(`${API_BASE}/admin/config/${key}`, { method: 'DELETE' });
    if (!response.ok) throw new Error("Delete config failed");
    return response.json();
};

export const getAdminUsers = async () => {
    const response = await fetch(`${API_BASE}/admin/users`);
    if (!response.ok) throw new Error("Fetch users failed");
    return response.json();
};

export const createAdminUser = async (username: string, password: string) => {
    const response = await fetch(`${API_BASE}/admin/users`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
    });
    if (!response.ok) throw new Error("Create user failed");
    return response.json();
};

export const deleteAdminUser = async (id: number) => {
    const response = await fetch(`${API_BASE}/admin/users/${id}`, { method: 'DELETE' });
    if (!response.ok) throw new Error("Delete user failed");
    return response.json();
};

export const updateAdminUser = async (id: number, password: string) => {
    const response = await fetch(`${API_BASE}/admin/users/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ password })
    });
    if (!response.ok) throw new Error("Update user failed");
    return response.json();
};

export const getAdminPlayers = async (skip = 0, limit = 50, search = '') => {
    const response = await fetch(`${API_BASE}/admin/players?skip=${skip}&limit=${limit}&search=${encodeURIComponent(search)}`);
    if (!response.ok) throw new Error("Fetch players failed");
    return response.json(); // Returns {items, total}
};

export const updateAdminPlayer = async (id: number, data: any) => {
    const response = await fetch(`${API_BASE}/admin/players/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    });
    if (!response.ok) throw new Error("Update player failed");
    return response.json();
};

export const mergePlayers = async (source_name: string, target_name: string) => {
    const response = await fetch(`${API_BASE}/admin/players/merge`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ source_name, target_name })
    });
    if (!response.ok) throw new Error("Merge failed");
    return response.json();
};

export const getMissionSquadStats = async (skip = 0, limit = 50, search = '') => {
    const response = await fetch(`${API_BASE}/admin/mission_squad_stats?skip=${skip}&limit=${limit}&search=${encodeURIComponent(search)}`);
    if (!response.ok) throw new Error("Fetch mission squad stats failed");
    return response.json(); // Returns {items, total}
};

export const updateMissionSquadStat = async (id: number, data: any) => {
    const response = await fetch(`${API_BASE}/admin/mission_squad_stats/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    });
    if (!response.ok) throw new Error("Update squad stat failed");
    return response.json();
};

// --- Rotations API ---

export interface Rotation {
    id: number;
    name: string;
    start_date: string;
    end_date: string;
    is_active: boolean;
    squad_count: number;
    squad_ids: number[];
}

export const getRotations = async () => {
    const response = await fetch(`${API_BASE}/admin/rotations/`);
    if (!response.ok) throw new Error("Fetch rotations failed");
    return response.json();
};

export const createRotation = async (data: { name: string; start_date: string; end_date: string; is_active: boolean; squad_ids: number[] }) => {
    const response = await fetch(`${API_BASE}/admin/rotations/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    });
    if (!response.ok) {
        const errText = await response.text();
        throw new Error(`Create rotation failed: ${response.status} ${errText}`);
    }
    return response.json();
};

export const updateRotation = async (id: number, data: { name: string; start_date: string; end_date: string; is_active: boolean; squad_ids?: number[] }) => {
    const response = await fetch(`${API_BASE}/admin/rotations/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    });
    if (!response.ok) {
        const errText = await response.text();
        throw new Error(`Update rotation failed: ${response.status} ${errText}`);
    }
    return response.json();
};

export const deleteRotation = async (id: number) => {
    const response = await fetch(`${API_BASE}/admin/rotations/${id}`, { method: 'DELETE' });
    if (!response.ok) throw new Error("Delete rotation failed");
    return response.json();
};
