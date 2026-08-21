/**
 * inmuebles-app entry point.
 *
 * The dynamic import is the standard Module Federation 2.0 async bootstrap
 * pattern: it defers module evaluation until MF2's runtime has had a chance
 * to negotiate shared singletons (react, @rentame/auth, etc.) with any
 * already-loaded host.  Without this indirection, eager module loading can
 * cause "shared module not found" runtime errors.
 *
 * In production this module is loaded by the shell via remoteEntry.js.
 * In standalone dev mode (npm start in this directory) it bootstraps
 * a minimal React tree for isolated development and visual verification.
 */
import('./bootstrap');
