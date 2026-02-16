'use client';

import { useSearchParams } from 'next/navigation';
import { useEffect, useState } from 'react';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000/api';

export default function VerifyEmailPage() {
  const params = useSearchParams();
  const [message, setMessage] = useState('Verifying...');

  useEffect(() => {
    const uid = params.get('uid');
    const token = params.get('token');
    if (!uid || !token) {
      setMessage('Invalid verification link.');
      return;
    }

    fetch(`${API_BASE}/auth/verify-email/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ uid, token }),
    })
      .then(async (response) => {
        const data = await response.json();
        if (response.ok) setMessage(data.detail || 'Email verified.');
        else setMessage(data.detail || 'Verification failed.');
      })
      .catch(() => setMessage('Verification failed.'));
  }, [params]);

  return (
    <section className='panel'>
      <h1>Email Verification</h1>
      <p>{message}</p>
    </section>
  );
}
