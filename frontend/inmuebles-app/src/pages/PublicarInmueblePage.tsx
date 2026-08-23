/**
 * PublicarInmueblePage — formulario controlado para publicar un inmueble.
 *
 * Contract (from task 16 tests):
 *  - Every field is accessible via getByLabelText with the patterns asserted
 *    in the test file.
 *  - The "Publicar" submit button is disabled until all required fields have
 *    a value AND at least 1 photo is attached.
 *  - Selecting more than 10 photos at once shows a role="alert" error and
 *    rejects the selection (fotos count stays at 0).
 *  - Submitting with 0 photos (e.g. via Enter key or fireEvent.submit) shows
 *    a role="alert" error and does NOT call the service.
 *  - On success, shows a confirmation message containing "publicado".
 *  - The JWT token is read from @rentame/auth's useAuth() (session.token).
 */
import React, { ChangeEvent, FormEvent, useEffect, useState } from 'react';
import { useAuth } from '@rentame/auth';
import { Button, Input, Select, Textarea } from '@rentame/ui';
import { Check } from 'lucide-react';
import { InmueblesApiError, publicarInmueble } from '../services/inmuebles.api';
import type { PublicarInmuebleInput } from '../services/inmuebles.api';
import { listarPropietariosVinculados } from '../services/agencias.api';
import type { PropietarioVinculado } from '../services/agencias.api';
import FotoDropzone from '../components/FotoDropzone';
import { cardStyle, gridRowStyle, sectionStyle, sectionTitleStyle } from '../styles/forms';

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const MAX_FOTOS = 10;

// ---------------------------------------------------------------------------
// Local types
// ---------------------------------------------------------------------------

interface FormFields {
  direccion: string;
  barrio: string;
  ciudad: string;
  tipo: string;
  areaM2: string;
  habitaciones: string;
  banos: string;
  valorMensual: string;
  descripcion: string;
}

const EMPTY_FORM: FormFields = {
  direccion: '',
  barrio: '',
  ciudad: '',
  tipo: '',
  areaM2: '',
  habitaciones: '',
  banos: '',
  valorMensual: '',
  descripcion: '',
};

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

interface Props {
  /** Called to navigate back to the list without publishing. */
  onVolver?: () => void;
  /** Called immediately after successful publication (e.g. to refresh the list
   * and navigate back). When omitted the success screen with "Publicar otro"
   * is shown instead, keeping the standalone behaviour intact. */
  onPublicado?: () => void;
}

const PublicarInmueblePage: React.FC<Props> = ({ onVolver, onPublicado }) => {
  const { session, role } = useAuth();

  const [fields, setFields] = useState<FormFields>(EMPTY_FORM);
  const [fotos, setFotos] = useState<File[]>([]);
  const [fotoError, setFotoError] = useState<string | null>(null);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [published, setPublished] = useState(false);

  // ---------------------------------------------------------------------------
  // Agente-only: propietario selector
  // ---------------------------------------------------------------------------

  const [propietarios, setPropietarios] = useState<PropietarioVinculado[]>([]);
  const [propietarioId, setPropietarioId] = useState<string>('');

  useEffect(() => {
    if (role !== 'agente' || !session) return;

    listarPropietariosVinculados(session.token)
      .then(setPropietarios)
      .catch(() => {
        // Non-critical — the selector will remain empty; the submit guard
        // will prevent publishing without a valid propietarioId.
      });
  }, [role, session]);

  // -------------------------------------------------------------------------
  // Derived state
  // -------------------------------------------------------------------------

  const allTextFieldsFilled =
    fields.direccion.trim() !== '' &&
    fields.barrio.trim() !== '' &&
    fields.ciudad.trim() !== '' &&
    fields.tipo !== '' &&
    fields.areaM2 !== '' &&
    fields.habitaciones !== '' &&
    fields.banos !== '' &&
    fields.valorMensual !== '' &&
    fields.descripcion.trim() !== '';

  const isFormReady =
    allTextFieldsFilled &&
    fotos.length > 0 &&
    fotoError === null &&
    (role !== 'agente' || propietarioId !== '');

  // -------------------------------------------------------------------------
  // Handlers
  // -------------------------------------------------------------------------

  const handleFieldChange = (
    e: ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>,
  ) => {
    const { name, value } = e.target;
    setFields((prev) => ({ ...prev, [name]: value }));
  };

  const handleFotosChange = (files: File[]) => {
    if (files.length > MAX_FOTOS) {
      setFotoError(`Solo se permiten máximo ${MAX_FOTOS} fotos. Seleccionaste ${files.length}.`);
      setFotos([]);
      return;
    }

    setFotoError(null);
    setFotos(files);
  };

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();

    if (fotos.length === 0) {
      setFotoError('Debes adjuntar al menos 1 foto.');
      return;
    }

    if (!session) {
      setSubmitError('Sesión no válida. Inicia sesión nuevamente.');
      return;
    }

    const datos: PublicarInmuebleInput = {
      direccion: fields.direccion,
      barrio: fields.barrio,
      ciudad: fields.ciudad,
      tipo: fields.tipo,
      areaM2: parseFloat(fields.areaM2),
      habitaciones: parseInt(fields.habitaciones, 10),
      banos: parseInt(fields.banos, 10),
      valorMensual: parseFloat(fields.valorMensual),
      descripcion: fields.descripcion,
      ...(role === 'agente' && propietarioId ? { propietarioId } : {}),
    };

    setIsSubmitting(true);
    setSubmitError(null);

    try {
      await publicarInmueble(datos, fotos, session.token);
      if (onPublicado) {
        onPublicado();
      } else {
        setPublished(true);
      }
    } catch (err) {
      if (err instanceof InmueblesApiError) {
        setSubmitError(err.message);
      } else {
        setSubmitError('Error inesperado al publicar. Inténtalo de nuevo.');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  // -------------------------------------------------------------------------
  // Success state
  // -------------------------------------------------------------------------

  if (published) {
    return (
      <div style={containerStyle}>
        <div style={successStyle}>
          <span data-testid="icono-exito" aria-hidden="true" style={successIconStyle}>
            <Check size={20} />
          </span>
          <p>El inmueble fue publicado exitosamente.</p>
        </div>
        <Button
          variant="secondary"
          onClick={() => {
            setPublished(false);
            setFields(EMPTY_FORM);
            setFotos([]);
            setFotoError(null);
            setSubmitError(null);
          }}
        >
          Publicar otro
        </Button>
      </div>
    );
  }

  // -------------------------------------------------------------------------
  // Form — active error: fotoError takes precedence over submitError
  // -------------------------------------------------------------------------

  const activeError = fotoError ?? submitError;

  const valorMensualPreview =
    fields.valorMensual !== ''
      ? new Intl.NumberFormat('es-CO', {
          style: 'currency',
          currency: 'COP',
          maximumFractionDigits: 0,
        }).format(Number(fields.valorMensual))
      : null;

  return (
    <div style={containerStyle}>
      {onVolver && (
        <Button type="button" variant="secondary" onClick={onVolver}>
          Volver a mis inmuebles
        </Button>
      )}
      <h1>Publicar inmueble</h1>
      <div style={cardStyle}>
        <form onSubmit={handleSubmit} noValidate>
          <section style={sectionStyle}>
            <h2 style={sectionTitleStyle}>Ubicación</h2>

            <div style={fieldStyle}>
              <label htmlFor="pub-direccion">Dirección</label>
              <Input
                id="pub-direccion"
                name="direccion"
                type="text"
                value={fields.direccion}
                onChange={handleFieldChange}
              />
            </div>

            <div style={fieldStyle}>
              <label htmlFor="pub-barrio">Barrio</label>
              <Input
                id="pub-barrio"
                name="barrio"
                type="text"
                value={fields.barrio}
                onChange={handleFieldChange}
              />
            </div>

            <div style={fieldStyle}>
              <label htmlFor="pub-ciudad">Ciudad</label>
              <Input
                id="pub-ciudad"
                name="ciudad"
                type="text"
                value={fields.ciudad}
                onChange={handleFieldChange}
              />
            </div>
          </section>

          <section style={sectionStyle}>
            <h2 style={sectionTitleStyle}>Características</h2>

            <div style={fieldStyle}>
              <label htmlFor="pub-tipo">Tipo de inmueble</label>
              <Select
                id="pub-tipo"
                name="tipo"
                value={fields.tipo}
                onChange={handleFieldChange}
              >
                <option value="">Seleccione un tipo...</option>
                <option value="apartamento">Apartamento</option>
                <option value="casa">Casa</option>
                <option value="local">Local comercial</option>
                <option value="oficina">Oficina</option>
                <option value="bodega">Bodega</option>
              </Select>
            </div>

            <div style={gridRowStyle}>
              <div style={fieldStyle}>
                <label htmlFor="pub-areaM2">Área en m²</label>
                <Input
                  id="pub-areaM2"
                  name="areaM2"
                  type="number"
                  min="1"
                  step="0.01"
                  value={fields.areaM2}
                  onChange={handleFieldChange}
                />
              </div>

              <div style={fieldStyle}>
                <label htmlFor="pub-habitaciones">Habitaciones</label>
                <Input
                  id="pub-habitaciones"
                  name="habitaciones"
                  type="number"
                  min="0"
                  value={fields.habitaciones}
                  onChange={handleFieldChange}
                />
              </div>

              <div style={fieldStyle}>
                <label htmlFor="pub-banos">Baños</label>
                <Input
                  id="pub-banos"
                  name="banos"
                  type="number"
                  min="0"
                  value={fields.banos}
                  onChange={handleFieldChange}
                />
              </div>
            </div>
          </section>

          <section style={sectionStyle}>
            <h2 style={sectionTitleStyle}>Precio y descripción</h2>

            <div style={fieldStyle}>
              <label htmlFor="pub-valorMensual">Valor mensual</label>
              <Input
                id="pub-valorMensual"
                name="valorMensual"
                type="number"
                min="1"
                value={fields.valorMensual}
                onChange={handleFieldChange}
              />
              {valorMensualPreview !== null && (
                <small style={currencyPreviewStyle}>{valorMensualPreview}</small>
              )}
            </div>

            <div style={fieldStyle}>
              <label htmlFor="pub-descripcion">Descripción</label>
              <Textarea
                id="pub-descripcion"
                name="descripcion"
                rows={4}
                value={fields.descripcion}
                onChange={handleFieldChange}
              />
            </div>
          </section>

          {role === 'agente' && (
            <section style={sectionStyle}>
              <h2 style={sectionTitleStyle}>Propietario</h2>
              <div style={fieldStyle}>
                <label htmlFor="pub-propietario">Propietario</label>
                <Select
                  id="pub-propietario"
                  value={propietarioId}
                  onChange={(e) => setPropietarioId(e.target.value)}
                >
                  <option value="">Seleccione un propietario...</option>
                  {propietarios
                    .filter((p) => p.estado === 'activa')
                    .map((p) => (
                      <option key={p.id} value={p.propietarioId}>
                        {p.propietarioEmail}
                      </option>
                    ))}
                </Select>
              </div>
            </section>
          )}

          <section style={sectionStyle}>
            <h2 style={sectionTitleStyle}>Fotos</h2>
            <div style={fieldStyle}>
              <label htmlFor="pub-fotos">Fotos</label>
              <FotoDropzone
                id="pub-fotos"
                fotos={fotos}
                maxFotos={MAX_FOTOS}
                onFilesSelected={handleFotosChange}
              />
            </div>
          </section>

          {activeError !== null && (
            <p role="alert" style={errorStyle}>
              {activeError}
            </p>
          )}

          {!isFormReady && (
            <p style={hintStyle}>
              Completa todos los campos y adjunta al menos 1 foto para publicar.
            </p>
          )}

          <Button type="submit" variant="primary" disabled={!isFormReady || isSubmitting}>
            {isSubmitting ? 'Publicando...' : 'Publicar'}
          </Button>
        </form>
      </div>
    </div>
  );
};

// ---------------------------------------------------------------------------
// Styles (inline — consistent with shell/TokenLoginPage.tsx)
// ---------------------------------------------------------------------------

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

const hintStyle: React.CSSProperties = {
  color: 'var(--color-text-secondary)',
  fontSize: '0.9rem',
  marginBottom: '0.75rem',
};

const currencyPreviewStyle: React.CSSProperties = {
  color: 'var(--color-text-secondary)',
  fontSize: '0.85rem',
};

const successStyle: React.CSSProperties = {
  display: 'flex',
  alignItems: 'center',
  gap: '0.75rem',
  marginBottom: '1rem',
};

const successIconStyle: React.CSSProperties = {
  display: 'inline-flex',
  alignItems: 'center',
  justifyContent: 'center',
  width: '2.5rem',
  height: '2.5rem',
  borderRadius: '50%',
  backgroundColor: 'var(--color-success)',
  color: 'var(--color-surface)',
  fontSize: '1.25rem',
  fontWeight: 700,
  flexShrink: 0,
};

export default PublicarInmueblePage;
