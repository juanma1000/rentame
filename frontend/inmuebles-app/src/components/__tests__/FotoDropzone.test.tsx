/**
 * Red phase — `FotoDropzone` (component not implemented yet, see
 * `openspec/changes/ui-formulario-inmueble/design.md`, decisions 1 and 2).
 *
 * `FotoDropzone` does not exist yet — every test below is expected to fail
 * on import (`Cannot find module '../FotoDropzone'`), the genuine Red
 * failure for this phase. No implementation is written here.
 *
 * Contract fixed by this Red phase, for `frontend-expert` to implement:
 *
 * ```ts
 * interface FotoDropzoneProps {
 *   id: string;               // for the <label htmlFor>
 *   fotos: File[];            // controlled from the parent
 *   maxFotos: number;
 *   onFilesSelected: (files: File[]) => void;
 * }
 * ```
 *
 * - Renders a real `<input type="file" multiple accept="image/*">` in the
 *   DOM, associated to `id`, never hidden with `display:none` nor removed
 *   (design.md decision 1 — the dropzone wraps the real input, it never
 *   replaces it).
 * - `fireEvent.change` on that input with `target: { files }` calls
 *   `onFilesSelected` with the selected files, mirroring the same pattern
 *   `PublicarInmueblePage.test.tsx`'s `attachFotos` helper uses today.
 * - `fireEvent.drop` on the dropzone container calls `onFilesSelected` with
 *   the files carried by the drop event's `dataTransfer.files`.
 * - Renders one `<img>` thumbnail per `File` in the `fotos` prop, generated
 *   via `URL.createObjectURL` (mocked here, since jsdom doesn't implement
 *   it) and revoked via `URL.revokeObjectURL` in the `useEffect` cleanup
 *   (design.md decision 2) — both on unmount and when `fotos` changes.
 * - Shows a "N/10 fotos" counter reflecting `fotos.length`/`maxFotos`.
 * - The input keeps the `multiple` attribute in every state.
 */
import '@testing-library/jest-dom';
import { fireEvent, render, screen } from '@testing-library/react';
import React from 'react';
import FotoDropzone from '../FotoDropzone';

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function makeFile(name: string): File {
  return new File(['fake-image-bytes'], name, { type: 'image/jpeg' });
}

function makeFiles(count: number): File[] {
  return Array.from({ length: count }, (_, i) => makeFile(`foto-${i + 1}.jpg`));
}

/**
 * jsdom does not implement `DataTransfer`, so a drop event's
 * `dataTransfer.files` cannot be assigned directly. `Object.defineProperty`
 * on the fired event lets us stub just the property the component reads,
 * without needing a full `DataTransfer` polyfill.
 */
function fireDropWithFiles(element: Element, files: File[]): void {
  const dropEvent = new Event('drop', { bubbles: true, cancelable: true });
  Object.defineProperty(dropEvent, 'dataTransfer', {
    value: { files },
  });
  fireEvent(element, dropEvent);
}

function getFileInput(container: HTMLElement, id: string): HTMLInputElement {
  const input = container.querySelector(`input#${id}`);
  expect(input).not.toBeNull();
  return input as HTMLInputElement;
}

// ---------------------------------------------------------------------------

describe('FotoDropzone (Red)', () => {
  let createObjectURLMock: jest.Mock;
  let revokeObjectURLMock: jest.Mock;

  beforeEach(() => {
    createObjectURLMock = jest.fn((file: File) => `blob:fake-url/${file.name}`);
    revokeObjectURLMock = jest.fn();

    // jsdom doesn't implement URL.createObjectURL/revokeObjectURL.
    (URL as unknown as { createObjectURL: jest.Mock }).createObjectURL = createObjectURLMock;
    (URL as unknown as { revokeObjectURL: jest.Mock }).revokeObjectURL = revokeObjectURLMock;
  });

  it('renders a real, visible file input associated to the given id', () => {
    const { container } = render(
      <FotoDropzone id="pub-fotos" fotos={[]} maxFotos={10} onFilesSelected={jest.fn()} />,
    );

    const input = getFileInput(container, 'pub-fotos');
    expect(input).toHaveAttribute('type', 'file');
    expect(input).toHaveAttribute('accept', 'image/*');
    expect(input).toHaveAttribute('multiple');
    expect(input).not.toHaveStyle({ display: 'none' });
    expect(input).toBeVisible();
  });

  it('calls onFilesSelected with the files chosen via the native input change event', () => {
    const onFilesSelected = jest.fn();
    const files = makeFiles(2);
    const { container } = render(
      <FotoDropzone id="pub-fotos" fotos={[]} maxFotos={10} onFilesSelected={onFilesSelected} />,
    );

    const input = getFileInput(container, 'pub-fotos');
    fireEvent.change(input, { target: { files } });

    expect(onFilesSelected).toHaveBeenCalledTimes(1);
    expect(onFilesSelected).toHaveBeenCalledWith(files);
  });

  it('calls onFilesSelected with the files carried by a drop event on the dropzone container', () => {
    const onFilesSelected = jest.fn();
    const files = makeFiles(2);
    const { container } = render(
      <FotoDropzone id="pub-fotos" fotos={[]} maxFotos={10} onFilesSelected={onFilesSelected} />,
    );

    const dropzone = container.querySelector('[data-testid="foto-dropzone"]');
    expect(dropzone).not.toBeNull();
    fireDropWithFiles(dropzone as Element, files);

    expect(onFilesSelected).toHaveBeenCalledTimes(1);
    expect(onFilesSelected).toHaveBeenCalledWith(files);
  });

  it('renders one thumbnail per file in the fotos prop', () => {
    const fotos = makeFiles(3);
    render(<FotoDropzone id="pub-fotos" fotos={fotos} maxFotos={10} onFilesSelected={jest.fn()} />);

    const thumbnails = screen.getAllByRole('img');
    expect(thumbnails).toHaveLength(3);
    expect(createObjectURLMock).toHaveBeenCalledTimes(3);
  });

  it('revokes previously created object URLs when the fotos prop changes', () => {
    const initialFotos = makeFiles(2);
    const { rerender } = render(
      <FotoDropzone id="pub-fotos" fotos={initialFotos} maxFotos={10} onFilesSelected={jest.fn()} />,
    );

    expect(revokeObjectURLMock).not.toHaveBeenCalled();

    const nextFotos = makeFiles(1);
    rerender(
      <FotoDropzone id="pub-fotos" fotos={nextFotos} maxFotos={10} onFilesSelected={jest.fn()} />,
    );

    expect(revokeObjectURLMock).toHaveBeenCalled();
  });

  it('revokes object URLs on unmount', () => {
    const fotos = makeFiles(2);
    const { unmount } = render(
      <FotoDropzone id="pub-fotos" fotos={fotos} maxFotos={10} onFilesSelected={jest.fn()} />,
    );

    unmount();

    expect(revokeObjectURLMock).toHaveBeenCalled();
  });

  it('shows a "0/10 fotos" counter when no photo has been selected', () => {
    render(<FotoDropzone id="pub-fotos" fotos={[]} maxFotos={10} onFilesSelected={jest.fn()} />);

    expect(screen.getByText('0/10 fotos')).toBeInTheDocument();
  });

  it('shows a "3/10 fotos" counter reflecting the current fotos length and maxFotos', () => {
    render(
      <FotoDropzone
        id="pub-fotos"
        fotos={makeFiles(3)}
        maxFotos={10}
        onFilesSelected={jest.fn()}
      />,
    );

    expect(screen.getByText('3/10 fotos')).toBeInTheDocument();
  });

  it('keeps the input as multiple regardless of how many fotos are already selected', () => {
    const { container } = render(
      <FotoDropzone id="pub-fotos" fotos={makeFiles(5)} maxFotos={10} onFilesSelected={jest.fn()} />,
    );

    const input = getFileInput(container, 'pub-fotos');
    expect(input).toHaveAttribute('multiple');
  });
});
