'use strict';
/**
 * Stub `URL.createObjectURL`/`URL.revokeObjectURL` for the jsdom test
 * environment.
 *
 * jsdom does not implement the Blob URL registry, but `FotoDropzone`
 * (`src/components/FotoDropzone.tsx`) calls `URL.createObjectURL(file)` to
 * build thumbnail previews for every attached foto. Without this stub any
 * test that selects fotos crashes with `URL.createObjectURL is not a
 * function`. The stub returns a fake, unique URL per call — good enough for
 * an `<img src>` in jsdom, which never actually loads images.
 */
if (typeof globalThis.URL.createObjectURL !== 'function') {
  let counter = 0;
  globalThis.URL.createObjectURL = function createObjectURL() {
    counter += 1;
    return `blob:mock-url-${counter}`;
  };
}

if (typeof globalThis.URL.revokeObjectURL !== 'function') {
  globalThis.URL.revokeObjectURL = function revokeObjectURL() {};
}
