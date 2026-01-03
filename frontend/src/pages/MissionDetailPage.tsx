import React from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { MissionDetail } from '../components/MissionDetail';

export const MissionDetailPage: React.FC = () => {
    const { id } = useParams<{ id: string }>();
    const navigate = useNavigate();

    if (!id) return <div>Invalid Mission ID</div>;

    return (
        <MissionDetail
            missionId={parseInt(id, 10)}
            onBack={() => navigate('/missions')}
        />
    );
};
