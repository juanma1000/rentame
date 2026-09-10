/**
 * Image imports (e.g. Leaflet's default marker icons in
 * `components/leafletIcon.ts`) are handled by Rspack's `asset/resource`
 * module type (`rspack.config.ts`), which resolves them to a string URL at
 * build time — these ambient declarations tell TypeScript the same.
 */
declare module '*.png' {
  const src: string;
  export default src;
}

declare module '*.jpg' {
  const src: string;
  export default src;
}

declare module '*.svg' {
  const src: string;
  export default src;
}
