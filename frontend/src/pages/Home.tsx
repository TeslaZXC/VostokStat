import React from 'react';

export const Home: React.FC = () => {
    return (
        <div className="home-dashboard">
            <h2>Добро пожаловать</h2>
            <p>
                Статистика от Артурки для проекта «Восток» (Arma 3). Всё — чисто игровой контент. Совпадения с реальностью случайны и не имеют значения.
            </p>

            <style>{`
                .home-dashboard {
                    display: flex;
                    flex-direction: column;
                    min-height: 60vh; /* Ensure container has height */
                }

                .home-dashboard h2 {
                    color: var(--color-text-muted);
                    text-transform: uppercase;
                    margin-bottom: 1rem;
                }
                .home-dashboard p {
                    margin-bottom: 2rem;
                    line-height: 1.6;
                    max-width: 800px;
                    color: rgba(255, 255, 255, 0.8);
                }

                .social-footer {
                    margin-top: auto; /* Push to bottom */
                    padding-top: 2rem;
                    border-top: 1px solid rgba(255, 255, 255, 0.1);
                    display: flex;
                    gap: 2rem;
                    justify-content: flex-start;
                    align-items: center;
                }

                .social-link {
                    display: flex;
                    align-items: center;
                    gap: 0.8rem;
                    color: var(--color-text-muted);
                    text-decoration: none;
                    transition: all 0.3s ease;
                    padding: 0.5rem 1rem;
                    border-radius: 8px;
                    background: rgba(255, 255, 255, 0.03);
                }

                .social-link:hover {
                    background: var(--color-accent);
                    color: #fff;
                    transform: translateY(-2px);
                    box-shadow: 0 4px 12px rgba(255, 68, 68, 0.2);
                }

                .social-icon-wrapper {
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    width: 24px;
                    height: 24px;
                }

                .social-link svg {
                    width: 100%;
                    height: 100%;
                    fill: currentColor;
                }
                
                .social-label {
                    font-size: 0.9rem;
                    font-weight: 500;
                }
            `}</style>

            <footer className="social-footer">
                <a href="https://github.com/TeslaZXC" target="_blank" rel="noopener noreferrer" className="social-link">
                    <div className="social-icon-wrapper">
                        <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                            <path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-1.125-3.795-1.125-.54-1.38-1.32-1.755-1.32-1.755-1.095-.75.075-.735.075-.735 1.2.075 1.83 1.23 1.83 1.23 1.08 1.815 2.805 1.29 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405 1.02 0 2.04.135 3 .405 2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.285 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z" />
                        </svg>
                    </div>
                    <span className="social-label">GitHub разработчика</span>
                </a>
                <a href="https://t.me/RR_Artyrka" target="_blank" rel="noopener noreferrer" className="social-link">
                    <div className="social-icon-wrapper">
                        <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                            <path d="M12 0C5.37 0 0 5.376 0 12s5.37 12 12 12 12-5.376 12-12S18.63 0 12 0zm5.55 8.358l-2.015 9.537c-.15.68-.567.848-1.15.527l-3.18-2.355-1.536 1.48c-.168.17-.312.313-.637.313l.228-3.24 5.9-5.337c.257-.226-.057-.35-.397-.132l-7.29 4.59-3.14-.98c-.682-.213-.695-.683.14-1.01l12.28-4.735c.57-.205 1.07.126.897 1.332z" />
                        </svg>
                    </div>
                    <span className="social-label">Telegram разработчика</span>
                </a>
                <a href="https://discord.gg/GS6CeTv5SQ" target="_blank" rel="noopener noreferrer" className="social-link">
                    <div className="social-icon-wrapper">
                        <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                            <path d="M20.317 4.37a19.791 19.791 0 00-4.885-1.515.074.074 0 00-.079.037c-.21.375-.444.864-.608 1.25a18.27 18.27 0 00-5.487 0 12.64 12.64 0 00-.617-1.25.077.077 0 00-.079-.037A19.736 19.736 0 003.677 4.37a.07.07 0 00-.032.027C.533 9.046-.32 13.58.099 18.057a.082.082 0 00.031.057 19.9 19.9 0 005.993 3.03.078.078 0 00.084-.028c.462-.63.874-1.295 1.226-1.994a.076.076 0 00-.041-.106 13.107 13.107 0 01-1.872-.892.077.077 0 01-.008-.128 10.2 10.2 0 00.372-.292.074.074 0 01.077-.01c3.928 1.793 8.18 1.793 12.062 0a.074.074 0 01.078.01c.12.098.246.198.373.292a.077.077 0 01-.006.127 12.299 12.299 0 01-1.873.892.077.077 0 00-.041.107c.36.698.772 1.362 1.225 1.993a.076.076 0 00.084.028 19.839 19.839 0 006.002-3.03.077.077 0 00.032-.054c.5-5.177-2.313-9.133-4.816-12.424a.076.076 0 00-.038-.027zM8.02 15.33c-1.183 0-2.157-1.085-2.157-2.419 0-1.333.956-2.419 2.157-2.419 1.21 0 2.176 1.085 2.156 2.419 0 1.334-.956 2.419-2.156 2.419zm7.975 0c-1.183 0-2.157-1.085-2.157-2.419 0-1.333.955-2.419 2.157-2.419 1.21 0 2.176 1.085 2.157 2.419 0 1.334-.946 2.419-2.157 2.419z" />
                        </svg>
                    </div>
                    <span className="social-label">Discord проекта vostok</span>
                </a>
            </footer>
        </div>
    );
};
