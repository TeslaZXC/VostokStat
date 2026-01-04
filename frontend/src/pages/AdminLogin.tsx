import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { adminLogin } from '../api';
import '../admin.css';

const AdminLogin: React.FC = () => {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState<string | null>(null);
    const navigate = useNavigate();

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            await adminLogin(username, password);
            navigate('/admin');
        } catch (err: any) {
            setError("Неверные учетные данные");
        }
    };

    // Using inline styles or verify if admin.css is loaded for this page.
    // If AdminLogin is outside AdminLayout, body class 'admin-mode' is NOT set automatically.
    // So we might want to manually set a clean style for this page or just use the box.

    return (
        <div style={{
            minHeight: '100vh',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            background: '#f4f6f9',
            fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif'
        }}>
            <div style={{
                width: '100%',
                maxWidth: '400px',
                padding: '2rem',
                background: '#fff',
                borderRadius: '0.25rem',
                boxShadow: '0 0 1px rgba(0,0,0,.125), 0 1px 3px rgba(0,0,0,.2)',
                borderTop: '3px solid #007bff'
            }}>
                <h2 style={{ marginBottom: '1.5rem', textAlign: 'center', color: '#212529' }}>Vostok Admin</h2>
                <form onSubmit={handleSubmit}>
                    <div style={{ marginBottom: '15px' }}>
                        <input
                            type="text"
                            value={username}
                            onChange={e => setUsername(e.target.value)}
                            placeholder="Имя пользователя"
                            className="admin-input"
                            style={{ width: '100%' }}
                        />
                    </div>
                    <div style={{ marginBottom: '20px' }}>
                        <input
                            type="password"
                            value={password}
                            onChange={e => setPassword(e.target.value)}
                            placeholder="Пароль"
                            className="admin-input"
                            style={{ width: '100%' }}
                        />
                    </div>
                    {error && <div style={{ color: '#dc3545', marginBottom: '15px', textAlign: 'center' }}>{error}</div>}
                    <button type="submit" className="admin-btn admin-btn-primary" style={{ width: '100%' }}>Войти</button>
                </form>
            </div>
        </div>
    );
};

export default AdminLogin;
