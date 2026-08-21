/**
 * Type declarations for Module Federation remote modules.
 *
 * Each entry here mirrors a key in the `remotes` object in rspack.config.ts.
 * TypeScript uses these declarations to type-check lazy imports like:
 *   const PropertyRoutes = React.lazy(() => import('inmueblesApp/PropertyRoutes'))
 */

/**
 * inmuebles-app remote (task 14.1 / task 16+).
 * Exposes ./PropertyRoutes — the top-level route component for the
 * inmuebles domain (MisInmueblesPage, PublishPropertyPage, EditPropertyPage).
 * The remote is bootstrapped in feature/hu-001-inmuebles-app (task 15+).
 */
declare module 'inmueblesApp/PropertyRoutes' {
  import type React from 'react';
  const PropertyRoutes: React.ComponentType;
  export default PropertyRoutes;
}
