import Link from 'next/link';
import { notFound } from 'next/navigation';
import type { Metadata } from 'next';

import { slugify } from '@/lib/seo';
import { serverApiFetch } from '@/lib/serverApi';
import type { School } from '@/lib/types';

type TeamTypePageProps = {
  params: {
    teamTypeSlug: string;
  };
};

const TEAM_TYPE_MAP: Record<string, string> = {
  varsity: 'Varsity',
  club: 'Club',
};

export async function generateMetadata({ params }: TeamTypePageProps): Promise<Metadata> {
  const teamType = TEAM_TYPE_MAP[params.teamTypeSlug];
  const titleType = teamType || 'Team Type';
  return {
    title: `${titleType} College Cycling Schools`,
    description: `Explore ${titleType.toLowerCase()} college cycling schools and compare available cycling programs.`,
  };
}

export default async function SchoolsByTeamTypePage({ params }: TeamTypePageProps) {
  const teamType = TEAM_TYPE_MAP[params.teamTypeSlug];
  if (!teamType) {
    notFound();
  }

  const schools =
    (await serverApiFetch<School[]>(
      `/schools/?team_type=${encodeURIComponent(teamType)}&sort=alphabetical`
    )) || [];

  return (
    <section className='panel page-panel'>
      <h1>{teamType} Cycling Schools</h1>
      <p>Browse college cycling schools with {teamType.toLowerCase()} team programs.</p>

      {schools.length === 0 && <p>No schools found for this team type.</p>}
      {schools.length > 0 && (
        <ul className='toc-list'>
          {schools.map((school) => (
            <li key={school.id}>
              <Link href={`/schools/cycling-program/${school.id}/${slugify(school.name)}`}>
                {school.name} Cycling Program
              </Link>
              {' '}
              <span className='toc-muted'>
                {[school.city, school.state].filter(Boolean).join(', ') || 'Location N/A'}
              </span>
            </li>
          ))}
        </ul>
      )}

      <p className='auth-note'>
        <Link href='/schools/table-of-contents'>Back to School Table of Contents</Link>
      </p>
    </section>
  );
}
