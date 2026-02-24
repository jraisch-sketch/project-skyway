import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Contact Collegiate Cycling Finder',
  description:
    'Contact Collegiate Cycling Finder for questions about college cycling program listings and platform support.',
};

export default function ContactPage() {
  return (
    <section className='panel page-panel'>
      <h1>Contact</h1>
      <p>Questions about school listings, account support, or data updates?</p>
      <p>Email: support@projectskyway.org</p>
      <p>
        We review conference and school data updates regularly and can help you find the right
        cycling program path.
      </p>
    </section>
  );
}
