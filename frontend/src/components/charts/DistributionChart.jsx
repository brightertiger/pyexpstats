import { useMemo } from 'react'
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts'
import { chartTheme } from './theme'

function normalPDF(x, mean, std) {
  const coefficient = 1 / (std * Math.sqrt(2 * Math.PI))
  const exponent = -0.5 * Math.pow((x - mean) / std, 2)
  return coefficient * Math.exp(exponent)
}

function DistributionChart({
  controlMean,
  variantMean,
  controlStd,
  variantStd = null,
  controlN,
  variantN,
  isConversion = true
}) {
  const t = chartTheme()
  const data = useMemo(() => {
    if (!controlMean || !variantMean || !controlN || !variantN) return null
    
    const se1 = isConversion 
      ? Math.sqrt((controlMean * (1 - controlMean)) / controlN)
      : (controlStd || 1) / Math.sqrt(controlN)
    const se2 = isConversion 
      ? Math.sqrt((variantMean * (1 - variantMean)) / variantN)
      : (variantStd || controlStd || 1) / Math.sqrt(variantN)

    // Plot the actual sampling distribution of each rate/mean (std = SE), so
    // visual overlap between the curves reflects statistical uncertainty.
    const displayStd1 = Math.max(se1, 1e-6)
    const displayStd2 = Math.max(se2, 1e-6)

    const minX = Math.min(controlMean - 4 * displayStd1, variantMean - 4 * displayStd2)
    const maxX = Math.max(controlMean + 4 * displayStd1, variantMean + 4 * displayStd2)
    
    const points = []
    const numPoints = 100
    
    for (let i = 0; i <= numPoints; i++) {
      const x = minX + (maxX - minX) * (i / numPoints)
      const y1 = normalPDF(x, controlMean, displayStd1)
      const y2 = normalPDF(x, variantMean, displayStd2)
      points.push({
        x,
        control: y1,
        variant: y2
      })
    }
    
    return { points, controlMean, variantMean }
  }, [controlMean, variantMean, controlStd, variantStd, controlN, variantN, isConversion])

  if (!data) return null

  const formatXAxis = (value) => {
    if (isConversion) {
      return `${(value * 100).toFixed(1)}%`
    }
    return value.toFixed(1)
  }

  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      return (
        <div className="chart-tooltip">
          <p className="tooltip-label">
            {isConversion ? `${(label * 100).toFixed(2)}%` : label.toFixed(2)}
          </p>
        </div>
      )
    }
    return null
  }

  return (
    <div className="distribution-container">
      <div className="chart-title">Uncertainty in Each Estimate</div>
      <ResponsiveContainer width="100%" height={200}>
        <AreaChart data={data.points} margin={{ top: 10, right: 20, left: 20, bottom: 10 }}>
          <defs>
            <linearGradient id="controlGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor={t.controlTint} stopOpacity={0.8}/>
              <stop offset="95%" stopColor={t.controlTint} stopOpacity={0.1}/>
            </linearGradient>
            <linearGradient id="variantGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor={t.variantTint} stopOpacity={0.8}/>
              <stop offset="95%" stopColor={t.variantTint} stopOpacity={0.1}/>
            </linearGradient>
          </defs>
          <XAxis
            dataKey="x"
            type="number"
            domain={['dataMin', 'dataMax']}
            tickFormatter={formatXAxis}
            tick={{ fontSize: 11, fill: t.axisText }}
            axisLine={{ stroke: t.axisLine }}
            tickCount={7}
          />
          <YAxis hide />
          <Tooltip content={<CustomTooltip />} />
          <ReferenceLine 
            x={data.controlMean} 
            stroke={t.control} 
            strokeDasharray="4 4"
            strokeWidth={1.5}
          />
          <ReferenceLine 
            x={data.variantMean} 
            stroke={t.variant} 
            strokeDasharray="4 4"
            strokeWidth={1.5}
          />
          <Area
            type="monotone"
            dataKey="control"
            stroke={t.control}
            fill="url(#controlGradient)"
            strokeWidth={2}
            name="Control"
            isAnimationActive={false}
          />
          <Area
            type="monotone"
            dataKey="variant"
            stroke={t.variant}
            fill="url(#variantGradient)"
            strokeWidth={2}
            name="Variant"
            isAnimationActive={false}
          />
        </AreaChart>
      </ResponsiveContainer>
      <div className="chart-legend">
        <span className="legend-item">
          <span className="legend-color control"></span>
          Control ({isConversion ? `${(data.controlMean * 100).toFixed(2)}%` : data.controlMean.toFixed(2)})
        </span>
        <span className="legend-item">
          <span className="legend-color variant"></span>
          Variant ({isConversion ? `${(data.variantMean * 100).toFixed(2)}%` : data.variantMean.toFixed(2)})
        </span>
      </div>
    </div>
  )
}

export default DistributionChart
