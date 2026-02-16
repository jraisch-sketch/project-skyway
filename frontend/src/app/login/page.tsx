'use client';

import { useState } from 'react';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000/api';

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [message, setMessage] = useState('');

  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    setMessage('');
    const response = await fetch(`${API_BASE}/auth/login/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });
    const data = await response.json();
    if (!response.ok) {
      setMessage(data.detail || 'Login failed');
      return;
    }
    localStorage.setItem('skyway_access', data.access);
    localStorage.setItem('skyway_refresh', data.refresh);
    setMessage('Login successful');
  };

  return (
    <form className='panel auth-form' onSubmit={submit}>
      <h1>Login</h1>
      <input value={email} onChange={(e) => setEmail(e.target.value)} placeholder='Email' type='email' required />
      <input value={password} onChange={(e) => setPassword(e.target.value)} placeholder='Password' type='password' required />
      <button type='submit'>Sign In</button>
      {message && <p>{message}</p>}
    </form>
  );
}
