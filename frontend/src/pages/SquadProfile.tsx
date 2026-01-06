import React, { useEffect, useState } from 'react';
import { useRotation } from '../context/RotationContext';
import { useParams, useNavigate } from 'react-router-dom';
import { fetchSquadProfile } from '../api';
import { formatPlayerName, getCleanName } from '../utils';
import type { SquadStats } from '../api';
import '../components/MissionDetail.css';
import {
    LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts';


export const SquadProfile: React.FC = () => {
    const { name } = useParams<{ name: string }>();
    const navigate = useNavigate();
    const { currentRotationId } = useRotation();
    const [stats, setStats] = useState<SquadStats | null>(null);
    const [loading, setLoading] = useState(true);

    const [page, setPage] = useState(1);
    const PAGE_SIZE = 5;

    useEffect(() => {
        const load = async () => {
            if (!name) return;
            setLoading(true);
            try {
                // Fetch profile only
                const profile = await fetchSquadProfile(name, currentRotationId);
                setStats(profile);
            } catch (e) {
                console.error(e);
            } finally {
                setLoading(false);
            }
        };
        load();
    }, [name, currentRotationId]);


    if (loading) return <div className="loading">Получение данных отряда...</div>;
    if (!stats) return <div className="error">Отряд не найден</div>;

    const totalPages = Math.ceil(stats.players.length / PAGE_SIZE);
    const currentMembers = stats.players.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);

    return (
        <div className="mission-detail">
            <div className="page-header-row" style={{ marginBottom: '2rem' }}>
                <h2 style={{ margin: 0 }}>ОТРЯД [{stats.squad_name.toUpperCase()}]</h2>
            </div>


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

            {/* Chart Section */}
            {stats.missions && stats.missions.length > 0 && (
                <div className="chart-container" style={{ marginBottom: '2rem', padding: '1rem', background: 'rgba(0,0,0,0.2)', border: '1px solid #3c4238', borderRadius: '8px' }}>
                    <h3>Динамика фрагов</h3>
                    <ResponsiveContainer width="100%" height={300}>
                        <LineChart data={[...stats.missions].reverse()}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#444" />
                            <XAxis dataKey="date" tickFormatter={(val) => val.split(' ')[0]} stroke="#888" />
                            <YAxis stroke="#888" />
                            <Tooltip
                                contentStyle={{ backgroundColor: '#1a1e1b', border: '1px solid #3c4238' }}
                                labelStyle={{ color: '#e0e0e0' }}
                            />
                            <Legend />
                            <Line type="monotone" dataKey="frags" name="Фраги" stroke="#007bff" strokeWidth={2} dot={false} />
                            <Line type="monotone" dataKey="deaths" name="Смерти" stroke="#dc3545" strokeWidth={2} dot={false} />
                        </LineChart>
                    </ResponsiveContainer>
                </div>
            )}

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

            <h3>История Миссий</h3>
            <div className="player-table">
                <div className="table-header">
                    <span>Миссия</span>
                    <span>Карта</span>
                    <span>Дата</span>
                    <span>Фраги</span>
                    <span>Смерти</span>
                    <span>K/D</span>
                </div>
                {stats.missions?.map(m => (
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
