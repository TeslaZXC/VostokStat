import React, { useState, useEffect, useRef } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { searchPlayer } from '../api';
import './NavBar.css';

export const NavBar: React.FC = () => {
    const navigate = useNavigate();
    const [query, setQuery] = useState('');
    const [suggestions, setSuggestions] = useState<string[]>([]);
    const [loading, setLoading] = useState(false);
    const [showSuggestions, setShowSuggestions] = useState(false);
    const wrapperRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        const fetchSuggestions = async () => {
            if (query.length < 2) {
                setSuggestions([]);
                return;
            }

            setLoading(true);
            setShowSuggestions(true); // Show immediately to show loading state
            try {
                const results = await searchPlayer(query);
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

    const handleSelectPlayer = (name: string) => {
        navigate(`/players/${name}`);
        setQuery('');
        setShowSuggestions(false);
    };

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
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
            </div>

            <div className="nav-search-container" ref={wrapperRef}>
                <form className="nav-search" onSubmit={handleSubmit}>
                    <input
                        type="text"
                        placeholder="ПОИСК БОЙЦА..."
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                        onFocus={() => query.length >= 2 && setShowSuggestions(true)}
                    />
                    {/* Loading is now handled inside suggestions */}
                </form>
                {showSuggestions && (suggestions.length > 0 || loading) && (
                    <div className="nav-suggestions">
                        {loading && (
                            <div className="nav-suggestion-item disabled" style={{ color: '#888', cursor: 'default' }}>
                                Загрузка...
                            </div>
                        )}
                        {!loading && suggestions.map((name, index) => (
                            <div
                                key={index}
                                className="nav-suggestion-item"
                                onClick={() => handleSelectPlayer(name)}
                            >
                                {name}
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </nav>
    );
};
