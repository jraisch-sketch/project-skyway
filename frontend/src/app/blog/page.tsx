import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Skyway Blog',
  description: 'News, updates, and guidance from Skyway Collegiate Cycling Finder.',
};

export default function BlogPage() {
  return (
    <section className='panel page-panel'>
      <h1>Blog</h1>
      <p>Skyway updates, conference insights, and college cycling guidance will appear here.</p>
      <p>Check back soon for new posts.</p>
    </section>
  );
}
