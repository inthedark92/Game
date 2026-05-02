import { create } from 'zustand';

interface GameState {
    profile: any;
    setProfile: (profile: any) => void;
    activeFrame: string;
    setActiveFrame: (frame: string) => void;
}

export const useGameStore = create<GameState>((set) => ({
    profile: null,
    setProfile: (profile) => set({ profile }),
    activeFrame: 'location',
    setActiveFrame: (frame) => set({ activeFrame: frame }),
}));
