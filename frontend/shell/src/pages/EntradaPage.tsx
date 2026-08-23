import React from 'react';
import { Link } from 'react-router';
import { radius, spacing, transitions, typography } from '@rentame/design-tokens';

/**
 * Pantalla de entrada simétrica por rol (HU-008).
 *
 * Muestra las tres opciones de registro con el mismo peso visual — ninguna
 * está pre-seleccionada ni destacada sobre las otras — más un enlace a
 * "Iniciar sesión" para quienes ya tienen cuenta.
 *
 * Reemplaza a `TokenLoginPage` (herramienta de desarrollo temporal) como
 * punto de entrada del shell sin sesión activa.
 */
const EntradaPage: React.FC = () => (
  <div style={containerStyle}>
    <h1 style={titleStyle}>Rentame</h1>
    {/* text-secondary sobre fondo blanco por defecto (sin --color-background explícito) — cumple el mínimo de contraste del README */}
    <p style={{ color: 'var(--color-text-secondary)' }}>¿Qué quieres hacer?</p>

    <div style={optionsStyle}>
      <Link to="/registro/propietario" style={optionLinkStyle}>
        Quiero publicar mi inmueble
      </Link>
      <Link to="/registro/agente" style={optionLinkStyle}>
        Gestiono inmuebles de otros
      </Link>
      <Link to="/registro/inquilino" style={optionLinkStyle}>
        Busco dónde vivir
      </Link>
    </div>

    <p style={{ marginTop: '2rem' }}>
      ¿Ya tienes cuenta? <Link to="/login" style={loginLinkStyle}>Iniciar sesión</Link>
    </p>
  </div>
);

const containerStyle: React.CSSProperties = {
  fontFamily: typography.fontFamilyBase,
  padding: '2rem',
  maxWidth: '520px',
  margin: '0 auto',
  textAlign: 'center',
};

const titleStyle: React.CSSProperties = {
  fontFamily: typography.fontFamilyDisplay,
  fontSize: typography.fontSizeH1,
  fontWeight: typography.fontWeightRegular,
  color: 'var(--color-primary)',
};

const optionsStyle: React.CSSProperties = {
  display: 'flex',
  flexDirection: 'column',
  gap: '1rem',
  marginTop: '1.5rem',
};

// Estilizado a mano (mismos tokens que `Button` variant="secondary" de
// `@rentame/ui`) — no puede ser el componente `Button` porque este es un
// <Link> real de react-router (navegación de verdad, no onClick) y `Button`
// solo renderiza <button>.
const optionLinkStyle: React.CSSProperties = {
  display: 'block',
  padding: `${spacing[3]} ${spacing[4]}`,
  border: '1px solid var(--color-primary)',
  borderRadius: radius.sm,
  textDecoration: 'none',
  backgroundColor: 'var(--color-surface)',
  color: 'var(--color-primary)',
  fontFamily: typography.fontFamilyBase,
  fontWeight: typography.fontWeightMedium,
  fontSize: typography.fontSizeBody,
  transition: transitions.base,
};

// Mismos tokens que `Button` variant="ghost" — acción secundaria, sin borde.
const loginLinkStyle: React.CSSProperties = {
  color: 'var(--color-primary)',
  fontWeight: typography.fontWeightMedium,
  textDecoration: 'underline',
};

export default EntradaPage;
