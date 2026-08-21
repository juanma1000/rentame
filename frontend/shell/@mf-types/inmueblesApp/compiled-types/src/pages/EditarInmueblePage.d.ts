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
import React from 'react';
import type { Inmueble } from '../services/inmuebles.api';
interface Props {
    inmueble: Inmueble;
    /** Called to navigate back to the list without saving. */
    onVolver?: () => void;
    /** Called immediately after a successful save. When omitted the success
     * screen is shown instead, keeping the standalone behaviour intact. */
    onActualizado?: () => void;
}
declare const EditarInmueblePage: React.FC<Props>;
export default EditarInmueblePage;
