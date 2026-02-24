'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';

import type { CmsNavItem } from '@/lib/types';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000/api';

type SessionUser = {
  full_name?: string;
  username?: string;
  email?: string;
};

type HeaderNavLink = {
  href: string;
  label: string;
  openInNewTab?: boolean;
};

function displayName(user: SessionUser | null): string {
  if (!user) return 'User';
  return user.full_name || user.username || user.email || 'User';
}

export default function HeaderNav({ initialPrimaryLinks }: { initialPrimaryLinks?: HeaderNavLink[] }) {
  const [loggedIn, setLoggedIn] = useState(false);
  const [name, setName] = useState('User');
  const [menuOpen, setMenuOpen] = useState(false);
  const [primaryLinks, setPrimaryLinks] = useState<HeaderNavLink[]>(
    initialPrimaryLinks && initialPrimaryLinks.length
      ? initialPrimaryLinks
      : [
          { href: '/content/about-skyway', label: 'About Skyway' },
          { href: '/content/collegiate-cycling-team-types-club-vs-varsity', label: 'Team Type Guide' },
          { href: '/content/all-colleges', label: 'All Colleges' },
          { href: '/content/submit-a-correction', label: 'Submit a Correction' },
          { href: '/content/skyway-blog', label: 'Blog' },
          { href: '/content/contact-us', label: 'Contact Us' },
        ]
  );

  useEffect(() => {
    const toHref = (item: CmsNavItem) => {
      if (item.page_slug) return `/content/${item.page_slug}`;
      return item.external_url || '#';
    };

    fetch(`${API_BASE}/cms/navigations/main-top-nav/`)
      .then(async (response) => {
        if (!response.ok) {
          throw new Error('Failed to load CMS navigation.');
        }
        const data = await response.json();
        const items: CmsNavItem[] = Array.isArray(data?.items) ? data.items : [];
        if (!items.length) return;
        setPrimaryLinks(
          items.map((item) => ({
            href: toHref(item),
            label: item.title,
            openInNewTab: item.open_new_tab,
          }))
        );
      })
      .catch(() => {
        // Keep fallback links if CMS nav is unavailable.
      });
  }, []);

  useEffect(() => {
    const token = localStorage.getItem('skyway_access');
    if (!token) {
      setLoggedIn(false);
      setName('User');
      return;
    }

    setLoggedIn(true);
    const cachedRaw = localStorage.getItem('skyway_user');
    if (cachedRaw) {
      try {
        const cachedUser = JSON.parse(cachedRaw) as SessionUser;
        setName(displayName(cachedUser));
      } catch {
        setName('User');
      }
    }

    fetch(`${API_BASE}/auth/me/`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then(async (response) => {
        if (!response.ok) {
          throw new Error('Session expired');
        }
        const data = await response.json();
        localStorage.setItem('skyway_user', JSON.stringify(data));
        setName(displayName(data));
      })
      .catch(() => {
        localStorage.removeItem('skyway_access');
        localStorage.removeItem('skyway_refresh');
        localStorage.removeItem('skyway_user');
        setLoggedIn(false);
        setName('User');
      });
  }, []);

  const logout = () => {
    localStorage.removeItem('skyway_access');
    localStorage.removeItem('skyway_refresh');
    localStorage.removeItem('skyway_user');
    setLoggedIn(false);
    setName('User');
    window.location.href = '/';
  };

  return (
    <div className='header-nav-shell'>
      <button
        type='button'
        className='nav-hamburger'
        aria-label='Toggle navigation menu'
        aria-expanded={menuOpen}
        onClick={() => setMenuOpen((prev) => !prev)}
      >
        <span />
        <span />
        <span />
      </button>

      <nav className={`header-nav-panel ${menuOpen ? 'open' : ''}`}>
        <div className='header-primary-links'>
          {primaryLinks.map((link) => (
            link.href.startsWith('http://') || link.href.startsWith('https://') ? (
              <a
                key={link.href}
                href={link.href}
                target={link.openInNewTab ? '_blank' : undefined}
                rel={link.openInNewTab ? 'noreferrer noopener' : undefined}
                onClick={() => setMenuOpen(false)}
              >
                {link.label}
              </a>
            ) : (
              <Link key={link.href} href={link.href} onClick={() => setMenuOpen(false)}>
                {link.label}
              </Link>
            )
          ))}
        </div>
        <div className='header-account-links'>
          {loggedIn ? (
            <>
              <Link href='/favorites' onClick={() => setMenuOpen(false)}>Favorites</Link>
              <Link href='/account' onClick={() => setMenuOpen(false)}>My Account</Link>
              <span className='nav-greeting'>Hello, {name}</span>
              <button type='button' className='nav-link-button' onClick={logout}>
                Logout
              </button>
            </>
          ) : (
            <Link href='/auth-access' onClick={() => setMenuOpen(false)}>Login / Register</Link>
          )}
        </div>
      </nav>
    </div>
  );
}
