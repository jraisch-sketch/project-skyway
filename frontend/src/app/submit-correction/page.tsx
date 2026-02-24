import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Submit a Correction | Skyway',
  description: 'Submit corrections for school and conference data listed on Skyway.',
};

export default function SubmitCorrectionPage() {
  return (
    <section className='panel page-panel'>
      <h1>Submit a Correction</h1>
      <p>
        Found an issue in school or conference information? Please email correction details to{' '}
        <a href='mailto:info@yjroutdoors.com'>info@yjroutdoors.com</a>.
      </p>
      <p>
        Include the school/conference name, the current value shown, and the corrected value for
        the fastest review.
      </p>
    </section>
  );
}
