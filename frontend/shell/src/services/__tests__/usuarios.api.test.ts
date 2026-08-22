/**
 * Task 10.1 (Red) — contract test for `services/usuarios.api.ts`.
 *
 * Fixes the contract of `registrar(payload)` and `login(payload)` BEFORE the
 * implementation exists (TDD Red phase, delegated to qa-expert per
 * `openspec/config.yaml`'s `apply` rule), per `design.md` decisions 1/3 and
 * the "Registro como propietario o inquilino" / "Registro como agente
 * requiere resolver el paso de agencia" / "Inicio de sesión con email y
 * contraseña" requirements in `openspec/changes/hu-008/specs/usuarios/spec.md`.
 *
 * Contract (mirrors the `agencias.api.ts` / `inmuebles.api.ts` fetch-based
 * client pattern already established in `inmuebles-app`; no `axios`
 * dependency exists anywhere in this monorepo):
 *   - `registrar({ email, password, nombre, rol })` sends a JSON `POST` to
 *     `${BASE_URL}/usuarios/registro`. `BASE_URL` reads
 *     `process.env.USUARIOS_API_URL`, falling back to
 *     `http://localhost:8000` (same convention as `INMUEBLES_API_URL`).
 *   - `login({ email, password })` sends a JSON `POST` to
 *     `${BASE_URL}/usuarios/login`.
 *   - Both resolve, on a 2xx response, with a camelCase-mapped
 *     `{ accessToken, usuario: { id, email, nombre, rol } }`, mapped from the
 *     backend's raw `{ access_token, usuario: { id, email, nombre, rol } }`.
 *   - Both throw a typed `UsuariosApiError` (not a bare `Error`) on a
 *     non-2xx response, whose `.message` is the backend's `{"detail": "..."}`
 *     message and whose `.status` is the HTTP status code (409 duplicate
 *     email, 422 validation, 401 invalid credentials).
 *
 * This module does not exist yet — every test below is expected to fail on
 * import (`Cannot find module '../usuarios.api'`), which is the genuine Red
 * failure for this phase. No implementation is written here.
 */
import type { AuthResult, LoginPayload, RegistrarPayload } from '../usuarios.api';
import { login, registrar, UsuariosApiError } from '../usuarios.api';

// ---------------------------------------------------------------------------
// Fixtures
// ---------------------------------------------------------------------------

const registrarPayload: RegistrarPayload = {
  email: 'nueva.persona@example.com',
  password: 'contrasena-segura-1',
  nombre: 'Nueva Persona',
  rol: 'propietario',
};

const loginPayload: LoginPayload = {
  email: 'nueva.persona@example.com',
  password: 'contrasena-segura-1',
};

const rawAuthResponse = {
  access_token: 'header.payload.signature',
  usuario: {
    id: 'usuario-uuid-1',
    email: registrarPayload.email,
    nombre: registrarPayload.nombre,
    rol: 'propietario',
  },
};

const expectedAuthResult: AuthResult = {
  accessToken: 'header.payload.signature',
  usuario: {
    id: 'usuario-uuid-1',
    email: registrarPayload.email,
    nombre: registrarPayload.nombre,
    rol: 'propietario',
  },
};

function mockFetchResolvedOnce(body: unknown, status = 201): jest.SpyInstance {
  return jest.spyOn(global, 'fetch').mockResolvedValueOnce({
    ok: status >= 200 && status < 300,
    status,
    json: async () => body,
  } as Response);
}

// ---------------------------------------------------------------------------

describe('usuarios.api — registrar (contract, Red)', () => {
  afterEach(() => {
    jest.restoreAllMocks();
  });

  it('sends a JSON POST request to .../usuarios/registro with the payload', async () => {
    mockFetchResolvedOnce(rawAuthResponse, 201);

    await registrar(registrarPayload);

    expect(global.fetch).toHaveBeenCalledTimes(1);
    const [url, requestInit] = (global.fetch as jest.Mock).mock.calls[0] as [
      string,
      RequestInit,
    ];

    expect(url).toEqual(expect.stringMatching(/\/usuarios\/registro$/));
    expect(requestInit.method).toBe('POST');
    const headers = requestInit.headers as Record<string, string>;
    expect(headers['Content-Type']).toBe('application/json');
    expect(JSON.parse(requestInit.body as string)).toEqual({
      email: registrarPayload.email,
      password: registrarPayload.password,
      nombre: registrarPayload.nombre,
      rol: registrarPayload.rol,
    });
  });

  it('resolves with a camelCase-mapped { accessToken, usuario } on a successful (201) response', async () => {
    mockFetchResolvedOnce(rawAuthResponse, 201);

    const result = await registrar(registrarPayload);

    expect(result).toEqual(expectedAuthResult);
  });

  it('throws a typed UsuariosApiError with the backend detail message when the email is already registered (409)', async () => {
    mockFetchResolvedOnce({ detail: 'El email ya está registrado.' }, 409);

    let caught: unknown;
    try {
      await registrar(registrarPayload);
    } catch (error) {
      caught = error;
    }

    expect(caught).toBeInstanceOf(UsuariosApiError);
    expect((caught as UsuariosApiError).message).toBe('El email ya está registrado.');
    expect((caught as UsuariosApiError).status).toBe(409);
  });

  it('throws a typed UsuariosApiError on a validation failure (422)', async () => {
    mockFetchResolvedOnce({ detail: 'El campo nombre es requerido.' }, 422);

    await expect(registrar(registrarPayload)).rejects.toThrow(UsuariosApiError);
  });
});

describe('usuarios.api — login (contract, Red)', () => {
  afterEach(() => {
    jest.restoreAllMocks();
  });

  it('sends a JSON POST request to .../usuarios/login with the credentials', async () => {
    mockFetchResolvedOnce(rawAuthResponse, 200);

    await login(loginPayload);

    expect(global.fetch).toHaveBeenCalledTimes(1);
    const [url, requestInit] = (global.fetch as jest.Mock).mock.calls[0] as [
      string,
      RequestInit,
    ];

    expect(url).toEqual(expect.stringMatching(/\/usuarios\/login$/));
    expect(requestInit.method).toBe('POST');
    const headers = requestInit.headers as Record<string, string>;
    expect(headers['Content-Type']).toBe('application/json');
    expect(JSON.parse(requestInit.body as string)).toEqual({
      email: loginPayload.email,
      password: loginPayload.password,
    });
  });

  it('resolves with a camelCase-mapped { accessToken, usuario } on a successful (200) response', async () => {
    mockFetchResolvedOnce(rawAuthResponse, 200);

    const result = await login(loginPayload);

    expect(result).toEqual(expectedAuthResult);
  });

  it('throws a typed UsuariosApiError with the single generic message on invalid credentials (401)', async () => {
    mockFetchResolvedOnce(
      { detail: 'Credenciales inválidas.' },
      401,
    );

    let caught: unknown;
    try {
      await login(loginPayload);
    } catch (error) {
      caught = error;
    }

    expect(caught).toBeInstanceOf(UsuariosApiError);
    expect((caught as UsuariosApiError).message).toBe('Credenciales inválidas.');
    expect((caught as UsuariosApiError).status).toBe(401);
  });
});
