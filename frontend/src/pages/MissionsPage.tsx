import React from 'react';
import { useNavigate } from 'react-router-dom';
import { MissionList as List } from '../components/MissionList';

export const MissionsPage: React.FC = () => {
    const navigate = useNavigate();
    return (
        <div>
            <List onSelectMission={(id) => navigate(`/missions/${id}`)} />
        </div>
    );
};
