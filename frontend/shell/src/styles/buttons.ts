import type { CSSProperties } from 'react';

/**
 * Estilos de botón compartidos dentro de `shell` (ver
 * `openspec/changes/ui-layout-navegacion/design.md`, decisión 4: archivo
 * local por microfrontend, no un paquete compartido).
 *
 * Construidos con los tokens de `@rentame/design-tokens` y validados contra
 * las reglas de contraste de su README:
 *   - `primaryButtonStyle`: texto `--color-surface` sobre fondo
 *     `--color-primary` — combinación "Surface on Primary", cubierta por
 *     `contrast.test.ts` en design-tokens (AA normal text, >= 4.5:1).
 *   - `secondaryButtonStyle`: fondo `--color-surface`, texto `--color-text`
 *     (par "Text on Surface", también validado AA) y borde `--color-border`
 *     — visualmente secundario sin depender de un color de acento.
 */
export const primaryButtonStyle: CSSProperties = {
  backgroundColor: 'var(--color-primary)',
  color: 'var(--color-surface)',
  border: '1px solid var(--color-primary)',
  borderRadius: 'var(--radius-card)',
  padding: '0.75rem 1.25rem',
  fontSize: '1rem',
  fontWeight: 600,
  cursor: 'pointer',
};

export const secondaryButtonStyle: CSSProperties = {
  backgroundColor: 'var(--color-surface)',
  color: 'var(--color-text)',
  border: '1px solid var(--color-border)',
  borderRadius: 'var(--radius-card)',
  padding: '0.75rem 1.25rem',
  fontSize: '1rem',
  fontWeight: 600,
  cursor: 'pointer',
};
