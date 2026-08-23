import React from 'react';
import './input.css';
import { getFieldStyle } from './fieldStyles';

export interface InputProps extends Omit<React.InputHTMLAttributes<HTMLInputElement>, 'className'> {
  error?: boolean;
}

export function Input({ error, style, ...rest }: InputProps): React.JSX.Element {
  return (
    <input
      className="rentame-input"
      style={{ ...getFieldStyle(error), ...style }}
      {...rest}
    />
  );
}
