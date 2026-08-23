/**
 * EditarInmueblePage — formulario controlado para editar un inmueble ya
 * publicado.
 *
 * Contract (from task 17 tests):
 *  - Receives the inmueble to edit as a required prop (`inmueble: Inmueble`).
 *    The page never fetches data itself — it is a pure, fully-controlled form.
 *  - Every field is pre-filled from `props.inmueble` on mount and is
 *    accessible via getByLabelText with the same label patterns as
 *    PublicarInmueblePage.
 *  - There is no fotos input — editing never touches photos.
 *  - The "Guardar cambios" submit button is enabled whenever all required
 *    text fields are filled.
 *  - On success, shows a confirmation message containing "actualizado".
 *  - The JWT token is read from @rentame/auth's useAuth() (session.token).
 *
 * Visual pattern: mirrors `PublicarInmueblePage.tsx` (task 4.2 of
 * `ui-formulario-inmueble`) — same `cardStyle`, sections ("Ubicación",
 * "Características", "Precio y descripción"), `styles/forms.ts` tokens and
 * currency preview. This form has no Fotos/Propietario sections. The success
 * icon is added purely for visual consistency with Publicar — no test
 * requires it here.
 */
import React, { ChangeEvent, FormEvent, useState } from 'react';
import { useAuth } from '@rentame/auth';
import { Button, Input, Select, Textarea } from '@rentame/ui';
import { Check } from 'lucide-react';
import { editarInmueble, InmueblesApiError } from '../services/inmuebles.api';
import type { EditarInmuebleInput, Inmueble } from '../services/inmuebles.api';
import { cardStyle, gridRowStyle, sectionStyle, sectionTitleStyle } from '../styles/forms';

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

function fromInmueble(inmueble: Inmueble): FormFields {
  return {
    direccion: inmueble.direccion,
    barrio: inmueble.barrio,
    ciudad: inmueble.ciudad,
    tipo: inmueble.tipo,
    areaM2: String(inmueble.areaM2),
    habitaciones: String(inmueble.habitaciones),
    banos: String(inmueble.banos),
    valorMensual: String(inmueble.valorMensual),
    descripcion: inmueble.descripcion,
  };
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

interface Props {
  inmueble: Inmueble;
  /** Called to navigate back to the list without saving. */
  onVolver?: () => void;
  /** Called immediately after a successful save. When omitted the success
   * screen is shown instead, keeping the standalone behaviour intact. */
  onActualizado?: () => void;
}

const EditarInmueblePage: React.FC<Props> = ({ inmueble, onVolver, onActualizado }) => {
  const { session } = useAuth();

  const [fields, setFields] = useState<FormFields>(() => fromInmueble(inmueble));
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [updated, setUpdated] = useState(false);

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

  const isFormReady = allTextFieldsFilled;

  // -------------------------------------------------------------------------
  // Handlers
  // -------------------------------------------------------------------------

  const handleFieldChange = (
    e: ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>,
  ) => {
    const { name, value } = e.target;
    setFields((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();

    if (!session) {
      setSubmitError('Sesión no válida. Inicia sesión nuevamente.');
      return;
    }

    const datos: EditarInmuebleInput = {
      direccion: fields.direccion,
      barrio: fields.barrio,
      ciudad: fields.ciudad,
      tipo: fields.tipo,
      areaM2: parseFloat(fields.areaM2),
      habitaciones: parseInt(fields.habitaciones, 10),
      banos: parseInt(fields.banos, 10),
      valorMensual: parseFloat(fields.valorMensual),
      descripcion: fields.descripcion,
    };

    setIsSubmitting(true);
    setSubmitError(null);

    try {
      await editarInmueble(inmueble.id, datos, session.token);
      if (onActualizado) {
        onActualizado();
      } else {
        setUpdated(true);
      }
    } catch (err) {
      if (err instanceof InmueblesApiError) {
        setSubmitError(err.message);
      } else {
        setSubmitError('Error inesperado al guardar. Inténtalo de nuevo.');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  // -------------------------------------------------------------------------
  // Success state
  // -------------------------------------------------------------------------

  if (updated) {
    return (
      <div style={containerStyle}>
        <div style={successStyle}>
          <span data-testid="icono-exito" aria-hidden="true" style={successIconStyle}>
            <Check size={20} />
          </span>
          <p>El inmueble fue actualizado exitosamente.</p>
        </div>
      </div>
    );
  }

  // -------------------------------------------------------------------------
  // Form
  // -------------------------------------------------------------------------

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
      <h1>Editar inmueble</h1>
      <div style={cardStyle}>
        <form onSubmit={handleSubmit} noValidate>
          <section style={sectionStyle}>
            <h2 style={sectionTitleStyle}>Ubicación</h2>

            <div style={fieldStyle}>
              <label htmlFor="edit-direccion">Dirección</label>
              <Input
                id="edit-direccion"
                name="direccion"
                type="text"
                value={fields.direccion}
                onChange={handleFieldChange}
              />
            </div>

            <div style={fieldStyle}>
              <label htmlFor="edit-barrio">Barrio</label>
              <Input
                id="edit-barrio"
                name="barrio"
                type="text"
                value={fields.barrio}
                onChange={handleFieldChange}
              />
            </div>

            <div style={fieldStyle}>
              <label htmlFor="edit-ciudad">Ciudad</label>
              <Input
                id="edit-ciudad"
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
              <label htmlFor="edit-tipo">Tipo de inmueble</label>
              <Select
                id="edit-tipo"
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
                <label htmlFor="edit-areaM2">Área en m²</label>
                <Input
                  id="edit-areaM2"
                  name="areaM2"
                  type="number"
                  min="1"
                  step="0.01"
                  value={fields.areaM2}
                  onChange={handleFieldChange}
                />
              </div>

              <div style={fieldStyle}>
                <label htmlFor="edit-habitaciones">Habitaciones</label>
                <Input
                  id="edit-habitaciones"
                  name="habitaciones"
                  type="number"
                  min="0"
                  value={fields.habitaciones}
                  onChange={handleFieldChange}
                />
              </div>

              <div style={fieldStyle}>
                <label htmlFor="edit-banos">Baños</label>
                <Input
                  id="edit-banos"
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
              <label htmlFor="edit-valorMensual">Valor mensual</label>
              <Input
                id="edit-valorMensual"
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
              <label htmlFor="edit-descripcion">Descripción</label>
              <Textarea
                id="edit-descripcion"
                name="descripcion"
                rows={4}
                value={fields.descripcion}
                onChange={handleFieldChange}
              />
            </div>
          </section>

          {submitError !== null && (
            <p role="alert" style={errorStyle}>
              {submitError}
            </p>
          )}

          <Button type="submit" variant="primary" disabled={!isFormReady || isSubmitting}>
            {isSubmitting ? 'Guardando...' : 'Guardar cambios'}
          </Button>
        </form>
      </div>
    </div>
  );
};

// ---------------------------------------------------------------------------
// Styles (inline — consistent with PublicarInmueblePage)
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

export default EditarInmueblePage;
