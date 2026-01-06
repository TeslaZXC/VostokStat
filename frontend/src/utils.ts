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
    // Helper to capitalize first letter
    const capitalize = (str: string) => str.charAt(0).toUpperCase() + str.slice(1);

    // If name already contains a tag like [TAG] Name, maybe just uppercase it?
    // But for now, if squad is explicitly provided, use it.
    if (squad) {
        return `[${squad.toUpperCase()}] ${capitalize(name)}`;
    }
    // If no squad provided, try to uppercase existing tag if present and capitalize name
    const tagMatch = name.match(/^\[(.*?)\]\s*(.*)$/);
    if (tagMatch) {
        return `[${tagMatch[1].toUpperCase()}] ${capitalize(tagMatch[2])}`;
    }
    return capitalize(name);
};

export const getCleanName = (name: string): string => {
    const tagMatch = name.match(/^\[(.*?)\]\s*(.*)$/);
    if (tagMatch) {
        return tagMatch[2];
    }
    return name;
};
