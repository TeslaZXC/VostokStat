import React from 'react';

export const Home: React.FC = () => {
    return (
        <div className="home-dashboard">
            <h2>Добро пожаловать</h2>
            <p>
                Данная статистика была сделана Артурко для игрового проекта "Восток" арма3, все пресдавтленые веещи имеют лишь игровой характер. Нкоторые названия совпадения и не имеют не чего общего с реальностью.
            </p>

            <style>{`
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
            `}</style>
        </div>
    );
};
