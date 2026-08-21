import '@testing-library/jest-dom';
import React from 'react';
import { render, screen } from '@testing-library/react';

import { AuthProvider } from '../AuthProvider';
import { useAuth } from '../useAuth';

/**
 * Minimal consumer used to probe what AuthProvider exposes via useAuth,
 * without asserting on internal implementation details.
 */
function SessionProbe(): React.ReactElement {
  const { session, isAuthenticated, role } = useAuth();

  return (
    <div>
      <span data-testid="is-authenticated">{String(isAuthenticated)}</span>
      <span data-testid="session">{session === null ? 'null' : 'present'}</span>
      <span data-testid="role">{role ?? 'none'}</span>
    </div>
  );
}

describe('@rentame/auth — AuthProvider', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('exposes no active session when there is no JWT stored', () => {
    render(
      <AuthProvider>
        <SessionProbe />
      </AuthProvider>,
    );

    expect(screen.getByTestId('is-authenticated')).toHaveTextContent('false');
    expect(screen.getByTestId('session')).toHaveTextContent('null');
    expect(screen.getByTestId('role')).toHaveTextContent('none');
  });
});
