import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { fetchSquadProfile } from '../api';
import { formatPlayerName, getCleanName } from '../utils';
import '../components/MissionDetail.css';

interface SquadMember {
    name: string;
    total_missions: number;
    total_frags: number;
    total_frags_veh: number;
    total_frags_inf: number;
    total_deaths: number;
    total_destroyed_vehicles: number;
    kd_ratio: number;
}

interface SquadStats {
    squad_name: string;
    total_missions: number;
    total_frags: number;
    total_deaths: number;
    kd_ratio: number;
    players: SquadMember[];
}

export const SquadProfile: React.FC = () => {
    const { name } = useParams<{ name: string }>();
    const navigate = useNavigate();
    const [stats, setStats] = useState<SquadStats | null>(null);
    const [loading, setLoading] = useState(true);
    const [page, setPage] = useState(1);
    const PAGE_SIZE = 5;

    useEffect(() => {
        if (!name) return;
        fetchSquadProfile(name)
            .then(setStats)
            .catch(console.error)
            .finally(() => setLoading(false));
    }, [name]);

    if (loading) return <div className="loading">Получение данных отряда...</div>;
    if (!stats) return <div className="error">Отряд не найден</div>;

    const totalPages = Math.ceil(stats.players.length / PAGE_SIZE);
    const currentMembers = stats.players.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);

    return (
        <div className="mission-detail">
            <h2>ОТРЯД [{stats.squad_name.toUpperCase()}]</h2>

            <div className="profile-stats-grid">
                <div className="stat-card">
                    <div className="label">Миссии</div>
                    <div className="value">{stats.total_missions}</div>
                </div>
                <div className="stat-card">
                    <div className="label">K/D Ratio</div>
                    <div className="value">{stats.kd_ratio.toFixed(2)}</div>
                </div>
                <div className="stat-card">
                    <div className="label">Всего фрагов</div>
                    <div className="value">{stats.total_frags}</div>
                </div>
                <div className="stat-card">
                    <div className="label">Всего потерь</div>
                    <div className="value">{stats.total_deaths}</div>
                </div>
            </div>

            <div className="player-table">
                <div className="table-header">
                    <span>Боец</span>
                    <span>Миссии</span>
                    <span>Фраги (Всего)</span>
                    <span>Пехота</span>
                    <span>Техника</span>
                    <span>Смерти</span>
                    <span>Уничтожил Техники</span>
                    <span>K/D</span>
                </div>
                {currentMembers.map((p, idx) => (
                    <div
                        key={idx}
                        className="table-row clickable-row"
                        onClick={() => navigate(`/players/${getCleanName(p.name)}`)}
                    >
                        <span>{formatPlayerName(p.name, stats.squad_name)}</span>
                        <span>{p.total_missions}</span>
                        <span>{p.total_frags}</span>
                        <span>{p.total_frags_inf}</span>
                        <span>{p.total_frags_veh}</span>
                        <span>{p.total_deaths}</span>
                        <span>{p.total_destroyed_vehicles}</span>
                        <span className={p.kd_ratio >= 1 ? 'kd-positive' : 'kd-negative'}>
                            {p.kd_ratio.toFixed(2)}
                        </span>
                    </div>
                ))}
            </div>

            {totalPages > 1 && (
                <div className="pagination">
                    <button disabled={page === 1} onClick={() => setPage(p => p - 1)}>&lt;</button>
                    <span>СТР. {page} / {totalPages}</span>
                    <button disabled={page === totalPages} onClick={() => setPage(p => p + 1)}>&gt;</button>
                </div>
            )}

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
                .pagination {
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    gap: 1rem;
                    margin-top: 1.5rem;
                    color: #888;
                }
                .pagination button {
                    background: rgba(255,255,255,0.1);
                    border: 1px solid var(--color-border);
                    color: #fff;
                    padding: 0.2rem 0.8rem;
                    cursor: pointer;
                }
                .pagination button:disabled {
                    opacity: 0.3;
                    cursor: not-allowed;
                }
            `}</style>
        </div>
    );
};
