import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import { Button } from '../Button';

/**
 * Contract under test (fixed by this Red-phase test file, `@rentame/ui` has
 * no `Button` component yet):
 *
 * interface ButtonProps {
 *   variant: 'primary' | 'secondary' | 'ghost' | 'danger' | 'premium';
 *   size?: 'sm' | 'md'; // default 'md'
 *   loading?: boolean;
 *   disabled?: boolean;
 *   type?: 'button' | 'submit';
 *   onClick?: () => void;
 *   children: React.ReactNode;
 * }
 *
 * Color verification mechanism (decision taken here, per design.md decision 3
 * — "Estados vía CSS real ... para :hover/:active/:focus-visible"):
 * base/resting colors (background/text/border per variant) are expected to be
 * set as **inline styles** (`style={{ backgroundColor: 'var(--color-primary)', ... }}`),
 * so they are asserted directly via `element.style.backgroundColor` /
 * `element.style.color` / `element.style.borderColor` in jsdom — no real CSS
 * cascade/`getComputedStyle` resolution of custom properties is needed for
 * these, since jsdom does not resolve `var()`. Only the *pseudo-states*
 * (hover/active/focus-visible) are expected to live in a real `button.css`
 * file (not exercised by this jsdom test, since jsdom does not evaluate
 * pseudo-class CSS rules either — that is left to visual/E2E verification).
 *
 * Loading indicator: rendered as an element with `data-testid="button-spinner"`.
 */

describe('Button', () => {
  it('renders its children as the button label', () => {
    render(<Button variant="primary">Publicar inmueble</Button>);

    expect(screen.getByRole('button', { name: 'Publicar inmueble' })).toBeInTheDocument();
  });

  describe('variant: primary', () => {
    it('uses --color-primary as background and --color-surface as text color', () => {
      render(<Button variant="primary">Guardar</Button>);
      const button = screen.getByRole('button', { name: 'Guardar' });

      expect(button.style.backgroundColor).toBe('var(--color-primary)');
      expect(button.style.color).toBe('var(--color-surface)');
    });
  });

  describe('variant: secondary', () => {
    it('uses --color-surface as background and --color-primary as border/text color', () => {
      render(<Button variant="secondary">Cancelar</Button>);
      const button = screen.getByRole('button', { name: 'Cancelar' });

      expect(button.style.backgroundColor).toBe('var(--color-surface)');
      expect(button.style.color).toBe('var(--color-primary)');
      expect(button.style.borderColor).toBe('var(--color-primary)');
    });
  });

  describe('variant: ghost', () => {
    it('has no solid background and uses --color-primary as text color', () => {
      render(<Button variant="ghost">Ver mas</Button>);
      const button = screen.getByRole('button', { name: 'Ver mas' });

      expect(button.style.backgroundColor).toBe('transparent');
      expect(button.style.color).toBe('var(--color-primary)');
    });
  });

  describe('variant: danger', () => {
    it('reflects --color-error in either background or border/text color', () => {
      render(<Button variant="danger">Eliminar</Button>);
      const button = screen.getByRole('button', { name: 'Eliminar' });

      const usesErrorColor =
        button.style.backgroundColor === 'var(--color-error)' ||
        button.style.borderColor === 'var(--color-error)' ||
        button.style.color === 'var(--color-error)';

      expect(usesErrorColor).toBe(true);
    });
  });

  describe('variant: premium', () => {
    it('uses --color-accent without a solid fill + white-text combination', () => {
      render(<Button variant="premium">Destacar</Button>);
      const button = screen.getByRole('button', { name: 'Destacar' });

      const usesAccent =
        button.style.borderColor === 'var(--color-accent)' ||
        button.style.color === 'var(--color-accent)';
      expect(usesAccent).toBe(true);

      // Contrast rule from design-tokens README: --color-accent must never be
      // a solid fill combined with --color-surface (white) text.
      const isForbiddenSolidWhiteOnGold =
        button.style.backgroundColor === 'var(--color-accent)' &&
        button.style.color === 'var(--color-surface)';
      expect(isForbiddenSolidWhiteOnGold).toBe(false);
    });
  });

  describe('disabled state', () => {
    it('renders the disabled attribute and does not invoke onClick when clicked', () => {
      const handleClick = jest.fn();
      render(
        <Button variant="primary" disabled onClick={handleClick}>
          Enviar
        </Button>,
      );
      const button = screen.getByRole('button', { name: 'Enviar' });

      expect(button).toBeDisabled();

      fireEvent.click(button);

      expect(handleClick).not.toHaveBeenCalled();
    });
  });

  describe('loading state', () => {
    it('does not invoke onClick when clicked and shows a loading indicator', () => {
      const handleClick = jest.fn();
      render(
        <Button variant="primary" loading onClick={handleClick}>
          Guardando
        </Button>,
      );
      const button = screen.getByRole('button', { name: 'Guardando' });

      fireEvent.click(button);

      expect(handleClick).not.toHaveBeenCalled();
      expect(screen.getByTestId('button-spinner')).toBeInTheDocument();
    });
  });

  describe('size prop', () => {
    it('applies a smaller padding for size="sm" than the default size="md"', () => {
      const { unmount } = render(
        <Button variant="primary" size="sm">
          Chico
        </Button>,
      );
      const smallButton = screen.getByRole('button', { name: 'Chico' });
      const smallPadding = smallButton.style.padding;
      unmount();

      render(<Button variant="primary">Mediano</Button>);
      const defaultButton = screen.getByRole('button', { name: 'Mediano' });
      const defaultPadding = defaultButton.style.padding;

      expect(smallPadding).not.toBe('');
      expect(defaultPadding).not.toBe('');
      expect(smallPadding).not.toBe(defaultPadding);
    });
  });

  describe('type prop', () => {
    it('defaults to type="button" when not provided', () => {
      render(<Button variant="primary">Sin tipo</Button>);
      const button = screen.getByRole('button', { name: 'Sin tipo' });

      expect(button).toHaveAttribute('type', 'button');
    });

    it('reflects type="submit" on the rendered <button> element', () => {
      render(
        <Button variant="primary" type="submit">
          Enviar formulario
        </Button>,
      );
      const button = screen.getByRole('button', { name: 'Enviar formulario' });

      expect(button).toHaveAttribute('type', 'submit');
    });
  });
});
