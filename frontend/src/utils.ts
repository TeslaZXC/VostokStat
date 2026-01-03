export const formatDuration = (frames: number): string => {
    // Formula: minutes = frames * 0.016
    const totalMinutes = frames * 0.016;

    if (totalMinutes < 60) {
        return `${Math.round(totalMinutes)} мин`;
    }

    const hours = Math.floor(totalMinutes / 60);
    const minutes = Math.round(totalMinutes % 60);

    if (minutes === 0) {
        return `${hours} ч`;
    }

    return `${hours} ч ${minutes} мин`;
};

export const formatPlayerName = (name: string, squad?: string | null): string => {
    // If name already contains a tag like [TAG] Name, maybe just uppercase it?
    // But for now, if squad is explicitly provided, use it.
    if (squad) {
        return `[${squad.toUpperCase()}] ${name}`;
    }
    // If no squad provided, try to uppercase existing tag if present
    const tagMatch = name.match(/^\[(.*?)\]\s*(.*)$/);
    if (tagMatch) {
        return `[${tagMatch[1].toUpperCase()}] ${tagMatch[2]}`;
    }
    return name;
};

export const getCleanName = (name: string): string => {
    const tagMatch = name.match(/^\[(.*?)\]\s*(.*)$/);
    if (tagMatch) {
        return tagMatch[2];
    }
    return name;
};
