import React, { useState } from 'react';
import { useNavigate } from 'react-router';
import { useAuth } from '@rentame/auth';
import { Button, Input } from '@rentame/ui';
import { typography } from '@rentame/design-tokens';
import { registrar, UsuariosApiError } from '../services/usuarios.api';
import type { Rol } from '../services/usuarios.api';
import {
  Agencia,
  AgenciasApiError,
  buscarAgencias,
  crearAgencia,
  solicitarUnirse,
} from '../services/agencias.api';

export interface RegistroPageProps {
  rol: Rol;
}

/**
 * Formulario de registro, parametrizado por rol (HU-008).
 *
 * Un único componente cubre los tres roles — la única diferencia de
 * comportamiento está en qué pasa DESPUÉS de un registro exitoso:
 *
 *   - propietario / inquilino: sesión inmediata (`useAuth().login`) +
 *     redirect a `/mis-inmuebles`.
 *   - agente: sesión inmediata también (el JWT hace falta para las llamadas
 *     de agencia), pero SIN redirect — se muestra el "paso de agencia"
 *     (crear una nueva o buscar y solicitar unirse a una existente) antes de
 *     considerar el registro completo.
 *
 * El router del shell (`App.tsx`) monta este componente tres veces, una por
 * ruta, con el prop `rol` fijo — `RegistroPage` en sí no conoce react-router
 * params.
 */
type AgenciaStep = 'ninguno' | 'eleccion' | 'crear' | 'buscar';

const RegistroPage: React.FC<RegistroPageProps> = ({ rol }) => {
  const { login: setSession } = useAuth();
  const navigate = useNavigate();

  // Formulario de registro -----------------------------------------------
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [nombre, setNombre] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  // Paso de agencia (solo rol="agente") ------------------------------------
  const [agenciaStep, setAgenciaStep] = useState<AgenciaStep>('ninguno');
  const [accessToken, setAccessToken] = useState<string | null>(null);
  const [agenciaError, setAgenciaError] = useState<string | null>(null);

  // Sub-paso: crear agencia nueva
  const [razonSocial, setRazonSocial] = useState('');
  const [nit, setNit] = useState('');
  const [creandoAgencia, setCreandoAgencia] = useState(false);

  // Sub-paso: buscar y unirse
  const [busqueda, setBusqueda] = useState('');
  const [resultados, setResultados] = useState<Agencia[]>([]);
  const [buscando, setBuscando] = useState(false);
  const [solicitudPendienteId, setSolicitudPendienteId] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setError(null);
    setSubmitting(true);

    try {
      const result = await registrar({ email, password, nombre, rol });
      setSession(result.accessToken);

      if (rol === 'agente') {
        setAccessToken(result.accessToken);
        setAgenciaStep('eleccion');
      } else {
        navigate('/mis-inmuebles', { replace: true });
      }
    } catch (err) {
      setError(err instanceof UsuariosApiError ? err.message : 'Error desconocido.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleCrearAgencia = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!accessToken) return;
    setAgenciaError(null);
    setCreandoAgencia(true);

    try {
      await crearAgencia({ razonSocial, nit }, accessToken);
      navigate('/mis-inmuebles', { replace: true });
    } catch (err) {
      setAgenciaError(err instanceof AgenciasApiError ? err.message : 'Error desconocido.');
    } finally {
      setCreandoAgencia(false);
    }
  };

  const handleBuscarAgencias = async () => {
    setAgenciaError(null);
    setBuscando(true);

    try {
      const encontradas = await buscarAgencias(busqueda);
      setResultados(encontradas);
    } catch (err) {
      setAgenciaError(err instanceof AgenciasApiError ? err.message : 'Error desconocido.');
    } finally {
      setBuscando(false);
    }
  };

  const handleSolicitarUnirse = async (agenciaId: string) => {
    if (!accessToken) return;
    setAgenciaError(null);

    try {
      await solicitarUnirse(agenciaId, accessToken);
      setSolicitudPendienteId(agenciaId);
    } catch (err) {
      setAgenciaError(err instanceof AgenciasApiError ? err.message : 'Error desconocido.');
    }
  };

  // -------------------------------------------------------------------------
  // Paso de agencia (solo rol="agente", tras un registro exitoso)
  // -------------------------------------------------------------------------
  if (rol === 'agente' && agenciaStep !== 'ninguno') {
    return (
      <div style={containerStyle}>
        <h1 style={titleStyle}>Configura tu agencia</h1>

        {agenciaError && (
          <p role="alert" style={alertStyle}>
            {agenciaError}
          </p>
        )}

        {agenciaStep === 'eleccion' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <Button type="button" variant="secondary" onClick={() => setAgenciaStep('crear')}>
              Crear agencia nueva
            </Button>
            <Button type="button" variant="secondary" onClick={() => setAgenciaStep('buscar')}>
              Unirme a una agencia existente
            </Button>
          </div>
        )}

        {agenciaStep === 'crear' && (
          <form onSubmit={handleCrearAgencia}>
            <div style={fieldStyle}>
              <label htmlFor="agencia-razon-social">Razón social</label>
              <Input
                id="agencia-razon-social"
                value={razonSocial}
                onChange={(e) => setRazonSocial(e.target.value)}
              />
            </div>
            <div style={fieldStyle}>
              <label htmlFor="agencia-nit">NIT</label>
              <Input
                id="agencia-nit"
                value={nit}
                onChange={(e) => setNit(e.target.value)}
              />
            </div>
            <Button type="submit" variant="primary" disabled={creandoAgencia}>
              Crear agencia
            </Button>
          </form>
        )}

        {agenciaStep === 'buscar' && (
          <div>
            <div style={fieldStyle}>
              <label htmlFor="agencia-buscar">Buscar agencia</label>
              <Input
                id="agencia-buscar"
                value={busqueda}
                onChange={(e) => setBusqueda(e.target.value)}
              />
            </div>
            <Button type="button" variant="secondary" onClick={handleBuscarAgencias} disabled={buscando}>
              Buscar
            </Button>

            <ul style={{ listStyle: 'none', padding: 0, marginTop: '1rem' }}>
              {resultados.map((agencia) => (
                <li key={agencia.id} style={agenciaResultStyle}>
                  <span>
                    {agencia.razonSocial} — NIT {agencia.nit}
                  </span>
                  {solicitudPendienteId === agencia.id ? (
                    <span>Solicitud pendiente</span>
                  ) : (
                    <Button type="button" variant="secondary" onClick={() => handleSolicitarUnirse(agencia.id)}>
                      Solicitar unirme
                    </Button>
                  )}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    );
  }

  // -------------------------------------------------------------------------
  // Formulario de registro
  // -------------------------------------------------------------------------
  return (
    <div style={containerStyle}>
      <h1 style={titleStyle}>{tituloPorRol[rol]}</h1>

      <form onSubmit={handleSubmit}>
        <div style={fieldStyle}>
          <label htmlFor="registro-email">Email</label>
          <Input
            id="registro-email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
        </div>

        <div style={fieldStyle}>
          <label htmlFor="registro-password">Contraseña</label>
          <Input
            id="registro-password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </div>

        <div style={fieldStyle}>
          <label htmlFor="registro-nombre">Nombre</label>
          <Input
            id="registro-nombre"
            value={nombre}
            onChange={(e) => setNombre(e.target.value)}
          />
        </div>

        {error && (
          <p role="alert" style={alertStyle}>
            {error}
          </p>
        )}

        <Button type="submit" variant="primary" disabled={submitting}>
          Registrarme
        </Button>
      </form>
    </div>
  );
};

const tituloPorRol: Record<Rol, string> = {
  propietario: 'Publica tu inmueble',
  agente: 'Gestiona inmuebles de otros',
  inquilino: 'Encuentra dónde vivir',
};

const containerStyle: React.CSSProperties = {
  fontFamily: typography.fontFamilyBase,
  padding: '2rem',
  maxWidth: '420px',
  margin: '0 auto',
};

const titleStyle: React.CSSProperties = {
  fontFamily: typography.fontFamilyDisplay,
  fontSize: typography.fontSizeH1,
  fontWeight: typography.fontWeightRegular,
  color: 'var(--color-primary)',
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

const agenciaResultStyle: React.CSSProperties = {
  display: 'flex',
  justifyContent: 'space-between',
  alignItems: 'center',
  gap: '1rem',
  padding: '0.5rem 0',
  borderBottom: '1px solid var(--color-border)',
};

export default RegistroPage;
