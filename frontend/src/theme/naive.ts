import type { GlobalThemeOverrides } from 'naive-ui'
import type { ThemePreset } from './presets'

function hexToRgba(hex: string, alpha: number): string {
  const n = parseInt(hex.slice(1), 16)
  const r = (n >> 16) & 0xff
  const g = (n >> 8) & 0xff
  const b = n & 0xff
  return `rgba(${r}, ${g}, ${b}, ${alpha})`
}

export function buildNaiveThemeOverrides(
  preset: ThemePreset,
  borderRadius: string,
): GlobalThemeOverrides {
  const { primary, primaryHover, primaryPressed, primarySuppl } = preset

  return {
    common: {
      primaryColor: primary,
      primaryColorHover: primaryHover,
      primaryColorPressed: primaryPressed,
      primaryColorSuppl: primarySuppl,
      bodyColor: '#f7f8fa',
      cardColor: '#ffffff',
      borderColor: '#e5e6eb',
      borderRadius,
    },
    Layout: {
      color: '#f7f8fa',
      siderColor: '#ffffff',
      siderBorderColor: '#e5e6eb',
      headerColor: '#ffffff',
      headerBorderColor: '#e5e6eb',
    },
    Menu: {
      borderRadius,
      itemColorActive: hexToRgba(primary, 0.08),
      itemColorActiveHover: hexToRgba(primary, 0.12),
      itemColorHover: '#f7f8fa',
      itemTextColor: '#4e5969',
      itemTextColorHover: '#1d2129',
      itemTextColorActive: primary,
      itemTextColorActiveHover: primary,
      itemTextColorChildActive: primary,
      itemTextColorChildActiveHover: primary,
      itemIconColor: '#86909c',
      itemIconColorHover: '#1d2129',
      itemIconColorActive: primary,
      itemIconColorActiveHover: primary,
      itemIconColorChildActive: primary,
      itemIconColorChildActiveHover: primary,
      groupTextColor: '#86909c',
      arrowColor: '#86909c',
      arrowColorHover: '#1d2129',
      arrowColorActive: primary,
      arrowColorActiveHover: primaryHover,
      arrowColorChildActive: primary,
      arrowColorChildActiveHover: primaryHover,
    },
    Card: {
      borderColor: '#e5e6eb',
      borderRadius: '0.5rem',
      titleFontWeight: '600',
    },
    DataTable: {
      thColor: hexToRgba(primary, 0.08),
    },
  }
}
