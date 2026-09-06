import React, { useEffect, useState } from 'react';
import { useAuth } from '@rentame/auth';
import { obtenerEstado as obtenerEstadoIdentidad } from './services/identidad.api';
import type { EstadoIdentidadValue } from './services/identidad.api';
import { obtenerEstado as obtenerEstadoSeguro } from './services/seguro.api';
import type { EstadoSeguroValue } from './services/seguro.api';
import { obtenerEstado as obtenerEstadoFirma } from './services/firma.api';
import ValidarIdentidadPage from './pages/ValidarIdentidadPage';
import ContratarSeguroPage from './pages/ContratarSeguroPage';
import GenerarContratoPage from './pages/GenerarContratoPage';
import MiArrendamientoPage from './pages/MiArrendamientoPage';

/**
 * ArrendamientoRoutes — top-level route component exposed by the
 * arrendamiento-app remote via Module Federation.
 *
 * Navigation model: local state machine (no nested react-router), same
 * pattern `inmuebles-app`'s `PropertyRoutes.tsx`/`BusquedaPublicaRoutes.tsx`
 * use — the shell (or, cross-remote, `inmuebles-app`) already owns the URL.
 *
 * On mount, fetches the 3 domain estados in parallel and picks the first
 * unmet step (design.md's "Wizard de orden estricto"): identidad -> seguro
 * -> firma -> "Mi arrendamiento" (once firma.estado === 'firmado'). Each
 * step's own page component (`ValidarIdentidadPage`, `ContratarSeguroPage`,
 * `GenerarContratoPage`) additionally re-asserts its own precondition via
 * the `on*` callbacks below, in case it is ever reached out of order.
 *
 * `inmuebleId`/`direccionInmueble`/`canonMensual` are only required to
 * reach paso 3 (`GenerarContratoPage`, see its own docstring for why) —
 * they are optional here so this same component can be re-entered later
 * (e.g. from a nav item) once the contrato is already firmado, without an
 * inmueble in context.
 *
 * Consumed by:
 *   const ArrendamientoRoutes = React.lazy(() => import('arrendamientoApp/ArrendamientoRoutes'))
 */

interface Props {
  inmuebleId?: string;
  direccionInmueble?: string;
  canonMensual?: number;
}

type Step = 'identidad' | 'seguro' | 'firma' | 'mi-arrendamiento';

const SEGURO_APROBADO_ESTADOS: EstadoSeguroValue[] = ['aprobada', 'activa'];

function calcularStepInicial(
  identidad: EstadoIdentidadValue,
  seguro: EstadoSeguroValue,
  firmaEstado: string,
): Step {
  if (firmaEstado === 'firmado') return 'mi-arrendamiento';
  if (identidad !== 'aprobado') return 'identidad';
  if (!SEGURO_APROBADO_ESTADOS.includes(seguro)) return 'seguro';
  return 'firma';
}

const ArrendamientoRoutes: React.FC<Props> = ({
  inmuebleId,
  direccionInmueble,
  canonMensual,
}) => {
  const { session } = useAuth();

  const [step, setStep] = useState<Step | null>(null);
  const [identidadEstado, setIdentidadEstado] = useState<EstadoIdentidadValue>('no_iniciado');
  const [seguroEstado, setSeguroEstado] = useState<EstadoSeguroValue>('no_iniciado');
  const [arrendamientoActivoId, setArrendamientoActivoId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!session) return;
    let cancelled = false;

    Promise.all([
      obtenerEstadoIdentidad(session.token),
      obtenerEstadoSeguro(session.token),
      obtenerEstadoFirma(session.token),
    ])
      .then(([identidad, seguro, firma]) => {
        if (cancelled) return;
        setIdentidadEstado(identidad.estado);
        setSeguroEstado(seguro.estado);
        if (firma.arrendamientoActivoId) {
          setArrendamientoActivoId(firma.arrendamientoActivoId);
        }
        setStep(calcularStepInicial(identidad.estado, seguro.estado, firma.estado));
      })
      .catch(() => {
        if (cancelled) return;
        setError('Error al consultar el estado del arrendamiento.');
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [session]);

  if (loading || step === null) {
    return (
      <div data-testid="arrendamiento-routes" style={{ fontFamily: 'sans-serif', padding: '2rem' }}>
        Cargando...
      </div>
    );
  }

  if (error !== null) {
    return (
      <div data-testid="arrendamiento-routes" style={{ fontFamily: 'sans-serif', padding: '2rem' }}>
        <p role="alert">{error}</p>
      </div>
    );
  }

  return (
    <div data-testid="arrendamiento-routes">
      {step === 'identidad' && (
        <ValidarIdentidadPage
          onSiguiente={() => {
            setIdentidadEstado('aprobado');
            setStep('seguro');
          }}
        />
      )}

      {step === 'seguro' && (
        <ContratarSeguroPage
          identidadEstado={identidadEstado}
          onVolverAIdentidad={() => setStep('identidad')}
          onSiguiente={() => {
            setSeguroEstado('aprobada');
            setStep('firma');
          }}
        />
      )}

      {step === 'firma' &&
        (inmuebleId === undefined ? (
          <div style={{ fontFamily: 'sans-serif', padding: '2rem' }}>
            <p>
              Para continuar con la firma del contrato, vuelve al inmueble desde el que iniciaste
              la solicitud de arrendamiento.
            </p>
          </div>
        ) : (
          <GenerarContratoPage
            seguroEstado={seguroEstado}
            onVolverASeguro={() => setStep('seguro')}
            inmuebleId={inmuebleId}
            direccionInmueble={direccionInmueble ?? ''}
            canonMensual={canonMensual ?? 0}
            onFirmado={(id) => {
              setArrendamientoActivoId(id);
              setStep('mi-arrendamiento');
            }}
          />
        ))}

      {step === 'mi-arrendamiento' && arrendamientoActivoId !== null && (
        <MiArrendamientoPage arrendamientoActivoId={arrendamientoActivoId} />
      )}
    </div>
  );
};

export default ArrendamientoRoutes;
