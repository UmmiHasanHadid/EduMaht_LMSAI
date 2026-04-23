import { createTheme } from '@mui/material/styles'

// EduMaht brand: warm indigo + amber accent, inspired by mentorship & book.
const common = {
  typography: {
    fontFamily: '"Plus Jakarta Sans", "Inter", system-ui, sans-serif',
    h1: { fontSize: '2.75rem', fontWeight: 800, letterSpacing: '-0.02em' },
    h2: { fontSize: '2.15rem', fontWeight: 700, letterSpacing: '-0.01em' },
    h3: { fontSize: '1.75rem', fontWeight: 700 },
    h4: { fontSize: '1.45rem', fontWeight: 700 },
    h5: { fontSize: '1.2rem', fontWeight: 700 },
    h6: { fontSize: '1.05rem', fontWeight: 700 },
    button: { textTransform: 'none', fontWeight: 700 },
  },
  shape: { borderRadius: 14 },
  components: {
    MuiButton: {
      styleOverrides: {
        root: { borderRadius: 999, paddingInline: 22, paddingBlock: 10 },
        contained: {
          boxShadow: '0 8px 22px -12px rgba(79, 70, 229, 0.55)',
          '&:hover': { boxShadow: '0 10px 28px -12px rgba(79, 70, 229, 0.7)' },
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: 18,
          boxShadow: '0 4px 24px -18px rgba(15, 23, 42, 0.3)',
        },
      },
    },
    MuiPaper: {
      styleOverrides: { rounded: { borderRadius: 18 } },
    },
    MuiTextField: { defaultProps: { variant: 'outlined' } },
    MuiChip: { styleOverrides: { root: { fontWeight: 600 } } },
  },
}

export const lightTheme = createTheme({
  ...common,
  palette: {
    mode: 'light',
    primary: { main: '#4F46E5', light: '#6366F1', dark: '#3730A3', contrastText: '#fff' },
    secondary: { main: '#F59E0B', light: '#FBBF24', dark: '#B45309', contrastText: '#1F2937' },
    success: { main: '#10B981' },
    info: { main: '#0EA5E9' },
    warning: { main: '#F59E0B' },
    error: { main: '#EF4444' },
    background: { default: '#F6F7FB', paper: '#FFFFFF' },
    text: { primary: '#0F172A', secondary: '#475569' },
  },
})

export const darkTheme = createTheme({
  ...common,
  palette: {
    mode: 'dark',
    primary: { main: '#818CF8', light: '#A5B4FC', dark: '#4F46E5', contrastText: '#0B0F1A' },
    secondary: { main: '#FBBF24', light: '#FDE68A', dark: '#D97706', contrastText: '#0B0F1A' },
    success: { main: '#34D399' },
    info: { main: '#38BDF8' },
    warning: { main: '#FBBF24' },
    error: { main: '#F87171' },
    background: { default: '#0B1020', paper: '#11182B' },
    text: { primary: '#E5E7EB', secondary: '#94A3B8' },
  },
})
