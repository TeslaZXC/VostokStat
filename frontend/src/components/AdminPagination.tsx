import React from 'react';

interface Props {
    total: number;
    limit: number;
    skip: number;
    onPageChange: (newSkip: number) => void;
    onLimitChange?: (newLimit: number) => void;
}

export const AdminPagination: React.FC<Props> = ({ total, limit, skip, onPageChange, onLimitChange }) => {
    const currentPage = Math.floor(skip / limit) + 1;
    const totalPages = Math.ceil(total / limit);

    if (total === 0) return null;

    const handlePrev = () => {
        if (currentPage > 1) {
            onPageChange(skip - limit);
        }
    };

    const handleNext = () => {
        if (currentPage < totalPages) {
            onPageChange(skip + limit);
        }
    };

    const handleLimitChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
        if (onLimitChange) {
            onLimitChange(Number(e.target.value));
        }
    };

    return (
        <div style={{ display: 'flex', alignItems: 'center', gap: '15px', marginTop: '1rem', justifyContent: 'flex-end', flexWrap: 'wrap' }}>
            {onLimitChange && (
                <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
                    <span style={{ fontSize: '0.9rem', color: '#6c757d' }}>Показывать по:</span>
                    <select
                        value={limit}
                        onChange={handleLimitChange}
                        className="admin-input"
                        style={{ width: 'auto', padding: '0.2rem 0.5rem', height: 'auto' }}
                    >
                        <option value="5">5</option>
                        <option value="10">10</option>
                        <option value="25">25</option>
                        <option value="50">50</option>
                        <option value="100">100</option>
                    </select>
                </div>
            )}

            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <button
                    className="admin-btn"
                    onClick={handlePrev}
                    disabled={currentPage === 1}
                    style={{ opacity: currentPage === 1 ? 0.5 : 1 }}
                >
                    &laquo; Назад
                </button>
                <span style={{ fontSize: '0.9rem', color: '#6c757d' }}>
                    Страница {currentPage} из {totalPages || 1} (Всего: {total})
                </span>
                <button
                    className="admin-btn"
                    onClick={handleNext}
                    disabled={currentPage >= totalPages}
                    style={{ opacity: currentPage >= totalPages ? 0.5 : 1 }}
                >
                    Вперед &raquo;
                </button>
            </div>
        </div>
    );
};
