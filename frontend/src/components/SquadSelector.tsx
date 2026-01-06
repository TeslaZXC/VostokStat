import React, { useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import type { TotalSquadsResponse } from '../api';

interface SquadSelectorProps {
    currentSquad?: string; // If null/undefined, matches "Total Stats"
    data: TotalSquadsResponse | null;
    isLoading?: boolean;
}

export const SquadSelector: React.FC<SquadSelectorProps> = ({ currentSquad, data, isLoading }) => {
    const navigate = useNavigate();

    // Flatten and sort all squads for the dropdown
    const allSquads = useMemo(() => {
        if (!data) return [];
        const squads = [
            ...(data.west || []),
            ...(data.east || []),
            ...(data.other || [])
        ];
        // Sort alphabetically
        return squads.sort((a, b) => a.squad_name.localeCompare(b.squad_name));
    }, [data]);

    const handleChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
        const value = e.target.value;
        if (value === 'ALL') {
            navigate('/total-stats');
        } else {
            navigate(`/squads/${encodeURIComponent(value)}`);
        }
    };

    if (isLoading) {
        return <select disabled><option>Загрузка...</option></select>;
    }

    return (
        <select
            className="squad-selector"
            value={currentSquad || 'ALL'}
            onChange={handleChange}
        >
            <option value="ALL">Все отряды</option>
            <optgroup label="Отряды">
                {allSquads.map(s => (
                    <option key={s.squad_name} value={s.squad_name}>
                        {s.squad_name}
                    </option>
                ))}
            </optgroup>
            <style>{`
                .squad-selector {
                    padding: 0.5rem 1rem;
                    background: rgba(0, 0, 0, 0.4);
                    border: 1px solid #3c4238;
                    color: #fff;
                    font-size: 1rem;
                    border-radius: 4px;
                    cursor: pointer;
                    outline: none;
                    min-width: 200px;
                }
                .squad-selector:hover {
                    border-color: #5c6358;
                }
                .squad-selector option {
                    background: #1a1e1b;
                    color: #fff;
                }
            `}</style>
        </select>
    );
};
