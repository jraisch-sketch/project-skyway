import { permanentRedirect } from 'next/navigation';

import { slugify } from '@/lib/seo';
import { serverApiFetch } from '@/lib/serverApi';
import type { SchoolDetail } from '@/lib/types';

export default async function SchoolDetailPage({ params }: { params: { id: string } }) {
  const school = await serverApiFetch<SchoolDetail>(`/schools/${params.id}/`);
  const slug = slugify(school?.name || `school-${params.id}`);
  permanentRedirect(`/schools/cycling-program/${params.id}/${slug}`);
}
