'use client';

import { useEffect, useMemo, useRef } from 'react';
import { Circle, MapContainer, Marker, Popup, TileLayer, ZoomControl, useMap } from 'react-leaflet';
import L from 'leaflet';

import { colorForConference, CONFERENCE_COLORS } from '@/lib/conferenceColors';
import type { School } from '@/lib/types';

const userMarkerIcon = L.icon({
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
});

const markerCache = new Map<string, L.Icon>();
type MappableSchool = {
  school: School;
  lat: number;
  lng: number;
};

function conferenceMarkerIcon(color: string): L.Icon {
  if (markerCache.has(color)) {
    return markerCache.get(color) as L.Icon;
  }

  const svg = `
    <svg xmlns="http://www.w3.org/2000/svg" width="13" height="21" viewBox="0 0 26 42">
      <path d="M13 1C6.373 1 1 6.373 1 13c0 8.967 12 28 12 28s12-19.033 12-28C25 6.373 19.627 1 13 1z" fill="${color}" stroke="#ffffff" stroke-width="1.8"/>
      <circle cx="13" cy="13" r="3.8" fill="#ffffff"/>
    </svg>
  `.trim();
  const iconUrl = `data:image/svg+xml;charset=UTF-8,${encodeURIComponent(svg)}`;
  const icon = L.icon({
    iconUrl,
    iconSize: [13, 21],
    iconAnchor: [6, 20],
    popupAnchor: [0, -18],
  });
  markerCache.set(color, icon);
  return icon;
}

type SchoolMapProps = {
  schools: School[];
  userLocation?: [number, number] | null;
  radiusMiles?: number | null;
  popupSchoolId?: number | null;
  popupRequestId?: number;
  mapHeight?: number | string;
  onRequestSchoolDetail?: (schoolId: number) => void;
  onUseMyLocation?: () => void;
  onToggleMaximize?: () => void;
  isMaximized?: boolean;
};

function FitMapToResults({
  points,
  includeUser,
}: {
  points: Array<[number, number]>;
  includeUser: [number, number] | null;
}) {
  const map = useMap();
  const initialFitDoneRef = useRef(false);

  useEffect(() => {
    const boundsPoints = includeUser ? [...points, includeUser] : points;
    if (boundsPoints.length === 0) {
      return;
    }
    if (boundsPoints.length === 1) {
      map.setView(boundsPoints[0], 9, { animate: false });
      return;
    }

    if (!initialFitDoneRef.current) {
      // On first load, bias the fitted view slightly east so USA land mass is centered better.
      map.fitBounds(boundsPoints, {
        paddingTopLeft: [210, 28],
        paddingBottomRight: [20, 28],
        maxZoom: 9,
        animate: false,
      });
      initialFitDoneRef.current = true;
      return;
    }

    map.fitBounds(boundsPoints, { padding: [28, 28], maxZoom: 9, animate: false });
  }, [map, points, includeUser]);

  return null;
}

function OpenSchoolPopup({
  schools,
  popupSchoolId,
  popupRequestId,
  markerRefs,
}: {
  schools: School[];
  popupSchoolId: number | null;
  popupRequestId: number;
  markerRefs: React.MutableRefObject<Record<number, L.Marker>>;
}) {
  const map = useMap();

  useEffect(() => {
    if (!popupSchoolId) {
      return;
    }
    const school = schools.find((item) => item.id === popupSchoolId);
    if (!school || school.latitude === null || school.longitude === null) {
      return;
    }
    const target: [number, number] = [school.latitude, school.longitude];
    map.setView(target, Math.max(map.getZoom(), 8), { animate: true });
    const marker = markerRefs.current[popupSchoolId];
    if (marker) {
      marker.openPopup();
    }
  }, [map, schools, popupSchoolId, popupRequestId, markerRefs]);

  return null;
}

export default function SchoolMap({
  schools,
  userLocation = null,
  radiusMiles = null,
  popupSchoolId = null,
  popupRequestId = 0,
  mapHeight = 500,
  onRequestSchoolDetail,
  onUseMyLocation,
  onToggleMaximize,
  isMaximized = false,
}: SchoolMapProps) {
  const markerRefs = useRef<Record<number, L.Marker>>({});
  const mappableSchools = useMemo(
    () =>
      schools
        .map((school) => {
          if (school.latitude === null || school.longitude === null) {
            return null;
          }
          const lat = Number(school.latitude);
          const lng = Number(school.longitude);
          if (!Number.isFinite(lat) || !Number.isFinite(lng)) {
            return null;
          }
          if (lat < -90 || lat > 90 || lng < -180 || lng > 180) {
            return null;
          }
          return { school, lat, lng } as MappableSchool;
        })
        .filter((entry): entry is MappableSchool => entry !== null),
    [schools]
  );
  const schoolPoints = useMemo(
    () => mappableSchools.map((entry) => [entry.lat, entry.lng] as [number, number]),
    [mappableSchools]
  );

  const visibleConferences = Array.from(
    new Set(schools.map((school) => school.conference).filter((conference) => Boolean(conference)))
  ).sort();

  const center: [number, number] = userLocation
    ? userLocation
    : mappableSchools.length > 0
      ? [mappableSchools[0].lat, mappableSchools[0].lng]
      : [41.2, -98.5];
  const zoom = userLocation ? 8 : 3;
  const mapKey = `${center[0]}-${center[1]}-${zoom}`;

  return (
    <div className='map-wrap'>
      <MapContainer key={mapKey} center={center} zoom={zoom} scrollWheelZoom zoomControl={false} style={{ height: mapHeight, width: '100%' }}>
        <ZoomControl position='bottomright' />
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url='https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png'
        />
        {userLocation && (
          <>
            <Marker position={userLocation} icon={userMarkerIcon}>
              <Popup>Your Location</Popup>
            </Marker>
            {radiusMiles && radiusMiles > 0 && (
              <Circle
                center={userLocation}
                radius={radiusMiles * 1609.34}
                pathOptions={{ color: '#0f6cbf', fillColor: '#0f6cbf', fillOpacity: 0.1 }}
              />
            )}
          </>
        )}
        {schoolPoints.length > 0 && (
          <FitMapToResults points={schoolPoints} includeUser={userLocation} />
        )}
        {popupSchoolId && (
          <OpenSchoolPopup
            schools={schools}
            popupSchoolId={popupSchoolId}
            popupRequestId={popupRequestId}
            markerRefs={markerRefs}
          />
        )}
        {mappableSchools.map(({ school, lat, lng }) => (
          <Marker
            key={`school-${school.id}`}
            position={[lat, lng]}
            icon={conferenceMarkerIcon(colorForConference(school.conference))}
            ref={(leafletMarker) => {
              if (leafletMarker) {
                markerRefs.current[school.id] = leafletMarker;
              } else {
                delete markerRefs.current[school.id];
              }
            }}
          >
            <Popup>
              <strong>{school.name}</strong>
              <br />
              Team Type: {school.team_type || 'N/A'}
              <br />
              Conference: {school.conference || 'N/A'}
              <br />
              <button
                type='button'
                className='list-card-link'
                onClick={() => onRequestSchoolDetail?.(school.id)}
              >
                View details
              </button>
            </Popup>
          </Marker>
        ))}
      </MapContainer>
      {onUseMyLocation && (
        <button
          type='button'
          className='map-locate-control'
          onClick={onUseMyLocation}
          title='Use My Location'
          aria-label='Use My Location'
        >
          <svg viewBox='0 0 24 24' aria-hidden='true'>
            <circle cx='12' cy='12' r='4.2' />
            <path d='M12 2v4M12 18v4M2 12h4M18 12h4' />
          </svg>
        </button>
      )}
      {onToggleMaximize && (
        <button
          type='button'
          className='map-maximize-control'
          onClick={onToggleMaximize}
          title={isMaximized ? 'Minimize Map' : 'Maximize Map'}
          aria-label={isMaximized ? 'Minimize Map' : 'Maximize Map'}
        >
          {isMaximized ? '−' : '+'}
        </button>
      )}
      {visibleConferences.length > 0 && (
        <div className='conference-legend'>
          <strong>USAC Conference Colors</strong>
          {visibleConferences.map((conference) => (
            <div key={conference} className='legend-item'>
              <span
                className='legend-swatch'
                style={{ backgroundColor: CONFERENCE_COLORS[conference] || '#7A8A99' }}
              />
              <span>{conference}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
