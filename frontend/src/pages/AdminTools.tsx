import React, { useState, useEffect } from 'react';
import { mergePlayers, getBackups, triggerBackup, getBackupDownloadUrl, getConfig, updateConfig } from '../api';
import type { BackupFile } from '../api';

const AdminTools: React.FC = () => {
    // Merge State
    const [source, setSource] = useState('');
    const [target, setTarget] = useState('');
    const [message, setMessage] = useState('');

    // Backup State
    const [backups, setBackups] = useState<BackupFile[]>([]);
    const [backupLoading, setBackupLoading] = useState(false);
    const [backupMessage, setBackupMessage] = useState('');

    // Telegram Config State
    const [tgToken, setTgToken] = useState('');
    const [tgChatId, setTgChatId] = useState('');

    const loadData = async () => {
        try {
            const b = await getBackups();
            setBackups(b);

            const configs = await getConfig();
            const token = configs.find((c: any) => c.key === 'TG_Bot_Token')?.value || '';
            const chat = configs.find((c: any) => c.key === 'TG_Backup_Chat_ID')?.value || '';
            setTgToken(token);
            setTgChatId(chat);
        } catch (e) { console.error(e); }
    };

    useEffect(() => { loadData(); }, []);

    const handleMerge = async () => {
        if (!source || !target) return;
        if (!confirm(`Перенести ВСЮ статистику от '${source}' К '${target}'? Это действие нельзя отменить.`)) return;
        try {
            const res = await mergePlayers(source, target);
            setMessage(res.message + (res.merged_count ? ` (Количество: ${res.merged_count})` : ''));
        } catch (e) { setMessage("Ошибка переноса статистики"); }
    };

    const handleTriggerBackup = async () => {
        setBackupLoading(true);
        try {
            await triggerBackup();
            setBackupMessage("Задача бэкапа запущена. Если настроен Telegram, файл скоро придет.");
            setTimeout(loadData, 2000); // Reload list
        } catch (e) { setBackupMessage("Ошибка запуска бэкапа"); }
        finally { setBackupLoading(false); }
    };

    const handleSaveConfig = async () => {
        try {
            await updateConfig('TG_Bot_Token', tgToken);
            await updateConfig('TG_Backup_Chat_ID', tgChatId);
            alert("Настройки Telegram сохранены");
        } catch (e) { alert("Ошибка сохранения"); }
    };

    const formatSize = (bytes: number) => {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    };

    return (
        <div>
            <h1 className="admin-title">Инструменты</h1>

            <div className="tools-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', gap: '2rem' }}>

                {/* Backup Card */}
                <div className="admin-card">
                    <h3>Telegram Бэкапы</h3>
                    <div style={{ marginBottom: '1.5rem', padding: '10px', background: 'rgba(0,0,0,0.2)', borderRadius: '4px' }}>
                        <h4>Настройки Telegram</h4>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', marginTop: '10px' }}>
                            <input
                                className="admin-input"
                                placeholder="Bot Token (от @BotFather)"
                                value={tgToken}
                                onChange={e => setTgToken(e.target.value)}
                            />
                            <input
                                className="admin-input"
                                placeholder="Chat ID (ваш ID)"
                                value={tgChatId}
                                onChange={e => setTgChatId(e.target.value)}
                            />
                            <button className="admin-btn" onClick={handleSaveConfig}>Сохранить Настройки</button>
                        </div>
                    </div>

                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                        <button
                            className="admin-btn admin-btn-primary"
                            onClick={handleTriggerBackup}
                            disabled={backupLoading}
                        >
                            {backupLoading ? 'Создание...' : 'Создать и отправить бэкап сейчас'}
                        </button>
                    </div>
                    {backupMessage && <div style={{ marginBottom: '10px', color: '#ffc107' }}>{backupMessage}</div>}

                    <div className="backup-list" style={{ maxHeight: '300px', overflowY: 'auto' }}>
                        <table className="admin-table" style={{ fontSize: '0.9rem' }}>
                            <thead><tr><th>Файл</th><th>Размер</th><th>Дата</th><th>Скачать</th></tr></thead>
                            <tbody>
                                {backups.map(b => (
                                    <tr key={b.name}>
                                        <td>{b.name}</td>
                                        <td>{formatSize(b.size)}</td>
                                        <td>{new Date(b.created * 1000).toLocaleString()}</td>
                                        <td>
                                            <a
                                                href={getBackupDownloadUrl(b.name)}
                                                className="admin-btn"
                                                style={{ padding: '2px 8px', fontSize: '0.8rem', textDecoration: 'none' }}
                                                download
                                            >
                                                â¬‡ï¸
                                            </a>
                                        </td>
                                    </tr>
                                ))}
                                {backups.length === 0 && <tr><td colSpan={4} style={{ textAlign: 'center' }}>Нет локальных бэкапов</td></tr>}
                            </tbody>
                        </table>
                    </div>
                </div>

                {/* Merge Card */}
                <div className="admin-card">
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
        </div>
    );
};

export default AdminTools;
