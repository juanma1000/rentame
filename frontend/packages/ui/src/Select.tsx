import React from 'react';
import './input.css';
import { getFieldStyle } from './fieldStyles';

export interface SelectProps extends Omit<React.SelectHTMLAttributes<HTMLSelectElement>, 'className'> {
  error?: boolean;
}

export function Select({ error, style, children, ...rest }: SelectProps): React.JSX.Element {
  return (
    <select
      className="rentame-input"
      style={{ ...getFieldStyle(error), ...style }}
      {...rest}
    >
      {children}
    </select>
  );
}
