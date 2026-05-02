import React, { useState, useEffect } from 'react';
import axios from 'axios';

const CombatPanel: React.FC<{ combatId: string }> = ({ combatId }) => {
    const [combat, setCombat] = useState<any>(null);

    useEffect(() => {
        fetchCombat();
        const ws = new WebSocket(`ws://${window.location.host}/ws/combat/${combatId}/`);
        ws.onmessage = (event) => {
            setCombat(JSON.parse(event.data));
        };
        return () => ws.close();
    }, [combatId]);

    const fetchCombat = async () => {
        const response = await axios.get(`/api/v2/combat/${combatId}/state/`);
        setCombat(response.data.state);
    };

    const makeTurn = async (attack: number, defense: number[]) => {
        await axios.post(`/api/v2/combat/${combatId}/turn/`, {
            attack_zone: attack,
            defense_zones: defense
        });
    };

    if (!combat) return <div>Loading Combat...</div>;

    return (
        <div className="combat-panel" style={{ color: '#fff' }}>
            <div className="combat-header" style={{ display: 'flex', justifyContent: 'space-between' }}>
                <div>{combat.player.name} ({combat.player.current_hp}/{combat.player.max_hp})</div>
                <div>VS</div>
                <div>{combat.monster.name} ({combat.monster.current_hp}/{combat.monster.max_hp})</div>
            </div>

            {combat.status === 'active' ? (
                <div className="controls" style={{ marginTop: '20px', textAlign: 'center' }}>
                    <p>Select Attack Zone:</p>
                    {[1, 2, 3, 4].map(z => (
                        <button key={z} onClick={() => makeTurn(z, [1, 2])}>Zone {z}</button>
                    ))}
                </div>
            ) : (
                <div className="result" style={{ marginTop: '20px', textAlign: 'center', fontSize: '20px' }}>
                    {combat.status === 'victory' ? 'VICTORY!' : 'DEFEAT'}
                    <p>{combat.result_message}</p>
                </div>
            )}

            <div className="log" style={{ marginTop: '20px', height: '150px', overflowY: 'auto', background: '#000', padding: '10px' }}>
                {combat.log.map((entry: string, i: number) => (
                    <div key={i}>{entry}</div>
                ))}
            </div>
        </div>
    );
};

export default CombatPanel;
