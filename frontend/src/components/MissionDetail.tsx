import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { fetchMissionDetails } from '../api';
import type { MissionDetail as MissionDetailType, PlayerStats, SquadStats } from '../types';
import './MissionDetail.css';
import { formatDuration, formatPlayerName, getCleanName } from '../utils';

interface MissionDetailProps {
    missionId: number;
    onBack: () => void;
}

type SortConfig<T> = {
    key: keyof T | null;
    direction: 'asc' | 'desc';
};

export const MissionDetail: React.FC<MissionDetailProps> = ({ missionId, onBack }) => {
    const navigate = useNavigate();
    const [mission, setMission] = useState<MissionDetailType | null>(null);
    const [loading, setLoading] = useState(true);

    // Player list state
    const [playerPage, setPlayerPage] = useState(1);
    const [playersPerPage] = useState(20);
    const [playerSearch, setPlayerSearch] = useState('');
    const [playerSort, setPlayerSort] = useState<SortConfig<PlayerStats>>({ key: 'frags', direction: 'desc' });
    const [squadSort, setSquadSort] = useState<SortConfig<SquadStats>>({ key: 'frags', direction: 'desc' });
    const [selectedSquadTag, setSelectedSquadTag] = useState<string | null>(null);
    const [selectedPlayerId, setSelectedPlayerId] = useState<number | null>(null);

    const toggleSquad = (squadTag: string) => {
        if (selectedSquadTag === squadTag) {
            setSelectedSquadTag(null);
        } else {
            setSelectedSquadTag(squadTag);
        }
    };

    const togglePlayer = (playerId: number) => {
        if (selectedPlayerId === playerId) {
            setSelectedPlayerId(null);
        } else {
            setSelectedPlayerId(playerId);
        }
    };

    interface SquadMember {
        name: string;
        frags: number;
        death: number;
        distance: number;
        dk_ratio?: number;
    }

    const [squadMemberSort, setSquadMemberSort] = useState<SortConfig<SquadMember>>({ key: 'frags', direction: 'desc' });

    const getSortedMembers = (members: any[]) => {
        return sortData(members || [], squadMemberSort);
    };

    useEffect(() => {
        const loadData = async () => {
            try {
                setLoading(true);
                const data = await fetchMissionDetails(missionId);
                setMission(data);
            } catch (e) {
                console.error(e);
            } finally {
                setLoading(false);
            }
        };
        loadData();
    }, [missionId]);

    const playerSquadMap = React.useMemo(() => {
        if (!mission) return new Map<string, string>();
        const map = new Map<string, string>();
        mission.players.forEach(p => {
            if (p.squad) map.set(p.name, p.squad);
        });
        return map;
    }, [mission]);

    const handleSort = <T,>(key: keyof T, currentSort: SortConfig<T>, setSort: React.Dispatch<React.SetStateAction<SortConfig<T>>>) => {
        let direction: 'asc' | 'desc' = 'desc';
        if (currentSort.key === key && currentSort.direction === 'desc') {
            direction = 'asc';
        }
        setSort({ key, direction });
    };

    const sortData = <T,>(data: T[], sortConfig: SortConfig<T>) => {
        if (!sortConfig.key) return data;
        return [...data].sort((a, b) => {
            // @ts-ignore
            const aVal = a[sortConfig.key];
            // @ts-ignore
            const bVal = b[sortConfig.key];

            if (aVal < bVal) return sortConfig.direction === 'asc' ? -1 : 1;
            if (aVal > bVal) return sortConfig.direction === 'asc' ? 1 : -1;
            return 0;
        });
    };

    if (loading) return <div className="loading">Получение разведданных...</div>;
    if (!mission) return <div className="error">Данные повреждены или отсутствуют.</div>;

    // Process Squads
    const westSquads = sortData(mission.squads.filter(s => s.side === 'WEST'), squadSort);
    const eastSquads = sortData(mission.squads.filter(s => s.side === 'EAST'), squadSort);

    // Process Players
    const filteredPlayers = mission.players.filter(p =>
        p.name.toLowerCase().includes(playerSearch.toLowerCase())
    );
    const sortedPlayers = sortData(filteredPlayers, playerSort);
    const totalPages = Math.ceil(sortedPlayers.length / playersPerPage);
    const currentPlayers = sortedPlayers.slice(
        (playerPage - 1) * playersPerPage,
        playerPage * playersPerPage
    );

    const renderSortArrow = (key: string, currentSort: SortConfig<any>) => {
        if (currentSort.key !== key) return <span className="sort-arrow">↕</span>;
        return <span className="sort-arrow">{currentSort.direction === 'asc' ? '↑' : '↓'}</span>;
    };

    const SquadTable = ({ squads, title, sideClass }: { squads: SquadStats[], title: string, sideClass: string }) => (
        <div className={`squad-column ${sideClass}`}>
            <h3 className="side-title">{title}</h3>
            <div className="player-table compact">
                <div className="table-header">
                    <span onClick={() => handleSort('squad_tag', squadSort, setSquadSort)}>Отряд {renderSortArrow('squad_tag', squadSort)}</span>
                    <span onClick={() => handleSort('frags', squadSort, setSquadSort)}>Ф {renderSortArrow('frags', squadSort)}</span>
                    <span onClick={() => handleSort('death', squadSort, setSquadSort)}>С {renderSortArrow('death', squadSort)}</span>
                    <span onClick={() => handleSort('tk', squadSort, setSquadSort)}>ТК {renderSortArrow('tk', squadSort)}</span>
                </div>
                {squads.map(s => (
                    <React.Fragment key={s.squad_tag}>
                        <div
                            className={`table-row clickable-row ${selectedSquadTag === s.squad_tag ? 'active-row' : ''}`}
                            onClick={() => toggleSquad(s.squad_tag)}
                        >
                            <div style={{ display: 'flex', alignItems: 'center' }}>
                                <span
                                    className="squad-tag hover-link"
                                    onClick={(e) => {
                                        e.stopPropagation();
                                        navigate(`/squads/${s.squad_tag}`);
                                    }}
                                    style={{ cursor: 'pointer', textDecoration: 'underline' }}
                                >
                                    {s.squad_tag}
                                </span>
                            </div>
                            <span>{s.frags}</span>
                            <span>{s.death}</span>
                            <span>{s.tk}</span>
                        </div>
                        {selectedSquadTag === s.squad_tag && (
                            <div className="squad-details-inline">
                                <div className="inline-header clickable">
                                    <span onClick={() => handleSort('name', squadMemberSort, setSquadMemberSort)}>Боец {renderSortArrow('name', squadMemberSort)}</span>
                                    <span onClick={() => handleSort('frags', squadMemberSort, setSquadMemberSort)}>Фраги {renderSortArrow('frags', squadMemberSort)}</span>
                                    <span onClick={() => handleSort('death', squadMemberSort, setSquadMemberSort)}>Смерти {renderSortArrow('death', squadMemberSort)}</span>
                                    <span onClick={() => handleSort('dk_ratio', squadMemberSort, setSquadMemberSort)}>K/D {renderSortArrow('dk_ratio', squadMemberSort)}</span>
                                </div>
                                {getSortedMembers(s.members || s.squad_players || []).map((m: any) => (
                                    <div key={m.name} className="inline-row">
                                        <div>
                                            <span
                                                className="hover-link"
                                                onClick={(e) => {
                                                    e.stopPropagation();
                                                    navigate(`/players/${getCleanName(m.name)}`);
                                                }}
                                                style={{ cursor: 'pointer', textDecoration: 'underline' }}
                                            >
                                                {formatPlayerName(m.name, s.squad_tag)}
                                            </span>
                                        </div>
                                        <span>{m.frags}</span>
                                        <span>{m.death}</span>
                                        <span>{(m.frags / (m.death || 1)).toFixed(2)}</span>
                                    </div>
                                ))}
                            </div>
                        )}
                    </React.Fragment>
                ))}
            </div>
        </div>
    );

    return (
        <div className="mission-detail">
            <div className="detail-header">
                <button className="back-btn" onClick={onBack}>&lt; ВЕРНУТЬСЯ К ОПЕРАЦИЯМ</button>
                <h2>{mission.missionName}</h2>
                <div className="meta-info">
                    <span>Дата: {mission.file_date}</span>
                    <span>Карта: {mission.map}</span>
                    <span>Время: {formatDuration(mission.duration_frames)}</span>
                </div>
            </div>

            <div className="squads-section">
                <SquadTable squads={westSquads} title="WEST FORCES" sideClass="west-side" />
                <div className="vs-divider">VS</div>
                <SquadTable squads={eastSquads} title="EAST FORCES" sideClass="east-side" />
            </div>

            <div className="stats-section">
                <div className="section-controls">
                    <h3>Личный Состав</h3>
                    <div className="filters">
                        <input
                            type="text"
                            placeholder="Фильтр бойцов..."
                            value={playerSearch}
                            onChange={(e) => { setPlayerSearch(e.target.value); setPlayerPage(1); }}
                            className="table-search"
                        />
                        <div className="pagination">
                            <button disabled={playerPage === 1} onClick={() => setPlayerPage(p => p - 1)}>&lt;</button>
                            <span>СТР. {playerPage} / {totalPages || 1}</span>
                            <button disabled={playerPage === totalPages} onClick={() => setPlayerPage(p => p + 1)}>&gt;</button>
                        </div>
                    </div>
                </div>

                <div className="player-table">
                    <div className="table-header clickable">
                        <span onClick={() => handleSort('name', playerSort, setPlayerSort)}>Имя {renderSortArrow('name', playerSort)}</span>
                        <span onClick={() => handleSort('side', playerSort, setPlayerSort)}>Сторона {renderSortArrow('side', playerSort)}</span>
                        <span onClick={() => handleSort('frags', playerSort, setPlayerSort)}>Фраги {renderSortArrow('frags', playerSort)}</span>
                        <span onClick={() => handleSort('death', playerSort, setPlayerSort)}>Смерти {renderSortArrow('death', playerSort)}</span>
                        <span>K/D</span>
                    </div>
                    {currentPlayers.map(p => (
                        <React.Fragment key={p.id}>
                            <div
                                className={`table-row clickable-row ${selectedPlayerId === p.id ? 'active-row' : ''}`}
                                onClick={() => togglePlayer(p.id)}
                            >
                                <div style={{ display: 'flex', alignItems: 'center' }}>
                                    <span
                                        className="hover-link"
                                        onClick={(e) => {
                                            e.stopPropagation();
                                            navigate(`/players/${getCleanName(p.name)}`);
                                        }}
                                        style={{ cursor: 'pointer', textDecoration: 'underline' }}
                                    >
                                        {formatPlayerName(p.name, p.squad)}
                                    </span>
                                </div>
                                <span className={`side ${p.side?.toLowerCase()}`}>{p.side}</span>
                                <span>{p.frags}</span>
                                <span>{p.death}</span>
                                <span>{(p.frags / (p.death || 1)).toFixed(2)}</span>
                            </div>
                            {selectedPlayerId === p.id && (
                                <div className="player-details-inline">
                                    <div className="detail-columns">
                                        <div className="detail-col">
                                            <h4>Уничтоженные Противники ({p.victims_players?.length || 0})</h4>
                                            <div className="event-list inline-list">
                                                {p.victims_players && p.victims_players.length > 0 ? (
                                                    p.victims_players.map((k, i) => (
                                                        <div key={i} className="event-item kill">
                                                            <span
                                                                className="event-name hover-link"
                                                                onClick={(e) => {
                                                                    e.stopPropagation();
                                                                    navigate(`/players/${getCleanName(k.name)}`);
                                                                }}
                                                                style={{ cursor: 'pointer', textDecoration: 'underline' }}
                                                            >
                                                                {formatPlayerName(k.name, playerSquadMap.get(k.name))}
                                                            </span>
                                                            <span className="event-weapon">{k.weapon}</span>
                                                            <span className="event-dist">{k.distance.toFixed(0)}м</span>
                                                        </div>
                                                    ))
                                                ) : <div className="no-data">Нет подтвержденных убийств</div>}
                                            </div>
                                        </div>
                                        <div className="detail-col">
                                            <h4>Уничтоженная Техника ({p.destroyed_vehicles?.length || 0})</h4>
                                            <div className="event-list inline-list">
                                                {p.destroyed_vehicles && p.destroyed_vehicles.length > 0 ? (
                                                    p.destroyed_vehicles.map((v, i) => (
                                                        <div key={i} className="event-item vehicle">
                                                            <span className="event-name">{v.name} ({v.veh_type})</span>
                                                            <span className="event-weapon">{v.weapon}</span>
                                                        </div>
                                                    ))
                                                ) : <div className="no-data">Техника не уничтожена</div>}
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            )}
                        </React.Fragment>
                    ))}
                </div>
            </div>


        </div >
    );
};
