import { useMemo } from 'react'
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, ReferenceLine, Area, ComposedChart } from 'recharts'
import { chartTheme } from './theme'

// Standard normal CDF (Abramowitz & Stegun 7.1.26 via erf)
function normCdf(x) {
  const t = 1 / (1 + 0.3275911 * Math.abs(x) / Math.SQRT2)
  const erf = 1 - (((((1.061405429 * t - 1.453152027) * t) + 1.421413741) * t - 0.284496736) * t + 0.254829592) * t * Math.exp(-(x * x) / 2)
  return x >= 0 ? 0.5 * (1 + erf) : 0.5 * (1 - erf)
}

// Inverse standard normal CDF (Acklam's approximation)
function normInv(p) {
  const a = [-39.6968302866538, 220.946098424521, -275.928510446969, 138.357751867269, -30.6647980661472, 2.50662827745924]
  const b = [-54.4760987982241, 161.585836858041, -155.698979859887, 66.8013118877197, -13.2806815528857]
  const c = [-0.00778489400243029, -0.322396458041136, -2.40075827716184, -2.54973253934373, 4.37466414146497, 2.93816398269878]
  const d = [0.00778469570904146, 0.32246712907004, 2.445134137143, 3.75440866190742]
  const pLow = 0.02425
  let q, r
  if (p < pLow) {
    q = Math.sqrt(-2 * Math.log(p))
    return (((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) /
      ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1)
  } else if (p <= 1 - pLow) {
    q = p - 0.5
    r = q * q
    return (((((a[0] * r + a[1]) * r + a[2]) * r + a[3]) * r + a[4]) * r + a[5]) * q /
      (((((b[0] * r + b[1]) * r + b[2]) * r + b[3]) * r + b[4]) * r + 1)
  } else {
    q = Math.sqrt(-2 * Math.log(1 - p))
    return -(((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) /
      ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1)
  }
}

function PowerCurveChart({
  requiredN,
  power,
  confidence = 95,
}) {
  const t = chartTheme()
  const data = useMemo(() => {
    if (!requiredN || requiredN <= 0 || !power) return null

    // Achieved power at sample size n, anchored so the curve passes exactly
    // through (requiredN, targetPower):
    //   power(n) = Phi( sqrt(n / requiredN) * (z_{a/2} + z_target) - z_{a/2} )
    const zAlpha = normInv(1 - (1 - confidence / 100) / 2)
    const zTarget = normInv(power / 100)

    const points = []
    const maxN = requiredN * 2
    const step = Math.max(1, Math.floor(maxN / 60))

    for (let n = Math.max(step, Math.floor(requiredN * 0.1)); n <= maxN; n += step) {
      const achievedPower = normCdf(Math.sqrt(n / requiredN) * (zAlpha + zTarget) - zAlpha) * 100
      points.push({ n, power: achievedPower })
    }

    return points
  }, [requiredN, power, confidence])

  if (!data) return null

  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      return (
        <div className="chart-tooltip">
          <p className="tooltip-label">Sample Size: {label.toLocaleString()}</p>
          <p className="tooltip-value">Power: {payload[0].value.toFixed(1)}%</p>
        </div>
      )
    }
    return null
  }

  return (
    <div className="power-curve-container">
      <div className="chart-title">Statistical Power vs Sample Size</div>
      <ResponsiveContainer width="100%" height={200}>
        <ComposedChart data={data} margin={{ top: 10, right: 30, left: 10, bottom: 10 }}>
          <defs>
            <linearGradient id="powerGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor={t.accentTint} stopOpacity={0.6}/>
              <stop offset="95%" stopColor={t.accentTint} stopOpacity={0.1}/>
            </linearGradient>
          </defs>
          <XAxis
            dataKey="n"
            type="number"
            domain={['dataMin', 'dataMax']}
            tickFormatter={(v) => v >= 1000 ? `${(v/1000).toFixed(0)}k` : v}
            tick={{ fontSize: 11, fill: t.axisText }}
            axisLine={{ stroke: t.axisLine }}
            tickCount={8}
          />
          <YAxis
            domain={[0, 100]}
            ticks={[0, 20, 40, 60, 80, 100]}
            tickFormatter={(v) => `${v}%`}
            tick={{ fontSize: 11, fill: t.axisText }}
            axisLine={{ stroke: t.axisLine }}
          />
          <Tooltip content={<CustomTooltip />} />
          <ReferenceLine
            y={power}
            stroke={t.variant}
            strokeDasharray="4 4"
          />
          <ReferenceLine
            x={requiredN}
            stroke={t.control}
            strokeDasharray="4 4"
          />
          <Area
            type="monotone"
            dataKey="power"
            fill="url(#powerGradient)"
            stroke="none"
            isAnimationActive={false}
          />
          <Line
            type="monotone"
            dataKey="power"
            stroke={t.accent}
            strokeWidth={2.5}
            dot={false}
            isAnimationActive={false}
          />
        </ComposedChart>
      </ResponsiveContainer>
      <div className="chart-legend">
        <span className="legend-item">
          <span className="legend-line solid purple"></span>
          Power curve
        </span>
        <span className="legend-item">
          <span className="legend-line dashed green"></span>
          Target power ({power}%)
        </span>
        <span className="legend-item">
          <span className="legend-line dashed blue"></span>
          Required N ({requiredN.toLocaleString()})
        </span>
      </div>
    </div>
  )
}

export default PowerCurveChart
