/**
 * Shell entry point.
 *
 * The dynamic import is the standard Module Federation 2.0 async bootstrap
 * pattern: it defers module evaluation until MF2's runtime has had a chance
 * to negotiate shared singletons (react, @rentame/auth, etc.) with any
 * already-loaded remotes.  Without this indirection, eager module loading
 * can cause "shared module not found" runtime errors.
 */
import('./bootstrap');
