import React from 'react';
import { Navigate, Outlet } from 'react-router';
import { AuthGuard } from '@rentame/auth';

/**
 * Layout wrapper for routes that require an active session.
 *
 * Uses AuthGuard from @rentame/auth to protect the nested route tree.
 * When no session is active the user is redirected to / (the dev-time
 * TokenLoginPage entry point — this will be replaced by a real login route
 * once the `usuarios` domain has a UI, out of scope for HU-001).
 *
 * Usage in the router:
 *   <Route element={<PrivateLayout />}>
 *     <Route path="/mis-inmuebles" element={<MisInmueblesPage />} />
 *   </Route>
 *
 * AuthGuard is intentionally router-agnostic and accepts any ReactNode as
 * `fallback`, so the redirect is composed here at the shell layer.
 */
const PrivateLayout: React.FC = () => (
  <AuthGuard fallback={<Navigate to="/" replace />}>
    <Outlet />
  </AuthGuard>
);

export default PrivateLayout;
