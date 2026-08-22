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
 */
import React, { ChangeEvent, FormEvent, useState } from 'react';
import { useAuth } from '@rentame/auth';
import { editarInmueble, InmueblesApiError } from '../services/inmuebles.api';
import type { EditarInmuebleInput, Inmueble } from '../services/inmuebles.api';

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
        <p>El inmueble fue actualizado exitosamente.</p>
      </div>
    );
  }

  // -------------------------------------------------------------------------
  // Form
  // -------------------------------------------------------------------------

  return (
    <div style={containerStyle}>
      {onVolver && (
        <button type="button" style={backButtonStyle} onClick={onVolver}>
          Volver a mis inmuebles
        </button>
      )}
      <h1>Editar inmueble</h1>
      <form onSubmit={handleSubmit} noValidate>
        <div style={fieldStyle}>
          <label htmlFor="edit-direccion">Dirección</label>
          <input
            id="edit-direccion"
            name="direccion"
            type="text"
            value={fields.direccion}
            onChange={handleFieldChange}
          />
        </div>

        <div style={fieldStyle}>
          <label htmlFor="edit-barrio">Barrio</label>
          <input
            id="edit-barrio"
            name="barrio"
            type="text"
            value={fields.barrio}
            onChange={handleFieldChange}
          />
        </div>

        <div style={fieldStyle}>
          <label htmlFor="edit-ciudad">Ciudad</label>
          <input
            id="edit-ciudad"
            name="ciudad"
            type="text"
            value={fields.ciudad}
            onChange={handleFieldChange}
          />
        </div>

        <div style={fieldStyle}>
          <label htmlFor="edit-tipo">Tipo de inmueble</label>
          <select
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
          </select>
        </div>

        <div style={fieldStyle}>
          <label htmlFor="edit-areaM2">Área en m²</label>
          <input
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
          <input
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
          <input
            id="edit-banos"
            name="banos"
            type="number"
            min="0"
            value={fields.banos}
            onChange={handleFieldChange}
          />
        </div>

        <div style={fieldStyle}>
          <label htmlFor="edit-valorMensual">Valor mensual</label>
          <input
            id="edit-valorMensual"
            name="valorMensual"
            type="number"
            min="1"
            value={fields.valorMensual}
            onChange={handleFieldChange}
          />
        </div>

        <div style={fieldStyle}>
          <label htmlFor="edit-descripcion">Descripción</label>
          <textarea
            id="edit-descripcion"
            name="descripcion"
            rows={4}
            value={fields.descripcion}
            onChange={handleFieldChange}
          />
        </div>

        {submitError !== null && (
          <p role="alert" style={errorStyle}>
            {submitError}
          </p>
        )}

        <button
          type="submit"
          disabled={!isFormReady || isSubmitting}
          style={buttonStyle}
        >
          {isSubmitting ? 'Guardando...' : 'Guardar cambios'}
        </button>
      </form>
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

const buttonStyle: React.CSSProperties = {
  padding: '0.5rem 1.25rem',
  cursor: 'pointer',
};

const errorStyle: React.CSSProperties = {
  color: 'var(--color-error)',
  marginBottom: '0.75rem',
};

const backButtonStyle: React.CSSProperties = {
  padding: '0.35rem 0.85rem',
  cursor: 'pointer',
  borderRadius: '4px',
  border: '1px solid var(--color-border)',
  marginBottom: '1rem',
  background: 'none',
};

export default EditarInmueblePage;
