import { colors } from '../tokens';
import { contrastRatio } from '../contrast';

const AA_NORMAL_TEXT = 4.5;
const AA_LARGE_TEXT_OR_GRAPHIC = 3;

describe('contrast rules documented in README.md', () => {
  it.each([
    ['Text on Background', colors.text, colors.background],
    ['Text on Surface', colors.text, colors.surface],
    ['SecondaryText on Surface', colors.textSecondary, colors.surface],
    ['Surface on Primary', colors.surface, colors.primary],
    ['Surface on Primary2', colors.surface, colors.primary2],
    ['Primary on Accent', colors.primary, colors.accent],
    ['Surface on Success', colors.surface, colors.success],
    ['Surface on Error', colors.surface, colors.error],
  ])('%s meets AA for normal text (>= 4.5:1)', (_label, fg, bg) => {
    expect(contrastRatio(fg, bg)).toBeGreaterThanOrEqual(AA_NORMAL_TEXT);
  });

  it('SecondaryText on Background does NOT meet AA normal text — must not be used directly on the page background', () => {
    expect(contrastRatio(colors.textSecondary, colors.background)).toBeLessThan(AA_NORMAL_TEXT);
  });

  it('Surface on Accent does NOT meet the minimum 3:1 — Accent must not be a solid fill with light text', () => {
    expect(contrastRatio(colors.surface, colors.accent)).toBeLessThan(AA_LARGE_TEXT_OR_GRAPHIC);
  });
});
