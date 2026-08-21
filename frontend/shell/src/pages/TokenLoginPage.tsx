import React, { useState } from 'react';
import { clearSession, decodeTokenPayload, storeSession } from '@rentame/auth';
import type { Role } from '@rentame/auth';

interface SessionInfo {
  sub: string;
  rol: Role;
}

/**
 * Developer tool: initialize a session by pasting a JWT.
 *
 * This page is a TEMPORARY stand-in for a real login flow.  The `usuarios`
 * domain does not have a UI yet (out of scope for HU-001).  Once login is
 * implemented, this page will be removed and replaced by the real auth flow.
 *
 * How to get a token for development:
 *   1. Run the backend (`uvicorn main:app`).
 *   2. Use the test helper `backend/shared/infrastructure/auth/jwt_handler.py`
 *      → `create_access_token(usuario_id=<uuid>, rol="propietario")`.
 *   3. Paste the resulting JWT here.
 *
 * AuthProvider / useAuth / AuthGuard are NOT used here — those are
 * implemented in tasks 12-14 (TDD).  This page talks directly to the
 * low-level session utilities from @rentame/auth.
 */
const TokenLoginPage: React.FC = () => {
  const [tokenInput, setTokenInput] = useState('');
  const [sessionInfo, setSessionInfo] = useState<SessionInfo | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setError(null);

    const trimmed = tokenInput.trim();
    const payload = decodeTokenPayload(trimmed);

    if (!payload) {
      setError(
        'Invalid token format. Paste a valid JWT issued by the Rentame backend ' +
          '(must contain sub and rol claims).',
      );
      return;
    }

    storeSession(trimmed);
    setSessionInfo({ sub: payload.sub, rol: payload.rol });
  };

  const handleClear = () => {
    clearSession();
    setSessionInfo(null);
    setTokenInput('');
    setError(null);
  };

  if (sessionInfo) {
    return (
      <div style={containerStyle}>
        <h1>Session initialized</h1>
        <p>
          <strong>User ID:</strong> {sessionInfo.sub}
        </p>
        <p>
          <strong>Role:</strong> {sessionInfo.rol}
        </p>
        <button onClick={handleClear} style={buttonStyle}>
          Clear session
        </button>
      </div>
    );
  }

  return (
    <div style={containerStyle}>
      <h1>Developer Token Login</h1>
      <p style={{ color: '#666', fontStyle: 'italic', fontSize: '0.9rem' }}>
        This screen is a temporary development tool. Paste a JWT obtained from the backend
        to initialize your session. It will be replaced by a real login flow once the{' '}
        <code>usuarios</code> domain has a UI.
      </p>
      <form onSubmit={handleSubmit}>
        <div style={{ marginBottom: '1rem' }}>
          <label htmlFor="token-input" style={{ display: 'block', marginBottom: '0.25rem' }}>
            JWT token
          </label>
          <textarea
            id="token-input"
            aria-label="JWT token input"
            value={tokenInput}
            onChange={(e) => setTokenInput(e.target.value)}
            placeholder="Paste your JWT here..."
            rows={5}
            style={{ width: '100%', fontFamily: 'monospace', fontSize: '0.85rem', boxSizing: 'border-box' }}
          />
        </div>
        {error && (
          <p role="alert" style={{ color: '#c0392b', marginBottom: '0.75rem' }}>
            {error}
          </p>
        )}
        <button type="submit" disabled={tokenInput.trim() === ''} style={buttonStyle}>
          Initialize session
        </button>
      </form>
    </div>
  );
};

const containerStyle: React.CSSProperties = {
  fontFamily: 'sans-serif',
  padding: '2rem',
  maxWidth: '520px',
  margin: '0 auto',
};

const buttonStyle: React.CSSProperties = {
  padding: '0.5rem 1.25rem',
  cursor: 'pointer',
};

export default TokenLoginPage;
