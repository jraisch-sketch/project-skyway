import Link from 'next/link';
import { notFound } from 'next/navigation';
import type { Metadata } from 'next';

import { getDisciplineLabels } from '@/lib/disciplines';
import { serverApiFetch } from '@/lib/serverApi';
import type { SchoolDetail } from '@/lib/types';

type SchoolProgramPageProps = {
  params: {
    id: string;
    schoolSlug: string;
  };
};

function formatProfileValue(value: string): string {
  if (!value) return 'N/A';
  return value
    .replaceAll('_', ' ')
    .replace(/\b\w/g, (ch) => ch.toUpperCase());
}

async function fetchSchool(id: string): Promise<SchoolDetail | null> {
  return serverApiFetch<SchoolDetail>(`/schools/${id}/`);
}

export async function generateMetadata({ params }: SchoolProgramPageProps): Promise<Metadata> {
  const school = await fetchSchool(params.id);
  if (!school) {
    return {
      title: 'School Cycling Program',
      description: 'College cycling program profile.',
    };
  }

  return {
    title: `${school.name} Cycling Program`,
    description: `Learn about ${school.name} cycling program details, conference, disciplines, and school profile.`,
  };
}

export default async function SchoolProgramPage({ params }: SchoolProgramPageProps) {
  const school = await fetchSchool(params.id);
  if (!school) {
    notFound();
  }

  const disciplines = getDisciplineLabels(school);
  const address =
    school.address_complete ||
    [school.street_address, school.city, school.state, school.zip_code].filter(Boolean).join(', ') ||
    'No address provided';

  return (
    <section className='panel page-panel'>
      <h1>{school.name} Cycling Program</h1>
      <p>
        {[school.city, school.state].filter(Boolean).join(', ') || 'Location N/A'}
        {school.team_type ? ` • ${school.team_type}` : ''}
      </p>

      <div className='detail-grid'>
        <div>
          <h3>Program Overview</h3>
          <p>Conference: {school.conference || 'N/A'}</p>
          <p>Cycling Program Status: {school.cycling_program_status || 'N/A'}</p>
          <p>Institution Control: {formatProfileValue(school.institution_control)}</p>
          <p>Institution Level: {formatProfileValue(school.institution_level)}</p>
          <p>Locale: {school.locale || 'N/A'}</p>
          <p>Head Coach: {school.head_coach || 'N/A'}</p>
          <p>Geocode Status: {school.geocode_status || 'N/A'}</p>
          <p>Address: {address}</p>
          <p>Enrollment: {school.enrollment || 'N/A'}</p>
          <p>Graduation Rate: {school.graduation_rate || 'N/A'}</p>
        </div>

        <div>
          <h3>Disciplines</h3>
          <div className='discipline-chips'>
            {disciplines.length > 0 ? (
              disciplines.map((label) => (
                <span key={label} className='chip'>{label}</span>
              ))
            ) : (
              <span className='chip muted-chip'>No discipline data</span>
            )}
          </div>
        </div>

        <div>
          <h3>School Links</h3>
          {school.school_website && <p><a href={school.school_website} target='_blank' rel='noreferrer'>School Website</a></p>}
          {school.athletic_dept_website && <p><a href={school.athletic_dept_website} target='_blank' rel='noreferrer'>Athletic Department</a></p>}
          {school.cycling_website && <p><a href={school.cycling_website} target='_blank' rel='noreferrer'>Cycling Program Site</a></p>}
        </div>
      </div>

      <p className='auth-note'>
        <Link href='/schools/table-of-contents'>Back to School Table of Contents</Link>
      </p>
    </section>
  );
}
