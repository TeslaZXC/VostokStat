import React, { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { fetchPlayerProfile } from '../api';
import { useRotation } from '../context/RotationContext';
import { formatPlayerName } from '../utils';
import type { PlayerAggregatedStats } from '../api';
import '../components/MissionDetail.css';
import { SquadTimeline } from '../components/SquadTimeline';

export const PlayerProfile: React.FC = () => {
    const { name } = useParams<{ name: string }>();
    const navigate = useNavigate();
    const { currentRotationId } = useRotation();
    const [profile, setProfile] = useState<PlayerAggregatedStats | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [selectedSquad, setSelectedSquad] = useState<string>('ALL'); // 'ALL' or squad name

    useEffect(() => {
        if (!name) return;

        const fetchData = async () => {
            setLoading(true);
            setError(null);
            try {
                const data = await fetchPlayerProfile(name, currentRotationId);
                setProfile(data);
                // Default to last_squad if available, else ALL
                if (data.last_squad) {
                    setSelectedSquad(data.last_squad);
                } else {
                    setSelectedSquad('ALL');
                }
            } catch {
                setError('Operative not found or KIA.');
            } finally {
                setLoading(false);
            }
        };

        fetchData();
    }, [name, currentRotationId]);

    if (loading) return <div className="loading">Загрузка досье...</div>;
    if (error) return <div className="error">{error}</div>;
    if (!profile) return null;

    // Filter/Select Stats
    const getDisplayedStats = () => {
        if (selectedSquad === 'ALL') {
            return {
                label: 'ALL STATS',
                missions: profile.total_missions,
                frags: profile.total_frags,
                deaths: profile.total_deaths,
                kd: profile.kd_ratio,
                armor: profile.total_destroyed_vehicles,
                missionList: profile.missions || []
            };
        } else {
            // Find stats for specific squad
            const squadStats = profile.squads.find(s => s.squad === selectedSquad);
            // Filter missions for this squad
            // Handle null/undefined squad in missions as 'No Squad' to match availableSquads
            const filteredMissions = (profile.missions || []).filter(m => (m.squad || 'No Squad') === selectedSquad);

            if (!squadStats) return null; // Should not happen

            return {
                label: selectedSquad,
                missions: squadStats.total_missions,
                frags: squadStats.total_frags,
                deaths: squadStats.total_deaths,
                kd: squadStats.kd_ratio,
                armor: squadStats.total_destroyed_vehicles,
                missionList: filteredMissions
            };
        }
    };

    const stats = getDisplayedStats();
    if (!stats) return <div>Stats not found</div>;

    // Unique squads for dropdown
    const availableSquads = profile.squads.map(s => s.squad).sort();

    return (
        <div className="mission-detail">
            <div className="profile-header-row" style={{ marginBottom: '2rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
                <h2 className={profile.side === 'WEST' ? 'text-west' : profile.side === 'EAST' ? 'text-east' : ''} style={{ marginBottom: 0 }}>
                    {profile.last_squad ? `[${profile.last_squad}] ` : ''}
                    {formatPlayerName(profile.name)}
                </h2>

                <select
                    className="squad-selector"
                    value={selectedSquad}
                    onChange={(e) => setSelectedSquad(e.target.value)}
                >
                    <option value="ALL">Вся статистика</option>
                    <optgroup label="Отряды">
                        {availableSquads.map(s => (
                            <option key={s} value={s}>{s}</option>
                        ))}
                    </optgroup>
                </select>
            </div>

            {/* Timeline */}
            <SquadTimeline
                timeline={profile.timeline || []}
                selectedSquad={selectedSquad}
                onSelectSquad={setSelectedSquad}
            />

            <div className="profile-stats-grid">
                <div className="stat-card">
                    <div className="label">Миссии ({selectedSquad === 'ALL' ? 'Всего' : selectedSquad})</div>
                    <div className="value">{stats.missions}</div>
                </div>
                <div className="stat-card">
                    <div className="label">K/D Ratio</div>
                    <div className="value">{stats.kd.toFixed(2)}</div>
                </div>
                <div className="stat-card">
                    <div className="label">Фраги</div>
                    <div className="value">{stats.frags}</div>
                </div>
                <div className="stat-card">
                    <div className="label">Уничтожил Техники</div>
                    <div className="value">{stats.armor}</div>
                </div>
            </div>

            <style>{`
                .profile-stats-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
                    gap: 1rem;
                    margin-bottom: 2rem;
                }
                .stat-card {
                    background: rgba(0,0,0,0.2);
                    padding: 1rem;
                    border: 1px solid var(--color-border);
                    text-align: center;
                }
                .stat-card .label {
                    color: #888;
                    text-transform: uppercase;
                    font-size: 0.8rem;
                    margin-bottom: 0.5rem;
                }
                .stat-card .value {
                    font-size: 1.5rem;
                    color: var(--color-text-muted);
                    font-weight: bold;
                }
                /* Custom grid for 6-column mission history */
                .missions-history-table .table-header,
                .missions-history-table .table-row {
                    grid-template-columns: 3fr 1.5fr 1.2fr 0.7fr 0.7fr 0.7fr !important;
                }
                .text-west { color: #8cb9ff !important; }
                .text-east { color: #ff8c8c !important; }
                .squad-selector {
                    padding: 0.5rem 1rem;
                    background: rgba(0, 0, 0, 0.4);
                    border: 1px solid #3c4238;
                    color: #fff;
                    font-size: 1rem;
                    border-radius: 4px;
                    cursor: pointer;
                    outline: none;
                    min-width: 200px;
                }
                .squad-selector option {
                    background: #1a1e1b;
                }
            `}</style>

            <h3>История Миссий ({selectedSquad === 'ALL' ? 'Все' : selectedSquad})</h3>
            <div className="player-table missions-history-table">
                <div className="table-header">
                    <span>Миссия</span>
                    <span>Карта</span>
                    <span>Дата</span>
                    <span>Фраги</span>
                    <span>Смерти</span>
                    <span>K/D</span>
                </div>
                {stats.missionList.map(m => (
                    <div
                        key={m.mission_id}
                        className="table-row clickable-row"
                        onClick={() => navigate(`/missions/${m.mission_id}`)}
                    >
                        <span>{m.mission_name}</span>
                        <span>{m.map_name}</span>
                        <span>{m.date.split(' ')[0]}</span>
                        <span>{m.frags}</span>
                        <span>{m.deaths}</span>
                        <span>{m.kd.toFixed(2)}</span>
                    </div>
                ))}
            </div>
        </div>
    );
};
