import React from 'react';
import { Link } from 'react-router';

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
    <h1>Rentame</h1>
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
      ¿Ya tienes cuenta? <Link to="/login">Iniciar sesión</Link>
    </p>
  </div>
);

const containerStyle: React.CSSProperties = {
  fontFamily: 'sans-serif',
  padding: '2rem',
  maxWidth: '520px',
  margin: '0 auto',
  textAlign: 'center',
};

const optionsStyle: React.CSSProperties = {
  display: 'flex',
  flexDirection: 'column',
  gap: '1rem',
  marginTop: '1.5rem',
};

const optionLinkStyle: React.CSSProperties = {
  display: 'block',
  padding: '1rem',
  border: '1px solid var(--color-border)',
  borderRadius: 'var(--radius-card)',
  textDecoration: 'none',
  color: 'inherit',
  fontWeight: 600,
};

export default EntradaPage;
