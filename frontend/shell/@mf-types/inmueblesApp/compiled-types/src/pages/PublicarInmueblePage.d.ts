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
import React from 'react';
interface Props {
    /** Called to navigate back to the list without publishing. */
    onVolver?: () => void;
    /** Called immediately after successful publication (e.g. to refresh the list
     * and navigate back). When omitted the success screen with "Publicar otro"
     * is shown instead, keeping the standalone behaviour intact. */
    onPublicado?: () => void;
}
declare const PublicarInmueblePage: React.FC<Props>;
export default PublicarInmueblePage;
