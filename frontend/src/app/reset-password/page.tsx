'use client';

import { useSearchParams } from 'next/navigation';
import { Suspense } from 'react';
import { useState } from 'react';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000/api';
type MessageState = { type: 'error' | 'success'; text: string } | null;

function ResetPasswordPageContent() {
  const params = useSearchParams();
  const [newPassword, setNewPassword] = useState('');
  const [message, setMessage] = useState<MessageState>(null);
  const [submitting, setSubmitting] = useState(false);

  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    const uid = params.get('uid');
    const token = params.get('token');
    if (!uid || !token) {
      setMessage({ type: 'error', text: 'Invalid password reset link.' });
      return;
    }

    setMessage(null);
    setSubmitting(true);
    try {
      const response = await fetch(`${API_BASE}/auth/password-reset/confirm/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ uid, token, new_password: newPassword }),
      });
      const data = await response.json().catch(() => ({}));
      const detail = typeof data.detail === 'string'
        ? data.detail
        : response.ok
          ? 'Password reset successfully.'
          : 'Password reset failed.';
      setMessage({ type: response.ok ? 'success' : 'error', text: detail });
    } catch (error) {
      const detail = error instanceof Error ? error.message : 'Password reset failed.';
      setMessage({ type: 'error', text: detail });
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form className='panel auth-form' onSubmit={submit}>
      <h1>Reset Password</h1>
      <input type='password' value={newPassword} onChange={(e) => setNewPassword(e.target.value)} placeholder='New password' required />
      <button type='submit' disabled={submitting}>{submitting ? 'Updating...' : 'Update Password'}</button>
      {message && (
        <p className={message.type === 'error' ? 'auth-error' : 'auth-success'}>
          {message.text}
        </p>
      )}
    </form>
  );
}

export default function ResetPasswordPage() {
  return (
    <Suspense fallback={<section className='panel'><p>Loading...</p></section>}>
      <ResetPasswordPageContent />
    </Suspense>
  );
}
