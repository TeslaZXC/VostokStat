import React from 'react';
import { NavBar } from './NavBar';
import './Layout.css';

interface LayoutProps {
    children: React.ReactNode;
}

export const Layout: React.FC<LayoutProps> = ({ children }) => {
    return (
        <div className="layout-container">
            <header className="main-header">
                <h1>Vostok<span className="highlight">Stat</span></h1>
            </header>
            <main className="content-area">
                <div className="glass-panel">
                    <NavBar />
                    <div className="page-content">
                        {children}
                    </div>
                </div>
            </main>
        </div>
    );
};
