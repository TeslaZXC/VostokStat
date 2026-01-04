import React, { useState, useEffect } from 'react';
import { getMissionSquadStats, updateMissionSquadStat } from '../api';
import { AdminPagination } from '../components/AdminPagination';

interface SquadStat {
    id: number;
    squad_tag: string;
    side: string;
    frags: number;
    death: number;
    mission_id: number;
}

interface Props {
    missionId?: number;
}

export const AdminSquadStatsList: React.FC<Props> = ({ missionId }) => {
    const [stats, setStats] = useState<SquadStat[]>([]);
    const [total, setTotal] = useState(0);
    const [skip, setSkip] = useState(0);
    const [limit, setLimit] = useState(10);
    const [search, setSearch] = useState('');
    const [loading, setLoading] = useState(true);

    // Edit State
    const [editId, setEditId] = useState<number | null>(null);
    const [editForm, setEditForm] = useState<Partial<SquadStat>>({});

    const load = async () => {
        setLoading(true);
        try {
            const data = await getMissionSquadStats(skip, limit, search, missionId);
            setStats(data.items);
            setTotal(data.total);
        } catch (e) { console.error(e); }
        finally { setLoading(false); }
    };

    useEffect(() => { load(); }, [skip, limit, search, missionId]);

    const handleLimitChange = (newLimit: number) => {
        setLimit(newLimit);
        setSkip(0);
    };

    const handleEditClick = (s: SquadStat) => {
        setEditId(s.id);
        setEditForm({ ...s });
    };

    const handleEditSave = async () => {
        if (!editId) return;
        try {
            await updateMissionSquadStat(editId, editForm);
            setEditId(null);
            load();
        } catch (e) { alert("Ошибка обновления статистики"); }
    };

    return (
        <div>
            <div className="admin-card">
                <input
                    placeholder="Поиск по тегу отряда..."
                    className="admin-input"
                    value={search}
                    onChange={e => { setSearch(e.target.value); setSkip(0); }}
                    style={{ maxWidth: '400px' }}
                />
            </div>

            {/* Edit Modal */}
            {editId && (
                <div style={{
                    position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
                    background: 'rgba(0,0,0,0.5)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1100
                }}>
                    <div className="admin-card" style={{ width: '500px', margin: 0, padding: '2rem' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
                            <h2 style={{ margin: 0 }}>Редактирование Статистики #{editId}</h2>
                            <button onClick={() => setEditId(null)} style={{ background: 'none', border: 'none', fontSize: '1.5rem', cursor: 'pointer' }}>&times;</button>
                        </div>

                        <div style={{ display: 'grid', gap: '1rem' }}>
                            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                                <div>
                                    <label style={{ fontWeight: 'bold', display: 'block', marginBottom: '0.5rem' }}>Тег отряда</label>
                                    <input className="admin-input" value={editForm.squad_tag} onChange={e => setEditForm({ ...editForm, squad_tag: e.target.value })} />
                                </div>
                                <div>
                                    <label style={{ fontWeight: 'bold', display: 'block', marginBottom: '0.5rem' }}>Сторона</label>
                                    <select className="admin-input" value={editForm.side} onChange={e => setEditForm({ ...editForm, side: e.target.value })}>
                                        <option value="WEST">WEST</option>
                                        <option value="EAST">EAST</option>
                                        <option value="GUER">GUER</option>
                                    </select>
                                </div>
                            </div>

                            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                                <div>
                                    <label style={{ fontWeight: 'bold', display: 'block', marginBottom: '0.5rem' }}>Фраги</label>
                                    <input className="admin-input" type="number" value={editForm.frags} onChange={e => setEditForm({ ...editForm, frags: parseInt(e.target.value) })} />
                                </div>
                                <div>
                                    <label style={{ fontWeight: 'bold', display: 'block', marginBottom: '0.5rem' }}>Смерти</label>
                                    <input className="admin-input" type="number" value={editForm.death} onChange={e => setEditForm({ ...editForm, death: parseInt(e.target.value) })} />
                                </div>
                            </div>

                            <div>
                                <label style={{ fontWeight: 'bold', display: 'block', marginBottom: '0.5rem' }}>ID Миссии</label>
                                <input className="admin-input" type="number" value={editForm.mission_id} onChange={e => setEditForm({ ...editForm, mission_id: parseInt(e.target.value) })} />
                            </div>
                        </div>

                        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '2rem' }}>
                            <button className="admin-btn" onClick={() => setEditId(null)}>Отмена</button>
                            <button className="admin-btn admin-btn-primary" onClick={handleEditSave} style={{ padding: '0.5rem 1.5rem' }}>Сохранить</button>
                        </div>
                    </div>
                </div>
            )}

            <div className="admin-table-container">
                <table className="admin-table">
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>Тег Отряда</th>
                            <th>Сторона</th>
                            <th>Фраги</th>
                            <th>Смерти</th>
                            <th>Миссия</th>
                            <th>Действия</th>
                        </tr>
                    </thead>
                    <tbody>
                        {loading ? <tr><td colSpan={7}>Загрузка...</td></tr> : stats.map(s => (
                            <tr key={s.id}>
                                <td>{s.id}</td>
                                <td>{s.squad_tag}</td>
                                <td>{s.side}</td>
                                <td>{s.frags}</td>
                                <td>{s.death}</td>
                                <td>{s.mission_id}</td>
                                <td>
                                    <button
                                        onClick={() => handleEditClick(s)}
                                        className="admin-btn"
                                        style={{ padding: '0.2rem 0.5rem', fontSize: '0.8rem', borderColor: '#007bff', color: '#007bff' }}
                                    >
                                        Ред.
                                    </button>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>

            <AdminPagination
                total={total}
                limit={limit}
                skip={skip}
                onPageChange={setSkip}
                onLimitChange={handleLimitChange}
            />
        </div>
    );
};
