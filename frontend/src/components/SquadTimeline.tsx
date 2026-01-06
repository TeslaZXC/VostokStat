import React from 'react';
import type { TimelineSegment } from '../api';

interface SquadTimelineProps {
    timeline: TimelineSegment[];
    onSelectSquad: (squad: string) => void;
    selectedSquad: string;
}

export const SquadTimeline: React.FC<SquadTimelineProps> = ({ timeline, onSelectSquad, selectedSquad }) => {
    // Total days to calculate proportional width - Not used currently as we use flex-grow
    // const totalDays = timeline.reduce((acc, s) => acc + s.days, 0);

    const segments = timeline || [];

    return (
        <div className="squad-timeline-wrapper">
            <h3 style={{ color: '#ccc', marginBottom: '0.5rem', marginTop: 0 }}>История Службы</h3>
            <div className="timeline-scroll-container">
                <div className="timeline-track">
                    {/* The Line */}
                    <div className="timeline-axis-line"></div>

                    {segments.map((seg, idx) => {
                        const isSelected = selectedSquad === seg.squad;

                        // Parse dates for display if they are strings
                        const startDate = new Date(seg.start_date.replace(' ', 'T'));
                        const endDate = new Date(seg.end_date.replace(' ', 'T'));

                        return (
                            <div
                                key={idx}
                                className={`timeline-block ${isSelected ? 'selected' : ''}`}
                                style={{
                                    flexGrow: seg.days,
                                    flexBasis: '100px', // Min width for readability
                                }}
                                onClick={() => onSelectSquad(seg.squad)}
                            >
                                {/* Top Label (Squad Name) */}
                                <div className="block-label-top">
                                    {seg.squad}
                                </div>

                                {/* The Bar Segment */}
                                <div
                                    className="block-bar"
                                    style={{ backgroundColor: stringToColor(seg.squad) }}
                                >
                                    {/* Days Label (Inside or hover) - User requested hover behavior */}
                                    <div className="hover-info">
                                        <div className="hover-days">{seg.days} дн.</div>
                                        <div className="hover-date">{startDate.toLocaleDateString('ru-RU')} - {endDate.toLocaleDateString('ru-RU')}</div>
                                    </div>
                                </div>

                                {/* Bottom Label (Date/Year? or hidden) */}
                                {/* <div className="block-label-bottom">
                                    {seg.startDate.getFullYear()}
                                </div> */}
                            </div>
                        );
                    })}
                </div>
            </div>

            <style>{`
                .squad-timeline-wrapper {
                    margin-bottom: 2rem;
                    background: rgba(18, 18, 18, 0.6);
                    border: 1px solid #333;
                    border-radius: 8px;
                    padding: 1rem;
                }
                .timeline-scroll-container {
                    overflow-x: auto;
                    overflow-y: hidden; /* Prevent vertical scrollbar jitter */
                    /* Reserve static space for top text and bottom tooltips */
                    padding-top: 40px; 
                    padding-bottom: 70px;
                }
                .timeline-scroll-container::-webkit-scrollbar {
                    height: 6px;
                }
                .timeline-scroll-container::-webkit-scrollbar-thumb {
                    background: #555;
                    border-radius: 3px;
                }
                
                .timeline-track {
                    display: flex;
                    position: relative;
                    min-width: 100%; /* Ensure it fills container */
                    width: max-content; /* Allow growing beyond container for scroll */
                    /* Removed internal padding as container handles it */
                    align-items: center; 
                }

                .timeline-axis-line {
                    position: absolute;
                    top: 50%;
                    left: 0;
                    right: 0;
                    height: 2px;
                    background: #444;
                    z-index: 0;
                    transform: translateY(5px); /* Adjust to center of bar */
                }

                .timeline-block {
                    position: relative;
                    z-index: 1;
                    margin: 0 4px; /* Gap between blocks */
                    cursor: pointer;
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    transition: transform 0.2s, opacity 0.2s;
                }
                .timeline-block:hover {
                    opacity: 1;
                    transform: translateY(-2px);
                }
                .timeline-block.selected .block-bar {
                    border: 2px solid #fff;
                    box-shadow: 0 0 10px rgba(255, 255, 255, 0.3);
                }

                .block-label-top {
                    position: absolute;
                    top: -25px;
                    font-size: 0.85rem;
                    font-weight: bold;
                    color: #ddd;
                    white-space: nowrap;
                    text-shadow: 0 1px 2px #000;
                    pointer-events: none;
                }

                .block-bar {
                    height: 20px;
                    width: 100%; /* Fill the flex item width */
                    border-radius: 4px; /* Rounded capsule look */
                    position: relative;
                    /* Gradient or solid */
                    background-image: linear-gradient(to bottom, rgba(255,255,255,0.1), rgba(0,0,0,0.1));
                }

                /* Hover Tooltip/Info */
                .hover-info {
                    position: absolute;
                    bottom: 100%;
                    left: 50%;
                    transform: translate(-50%, -10px);
                    background: rgba(0, 0, 0, 0.9);
                    border: 1px solid #555;
                    padding: 8px;
                    border-radius: 4px;
                    pointer-events: none;
                    opacity: 0;
                    transition: opacity 0.2s;
                    white-space: nowrap;
                    z-index: 100;
                    text-align: center;
                    box-shadow: 0 4px 10px rgba(0,0,0,0.5);
                }
                .timeline-block:hover .hover-info {
                    opacity: 1;
                    top: 100%; /* Show BELOW the bar */
                    bottom: auto;
                    transform: translate(-50%, 10px);
                }

                .hover-days {
                    font-size: 1rem;
                    font-weight: bold;
                    color: #fff;
                }
                .hover-date {
                    font-size: 0.75rem;
                    color: #aaa;
                    margin-top: 2px;
                }
            `}</style>
        </div>
    );
};

// Helper to generate consistent colors
function stringToColor(str: string) {
    if (str === 'No Squad') return '#444';
    let hash = 0;
    for (let i = 0; i < str.length; i++) hash = str.charCodeAt(i) + ((hash << 5) - hash);
    const c = (hash & 0x00FFFFFF).toString(16).toUpperCase();
    return '#' + '00000'.substring(0, 6 - c.length) + c;
}
