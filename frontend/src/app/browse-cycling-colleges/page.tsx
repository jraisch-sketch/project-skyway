'use client';

import dynamic from 'next/dynamic';
import Link from 'next/link';
import { useEffect, useMemo, useRef, useState } from 'react';

import { apiFetch } from '@/lib/api';
import { DISCIPLINE_LABELS, getDisciplineLabels } from '@/lib/disciplines';
import { slugify } from '@/lib/seo';
import type { FilterOptions, School, SchoolDetail } from '@/lib/types';

const SchoolMap = dynamic(() => import('@/components/SchoolMap'), { ssr: false });
const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000/api';

type ActiveTab = 'list' | 'map';

function formatProfileValue(value: string): string {
  if (!value) return 'N/A';
  return value
    .replaceAll('_', ' ')
    .replace(/\b\w/g, (ch) => ch.toUpperCase());
}

export default function BrowseCyclingCollegesPage() {
  const [schools, setSchools] = useState<School[]>([]);
  const [filters, setFilters] = useState<FilterOptions | null>(null);
  const [activeTab, setActiveTab] = useState<ActiveTab>('list');
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
  const [detailSchoolId, setDetailSchoolId] = useState<number | null>(null);
  const [detailSchool, setDetailSchool] = useState<SchoolDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [detailError, setDetailError] = useState('');
  const [logoLoadError, setLogoLoadError] = useState(false);
  const [favoriteStatus, setFavoriteStatus] = useState('');
  const [favoritesOnly, setFavoritesOnly] = useState(false);
  const [favoriteSchoolIds, setFavoriteSchoolIds] = useState<number[]>([]);
  const disciplineMenuRef = useRef<HTMLDivElement | null>(null);
  const disciplineChoices = useMemo(
    () => filters?.disciplines?.filter((key) => key in DISCIPLINE_LABELS) ?? Object.keys(DISCIPLINE_LABELS),
    [filters],
  );

  useEffect(() => {
    apiFetch<FilterOptions>('/filters/')
      .then(setFilters)
      .catch((error) => console.error(error));
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
        setDetailSchoolId(null);
        setDetailSchool(null);
        setDetailError('');
      }
    };
    window.addEventListener('keydown', onEscape);
    return () => window.removeEventListener('keydown', onEscape);
  }, []);

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

  useEffect(() => {
    setDisciplines((current) => current.filter((key) => disciplineChoices.includes(key)));
  }, [disciplineChoices]);

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

  const detailDisciplineLabels = useMemo(() => {
    if (!detailSchool) return [];
    return getDisciplineLabels(detailSchool);
  }, [detailSchool]);

  const tabSchools = useMemo(() => {
    if (!favoritesOnly) {
      return schools;
    }
    const idSet = new Set(favoriteSchoolIds);
    return schools.filter((school) => idSet.has(school.id));
  }, [schools, favoritesOnly, favoriteSchoolIds]);

  const mapPinCount = useMemo(
    () =>
      tabSchools.filter((school) => {
        if (school.latitude === null || school.longitude === null) {
          return false;
        }
        const schoolLat = Number(school.latitude);
        const schoolLng = Number(school.longitude);
        return Number.isFinite(schoolLat) && Number.isFinite(schoolLng) && schoolLat >= -90 && schoolLat <= 90 && schoolLng >= -180 && schoolLng <= 180;
      }).length,
    [tabSchools]
  );

  return (
    <section className='browse-cycling-shell'>
      <aside className='browse-cycling-nav panel'>
        <h1>Browse Cycling Colleges</h1>
        <p>Filter schools and switch between list and map views.</p>

        <label className='filter-field keyword-filter'>
          <span>Keyword Search</span>
          <input
            placeholder='School, city, state'
            value={q}
            onChange={(event) => setQ(event.target.value)}
          />
        </label>

        <div className='browse-filters'>
          <label className='filter-field'>
            <span>Team Type</span>
            <select value={teamType} onChange={(event) => setTeamType(event.target.value)}>
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
            <select value={conference} onChange={(event) => setConference(event.target.value)}>
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
            <select value={state} onChange={(event) => setState(event.target.value)}>
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

        <div className='browse-nav-actions'>
          <button type='button' className='filter-link' onClick={detectLocation}>
            Use my location
          </button>
          <button type='button' className='filter-link' onClick={toggleFavoritesOnMap}>
            {favoritesOnly ? 'Show All Schools' : 'Show My Favorites'}
          </button>
          <button type='button' className='filter-link' onClick={clearFilters}>
            Clear Filters
          </button>
          {favoriteStatus && <p className='auth-error'>{favoriteStatus}</p>}
        </div>
      </aside>

      <div className='browse-cycling-content panel'>
        <div className='browse-tabs'>
          <button
            type='button'
            className={`browse-tab ${activeTab === 'list' ? 'active' : ''}`}
            onClick={() => setActiveTab('list')}
          >
            List View ({tabSchools.length})
          </button>
          <button
            type='button'
            className={`browse-tab ${activeTab === 'map' ? 'active' : ''}`}
            onClick={() => setActiveTab('map')}
          >
            Map View (Pins {mapPinCount})
          </button>
        </div>

        {activeTab === 'list' ? (
          <div className='browse-tab-panel'>
            <div className='results-scroll browse-results-scroll'>
              {tabSchools.map((school) => (
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
                      setActiveTab('map');
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
              {tabSchools.length === 0 && <p>No schools matched your current filters.</p>}
            </div>
          </div>
        ) : (
          <div className='browse-tab-panel browse-map-panel'>
            <SchoolMap
              schools={tabSchools}
              userLocation={lat !== null && lng !== null ? [lat, lng] : null}
              radiusMiles={radius}
              popupSchoolId={popupSchoolId}
              popupRequestId={popupRequestId}
              mapHeight='68vh'
              onRequestSchoolDetail={openSchoolDetail}
              onUseMyLocation={detectLocation}
            />
          </div>
        )}
      </div>

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
                  <table className='school-overlay-table'>
                    <tbody>
                      <tr>
                        <th>Conference</th>
                        <td>{detailSchool.conference || 'N/A'}</td>
                      </tr>
                      <tr>
                        <th>Team Type</th>
                        <td>{detailSchool.team_type || 'N/A'}</td>
                      </tr>
                      <tr>
                        <th>Cycling Program Status</th>
                        <td>{detailSchool.cycling_program_status || 'N/A'}</td>
                      </tr>
                      <tr>
                        <th>Address</th>
                        <td>{detailAddress}</td>
                      </tr>
                      <tr>
                        <th>Institution Control</th>
                        <td>{formatProfileValue(detailSchool.institution_control)}</td>
                      </tr>
                      <tr>
                        <th>Institution Level</th>
                        <td>{formatProfileValue(detailSchool.institution_level)}</td>
                      </tr>
                      <tr>
                        <th>Locale</th>
                        <td>{detailSchool.locale || 'N/A'}</td>
                      </tr>
                      <tr>
                        <th>Enrollment</th>
                        <td>{detailSchool.enrollment || 'N/A'}</td>
                      </tr>
                      <tr>
                        <th>Acceptance Rate</th>
                        <td>{detailSchool.acceptance_rate || 'N/A'}</td>
                      </tr>
                      <tr>
                        <th>Graduation Rate</th>
                        <td>{detailSchool.graduation_rate || 'N/A'}</td>
                      </tr>
                      <tr>
                        <th>Disciplines</th>
                        <td>
                          <div className='discipline-chips'>
                            {detailDisciplineLabels.length > 0 ? (
                              detailDisciplineLabels.map((label) => (
                                <span key={label} className='chip'>{label}</span>
                              ))
                            ) : (
                              <span className='chip muted-chip'>No discipline data</span>
                            )}
                          </div>
                        </td>
                      </tr>
                    </tbody>
                  </table>
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
                    <Link href={`/schools/cycling-program/${detailSchool.id}/${slugify(detailSchool.name)}`}>
                      View full school details
                    </Link>
                  </div>
                </>
              )}
            </div>
          </section>
        </div>
      )}
    </section>
  );
}
