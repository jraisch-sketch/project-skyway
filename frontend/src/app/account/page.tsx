'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';

import type { FavoriteSchool } from '@/lib/types';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000/api';

type AccountProfile = {
  id: number;
  email: string;
  account_type: 'student' | 'parent' | 'admin';
  grad_year: number | null;
  full_name: string;
};

function labelForAccountType(accountType: string): string {
  if (accountType === 'student') return 'Student';
  if (accountType === 'parent') return 'Parent';
  if (accountType === 'admin') return 'Admin';
  return accountType;
}

export default function AccountPage() {
  const [account, setAccount] = useState<AccountProfile | null>(null);
  const [favorites, setFavorites] = useState<FavoriteSchool[]>([]);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('skyway_access');
    if (!token) {
      setError('You are not logged in.');
      setLoading(false);
      return;
    }

    Promise.all([
      fetch(`${API_BASE}/auth/me/`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      }),
      fetch(`${API_BASE}/favorites/`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      }),
    ])
      .then(async ([accountResponse, favoritesResponse]) => {
        const accountData = await accountResponse.json();
        if (!accountResponse.ok) {
          throw new Error(accountData?.detail || 'Could not load account.');
        }
        const favoritesData = await favoritesResponse.json();
        if (!favoritesResponse.ok) {
          throw new Error(favoritesData?.detail || 'Could not load favorites.');
        }
        setAccount(accountData);
        setFavorites(Array.isArray(favoritesData) ? favoritesData : []);
      })
      .catch((requestError: Error) => setError(requestError.message || 'Could not load account.'))
      .finally(() => setLoading(false));
  }, []);

  return (
    <section className='panel auth-form'>
      <h1>My Account</h1>
      {loading && <p>Loading account...</p>}
      {!loading && error && (
        <p className='auth-error'>
          {error} <Link href='/login'>Go to login</Link>
        </p>
      )}
      {!loading && !error && account && (
        <div className='detail-grid'>
          <div>
            <h3>Profile</h3>
            <p><strong>Name:</strong> {account.full_name || 'N/A'}</p>
            <p><strong>Email:</strong> {account.email}</p>
            <p><strong>Account Type:</strong> {labelForAccountType(account.account_type)}</p>
            <p><strong>Graduation Year:</strong> {account.grad_year ?? 'N/A'}</p>
          </div>
          <div>
            <h3>Favorite Schools</h3>
            {favorites.length === 0 && <p>No favorite schools yet.</p>}
            {favorites.length > 0 && (
              <ul>
                {favorites.map((favorite) => (
                  <li key={favorite.id}>
                    {favorite.school.name}
                    {' '}
                    <span className='muted-chip'>
                      {[favorite.school.city, favorite.school.state].filter(Boolean).join(', ') || 'Location N/A'}
                    </span>
                  </li>
                ))}
              </ul>
            )}
            <p className='auth-note'><Link href='/favorites'>Open full favorites list</Link></p>
          </div>
        </div>
      )}
    </section>
  );
}
