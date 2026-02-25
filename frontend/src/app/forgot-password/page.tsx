'use client';

import { useState } from 'react';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000/api';
type MessageState = { type: 'error' | 'success'; text: string } | null;

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState('');
  const [message, setMessage] = useState<MessageState>(null);
  const [submitting, setSubmitting] = useState(false);

  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    setMessage(null);
    setSubmitting(true);
    try {
      const response = await fetch(`${API_BASE}/auth/password-reset/request/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email }),
      });
      const data = await response.json().catch(() => ({}));
      const detail = typeof data.detail === 'string'
        ? data.detail
        : response.ok
          ? 'If the account exists, a password reset email has been sent.'
          : 'Could not send password reset email.';
      setMessage({ type: response.ok ? 'success' : 'error', text: detail });
    } catch (error) {
      const detail = error instanceof Error ? error.message : 'Could not send password reset email.';
      setMessage({ type: 'error', text: detail });
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form className='panel auth-form' onSubmit={submit}>
      <h1>Forgot Password</h1>
      <input type='email' value={email} onChange={(e) => setEmail(e.target.value)} placeholder='Email' required />
      <button type='submit' disabled={submitting}>{submitting ? 'Sending...' : 'Send Reset Email'}</button>
      {message && (
        <p className={message.type === 'error' ? 'auth-error' : 'auth-success'}>
          {message.text}
        </p>
      )}
    </form>
  );
}
