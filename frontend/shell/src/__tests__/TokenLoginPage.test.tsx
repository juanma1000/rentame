import '@testing-library/jest-dom';
import { fireEvent, render, screen } from '@testing-library/react';
import React from 'react';
import TokenLoginPage from '../pages/TokenLoginPage';

// ---------------------------------------------------------------------------
// Helper: build a structurally-valid (unsigned) JWT for test assertions.
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

// ---------------------------------------------------------------------------

describe('TokenLoginPage', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('renders the token textarea and submit button', () => {
    render(<TokenLoginPage />);

    expect(screen.getByRole('textbox', { name: /jwt token input/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /initialize session/i })).toBeInTheDocument();
  });

  it('submit button is disabled when the token input is empty', () => {
    render(<TokenLoginPage />);

    expect(screen.getByRole('button', { name: /initialize session/i })).toBeDisabled();
  });

  it('submit button is enabled once the user types into the token field', () => {
    render(<TokenLoginPage />);

    fireEvent.change(screen.getByRole('textbox', { name: /jwt token input/i }), {
      target: { value: 'some.token.value' },
    });

    expect(screen.getByRole('button', { name: /initialize session/i })).not.toBeDisabled();
  });

  it('shows the success state with decoded sub and rol after a valid token is submitted', () => {
    const token = makeToken({ sub: 'user-abc-123', rol: 'propietario', exp: 9_999_999_999 });
    render(<TokenLoginPage />);

    fireEvent.change(screen.getByRole('textbox', { name: /jwt token input/i }), {
      target: { value: token },
    });
    fireEvent.click(screen.getByRole('button', { name: /initialize session/i }));

    expect(screen.getByText(/session initialized/i)).toBeInTheDocument();
    expect(screen.getByText(/user-abc-123/)).toBeInTheDocument();
    expect(screen.getByText(/propietario/i)).toBeInTheDocument();
  });

  it('stores the JWT in localStorage after a valid submission', () => {
    const token = makeToken({ sub: 'user-xyz', rol: 'agente', exp: 9_999_999_999 });
    render(<TokenLoginPage />);

    fireEvent.change(screen.getByRole('textbox', { name: /jwt token input/i }), {
      target: { value: token },
    });
    fireEvent.click(screen.getByRole('button', { name: /initialize session/i }));

    expect(localStorage.getItem('rentame_auth_token')).toBe(token);
  });

  it('shows an error alert when submitting an invalid token format', () => {
    render(<TokenLoginPage />);

    fireEvent.change(screen.getByRole('textbox', { name: /jwt token input/i }), {
      target: { value: 'not-a-valid-jwt' },
    });
    fireEvent.click(screen.getByRole('button', { name: /initialize session/i }));

    expect(screen.getByRole('alert')).toBeInTheDocument();
    // Should stay on the form, not transition to the success view
    expect(screen.queryByText(/session initialized/i)).not.toBeInTheDocument();
  });

  it('returns to the input form and clears localStorage after "Clear session" is clicked', () => {
    const token = makeToken({ sub: 'user-clear', rol: 'propietario', exp: 9_999_999_999 });
    render(<TokenLoginPage />);

    // Initialize session
    fireEvent.change(screen.getByRole('textbox', { name: /jwt token input/i }), {
      target: { value: token },
    });
    fireEvent.click(screen.getByRole('button', { name: /initialize session/i }));
    expect(screen.getByText(/session initialized/i)).toBeInTheDocument();

    // Clear it
    fireEvent.click(screen.getByRole('button', { name: /clear session/i }));

    expect(screen.getByRole('textbox', { name: /jwt token input/i })).toBeInTheDocument();
    expect(localStorage.getItem('rentame_auth_token')).toBeNull();
  });
});
