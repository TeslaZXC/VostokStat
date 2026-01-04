import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { fetchTotalSquadStats } from '../api';
import type { TotalSquadsResponse, SquadStats } from '../api';
import '../components/MissionDetail.css';
import {
    LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts';

const TotalStats: React.FC = () => {
    const [data, setData] = useState<TotalSquadsResponse | null>(null);
    const [loading, setLoading] = useState<boolean>(true);
    const [error, setError] = useState<string | null>(null);
    const navigate = useNavigate();

    useEffect(() => {
        const loadData = async () => {
            try {
                const result = await fetchTotalSquadStats();
                setData(result);
            } catch (err) {
                setError('Не удалось загрузить данные.');
            } finally {
                setLoading(false);
            }
        };
        loadData();
    }, []);

    if (loading) return <div className="loading">Загрузка...</div>;
    if (error) return <div className="error">{error}</div>;

    // Calculate Summary Stats
    const calculateSummary = (squads: SquadStats[]) => {
        const frags = squads.reduce((acc, s) => acc + s.total_frags, 0);
        const deaths = squads.reduce((acc, s) => acc + s.total_deaths, 0);
        const kd = deaths > 0 ? (frags / deaths).toFixed(2) : frags.toFixed(2);
        return { frags, deaths, kd };
    };

    const westSummary = calculateSummary(data?.west || []);
    const eastSummary = calculateSummary(data?.east || []);

    const renderSummaryCard = (title: string, summary: { frags: number, deaths: number, kd: string }, sideClass: string) => (
        <div className={`summary-card ${sideClass}`}>
            <h3>{title}</h3>
            <div className="summary-stat">
                <span>Убийств:</span> <strong>{summary.frags}</strong>
            </div>
            <div className="summary-stat">
                <span>Смертей:</span> <strong>{summary.deaths}</strong>
            </div>
            <div className="summary-stat">
                <span>Ср. K/D:</span> <strong>{summary.kd}</strong>
            </div>
        </div>
    );

    const renderTable = (title: string, squads: SquadStats[], sideClass: string) => (
        <div className={`stats-column ${sideClass}`}>
            <h2 className={`side-title ${sideClass}`}>{title}</h2>
            <div className="player-table">
                <div className="table-header">
                    <span>Отряд</span>
                    <span>Миссии</span>
                    <span>Фраги</span>
                    <span>Смерти</span>
                    <span>K/D</span>
                </div>
                {squads.map((s, index) => (
                    <div
                        key={index}
                        className="table-row clickable-row"
                        onClick={() => navigate(`/squads/${encodeURIComponent(s.squad_name)}`)}
                    >
                        <span>{s.squad_name}</span>
                        <span>{s.total_missions}</span>
                        <span>{s.total_frags}</span>
                        <span>{s.total_deaths}</span>
                        <span>{s.kd_ratio.toFixed(2)}</span>
                    </div>
                ))}
                {squads.length === 0 && <div className="table-row"><span>Нет данных (Проверьте Admin Panel)</span></div>}
            </div>
        </div>
    );

    return (
        <div className="container fade-in">
            <h1 className="page-title">Статистика Сторон</h1>

            <div className="summary-container">
                {renderSummaryCard("Синие (WEST)", westSummary, "west-side-card")}
                {renderSummaryCard("Красные (EAST)", eastSummary, "east-side-card")}
            </div>

            {/* Chart Section */}
            {data?.history && data.history.length > 0 && (
                <div className="chart-container">
                    <h3>Динамика фрагов по миссиям</h3>
                    <ResponsiveContainer width="100%" height={300}>
                        <LineChart data={data.history}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#444" />
                            <XAxis dataKey="date" stroke="#888" />
                            <YAxis stroke="#888" />
                            <Tooltip
                                contentStyle={{ backgroundColor: '#1a1e1b', border: '1px solid #3c4238' }}
                                labelStyle={{ color: '#e0e0e0' }}
                            />
                            <Legend />
                            <Line type="monotone" dataKey="west_frags" name="WEST Фраги" stroke="#007bff" strokeWidth={2} dot={false} />
                            <Line type="monotone" dataKey="east_frags" name="EAST Фраги" stroke="#dc3545" strokeWidth={2} dot={false} />
                        </LineChart>
                    </ResponsiveContainer>
                </div>
            )}

            <div className="total-stats-container">
                {renderTable("WEST Отряды", data?.west || [], "west-side")}
                {renderTable("EAST Отряды", data?.east || [], "east-side")}
            </div>

            {(data?.other && data.other.length > 0) && (
                <div className="other-stats-container">
                    {renderTable("Другие", data.other, "other-side")}
                </div>
            )}

            <style>{`
                .total-stats-container {
                    display: flex;
                    gap: 2rem;
                    flex-wrap: wrap;
                    justify-content: center;
                    margin-top: 2rem;
                }
                .summary-container {
                     display: flex;
                     justify-content: center;
                     gap: 2rem;
                     margin-bottom: 2rem;
                }
                .summary-card {
                    background: rgba(0, 0, 0, 0.4);
                    padding: 1.5rem;
                    border-radius: 8px;
                    border: 1px solid #3c4238;
                    min-width: 200px;
                    text-align: center;
                }
                .west-side-card { border-top: 4px solid #007bff; }
                .east-side-card { border-top: 4px solid #dc3545; }
                
                .summary-stat {
                    display: flex;
                    justify-content: space-between;
                    margin: 0.5rem 0;
                    color: #ddd;
                }

                .chart-container {
                    background: rgba(0, 0, 0, 0.4);
                    padding: 1rem;
                    border-radius: 8px;
                    border: 1px solid #3c4238;
                    margin-bottom: 2rem;
                }

                .stats-column {
                    flex: 1;
                    min-width: 300px;
                    background: rgba(0, 0, 0, 0.4);
                    padding: 1rem;
                    border-radius: 8px;
                }
                .west-side { border-top: 4px solid #007bff; }
                .east-side { border-top: 4px solid #dc3545; }
                .other-side { border-top: 4px solid #6c757d; margin-top: 2rem; }
                
                .side-title {
                    text-align: center;
                    margin-bottom: 1rem;
                    font-size: 1.5rem;
                }
                .west-side .side-title { color: #007bff; }
                .east-side .side-title { color: #dc3545; }
            `}</style>
        </div>
    );
};

export default TotalStats;
