import type React from 'react';
import { radius, typography, spacing } from '@rentame/design-tokens';

/**
 * Shared inline style for Input/Select/Textarea so height and typography
 * stay consistent across the 3 field components (per design.md).
 */
export function getFieldStyle(error?: boolean): React.CSSProperties {
  return {
    padding: `${spacing[2]} ${spacing[3]}`,
    fontSize: typography.fontSizeBody,
    fontFamily: typography.fontFamilyBase,
    borderRadius: radius.sm,
    borderWidth: '1px',
    borderStyle: 'solid',
    borderColor: error ? 'var(--color-error)' : 'var(--color-border, #d0d5dd)',
    backgroundColor: 'var(--color-surface)',
    color: 'var(--color-text, inherit)',
  };
}
