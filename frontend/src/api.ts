
const API_BASE = '/api';

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
    const response = await fetch(`${API_BASE}/players/search/${name}`);
    if (!response.ok) throw new Error('Failed to search player');
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
