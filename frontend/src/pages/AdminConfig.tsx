import React, { useState, useEffect } from 'react';
import { getAdminConfig, updateAdminConfig, deleteAdminConfig } from '../api';

interface ConfigItem {
    key: string;
    value: string;
}

const AdminConfig: React.FC = () => {
    const [configs, setConfigs] = useState<ConfigItem[]>([]);
    const [key, setKey] = useState('');
    const [val, setVal] = useState('');

    const load = async () => {
        try {
            const data = await getAdminConfig();
            setConfigs(data);
        } catch (e) { console.error(e); }
    };

    useEffect(() => { load(); }, []);

    const handleSave = async () => {
        if (!key) return;
        try {
            await updateAdminConfig(key, val);
            setKey(''); setVal('');
            load();
        } catch (e) { alert("Ошибка сохранения"); }
    };

    const handleDelete = async (k: string) => {
        if (!confirm(`Удалить настройку ${k}?`)) return;
        try {
            await deleteAdminConfig(k);
            load();
        } catch (e) { alert("Ошибка удаления"); }
    };

    return (
        <div>
            <h1 className="admin-title">Конфигурация приложения</h1>
            <div className="admin-card" style={{ display: 'flex', gap: '10px' }}>
                <input placeholder="Ключ (Key)" className="admin-input" value={key} onChange={e => setKey(e.target.value)} />
                <input placeholder="Значение (Value)" className="admin-input" value={val} onChange={e => setVal(e.target.value)} />
                <button className="admin-btn admin-btn-primary" onClick={handleSave}>Сохранить</button>
            </div>

            <div className="admin-table-container">
                <table className="admin-table">
                    <thead><tr><th>Ключ</th><th>Значение</th><th>Действие</th></tr></thead>
                    <tbody>
                        {configs.map(c => (
                            <tr key={c.key}>
                                <td>{c.key}</td>
                                <td>{c.value}</td>
                                <td>
                                    <button onClick={() => handleDelete(c.key)} className="admin-btn admin-btn-danger" style={{ padding: '0.2rem 0.5rem', fontSize: '0.8rem' }}>
                                        Удалить
                                    </button>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
};

export default AdminConfig;
