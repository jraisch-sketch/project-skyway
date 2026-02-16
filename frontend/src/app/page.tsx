'use client';

import dynamic from 'next/dynamic';
import Link from 'next/link';
import { useEffect, useMemo, useRef, useState } from 'react';

import { apiFetch } from '@/lib/api';
import { DISCIPLINE_LABELS, getDisciplineLabels } from '@/lib/disciplines';
import type { FilterOptions, School } from '@/lib/types';

const SchoolMap = dynamic(() => import('@/components/SchoolMap'), { ssr: false });

const disciplineChoices = Object.keys(DISCIPLINE_LABELS);

export default function HomePage() {
  const [schools, setSchools] = useState<School[]>([]);
  const [filters, setFilters] = useState<FilterOptions | null>(null);
  const [q, setQ] = useState('');
  const [teamType, setTeamType] = useState('');
  const [conference, setConference] = useState('');
  const [state, setState] = useState('');
  const [sort, setSort] = useState('relevance');
  const [disciplines, setDisciplines] = useState<string[]>([]);
  const [lat, setLat] = useState<number | null>(null);
  const [lng, setLng] = useState<number | null>(null);
  const [radius, setRadius] = useState<number | null>(null);
  const [popupSchoolId, setPopupSchoolId] = useState<number | null>(null);
  const [popupRequestId, setPopupRequestId] = useState(0);
  const [disciplineMenuOpen, setDisciplineMenuOpen] = useState(false);
  const disciplineMenuRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    apiFetch<FilterOptions>('/filters/')
      .then(setFilters)
      .catch((error) => console.error(error));
  }, []);

  const queryString = useMemo(() => {
    const params = new URLSearchParams();
    if (q) params.set('q', q);
    if (teamType) params.set('team_type', teamType);
    if (conference) params.set('conference', conference);
    if (state) params.set('state', state);
    if (sort) params.set('sort', sort);
    if (disciplines.length) params.set('disciplines', disciplines.join(','));
    if (lat !== null && lng !== null) {
      params.set('lat', String(lat));
      params.set('lng', String(lng));
    }
    if (radius !== null) {
      params.set('radius', String(radius));
    }
    return params.toString();
  }, [q, teamType, conference, state, sort, disciplines, lat, lng, radius]);

  useEffect(() => {
    apiFetch<School[]>(`/schools/?${queryString}`)
      .then(setSchools)
      .catch((error) => console.error(error));
  }, [queryString]);

  useEffect(() => {
    const onClickOutside = (event: MouseEvent) => {
      if (
        disciplineMenuRef.current &&
        !disciplineMenuRef.current.contains(event.target as Node)
      ) {
        setDisciplineMenuOpen(false);
      }
    };
    document.addEventListener('mousedown', onClickOutside);
    return () => document.removeEventListener('mousedown', onClickOutside);
  }, []);

  const detectLocation = () => {
    if (!navigator.geolocation) return;
    navigator.geolocation.getCurrentPosition((position) => {
      setLat(position.coords.latitude);
      setLng(position.coords.longitude);
      setRadius(100);
      setSort('distance');
    });
  };

  const clearFilters = () => {
    setQ('');
    setTeamType('');
    setConference('');
    setState('');
    setSort('relevance');
    setDisciplines([]);
    setLat(null);
    setLng(null);
    setRadius(null);
    setPopupSchoolId(null);
  };

  return (
    <div className='stack'>
      <section className='panel'>
        <h1>Find College Cycling Programs</h1>
        <div className='filter-bar'>
          <div className='filters'>
            <input
              placeholder='Search school, city, or state'
              value={q}
              onChange={(e) => setQ(e.target.value)}
            />
            <select value={teamType} onChange={(e) => setTeamType(e.target.value)}>
              <option value=''>All Team Types</option>
              {filters?.team_types.map((option) => (
                <option key={option} value={option}>
                  {option}
                </option>
              ))}
            </select>
            <select value={conference} onChange={(e) => setConference(e.target.value)}>
              <option value=''>All Conferences</option>
              {filters?.conferences.map((option) => (
                <option key={option} value={option}>
                  {option}
                </option>
              ))}
            </select>
            <select value={state} onChange={(e) => setState(e.target.value)}>
              <option value=''>All States</option>
              {filters?.states.map((option) => (
                <option key={option} value={option}>
                  {option}
                </option>
              ))}
            </select>
            <div className='multi-dropdown' ref={disciplineMenuRef}>
              <button
                type='button'
                className='multi-dropdown-trigger'
                onClick={() => setDisciplineMenuOpen((prev) => !prev)}
              >
                {disciplines.length > 0
                  ? `Disciplines (${disciplines.length})`
                  : 'Disciplines'}
              </button>
              {disciplineMenuOpen && (
                <div className='multi-dropdown-menu'>
                  {disciplineChoices.map((item) => (
                    <label key={item} className='multi-dropdown-item'>
                      <input
                        type='checkbox'
                        checked={disciplines.includes(item)}
                        onChange={() =>
                          setDisciplines((prev) =>
                            prev.includes(item)
                              ? prev.filter((value) => value !== item)
                              : [...prev, item]
                          )
                        }
                      />
                      <span>{DISCIPLINE_LABELS[item]}</span>
                    </label>
                  ))}
                </div>
              )}
            </div>
          </div>
          <div className='filter-links'>
            <span className='sort-label'>Sort:</span>
            <button
              type='button'
              className={`filter-link ${sort === 'relevance' ? 'active' : ''}`}
              onClick={() => setSort('relevance')}
            >
              Relevance
            </button>
            <button
              type='button'
              className={`filter-link ${sort === 'distance' ? 'active' : ''}`}
              onClick={() => setSort('distance')}
            >
              Distance
            </button>
            <button
              type='button'
              className={`filter-link ${sort === 'alphabetical' ? 'active' : ''}`}
              onClick={() => setSort('alphabetical')}
            >
              A-Z
            </button>
            <button type='button' className='filter-link' onClick={detectLocation}>
              Use My Location
            </button>
            <button type='button' className='filter-link' onClick={clearFilters}>
              Clear Filters
            </button>
          </div>
        </div>
        <p className='filter-hint'>Disciplines: select one or more from the dropdown.</p>
      </section>

      <section className='layout-grid'>
        <div className='panel'>
          <h2>Map View</h2>
          <SchoolMap
            schools={schools}
            userLocation={lat !== null && lng !== null ? [lat, lng] : null}
            radiusMiles={radius}
            popupSchoolId={popupSchoolId}
            popupRequestId={popupRequestId}
          />
        </div>
        <div className='panel list-panel'>
          <h2>List View ({schools.length})</h2>
          {schools.map((school) => (
            <article className='school-card' key={school.id}>
              <h3>{school.name}</h3>
              <p>{[school.city, school.state].filter(Boolean).join(', ') || 'City/State N/A'}</p>
              <p>Team Type: {school.team_type || 'N/A'}</p>
              <p>Conference: {school.conference || 'N/A'}</p>
              <p>Cycling Program Status: {school.cycling_program_status || 'active'}</p>
              <div className='discipline-chips'>
                {getDisciplineLabels(school).length > 0 ? (
                  getDisciplineLabels(school).map((label) => (
                    <span key={label} className='chip'>{label}</span>
                  ))
                ) : (
                  <span className='chip muted-chip'>No discipline data</span>
                )}
              </div>
              <button
                type='button'
                className='list-card-link'
                onClick={() => {
                  setPopupSchoolId(school.id);
                  setPopupRequestId((prev) => prev + 1);
                }}
              >
                Show on map
              </button>
              <br />
              <Link className='list-card-link' href={`/schools/${school.id}`}>View details</Link>
            </article>
          ))}
          {schools.length === 0 && <p>No schools matched your current filters.</p>}
        </div>
      </section>
    </div>
  );
}
