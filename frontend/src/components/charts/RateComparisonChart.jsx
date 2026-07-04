import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell, ReferenceLine, ErrorBar } from 'recharts'
import { chartTheme } from './theme'

function RateComparisonChart({
  controlRate,
  treatmentRate,
  controlCI = null,
  treatmentCI = null,
  label = 'Event Rate',
  unit = 'per day'
}) {
  const t = chartTheme()
  if (controlRate === undefined || treatmentRate === undefined) return null

  const data = [
    {
      name: 'Control',
      rate: controlRate,
      error: controlCI ? [controlRate - controlCI[0], controlCI[1] - controlRate] : [0, 0],
    },
    {
      name: 'Treatment',
      rate: treatmentRate,
      error: treatmentCI ? [treatmentRate - treatmentCI[0], treatmentCI[1] - treatmentRate] : [0, 0],
    }
  ]

  const maxRate = Math.max(
    controlCI ? controlCI[1] : controlRate,
    treatmentCI ? treatmentCI[1] : treatmentRate
  ) * 1.15

  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      const d = payload[0].payload
      return (
        <div className="chart-tooltip">
          <p className="tooltip-label">{d.name}</p>
          <p className="tooltip-value">{d.rate.toFixed(4)} {unit}</p>
        </div>
      )
    }
    return null
  }

  const percentChange = controlRate !== 0
    ? ((treatmentRate - controlRate) / controlRate * 100).toFixed(1)
    : null

  return (
    <div className="rate-comparison-container">
      <div className="chart-title">{label} Comparison</div>
      <ResponsiveContainer width="100%" height={150}>
        <BarChart data={data} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
          <XAxis 
            dataKey="name" 
            tick={{ fontSize: 12, fill: t.axisText }}
            axisLine={{ stroke: t.axisLine }}
          />
          <YAxis 
            domain={[0, maxRate]}
            tickFormatter={(v) => v.toFixed(2)}
            tick={{ fontSize: 11, fill: t.axisText }}
            axisLine={{ stroke: t.axisLine }}
          />
          <Tooltip content={<CustomTooltip />} />
          <ReferenceLine 
            y={controlRate} 
            stroke={t.control} 
            strokeDasharray="4 4" 
            strokeOpacity={0.6}
          />
          <Bar dataKey="rate" radius={[4, 4, 0, 0]} barSize={60} isAnimationActive={false}>
            <Cell fill={t.controlTint} stroke={t.control} strokeWidth={1} />
            <Cell fill={treatmentRate < controlRate ? t.variantTint : t.badTint} stroke={treatmentRate < controlRate ? t.variant : t.bad} strokeWidth={1} />
            {(controlCI || treatmentCI) && (
              <ErrorBar dataKey="error" width={6} strokeWidth={1.5} stroke={t.ink} />
            )}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
      {percentChange !== null && (
        <div className="rate-change-indicator">
          <span className={`rate-change ${treatmentRate < controlRate ? 'decrease' : 'increase'}`}>
            {treatmentRate < controlRate ? '↓' : '↑'} {Math.abs(parseFloat(percentChange))}%
          </span>
          <span className="rate-change-label">
            {treatmentRate < controlRate ? 'reduction' : 'increase'} in treatment
          </span>
        </div>
      )}
    </div>
  )
}

export default RateComparisonChart
