import React, { useState, useEffect, useRef } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { searchGeneral } from '../api';
import type { SearchResult } from '../api';
import './NavBar.css';

export const NavBar: React.FC = () => {
    const navigate = useNavigate();
    const [query, setQuery] = useState('');
    const [suggestions, setSuggestions] = useState<SearchResult[]>([]);
    const [loading, setLoading] = useState(false);
    const [showSuggestions, setShowSuggestions] = useState(false);
    const wrapperRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        const fetchSuggestions = async () => {
            if (!query) {
                setSuggestions([]);
                return;
            }

            setLoading(true);
            setShowSuggestions(true); // Show immediately to show loading state
            try {
                const results = await searchGeneral(query);
                setSuggestions(results);
            } catch (console) {
                // Silent fail
            } finally {
                setLoading(false);
            }
        };

        const timeoutId = setTimeout(fetchSuggestions, 500);
        return () => clearTimeout(timeoutId);
    }, [query]);

    // Close suggestions when clicking outside
    useEffect(() => {
        const handleClickOutside = (event: MouseEvent) => {
            if (wrapperRef.current && !wrapperRef.current.contains(event.target as Node)) {
                setShowSuggestions(false);
            }
        };

        document.addEventListener('mousedown', handleClickOutside);
        return () => {
            document.removeEventListener('mousedown', handleClickOutside);
        };
    }, [wrapperRef]);

    const handleSelectResult = (result: SearchResult) => {
        if (result.type === 'squad') {
            navigate(`/squads/${result.name}`);
        } else {
            navigate(`/players/${result.name}`);
        }
        setQuery('');
        setShowSuggestions(false);
    };

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        // If Enter is pressed, default to searching player for now, or maybe the first suggestion?
        // Let's stick to player search default for legacy behavior if no suggestion selected,
        // OR if query matches a known squad format, try squad.
        // Better yet: navigate to a generic search page? We don't have one.
        // Fallback: /players/ is the generic catch-all route that shows 404 if not found.
        if (query.trim()) {
            navigate(`/players/${encodeURIComponent(query.trim())}`);
            setQuery('');
            setShowSuggestions(false);
        }
    };

    return (
        <nav className="main-navbar">
            <div className="nav-links">
                <NavLink to="/" className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>ГЛАВНАЯ</NavLink>
                <NavLink to="/missions" className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>ОПЕРАЦИИ</NavLink>
                <NavLink to="/squads" className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>ТОП ОТРЯДОВ</NavLink>
                <NavLink to="/players" className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>ТОП БОЙЦОВ</NavLink>
                <NavLink to="/total-stats" className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>СТАТИСТИКА СТОРОН</NavLink>
            </div>

            <div className="nav-search-container" ref={wrapperRef}>
                <form className="nav-search" onSubmit={handleSubmit}>
                    <input
                        type="text"
                        placeholder="ПОИСК (Игрок / Отряд)..."
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                        onFocus={() => query.length >= 1 && setShowSuggestions(true)}
                    />
                </form>
                {showSuggestions && (suggestions.length > 0 || loading) && (
                    <div className="nav-suggestions">
                        {loading && (
                            <div className="nav-suggestion-item disabled" style={{ color: '#888', cursor: 'default' }}>
                                Загрузка...
                            </div>
                        )}
                        {!loading && suggestions.map((item, index) => (
                            <div
                                key={index}
                                className="nav-suggestion-item"
                                onClick={() => handleSelectResult(item)}
                            >
                                <span style={{ marginRight: '8px', opacity: 0.7 }}>
                                    {item.type === 'squad' ? '🛡️' : '👤'}
                                </span>
                                {item.label}
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </nav>
    );
};
