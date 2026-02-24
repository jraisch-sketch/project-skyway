import Link from 'next/link';
import type { Metadata } from 'next';

import { slugify } from '@/lib/seo';
import { serverApiFetch } from '@/lib/serverApi';
import type { FilterOptions, School } from '@/lib/types';

export const metadata: Metadata = {
  title: 'School Table of Contents | College Cycling Programs',
  description:
    'Browse college cycling schools by conference with SEO-friendly conference pages and school program profiles.',
};

export default async function SchoolTableOfContentsPage() {
  const filters = await serverApiFetch<FilterOptions>('/filters/');
  const schools = (await serverApiFetch<School[]>('/schools/?sort=alphabetical')) || [];
  const conferences = filters?.conferences || [];
  const states = filters?.states || [];

  return (
    <section className='panel page-panel'>
      <h1>School Table of Contents</h1>
      <p>
        Browse colleges using navigation paths that mirror search filters. Use conference, team
        type, and state pages to find the best college cycling programs.
      </p>

      <div className='toc-columns'>
        <div className='toc-column'>
          <h2>All Schools A-Z</h2>
          {schools.length === 0 && <p>No schools available right now.</p>}
          {schools.length > 0 && (
            <ul className='toc-list'>
              {schools.map((school) => (
                <li key={school.id}>
                  <Link href={`/schools/cycling-program/${school.id}/${slugify(school.name)}`}>
                    {school.name} Cycling Program
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </div>

        <div className='toc-column'>
          <h2>Schools by Team Type</h2>
          <ul className='toc-list'>
            <li>
              <Link href='/schools/by-team-type/varsity'>Varsity Cycling Schools</Link>
            </li>
            <li>
              <Link href='/schools/by-team-type/club'>Club Cycling Schools</Link>
            </li>
          </ul>

          <h2 className='toc-section-title'>View Schools by Conference</h2>
          {conferences.length === 0 && <p>No conferences available right now.</p>}
          {conferences.length > 0 && (
            <ul className='toc-list'>
              {conferences.map((conference) => (
                <li key={conference}>
                  <Link href={`/schools/by-conference/${slugify(conference)}`}>
                    {conference} Conference Schools
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </div>

        <div className='toc-column'>
          <h2>Schools by State A-Z</h2>
          {states.length === 0 && <p>No states available right now.</p>}
          {states.length > 0 && (
            <ul className='toc-list'>
              {states.map((state) => (
                <li key={state}>
                  <Link href={`/schools/by-state/${slugify(state)}`}>
                    {state} Cycling Schools
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </section>
  );
}
