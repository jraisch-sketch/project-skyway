function resolveServerApiBase(): string {
  const configured = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://127.0.0.1:8000/api';

  if (/^https?:\/\//.test(configured)) {
    return configured;
  }

  if (configured.startsWith('/')) {
    const host = process.env.SERVER_API_ORIGIN_HOST || '127.0.0.1';
    const port = process.env.PORT || '3000';
    return `http://${host}:${port}${configured}`;
  }

  return configured;
}

export async function serverApiFetch<T>(path: string): Promise<T | null> {
  try {
    const apiBase = resolveServerApiBase();
    const response = await fetch(`${apiBase}${path}`, { cache: 'no-store' });
    if (!response.ok) {
      return null;
    }
    return (await response.json()) as T;
  } catch {
    return null;
  }
}
