'use client';

import { useState } from 'react';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000/api';

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState('');
  const [message, setMessage] = useState('');

  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    const response = await fetch(`${API_BASE}/auth/password-reset/request/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email }),
    });
    const data = await response.json();
    setMessage(data.detail || (response.ok ? 'Request sent.' : 'Failed to send request.'));
  };

  return (
    <form className='panel auth-form' onSubmit={submit}>
      <h1>Forgot Password</h1>
      <input type='email' value={email} onChange={(e) => setEmail(e.target.value)} placeholder='Email' required />
      <button type='submit'>Send Reset Email</button>
      {message && <p>{message}</p>}
    </form>
  );
}
