'use client';

import Link from 'next/link';
import { useEffect, useMemo, useState } from 'react';

import { getDisciplineLabels } from '@/lib/disciplines';
import { slugify } from '@/lib/seo';
import type { FavoriteSchool } from '@/lib/types';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000/api';

type SortKey =
  | 'school'
  | 'location'
  | 'teamType'
  | 'conference'
  | 'disciplines'
  | 'dateAdded';

type SortDirection = 'asc' | 'desc';

function getSortableValue(favorite: FavoriteSchool, key: SortKey): string | number {
  switch (key) {
    case 'school':
      return favorite.school.name || '';
    case 'location':
      return [favorite.school.city, favorite.school.state].filter(Boolean).join(', ');
    case 'teamType':
      return favorite.school.team_type || '';
    case 'conference':
      return favorite.school.conference || '';
    case 'disciplines':
      return getDisciplineLabels(favorite.school).join(', ');
    case 'dateAdded':
      return new Date(favorite.created_at).getTime();
    default:
      return '';
  }
}

export default function FavoritesPage() {
  const [favorites, setFavorites] = useState<FavoriteSchool[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [sortKey, setSortKey] = useState<SortKey>('dateAdded');
  const [sortDirection, setSortDirection] = useState<SortDirection>('desc');

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

  const sortedFavorites = useMemo(() => {
    return [...favorites].sort((a, b) => {
      const aValue = getSortableValue(a, sortKey);
      const bValue = getSortableValue(b, sortKey);
      const direction = sortDirection === 'asc' ? 1 : -1;

      if (typeof aValue === 'number' && typeof bValue === 'number') {
        return (aValue - bValue) * direction;
      }

      return String(aValue).localeCompare(String(bValue), undefined, { sensitivity: 'base' }) * direction;
    });
  }, [favorites, sortDirection, sortKey]);

  const toggleSort = (key: SortKey) => {
    if (sortKey === key) {
      setSortDirection((currentDirection) => (currentDirection === 'asc' ? 'desc' : 'asc'));
      return;
    }

    setSortKey(key);
    setSortDirection('asc');
  };

  const sortIndicator = (key: SortKey): string => {
    if (sortKey !== key) {
      return '';
    }
    return sortDirection === 'asc' ? ' (A-Z)' : ' (Z-A)';
  };

  return (
    <section className='panel'>
      <h1>My Favorite Schools</h1>
      {loading && <p>Loading favorites...</p>}
      {!loading && error && <p className='auth-error'>{error}</p>}
      {!loading && !error && favorites.length === 0 && (
        <p>No favorites yet. Go back to <Link href='/'>Search</Link> and add a school.</p>
      )}
      {!loading && !error && favorites.length > 0 && (
        <div className='favorites-table-wrap'>
          <table className='favorites-table'>
            <thead>
              <tr>
                <th><button type='button' className='favorites-sort-button' onClick={() => toggleSort('school')}>School{sortIndicator('school')}</button></th>
                <th><button type='button' className='favorites-sort-button' onClick={() => toggleSort('location')}>City/State{sortIndicator('location')}</button></th>
                <th><button type='button' className='favorites-sort-button' onClick={() => toggleSort('teamType')}>Team Type{sortIndicator('teamType')}</button></th>
                <th><button type='button' className='favorites-sort-button' onClick={() => toggleSort('conference')}>Conference{sortIndicator('conference')}</button></th>
                <th><button type='button' className='favorites-sort-button' onClick={() => toggleSort('disciplines')}>Discipline tags{sortIndicator('disciplines')}</button></th>
                <th><button type='button' className='favorites-sort-button' onClick={() => toggleSort('dateAdded')}>Date Added as favorite{sortIndicator('dateAdded')}</button></th>
              </tr>
            </thead>
            <tbody>
              {sortedFavorites.map((favorite) => {
                const disciplineLabels = getDisciplineLabels(favorite.school);

                return (
                  <tr key={favorite.id}>
                    <td data-label='School'>
                      <Link
                        href={`/schools/cycling-program/${favorite.school.id}/${slugify(favorite.school.name)}`}
                        className='favorites-school-name'
                      >
                        {favorite.school.name}
                      </Link>
                      <div className='favorites-school-links'>
                        {favorite.school.school_website && (
                          <a href={favorite.school.school_website} target='_blank' rel='noreferrer'>School</a>
                        )}
                        {favorite.school.athletic_dept_website && (
                          <a href={favorite.school.athletic_dept_website} target='_blank' rel='noreferrer'>Athletics</a>
                        )}
                        {favorite.school.cycling_website && (
                          <a href={favorite.school.cycling_website} target='_blank' rel='noreferrer'>Cycling</a>
                        )}
                      </div>
                    </td>
                    <td data-label='City/State'>{[favorite.school.city, favorite.school.state].filter(Boolean).join(', ') || 'N/A'}</td>
                    <td data-label='Team Type'>{favorite.school.team_type || 'N/A'}</td>
                    <td data-label='Conference'>{favorite.school.conference || 'N/A'}</td>
                    <td data-label='Discipline tags'>
                      <div className='discipline-chips'>
                        {disciplineLabels.length > 0 ? (
                          disciplineLabels.map((label) => (
                            <span key={`${favorite.id}-${label}`} className='chip'>{label}</span>
                          ))
                        ) : (
                          <span className='chip muted-chip'>No discipline data</span>
                        )}
                      </div>
                    </td>
                    <td data-label='Date Added'>{new Date(favorite.created_at).toLocaleDateString()}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
