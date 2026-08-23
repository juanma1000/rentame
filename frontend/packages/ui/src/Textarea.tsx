import React from 'react';
import './input.css';
import { getFieldStyle } from './fieldStyles';

export interface TextareaProps
  extends Omit<React.TextareaHTMLAttributes<HTMLTextAreaElement>, 'className'> {
  error?: boolean;
}

export function Textarea({ error, style, ...rest }: TextareaProps): React.JSX.Element {
  return (
    <textarea
      className="rentame-input"
      style={{ ...getFieldStyle(error), resize: 'vertical', ...style }}
      {...rest}
    />
  );
}
