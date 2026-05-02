import React, { useState } from 'react';
import axios from 'axios';
import { useGameStore } from '../store/useGameStore';

const Login: React.FC = () => {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [isRegister, setIsRegister] = useState(false);
    const { setProfile } = useGameStore();

    const handleAuth = async () => {
        const endpoint = isRegister ? '/api/v2/auth/register/' : '/api/v2/auth/login/';
        try {
            const response = await axios.post(endpoint, { username, password });
            setProfile(response.data);
        } catch (error) {
            alert('Auth failed');
        }
    };

    return (
        <div className="login-container" style={{
            display: 'flex',
            flexDirection: 'column',
            width: '300px',
            margin: '100px auto',
            padding: '20px',
            background: '#333',
            color: '#fff',
            borderRadius: '8px'
        }}>
            <h2>{isRegister ? 'Register' : 'Login'}</h2>
            <input
                type="text"
                placeholder="Username"
                value={username}
                onChange={e => setUsername(e.target.value)}
                style={{ marginBottom: '10px', padding: '5px' }}
            />
            <input
                type="password"
                placeholder="Password"
                value={password}
                onChange={e => setPassword(e.target.value)}
                style={{ marginBottom: '10px', padding: '5px' }}
            />
            <button onClick={handleAuth} style={{ padding: '10px', background: '#555', color: '#fff', border: 'none', cursor: 'pointer' }}>
                {isRegister ? 'Register' : 'Login'}
            </button>
            <p onClick={() => setIsRegister(!isRegister)} style={{ cursor: 'pointer', fontSize: '12px', marginTop: '10px' }}>
                {isRegister ? 'Already have an account? Login' : 'Need an account? Register'}
            </p>
        </div>
    );
};

export default Login;
