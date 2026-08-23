import React from 'react';
import { radius, typography, spacing, transitions } from '@rentame/design-tokens';
import './button.css';

export type ButtonVariant = 'primary' | 'secondary' | 'ghost' | 'danger' | 'premium';
export type ButtonSize = 'sm' | 'md';

export interface ButtonProps {
  variant: ButtonVariant;
  size?: ButtonSize;
  loading?: boolean;
  disabled?: boolean;
  type?: 'button' | 'submit';
  onClick?: () => void;
  children: React.ReactNode;
}

const variantStyles: Record<ButtonVariant, React.CSSProperties> = {
  primary: {
    backgroundColor: 'var(--color-primary)',
    color: 'var(--color-surface)',
    borderColor: 'var(--color-primary)',
  },
  secondary: {
    backgroundColor: 'var(--color-surface)',
    color: 'var(--color-primary)',
    borderColor: 'var(--color-primary)',
  },
  ghost: {
    backgroundColor: 'transparent',
    color: 'var(--color-primary)',
    borderColor: 'transparent',
  },
  danger: {
    backgroundColor: 'var(--color-surface)',
    color: 'var(--color-error)',
    borderColor: 'var(--color-error)',
  },
  premium: {
    backgroundColor: 'transparent',
    color: 'var(--color-primary)',
    borderColor: 'var(--color-accent)',
  },
};

const sizePadding: Record<ButtonSize, string> = {
  sm: `${spacing[1]} ${spacing[3]}`,
  md: `${spacing[2]} ${spacing[4]}`,
};

export function Button({
  variant,
  size = 'md',
  loading = false,
  disabled = false,
  type = 'button',
  onClick,
  children,
}: ButtonProps): React.JSX.Element {
  const isDisabled = disabled || loading;

  const handleClick = (): void => {
    if (isDisabled) {
      return;
    }
    onClick?.();
  };

  const style: React.CSSProperties = {
    ...variantStyles[variant],
    padding: sizePadding[size],
    borderRadius: radius.sm,
    borderWidth: '1px',
    borderStyle: 'solid',
    fontFamily: typography.fontFamilyBase,
    fontWeight: typography.fontWeightMedium,
    fontSize: typography.fontSizeBody,
    transition: transitions.base,
    cursor: isDisabled ? 'not-allowed' : 'pointer',
    opacity: isDisabled ? 0.6 : 1,
    display: 'inline-flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: spacing[2],
  };

  return (
    <button
      type={type}
      className={`rentame-button rentame-button--${variant}`}
      style={style}
      disabled={isDisabled}
      onClick={handleClick}
    >
      {loading ? <span data-testid="button-spinner" className="rentame-button__spinner" /> : null}
      {children}
    </button>
  );
}
