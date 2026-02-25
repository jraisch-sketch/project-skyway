'use client';

import dynamic from 'next/dynamic';
import { useEffect, useMemo, useRef, useState } from 'react';

import CmsBlocks from '@/components/CmsBlocks';
import { apiFetch } from '@/lib/api';
import { DISCIPLINE_LABELS, getDisciplineLabels } from '@/lib/disciplines';
import type { CmsWidgetPlacement, ConferenceSummary, FilterOptions, School, SchoolDetail } from '@/lib/types';

const SchoolMap = dynamic(() => import('@/components/SchoolMap'), { ssr: false });
const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000/api';

const disciplineChoices = Object.keys(DISCIPLINE_LABELS);

function formatProfileValue(value: string): string {
  if (!value) return 'N/A';
  return value
    .replaceAll('_', ' ')
    .replace(/\b\w/g, (ch) => ch.toUpperCase());
}

export default function HomePage() {
  const [schools, setSchools] = useState<School[]>([]);
  const [filters, setFilters] = useState<FilterOptions | null>(null);
  const [q, setQ] = useState('');
  const [teamType, setTeamType] = useState('');
  const [conference, setConference] = useState('');
  const [state, setState] = useState('');
  const [disciplines, setDisciplines] = useState<string[]>([]);
  const [lat, setLat] = useState<number | null>(null);
  const [lng, setLng] = useState<number | null>(null);
  const [radius, setRadius] = useState<number | null>(null);
  const [popupSchoolId, setPopupSchoolId] = useState<number | null>(null);
  const [popupRequestId, setPopupRequestId] = useState(0);
  const [disciplineMenuOpen, setDisciplineMenuOpen] = useState(false);
  const [resultsOpen, setResultsOpen] = useState(true);
  const [detailSchoolId, setDetailSchoolId] = useState<number | null>(null);
  const [detailSchool, setDetailSchool] = useState<SchoolDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [detailError, setDetailError] = useState('');
  const [logoLoadError, setLogoLoadError] = useState(false);
  const [favoriteStatus, setFavoriteStatus] = useState('');
  const [favoritesOnly, setFavoritesOnly] = useState(false);
  const [favoriteSchoolIds, setFavoriteSchoolIds] = useState<number[]>([]);
  const [mapMaximized, setMapMaximized] = useState(false);
  const [conferenceRows, setConferenceRows] = useState<ConferenceSummary[]>([]);
  const [homeWidgets, setHomeWidgets] = useState<CmsWidgetPlacement[]>([]);
  const disciplineMenuRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    apiFetch<FilterOptions>('/filters/')
      .then(setFilters)
      .catch((error) => console.error(error));
  }, []);

  useEffect(() => {
    apiFetch<ConferenceSummary[]>('/conferences/')
      .then(setConferenceRows)
      .catch((error) => console.error(error));
  }, []);

  useEffect(() => {
    apiFetch<CmsWidgetPlacement[]>('/cms/widgets/?route_path=/')
      .then(setHomeWidgets)
      .catch(() => setHomeWidgets([]));
  }, []);

  useEffect(() => {
    if (detailSchoolId === null) {
      return;
    }

    let cancelled = false;
    setDetailLoading(true);
    setDetailError('');

    apiFetch<SchoolDetail>(`/schools/${detailSchoolId}/`)
      .then((school) => {
        if (cancelled) return;
        setDetailSchool(school);
      })
      .catch((error: Error) => {
        if (cancelled) return;
        setDetailError(error.message || 'Could not load school details.');
      })
      .finally(() => {
        if (cancelled) return;
        setDetailLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [detailSchoolId]);

  useEffect(() => {
    const onEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        if (mapMaximized) {
          setMapMaximized(false);
          return;
        }
        setDetailSchoolId(null);
        setDetailSchool(null);
        setDetailError('');
      }
    };
    window.addEventListener('keydown', onEscape);
    return () => window.removeEventListener('keydown', onEscape);
  }, [mapMaximized]);

  useEffect(() => {
    document.body.style.overflow = mapMaximized ? 'hidden' : '';
    return () => {
      document.body.style.overflow = '';
    };
  }, [mapMaximized]);

  const queryString = useMemo(() => {
    const params = new URLSearchParams();
    if (q) params.set('q', q);
    if (teamType) params.set('team_type', teamType);
    if (conference) params.set('conference', conference);
    if (state) params.set('state', state);
    if (disciplines.length) params.set('disciplines', disciplines.join(','));
    if (lat !== null && lng !== null) {
      params.set('lat', String(lat));
      params.set('lng', String(lng));
    }
    if (radius !== null) {
      params.set('radius', String(radius));
    }
    return params.toString();
  }, [q, teamType, conference, state, disciplines, lat, lng, radius]);

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
    });
  };

  const clearFilters = () => {
    setQ('');
    setTeamType('');
    setConference('');
    setState('');
    setDisciplines([]);
    setLat(null);
    setLng(null);
    setRadius(null);
    setPopupSchoolId(null);
  };

  const openSchoolDetail = (schoolId: number) => {
    setDetailSchoolId(schoolId);
    setDetailSchool(null);
    setDetailError('');
    setLogoLoadError(false);
  };

  const closeSchoolDetail = () => {
    setDetailSchoolId(null);
    setDetailSchool(null);
    setDetailError('');
    setLogoLoadError(false);
  };

  const loadFavoriteSchoolIds = async () => {
    const token = localStorage.getItem('skyway_access');
    if (!token) {
      window.location.href = '/auth-access';
      return;
    }
    const response = await fetch(`${API_BASE}/favorites/`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    if (response.status === 401) {
      localStorage.removeItem('skyway_access');
      localStorage.removeItem('skyway_refresh');
      localStorage.removeItem('skyway_user');
      window.location.href = '/auth-access';
      return;
    }
    if (!response.ok) {
      const data = await response.json().catch(() => ({}));
      throw new Error(data?.detail || 'Could not load favorites.');
    }
    const data = await response.json();
    const ids = Array.isArray(data)
      ? data
          .map((favorite) => Number(favorite?.school?.id))
          .filter((id) => Number.isFinite(id))
      : [];
    setFavoriteSchoolIds(ids);
  };

  const toggleFavoritesOnMap = async () => {
    if (favoritesOnly) {
      setFavoritesOnly(false);
      setFavoriteStatus('');
      return;
    }
    setFavoriteStatus('');
    try {
      await loadFavoriteSchoolIds();
      setFavoritesOnly(true);
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Could not load favorites.';
      setFavoriteStatus(message);
    }
  };

  const addToFavorites = async (schoolId: number) => {
    const token = localStorage.getItem('skyway_access');
    if (!token) {
      window.location.href = `/auth-access?school_id=${schoolId}`;
      return;
    }

    setFavoriteStatus('');
    try {
      const response = await fetch(`${API_BASE}/favorites/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ school_id: schoolId, visibility: 'private' }),
      });
      if (response.status === 401) {
        localStorage.removeItem('skyway_access');
        localStorage.removeItem('skyway_refresh');
        window.location.href = `/auth-access?school_id=${schoolId}`;
        return;
      }
      if (!response.ok) {
        const data = await response.json().catch(() => ({}));
        setFavoriteStatus(data?.detail || 'Could not add favorite right now.');
        return;
      }
      window.location.href = '/favorites';
    } catch {
      setFavoriteStatus('Could not reach the server. Try again.');
    }
  };

  const resolvedLogoUrl = useMemo(() => {
    if (!detailSchool?.logo || logoLoadError) {
      return '';
    }
    if (detailSchool.logo.startsWith('http://') || detailSchool.logo.startsWith('https://')) {
      return detailSchool.logo;
    }
    if (detailSchool.logo.startsWith('/')) {
      const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000/api';
      const apiOrigin = apiBase.replace(/\/api\/?$/, '');
      return `${apiOrigin}${detailSchool.logo}`;
    }
    return detailSchool.logo;
  }, [detailSchool, logoLoadError]);

  const detailAddress = useMemo(() => {
    if (!detailSchool) return '';
    const composed = [
      detailSchool.street_address,
      [detailSchool.city, detailSchool.state].filter(Boolean).join(', '),
      detailSchool.zip_code,
    ]
      .filter((value) => Boolean(value))
      .join(' ')
      .trim();
    return detailSchool.address_complete || composed || 'No address provided';
  }, [detailSchool]);

  const mapSchools = useMemo(() => {
    if (!favoritesOnly) {
      return schools;
    }
    const idSet = new Set(favoriteSchoolIds);
    return schools.filter((school) => idSet.has(school.id));
  }, [schools, favoritesOnly, favoriteSchoolIds]);

  const mapPinCount = useMemo(
    () =>
      mapSchools.filter((school) => {
        if (school.latitude === null || school.longitude === null) {
          return false;
        }
        const lat = Number(school.latitude);
        const lng = Number(school.longitude);
        return Number.isFinite(lat) && Number.isFinite(lng) && lat >= -90 && lat <= 90 && lng >= -180 && lng <= 180;
      }).length,
    [mapSchools]
  );

  return (
    <>
      {homeWidgets.length ? (
        <section className='cms-home-widgets'>
          {homeWidgets.map((placement) => (
            <article key={placement.id} className='panel cms-home-widget'>
              {placement.widget.title ? <h2>{placement.widget.title}</h2> : null}
              <CmsBlocks blocks={placement.widget.body || []} />
            </article>
          ))}
        </section>
      ) : null}
      <div className={`map-first-shell ${mapMaximized ? 'map-maximized' : ''}`}>
      <div className='map-canvas'>
        {mapMaximized && (
          <button
            type='button'
            className='map-max-close'
            onClick={() => setMapMaximized(false)}
          >
            X Minimize map
          </button>
        )}
        <SchoolMap
          schools={mapSchools}
          userLocation={lat !== null && lng !== null ? [lat, lng] : null}
          radiusMiles={radius}
          popupSchoolId={popupSchoolId}
          popupRequestId={popupRequestId}
          mapHeight='100%'
          onRequestSchoolDetail={openSchoolDetail}
          onUseMyLocation={detectLocation}
          onToggleMaximize={() => setMapMaximized((prev) => !prev)}
          isMaximized={mapMaximized}
        />

        <section className='floating-toolbar'>
          <div className='filters map-first-filters'>
            <label className='filter-field'>
              <span>Keyword</span>
              <input
                placeholder='School, city, state'
                value={q}
                onChange={(e) => setQ(e.target.value)}
              />
            </label>
            <label className='filter-field'>
              <span>Team Type</span>
              <select value={teamType} onChange={(e) => setTeamType(e.target.value)}>
                <option value=''>All Team Types</option>
                {filters?.team_types.map((option) => (
                  <option key={option} value={option}>
                    {option}
                  </option>
                ))}
              </select>
            </label>
            <label className='filter-field'>
              <span>USAC Conference</span>
              <select value={conference} onChange={(e) => setConference(e.target.value)}>
                <option value=''>All USAC Conferences</option>
                {filters?.conferences.map((option) => (
                  <option key={option} value={option}>
                    {option}
                  </option>
                ))}
              </select>
            </label>
            <label className='filter-field'>
              <span>State</span>
              <select value={state} onChange={(e) => setState(e.target.value)}>
                <option value=''>All States</option>
                {filters?.states.map((option) => (
                  <option key={option} value={option}>
                    {option}
                  </option>
                ))}
              </select>
            </label>
            <div className='filter-field'>
              <span>Disciplines</span>
              <div className='multi-dropdown' ref={disciplineMenuRef}>
                <button
                  type='button'
                  className='multi-dropdown-trigger'
                  onClick={() => setDisciplineMenuOpen((prev) => !prev)}
                >
                  {disciplines.length > 0
                    ? `Selected (${disciplines.length})`
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
          </div>

          <div className='floating-actions'>
            <span className='sort-label'>Pins visible: {mapPinCount}</span>
            <div className='floating-actions-right'>
              <button type='button' className='filter-link' onClick={toggleFavoritesOnMap}>
                {favoritesOnly ? 'Show All Schools' : 'Show My Favorites'}
              </button>
              <button type='button' className='filter-link' onClick={clearFilters}>
                Clear Filters
              </button>
            </div>
          </div>
        </section>
      </div>

      <aside className={`results-drawer ${resultsOpen ? 'open' : 'collapsed'}`}>
        <div className='results-head'>
          <strong>Results ({schools.length})</strong>
          <button
            type='button'
            className='drawer-toggle'
            onClick={() => setResultsOpen((prev) => !prev)}
          >
            {resultsOpen ? 'Hide' : 'Show'}
          </button>
        </div>

        {resultsOpen && (
          <div className='results-scroll'>
            {favoriteStatus && <p className='auth-error'>{favoriteStatus}</p>}
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
                <button
                  type='button'
                  className='list-card-link'
                  onClick={() => openSchoolDetail(school.id)}
                >
                  View details
                </button>
                <br />
                <button
                  type='button'
                  className='list-card-link'
                  onClick={() => addToFavorites(school.id)}
                >
                  Add to favorites
                </button>
              </article>
            ))}
            {schools.length === 0 && <p>No schools matched your current filters.</p>}
          </div>
        )}
      </aside>
      <button
        type='button'
        className='mobile-drawer-button'
        onClick={() => setResultsOpen((prev) => !prev)}
      >
        {resultsOpen ? 'Hide Results' : `Show Results (${schools.length})`}
      </button>
      {detailSchoolId !== null && (
        <div className='school-overlay-backdrop' onClick={closeSchoolDetail}>
          <section className='school-overlay-panel' onClick={(event) => event.stopPropagation()}>
            <div className='school-overlay-head'>
              <strong>School details</strong>
              <button type='button' className='drawer-toggle' onClick={closeSchoolDetail}>
                Close
              </button>
            </div>
            <div className='school-overlay-content'>
              {detailLoading && <p>Loading details...</p>}
              {!detailLoading && detailError && <p>{detailError}</p>}
              {!detailLoading && !detailError && detailSchool && (
                <>
                  <div className='school-overlay-top'>
                    <div className='school-overlay-logo-wrap'>
                      {resolvedLogoUrl ? (
                        <img
                          src={resolvedLogoUrl}
                          alt={`${detailSchool.name} logo`}
                          className='school-overlay-logo'
                          onError={() => setLogoLoadError(true)}
                        />
                      ) : (
                        <div className='school-overlay-logo-placeholder'>
                          {detailSchool.name.slice(0, 2).toUpperCase()}
                        </div>
                      )}
                    </div>
                    <div>
                      <h3>{detailSchool.name}</h3>
                      <p>{[detailSchool.city, detailSchool.state].filter(Boolean).join(', ') || 'City/State N/A'}</p>
                    </div>
                  </div>
                  <p>Conference: {detailSchool.conference || 'N/A'}</p>
                  <p>Team Type: {detailSchool.team_type || 'N/A'}</p>
                  <p>Head Coach: {detailSchool.head_coach || 'N/A'}</p>
                  <p>Address: {detailAddress}</p>
                  <p>Geocode Status: {detailSchool.geocode_status || 'N/A'}</p>
                  <p>Institution Control: {formatProfileValue(detailSchool.institution_control)}</p>
                  <p>Institution Level: {formatProfileValue(detailSchool.institution_level)}</p>
                  <p>Locale: {detailSchool.locale || 'N/A'}</p>
                  <p>Cycling Program Status: {detailSchool.cycling_program_status || 'N/A'}</p>
                  <p>Enrollment: {detailSchool.enrollment || 'N/A'}</p>
                  <p>Acceptance Rate: {detailSchool.acceptance_rate || 'N/A'}</p>
                  <p>Graduation Rate: {detailSchool.graduation_rate || 'N/A'}</p>
                  <div className='discipline-chips'>
                    {getDisciplineLabels(detailSchool).length > 0 ? (
                      getDisciplineLabels(detailSchool).map((label) => (
                        <span key={label} className='chip'>{label}</span>
                      ))
                    ) : (
                      <span className='chip muted-chip'>No discipline data</span>
                    )}
                  </div>
                  <div className='school-overlay-links'>
                    {detailSchool.school_website && (
                      <a href={detailSchool.school_website} target='_blank' rel='noreferrer'>School website</a>
                    )}
                    {detailSchool.athletic_dept_website && (
                      <a href={detailSchool.athletic_dept_website} target='_blank' rel='noreferrer'>Athletics</a>
                    )}
                    {detailSchool.cycling_website && (
                      <a href={detailSchool.cycling_website} target='_blank' rel='noreferrer'>Cycling</a>
                    )}
                  </div>
                </>
              )}
            </div>
          </section>
        </div>
      )}
      </div>
      <section className='panel page-panel conference-table-panel'>
        <h2>Cycling Conferences</h2>
        <div className='conference-table-wrap'>
          <table className='conference-table'>
            <thead>
              <tr>
                <th>Long Name</th>
                <th>Acronym</th>
                <th>Teams</th>
                <th>Description</th>
              </tr>
            </thead>
            <tbody>
              {conferenceRows.map((conference) => (
                <tr key={conference.id}>
                  <td>{conference.long_name || conference.name}</td>
                  <td>{conference.acronym || 'N/A'}</td>
                  <td>{conference.team_count ?? 0}</td>
                  <td>{conference.description || 'No description provided.'}</td>
                </tr>
              ))}
              {conferenceRows.length === 0 && (
                <tr>
                  <td colSpan={4}>No conferences available.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>
    </>
  );
}
