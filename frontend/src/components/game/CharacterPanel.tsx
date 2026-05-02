import React from 'react';
import { useGameStore } from '../../store/useGameStore';
import axios from 'axios';

const CharacterPanel: React.FC = () => {
    const { profile, setProfile } = useGameStore();

    const addStat = async (stat: string) => {
        try {
            const response = await axios.post('/api/v2/profile/distribute_stat/', { stat_name: stat });
            setProfile(response.data);
        } catch (error) {
            console.error('Error distributing stat:', error);
        }
    };

    if (!profile) return null;

    return (
        <div className="character-panel" style={{ color: '#ccc' }}>
            <h2>{profile.name}</h2>
            <div className="stats-section">
                <div>Level: {profile.level}.{profile.sublevel}</div>
                <div>Free Stats: {profile.free_stats}</div>

                <div style={{ marginTop: '10px' }}>
                    <div>Strength: {profile.strength_base} + {profile.strength_mod}
                        {profile.free_stats > 0 && <button onClick={() => addStat('strength')}>+</button>}
                    </div>
                    <div>Agility: {profile.agility_base} + {profile.agility_mod}
                        {profile.free_stats > 0 && <button onClick={() => addStat('agility')}>+</button>}
                    </div>
                    {/* Add other stats similarly */}
                </div>
            </div>
        </div>
    );
};

export default CharacterPanel;
