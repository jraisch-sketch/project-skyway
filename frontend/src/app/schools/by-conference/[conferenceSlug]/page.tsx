import Link from 'next/link';
import { notFound } from 'next/navigation';
import type { Metadata } from 'next';

import { slugify } from '@/lib/seo';
import { serverApiFetch } from '@/lib/serverApi';
import type { FilterOptions, School } from '@/lib/types';

type ConferencePageProps = {
  params: {
    conferenceSlug: string;
  };
};

export async function generateMetadata({ params }: ConferencePageProps): Promise<Metadata> {
  const filters = await serverApiFetch<FilterOptions>('/filters/');
  const conferences = filters?.conferences || [];
  const conferenceName =
    conferences.find((name) => slugify(name) === params.conferenceSlug) || 'Conference';

  return {
    title: `${conferenceName} College Cycling Schools`,
    description: `Explore ${conferenceName} conference college cycling schools and review each cycling program profile.`,
  };
}

export default async function SchoolsByConferencePage({ params }: ConferencePageProps) {
  const filters = await serverApiFetch<FilterOptions>('/filters/');
  const conferences = filters?.conferences || [];
  const conferenceName = conferences.find((name) => slugify(name) === params.conferenceSlug);

  if (!conferenceName) {
    notFound();
  }

  const schools =
    (await serverApiFetch<School[]>(
      `/schools/?conference=${encodeURIComponent(conferenceName)}&sort=alphabetical`
    )) || [];

  return (
    <section className='panel page-panel'>
      <h1>{conferenceName} Conference Schools</h1>
      <p>Browse college cycling schools in the {conferenceName} conference.</p>

      {schools.length === 0 && <p>No schools found for this conference.</p>}
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
