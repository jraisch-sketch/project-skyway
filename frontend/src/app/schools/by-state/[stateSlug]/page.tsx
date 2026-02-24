import Link from 'next/link';
import { notFound } from 'next/navigation';
import type { Metadata } from 'next';

import { slugify } from '@/lib/seo';
import { serverApiFetch } from '@/lib/serverApi';
import type { FilterOptions, School } from '@/lib/types';

type StatePageProps = {
  params: {
    stateSlug: string;
  };
};

export async function generateMetadata({ params }: StatePageProps): Promise<Metadata> {
  const filters = await serverApiFetch<FilterOptions>('/filters/');
  const states = filters?.states || [];
  const state = states.find((entry) => slugify(entry) === params.stateSlug) || 'State';
  return {
    title: `${state} College Cycling Schools`,
    description: `Explore college cycling schools in ${state} and compare available cycling programs.`,
  };
}

export default async function SchoolsByStatePage({ params }: StatePageProps) {
  const filters = await serverApiFetch<FilterOptions>('/filters/');
  const states = filters?.states || [];
  const state = states.find((entry) => slugify(entry) === params.stateSlug);

  if (!state) {
    notFound();
  }

  const schools =
    (await serverApiFetch<School[]>(
      `/schools/?state=${encodeURIComponent(state)}&sort=alphabetical`
    )) || [];

  return (
    <section className='panel page-panel'>
      <h1>{state} Cycling Schools</h1>
      <p>Browse college cycling schools located in {state}.</p>

      {schools.length === 0 && <p>No schools found for this state.</p>}
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
