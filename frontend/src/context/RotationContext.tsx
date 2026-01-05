import React, { createContext, useState, useContext, useEffect } from 'react';
import type { ReactNode } from 'react';
import { getRotations } from '../api';
import type { Rotation } from '../api';

interface RotationContextType {
    currentRotationId: number | null; // null = All Time
    rotations: Rotation[];
    setRotation: (id: number | null) => void;
    loading: boolean;
}

const RotationContext = createContext<RotationContextType | undefined>(undefined);

export const RotationProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
    const [currentRotationId, setCurrentRotationId] = useState<number | null>(null);
    const [rotations, setRotations] = useState<Rotation[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        // Load rotations once on mount
        getRotations()
            .then(data => {
                setRotations(data);
                // Check local storage or default active?
                const stored = localStorage.getItem('vostok_rotation');
                if (stored) {
                    setCurrentRotationId(Number(stored));
                } else {
                    // Start with active one if exists? Or null?
                    const active = data.find((r: Rotation) => r.is_active);
                    if (active) setCurrentRotationId(active.id);
                }
            })
            .catch(err => console.error(err))
            .finally(() => setLoading(false));
    }, []);

    const setRotation = (id: number | null) => {
        setCurrentRotationId(id);
        if (id) localStorage.setItem('vostok_rotation', String(id));
        else localStorage.removeItem('vostok_rotation');
    };

    return (
        <RotationContext.Provider value={{ currentRotationId, rotations, setRotation, loading }}>
            {children}
        </RotationContext.Provider>
    );
};

export const useRotation = () => {
    const context = useContext(RotationContext);
    if (!context) throw new Error("useRotation must be used within RotationProvider");
    return context;
};
