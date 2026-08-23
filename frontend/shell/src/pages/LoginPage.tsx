import React, { useState } from 'react';
import { useNavigate } from 'react-router';
import { useAuth } from '@rentame/auth';
import { login, UsuariosApiError } from '../services/usuarios.api';
import { primaryButtonStyle } from '../styles/buttons';

/**
 * Inicio de sesión con email y contraseña (HU-008).
 *
 * Éxito: persiste la sesión vía `useAuth().login(accessToken)` y redirige a
 * `/mis-inmuebles` (única ruta protegida del shell hoy).
 *
 * Error (401): el backend devuelve un único mensaje genérico, indistinguible
 * entre email inexistente y contraseña incorrecta — se muestra tal cual, sin
 * redirigir ni romper la pantalla.
 */
const LoginPage: React.FC = () => {
  const { login: setSession } = useAuth();
  const navigate = useNavigate();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setError(null);
    setSubmitting(true);

    try {
      const result = await login({ email, password });
      setSession(result.accessToken);
      navigate('/mis-inmuebles', { replace: true });
    } catch (err) {
      setError(err instanceof UsuariosApiError ? err.message : 'Error desconocido.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div style={containerStyle}>
      <h1>Iniciar sesión</h1>

      <form onSubmit={handleSubmit}>
        <div style={fieldStyle}>
          <label htmlFor="login-email">Email</label>
          <input
            id="login-email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
        </div>

        <div style={fieldStyle}>
          <label htmlFor="login-password">Contraseña</label>
          <input
            id="login-password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </div>

        {error && (
          <p role="alert" style={alertStyle}>
            {error}
          </p>
        )}

        <button type="submit" disabled={submitting} style={primaryButtonStyle}>
          Iniciar sesión
        </button>
      </form>
    </div>
  );
};

const containerStyle: React.CSSProperties = {
  fontFamily: 'sans-serif',
  padding: '2rem',
  maxWidth: '420px',
  margin: '0 auto',
};

const fieldStyle: React.CSSProperties = {
  marginBottom: '1rem',
  display: 'flex',
  flexDirection: 'column',
  gap: '0.25rem',
};

const alertStyle: React.CSSProperties = {
  color: 'var(--color-error)',
  marginBottom: '0.75rem',
};

export default LoginPage;
