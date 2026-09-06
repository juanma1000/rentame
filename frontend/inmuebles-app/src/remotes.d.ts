/**
 * Type declarations for Module Federation remote modules consumed by
 * inmuebles-app itself (cross-remote, not through the shell).
 *
 * Mirrors `shell/src/remotes.d.ts`'s convention. TypeScript uses these
 * declarations to type-check lazy imports like:
 *   const ArrendamientoRoutes = React.lazy(() => import('arrendamientoApp/ArrendamientoRoutes'))
 */

/**
 * arrendamiento-app remote (frontend-flujo-arrendamiento, task 13.2).
 * Exposes ./ArrendamientoRoutes — the top-level route component for the
 * 4-step arrendamiento wizard (identidad, seguro, firma) + "Mi
 * arrendamiento". Consumed directly from `InmuebleDetallePublicoPage`
 * ("Solicitar arrendamiento"), not routed through the shell.
 */
declare module 'arrendamientoApp/ArrendamientoRoutes' {
  import type React from 'react';
  const ArrendamientoRoutes: React.ComponentType<{
    inmuebleId?: string;
    direccionInmueble?: string;
    canonMensual?: number;
  }>;
  export default ArrendamientoRoutes;
}
