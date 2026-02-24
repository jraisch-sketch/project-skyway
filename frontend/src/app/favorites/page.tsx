'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';

import type { FavoriteSchool } from '@/lib/types';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000/api';

export default function FavoritesPage() {
  const [favorites, setFavorites] = useState<FavoriteSchool[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const token = localStorage.getItem('skyway_access');
    if (!token) {
      window.location.href = '/auth-access';
      return;
    }

    fetch(`${API_BASE}/favorites/`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    })
      .then(async (response) => {
        if (response.status === 401) {
          localStorage.removeItem('skyway_access');
          localStorage.removeItem('skyway_refresh');
          window.location.href = '/auth-access';
          return;
        }
        const data = await response.json();
        if (!response.ok) {
          throw new Error(data?.detail || 'Could not load favorites.');
        }
        setFavorites(data);
      })
      .catch((requestError: Error) => setError(requestError.message || 'Could not load favorites.'))
      .finally(() => setLoading(false));
  }, []);

  return (
    <section className='panel'>
      <h1>My Favorite Schools</h1>
      {loading && <p>Loading favorites...</p>}
      {!loading && error && <p className='auth-error'>{error}</p>}
      {!loading && !error && favorites.length === 0 && (
        <p>No favorites yet. Go back to <Link href='/'>Search</Link> and add a school.</p>
      )}
      {!loading && !error && favorites.length > 0 && (
        <div className='results-scroll' style={{ maxHeight: 'unset', overflow: 'visible', padding: 0 }}>
          {favorites.map((favorite) => (
            <article className='school-card' key={favorite.id}>
              <h3>{favorite.school.name}</h3>
              <p>{[favorite.school.city, favorite.school.state].filter(Boolean).join(', ') || 'City/State N/A'}</p>
              <p>Team Type: {favorite.school.team_type || 'N/A'}</p>
              <p>Conference: {favorite.school.conference || 'N/A'}</p>
              <p>Saved: {new Date(favorite.created_at).toLocaleDateString()}</p>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}
