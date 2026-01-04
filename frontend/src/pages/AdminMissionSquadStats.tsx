import React from 'react';
import { AdminSquadStatsList } from '../components/AdminSquadStatsList';

const AdminMissionSquadStats: React.FC = () => {
    return (
        <div>
            <h1 className="admin-title">Статистика Отрядов (MissionSquadStats)</h1>
            <AdminSquadStatsList />
        </div>
    );
};

export default AdminMissionSquadStats;
