import '@testing-library/jest-dom';
import React from 'react';
import { render, screen } from '@testing-library/react';

import { AuthProvider } from '../AuthProvider';
import { AuthGuard } from '../AuthGuard';
import { storeSession } from '../session';
import { makeToken } from './testHelpers';

describe('@rentame/auth — AuthGuard', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('renders the fallback instead of children when there is no active session', () => {
    render(
      <AuthProvider>
        <AuthGuard fallback={<p>Please log in</p>}>
          <p>Protected content</p>
        </AuthGuard>
      </AuthProvider>,
    );

    expect(screen.getByText('Please log in')).toBeInTheDocument();
    expect(screen.queryByText('Protected content')).not.toBeInTheDocument();
  });

  it('renders nothing when there is no active session and no fallback is provided', () => {
    const { container } = render(
      <AuthProvider>
        <AuthGuard>
          <p>Protected content</p>
        </AuthGuard>
      </AuthProvider>,
    );

    expect(container).toBeEmptyDOMElement();
  });

  it('renders children when there is an active session', () => {
    storeSession(makeToken({ sub: 'user-1', rol: 'propietario', exp: 9_999_999_999 }));

    render(
      <AuthProvider>
        <AuthGuard fallback={<p>Please log in</p>}>
          <p>Protected content</p>
        </AuthGuard>
      </AuthProvider>,
    );

    expect(screen.getByText('Protected content')).toBeInTheDocument();
    expect(screen.queryByText('Please log in')).not.toBeInTheDocument();
  });
});
