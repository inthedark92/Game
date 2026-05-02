import React, { useState, useEffect } from 'react';
import { useGameStore } from '../../store/useGameStore';

interface Message {
    username: string;
    message: string;
}

const ChatPanel: React.FC = () => {
    const [messages, setMessages] = useState<Message[]>([]);
    const [input, setInput] = useState('');
    const [socket, setSocket] = useState<WebSocket | null>(null);

    useEffect(() => {
        const ws = new WebSocket(`ws://${window.location.host}/ws/chat/world/`);
        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            setMessages(prev => [...prev, data]);
        };
        setSocket(ws);
        return () => ws.close();
    }, []);

    const sendMessage = () => {
        if (socket && input) {
            socket.send(JSON.stringify({ message: input }));
            setInput('');
        }
    };

    return (
        <div className="chat-panel" style={{ height: '100%', display: 'flex', flexDirection: 'column', background: '#111', color: '#fff' }}>
            <div className="messages" style={{ flex: 1, overflowY: 'auto', padding: '10px' }}>
                {messages.map((m, i) => (
                    <div key={i}><strong>{m.username}:</strong> {m.message}</div>
                ))}
            </div>
            <div className="input-area" style={{ display: 'flex' }}>
                <input
                    style={{ flex: 1, background: '#222', color: '#fff', border: '1px solid #444' }}
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && sendMessage()}
                />
                <button onClick={sendMessage}>Send</button>
            </div>
        </div>
    );
};

export default ChatPanel;
