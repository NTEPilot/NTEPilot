import { useCallback, useEffect, useMemo, useState } from 'react';
import { applyTheme, argbFromHex, hexFromArgb, themeFromSourceColor } from '@material/material-color-utilities';

export type ThemeMode = 'light' | 'dark';

const THEME_STORAGE_KEY = 'ntepilot.themeMode';
const MATERIAL_BLUE = '#006CFF';
const META_THEME_COLORS: Record<ThemeMode, string> = {
  light: '#FBF8FF',
  dark: '#111318',
};

const SURFACE_TONES = {
  light: {
    surfaceDim: 87,
    surface: 98,
    surfaceBright: 98,
    surfaceContainerLowest: 100,
    surfaceContainerLow: 96,
    surfaceContainer: 94,
    surfaceContainerHigh: 92,
    surfaceContainerHighest: 90,
    surfaceVariant: 90,
    onSurface: 10,
    onSurfaceVariant: 30,
    inverseSurface: 20,
    inverseOnSurface: 95,
    outline: 50,
    outlineVariant: 80,
    primary: 40,
    inversePrimary: 80,
  },
  dark: {
    surfaceDim: 6,
    surface: 6,
    surfaceBright: 24,
    surfaceContainerLowest: 4,
    surfaceContainerLow: 10,
    surfaceContainer: 12,
    surfaceContainerHigh: 17,
    surfaceContainerHighest: 22,
    surfaceVariant: 30,
    onSurface: 90,
    onSurfaceVariant: 80,
    inverseSurface: 90,
    inverseOnSurface: 20,
    outline: 60,
    outlineVariant: 30,
    primary: 80,
    inversePrimary: 40,
  },
} as const;

function preferredTheme(): ThemeMode {
  const stored = localStorage.getItem(THEME_STORAGE_KEY);
  if (stored === 'light' || stored === 'dark') return stored;
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
}

function syncThemeColor(mode: ThemeMode) {
  const themeColor = META_THEME_COLORS[mode];
  let meta = document.querySelector<HTMLMetaElement>('meta[name="theme-color"]');
  if (!meta) {
    meta = document.createElement('meta');
    meta.name = 'theme-color';
    document.head.appendChild(meta);
  }
  meta.content = themeColor;
}

function setColor(target: HTMLElement, token: string, color: number) {
  target.style.setProperty(token, hexFromArgb(color));
}

function applyMaterialWebSurfaceTokens(
  target: HTMLElement,
  theme: ReturnType<typeof themeFromSourceColor>,
  mode: ThemeMode,
) {
  const tones = SURFACE_TONES[mode];
  const neutral = theme.palettes.neutral;
  const neutralVariant = theme.palettes.neutralVariant;
  const primary = theme.palettes.primary;

  setColor(target, '--md-sys-color-surface-dim', neutral.tone(tones.surfaceDim));
  setColor(target, '--md-sys-color-surface', neutral.tone(tones.surface));
  setColor(target, '--md-sys-color-surface-bright', neutral.tone(tones.surfaceBright));
  setColor(target, '--md-sys-color-surface-container-lowest', neutral.tone(tones.surfaceContainerLowest));
  setColor(target, '--md-sys-color-surface-container-low', neutral.tone(tones.surfaceContainerLow));
  setColor(target, '--md-sys-color-surface-container', neutral.tone(tones.surfaceContainer));
  setColor(target, '--md-sys-color-surface-container-high', neutral.tone(tones.surfaceContainerHigh));
  setColor(target, '--md-sys-color-surface-container-highest', neutral.tone(tones.surfaceContainerHighest));
  setColor(target, '--md-sys-color-on-surface', neutral.tone(tones.onSurface));
  setColor(target, '--md-sys-color-surface-variant', neutralVariant.tone(tones.surfaceVariant));
  setColor(target, '--md-sys-color-on-surface-variant', neutralVariant.tone(tones.onSurfaceVariant));
  setColor(target, '--md-sys-color-inverse-surface', neutral.tone(tones.inverseSurface));
  setColor(target, '--md-sys-color-inverse-on-surface', neutral.tone(tones.inverseOnSurface));
  setColor(target, '--md-sys-color-outline', neutralVariant.tone(tones.outline));
  setColor(target, '--md-sys-color-outline-variant', neutralVariant.tone(tones.outlineVariant));
  setColor(target, '--md-sys-color-surface-tint', primary.tone(tones.primary));
  setColor(target, '--md-sys-color-inverse-primary', primary.tone(tones.inversePrimary));
  target.style.setProperty('--md-sys-color-scrim', '#000000');
}

export function useThemeMode() {
  const [mode, setModeState] = useState<ThemeMode>(preferredTheme);
  const theme = useMemo(() => themeFromSourceColor(argbFromHex(MATERIAL_BLUE)), []);

  useEffect(() => {
    document.documentElement.dataset.theme = mode;
    document.documentElement.style.colorScheme = mode;
    applyTheme(theme, { target: document.documentElement, dark: mode === 'dark' });
    applyMaterialWebSurfaceTokens(document.documentElement, theme, mode);
    localStorage.setItem(THEME_STORAGE_KEY, mode);
    syncThemeColor(mode);
  }, [mode, theme]);

  const setMode = useCallback((nextMode: ThemeMode) => {
    setModeState(nextMode);
  }, []);

  const toggleTheme = useCallback(() => {
    setModeState((current) => (current === 'dark' ? 'light' : 'dark'));
  }, []);

  return {
    mode,
    setMode,
    toggleTheme,
    isDark: mode === 'dark',
  };
}
