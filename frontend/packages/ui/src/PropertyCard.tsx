import React from 'react';
import { colors, radius, shadows, spacing, typography } from '@rentame/design-tokens';
import { Badge } from './Badge';

export type PropertyCardEstado = 'disponible' | 'no_disponible' | 'oculto';

export interface PropertyCardProps {
  direccion: string;
  barrio: string;
  ciudad: string;
  habitaciones: number;
  banos: number;
  valorMensual: number;
  fotoUrl: string | null;
  estado: PropertyCardEstado;
  onClick?: () => void;
  showFavorito?: boolean;
  acciones?: React.ReactNode;
  /**
   * Overrides the badge's visible text without changing the color mapping
   * (still derived from `estado`). Callers with more than two real domain
   * states — e.g. `MisInmueblesPage`/`InmueblesGestionadosPage`, which
   * distinguish "oculto" ("Despublicado") from "no_disponible" ("No
   * disponible") for their existing test contract — pass their own label
   * here; defaults to "Disponible" / the raw `estado` string otherwise.
   */
  estadoLabel?: string;
}

// Design decisions (design.md decision 5 / specs/design-system/spec.md — "PropertyCard reutilizable"):
// - Currency format: "$" + toLocaleString('es-CO'), matching BusquedaPublicaPage.formatValor.
// - Photo is the protagonist: generous height (240px) vs. the previous 160px in BusquedaPublicaPage,
//   with object-fit: cover so varied aspect ratios don't distort.
// - When fotoUrl is null, a placeholder keeps the layout from collapsing.
// - Favorito control only renders when showFavorito is true (default false).
// - `estado === 'disponible'` maps to Badge variant "available"; any other estado maps to "unavailable".

function formatValor(valor: number): string {
  return `$${valor.toLocaleString('es-CO')}`;
}

export function PropertyCard({
  direccion,
  barrio,
  ciudad,
  habitaciones,
  banos,
  valorMensual,
  fotoUrl,
  estado,
  onClick,
  showFavorito = false,
  acciones,
  estadoLabel,
}: PropertyCardProps): React.JSX.Element {
  const badgeVariant = estado === 'disponible' ? 'available' : 'unavailable';

  const cardStyle: React.CSSProperties = {
    backgroundColor: colors.surface,
    border: `1px solid ${colors.border}`,
    borderRadius: radius.card,
    boxShadow: shadows.sm,
    overflow: 'hidden',
    fontFamily: typography.fontFamilyBase,
    position: 'relative',
    cursor: onClick ? 'pointer' : undefined,
  };

  const mediaWrapperStyle: React.CSSProperties = {
    position: 'relative',
    width: '100%',
    height: '240px',
    backgroundColor: colors.background,
  };

  const imgStyle: React.CSSProperties = {
    width: '100%',
    height: '100%',
    objectFit: 'cover',
    display: 'block',
  };

  const placeholderStyle: React.CSSProperties = {
    width: '100%',
    height: '100%',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    color: colors.textSecondary,
    fontSize: typography.fontSizeSmall,
  };

  const badgeWrapperStyle: React.CSSProperties = {
    position: 'absolute',
    top: spacing[3],
    left: spacing[3],
  };

  const favoritoStyle: React.CSSProperties = {
    position: 'absolute',
    top: spacing[3],
    right: spacing[3],
    border: 'none',
    backgroundColor: colors.surface,
    borderRadius: radius.sm,
    width: '32px',
    height: '32px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    cursor: 'pointer',
    boxShadow: shadows.sm,
  };

  const bodyStyle: React.CSSProperties = {
    padding: spacing[4],
  };

  const direccionStyle: React.CSSProperties = {
    margin: 0,
    fontSize: typography.fontSizeBody,
    fontWeight: typography.fontWeightSemibold,
    color: colors.text,
  };

  const ubicacionStyle: React.CSSProperties = {
    margin: `${spacing[1]} 0 ${spacing[3]}`,
    fontSize: typography.fontSizeSmall,
    color: colors.textSecondary,
  };

  const detallesStyle: React.CSSProperties = {
    display: 'flex',
    gap: spacing[4],
    fontSize: typography.fontSizeSmall,
    color: colors.textSecondary,
    marginBottom: spacing[3],
  };

  const valorStyle: React.CSSProperties = {
    margin: 0,
    fontSize: typography.fontSizeH3,
    fontWeight: typography.fontWeightBold,
    color: colors.primary,
  };

  const accionesStyle: React.CSSProperties = {
    marginTop: spacing[3],
  };

  return (
    <div className="rentame-property-card" style={cardStyle} onClick={onClick}>
      <div style={mediaWrapperStyle}>
        {fotoUrl ? (
          <img src={fotoUrl} alt={direccion} style={imgStyle} />
        ) : (
          <div data-testid="property-card-photo-placeholder" style={placeholderStyle}>
            Sin foto
          </div>
        )}

        <div style={badgeWrapperStyle}>
          <Badge variant={badgeVariant}>
            {estadoLabel ?? (estado === 'disponible' ? 'Disponible' : estado)}
          </Badge>
        </div>

        {showFavorito && (
          <button
            type="button"
            aria-label="Marcar como favorito"
            data-testid="property-card-favorito"
            style={favoritoStyle}
            onClick={(event) => {
              event.stopPropagation();
            }}
          >
            ♥
          </button>
        )}
      </div>

      <div style={bodyStyle}>
        <p style={direccionStyle}>{direccion}</p>
        <p style={ubicacionStyle}>
          {barrio}, {ciudad}
        </p>

        <div style={detallesStyle}>
          <span>{habitaciones} hab.</span>
          <span>{banos} baños</span>
        </div>

        <p style={valorStyle}>{formatValor(valorMensual)}</p>

        {acciones && <div style={accionesStyle}>{acciones}</div>}
      </div>
    </div>
  );
}
