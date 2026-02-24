'use client';

import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import { useState } from 'react';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000/api';

type MessageState = { type: 'error' | 'success'; text: string } | null;

function normalizeApiError(data: unknown, fallback: string): string {
  if (!data || typeof data !== 'object') return fallback;
  const detail = (data as { detail?: unknown }).detail;
  if (typeof detail === 'string') return detail;
  return Object.values(data as Record<string, unknown>)
    .flat()
    .map((value) => String(value))
    .join(' ') || fallback;
}

export default function AuthAccessPage() {
  const params = useSearchParams();
  const schoolId = params.get('school_id');
  const currentYear = new Date().getFullYear();
  const gradYearOptions = Array.from({ length: 11 }, (_, index) => currentYear + index);

  const [loginEmail, setLoginEmail] = useState('');
  const [loginPassword, setLoginPassword] = useState('');
  const [registerForm, setRegisterForm] = useState({
    full_name: '',
    email: '',
    account_type: 'student',
    grad_year: String(currentYear),
    password: '',
    password_confirm: '',
  });
  const [loginMessage, setLoginMessage] = useState<MessageState>(null);
  const [registerMessage, setRegisterMessage] = useState<MessageState>(null);
  const [busy, setBusy] = useState(false);

  const addFavoriteIfNeeded = async (token: string) => {
    if (!schoolId) return;
    const response = await fetch(`${API_BASE}/favorites/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ school_id: Number(schoolId), visibility: 'private' }),
    });
    if (!response.ok) {
      const data = await response.json().catch(() => ({}));
      throw new Error(normalizeApiError(data, 'Could not add selected school to favorites.'));
    }
  };

  const handleLogin = async (event: React.FormEvent) => {
    event.preventDefault();
    setLoginMessage(null);
    if (!loginEmail.trim() || !loginPassword) {
      setLoginMessage({ type: 'error', text: 'Email and password are required.' });
      return;
    }
    setBusy(true);
    try {
      const response = await fetch(`${API_BASE}/auth/login/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: loginEmail.trim(), password: loginPassword }),
      });
      const data = await response.json();
      if (!response.ok) {
        setLoginMessage({ type: 'error', text: normalizeApiError(data, 'Login failed.') });
        return;
      }
      localStorage.setItem('skyway_access', data.access);
      localStorage.setItem('skyway_refresh', data.refresh);
      await addFavoriteIfNeeded(data.access);
      window.location.href = '/favorites';
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Could not complete login.';
      setLoginMessage({ type: 'error', text: message });
    } finally {
      setBusy(false);
    }
  };

  const handleRegister = async (event: React.FormEvent) => {
    event.preventDefault();
    setRegisterMessage(null);
    if (registerForm.full_name.trim().split(/\s+/).length < 2) {
      setRegisterMessage({ type: 'error', text: 'Enter your full name (first and last).' });
      return;
    }
    if (registerForm.password !== registerForm.password_confirm) {
      setRegisterMessage({ type: 'error', text: 'Passwords do not match.' });
      return;
    }
    setBusy(true);
    try {
      const registerResponse = await fetch(`${API_BASE}/auth/register/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          full_name: registerForm.full_name.trim(),
          email: registerForm.email.trim(),
          account_type: registerForm.account_type,
          grad_year: Number(registerForm.grad_year),
          password: registerForm.password,
          password_confirm: registerForm.password_confirm,
        }),
      });
      const registerData = await registerResponse.json();
      if (!registerResponse.ok) {
        setRegisterMessage({ type: 'error', text: normalizeApiError(registerData, 'Registration failed.') });
        return;
      }

      const loginResponse = await fetch(`${API_BASE}/auth/login/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: registerForm.email.trim(), password: registerForm.password }),
      });
      const loginData = await loginResponse.json();
      if (!loginResponse.ok) {
        setRegisterMessage({ type: 'error', text: normalizeApiError(loginData, 'Registration succeeded but auto-login failed.') });
        return;
      }
      localStorage.setItem('skyway_access', loginData.access);
      localStorage.setItem('skyway_refresh', loginData.refresh);
      await addFavoriteIfNeeded(loginData.access);
      window.location.href = '/favorites';
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Could not complete registration.';
      setRegisterMessage({ type: 'error', text: message });
    } finally {
      setBusy(false);
    }
  };

  return (
    <section className='panel'>
      <h1>{schoolId ? 'Log in or Create Account to Favorite this School' : 'Log in or Create Account'}</h1>
      <div className='auth-combo-grid'>
        <form className='auth-form' onSubmit={handleLogin}>
          <h2>Login</h2>
          <input
            type='email'
            placeholder='Email'
            value={loginEmail}
            onChange={(event) => setLoginEmail(event.target.value)}
            required
          />
          <input
            type='password'
            placeholder='Password'
            value={loginPassword}
            onChange={(event) => setLoginPassword(event.target.value)}
            required
          />
          <button type='submit' disabled={busy}>{busy ? 'Please wait...' : 'Login'}</button>
          {loginMessage && (
            <p className={loginMessage.type === 'error' ? 'auth-error' : 'auth-success'}>
              {loginMessage.text}
            </p>
          )}
          <p className='auth-note'>
            <Link href='/forgot-password'>Forgot password?</Link>
          </p>
        </form>

        <form className='auth-form' onSubmit={handleRegister}>
          <h2>Create Account</h2>
          <input
            placeholder='Full name'
            value={registerForm.full_name}
            onChange={(event) => setRegisterForm((prev) => ({ ...prev, full_name: event.target.value }))}
            required
          />
          <input
            type='email'
            placeholder='Email'
            value={registerForm.email}
            onChange={(event) => setRegisterForm((prev) => ({ ...prev, email: event.target.value }))}
            required
          />
          <label className='filter-field'>
            <span>Account Type</span>
            <select
              value={registerForm.account_type}
              onChange={(event) => setRegisterForm((prev) => ({ ...prev, account_type: event.target.value }))}
            >
              <option value='student'>Student</option>
              <option value='parent'>Parent</option>
            </select>
          </label>
          <label className='filter-field'>
            <span>Graduation Year</span>
            <select
              value={registerForm.grad_year}
              onChange={(event) => setRegisterForm((prev) => ({ ...prev, grad_year: event.target.value }))}
            >
              {gradYearOptions.map((year) => (
                <option key={year} value={year}>
                  {year}
                </option>
              ))}
            </select>
          </label>
          <input
            type='password'
            placeholder='Password'
            value={registerForm.password}
            onChange={(event) => setRegisterForm((prev) => ({ ...prev, password: event.target.value }))}
            required
          />
          <input
            type='password'
            placeholder='Confirm password'
            value={registerForm.password_confirm}
            onChange={(event) => setRegisterForm((prev) => ({ ...prev, password_confirm: event.target.value }))}
            required
          />
          <button type='submit' disabled={busy}>{busy ? 'Please wait...' : 'Create Account'}</button>
          {registerMessage && (
            <p className={registerMessage.type === 'error' ? 'auth-error' : 'auth-success'}>
              {registerMessage.text}
            </p>
          )}
        </form>
      </div>
    </section>
  );
}
