import React, { createContext, useContext, useState, useMemo, useCallback } from 'react';
import { createTheme, ThemeProvider as MuiThemeProvider, Theme, alpha } from '@mui/material/styles';

type ThemeMode = 'light' | 'dark';

export interface AccentColor {
  name: string;
  main: string;
  light: string;
  dark: string;
}

export const ACCENT_COLORS: AccentColor[] = [
  { name: 'Blue', main: '#2563eb', light: '#60a5fa', dark: '#1d4ed8' },
  { name: 'Indigo', main: '#4f46e5', light: '#818cf8', dark: '#3730a3' },
  { name: 'Violet', main: '#7c3aed', light: '#a78bfa', dark: '#5b21b6' },
  { name: 'Rose', main: '#e11d48', light: '#fb7185', dark: '#9f1239' },
  { name: 'Emerald', main: '#059669', light: '#34d399', dark: '#047857' },
  { name: 'Teal', main: '#0d9488', light: '#2dd4bf', dark: '#0f766e' },
  { name: 'Amber', main: '#d97706', light: '#fbbf24', dark: '#b45309' },
  { name: 'Slate', main: '#475569', light: '#94a3b8', dark: '#334155' },
];

interface ThemeContextType {
  mode: ThemeMode;
  toggleMode: () => void;
  accentColor: AccentColor;
  setAccentColor: (color: AccentColor) => void;
  accentColors: AccentColor[];
  theme: Theme;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

export const useThemeContext = () => {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useThemeContext must be used within a ThemeContextProvider');
  }
  return context;
};

function buildTheme(mode: ThemeMode, accent: AccentColor): Theme {
  const isLight = mode === 'light';

  return createTheme({
    palette: {
      mode,
      primary: {
        main: accent.main,
        light: accent.light,
        dark: accent.dark,
      },
      secondary: {
        main: isLight ? '#6b7280' : '#9ca3af',
        light: isLight ? '#9ca3af' : '#d1d5db',
        dark: isLight ? '#374151' : '#6b7280',
      },
      background: {
        default: isLight ? '#f8fafc' : '#0f172a',
        paper: isLight ? '#ffffff' : '#1e293b',
      },
      success: { main: '#10b981', light: '#34d399', dark: '#059669' },
      warning: { main: '#f59e0b', light: '#fbbf24', dark: '#d97706' },
      error: { main: '#ef4444', light: '#f87171', dark: '#dc2626' },
      info: { main: '#3b82f6', light: '#60a5fa', dark: '#2563eb' },
      divider: isLight ? '#e2e8f0' : '#334155',
      text: {
        primary: isLight ? '#0f172a' : '#f1f5f9',
        secondary: isLight ? '#64748b' : '#94a3b8',
      },
    },
    typography: {
      fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
      h1: { fontSize: '2.25rem', fontWeight: 700, letterSpacing: '-0.025em' },
      h2: { fontSize: '1.875rem', fontWeight: 700, letterSpacing: '-0.025em' },
      h3: { fontSize: '1.5rem', fontWeight: 600, letterSpacing: '-0.01em' },
      h4: { fontSize: '1.25rem', fontWeight: 600, letterSpacing: '-0.01em' },
      h5: { fontSize: '1.125rem', fontWeight: 600 },
      h6: { fontSize: '1rem', fontWeight: 600 },
      subtitle1: { fontWeight: 500 },
      subtitle2: { fontWeight: 500 },
      body2: { fontSize: '0.875rem', lineHeight: 1.6 },
    },
    shape: { borderRadius: 12 },
    shadows: [
      'none',
      isLight
        ? '0 1px 2px 0 rgb(0 0 0 / 0.05)'
        : '0 1px 2px 0 rgb(0 0 0 / 0.3)',
      isLight
        ? '0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1)'
        : '0 1px 3px 0 rgb(0 0 0 / 0.4), 0 1px 2px -1px rgb(0 0 0 / 0.3)',
      isLight
        ? '0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)'
        : '0 4px 6px -1px rgb(0 0 0 / 0.4), 0 2px 4px -2px rgb(0 0 0 / 0.3)',
      isLight
        ? '0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1)'
        : '0 10px 15px -3px rgb(0 0 0 / 0.4), 0 4px 6px -4px rgb(0 0 0 / 0.3)',
      isLight
        ? '0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1)'
        : '0 20px 25px -5px rgb(0 0 0 / 0.4), 0 8px 10px -6px rgb(0 0 0 / 0.3)',
      // Rest are the same as shadow[5] for simplicity
      ...Array(19).fill(
        isLight
          ? '0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1)'
          : '0 20px 25px -5px rgb(0 0 0 / 0.4), 0 8px 10px -6px rgb(0 0 0 / 0.3)'
      ),
    ] as Theme['shadows'],
    components: {
      MuiCssBaseline: {
        styleOverrides: {
          body: {
            scrollbarWidth: 'thin',
            scrollbarColor: isLight ? '#cbd5e1 transparent' : '#475569 transparent',
          },
          '::-webkit-scrollbar': {
            width: '6px',
            height: '6px',
          },
          '::-webkit-scrollbar-track': {
            background: 'transparent',
          },
          '::-webkit-scrollbar-thumb': {
            background: isLight ? '#cbd5e1' : '#475569',
            borderRadius: '3px',
          },
          '::-webkit-scrollbar-thumb:hover': {
            background: isLight ? '#94a3b8' : '#64748b',
          },
        },
      },
      MuiButton: {
        styleOverrides: {
          root: {
            textTransform: 'none' as const,
            borderRadius: 10,
            padding: '8px 20px',
            fontWeight: 600,
            fontSize: '0.875rem',
            boxShadow: 'none',
            '&:hover': {
              boxShadow: 'none',
            },
          },
          contained: {
            '&:hover': {
              boxShadow: `0 4px 12px ${alpha(accent.main, 0.4)}`,
            },
          },
        },
      },
      MuiCard: {
        styleOverrides: {
          root: {
            borderRadius: 16,
            border: `1px solid ${isLight ? '#e2e8f0' : '#334155'}`,
            boxShadow: isLight
              ? '0 1px 3px 0 rgb(0 0 0 / 0.04)'
              : '0 1px 3px 0 rgb(0 0 0 / 0.2)',
            backgroundImage: 'none',
            transition: 'border-color 0.2s ease, box-shadow 0.2s ease',
            '&:hover': {
              borderColor: isLight ? '#cbd5e1' : '#475569',
              boxShadow: isLight
                ? '0 4px 12px 0 rgb(0 0 0 / 0.06)'
                : '0 4px 12px 0 rgb(0 0 0 / 0.3)',
            },
          },
        },
      },
      MuiPaper: {
        styleOverrides: {
          root: {
            borderRadius: 16,
            backgroundImage: 'none',
          },
        },
      },
      MuiChip: {
        styleOverrides: {
          root: {
            fontWeight: 500,
            borderRadius: 8,
          },
        },
      },
      MuiLinearProgress: {
        styleOverrides: {
          root: {
            borderRadius: 4,
            height: 6,
            backgroundColor: isLight ? '#e2e8f0' : '#334155',
          },
        },
      },
      MuiDialog: {
        styleOverrides: {
          paper: {
            borderRadius: 20,
            border: `1px solid ${isLight ? '#e2e8f0' : '#334155'}`,
          },
        },
      },
      MuiDrawer: {
        styleOverrides: {
          paper: {
            borderRight: 'none',
          },
        },
      },
      MuiAppBar: {
        styleOverrides: {
          root: {
            backgroundImage: 'none',
          },
        },
      },
      MuiListItemButton: {
        styleOverrides: {
          root: {
            borderRadius: 10,
            '&.Mui-selected': {
              backgroundColor: alpha(accent.main, isLight ? 0.1 : 0.2),
              color: accent.main,
              '& .MuiListItemIcon-root': {
                color: accent.main,
              },
              '&:hover': {
                backgroundColor: alpha(accent.main, isLight ? 0.15 : 0.25),
              },
            },
          },
        },
      },
    },
  });
}

export const ThemeContextProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [mode, setMode] = useState<ThemeMode>(() => {
    return (localStorage.getItem('compliance-theme-mode') as ThemeMode) || 'light';
  });

  const [accentColor, setAccentColorState] = useState<AccentColor>(() => {
    try {
      const saved = localStorage.getItem('compliance-accent-color');
      if (saved) {
        const parsed = JSON.parse(saved);
        return ACCENT_COLORS.find(c => c.name === parsed.name) || ACCENT_COLORS[0];
      }
    } catch {}
    return ACCENT_COLORS[0];
  });

  const toggleMode = useCallback(() => {
    setMode((prev) => {
      const next = prev === 'light' ? 'dark' : 'light';
      localStorage.setItem('compliance-theme-mode', next);
      return next;
    });
  }, []);

  const setAccentColor = useCallback((color: AccentColor) => {
    setAccentColorState(color);
    localStorage.setItem('compliance-accent-color', JSON.stringify(color));
  }, []);

  const theme = useMemo(() => buildTheme(mode, accentColor), [mode, accentColor]);

  const value = useMemo(
    () => ({
      mode,
      toggleMode,
      accentColor,
      setAccentColor,
      accentColors: ACCENT_COLORS,
      theme,
    }),
    [mode, toggleMode, accentColor, setAccentColor, theme]
  );

  return (
    <ThemeContext.Provider value={value}>
      <MuiThemeProvider theme={theme}>
        {children}
      </MuiThemeProvider>
    </ThemeContext.Provider>
  );
};
