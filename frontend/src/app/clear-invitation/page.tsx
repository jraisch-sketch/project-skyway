'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

const INVITE_CODE_COOKIE = 'skyway_invite_code';

function clearCookie(name: string): void {
  document.cookie = `${name}=; path=/; max-age=0; SameSite=Lax`;
}

export default function ClearInvitationPage() {
  const router = useRouter();

  useEffect(() => {
    clearCookie(INVITE_CODE_COOKIE);
    router.replace('/');
  }, [router]);

  return (
    <main className="stack">
      <section className="panel">
        <h1>Clearing invitation access...</h1>
        <p>Redirecting you to the home page.</p>
      </section>
    </main>
  );
}
