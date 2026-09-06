/**
 * ContratarSeguroPage — wizard paso 2: contratar seguro de arrendamiento.
 *
 * `identidadEstado` is passed down by `ArrendamientoRoutes` (which already
 * fetched it while deciding which step to render) rather than re-fetched
 * here. When it is not `'aprobado'`, this page immediately calls
 * `onVolverAIdentidad()` and renders nothing else — a defensive gate,
 * matching the "no se puede acceder al paso de seguro sin identidad
 * verificada" requirement, in case a caller ever mounts this step out of
 * order.
 *
 * Once identidad is aprobado, fetches the seguro estado
 * (`seguro.api.ts`'s `obtenerEstado`) and behaves like
 * `ValidarIdentidadPage`: `no_iniciado`/`rechazada` shows the form
 * (cédula + documentos), `aprobada` shows the prima mensual and a
 * "Siguiente" control.
 */
import React, { ChangeEvent, FormEvent, useEffect, useState } from 'react';
import { useAuth } from '@rentame/auth';
import { Button, Input } from '@rentame/ui';
import { contratarSeguro, obtenerEstado, SeguroApiError } from '../services/seguro.api';
import type { EstadoSeguroValue } from '../services/seguro.api';
import type { EstadoIdentidadValue } from '../services/identidad.api';

interface Props {
  /** Fetched by `ArrendamientoRoutes` — gates access to this step. */
  identidadEstado: EstadoIdentidadValue;
  /** Called (on mount) when `identidadEstado !== 'aprobado'`. */
  onVolverAIdentidad: () => void;
  /** Called when seguro is (already, or just became) aprobada and the
   * inquilino chooses to advance to the next step of the wizard. */
  onSiguiente: () => void;
}

function formatMoney(valor: number): string {
  return valor.toLocaleString('es-CO');
}

const ContratarSeguroPage: React.FC<Props> = ({
  identidadEstado,
  onVolverAIdentidad,
  onSiguiente,
}) => {
  const { session } = useAuth();

  const [estado, setEstado] = useState<EstadoSeguroValue | null>(null);
  const [primaMensual, setPrimaMensual] = useState<number | null>(null);
  const [loadingEstado, setLoadingEstado] = useState(true);
  const [fetchError, setFetchError] = useState<string | null>(null);

  const [cedula, setCedula] = useState('');
  const [documentos, setDocumentos] = useState<File[]>([]);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Gate: redirect back to paso 1 when identidad is not aprobado yet.
  useEffect(() => {
    if (identidadEstado !== 'aprobado') {
      onVolverAIdentidad();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [identidadEstado]);

  useEffect(() => {
    if (identidadEstado !== 'aprobado' || !session) return;
    let cancelled = false;

    obtenerEstado(session.token)
      .then((resultado) => {
        if (cancelled) return;
        setEstado(resultado.estado);
        setPrimaMensual(resultado.primaMensual);
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        setFetchError(
          err instanceof SeguroApiError ? err.message : 'Error al consultar el estado.',
        );
      })
      .finally(() => {
        if (!cancelled) setLoadingEstado(false);
      });

    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [identidadEstado, session]);

  if (identidadEstado !== 'aprobado') {
    return null;
  }

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();

    if (!session || documentos.length === 0) return;

    setIsSubmitting(true);
    setSubmitError(null);

    try {
      const poliza = await contratarSeguro(cedula, documentos, session.token);
      setEstado(poliza.estado as EstadoSeguroValue);
      setPrimaMensual(poliza.primaMensual);
      if (poliza.estado === 'rechazada') {
        setSubmitError('La póliza fue rechazada. Verifica los documentos e inténtalo de nuevo.');
      }
    } catch (err) {
      setSubmitError(
        err instanceof SeguroApiError ? err.message : 'Error inesperado al contratar. Inténtalo de nuevo.',
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

  if (estado === 'aprobada' || estado === 'activa') {
    return (
      <div style={containerStyle}>
        <h1>Seguro de arrendamiento</h1>
        <p>Tu póliza fue aprobada.</p>
        {primaMensual !== null && <p>Prima mensual: ${formatMoney(primaMensual)}</p>}
        <Button variant="primary" onClick={onSiguiente}>
          Siguiente
        </Button>
      </div>
    );
  }

  if (estado === 'pendiente') {
    return (
      <div style={containerStyle}>
        <h1>Seguro de arrendamiento</h1>
        <p>Tu póliza está en proceso de análisis. Vuelve a intentarlo en unos minutos.</p>
      </div>
    );
  }

  const isFormReady = cedula.trim() !== '' && documentos.length > 0;

  return (
    <div style={containerStyle}>
      <h1>Seguro de arrendamiento</h1>
      <p>Sube tu cédula y los documentos de soporte para contratar el seguro de arrendamiento.</p>

      <form onSubmit={handleSubmit} noValidate>
        <div style={fieldStyle}>
          <label htmlFor="cs-cedula">Cédula</label>
          <Input
            id="cs-cedula"
            name="cedula"
            type="text"
            value={cedula}
            onChange={(e: ChangeEvent<HTMLInputElement>) => setCedula(e.target.value)}
          />
        </div>

        <div style={fieldStyle}>
          <label htmlFor="cs-documentos">Documentos (desprendibles de pago, certificado laboral)</label>
          <input
            id="cs-documentos"
            type="file"
            accept="application/pdf,image/*"
            multiple
            onChange={(e: ChangeEvent<HTMLInputElement>) =>
              setDocumentos(Array.from(e.target.files ?? []))
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

export default ContratarSeguroPage;
