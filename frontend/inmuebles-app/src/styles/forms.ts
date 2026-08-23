import type { CSSProperties } from 'react';
import './forms.css';

/** Apply alongside `inputStyle`/`selectStyle`/`textareaStyle` — provides the
 * `:focus` state that inline styles can't express (see `forms.css`). */
export const FIELD_CLASS_NAME = 'rentame-field';

/**
 * Estilos de formulario compartidos dentro de `inmuebles-app`
 * (`PublicarInmueblePage`/`EditarInmueblePage`), local a este microfrontend
 * — mismo criterio de `styles/buttons.ts` (ver
 * `openspec/changes/ui-layout-navegacion/design.md` decisión 4).
 *
 * Construidos con los tokens de `@rentame/design-tokens`.
 */

export const cardStyle: CSSProperties = {
  backgroundColor: 'var(--color-surface)',
  border: '1px solid var(--color-border)',
  borderRadius: 'var(--radius-card)',
  boxShadow: '0 1px 3px rgba(0, 0, 0, 0.08)',
  padding: '2rem',
};

export const sectionStyle: CSSProperties = {
  marginBottom: '1.75rem',
};

export const sectionTitleStyle: CSSProperties = {
  fontSize: '0.95rem',
  fontWeight: 600,
  color: 'var(--color-text-secondary)',
  textTransform: 'uppercase',
  letterSpacing: '0.03em',
  marginBottom: '1rem',
  borderBottom: '1px solid var(--color-border)',
  paddingBottom: '0.5rem',
};

export const gridRowStyle: CSSProperties = {
  display: 'grid',
  gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))',
  gap: '1rem',
};

const fieldBase: CSSProperties = {
  border: '1px solid var(--color-border)',
  borderRadius: 'var(--radius-card)',
  padding: '0.6rem 0.75rem',
  fontSize: '1rem',
  color: 'var(--color-text)',
  backgroundColor: 'var(--color-surface)',
  fontFamily: 'inherit',
};

export const inputStyle: CSSProperties = { ...fieldBase };
export const selectStyle: CSSProperties = { ...fieldBase };
export const textareaStyle: CSSProperties = { ...fieldBase, resize: 'vertical' };
