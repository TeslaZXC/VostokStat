import React, { useState, useEffect } from 'react';
import { getAdminPlayers, updateAdminPlayer } from '../api';
import { AdminPagination } from '../components/AdminPagination';

interface Player {
    id: number;
    name: string;
    squad: string;
    side: string;
    mission_id: number;
}

interface Props {
    missionId?: number;
}

export const AdminPlayersList: React.FC<Props> = ({ missionId }) => {
    const [players, setPlayers] = useState<Player[]>([]);
    const [total, setTotal] = useState(0);
    const [skip, setSkip] = useState(0);
    const [limit, setLimit] = useState(10);
    const [search, setSearch] = useState('');
    const [loading, setLoading] = useState(true);

    // Edit State
    const [editId, setEditId] = useState<number | null>(null);
    const [editForm, setEditForm] = useState<Partial<Player>>({});

    const load = async () => {
        setLoading(true);
        try {
            const data = await getAdminPlayers(skip, limit, search, missionId);
            setPlayers(data.items);
            setTotal(data.total);
        } catch (e) {
            console.error(e);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        load();
    }, [skip, limit, search, missionId]);

    const handleLimitChange = (newLimit: number) => {
        setLimit(newLimit);
        setSkip(0);
    };

    const handleEditClick = (p: Player) => {
        setEditId(p.id);
        setEditForm({ ...p });
    };

    const handleEditSave = async () => {
        if (!editId) return;
        try {
            await updateAdminPlayer(editId, editForm);
            setEditId(null);
            load();
        } catch (e) {
            alert("Ошибка обновления игрока");
        }
    };

    return (
        <div>
            <div className="admin-card">
                <input
                    placeholder="Поиск игрока..."
                    className="admin-input"
                    value={search}
                    onChange={e => { setSearch(e.target.value); setSkip(0); }}
                    style={{ maxWidth: '400px' }}
                />
            </div>

            {/* Edit Modal - Rendered slightly differently if embedded, but keeping it modal to avoid clutter */}
            {editId && (
                <div style={{
                    position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
                    background: 'rgba(0,0,0,0.5)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1100 // Higher z-index for nested
                }}>
                    <div className="admin-card" style={{ width: '600px', margin: 0, padding: '2rem', maxHeight: '90vh', overflowY: 'auto' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
                            <h2 style={{ margin: 0 }}>Редактирование Игрока #{editId}</h2>
                            <button onClick={() => setEditId(null)} style={{ background: 'none', border: 'none', fontSize: '1.5rem', cursor: 'pointer' }}>&times;</button>
                        </div>

                        <div style={{ display: 'grid', gap: '1rem' }}>
                            <div>
                                <label style={{ fontWeight: 'bold', display: 'block', marginBottom: '0.5rem' }}>Имя игрока</label>
                                <input className="admin-input" value={editForm.name} onChange={e => setEditForm({ ...editForm, name: e.target.value })} />
                            </div>

                            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                                <div>
                                    <label style={{ fontWeight: 'bold', display: 'block', marginBottom: '0.5rem' }}>Отряд</label>
                                    <input className="admin-input" value={editForm.squad} onChange={e => setEditForm({ ...editForm, squad: e.target.value })} />
                                </div>
                                <div>
                                    <label style={{ fontWeight: 'bold', display: 'block', marginBottom: '0.5rem' }}>Сторона</label>
                                    <select className="admin-input" value={editForm.side} onChange={e => setEditForm({ ...editForm, side: e.target.value })}>
                                        <option value="WEST">WEST</option>
                                        <option value="EAST">EAST</option>
                                        <option value="GUER">GUER</option>
                                        <option value="CIV">CIV</option>
                                    </select>
                                </div>
                            </div>

                            <div>
                                <label style={{ fontWeight: 'bold', display: 'block', marginBottom: '0.5rem' }}>ID Миссии</label>
                                <input className="admin-input" type="number" value={editForm.mission_id} onChange={e => setEditForm({ ...editForm, mission_id: parseInt(e.target.value) })} />
                            </div>
                        </div>

                        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '2rem' }}>
                            <button className="admin-btn" onClick={() => setEditId(null)}>Отмена</button>
                            <button className="admin-btn admin-btn-primary" onClick={handleEditSave} style={{ padding: '0.5rem 1.5rem' }}>Сохранить изменения</button>
                        </div>
                    </div>
                </div>
            )}

            <div className="admin-table-container">
                <table className="admin-table">
                    <thead><tr><th>ID</th><th>Имя</th><th>Отряд</th><th>Сторона</th><th>Миссия</th><th>Действия</th></tr></thead>
                    <tbody>
                        {loading ? <tr><td colSpan={6}>Загрузка...</td></tr> : players.map(p => (
                            <tr key={p.id}>
                                <td>{p.id}</td>
                                <td>{p.name}</td>
                                <td>{p.squad}</td>
                                <td>{p.side}</td>
                                <td>{p.mission_id}</td>
                                <td>
                                    <button
                                        onClick={() => handleEditClick(p)}
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
