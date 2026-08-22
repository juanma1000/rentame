/**
 * Task 10.2 (Red) — contract test for `pages/EntradaPage.tsx`.
 *
 * Fixes the contract of `EntradaPage` BEFORE the implementation exists (TDD
 * Red phase, delegated to qa-expert per `openspec/config.yaml`'s `apply`
 * rule), per the "Pantalla de entrada simétrica por rol" requirement in
 * `openspec/changes/hu-008/specs/usuarios/spec.md`:
 *
 *   GIVEN a person with no active session
 *   WHEN they land on the entry screen
 *   THEN the system shows all three registration options (propietario,
 *        agente, inquilino) without visually prioritizing any of them.
 *
 * Contract assumed for this task (documented here since `design.md` leaves
 * the exact routes to implementation):
 *   - Three equally-weighted, clickable options (rendered as links or
 *     buttons with accessible roles), each navigating to its own
 *     registration route:
 *       - "Quiero publicar mi inmueble"    → /registro/propietario
 *       - "Gestiono inmuebles de otros"    → /registro/agente
 *       - "Busco dónde vivir"              → /registro/inquilino
 *   - An additional "Iniciar sesión" link/button for people who already
 *     have an account → /login
 *   - "Symmetry" is verified at the test level as: all three options are
 *     present simultaneously in the accessibility tree as clickable
 *     elements (links), with none of the three rendered with a `disabled`
 *     state or missing from the tree — visual/CSS priority (font-size,
 *     ordering, color) is a `frontend-expert` implementation concern, not
 *     something this RTL test can assert directly, but the presence check
 *     guards against a future regression where one option is accidentally
 *     hidden, commented out, or gated behind another option's flow.
 *
 * `EntradaPage` does not exist yet in `../pages/EntradaPage` — every test
 * below is expected to fail on import (`Cannot find module
 * '../pages/EntradaPage'`), the genuine Red failure for this phase. No
 * implementation is written here.
 */
import '@testing-library/jest-dom';
import { fireEvent, render, screen } from '@testing-library/react';
import React from 'react';
import { MemoryRouter, Route, Routes } from 'react-router';
import { AuthProvider } from '@rentame/auth';

import EntradaPage from '../pages/EntradaPage';

function renderEntradaPage() {
  return render(
    <AuthProvider>
      <MemoryRouter initialEntries={['/']}>
        <Routes>
          <Route path="/" element={<EntradaPage />} />
          <Route path="/registro/propietario" element={<div>Registro propietario page</div>} />
          <Route path="/registro/agente" element={<div>Registro agente page</div>} />
          <Route path="/registro/inquilino" element={<div>Registro inquilino page</div>} />
          <Route path="/login" element={<div>Login page</div>} />
        </Routes>
      </MemoryRouter>
    </AuthProvider>,
  );
}

describe('EntradaPage (contract, Red)', () => {
  it('renders all three registration options simultaneously, as accessible links', () => {
    renderEntradaPage();

    const propietarioLink = screen.getByRole('link', {
      name: /quiero publicar mi inmueble/i,
    });
    const agenteLink = screen.getByRole('link', { name: /gestiono inmuebles de otros/i });
    const inquilinoLink = screen.getByRole('link', { name: /busco dónde vivir/i });

    expect(propietarioLink).toBeInTheDocument();
    expect(agenteLink).toBeInTheDocument();
    expect(inquilinoLink).toBeInTheDocument();

    // None of the three options is disabled — all equally actionable.
    expect(propietarioLink).not.toHaveAttribute('aria-disabled', 'true');
    expect(agenteLink).not.toHaveAttribute('aria-disabled', 'true');
    expect(inquilinoLink).not.toHaveAttribute('aria-disabled', 'true');
  });

  it('also renders an "Iniciar sesión" link for people who already have an account', () => {
    renderEntradaPage();

    expect(screen.getByRole('link', { name: /iniciar sesión/i })).toBeInTheDocument();
  });

  it('navigates to /registro/propietario when "Quiero publicar mi inmueble" is clicked', () => {
    renderEntradaPage();

    fireEvent.click(screen.getByRole('link', { name: /quiero publicar mi inmueble/i }));

    expect(screen.getByText(/registro propietario page/i)).toBeInTheDocument();
  });

  it('navigates to /registro/agente when "Gestiono inmuebles de otros" is clicked', () => {
    renderEntradaPage();

    fireEvent.click(screen.getByRole('link', { name: /gestiono inmuebles de otros/i }));

    expect(screen.getByText(/registro agente page/i)).toBeInTheDocument();
  });

  it('navigates to /registro/inquilino when "Busco dónde vivir" is clicked', () => {
    renderEntradaPage();

    fireEvent.click(screen.getByRole('link', { name: /busco dónde vivir/i }));

    expect(screen.getByText(/registro inquilino page/i)).toBeInTheDocument();
  });

  it('navigates to /login when "Iniciar sesión" is clicked', () => {
    renderEntradaPage();

    fireEvent.click(screen.getByRole('link', { name: /iniciar sesión/i }));

    expect(screen.getByText(/login page/i)).toBeInTheDocument();
  });
});
