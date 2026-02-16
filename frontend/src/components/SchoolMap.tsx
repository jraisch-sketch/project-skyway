'use client';

import { useEffect, useRef } from 'react';
import { Circle, MapContainer, Marker, Popup, TileLayer, useMap } from 'react-leaflet';
import L from 'leaflet';
import Link from 'next/link';

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
};

function FitMapToResults({
  points,
  includeUser,
}: {
  points: Array<[number, number]>;
  includeUser: [number, number] | null;
}) {
  const map = useMap();

  useEffect(() => {
    const boundsPoints = includeUser ? [...points, includeUser] : points;
    if (boundsPoints.length === 0) {
      return;
    }
    if (boundsPoints.length === 1) {
      map.setView(boundsPoints[0], 9, { animate: false });
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
}: SchoolMapProps) {
  const markerRefs = useRef<Record<number, L.Marker>>({});
  const schoolPoints = schools
    .filter((school) => school.latitude !== null && school.longitude !== null)
    .map((school) => [school.latitude as number, school.longitude as number] as [number, number]);

  const visibleConferences = Array.from(
    new Set(schools.map((school) => school.conference).filter((conference) => Boolean(conference)))
  ).sort();

  const centeredSchool = schools.find(
    (school) => school.latitude !== null && school.longitude !== null
  );
  const center: [number, number] = userLocation
    ? userLocation
    : centeredSchool
      ? [centeredSchool.latitude as number, centeredSchool.longitude as number]
      : [41.2, -98.5];
  const zoom = userLocation ? 8 : 3;
  const mapKey = `${center[0]}-${center[1]}-${zoom}`;

  return (
    <div className='map-wrap'>
      <MapContainer key={mapKey} center={center} zoom={zoom} scrollWheelZoom style={{ height: 500, width: '100%' }}>
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
        {schools
          .filter((school) => school.latitude !== null && school.longitude !== null)
          .map((school) => (
            <Marker
              key={school.id}
              position={[school.latitude as number, school.longitude as number]}
              icon={conferenceMarkerIcon(colorForConference(school.conference))}
              ref={(marker) => {
                if (marker) {
                  markerRefs.current[school.id] = marker;
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
              <Link href={`/schools/${school.id}`}>View details</Link>
            </Popup>
          </Marker>
          ))}
      </MapContainer>
      {visibleConferences.length > 0 && (
        <div className='conference-legend'>
          <strong>Conference Colors</strong>
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
