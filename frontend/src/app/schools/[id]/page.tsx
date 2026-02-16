import Link from 'next/link';

import { apiFetch } from '@/lib/api';
import { getDisciplineLabels } from '@/lib/disciplines';
import type { SchoolDetail } from '@/lib/types';

export default async function SchoolDetailPage({ params }: { params: { id: string } }) {
  const school = await apiFetch<SchoolDetail>(`/schools/${params.id}/`);
  const disciplines = getDisciplineLabels(school);

  return (
    <div className='panel'>
      <Link href='/'>Back to search</Link>
      <h1>{school.name}</h1>
      <p>
        {school.city}, {school.state} {school.team_type && `• ${school.team_type}`}
      </p>

      <div className='detail-grid'>
        <div>
          <h3>Program</h3>
          <p>Conference: {school.conference || 'N/A'}</p>
          <p>Roster Male: {school.roster_male ?? 'N/A'}</p>
          <p>Roster Female: {school.roster_female ?? 'N/A'}</p>
          <p>Head Coach: {school.head_coach || 'N/A'}</p>
          <p>Program Strengths: {school.program_strengths || 'N/A'}</p>
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
          <h3>Academics & Cost</h3>
          <p>Avg Cost: {school.avg_cost || 'N/A'}</p>
          <p>Enrollment: {school.enrollment || 'N/A'}</p>
          <p>Acceptance Rate: {school.acceptance_rate || 'N/A'}</p>
          <p>Graduation Rate: {school.graduation_rate || 'N/A'}</p>
        </div>

        <div>
          <h3>Links</h3>
          {school.school_website && <p><a href={school.school_website} target='_blank' rel='noreferrer'>School Website</a></p>}
          {school.athletic_dept_website && <p><a href={school.athletic_dept_website} target='_blank' rel='noreferrer'>Athletic Dept</a></p>}
          {school.cycling_website && <p><a href={school.cycling_website} target='_blank' rel='noreferrer'>Cycling Program</a></p>}
          {school.instagram && <p><a href={school.instagram} target='_blank' rel='noreferrer'>Instagram</a></p>}
          {school.facebook && <p><a href={school.facebook} target='_blank' rel='noreferrer'>Facebook</a></p>}
          {school.twitter && <p><a href={school.twitter} target='_blank' rel='noreferrer'>Twitter</a></p>}
        </div>
      </div>
    </div>
  );
}
