import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts'
import { chartTheme } from './theme'

function DiffInDiffChart({
  controlPre,
  controlPost,
  treatmentPre,
  treatmentPost,
  isConversion = true,
  diffInDiff = null
}) {
  const t = chartTheme()
  if (controlPre === undefined || controlPost === undefined || 
      treatmentPre === undefined || treatmentPost === undefined) return null

  const data = [
    {
      period: 'Pre-Period',
      control: controlPre,
      treatment: treatmentPre,
      // Counterfactual starts at the treatment pre-period value and follows
      // the control group's trend
      counterfactual: treatmentPre
    },
    {
      period: 'Post-Period',
      control: controlPost,
      treatment: treatmentPost,
      counterfactual: treatmentPre + (controlPost - controlPre)
    }
  ]

  const formatValue = (v) => {
    if (v === null || v === undefined) return ''
    return isConversion ? `${(v * 100).toFixed(2)}%` : `$${v.toFixed(2)}`
  }

  const allValues = [controlPre, controlPost, treatmentPre, treatmentPost]
  const minVal = Math.min(...allValues) * 0.9
  const maxVal = Math.max(...allValues) * 1.1

  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      return (
        <div className="chart-tooltip">
          <p className="tooltip-label">{label}</p>
          {payload.filter(p => p.value !== null).map((p, i) => (
            <p key={i} className="tooltip-value" style={{ color: p.color }}>
              {p.name}: {formatValue(p.value)}
            </p>
          ))}
        </div>
      )
    }
    return null
  }

  const controlChange = controlPost - controlPre
  const treatmentChange = treatmentPost - treatmentPre

  return (
    <div className="did-chart-container">
      <div className="chart-title">Parallel Trends Visualization</div>
      <ResponsiveContainer width="100%" height={220}>
        <LineChart data={data} margin={{ top: 20, right: 30, left: 20, bottom: 10 }}>
          <XAxis 
            dataKey="period" 
            tick={{ fontSize: 12, fill: t.axisText }}
            axisLine={{ stroke: t.axisLine }}
          />
          <YAxis 
            domain={[minVal, maxVal]}
            tickFormatter={(v) => isConversion ? `${(v * 100).toFixed(1)}%` : v.toFixed(0)}
            tick={{ fontSize: 11, fill: t.axisText }}
            axisLine={{ stroke: t.axisLine }}
          />
          <Tooltip content={<CustomTooltip />} />
          <ReferenceLine 
            x="Post-Period" 
            stroke={t.axisLine} 
            strokeDasharray="2 2"
          />
          
          <Line
            type="linear"
            dataKey="control"
            stroke={t.control}
            strokeWidth={2.5}
            dot={{ fill: t.control, r: 5 }}
            name="Control"
            isAnimationActive={false}
          />
          <Line
            type="linear"
            dataKey="treatment"
            stroke={t.variant}
            strokeWidth={2.5}
            dot={{ fill: t.variant, r: 5 }}
            name="Treatment"
            isAnimationActive={false}
          />
          <Line
            type="linear"
            dataKey="counterfactual"
            stroke={t.warn}
            strokeWidth={2}
            strokeDasharray="5 5"
            dot={{ fill: t.warn, r: 4 }}
            name="Counterfactual"
            isAnimationActive={false}
          />
        </LineChart>
      </ResponsiveContainer>
      
      <div className="did-explanation">
        <div className="did-arrows">
          <div className="did-arrow control">
            <span className="arrow-label">Control Δ</span>
            <span className="arrow-value">
              {controlChange >= 0 ? '+' : ''}{isConversion ? `${(controlChange * 100).toFixed(2)}pp` : `$${controlChange.toFixed(2)}`}
            </span>
          </div>
          <div className="did-arrow treatment">
            <span className="arrow-label">Treatment Δ</span>
            <span className="arrow-value">
              {treatmentChange >= 0 ? '+' : ''}{isConversion ? `${(treatmentChange * 100).toFixed(2)}pp` : `$${treatmentChange.toFixed(2)}`}
            </span>
          </div>
          {diffInDiff !== null && (
            <div className="did-arrow effect">
              <span className="arrow-label">DiD Effect</span>
              <span className="arrow-value highlight">
                {diffInDiff >= 0 ? '+' : ''}{isConversion ? `${(diffInDiff * 100).toFixed(2)}pp` : `$${diffInDiff.toFixed(2)}`}
              </span>
            </div>
          )}
        </div>
      </div>
      
      <div className="chart-legend">
        <span className="legend-item">
          <span className="legend-color control"></span>
          Control Group
        </span>
        <span className="legend-item">
          <span className="legend-color variant"></span>
          Treatment Group
        </span>
        <span className="legend-item">
          <span className="legend-color counterfactual"></span>
          Counterfactual
        </span>
      </div>
    </div>
  )
}

export default DiffInDiffChart
