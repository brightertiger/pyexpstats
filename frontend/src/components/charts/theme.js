// Chart colors read from the CSS token layer so recharts and the stylesheet
// share one palette. Fallbacks mirror the tokens for non-browser contexts.
let cache = null

export function chartTheme() {
  if (cache) return cache
  const css = typeof window !== 'undefined'
    ? getComputedStyle(document.documentElement)
    : null
  const v = (name, fallback) => {
    const value = css ? css.getPropertyValue(name).trim() : ''
    return value || fallback
  }
  cache = {
    control: v('--control', '#47639b'),
    controlTint: v('--control-tint', '#e3e8f2'),
    variant: v('--variant', '#2e7b4f'),
    variantTint: v('--variant-tint', '#e0eee4'),
    bad: v('--bad', '#a64840'),
    badTint: v('--bad-tint', '#f5e4e0'),
    warn: v('--warn', '#8f6512'),
    accent: v('--accent', '#0e6e66'),
    accentTint: v('--accent-tint', '#dcebe6'),
    ink: v('--ink', '#23201c'),
    axisText: v('--ink-3', '#6e6557'),
    axisLine: v('--line', '#e3dbca'),
  }
  return cache
}
