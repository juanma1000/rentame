/**
 * Tasks 11.1 / 11.3 (Red) — contract test for `pages/RegistroPage.tsx`.
 *
 * Fixes the contract of `RegistroPage` BEFORE the implementation exists (TDD
 * Red phase), per the following requirements in
 * `openspec/changes/hu-008/specs/usuarios/spec.md`:
 *   - "Registro como propietario o inquilino"
 *   - "Registro como agente requiere resolver el paso de agencia"
 * and the sequence diagram in `design.md` ("Registro de agente + paso de
 * agencia").
 *
 * Contract assumed for this task (per the parent task's instruction, since
 * `tasks.md` 11.1/11.2 leaves this open: "pueden compartir un único
 * componente parametrizado por rol"):
 *   - A SINGLE component, `RegistroPage`, parametrized via a required prop
 *     `rol: 'propietario' | 'agente' | 'inquilino'` — NOT a route param. The
 *     shell's router is expected to mount three routes
 *     (`/registro/propietario`, `/registro/agente`, `/registro/inquilino`),
 *     each rendering `<RegistroPage rol="..." />` with a fixed literal prop.
 *     This keeps `RegistroPage` itself decoupled from React Router's params
 *     API and trivially testable by rendering it directly with each prop
 *     value.
 *   - Form fields: `email` (labelled "Email"), `password` (labelled
 *     "Contraseña"), `nombre` (labelled "Nombre"). Submit button whose
 *     accessible name matches /registrarme|crear cuenta|registrar/i.
 *   - On submit, calls `POST /usuarios/registro` via `global.fetch` (mocked
 *     here; the real HTTP call lives in `services/usuarios.api.ts`, task
 *     10.1) with `{ email, password, nombre, rol }`.
 *   - propietario/inquilino: on a successful (2xx) response, calls the REAL
 *     `@rentame/auth` `useAuth().login(accessToken)` (not mocked, per the
 *     parent task's instruction) and redirects immediately to
 *     `/mis-inmuebles` (the only protected route in the shell's router
 *     today).
 *   - agente: on a successful (2xx) response to `/usuarios/registro`, ALSO
 *     calls `login(accessToken)` (the JWT is needed to authenticate the
 *     subsequent agencia calls) but does NOT redirect to `/mis-inmuebles`
 *     yet — instead renders a "resolve tu agencia" step with two paths:
 *       - "Crear agencia nueva": a form with "Razón social" and "NIT"
 *         fields and a submit button; on submit, calls
 *         `POST /agencias/` with `Authorization: Bearer <token>`; on
 *         success (2xx), redirects to `/mis-inmuebles`.
 *       - "Unirme a una agencia existente": a search input + button; on
 *         search, calls `GET /agencias/buscar?q=<texto>` WITHOUT an
 *         `Authorization` header (public endpoint) and renders the returned
 *         agencias, each with a "Solicitar unirme" action; clicking it
 *         calls `POST /agencias/{id}/solicitudes` with
 *         `Authorization: Bearer <token>`; on success (2xx), shows a
 *         "solicitud pendiente" status (NOT an error, NOT a redirect).
 *   - On any error response from `/usuarios/registro` (409 duplicate email,
 *     422 validation), shows a readable error message (`role="alert"`)
 *     without crashing and without redirecting or advancing to the agencia
 *     step.
 *
 * `RegistroPage` does not exist yet in `../pages/RegistroPage` — every test
 * below is expected to fail on import (`Cannot find module
 * '../pages/RegistroPage'`), the genuine Red failure for this phase. No
 * implementation is written here.
 */
import '@testing-library/jest-dom';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import React from 'react';
import { MemoryRouter, Route, Routes } from 'react-router';
import { AuthProvider } from '@rentame/auth';

import RegistroPage from '../pages/RegistroPage';

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function mockFetchSequence(
  ...responses: Array<{ status: number; body: unknown }>
): jest.SpyInstance {
  const spy = jest.spyOn(global, 'fetch');
  responses.forEach(({ status, body }) => {
    spy.mockResolvedValueOnce({
      ok: status >= 200 && status < 300,
      status,
      json: async () => body,
    } as Response);
  });
  return spy;
}

function renderRegistroPage(rol: 'propietario' | 'agente' | 'inquilino') {
  return render(
    <AuthProvider>
      <MemoryRouter initialEntries={[`/registro/${rol}`]}>
        <Routes>
          <Route path={`/registro/${rol}`} element={<RegistroPage rol={rol} />} />
          <Route path="/mis-inmuebles" element={<div>Mis inmuebles page</div>} />
        </Routes>
      </MemoryRouter>
    </AuthProvider>,
  );
}

function fillRegistroForm(email: string, password: string, nombre: string) {
  fireEvent.change(screen.getByLabelText(/email/i), { target: { value: email } });
  fireEvent.change(screen.getByLabelText(/contraseña|password/i), {
    target: { value: password },
  });
  fireEvent.change(screen.getByLabelText(/nombre/i), { target: { value: nombre } });
  fireEvent.click(
    screen.getByRole('button', { name: /registrarme|crear cuenta|registrar/i }),
  );
}

const rawAuthResponse = (rol: 'propietario' | 'agente' | 'inquilino') => ({
  access_token: 'header.payload.signature',
  usuario: { id: 'usuario-1', email: 'nueva.persona@example.com', nombre: 'Nueva Persona', rol },
});

// ---------------------------------------------------------------------------
// propietario / inquilino — immediate session + redirect
// ---------------------------------------------------------------------------

describe.each(['propietario', 'inquilino'] as const)(
  'RegistroPage rol="%s" (contract, Red)',
  (rol) => {
    afterEach(() => {
      jest.restoreAllMocks();
      localStorage.clear();
    });

    it('renders email, password and nombre fields plus a submit button', () => {
      renderRegistroPage(rol);

      expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/contraseña|password/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/nombre/i)).toBeInTheDocument();
      expect(
        screen.getByRole('button', { name: /registrarme|crear cuenta|registrar/i }),
      ).toBeInTheDocument();
    });

    it('on successful registration, persists the session and redirects to a protected route', async () => {
      mockFetchSequence({ status: 201, body: rawAuthResponse(rol) });

      renderRegistroPage(rol);
      fillRegistroForm('nueva.persona@example.com', 'contrasena-1', 'Nueva Persona');

      await waitFor(() => {
        expect(screen.getByText(/mis inmuebles page/i)).toBeInTheDocument();
      });

      expect(localStorage.getItem('rentame_auth_token')).toBe('header.payload.signature');
    });

    it('on a duplicate-email error (409), shows a readable message without crashing or redirecting', async () => {
      mockFetchSequence({ status: 409, body: { detail: 'El email ya está registrado.' } });

      renderRegistroPage(rol);
      fillRegistroForm('ya.existe@example.com', 'contrasena-1', 'Alguien');

      await waitFor(() => {
        expect(screen.getByRole('alert')).toHaveTextContent(/el email ya está registrado/i);
      });

      expect(screen.queryByText(/mis inmuebles page/i)).not.toBeInTheDocument();
      expect(localStorage.getItem('rentame_auth_token')).toBeNull();
    });

    it('on a validation error (422), shows a readable message without crashing or redirecting', async () => {
      mockFetchSequence({ status: 422, body: { detail: 'El campo nombre es requerido.' } });

      renderRegistroPage(rol);
      fillRegistroForm('persona@example.com', 'contrasena-1', '');

      await waitFor(() => {
        expect(screen.getByRole('alert')).toBeInTheDocument();
      });

      expect(screen.queryByText(/mis inmuebles page/i)).not.toBeInTheDocument();
    });
  },
);

// ---------------------------------------------------------------------------
// agente — registro exitoso must NOT redirect immediately; shows agencia step
// ---------------------------------------------------------------------------

describe('RegistroPage rol="agente" (contract, Red)', () => {
  afterEach(() => {
    jest.restoreAllMocks();
    localStorage.clear();
  });

  it('after a successful registro, shows the agencia step (crear vs. unirse) instead of redirecting', async () => {
    mockFetchSequence({ status: 201, body: rawAuthResponse('agente') });

    renderRegistroPage('agente');
    fillRegistroForm('agente.nuevo@example.com', 'contrasena-1', 'Agente Nuevo');

    await waitFor(() => {
      expect(
        screen.getByRole('button', { name: /crear.*agencia/i }),
      ).toBeInTheDocument();
    });
    expect(
      screen.getByRole('button', { name: /unirme.*agencia|unirse.*agencia/i }),
    ).toBeInTheDocument();

    // Must NOT have redirected to /mis-inmuebles yet — the agencia step is
    // required before the agente's registration is considered complete.
    expect(screen.queryByText(/mis inmuebles page/i)).not.toBeInTheDocument();

    // The JWT from registro IS already persisted — needed to authenticate
    // the subsequent agencia calls.
    expect(localStorage.getItem('rentame_auth_token')).toBe('header.payload.signature');
  });

  it('"crear agencia nueva": submitting razón social + NIT calls POST /agencias/ with the JWT and redirects on success', async () => {
    mockFetchSequence(
      { status: 201, body: rawAuthResponse('agente') },
      { status: 201, body: { id: 'agencia-1', razon_social: 'Mi Agencia SAS', nit: '900123456' } },
    );

    renderRegistroPage('agente');
    fillRegistroForm('agente.nuevo@example.com', 'contrasena-1', 'Agente Nuevo');

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /crear.*agencia/i })).toBeInTheDocument();
    });
    fireEvent.click(screen.getByRole('button', { name: /crear.*agencia/i }));

    fireEvent.change(screen.getByLabelText(/razón social/i), {
      target: { value: 'Mi Agencia SAS' },
    });
    fireEvent.change(screen.getByLabelText(/nit/i), { target: { value: '900123456' } });
    fireEvent.click(screen.getByRole('button', { name: /^crear agencia$/i }));

    await waitFor(() => {
      expect(screen.getByText(/mis inmuebles page/i)).toBeInTheDocument();
    });

    expect(global.fetch).toHaveBeenCalledTimes(2);
    const [url, requestInit] = (global.fetch as jest.Mock).mock.calls[1] as [
      string,
      RequestInit,
    ];
    expect(url).toEqual(expect.stringMatching(/\/agencias\/?$/));
    expect(requestInit.method).toBe('POST');
    const headers = requestInit.headers as Record<string, string>;
    expect(headers['Authorization']).toBe('Bearer header.payload.signature');
    const body = JSON.parse(requestInit.body as string) as Record<string, unknown>;
    expect(body).toEqual({ razon_social: 'Mi Agencia SAS', nit: '900123456' });
  });

  it('"unirme a una agencia existente": searches without auth, requests to join with the JWT, and shows a pending status on success', async () => {
    mockFetchSequence(
      { status: 201, body: rawAuthResponse('agente') },
      {
        status: 200,
        body: [{ id: 'agencia-1', razon_social: 'Agencia Existente SAS', nit: '900999888' }],
      },
      { status: 201, body: { id: 'solicitud-1', estado: 'pendiente' } },
    );

    renderRegistroPage('agente');
    fillRegistroForm('agente.nuevo@example.com', 'contrasena-1', 'Agente Nuevo');

    await waitFor(() => {
      expect(
        screen.getByRole('button', { name: /unirme.*agencia|unirse.*agencia/i }),
      ).toBeInTheDocument();
    });
    fireEvent.click(screen.getByRole('button', { name: /unirme.*agencia|unirse.*agencia/i }));

    fireEvent.change(screen.getByLabelText(/buscar agencia/i), {
      target: { value: 'Existente' },
    });
    fireEvent.click(screen.getByRole('button', { name: /^buscar$/i }));

    await waitFor(() => {
      expect(screen.getByText(/agencia existente sas/i)).toBeInTheDocument();
    });

    // Search call must NOT carry an Authorization header — public endpoint.
    const [searchUrl, searchInit] = (global.fetch as jest.Mock).mock.calls[1] as [
      string,
      RequestInit | undefined,
    ];
    expect(searchUrl).toEqual(expect.stringMatching(/\/agencias\/buscar\?q=Existente$/));
    const searchHeaders = (searchInit?.headers ?? {}) as Record<string, string>;
    expect(searchHeaders['Authorization']).toBeUndefined();

    fireEvent.click(screen.getByRole('button', { name: /solicitar unirme/i }));

    await waitFor(() => {
      expect(screen.getByText(/solicitud pendiente|pendiente/i)).toBeInTheDocument();
    });
    expect(screen.queryByRole('alert')).not.toBeInTheDocument();

    expect(global.fetch).toHaveBeenCalledTimes(3);
    const [joinUrl, joinInit] = (global.fetch as jest.Mock).mock.calls[2] as [
      string,
      RequestInit,
    ];
    expect(joinUrl).toEqual(expect.stringMatching(/\/agencias\/agencia-1\/solicitudes$/));
    expect(joinInit.method).toBe('POST');
    const joinHeaders = joinInit.headers as Record<string, string>;
    expect(joinHeaders['Authorization']).toBe('Bearer header.payload.signature');
  });
});
