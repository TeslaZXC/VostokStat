import React, { useState, useEffect } from 'react';
import {
    getRotations, createRotation, updateRotation, deleteRotation, getAdminSquads
} from '../api';
import type { Rotation } from '../api';
import '../admin.css';

const AdminRotations: React.FC = () => {
    const [rotations, setRotations] = useState<Rotation[]>([]);
    const [loading, setLoading] = useState(false);

    // Modal State
    const [showModal, setShowModal] = useState(false);
    const [editingRot, setEditingRot] = useState<Rotation | null>(null); // If null, creating new

    // Form State
    const [name, setName] = useState('');
    const [startDate, setStartDate] = useState('');
    const [endDate, setEndDate] = useState('');
    const [isActive, setIsActive] = useState(false);
    const [selectedSquadIds, setSelectedSquadIds] = useState<Set<number>>(new Set());

    // Available Squads for selection
    const [allSquads, setAllSquads] = useState<{ id: number, name: string }[]>([]);

    useEffect(() => {
        loadRotations();
        loadAllSquads();
    }, []);

    const loadRotations = async () => {
        setLoading(true);
        try {
            const data = await getRotations();
            setRotations(data);
        } catch (err) {
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    const loadAllSquads = async () => {
        try {
            // Fetch a large number of squads to populate the selector
            // Ideally should be a dedicated 'all-squads-list' endpoint but utilizing existing one
            const res = await getAdminSquads(0, 1000);
            setAllSquads(res.items.map((s: any) => ({ id: s.id, name: s.name })));
        } catch (err) {
            console.error("Failed to load squads for selector", err);
        }
    };

    const handleEdit = (rot: Rotation) => {
        setEditingRot(rot);
        setName(rot.name);
        setStartDate(rot.start_date);
        setEndDate(rot.end_date);
        setIsActive(rot.is_active);
        setSelectedSquadIds(new Set(rot.squad_ids));
        setShowModal(true);
    };

    const handleCreate = () => {
        setEditingRot(null);
        setName('');
        setStartDate('');
        setEndDate('');
        setIsActive(false);
        setSelectedSquadIds(new Set());
        setShowModal(true);
    };

    const handleDelete = async (id: number) => {
        if (!confirm("Are you sure you want to delete this rotation?")) return;
        try {
            await deleteRotation(id);
            loadRotations();
        } catch (err) {
            alert("Failed to delete");
        }
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            const payload = {
                name,
                start_date: startDate,
                end_date: endDate,
                is_active: isActive,
                squad_ids: Array.from(selectedSquadIds)
            };

            if (editingRot) {
                await updateRotation(editingRot.id, payload);
            } else {
                await createRotation(payload);
            }
            setShowModal(false);
            loadRotations();
        } catch (err: any) {
            console.error(err);
            alert(`Failed to save: ${err.message}`);
        }
    };

    const toggleSquad = (id: number) => {
        const newSet = new Set(selectedSquadIds);
        if (newSet.has(id)) newSet.delete(id);
        else newSet.add(id);
        setSelectedSquadIds(newSet);
    };

    return (
        <div className="admin-section">
            <div className="admin-header">
                <h2>Rotations (Seasons)</h2>
                <button className="admin-btn primary" onClick={handleCreate}>+ New Rotation</button>
            </div>

            {loading ? <p>Loading...</p> : (
                <table className="admin-table">
                    <thead>
                        <tr>
                            <th>Name</th>
                            <th>Dates</th>
                            <th>Squads</th>
                            <th>Active?</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        {rotations.map(r => (
                            <tr key={r.id}>
                                <td>{r.name}</td>
                                <td>{r.start_date} &rarr; {r.end_date}</td>
                                <td>{r.squad_count}</td>
                                <td>{r.is_active ? '✅' : ''}</td>
                                <td>
                                    <button onClick={() => handleEdit(r)}>Edit</button>
                                    <button className="danger" onClick={() => handleDelete(r.id)}>Delete</button>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            )}

            {showModal && (
                <div className="modal-overlay">
                    <div className="modal-content large-modal">
                        <h3>{editingRot ? 'Edit Rotation' : 'New Rotation'}</h3>
                        <form onSubmit={handleSubmit}>
                            <div className="form-group">
                                <label>Name:</label>
                                <input value={name} onChange={e => setName(e.target.value)} required />
                            </div>
                            <div className="form-row">
                                <div className="form-group">
                                    <label>Start Date (YYYY-MM-DD):</label>
                                    <input type="date" value={startDate} onChange={e => setStartDate(e.target.value)} required />
                                </div>
                                <div className="form-group">
                                    <label>End Date (YYYY-MM-DD):</label>
                                    <input type="date" value={endDate} onChange={e => setEndDate(e.target.value)} required />
                                </div>
                            </div>
                            <div className="form-group">
                                <label>
                                    <input type="checkbox" checked={isActive} onChange={e => setIsActive(e.target.checked)} />
                                    Is Active Default?
                                </label>
                            </div>

                            <div className="form-group">
                                <label>Whitelisted Squads ({selectedSquadIds.size} selected):</label>
                                <div className="squad-selector-list" style={{ maxHeight: '300px', overflowY: 'auto', border: '1px solid #444', padding: '10px' }}>
                                    {allSquads.map(sq => (
                                        <div key={sq.id} style={{ marginBottom: '5px' }}>
                                            <label style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                                                <input
                                                    type="checkbox"
                                                    checked={selectedSquadIds.has(sq.id)}
                                                    onChange={() => toggleSquad(sq.id)}
                                                />
                                                {sq.name}
                                            </label>
                                        </div>
                                    ))}
                                </div>
                            </div>

                            <div className="modal-actions">
                                <button type="button" onClick={() => setShowModal(false)}>Cancel</button>
                                <button type="submit" className="primary">Save</button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
};

export default AdminRotations;
