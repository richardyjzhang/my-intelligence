import type { ThemePreset } from './presets'

const SERVER_PRESET_ID = '__server__'

function parseHex(hex: string): { r: number; g: number; b: number } | null {
  const m = /^#?([0-9a-fA-F]{6})$/.exec(hex.trim())
  if (!m) return null
  const n = parseInt(m[1], 16)
  return { r: (n >> 16) & 255, g: (n >> 8) & 255, b: n & 255 }
}

function toHex(r: number, g: number, b: number): string {
  const clamp = (x: number) => Math.max(0, Math.min(255, Math.round(x)))
  return `#${[clamp(r), clamp(g), clamp(b)]
    .map((x) => x.toString(16).padStart(2, '0'))
    .join('')}`
}

function mix(
  a: { r: number; g: number; b: number },
  b: { r: number; g: number; b: number },
  t: number,
) {
  return {
    r: a.r + (b.r - a.r) * t,
    g: a.g + (b.g - a.g) * t,
    b: a.b + (b.b - a.b) * t,
  }
}

/** 根据后端主题色 hex 推导 hover / pressed，与内置预设观感一致 */
export function themePresetFromPrimaryHex(name: string, primaryHex: string): ThemePreset {
  const p = parseHex(primaryHex)
  if (!p) {
    return {
      id: SERVER_PRESET_ID,
      name,
      primary: '#0891b2',
      primaryHover: '#1ab3d0',
      primaryPressed: '#06748c',
      primarySuppl: '#06748c',
    }
  }
  const white = { r: 255, g: 255, b: 255 }
  const black = { r: 0, g: 0, b: 0 }
  const hover = mix(p, white, 0.12)
  const pressed = mix(p, black, 0.15)
  const suppl = mix(p, black, 0.12)
  return {
    id: SERVER_PRESET_ID,
    name,
    primary: toHex(p.r, p.g, p.b),
    primaryHover: toHex(hover.r, hover.g, hover.b),
    primaryPressed: toHex(pressed.r, pressed.g, pressed.b),
    primarySuppl: toHex(suppl.r, suppl.g, suppl.b),
  }
}
