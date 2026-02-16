'use client';

import { useState } from 'react';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000/api';

export default function RegisterPage() {
  const [form, setForm] = useState({
    username: '',
    email: '',
    password: '',
    grad_year: '',
    location: '',
    cycling_discipline: '',
  });
  const [message, setMessage] = useState('');

  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    setMessage('');
    const payload = {
      ...form,
      grad_year: form.grad_year ? Number(form.grad_year) : null,
    };

    const response = await fetch(`${API_BASE}/auth/register/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });

    const data = await response.json();
    if (!response.ok) {
      setMessage(JSON.stringify(data));
      return;
    }

    setMessage(data.detail || 'Registration successful. Verify your email.');
  };

  return (
    <form className='panel auth-form' onSubmit={submit}>
      <h1>Create Student Account</h1>
      <input placeholder='Name' value={form.username} onChange={(e) => setForm({ ...form, username: e.target.value })} required />
      <input placeholder='Email' type='email' value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} required />
      <input placeholder='Password' type='password' value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} required />
      <input placeholder='Graduation Year' type='number' value={form.grad_year} onChange={(e) => setForm({ ...form, grad_year: e.target.value })} />
      <input placeholder='Location' value={form.location} onChange={(e) => setForm({ ...form, location: e.target.value })} />
      <input placeholder='Preferred Discipline' value={form.cycling_discipline} onChange={(e) => setForm({ ...form, cycling_discipline: e.target.value })} />
      <button type='submit'>Register</button>
      {message && <p>{message}</p>}
    </form>
  );
}
