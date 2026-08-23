import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { PropertyCard } from '../PropertyCard';

// Design decisions (design.md, decision 5 / specs/design-system/spec.md — Requirement "PropertyCard reutilizable"):
// - Currency format: `.toLocaleString('es-CO')` prefixed with "$", same criterion already used in
//   `BusquedaPublicaPage.formatValor` / `PublicarInmueblePage` — e.g. 1200000 -> "$1.200.000".
// - When `fotoUrl` is `null`, no `<img>` is rendered; instead a placeholder element
//   (`data-testid="property-card-photo-placeholder"`) takes its place, so the card layout never collapses.
// - Favorito slot: rendered only when `showFavorito` is `true` (default `false`), exposed as a
//   `button` with `aria-label="Marcar como favorito"` — queried here via `queryByRole('button', { name: /favorito/i })`.

const baseProps = {
  direccion: 'Calle 10 # 20-30',
  barrio: 'El Poblado',
  ciudad: 'Medellín',
  habitaciones: 3,
  banos: 2,
  valorMensual: 1200000,
  fotoUrl: 'https://example.com/foto.jpg',
  estado: 'disponible' as const,
};

describe('PropertyCard', () => {
  it('renders direccion, ubicacion, habitaciones, banos and formatted valorMensual', () => {
    render(<PropertyCard {...baseProps} />);

    expect(screen.getByText('Calle 10 # 20-30')).toBeInTheDocument();
    expect(screen.getByText('El Poblado, Medellín')).toBeInTheDocument();
    // Scoped exact matches — a loose /3/ or /2/ regex also matches digits
    // inside the address itself ("20-30"), producing a false ambiguous match.
    expect(screen.getByText('3 hab.')).toBeInTheDocument();
    expect(screen.getByText('2 baños')).toBeInTheDocument();
    expect(screen.getByText(/\$1\.200\.000/)).toBeInTheDocument();
  });

  it('renders an <img> with the given fotoUrl when it is not null', () => {
    render(<PropertyCard {...baseProps} />);

    const img = screen.getByRole('img');
    expect(img).toHaveAttribute('src', 'https://example.com/foto.jpg');
  });

  it('renders a placeholder instead of an <img> when fotoUrl is null', () => {
    render(<PropertyCard {...baseProps} fotoUrl={null} />);

    expect(screen.queryByRole('img')).not.toBeInTheDocument();
    expect(screen.getByTestId('property-card-photo-placeholder')).toBeInTheDocument();
  });

  it('renders the "available" Badge when estado is "disponible"', () => {
    render(<PropertyCard {...baseProps} estado="disponible" />);

    expect(screen.getByText(/disponible/i).closest('.rentame-badge--available')).not.toBeNull();
  });

  it.each(['oculto', 'no_disponible'] as const)(
    'renders the "unavailable" Badge when estado is "%s"',
    (estado) => {
      render(<PropertyCard {...baseProps} estado={estado} />);

      const badge = document.querySelector('.rentame-badge--unavailable');
      expect(badge).not.toBeNull();
    },
  );

  it('invokes onClick when the card is clicked', () => {
    const onClick = jest.fn();
    render(<PropertyCard {...baseProps} onClick={onClick} />);

    fireEvent.click(screen.getByText('Calle 10 # 20-30'));

    expect(onClick).toHaveBeenCalledTimes(1);
  });

  it('does not render any favorito icon/button by default', () => {
    render(<PropertyCard {...baseProps} />);

    expect(screen.queryByRole('button', { name: /favorito/i })).not.toBeInTheDocument();
    expect(screen.queryByTestId('property-card-favorito')).not.toBeInTheDocument();
  });

  it('does not render the favorito control when showFavorito is explicitly false', () => {
    render(<PropertyCard {...baseProps} showFavorito={false} />);

    expect(screen.queryByRole('button', { name: /favorito/i })).not.toBeInTheDocument();
  });

  it('renders acciones content inside the card when provided', () => {
    render(
      <PropertyCard {...baseProps} acciones={<button>Editar</button>} />,
    );

    const editarButton = screen.getByRole('button', { name: 'Editar' });
    expect(editarButton).toBeInTheDocument();
  });
});
