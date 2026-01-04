import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { fetchTopSquads } from '../api';
import type { SquadAggregatedStats } from '../types';
import '../components/MissionDetail.css';

import { useRotation } from '../context/RotationContext';

export const TopSquads: React.FC = () => {
    const { currentRotationId } = useRotation();
    const [squads, setSquads] = useState<SquadAggregatedStats[]>([]);
    const [loading, setLoading] = useState(true);
    const navigate = useNavigate();

    useEffect(() => {
        setLoading(true);
        fetchTopSquads(currentRotationId)
            .then(setSquads)
            .catch(console.error)
            .finally(() => setLoading(false));
    }, [currentRotationId]);

    if (loading) return <div className="loading">Анализ эффективности отрядов...</div>;

    return (
        <div className="mission-detail">
            <h2>Топ Отрядов</h2>
            <div className="player-table">
                <div className="table-header">
                    <span>Отряд</span>
                    <span>Миссии</span>
                    <span>Фраги</span>
                    <span>Смерти</span>
                    <span>K/D</span>
                </div>
                {squads.map((s, index) => {
                    let rankClass = '';
                    if (index === 0) rankClass = 'rank-1';
                    if (index === 1) rankClass = 'rank-2';
                    if (index === 2) rankClass = 'rank-3';

                    return (
                        <div
                            key={s.squad_name}
                            className={`table-row clickable-row ${rankClass}`}
                            onClick={() => navigate(`/squads/${s.squad_name}`)}
                        >
                            <span>
                                {index === 0 && ''}
                                {index === 1 && ''}
                                {index === 2 && ''}
                                {s.squad_name}
                            </span>
                            <span>{s.total_missions}</span>
                            <span>{s.total_frags}</span>
                            <span>{s.total_deaths}</span>
                            <span>{s.kd_ratio.toFixed(2)}</span>
                        </div>
                    );
                })}
            </div>
            <style>{`
                .rank-1 {
                    background: linear-gradient(90deg, rgba(255, 215, 0, 0.1) 0%, transparent 100%);
                    border-left: 4px solid #FFD700 !important;
                }
                .rank-1 span {
                    color: #FFD700 !important;
                    font-weight: bold;
                    text-shadow: 0 0 10px rgba(255, 215, 0, 0.3);
                }

                .rank-2 {
                    background: linear-gradient(90deg, rgba(192, 192, 192, 0.1) 0%, transparent 100%);
                    border-left: 4px solid #C0C0C0 !important;
                }
                .rank-2 span {
                    color: #C0C0C0 !important;
                    font-weight: bold;
                    text-shadow: 0 0 10px rgba(192, 192, 192, 0.3);
                }

                .rank-3 {
                    background: linear-gradient(90deg, rgba(205, 127, 50, 0.1) 0%, transparent 100%);
                    border-left: 4px solid #CD7F32 !important;
                }
                .rank-3 span {
                    color: #CD7F32 !important;
                    font-weight: bold;
                    text-shadow: 0 0 10px rgba(205, 127, 50, 0.3);
                }
            `}</style>
        </div>

    );
};
