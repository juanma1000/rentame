import React from 'react';
import { render, screen } from '@testing-library/react';
import { Badge } from '../Badge';
import { Button } from '../Button';

// Design decisions documented (design.md, decision 4 / spec Badge requirement):
// - `available`: uses --color-success (border/text) to reflect a real "disponible" estado.
// - `unavailable`: uses --color-text-secondary as a neutral gray (no dedicated "neutral" token exists).
// - `verified` / `featured` / `premium`: use --color-accent (gold) only as border/text, NEVER as a solid
//   filled background with white text (contrast rule from design-tokens README forbids gold fill + white text).
// - `new`: uses --color-primary (Navy) as border/text, to distinguish it from the premium/gold family.
// Badges must be small and discreet: smaller fontSize/padding than a Button (size md).

describe('Badge', () => {
  const variants = ['verified', 'featured', 'new', 'available', 'unavailable', 'premium'] as const;

  it.each(variants)('renders its children text for variant "%s"', (variant) => {
    render(<Badge variant={variant}>Etiqueta {variant}</Badge>);

    expect(screen.getByText(`Etiqueta ${variant}`)).toBeInTheDocument();
  });

  it('uses --color-success for the "available" variant', () => {
    render(<Badge variant="available">Disponible</Badge>);

    const badge = screen.getByText('Disponible');
    const usesSuccessColor =
      badge.style.color === 'var(--color-success)' ||
      badge.style.borderColor === 'var(--color-success)' ||
      badge.style.backgroundColor === 'var(--color-success)';

    expect(usesSuccessColor).toBe(true);
  });

  it('uses a neutral gray (--color-text-secondary) for the "unavailable" variant', () => {
    render(<Badge variant="unavailable">No disponible</Badge>);

    const badge = screen.getByText('No disponible');
    const usesNeutralColor =
      badge.style.color === 'var(--color-text-secondary)' ||
      badge.style.borderColor === 'var(--color-text-secondary)' ||
      badge.style.backgroundColor === 'var(--color-text-secondary)';

    expect(usesNeutralColor).toBe(true);
  });

  it.each(['verified', 'featured', 'premium'] as const)(
    'uses --color-accent for the "%s" variant, never as a solid background',
    (variant) => {
      render(<Badge variant={variant}>Etiqueta</Badge>);

      const badge = screen.getByText('Etiqueta');
      const usesAccentColor =
        badge.style.color === 'var(--color-accent)' || badge.style.borderColor === 'var(--color-accent)';

      expect(usesAccentColor).toBe(true);
      expect(badge.style.backgroundColor).not.toBe('var(--color-accent)');
    },
  );

  it('uses --color-primary or --color-accent for the "new" variant', () => {
    render(<Badge variant="new">Nuevo</Badge>);

    const badge = screen.getByText('Nuevo');
    const usesExpectedColor =
      badge.style.color === 'var(--color-primary)' ||
      badge.style.borderColor === 'var(--color-primary)' ||
      badge.style.color === 'var(--color-accent)' ||
      badge.style.borderColor === 'var(--color-accent)';

    expect(usesExpectedColor).toBe(true);
  });

  it('is visibly smaller and more discreet than a Button (size md)', () => {
    render(
      <div>
        <Badge variant="available">Disponible</Badge>
        <Button variant="primary" size="md">
          Confirmar
        </Button>
      </div>,
    );

    const badge = screen.getByText('Disponible');
    const button = screen.getByText('Confirmar');

    const badgeFontSize = parseFloat(badge.style.fontSize);
    const buttonFontSize = parseFloat(button.style.fontSize);
    expect(badgeFontSize).toBeLessThan(buttonFontSize);

    const badgePaddingSum = badge.style.padding
      .split(' ')
      .reduce((sum, value) => sum + parseFloat(value), 0);
    const buttonPaddingSum = button.style.padding
      .split(' ')
      .reduce((sum, value) => sum + parseFloat(value), 0);
    expect(badgePaddingSum).toBeLessThan(buttonPaddingSum);
  });
});
