import fs from 'fs';
import path from 'path';
import { colors } from '../tokens';
import { contrastRatio } from '../contrast';

const AA_LARGE_TEXT_OR_GRAPHIC = 3;

const cssPath = path.resolve(__dirname, '../tokens.css');
const css = fs.readFileSync(cssPath, 'utf-8');

function expectVar(name: string, expectedValue: string) {
  const regex = new RegExp(`${name}\\s*:\\s*${expectedValue.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}\\s*;`);
  expect(css).toMatch(regex);
}

describe('typography tokens', () => {
  it('defines --font-family-base with Inter and sans-serif fallback', () => {
    expect(css).toMatch(/--font-family-base\s*:\s*['"]?Inter['"]?[^;]*sans-serif\s*;/);
  });

  it('defines --font-family-display with DM Serif Display and serif fallback', () => {
    expect(css).toMatch(/--font-family-display\s*:\s*['"]?DM Serif Display['"]?[^;]*serif\s*;/);
  });

  it.each([
    ['--font-size-display', ['40px', '48px']],
    ['--font-size-h1', ['32px']],
    ['--font-size-h2', ['24px']],
    ['--font-size-h3', ['18px', '20px']],
    ['--font-size-body', ['14px', '16px']],
    ['--font-size-small', ['12px', '13px']],
  ])('defines %s with an accepted value', (varName, acceptedValues) => {
    const match = css.match(new RegExp(`${varName}\\s*:\\s*([^;]+);`));
    expect(match).not.toBeNull();
    const value = match ? match[1].trim() : '';
    expect(acceptedValues).toContain(value);
  });

  it.each([
    ['--font-weight-regular', '400'],
    ['--font-weight-medium', '500'],
    ['--font-weight-semibold', '600'],
    ['--font-weight-bold', '700'],
  ])('defines %s as %s', (varName, expectedValue) => {
    expectVar(varName, expectedValue);
  });
});

describe('spacing tokens follow the 4px scale', () => {
  it.each([
    ['--space-1', '4px'],
    ['--space-2', '8px'],
    ['--space-3', '12px'],
    ['--space-4', '16px'],
    ['--space-5', '20px'],
    ['--space-6', '24px'],
    ['--space-8', '32px'],
    ['--space-10', '40px'],
    ['--space-12', '48px'],
    ['--space-16', '64px'],
  ])('defines %s as %s', (varName, expectedValue) => {
    expectVar(varName, expectedValue);
  });
});

describe('radius tokens', () => {
  it('defines --radius-sm as 6px', () => {
    expectVar('--radius-sm', '6px');
  });

  it('defines --radius-lg as 12px', () => {
    expectVar('--radius-lg', '12px');
  });

  it('keeps --radius-card untouched at 10px', () => {
    expectVar('--radius-card', '10px');
  });
});

describe('shadow tokens', () => {
  it('defines --shadow-sm as a soft shadow', () => {
    // expectVar() already escapes its expectedValue for regex use — pass
    // the plain literal CSS value here, not a pre-escaped regex fragment
    // (a prior version double-escaped this, forcing invalid literal
    // backslashes into tokens.css just to satisfy the test).
    expectVar('--shadow-sm', '0 1px 2px rgba(0, 0, 0, 0.05)');
  });

  it('defines --shadow-md matching the value already used in inmuebles-app/src/styles/forms.ts', () => {
    expectVar('--shadow-md', '0 1px 3px rgba(0, 0, 0, 0.08)');
  });
});

describe('transition tokens', () => {
  it('defines --transition-base', () => {
    expectVar('--transition-base', '150ms ease');
  });
});

describe('z-index tokens', () => {
  it('defines --z-header', () => {
    const match = css.match(/--z-header\s*:\s*([^;]+);/);
    expect(match).not.toBeNull();
    expect(Number(match ? match[1].trim() : NaN)).toBe(100);
  });

  it('defines --z-modal', () => {
    const match = css.match(/--z-modal\s*:\s*([^;]+);/);
    expect(match).not.toBeNull();
    expect(Number(match ? match[1].trim() : NaN)).toBe(1000);
  });

  it('--z-modal is greater than --z-header', () => {
    const header = Number((css.match(/--z-header\s*:\s*([^;]+);/) || [])[1]);
    const modal = Number((css.match(/--z-modal\s*:\s*([^;]+);/) || [])[1]);
    expect(modal).toBeGreaterThan(header);
  });
});

describe('breakpoint tokens', () => {
  it.each([
    ['--breakpoint-sm', '640px'],
    ['--breakpoint-md', '768px'],
    ['--breakpoint-lg', '1024px'],
  ])('defines %s as %s as a CSS custom property (documented limitation: not usable inside @media)', (varName, expectedValue) => {
    expectVar(varName, expectedValue);
  });
});

describe('breakpoints exported as TS values for JS-driven media queries', () => {
  it('exposes breakpoints.sm/md/lg in px, matching the CSS custom properties', async () => {
    const { breakpoints } = await import('../tokens');
    expect(breakpoints).toEqual({ sm: 640, md: 768, lg: 1024 });
  });
});

describe('--color-warning', () => {
  it('is defined in tokens.css as #B7791F', () => {
    expectVar('--color-warning', '#B7791F');
  });

  it('is exported from tokens.ts as colors.warning', () => {
    expect(colors.warning).toBe('#B7791F');
  });

  it('Primary on Warning meets the minimum 3:1 contrast for large text/graphics', () => {
    expect(contrastRatio(colors.primary, colors.warning)).toBeGreaterThanOrEqual(AA_LARGE_TEXT_OR_GRAPHIC);
  });
});
