import '@testing-library/jest-dom';
import React from 'react';
import { render, screen } from '@testing-library/react';

import { AuthProvider } from '../AuthProvider';
import { useAuth } from '../useAuth';
import { storeSession } from '../session';
import { makeToken } from './testHelpers';

/**
 * Minimal consumer that renders everything useAuth exposes so assertions
 * can be made through the DOM, consistent with RTL conventions.
 */
function AuthConsumer(): React.ReactElement {
  const { session, payload, role, isAuthenticated } = useAuth();

  return (
    <div>
      <span data-testid="authenticated">{String(isAuthenticated)}</span>
      <span data-testid="sub">{payload?.sub ?? ''}</span>
      <span data-testid="role">{role ?? ''}</span>
      <span data-testid="token">{session?.token ?? ''}</span>
    </div>
  );
}

describe('@rentame/auth — useAuth', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('exposes the decoded JWT and the user role when the session is valid', () => {
    const token = makeToken({ sub: 'user-123', rol: 'inquilino', exp: 9_999_999_999 });
    storeSession(token);

    render(
      <AuthProvider>
        <AuthConsumer />
      </AuthProvider>,
    );

    expect(screen.getByTestId('authenticated')).toHaveTextContent('true');
    expect(screen.getByTestId('sub')).toHaveTextContent('user-123');
    expect(screen.getByTestId('role')).toHaveTextContent('inquilino');
    expect(screen.getByTestId('token')).toHaveTextContent(token);
  });

  it('throws a helpful error when used outside of an AuthProvider', () => {
    const consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation(() => {});

    function BareConsumer(): React.ReactElement | null {
      useAuth();
      return null;
    }

    expect(() => render(<BareConsumer />)).toThrow(/AuthProvider/);

    consoleErrorSpy.mockRestore();
  });
});
