import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'About Collegiate Cycling Finder',
  description:
    'Learn about Collegiate Cycling Finder and how we help families discover college cycling programs.',
};

export default function AboutPage() {
  return (
    <section className='panel page-panel'>
      <h1>About</h1>
      <p>
        Collegiate Cycling Finder helps students and families explore college cycling programs by
        conference, location, team type, and discipline.
      </p>
      <p>
        Use our interactive map, school profiles, and conference navigation pages to quickly find
        cycling programs that fit your goals.
      </p>
    </section>
  );
}
