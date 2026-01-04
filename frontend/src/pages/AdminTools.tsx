import React, { useState } from 'react';
import { mergePlayers } from '../api';

const AdminTools: React.FC = () => {
    const [source, setSource] = useState('');
    const [target, setTarget] = useState('');
    const [message, setMessage] = useState('');

    const handleMerge = async () => {
        if (!source || !target) return;
        if (!confirm(`Перенести ВСЮ статистику от '${source}' К '${target}'? Это действие нельзя отменить.`)) return;

        try {
            const res = await mergePlayers(source, target);
            setMessage(res.message + (res.merged_count ? ` (Количество: ${res.merged_count})` : ''));
        } catch (e) {
            setMessage("Ошибка переноса статистики");
        }
    };

    return (
        <div>
            <h1 className="admin-title">Инструменты</h1>

            <div className="admin-card" style={{ maxWidth: '600px' }}>
                <h3>Объединение игроков (Merge Players)</h3>
                <p className="text-muted" style={{ marginBottom: '15px' }}>
                    Переносит всю статистику от <b>Исходного (Source)</b> игрока к <b>Целевому (Target)</b>. Полезно для исправления опечаток или смены ника.
                </p>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                    <input
                        placeholder="Исходный ник (например, Artyrka.old)"
                        className="admin-input"
                        value={source}
                        onChange={e => setSource(e.target.value)}
                    />
                    <div style={{ textAlign: 'center', fontSize: '1.2rem' }}>â¬‡ï¸ </div>
                    <input
                        placeholder="Целевой ник (например, Artyrka)"
                        className="admin-input"
                        value={target}
                        onChange={e => setTarget(e.target.value)}
                    />
                    <button className="admin-btn admin-btn-primary" onClick={handleMerge} style={{ marginTop: '10px' }}>Выполнить перенос</button>
                </div>
                {message && <div style={{ marginTop: '15px', padding: '10px', background: '#d4edda', color: '#155724', borderRadius: '4px', border: '1px solid #c3e6cb' }}>{message}</div>}
            </div>
        </div>
    );
};

export default AdminTools;
