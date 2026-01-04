import React from 'react';
import { useSearchParams } from 'react-router-dom';
import { AdminPlayersList } from '../components/AdminPlayersList';

const AdminPlayers: React.FC = () => {
    const [searchParams, setSearchParams] = useSearchParams();
    const missionIdFilter = searchParams.get('mission_id') ? parseInt(searchParams.get('mission_id')!) : undefined;

    const clearMissionFilter = () => {
        setSearchParams({});
    };

    return (
        <div>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <h1 className="admin-title">Игроки {missionIdFilter ? `(Миссия #${missionIdFilter})` : '(Все)'}</h1>
                {missionIdFilter && (
                    <button className="admin-btn" onClick={clearMissionFilter}>
                        Сбросить фильтр миссии
                    </button>
                )}
            </div>

            <AdminPlayersList missionId={missionIdFilter} />
        </div>
    );
};

export default AdminPlayers;
