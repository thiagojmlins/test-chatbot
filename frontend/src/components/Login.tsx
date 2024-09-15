import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import httpClient from '../httpClient';

const Login = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const navigate = useNavigate();

  const handleLogin = async () => {
    const formData = new FormData(); // Create form data
    formData.append('username', username);
    formData.append('password', password);

    try {
      const response = await httpClient.post('/token', formData);
      localStorage.setItem('token', response.data.access_token);
      navigate('/chat'); // Redirect to chat after successful login
    } catch (error) {
      console.error('Login failed', error);
    }
  };

  return (
    <div className="max-w-md w-full bg-white p-6 rounded shadow-md">
      <h2 className="text-2xl mb-4">Login</h2>
      <input
        type="text"
        placeholder="Username"
        className="w-full p-2 mb-4 border"
        value={username}
        onChange={(e) => setUsername(e.target.value)}
      />
      <input
        type="password"
        placeholder="Password"
        className="w-full p-2 mb-4 border"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
      />
      <button
        className="w-full bg-purple-500 text-white p-2 rounded"
        onClick={handleLogin}
      >
        Login
      </button>
      <p className="mt-2 text-sm text-gray-400">
        New user?{' '}
        <a className="text-purple-500" href="/signup">
          Sign up
        </a>
      </p>
    </div>
  );
};

export default Login;
