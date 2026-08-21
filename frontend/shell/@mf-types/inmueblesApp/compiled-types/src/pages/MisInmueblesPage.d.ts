/**
 * MisInmueblesPage — panel "Mis inmuebles" para el propietario autenticado.
 *
 * Fetches the propietario's own listings via `listarMisInmuebles(token)` on
 * mount and renders them as a list.  Each card shows a human-readable status
 * badge and, depending on the current `estado`, a "Despublicar" or
 * "Republicar" button.  Clicking a button calls `cambiarDisponibilidad` and
 * updates the card's local state from the response — no full-list refetch.
 *
 * Status badge mapping (per `EstadoInmueble` in
 * `backend/inmuebles/domain/inmueble.py`):
 *   - `"disponible"`    → "Disponible"
 *   - `"no_disponible"` → "No disponible"
 *   - `"oculto"`        → "Despublicado"
 *
 * The `"no_disponible"` state is only reachable via the future arrendamiento
 * domain — propietarios cannot trigger it manually, so no button is rendered.
 */
import React from 'react';
import type { Inmueble } from '../services/inmuebles.api';
interface Props {
    /**
     * Called when the user clicks "Publicar nuevo inmueble".
     * When omitted the button is not rendered (standalone use, or in tests).
     */
    onPublicar?: () => void;
    /**
     * Called when the user clicks "Editar" on a card, receiving the target
     * inmueble. When omitted the button is not rendered.
     */
    onEditar?: (inmueble: Inmueble) => void;
}
declare const MisInmueblesPage: React.FC<Props>;
export default MisInmueblesPage;
