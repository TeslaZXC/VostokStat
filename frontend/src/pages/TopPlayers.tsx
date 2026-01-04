import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { fetchTopPlayers } from '../api';
import type { PlayerAggregatedStats } from '../types';
import { formatPlayerName, getCleanName } from '../utils';
import '../components/MissionDetail.css';

import { useRotation } from '../context/RotationContext';

export const TopPlayers: React.FC = () => {
    const navigate = useNavigate();
    const { currentRotationId } = useRotation();
    const [players, setPlayers] = useState<PlayerAggregatedStats[]>([]);
    const [category, setCategory] = useState('general');
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const loadData = async () => {
            setLoading(true);
            try {
                const data = await fetchTopPlayers(category, currentRotationId);
                setPlayers(data);
            } catch (e) {
                console.error(e);
            } finally {
                setLoading(false);
            }
        };
        loadData();
    }, [category, currentRotationId]);

    return (
        <div className="mission-detail">
            <h2>Рейтинг Бойцов</h2>

            <div className="category-tabs">
                <button
                    className={`tab-btn ${category === 'general' ? 'active' : ''}`}
                    onClick={() => setCategory('general')}
                >Общий</button>
                <button
                    className={`tab-btn ${category === 'vehicle' ? 'active' : ''}`}
                    onClick={() => setCategory('vehicle')}
                >Техника</button>
                <button
                    className={`tab-btn ${category === 'infantry' ? 'active' : ''}`}
                    onClick={() => setCategory('infantry')}
                >Пехота</button>
            </div>

            <style>{`
                .category-tabs {
                    display: flex;
                    gap: 1rem;
                    margin-bottom: 2rem;
                }
                .tab-btn {
                    background: transparent;
                    border: 1px solid var(--color-border);
                    color: var(--color-text-main);
                    padding: 0.5rem 1.5rem;
                    cursor: pointer;
                    text-transform: uppercase;
                    letter-spacing: 1px;
                }
                .tab-btn.active {
                    background: var(--color-text-muted);
                    color: var(--color-bg-dark);
                    border-color: var(--color-text-muted);
                    font-weight: bold;
                }
                .text-west { color: #8cb9ff !important; }
                .text-east { color: #ff8c8c !important; }
            `}</style>

            {loading ? (
                <div className="loading">Синхронизация списков лидеров...</div>
            ) : (
                <div className="player-table">
                    <div className="table-header">
                        <span>Имя</span>
                        <span>Миссии</span>
                        <span>Убийств</span>
                        <span>Смертей</span>
                        <span>K/D</span>
                    </div>
                    {players.map(p => (
                        <div
                            key={p.name}
                            className="table-row clickable-row"
                            onClick={() => navigate(`/players/${getCleanName(p.name)}`)}
                        >
                            <span className={p.side === 'WEST' ? 'text-west' : p.side === 'EAST' ? 'text-east' : ''}>
                                {formatPlayerName(p.name)}
                            </span>
                            <span>{p.total_missions}</span>
                            <span>{p.total_frags}</span>
                            <span>{p.total_deaths}</span>
                            <span>{p.kd_ratio.toFixed(2)}</span>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
};
