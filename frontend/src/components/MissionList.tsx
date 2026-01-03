import React, { useEffect, useState } from 'react';
import { fetchMissions } from '../api';
import type { MissionSummary } from '../types';
import './MissionList.css';
import { formatDuration } from '../utils';

interface MissionListProps {
    onSelectMission: (id: number) => void;
}

export const MissionList: React.FC<MissionListProps> = ({ onSelectMission }) => {
    const [missions, setMissions] = useState<MissionSummary[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        loadMissions();
    }, []);

    const loadMissions = async () => {
        try {
            setLoading(true);
            const data = await fetchMissions();
            setMissions(data);
        } catch {
            setError('Не удалось загрузить данные');
        } finally {
            setLoading(false);
        }
    };

    if (loading) return <div className="loading">Установка соединения...</div>;
    if (error) return <div className="error">{error}</div>;

    return (
        <div className="mission-list">
            <h2>Последние Операции</h2>
            <div className="mission-grid-header">
                <span>Дата</span>
                <span>Миссия</span>
                <span>Карта</span>
                <span>Победитель</span>
                <span>Длит.</span>
            </div>
            <div className="mission-grid">
                {missions.map((m) => (
                    <div key={m.id} className="mission-row" onClick={() => onSelectMission(m.id)}>
                        <span className="mission-date">{m.file_date}</span>
                        <span className="mission-name" title={m.missionName}>{m.missionName}</span>
                        <span className="mission-map">{m.map}</span>
                        <span className={`mission-winner ${m.win_side?.toLowerCase()}`}>{m.win_side || 'Ничья'}</span>
                        <span className="mission-duration">{formatDuration(m.duration_frames)}</span>
                    </div>
                ))}
            </div>
        </div>
    );
};
