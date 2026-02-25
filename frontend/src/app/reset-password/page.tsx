'use client';

import { useSearchParams } from 'next/navigation';
import { Suspense } from 'react';
import { useState } from 'react';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000/api';

function ResetPasswordPageContent() {
  const params = useSearchParams();
  const [newPassword, setNewPassword] = useState('');
  const [message, setMessage] = useState('');

  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    const uid = params.get('uid');
    const token = params.get('token');
    if (!uid || !token) {
      setMessage('Invalid password reset link.');
      return;
    }

    const response = await fetch(`${API_BASE}/auth/password-reset/confirm/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ uid, token, new_password: newPassword }),
    });
    const data = await response.json();
    setMessage(data.detail || (response.ok ? 'Password reset successfully.' : 'Password reset failed.'));
  };

  return (
    <form className='panel auth-form' onSubmit={submit}>
      <h1>Reset Password</h1>
      <input type='password' value={newPassword} onChange={(e) => setNewPassword(e.target.value)} placeholder='New password' required />
      <button type='submit'>Update Password</button>
      {message && <p>{message}</p>}
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
