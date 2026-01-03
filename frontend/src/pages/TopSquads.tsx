import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { fetchTopSquads } from '../api';
import type { SquadAggregatedStats } from '../types';
import '../components/MissionDetail.css';

export const TopSquads: React.FC = () => {
    const [squads, setSquads] = useState<SquadAggregatedStats[]>([]);
    const [loading, setLoading] = useState(true);
    const navigate = useNavigate();

    useEffect(() => {
        fetchTopSquads()
            .then(setSquads)
            .catch(console.error)
            .finally(() => setLoading(false));
    }, []);

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
                {squads.map(s => (
                    <div
                        key={s.squad_name}
                        className="table-row clickable-row"
                        onClick={() => navigate(`/squads/${s.squad_name}`)}
                    >
                        <span>{s.squad_name}</span>
                        <span>{s.total_missions}</span>
                        <span>{s.total_frags}</span>
                        <span>{s.total_deaths}</span>
                        <span>{s.kd_ratio.toFixed(2)}</span>
                    </div>
                ))}
            </div>
        </div>
    );
};
