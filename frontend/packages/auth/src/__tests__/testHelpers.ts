/**
 * Shared test helper for @rentame/auth test suites.
 *
 * Builds a structurally-valid (but unsigned) JWT string for testing purposes.
 * Mirrors the helper already used in session.test.ts so all suites in this
 * package construct tokens the same way.
 */
export function makeToken(payload: Record<string, unknown>): string {
  const encode = (obj: unknown): string =>
    btoa(JSON.stringify(obj))
      .replace(/\+/g, '-')
      .replace(/\//g, '_')
      .replace(/=/g, '');

  const header = encode({ alg: 'HS256', typ: 'JWT' });
  const body = encode(payload);
  return `${header}.${body}.test-signature`;
}
