import { useState } from 'react';
import httpClient from '../httpClient';
import { useNavigate } from 'react-router-dom';

const SignUp = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const navigate = useNavigate();

  const handleSignUp = async () => {
    try {
      await httpClient.post('/users', { username, password });
      alert('User created successfully');
      navigate('/login');
    } catch (error) {
      console.error('Sign up error', error);
    }
  };

  return (
    <div className="max-w-md w-full bg-white p-6 rounded shadow-md">
      <h2 className="text-2xl mb-4">Sign Up</h2>
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
        onClick={handleSignUp}
      >
        Sign Up
      </button>
    </div>
  );
};

export default SignUp;
