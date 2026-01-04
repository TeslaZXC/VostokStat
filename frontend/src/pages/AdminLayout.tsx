import React, { useEffect } from 'react';
import { Link, Outlet, useNavigate, useLocation } from 'react-router-dom';
import { adminLogout } from '../api';
import '../admin.css'; // Import the new styles

export const AdminLayout: React.FC = () => {
    const navigate = useNavigate();
    const location = useLocation();

    // Toggle body class for isolation
    useEffect(() => {
        document.body.classList.add('admin-mode');
        const root = document.getElementById('root');
        if (root) root.classList.add('admin-root');

        return () => {
            document.body.classList.remove('admin-mode');
            if (root) root.classList.remove('admin-root');
        };
    }, []);

    const handleLogout = async () => {
        await adminLogout();
        navigate('/admin/login');
    };

    const isActive = (path: string) => location.pathname === path;

    return (
        <div className="admin-layout">
            {/* Sidebar */}
            <div className="admin-sidebar">
                <div className="admin-header">
                    Vostok Admin
                </div>

                <nav className="admin-nav">
                    <Link to="/admin" className={`admin-nav-link ${isActive("/admin") ? 'active' : ''}`}>Отрады (Squads)</Link>
                    <Link to="/admin/missions" className={`admin-nav-link ${isActive("/admin/missions") ? 'active' : ''}`}>Миссии</Link>
                    <Link to="/admin/mission-squad-stats" className={`admin-nav-link ${isActive("/admin/mission-squad-stats") ? 'active' : ''}`}>Статистика (Ms)</Link>
                    <Link to="/admin/players" className={`admin-nav-link ${isActive("/admin/players") ? 'active' : ''}`}>Игроки</Link>
                    <Link to="/admin/config" className={`admin-nav-link ${isActive("/admin/config") ? 'active' : ''}`}>Конфиг</Link>
                    <Link to="/admin/tools" className={`admin-nav-link ${isActive("/admin/tools") ? 'active' : ''}`}>Инструменты</Link>
                    <Link to="/admin/users" className={`admin-nav-link ${isActive("/admin/users") ? 'active' : ''}`}>Админы</Link>
                </nav>

                <div style={{ marginTop: 'auto', padding: '1rem' }}>
                    <Link to="/" className="admin-nav-link" style={{ color: '#888', marginBottom: '10px' }}>â†  На сайт</Link>
                    <button
                        onClick={handleLogout}
                        className="admin-btn admin-btn-danger"
                        style={{ width: '100%' }}>
                        Выйти
                    </button>
                </div>
            </div>

            {/* Main Content */}
            <div className="admin-content">
                <Outlet />
            </div>
        </div>
    );
};
