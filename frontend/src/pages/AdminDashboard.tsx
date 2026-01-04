import React, { useState, useEffect } from 'react';
import { getAdminSquads, addAdminSquad, deleteAdminSquad, checkAdminAuth } from '../api';
import { useNavigate } from 'react-router-dom';
import { AdminPagination } from '../components/AdminPagination';

interface AdminSquad {
    name: string;
    tags: string[];
}

const AdminDashboard: React.FC = () => {
    const [squads, setSquads] = useState<AdminSquad[]>([]);
    const [newName, setNewName] = useState('');
    const [newTags, setNewTags] = useState('');
    const [loading, setLoading] = useState(true);

    // Pagination State
    const [total, setTotal] = useState(0);
    const [skip, setSkip] = useState(0);
    const [limit, setLimit] = useState(10);
    const [search, setSearch] = useState('');

    const navigate = useNavigate();

    const load = async () => {
        setLoading(true);
        try {
            try { await checkAdminAuth(); } catch { navigate('/admin/login'); return; }
            const data = await getAdminSquads(skip, limit, search);
            setSquads(data.items);
            setTotal(data.total);
        } catch (err) { console.error(err); }
        finally { setLoading(false); }
    };

    useEffect(() => {
        load();
    }, [navigate, skip, limit, search]);

    const handleLimitChange = (newLimit: number) => {
        setLimit(newLimit);
        setSkip(0); // Reset to first page
    };

    const handleAdd = async () => {
        if (!newName) return;
        const tagsArray = newTags.split(',').map(s => s.trim()).filter(Boolean);
        try {
            await addAdminSquad(newName, tagsArray);
            setNewName(''); setNewTags('');
            load(); // Reload current page
        } catch (err) { alert("Ошибка при добавлении отряда"); }
    };

    const handleDelete = async (name: string) => {
        if (!confirm(`Удалить отряд ${name}?`)) return;
        try {
            await deleteAdminSquad(name);
            load();
        } catch (err) { alert("Ошибка при удалении отряда"); }
    };

    const handleEditPopulate = (s: AdminSquad) => {
        setNewName(s.name);
        setNewTags(s.tags.join(', '));
        window.scrollTo({ top: 0, behavior: 'smooth' });
    };

    return (
        <div>
            <h1 className="admin-title">Управление отрядами</h1>

            <div className="admin-card">
                <h3>Добавить / Изменить Отряд</h3>
                <div style={{ display: 'flex', gap: '10px', marginTop: '10px', flexWrap: 'wrap' }}>
                    <input
                        placeholder="Название (например, 75th Ranger)"
                        value={newName}
                        onChange={e => setNewName(e.target.value)}
                        className="admin-input"
                        style={{ flex: 1 }}
                    />
                    <input
                        placeholder="Теги (через запятую, например: 75, [75])"
                        value={newTags}
                        onChange={e => setNewTags(e.target.value)}
                        className="admin-input"
                        style={{ flex: 2 }}
                    />
                    <button onClick={handleAdd} className="admin-btn admin-btn-primary">Сохранить</button>
                    {(newName || newTags) && (
                        <button onClick={() => { setNewName(''); setNewTags(''); }} className="admin-btn">Очистить</button>
                    )}
                </div>
                <small className="text-muted" style={{ display: 'block', marginTop: '5px' }}>
                    * Добавление существующего имени обновит его теги.
                </small>
            </div>

            <div className="admin-card">
                <input
                    placeholder="Поиск отряда..."
                    className="admin-input"
                    value={search}
                    onChange={e => { setSearch(e.target.value); setSkip(0); }}
                    style={{ maxWidth: '400px' }}
                />
            </div>

            <div className="admin-table-container">
                <table className="admin-table">
                    <thead>
                        <tr>
                            <th>Название</th>
                            <th>Теги</th>
                            <th style={{ width: '150px' }}>Действия</th>
                        </tr>
                    </thead>
                    <tbody>
                        {loading ? <tr><td colSpan={3}>Загрузка...</td></tr> : squads.map(s => (
                            <tr key={s.name}>
                                <td>{s.name}</td>
                                <td>
                                    {s.tags.map(t => (
                                        <span key={t} style={{
                                            display: 'inline-block',
                                            background: '#e9ecef',
                                            padding: '2px 6px',
                                            borderRadius: '4px',
                                            marginRight: '4px',
                                            fontSize: '0.85rem'
                                        }}>
                                            {t}
                                        </span>
                                    ))}
                                </td>
                                <td>
                                    <button
                                        onClick={() => handleEditPopulate(s)}
                                        className="admin-btn"
                                        style={{ padding: '0.2rem 0.5rem', fontSize: '0.8rem', marginRight: '5px', borderColor: '#007bff', color: '#007bff' }}
                                    >
                                        Изм.
                                    </button>
                                    <button
                                        onClick={() => handleDelete(s.name)}
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

export default AdminDashboard;
