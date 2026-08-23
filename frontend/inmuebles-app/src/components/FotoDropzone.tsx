import type { ChangeEvent, DragEvent } from 'react';
import { useEffect, useState } from 'react';

/**
 * Dropzone de fotos para el formulario de publicación de inmuebles
 * (`openspec/changes/ui-formulario-inmueble/design.md`, decisiones 1 y 2).
 *
 * Envuelve un `<input type="file">` real y siempre visible (nunca oculto ni
 * removido) para preservar accesibilidad y compatibilidad con los tests
 * existentes que interactúan con el input nativo.
 */

export interface FotoDropzoneProps {
  id: string;
  fotos: File[];
  maxFotos: number;
  onFilesSelected: (files: File[]) => void;
}

const dropzoneStyle = {
  border: '2px dashed var(--color-border)',
  borderRadius: 'var(--radius-card)',
  backgroundColor: 'var(--color-surface)',
  color: 'var(--color-text-secondary)',
  padding: '1.5rem',
  textAlign: 'center' as const,
  display: 'flex',
  flexDirection: 'column' as const,
  alignItems: 'center',
  gap: '0.75rem',
};

const thumbnailsStyle = {
  display: 'flex',
  flexWrap: 'wrap' as const,
  gap: '0.5rem',
  justifyContent: 'center',
};

const thumbnailStyle = {
  width: '80px',
  height: '80px',
  objectFit: 'cover' as const,
  borderRadius: 'var(--radius-card)',
  border: '1px solid var(--color-border)',
};

const counterStyle = {
  fontSize: '0.85rem',
  color: 'var(--color-text-secondary)',
};

export default function FotoDropzone({ id, fotos, maxFotos, onFilesSelected }: FotoDropzoneProps) {
  const [objectUrls, setObjectUrls] = useState<string[]>([]);

  useEffect(() => {
    const urls = fotos.map((file) => URL.createObjectURL(file));
    setObjectUrls(urls);

    return () => {
      urls.forEach((url) => URL.revokeObjectURL(url));
    };
  }, [fotos]);

  function handleDrop(e: DragEvent<HTMLDivElement>) {
    e.preventDefault();
    onFilesSelected(Array.from(e.dataTransfer.files));
  }

  function handleDragOver(e: DragEvent<HTMLDivElement>) {
    e.preventDefault();
  }

  function handleChange(e: ChangeEvent<HTMLInputElement>) {
    onFilesSelected(Array.from(e.target.files ?? []));
  }

  return (
    <div
      data-testid="foto-dropzone"
      style={dropzoneStyle}
      onDrop={handleDrop}
      onDragOver={handleDragOver}
    >
      <label htmlFor={id} style={{ cursor: 'pointer' }}>
        Arrastra tus fotos aquí o hacé clic para seleccionar
      </label>
      <input
        id={id}
        type="file"
        multiple
        accept="image/*"
        onChange={handleChange}
      />
      {fotos.length > 0 && (
        <div style={thumbnailsStyle}>
          {fotos.map((file, index) => (
            <img
              key={`${file.name}-${index}`}
              src={objectUrls[index]}
              alt={file.name}
              style={thumbnailStyle}
            />
          ))}
        </div>
      )}
      <span style={counterStyle}>
        {fotos.length}/{maxFotos} fotos
      </span>
    </div>
  );
}
