import React, { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { fetchPlayerProfile } from '../api';
import { useRotation } from '../context/RotationContext';
import type { PlayerAggregatedStats } from '../api';
import '../components/MissionDetail.css';

export const PlayerProfile: React.FC = () => {
    const { name } = useParams<{ name: string }>();
    const navigate = useNavigate();
    const { currentRotationId } = useRotation();
    const [profile, setProfile] = useState<PlayerAggregatedStats | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        if (!name) return;

        const fetchData = async () => {
            setLoading(true);
            setError(null);
            try {
                const data = await fetchPlayerProfile(name, currentRotationId);
                setProfile(data);
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

    return (
        <div className="mission-detail">
            <h2>{profile.name}</h2>

            <div className="profile-stats-grid">
                <div className="stat-card">
                    <div className="label">Missions</div>
                    <div className="value">{profile.total_missions}</div>
                </div>
                <div className="stat-card">
                    <div className="label">K/D Ratio</div>
                    <div className="value">{profile.kd_ratio.toFixed(2)}</div>
                </div>
                <div className="stat-card">
                    <div className="label">Total Frags</div>
                    <div className="value">{profile.total_frags}</div>
                </div>
                <div className="stat-card">
                    <div className="label">Armor Kills</div>
                    <div className="value">{profile.total_destroyed_vehicles}</div>
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
            `}</style>

            <h3>История Отрядов</h3>
            <div className="player-table">
                <div className="table-header">
                    <span>Отряд</span>
                    <span>Миссии</span>
                    <span>Фраги</span>
                    <span>Смерти</span>
                    <span>K/D</span>
                </div>
                {profile.squads?.map(s => (
                    <div key={s.squad} className="table-row">
                        <span>{s.squad}</span>
                        <span>{s.total_missions}</span>
                        <span>{s.total_frags}</span>
                        <span>{s.total_deaths}</span>
                        <span>{s.kd_ratio.toFixed(2)}</span>
                    </div>
                ))}
            </div>

            <h3>История Миссий</h3>
            <div className="player-table missions-history-table">
                <div className="table-header">
                    <span>Миссия</span>
                    <span>Карта</span>
                    <span>Дата</span>
                    <span>Фраги</span>
                    <span>Смерти</span>
                    <span>K/D</span>
                </div>
                {profile.missions?.map(m => (
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
