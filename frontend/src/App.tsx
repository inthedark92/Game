import React from 'react';
import TopPanel from './components/layout/TopPanel';
import Login from './components/Login';
import CharacterPanel from './components/game/CharacterPanel';
import InventoryPanel from './components/game/InventoryPanel';
import CombatPanel from './components/game/CombatPanel';
import ChatPanel from './components/chat/ChatPanel';
import { useGameStore } from './store/useGameStore';

function App() {
  const { profile, activeFrame, setActiveFrame } = useGameStore();

  if (!profile) {
      return <Login />;
  }

  return (
    <div className="game-wrapper" style={{ height: '100vh', display: 'flex', flexDirection: 'column', background: '#000' }}>
      <TopPanel
        hp={profile.current_hp}
        maxHp={profile.max_hp}
        mp={profile.current_mp}
        maxMp={profile.max_mp}
        level={profile.level}
        sublevel={profile.sublevel}
        name={profile.name}
      />
      <div style={{ flex: 1, display: 'flex', overflow: 'hidden' }}>
        <div className="main-area" style={{ flex: 1, padding: '20px', background: '#222', overflowY: 'auto' }}>
            <div className="nav-buttons" style={{ marginBottom: '20px' }}>
                <button onClick={() => setActiveFrame('location')}>Location</button>
                <button onClick={() => setActiveFrame('character')}>Character</button>
                <button onClick={() => setActiveFrame('inventory')}>Inventory</button>
                <button onClick={() => setActiveFrame('combat')}>Combat (Hunt)</button>
            </div>

            {activeFrame === 'location' && <div>Location: {profile.current_location?.name || 'Unknown'}</div>}
            {activeFrame === 'character' && <CharacterPanel />}
            {activeFrame === 'inventory' && <InventoryPanel />}
            {activeFrame === 'combat' && <div>Click "Hunt" to start a battle (Mock)</div>}
        </div>
        <div className="sidebar" style={{ width: '300px', background: '#333', borderLeft: '1px solid #444', display: 'flex', flexDirection: 'column' }}>
            <div style={{ height: '70%' }}>
                <ChatPanel />
            </div>
            <div style={{ height: '30%', borderTop: '1px solid #444', padding: '10px', color: '#ccc' }}>
                Online List (Mock)
            </div>
        </div>
      </div>
    </div>
  )
}

export default App
