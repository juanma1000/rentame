/**
 * GenerarContratoPage — wizard paso 3: generar y firmar el contrato de
 * arrendamiento.
 *
 * `seguroEstado` is passed down by `ArrendamientoRoutes` (already fetched
 * while deciding which step to render), same gating pattern
 * `ContratarSeguroPage` uses for `identidadEstado`. When it is not
 * `'aprobada'`/`'activa'`, this page calls `onVolverASeguro()` on mount and
 * renders nothing else.
 *
 * `inmuebleId`/`direccionInmueble`/`canonMensual` are also passed down —
 * they come from the inmueble the wizard was entered from
 * (`InmuebleDetallePublicoPage` -> `ArrendamientoRoutes`), since `Contrato`
 * is the first place an inmueble concrete enters this flow (design.md's
 * Context section) and the backend's `GenerarContratoCommand` requires
 * them. `nombreInquilino`/`nombrePropietario` are collected in this page's
 * form (the JWT carries no name, only `sub`/`rol`); `duracionMeses`
 * defaults to 12 months (not specified anywhere in the PRD/specs — a
 * reasonable, documented default, editable in the form).
 *
 * Once seguro is aprobada, fetches the firma estado (`firma.api.ts`'s
 * `obtenerEstado`): `no_iniciado` shows the form, `enviado_a_firma` shows a
 * waiting message (the `ViafirmaAdapter`'s webhook resolves it
 * asynchronously — see `firma_contrato`'s own docs), `firmado` calls
 * `onFirmado(arrendamientoActivoId)` immediately (the wizard is over — the
 * caller navigates to "Mi arrendamiento").
 */
import React, { ChangeEvent, FormEvent, useEffect, useState } from 'react';
import { useAuth } from '@rentame/auth';
import { Button, Input } from '@rentame/ui';
import { FirmaApiError, generarContrato, obtenerEstado } from '../services/firma.api';
import type { EstadoFirmaValue } from '../services/firma.api';
import type { EstadoSeguroValue } from '../services/seguro.api';

const DURACION_MESES_DEFAULT = 12;

interface Props {
  /** Fetched by `ArrendamientoRoutes` — gates access to this step. */
  seguroEstado: EstadoSeguroValue;
  /** Called (on mount) when `seguroEstado` is not `aprobada`/`activa`. */
  onVolverASeguro: () => void;
  /** Inmueble the wizard was entered from — threaded down from
   * `InmuebleDetallePublicoPage`. */
  inmuebleId: string;
  direccionInmueble: string;
  canonMensual: number;
  /** Called once the contrato reaches `firmado`, with the newly created
   * `ArrendamientoActivo`'s id. */
  onFirmado: (arrendamientoActivoId: string) => void;
}

const SEGURO_APROBADO_ESTADOS: EstadoSeguroValue[] = ['aprobada', 'activa'];

const GenerarContratoPage: React.FC<Props> = ({
  seguroEstado,
  onVolverASeguro,
  inmuebleId,
  direccionInmueble,
  canonMensual,
  onFirmado,
}) => {
  const { session } = useAuth();

  const seguroAprobado = SEGURO_APROBADO_ESTADOS.includes(seguroEstado);

  const [estado, setEstado] = useState<EstadoFirmaValue | null>(null);
  const [loadingEstado, setLoadingEstado] = useState(true);
  const [fetchError, setFetchError] = useState<string | null>(null);

  const [nombreInquilino, setNombreInquilino] = useState('');
  const [nombrePropietario, setNombrePropietario] = useState('');
  const [duracionMeses, setDuracionMeses] = useState(String(DURACION_MESES_DEFAULT));
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Gate: redirect back to paso 2 when seguro is not aprobada/activa yet.
  useEffect(() => {
    if (!seguroAprobado) {
      onVolverASeguro();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [seguroAprobado]);

  useEffect(() => {
    if (!seguroAprobado || !session) return;
    let cancelled = false;

    obtenerEstado(session.token)
      .then((resultado) => {
        if (cancelled) return;
        setEstado(resultado.estado);
        if (resultado.estado === 'firmado' && resultado.arrendamientoActivoId) {
          onFirmado(resultado.arrendamientoActivoId);
        }
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        setFetchError(
          err instanceof FirmaApiError ? err.message : 'Error al consultar el estado.',
        );
      })
      .finally(() => {
        if (!cancelled) setLoadingEstado(false);
      });

    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [seguroAprobado, session]);

  if (!seguroAprobado) {
    return null;
  }

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();

    if (!session) return;

    setIsSubmitting(true);
    setSubmitError(null);

    try {
      const contrato = await generarContrato(
        {
          inmuebleId,
          nombreInquilino,
          nombrePropietario,
          direccionInmueble,
          canonMensual,
          duracionMeses: parseInt(duracionMeses, 10),
        },
        session.token,
      );
      setEstado(contrato.estado as EstadoFirmaValue);
    } catch (err) {
      setSubmitError(
        err instanceof FirmaApiError
          ? err.message
          : 'Error inesperado al generar el contrato. Inténtalo de nuevo.',
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

  if (estado === 'firmado') {
    // onFirmado already fired from the effect above — nothing to render,
    // the caller navigates away to "Mi arrendamiento".
    return null;
  }

  if (estado === 'enviado_a_firma' || estado === 'borrador') {
    return (
      <div style={containerStyle}>
        <h1>Firma del contrato</h1>
        <p>Esperando el resultado de la firma electrónica del contrato...</p>
      </div>
    );
  }

  const isFormReady =
    nombreInquilino.trim() !== '' &&
    nombrePropietario.trim() !== '' &&
    duracionMeses.trim() !== '';

  return (
    <div style={containerStyle}>
      <h1>Firma del contrato</h1>
      {(estado === 'rechazado' || estado === 'expirado') && (
        <p role="alert" style={errorStyle}>
          El proceso de firma anterior terminó en estado &quot;{estado}&quot;. Puedes intentarlo
          de nuevo.
        </p>
      )}
      <p>Confirma los datos para generar el contrato de arrendamiento y enviarlo a firma.</p>

      <form onSubmit={handleSubmit} noValidate>
        <div style={fieldStyle}>
          <label htmlFor="gc-nombre-inquilino">Nombre del inquilino</label>
          <Input
            id="gc-nombre-inquilino"
            name="nombreInquilino"
            type="text"
            value={nombreInquilino}
            onChange={(e: ChangeEvent<HTMLInputElement>) => setNombreInquilino(e.target.value)}
          />
        </div>

        <div style={fieldStyle}>
          <label htmlFor="gc-nombre-propietario">Nombre del propietario</label>
          <Input
            id="gc-nombre-propietario"
            name="nombrePropietario"
            type="text"
            value={nombrePropietario}
            onChange={(e: ChangeEvent<HTMLInputElement>) => setNombrePropietario(e.target.value)}
          />
        </div>

        <div style={fieldStyle}>
          <label htmlFor="gc-duracion-meses">Duración (meses)</label>
          <Input
            id="gc-duracion-meses"
            name="duracionMeses"
            type="number"
            min="1"
            value={duracionMeses}
            onChange={(e: ChangeEvent<HTMLInputElement>) => setDuracionMeses(e.target.value)}
          />
        </div>

        {submitError !== null && (
          <p role="alert" style={errorStyle}>
            {submitError}
          </p>
        )}

        <Button type="submit" variant="primary" disabled={!isFormReady || isSubmitting}>
          {isSubmitting ? 'Generando...' : 'Generar contrato'}
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

export default GenerarContratoPage;
