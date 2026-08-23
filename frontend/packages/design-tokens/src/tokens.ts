export const colors = {
  primary: '#0F172A',
  primary2: '#1E3A5F',
  accent: '#C8A96B',
  background: '#F7F4ED',
  surface: '#FFFFFF',
  text: '#111827',
  textSecondary: '#64748B',
  border: '#E5E1D8',
  success: '#3F7D58',
  error: '#B94A48',
  warning: '#B7791F',
} as const;

export const radius = {
  card: '10px',
  sm: '6px',
  lg: '12px',
} as const;

export const typography = {
  fontFamilyBase: "'Inter', sans-serif",
  fontFamilyDisplay: "'DM Serif Display', serif",
  fontSizeDisplay: '48px',
  fontSizeH1: '32px',
  fontSizeH2: '24px',
  fontSizeH3: '20px',
  fontSizeBody: '16px',
  fontSizeSmall: '13px',
  fontWeightRegular: 400,
  fontWeightMedium: 500,
  fontWeightSemibold: 600,
  fontWeightBold: 700,
} as const;

export const spacing = {
  1: '4px',
  2: '8px',
  3: '12px',
  4: '16px',
  5: '20px',
  6: '24px',
  8: '32px',
  10: '40px',
  12: '48px',
  16: '64px',
} as const;

export const shadows = {
  sm: '0 1px 2px rgba(0, 0, 0, 0.05)',
  md: '0 1px 3px rgba(0, 0, 0, 0.08)',
} as const;

export const transitions = {
  base: '150ms ease',
} as const;

export const zIndex = {
  header: 100,
  modal: 1000,
} as const;

export const breakpoints = {
  sm: 640,
  md: 768,
  lg: 1024,
} as const;
