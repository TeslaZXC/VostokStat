import React, { useState, useEffect } from 'react';
import { getAdminUsers, createAdminUser, deleteAdminUser, updateAdminUser } from '../api';

interface AdminUser {
    id: number;
    username: string;
}

const AdminUsers: React.FC = () => {
    const [users, setUsers] = useState<AdminUser[]>([]);
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');

    const load = async () => {
        try {
            const data = await getAdminUsers();
            setUsers(data);
        } catch (e) { console.error(e); }
    };

    useEffect(() => { load(); }, []);

    const handleCreate = async () => {
        if (!username || !password) return;
        try {
            await createAdminUser(username, password);
            setUsername(''); setPassword('');
            load();
        } catch (e) { alert("Ошибка создания пользователя (возможно уже существует)"); }
    };

    const handleDelete = async (id: number) => {
        if (!confirm("Удалить пользователя?")) return;
        try {
            await deleteAdminUser(id);
            load();
        } catch (e: any) { alert("Ошибка удаления: " + e.message); }
    };

    const handleChangePass = async (id: number) => {
        const newPass = prompt("Введите новый пароль:");
        if (!newPass) return;
        try {
            await updateAdminUser(id, newPass);
            alert("Пароль обновлен");
        } catch (e) { alert("Ошибка обновления пароля"); }
    };

    return (
        <div>
            <h1 className="admin-title">Управление Администраторами</h1>
            <div className="admin-card" style={{ display: 'flex', gap: '10px' }}>
                <input placeholder="Имя пользователя" className="admin-input" value={username} onChange={e => setUsername(e.target.value)} />
                <input placeholder="Пароль" type="password" className="admin-input" value={password} onChange={e => setPassword(e.target.value)} />
                <button className="admin-btn admin-btn-primary" onClick={handleCreate}>Создать</button>
            </div>

            <div className="admin-table-container">
                <table className="admin-table">
                    <thead><tr><th>ID</th><th>Имя пользователя</th><th>Действие</th></tr></thead>
                    <tbody>
                        {users.map(u => (
                            <tr key={u.id}>
                                <td>{u.id}</td>
                                <td>{u.username}</td>
                                <td>
                                    <button onClick={() => handleChangePass(u.id)} className="admin-btn" style={{ marginRight: '10px', color: '#6c757d', border: '1px solid #ced4da' }}>Пароль</button>
                                    <button onClick={() => handleDelete(u.id)} className="admin-btn admin-btn-danger">Удалить</button>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
};

export default AdminUsers;
