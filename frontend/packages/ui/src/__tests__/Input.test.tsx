import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import { Input } from '../Input';
import { Select } from '../Select';
import { Textarea } from '../Textarea';

/**
 * Contract under test (fixed by this Red-phase test file, `@rentame/ui` has
 * no `Input`/`Select`/`Textarea` components yet). Decision: the 3 components
 * are covered in this single file (not 3 separate files) since their
 * contract/behavior is symmetric and this keeps the height/typography
 * consistency assertions (test 2) side by side for easier comparison.
 *
 * interface InputProps extends Omit<React.InputHTMLAttributes<HTMLInputElement>, 'className'> {
 *   error?: boolean;
 * }
 * interface SelectProps extends Omit<React.SelectHTMLAttributes<HTMLSelectElement>, 'className'> {
 *   error?: boolean;
 * }
 * interface TextareaProps extends Omit<React.TextareaHTMLAttributes<HTMLTextAreaElement>, 'className'> {
 *   error?: boolean;
 * }
 *
 * Per design.md ("Componentes con props explícitas, sin `className` libre
 * desde el caller"), `className` is omitted from the native attributes so
 * callers cannot override styling arbitrarily; native HTML attributes
 * (`id`, `name`, `value`, `onChange`, `disabled`, `required`, etc.) are kept
 * so `PublicarInmueblePage`/`EditarInmueblePage` can pass them unchanged.
 *
 * Focus verification mechanism (same criterion as `forms.css`/`FIELD_CLASS_NAME`
 * today, and as `button.css` pseudo-states in `Button.test.tsx`): jsdom does
 * not evaluate `:focus-visible` CSS rules, so the real `--color-primary`
 * focus ring is verified in E2E/visual testing. Here we only confirm the
 * rendered element carries the CSS class expected to be wired to that rule
 * (`rentame-input`), analogous to `rentame-field` in `forms.css` today.
 */

const FOCUS_CLASS = 'rentame-input';

describe('Input', () => {
  it('renders a native <input> element with the passed props', () => {
    const handleChange = jest.fn();
    render(
      <Input id="direccion" name="direccion" value="Calle 123" onChange={handleChange} />,
    );

    const input = screen.getByRole('textbox');
    expect(input.tagName).toBe('INPUT');
    expect(input).toHaveAttribute('id', 'direccion');
    expect(input).toHaveAttribute('name', 'direccion');
    expect(input).toHaveValue('Calle 123');
  });

  it('applies the focus CSS class expected to be wired to --color-primary', () => {
    render(<Input id="direccion" />);
    const input = screen.getByRole('textbox');

    expect(input.className).toContain(FOCUS_CLASS);
  });

  describe('error state', () => {
    it('applies a distinct border color when error is true, compared to no error', () => {
      const { unmount } = render(<Input id="a" />);
      const noErrorInput = screen.getByRole('textbox');
      const noErrorBorderColor = noErrorInput.style.borderColor;
      unmount();

      render(<Input id="b" error />);
      const errorInput = screen.getByRole('textbox');

      expect(errorInput.style.borderColor).toBe('var(--color-error)');
      expect(errorInput.style.borderColor).not.toBe(noErrorBorderColor);
    });
  });

  describe('disabled state', () => {
    it('renders the disabled attribute', () => {
      render(<Input id="direccion" disabled />);
      const input = screen.getByRole('textbox');

      expect(input).toBeDisabled();
    });
  });
});

describe('Select', () => {
  it('renders a native <select> element with the passed props', () => {
    const handleChange = jest.fn();
    render(
      <Select id="tipo" name="tipo" value="casa" onChange={handleChange}>
        <option value="casa">Casa</option>
        <option value="depto">Departamento</option>
      </Select>,
    );

    const select = screen.getByRole('combobox');
    expect(select.tagName).toBe('SELECT');
    expect(select).toHaveAttribute('id', 'tipo');
    expect(select).toHaveAttribute('name', 'tipo');
    expect(select).toHaveValue('casa');
  });

  it('applies the focus CSS class expected to be wired to --color-primary', () => {
    render(
      <Select id="tipo">
        <option value="casa">Casa</option>
      </Select>,
    );
    const select = screen.getByRole('combobox');

    expect(select.className).toContain(FOCUS_CLASS);
  });

  describe('error state', () => {
    it('applies a distinct border color when error is true, compared to no error', () => {
      const { unmount } = render(
        <Select id="a">
          <option value="x">X</option>
        </Select>,
      );
      const noErrorSelect = screen.getByRole('combobox');
      const noErrorBorderColor = noErrorSelect.style.borderColor;
      unmount();

      render(
        <Select id="b" error>
          <option value="x">X</option>
        </Select>,
      );
      const errorSelect = screen.getByRole('combobox');

      expect(errorSelect.style.borderColor).toBe('var(--color-error)');
      expect(errorSelect.style.borderColor).not.toBe(noErrorBorderColor);
    });
  });

  describe('disabled state', () => {
    it('renders the disabled attribute', () => {
      render(
        <Select id="tipo" disabled>
          <option value="casa">Casa</option>
        </Select>,
      );
      const select = screen.getByRole('combobox');

      expect(select).toBeDisabled();
    });
  });
});

describe('Textarea', () => {
  it('renders a native <textarea> element with the passed props', () => {
    const handleChange = jest.fn();
    render(
      <Textarea id="descripcion" name="descripcion" value="Un lindo depto" onChange={handleChange} />,
    );

    const textarea = screen.getByRole('textbox');
    expect(textarea.tagName).toBe('TEXTAREA');
    expect(textarea).toHaveAttribute('id', 'descripcion');
    expect(textarea).toHaveAttribute('name', 'descripcion');
    expect(textarea).toHaveValue('Un lindo depto');
  });

  it('applies the focus CSS class expected to be wired to --color-primary', () => {
    render(<Textarea id="descripcion" />);
    const textarea = screen.getByRole('textbox');

    expect(textarea.className).toContain(FOCUS_CLASS);
  });

  describe('error state', () => {
    it('applies a distinct border color when error is true, compared to no error', () => {
      const { unmount } = render(<Textarea id="a" />);
      const noErrorTextarea = screen.getByRole('textbox');
      const noErrorBorderColor = noErrorTextarea.style.borderColor;
      unmount();

      render(<Textarea id="b" error />);
      const errorTextarea = screen.getByRole('textbox');

      expect(errorTextarea.style.borderColor).toBe('var(--color-error)');
      expect(errorTextarea.style.borderColor).not.toBe(noErrorBorderColor);
    });
  });

  describe('disabled state', () => {
    it('renders the disabled attribute', () => {
      render(<Textarea id="descripcion" disabled />);
      const textarea = screen.getByRole('textbox');

      expect(textarea).toBeDisabled();
    });
  });
});

describe('height/typography consistency across Input, Select, and Textarea', () => {
  it('uses the same inline padding and fontSize in all 3 field components', () => {
    render(
      <>
        <Input id="input-field" />
        <Select id="select-field">
          <option value="x">X</option>
        </Select>
        <Textarea id="textarea-field" />
      </>,
    );

    const select = screen.getByRole('combobox') as HTMLSelectElement;
    // Both <input> and <textarea> resolve to role "textbox" with no accessible
    // name here; disambiguate explicitly by id instead of role.
    const textarea = document.getElementById('textarea-field') as HTMLTextAreaElement;
    const inputEl = document.getElementById('input-field') as HTMLInputElement;

    expect(inputEl.style.padding).not.toBe('');
    expect(inputEl.style.padding).toBe(select.style.padding);
    expect(inputEl.style.padding).toBe(textarea.style.padding);

    expect(inputEl.style.fontSize).not.toBe('');
    expect(inputEl.style.fontSize).toBe(select.style.fontSize);
    expect(inputEl.style.fontSize).toBe(textarea.style.fontSize);

    // Textarea is allowed to differ on `resize` (needs vertical resizing,
    // unlike a single-line Input/Select).
    expect(textarea.style.resize).toBe('vertical');
  });
});
