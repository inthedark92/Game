import React from 'react';

interface TopPanelProps {
    hp: number;
    maxHp: number;
    mp: number;
    maxMp: number;
    level: number;
    sublevel: number;
    name: string;
}

const TopPanel: React.FC<TopPanelProps> = ({ hp, maxHp, mp, maxMp, level, sublevel, name }) => {
    const hpPercent = (hp / maxHp) * 100;
    const mpPercent = (mp / maxMp) * 100;

    return (
        <div className="top-panel" style={{
            background: '#333',
            color: '#fff',
            padding: '10px',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            borderBottom: '2px solid #555'
        }}>
            <div className="player-info">
                <span style={{ fontWeight: 'bold' }}>{name}</span> [{level}.{sublevel}]
            </div>
            <div className="resources" style={{ display: 'flex', gap: '20px', flex: 1, margin: '0 20px' }}>
                <div className="hp-bar-container" style={{ flex: 1, background: '#500', height: '20px', position: 'relative' }}>
                    <div className="hp-bar" style={{ width: `${hpPercent}%`, background: '#f00', height: '100%' }}></div>
                    <div style={{ position: 'absolute', top: 0, width: '100%', textAlign: 'center', fontSize: '12px' }}>
                        HP: {hp}/{maxHp}
                    </div>
                </div>
                <div className="mp-bar-container" style={{ flex: 1, background: '#005', height: '20px', position: 'relative' }}>
                    <div className="mp-bar" style={{ width: `${mpPercent}%`, background: '#00f', height: '100%' }}></div>
                    <div style={{ position: 'absolute', top: 0, width: '100%', textAlign: 'center', fontSize: '12px' }}>
                        MP: {mp}/{maxMp}
                    </div>
                </div>
            </div>
            <div className="actions">
                <button>Menu</button>
            </div>
        </div>
    );
};

export default TopPanel;
