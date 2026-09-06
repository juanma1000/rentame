/**
 * ValidarIdentidadPage — wizard paso 1: verificar identidad.
 *
 * Fetches the inquilino's current identidad estado on mount
 * (`identidad.api.ts`'s `obtenerEstado`). When `aprobado`, shows a
 * confirmation and a "Siguiente" control that calls `onSiguiente` (the
 * caller, `ArrendamientoRoutes`, advances the wizard). Otherwise
 * (`no_iniciado`/`rechazado`) shows the form: cédula + frente/dorso
 * uploads. Submitting calls `validarIdentidad`, which resolves
 * synchronously with the result (the current `FakeAdapter` never leaves a
 * validación `pendiente`) — `aprobado` shows the same confirmation,
 * `rechazado` shows an error and re-enables the form to retry.
 */
import React, { ChangeEvent, FormEvent, useEffect, useState } from 'react';
import { useAuth } from '@rentame/auth';
import { Button, Input } from '@rentame/ui';
import { IdentidadApiError, obtenerEstado, validarIdentidad } from '../services/identidad.api';
import type { EstadoIdentidadValue } from '../services/identidad.api';

interface Props {
  /** Called when identidad is (already, or just became) aprobado and the
   * inquilino chooses to advance to the next step of the wizard. */
  onSiguiente: () => void;
}

const ValidarIdentidadPage: React.FC<Props> = ({ onSiguiente }) => {
  const { session } = useAuth();

  const [estado, setEstado] = useState<EstadoIdentidadValue | null>(null);
  const [loadingEstado, setLoadingEstado] = useState(true);
  const [fetchError, setFetchError] = useState<string | null>(null);

  const [cedula, setCedula] = useState('');
  const [imagenFrente, setImagenFrente] = useState<File | null>(null);
  const [imagenDorso, setImagenDorso] = useState<File | null>(null);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    if (!session) return;
    let cancelled = false;

    obtenerEstado(session.token)
      .then((resultado) => {
        if (cancelled) return;
        setEstado(resultado.estado);
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        setFetchError(
          err instanceof IdentidadApiError ? err.message : 'Error al consultar el estado.',
        );
      })
      .finally(() => {
        if (!cancelled) setLoadingEstado(false);
      });

    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [session]);

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();

    if (!session || !imagenFrente || !imagenDorso) return;

    setIsSubmitting(true);
    setSubmitError(null);

    try {
      const resultado = await validarIdentidad(cedula, imagenFrente, imagenDorso, session.token);
      setEstado(resultado.estado as EstadoIdentidadValue);
      if (resultado.estado === 'rechazado') {
        setSubmitError('La identidad fue rechazada. Verifica los datos e inténtalo de nuevo.');
      }
    } catch (err) {
      setSubmitError(
        err instanceof IdentidadApiError ? err.message : 'Error inesperado al validar. Inténtalo de nuevo.',
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  if (loadingEstado) {
    return <div style={containerStyle}>Cargando...</div>;
  }

  if (fetchError !== null) {
    return (
      <div style={containerStyle}>
        <p role="alert">{fetchError}</p>
      </div>
    );
  }

  if (estado === 'aprobado') {
    return (
      <div style={containerStyle}>
        <h1>Verificación de identidad</h1>
        <p>Tu identidad fue verificada exitosamente.</p>
        <Button variant="primary" onClick={onSiguiente}>
          Siguiente
        </Button>
      </div>
    );
  }

  if (estado === 'pendiente') {
    return (
      <div style={containerStyle}>
        <h1>Verificación de identidad</h1>
        <p>Tu validación de identidad está en proceso. Vuelve a intentarlo en unos minutos.</p>
      </div>
    );
  }

  const isFormReady = cedula.trim() !== '' && imagenFrente !== null && imagenDorso !== null;

  return (
    <div style={containerStyle}>
      <h1>Verificación de identidad</h1>
      <p>Sube tu cédula para verificar tu identidad y continuar con el arrendamiento.</p>

      <form onSubmit={handleSubmit} noValidate>
        <div style={fieldStyle}>
          <label htmlFor="vi-cedula">Cédula</label>
          <Input
            id="vi-cedula"
            name="cedula"
            type="text"
            value={cedula}
            onChange={(e: ChangeEvent<HTMLInputElement>) => setCedula(e.target.value)}
          />
        </div>

        <div style={fieldStyle}>
          <label htmlFor="vi-frente">Foto frente del documento</label>
          <input
            id="vi-frente"
            type="file"
            accept="image/*"
            onChange={(e: ChangeEvent<HTMLInputElement>) =>
              setImagenFrente(e.target.files?.[0] ?? null)
            }
          />
        </div>

        <div style={fieldStyle}>
          <label htmlFor="vi-dorso">Foto dorso del documento</label>
          <input
            id="vi-dorso"
            type="file"
            accept="image/*"
            onChange={(e: ChangeEvent<HTMLInputElement>) =>
              setImagenDorso(e.target.files?.[0] ?? null)
            }
          />
        </div>

        {submitError !== null && (
          <p role="alert" style={errorStyle}>
            {submitError}
          </p>
        )}

        <Button type="submit" variant="primary" disabled={!isFormReady || isSubmitting}>
          {isSubmitting ? 'Enviando...' : 'Enviar'}
        </Button>
      </form>
    </div>
  );
};

const containerStyle: React.CSSProperties = {
  fontFamily: 'sans-serif',
  padding: '2rem',
  maxWidth: '640px',
  margin: '0 auto',
};

const fieldStyle: React.CSSProperties = {
  marginBottom: '1rem',
  display: 'flex',
  flexDirection: 'column',
  gap: '0.25rem',
};

const errorStyle: React.CSSProperties = {
  color: 'var(--color-error)',
  marginBottom: '0.75rem',
};

export default ValidarIdentidadPage;
