/**
 * MiArrendamientoPage — historial de pagos del arrendamiento activo del
 * inquilino, con un botón "Pagar" para el `Pago` pendiente.
 *
 * Distinct from the wizard (design.md decisión 4): the wizard is a
 * one-time onboarding flow that ends when `ArrendamientoActivo` is
 * created; pagar is a recurring monthly action, so it lives here instead
 * of as a fifth wizard step.
 *
 * Fetches the full historial via `pagos.api.ts`'s `obtenerHistorial` on
 * mount (any estado, per spec.md's "sin filtrar por estado"). Shows a
 * "Pagar" button only next to a `Pago` in estado `pendiente`; clicking it
 * calls `iniciarPago` and replaces that row with the resolved `Pago` (the
 * current `FakeAdapter` resolves synchronously to `completado` — see
 * `iniciarPago`'s own docstring in
 * `backend/pagos/application/iniciar_pago.py`).
 */
import React, { useEffect, useState } from 'react';
import { useAuth } from '@rentame/auth';
import { Badge, Button } from '@rentame/ui';
import { iniciarPago, obtenerHistorial, PagosApiError } from '../services/pagos.api';
import type { Pago } from '../services/pagos.api';

interface Props {
  arrendamientoActivoId: string;
}

function formatMoney(valor: number): string {
  return valor.toLocaleString('es-CO');
}

function badgeVariantFor(estado: Pago['estado']): 'available' | 'unavailable' | 'new' {
  if (estado === 'completado') return 'available';
  if (estado === 'fallido') return 'unavailable';
  return 'new';
}

const MiArrendamientoPage: React.FC<Props> = ({ arrendamientoActivoId }) => {
  const { session } = useAuth();

  const [pagos, setPagos] = useState<Pago[]>([]);
  const [loading, setLoading] = useState(true);
  const [fetchError, setFetchError] = useState<string | null>(null);
  const [payingId, setPayingId] = useState<string | null>(null);
  const [payError, setPayError] = useState<string | null>(null);

  useEffect(() => {
    if (!session) return;
    let cancelled = false;

    obtenerHistorial(arrendamientoActivoId, session.token)
      .then((resultado) => {
        if (cancelled) return;
        setPagos(resultado);
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        setFetchError(
          err instanceof PagosApiError ? err.message : 'Error al consultar el historial.',
        );
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [arrendamientoActivoId, session]);

  const handlePagar = async (pagoId: string) => {
    if (!session) return;

    setPayingId(pagoId);
    setPayError(null);

    try {
      const actualizado = await iniciarPago(pagoId, session.token);
      setPagos((prev) => prev.map((p) => (p.id === actualizado.id ? actualizado : p)));
    } catch (err) {
      setPayError(
        err instanceof PagosApiError ? err.message : 'Error inesperado al iniciar el pago.',
      );
    } finally {
      setPayingId(null);
    }
  };

  if (loading) {
    return <div style={containerStyle}>Cargando...</div>;
  }

  if (fetchError !== null) {
    return (
      <div style={containerStyle}>
        <p role="alert">{fetchError}</p>
      </div>
    );
  }

  return (
    <div style={containerStyle}>
      <h1>Mi arrendamiento</h1>

      {payError !== null && (
        <p role="alert" style={errorStyle}>
          {payError}
        </p>
      )}

      {pagos.length === 0 ? (
        <p>Todavía no tienes pagos registrados.</p>
      ) : (
        <ul style={listStyle}>
          {pagos.map((pago) => (
            <li key={pago.id} style={rowStyle}>
              <span>{pago.fechaLimite}</span>
              <span>${formatMoney(pago.monto)}</span>
              <Badge variant={badgeVariantFor(pago.estado)}>{pago.estado}</Badge>
              {pago.estado === 'pendiente' && (
                <Button
                  variant="primary"
                  size="sm"
                  disabled={payingId === pago.id}
                  onClick={() => handlePagar(pago.id)}
                >
                  {payingId === pago.id ? 'Pagando...' : 'Pagar'}
                </Button>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};

const containerStyle: React.CSSProperties = {
  fontFamily: 'sans-serif',
  padding: '2rem',
  maxWidth: '640px',
  margin: '0 auto',
};

const listStyle: React.CSSProperties = {
  listStyle: 'none',
  padding: 0,
  margin: 0,
  display: 'flex',
  flexDirection: 'column',
  gap: '0.75rem',
};

const rowStyle: React.CSSProperties = {
  display: 'flex',
  alignItems: 'center',
  gap: '1rem',
  padding: '0.75rem',
  border: '1px solid var(--color-border)',
  borderRadius: 'var(--radius-card)',
};

const errorStyle: React.CSSProperties = {
  color: 'var(--color-error)',
  marginBottom: '0.75rem',
};

export default MiArrendamientoPage;
