/**
 * Fixes Leaflet's default marker icon under bundlers (Rspack included).
 *
 * `L.Icon.Default` resolves its image URLs relative to the bundled JS file's
 * own location, which breaks outside a plain `<script>`/webpack-with-
 * `url-loader` setup — the icon silently fails to load (a well-known
 * Leaflet + bundler issue). The fix is the same one documented across
 * every Leaflet + Rspack/webpack/Vite integration: import the marker
 * images directly (so the bundler emits and resolves them) and re-point
 * `L.Icon.Default`'s options at those resolved URLs.
 */
import L from 'leaflet';
import iconRetinaUrl from 'leaflet/dist/images/marker-icon-2x.png';
import iconUrl from 'leaflet/dist/images/marker-icon.png';
import shadowUrl from 'leaflet/dist/images/marker-shadow.png';

delete (L.Icon.Default.prototype as unknown as { _getIconUrl?: unknown })._getIconUrl;

L.Icon.Default.mergeOptions({
  iconRetinaUrl,
  iconUrl,
  shadowUrl,
});

export const defaultMarkerIcon = new L.Icon.Default();
