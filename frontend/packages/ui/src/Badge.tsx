import React from 'react';
import { radius, typography, spacing } from '@rentame/design-tokens';

export type BadgeVariant = 'verified' | 'featured' | 'new' | 'available' | 'unavailable' | 'premium';

export interface BadgeProps {
  variant: BadgeVariant;
  children: React.ReactNode;
}

// Design decisions documented (design.md, decision 4 / spec Badge requirement):
// - `available`: --color-success (border/text) reflects a real "disponible" estado.
// - `unavailable`: --color-text-secondary as neutral gray (no dedicated "neutral" token exists).
// - `verified` / `featured` / `premium`: --color-accent (gold) only as border/text, NEVER as a
//   solid filled background with white text (contrast rule from design-tokens README).
// - `new`: --color-primary (Navy) as border/text, distinct from the premium/gold family.
const variantStyles: Record<BadgeVariant, React.CSSProperties> = {
  verified: {
    backgroundColor: 'transparent',
    color: 'var(--color-accent)',
    borderColor: 'var(--color-accent)',
  },
  featured: {
    backgroundColor: 'transparent',
    color: 'var(--color-accent)',
    borderColor: 'var(--color-accent)',
  },
  premium: {
    backgroundColor: 'transparent',
    color: 'var(--color-accent)',
    borderColor: 'var(--color-accent)',
  },
  new: {
    backgroundColor: 'transparent',
    color: 'var(--color-primary)',
    borderColor: 'var(--color-primary)',
  },
  available: {
    backgroundColor: 'transparent',
    color: 'var(--color-success)',
    borderColor: 'var(--color-success)',
  },
  unavailable: {
    backgroundColor: 'transparent',
    color: 'var(--color-text-secondary)',
    borderColor: 'var(--color-text-secondary)',
  },
};

export function Badge({ variant, children }: BadgeProps): React.JSX.Element {
  const style: React.CSSProperties = {
    ...variantStyles[variant],
    padding: `2px ${spacing[2]}`,
    borderRadius: radius.sm,
    borderWidth: '1px',
    borderStyle: 'solid',
    fontFamily: typography.fontFamilyBase,
    fontWeight: typography.fontWeightMedium,
    fontSize: typography.fontSizeSmall,
    display: 'inline-flex',
    alignItems: 'center',
    lineHeight: 1.2,
  };

  return (
    <span className={`rentame-badge rentame-badge--${variant}`} style={style}>
      {children}
    </span>
  );
}
