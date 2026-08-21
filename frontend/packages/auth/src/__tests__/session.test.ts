import { clearSession, decodeTokenPayload, getSession, storeSession } from '../session';

// ---------------------------------------------------------------------------
// Helper: build a structurally-valid (but unsigned) JWT for testing purposes.
// Payload fields mirror the backend's jwt_handler.py:  { sub, rol, exp }.
// ---------------------------------------------------------------------------
function makeToken(payload: Record<string, unknown>): string {
  const encode = (obj: unknown): string =>
    btoa(JSON.stringify(obj))
      .replace(/\+/g, '-')
      .replace(/\//g, '_')
      .replace(/=/g, '');

  const header = encode({ alg: 'HS256', typ: 'JWT' });
  const body = encode(payload);
  return `${header}.${body}.test-signature`;
}

const VALID_TOKEN = makeToken({
  sub: 'test-user-id',
  rol: 'propietario',
  exp: 9_999_999_999,
});

// ---------------------------------------------------------------------------

describe('@rentame/auth — session utilities', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  // ---- storeSession / getSession ------------------------------------------

  describe('storeSession + getSession', () => {
    it('stores a token and retrieves it with the decoded payload', () => {
      storeSession(VALID_TOKEN);
      const session = getSession();

      expect(session).not.toBeNull();
      expect(session?.token).toBe(VALID_TOKEN);
      expect(session?.payload.sub).toBe('test-user-id');
      expect(session?.payload.rol).toBe('propietario');
      expect(session?.payload.exp).toBe(9_999_999_999);
    });

    it('returns null when no session has been stored', () => {
      expect(getSession()).toBeNull();
    });

    it('clears a malformed token from localStorage and returns null', () => {
      localStorage.setItem('rentame_auth_token', 'not.a.valid.jwt');
      const session = getSession();

      expect(session).toBeNull();
      // Also cleaned up so it does not re-surface
      expect(localStorage.getItem('rentame_auth_token')).toBeNull();
    });
  });

  // ---- clearSession --------------------------------------------------------

  describe('clearSession', () => {
    it('removes the stored session so getSession returns null afterward', () => {
      storeSession(VALID_TOKEN);
      clearSession();
      expect(getSession()).toBeNull();
    });

    it('is idempotent when called with no active session', () => {
      expect(() => clearSession()).not.toThrow();
    });
  });

  // ---- decodeTokenPayload --------------------------------------------------

  describe('decodeTokenPayload', () => {
    it('decodes sub and rol from a valid JWT', () => {
      const payload = decodeTokenPayload(VALID_TOKEN);

      expect(payload).not.toBeNull();
      expect(payload?.sub).toBe('test-user-id');
      expect(payload?.rol).toBe('propietario');
    });

    it('returns null for a string with fewer than three dot-separated parts', () => {
      expect(decodeTokenPayload('only.two')).toBeNull();
    });

    it('returns null for a string with more than three dot-separated parts', () => {
      expect(decodeTokenPayload('one.two.three.four')).toBeNull();
    });

    it('returns null when the payload is missing the sub claim', () => {
      const token = makeToken({ rol: 'propietario', exp: 9_999_999_999 });
      expect(decodeTokenPayload(token)).toBeNull();
    });

    it('returns null when the payload is missing the rol claim', () => {
      const token = makeToken({ sub: 'user-id', exp: 9_999_999_999 });
      expect(decodeTokenPayload(token)).toBeNull();
    });

    it('returns null when the payload is not valid JSON', () => {
      const badB64 = 'eyJhbGciOiJIUzI1NiJ9.!!!not-base64!!!.sig';
      expect(decodeTokenPayload(badB64)).toBeNull();
    });

    it('includes exp when present', () => {
      const payload = decodeTokenPayload(VALID_TOKEN);
      expect(payload?.exp).toBe(9_999_999_999);
    });

    it('omits exp when not present in the payload', () => {
      const token = makeToken({ sub: 'u', rol: 'agente' });
      const payload = decodeTokenPayload(token);
      expect(payload?.exp).toBeUndefined();
    });
  });
});
