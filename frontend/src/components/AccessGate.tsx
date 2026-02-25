'use client';

import { FormEvent, useEffect, useMemo, useState } from 'react';
import { usePathname } from 'next/navigation';

import { apiFetch } from '@/lib/api';

const ACCESS_CODE_COOKIE = 'skyway_invite_code';
const DEVICE_ID_COOKIE = 'skyway_device_id';
const COOKIE_MAX_AGE = 60 * 60 * 24 * 365 * 10;

type AccessResponse = {
  granted: boolean;
  expires_at: string;
};

function getCookie(name: string): string {
  if (typeof document === 'undefined') {
    return '';
  }
  const value = document.cookie
    .split('; ')
    .find((row) => row.startsWith(`${name}=`))
    ?.split('=')[1];
  return value ? decodeURIComponent(value) : '';
}

function setCookie(name: string, value: string, maxAgeSeconds: number): void {
  document.cookie = `${name}=${encodeURIComponent(value)}; path=/; max-age=${maxAgeSeconds}; SameSite=Lax`;
}

function buildDeviceId(): string {
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
    return crypto.randomUUID();
  }
  return `dev-${Math.random().toString(36).slice(2, 10)}-${Date.now()}`;
}

function ensureDeviceId(): string {
  const existing = getCookie(DEVICE_ID_COOKIE);
  if (existing) {
    return existing;
  }
  const next = buildDeviceId();
  setCookie(DEVICE_ID_COOKIE, next, COOKIE_MAX_AGE);
  return next;
}

function readErrorMessage(error: unknown): string {
  if (error instanceof Error) {
    const raw = error.message || '';
    if (raw.startsWith('{')) {
      try {
        const parsed = JSON.parse(raw) as { detail?: string };
        if (parsed.detail) {
          return parsed.detail;
        }
      } catch {
        return raw;
      }
    }
    return raw || 'Access denied. Please try again.';
  }
  return 'Access denied. Please try again.';
}

export default function AccessGate({ invitationCodeRequired = true }: { invitationCodeRequired?: boolean }) {
  const pathname = usePathname();
  const [isChecking, setIsChecking] = useState(true);
  const [isUnlocked, setIsUnlocked] = useState(false);
  const [codeInput, setCodeInput] = useState('');
  const [errorText, setErrorText] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const contactEmail = useMemo(
    () => process.env.NEXT_PUBLIC_INVITE_CONTACT_EMAIL || 'skyway@yjroutdoors.com',
    []
  );

  useEffect(() => {
    if (!invitationCodeRequired) {
      setIsUnlocked(true);
      setIsChecking(false);
      return;
    }

    let active = true;

    const check = async () => {
      const deviceId = ensureDeviceId();
      const rememberedCode = getCookie(ACCESS_CODE_COOKIE);
      if (!rememberedCode) {
        if (active) {
          setIsChecking(false);
        }
        return;
      }

      try {
        await apiFetch<AccessResponse>('/auth/access/check/', {
          method: 'POST',
          body: JSON.stringify({
            code: rememberedCode,
            device_id: deviceId,
          }),
        });
        if (active) {
          setIsUnlocked(true);
          setErrorText('');
        }
      } catch (error) {
        if (active) {
          setErrorText(readErrorMessage(error));
          setIsUnlocked(false);
        }
      } finally {
        if (active) {
          setIsChecking(false);
        }
      }
    };

    check();

    return () => {
      active = false;
    };
  }, [invitationCodeRequired]);

  useEffect(() => {
    if (isUnlocked) {
      document.body.classList.remove('invite-gate-locked');
      return;
    }
    document.body.classList.add('invite-gate-locked');
    return () => {
      document.body.classList.remove('invite-gate-locked');
    };
  }, [isUnlocked]);

  const onSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setSubmitting(true);
    setErrorText('');

    try {
      const deviceId = ensureDeviceId();
      await apiFetch<AccessResponse>('/auth/access/enter/', {
        method: 'POST',
        body: JSON.stringify({
          code: codeInput,
          device_id: deviceId,
        }),
      });
      setCookie(ACCESS_CODE_COOKIE, codeInput, COOKIE_MAX_AGE);
      setIsUnlocked(true);
      setCodeInput('');
    } catch (error) {
      setErrorText(readErrorMessage(error));
    } finally {
      setSubmitting(false);
    }
  };

  if (!invitationCodeRequired || isUnlocked || pathname === '/clear-invitation') {
    return null;
  }

  return (
    <div className="invite-gate-backdrop" role="presentation">
      <div className="invite-gate-modal" role="dialog" aria-modal="true" aria-labelledby="invite-gate-title">
        <p className="invite-gate-eyebrow">Invitation Access</p>
        <h2 id="invite-gate-title">Enter your invitation code</h2>
        <p className="invite-gate-copy">
          This preview is invitation-only. Enter your case-sensitive access code to continue.
        </p>

        <form onSubmit={onSubmit} className="invite-gate-form">
          <label htmlFor="access-code-input">Access code</label>
          <input
            id="access-code-input"
            type="text"
            autoCapitalize="none"
            autoCorrect="off"
            autoComplete="off"
            value={codeInput}
            onChange={(event) => setCodeInput(event.target.value)}
            placeholder="Example: SKYWAY-BETA-01"
            required
            disabled={isChecking || submitting}
          />
          <button type="submit" disabled={isChecking || submitting || !codeInput}>
            {isChecking ? 'Checking...' : submitting ? 'Submitting...' : 'Enter site'}
          </button>
        </form>

        {errorText ? <p className="invite-gate-error">{errorText}</p> : null}

        <p className="invite-gate-help">
          Need an invite code? Email <a href={`mailto:${contactEmail}`}>{contactEmail}</a>.
        </p>
      </div>
    </div>
  );
}
