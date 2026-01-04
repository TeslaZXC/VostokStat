import React, { useState, useEffect } from 'react';
import { getAdminMissions, deleteAdminMission, deleteAllMissions, updateAdminMission } from '../api';
import { AdminPagination } from '../components/AdminPagination';
import { AdminPlayersList } from '../components/AdminPlayersList';
import { AdminSquadStatsList } from '../components/AdminSquadStatsList';
import { useNavigate } from 'react-router-dom';

interface Mission {
    id: number;
    mission_name: string;
    file_date: string;
    map_name: string;
    total_players: number;
    win_side: string;
}

type Tab = 'info' | 'players' | 'squads';

const AdminMissions: React.FC = () => {
    const [missions, setMissions] = useState<Mission[]>([]);
    const [total, setTotal] = useState(0);
    const [skip, setSkip] = useState(0);
    const [limit, setLimit] = useState(10);
    const [search, setSearch] = useState('');
    const [loading, setLoading] = useState(true);

    const navigate = useNavigate();

    // Edit State
    const [editId, setEditId] = useState<number | null>(null);
    const [editForm, setEditForm] = useState<Partial<Mission>>({});
    const [activeTab, setActiveTab] = useState<Tab>('info');

    const load = async () => {
        setLoading(true);
        try {
            const data = await getAdminMissions(skip, limit, search);
            setMissions(data.items);
            setTotal(data.total);
        } catch (e) {
            console.error(e);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        load();
    }, [skip, limit, search]);

    const handleLimitChange = (newLimit: number) => {
        setLimit(newLimit);
        setSkip(0);
    };

    const handleDelete = async (id: number) => {
        if (!confirm("Удалить эту миссию?")) return;
        try {
            await deleteAdminMission(id);
            load();
        } catch (e) {
            alert("Ошибка при удалении миссии");
        }
    };

    const handleDeleteAll = async () => {
        if (!confirm("ВНИМАНИЕ: УДАЛИТЬ ВСЕ МИССИИ? Это действие нельзя отменить.")) return;
        if (!confirm("Вы абсолютно уверены?")) return;
        try {
            await deleteAllMissions();
            load();
        } catch (e) {
            alert("Ошибка при удалении всех миссий");
        }
    };

    const handleEditClick = (m: Mission) => {
        setEditId(m.id);
        setEditForm({ ...m });
        setActiveTab('info'); // Reset to info tab
    };

    const handleEditSave = async () => {
        if (!editId) return;
        try {
            await updateAdminMission(editId, editForm);
            alert("Миссия обновлена!");
            // setEditId(null); // Optional: Do we want to close or stay? Let's stay since we might edit players next.
            load();
        } catch (e) {
            alert("Ошибка обновления миссии");
        }
    };

    return (
        <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
                <h1 className="admin-title">Миссии</h1>
                <button
                    onClick={handleDeleteAll}
                    className="admin-btn admin-btn-danger"
                >
                    УДАЛИТЬ ВСЕ МИССИИ
                </button>
            </div>

            <div className="admin-card">
                <input
                    placeholder="Поиск миссии..."
                    className="admin-input"
                    value={search}
                    onChange={e => { setSearch(e.target.value); setSkip(0); }}
                    style={{ width: '100%', maxWidth: '400px' }}
                />
            </div>

            {/* Unified Modal */}
            {editId && (
                <div style={{
                    position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
                    background: 'rgba(0,0,0,0.5)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000
                }}>
                    <div className="admin-card" style={{ width: '900px', height: '80vh', margin: 0, padding: '0', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>

                        {/* Modal Header */}
                        <div style={{ padding: '1.5rem', borderBottom: '1px solid #dee2e6', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <h2 style={{ margin: 0 }}>Редактирование миссии #{editId}</h2>
                            <button onClick={() => setEditId(null)} style={{ background: 'none', border: 'none', fontSize: '1.5rem', cursor: 'pointer' }}>&times;</button>
                        </div>

                        {/* Tabs */}
                        <div className="admin-tabs">
                            <button 
                                onClick={() => setActiveTab('info')}
                                className={`admin-tab ${activeTab === 'info' ? 'active' : ''}`}
                            >
                                Основное
                            </button>
                            <button 
                                onClick={() => setActiveTab('players')}
                                className={`admin-tab ${activeTab === 'players' ? 'active' : ''}`}
                            >
                                Игроки
                            </button>
                            <button 
                                onClick={() => setActiveTab('squads')}
                                className={`admin-tab ${activeTab === 'squads' ? 'active' : ''}`}
                            >
                                Отряды
                            </button>
                        </div>

                        {/* Model Body (Scrollable) */}
                        <div style={{ flex: 1, overflowY: 'auto', padding: '2rem' }}>

                            {/* Info Tab */}
                            {activeTab === 'info' && (
                                <div style={{ display: 'grid', gap: '1rem' }}>
                                    <div>
                                        <label style={{ fontWeight: 'bold', display: 'block', marginBottom: '0.5rem' }}>Название</label>
                                        <input className="admin-input" value={editForm.mission_name} onChange={e => setEditForm({ ...editForm, mission_name: e.target.value })} />
                                    </div>

                                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                                        <div>
                                            <label style={{ fontWeight: 'bold', display: 'block', marginBottom: '0.5rem' }}>Карта</label>
                                            <input className="admin-input" value={editForm.map_name} onChange={e => setEditForm({ ...editForm, map_name: e.target.value })} />
                                        </div>
                                        <div>
                                            <label style={{ fontWeight: 'bold', display: 'block', marginBottom: '0.5rem' }}>Дата (YYYY-MM-DD)</label>
                                            <input className="admin-input" value={editForm.file_date} onChange={e => setEditForm({ ...editForm, file_date: e.target.value })} />
                                        </div>
                                    </div>

                                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                                        <div>
                                            <label style={{ fontWeight: 'bold', display: 'block', marginBottom: '0.5rem' }}>Всего игроков</label>
                                            <input className="admin-input" type="number" value={editForm.total_players} onChange={e => setEditForm({ ...editForm, total_players: parseInt(e.target.value) })} />
                                        </div>
                                        <div>
                                            <label style={{ fontWeight: 'bold', display: 'block', marginBottom: '0.5rem' }}>Победа</label>
                                            <select className="admin-input" value={editForm.win_side} onChange={e => setEditForm({ ...editForm, win_side: e.target.value })}>
                                                <option value="WEST">WEST</option>
                                                <option value="EAST">EAST</option>
                                                <option value="GUER">GUER</option>
                                                <option value="UNKNOWN">UNKNOWN</option>
                                            </select>
                                        </div>
                                    </div>

                                    <div style={{ marginTop: '1rem' }}>
                                        <button className="admin-btn admin-btn-primary" onClick={handleEditSave} style={{ padding: '0.5rem 1.5rem' }}>Сохранить изменения миссии</button>
                                    </div>
                                </div>
                            )}

                            {/* Players Tab */}
                            {activeTab === 'players' && (
                                <div>
                                    <div style={{ marginBottom: '1rem', color: '#6c757d' }}>
                                        Здесь показаны только игроки этой миссии.
                                    </div>
                                    <AdminPlayersList missionId={editId} />
                                </div>
                            )}

                            {/* Squads Tab */}
                            {activeTab === 'squads' && (
                                <div>
                                    <div style={{ marginBottom: '1rem', color: '#6c757d' }}>
                                        Здесь показана статистика отрядов за эту миссию.
                                    </div>
                                    <AdminSquadStatsList missionId={editId} />
                                </div>
                            )}

                        </div>

                        {/* Footer */}
                        <div style={{ padding: '1rem 2rem', borderTop: '1px solid #dee2e6', display: 'flex', justifyContent: 'flex-end' }}>
                            <button className="admin-btn" onClick={() => setEditId(null)}>Закрыть окно</button>
                        </div>
                    </div>
                </div>
            )}

            <div className="admin-table-container">
                <table className="admin-table">
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>Дата</th>
                            <th>Название</th>
                            <th>Карта</th>
                            <th>Игроки</th>
                            <th>Победа</th>
                            <th style={{ minWidth: '200px' }}>Действия</th>
                        </tr>
                    </thead>
                    <tbody>
                        {loading ? <tr><td colSpan={7}>Загрузка...</td></tr> : missions.map(m => (
                            <tr key={m.id}>
                                <td>{m.id}</td>
                                <td>{m.file_date}</td>
                                <td>{m.mission_name}</td>
                                <td>{m.map_name}</td>
                                <td>{m.total_players}</td>
                                <td>{m.win_side}</td>
                                <td>
                                    <button
                                        onClick={() => handleEditClick(m)}
                                        className="admin-btn"
                                        style={{ padding: '0.2rem 0.5rem', fontSize: '0.8rem', marginRight: '5px', borderColor: '#007bff', color: '#007bff' }}
                                    >
                                        Ред. / Открыть
                                    </button>
                                    <button
                                        onClick={() => handleDelete(m.id)}
                                        className="admin-btn admin-btn-danger"
                                        style={{ padding: '0.2rem 0.5rem', fontSize: '0.8rem' }}
                                    >
                                        Удалить
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

export default AdminMissions;
