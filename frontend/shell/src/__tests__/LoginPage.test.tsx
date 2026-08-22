/**
 * Task 11.5 (Red) — contract test for `pages/LoginPage.tsx`.
 *
 * Fixes the contract of `LoginPage` BEFORE the implementation exists (TDD
 * Red phase), per the "Inicio de sesión con email y contraseña" requirement
 * in `openspec/changes/hu-008/specs/usuarios/spec.md`:
 *
 *   GIVEN a registered account with known email and password
 *   WHEN it logs in with those credentials
 *   THEN the system returns a valid JWT and grants an active session
 *
 *   GIVEN a login attempt with a non-existent email or an incorrect password
 *   WHEN those credentials are submitted
 *   THEN the system rejects the login with a single, generic error message
 *
 * Contract assumed for this task:
 *   - Form with `email` and `password` fields, and a submit button.
 *   - On submit, calls `POST /usuarios/login` via `global.fetch` (mocked
 *     here — the real HTTP call lives in `services/usuarios.api.ts`, task
 *     10.1, whose contract test is separate).
 *   - On a successful (2xx) response, calls `useAuth().login(accessToken)`
 *     (the REAL `@rentame/auth` context, not mocked, per the parent task's
 *     "no mockees @rentame/auth" instruction — this exercises the actual
 *     `login()` side effect: persisting the session AND updating the
 *     reactive context) and redirects to a protected route (`/mis-inmuebles`,
 *     the only protected route that exists in the shell today per `App.tsx`).
 *   - On a 401 (backend's single generic message, indistinguishable whether
 *     the email or the password was wrong), shows that message without
 *     crashing and without redirecting.
 *
 * `LoginPage` does not exist yet in `../pages/LoginPage` — every test below
 * is expected to fail on import (`Cannot find module '../pages/LoginPage'`),
 * the genuine Red failure for this phase. No implementation is written here.
 */
import '@testing-library/jest-dom';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import React from 'react';
import { MemoryRouter, Route, Routes } from 'react-router';
import { AuthProvider } from '@rentame/auth';

import LoginPage from '../pages/LoginPage';

function mockFetchResolvedOnce(body: unknown, status: number): jest.SpyInstance {
  return jest.spyOn(global, 'fetch').mockResolvedValueOnce({
    ok: status >= 200 && status < 300,
    status,
    json: async () => body,
  } as Response);
}

function renderLoginPage() {
  return render(
    <AuthProvider>
      <MemoryRouter initialEntries={['/login']}>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/mis-inmuebles" element={<div>Mis inmuebles page</div>} />
        </Routes>
      </MemoryRouter>
    </AuthProvider>,
  );
}

function fillAndSubmit(email: string, password: string) {
  fireEvent.change(screen.getByLabelText(/email/i), { target: { value: email } });
  fireEvent.change(screen.getByLabelText(/contraseña|password/i), {
    target: { value: password },
  });
  fireEvent.click(screen.getByRole('button', { name: /iniciar sesión|ingresar|login/i }));
}

describe('LoginPage (contract, Red)', () => {
  afterEach(() => {
    jest.restoreAllMocks();
    localStorage.clear();
  });

  it('renders email and password fields plus a submit button', () => {
    renderLoginPage();

    expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/contraseña|password/i)).toBeInTheDocument();
    expect(
      screen.getByRole('button', { name: /iniciar sesión|ingresar|login/i }),
    ).toBeInTheDocument();
  });

  it('on successful login, persists the session and redirects to a protected route', async () => {
    mockFetchResolvedOnce(
      {
        access_token: 'header.payload.signature',
        usuario: { id: 'usuario-1', email: 'persona@example.com', nombre: 'Persona', rol: 'propietario' },
      },
      200,
    );

    renderLoginPage();
    fillAndSubmit('persona@example.com', 'contrasena-correcta');

    await waitFor(() => {
      expect(screen.getByText(/mis inmuebles page/i)).toBeInTheDocument();
    });

    // The REAL @rentame/auth session must have been persisted by login().
    expect(localStorage.getItem('rentame_auth_token')).toBe('header.payload.signature');
  });

  it('on a 401 response, shows the single generic error message without crashing or redirecting', async () => {
    mockFetchResolvedOnce({ detail: 'Credenciales inválidas.' }, 401);

    renderLoginPage();
    fillAndSubmit('persona@example.com', 'contrasena-incorrecta');

    await waitFor(() => {
      expect(screen.getByRole('alert')).toHaveTextContent(/credenciales inválidas/i);
    });

    expect(screen.queryByText(/mis inmuebles page/i)).not.toBeInTheDocument();
    expect(localStorage.getItem('rentame_auth_token')).toBeNull();
  });
});
