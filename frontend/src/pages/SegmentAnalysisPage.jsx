import { useState } from 'react'
import ReactMarkdown from 'react-markdown'
import FormField from '../components/FormField'

function SegmentAnalysisPage() {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [result, setResult] = useState(null)

  const [segments, setSegments] = useState([
    { segment_name: 'device', segment_value: 'mobile', control_visitors: 5000, control_conversions: 250, variant_visitors: 5000, variant_conversions: 300 },
    { segment_name: 'device', segment_value: 'desktop', control_visitors: 3000, control_conversions: 180, variant_visitors: 3000, variant_conversions: 200 },
  ])

  const [settings, setSettings] = useState({
    correction_method: 'bonferroni',
    confidence: 95,
    min_sample_per_segment: 100,
  })

  const handleSegmentChange = (index, field, value) => {
    setSegments(prev => prev.map((seg, i) =>
      i === index ? { ...seg, [field]: field.includes('visitors') || field.includes('conversions') ? parseInt(value) || 0 : value } : seg
    ))
  }

  const addSegment = () => {
    setSegments(prev => [...prev, {
      segment_name: 'segment',
      segment_value: `value_${prev.length + 1}`,
      control_visitors: 1000,
      control_conversions: 50,
      variant_visitors: 1000,
      variant_conversions: 55
    }])
  }

  const removeSegment = (index) => {
    if (segments.length > 1) {
      setSegments(prev => prev.filter((_, i) => i !== index))
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError(null)
    setResult(null)

    try {
      const res = await fetch('/api/segments/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          segments,
          ...settings,
        }),
      })

      if (!res.ok) {
        const data = await res.json()
        throw new Error(data.detail || 'Analysis failed')
      }

      const data = await res.json()
      setResult(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Segment Analysis</h1>
        <p className="page-description">
          See how your test performs across different user groups like mobile vs desktop, new vs returning users, etc.
        </p>
      </div>

      <div className="info-box">
        <span className="info-box-icon">🎯</span>
        <div className="info-box-content">
          <div className="info-box-title">Why analyze by segment?</div>
          <div className="info-box-text">
            Your overall results can hide important differences between user groups.
            A change might work great for mobile users but hurt desktop users, or vice versa.
            Segment analysis helps you find these hidden patterns and make better decisions.
          </div>
        </div>
      </div>

      <form onSubmit={handleSubmit}>
        <div className="card">
          <div className="card-title">Segment Data</div>
          <p className="page-description" style={{ marginBottom: '16px' }}>
            Enter data for each segment you want to analyze.
          </p>

          <div className="segment-data-table">
            <div className="segment-header">
              <span>Segment</span>
              <span>Value</span>
              <span>Control Visitors</span>
              <span>Control Conv.</span>
              <span>Variant Visitors</span>
              <span>Variant Conv.</span>
              <span></span>
            </div>
            {segments.map((seg, index) => (
              <div key={index} className="segment-row">
                <input
                  type="text"
                  className="form-input"
                  value={seg.segment_name}
                  onChange={(e) => handleSegmentChange(index, 'segment_name', e.target.value)}
                  placeholder="e.g., device"
                />
                <input
                  type="text"
                  className="form-input"
                  value={seg.segment_value}
                  onChange={(e) => handleSegmentChange(index, 'segment_value', e.target.value)}
                  placeholder="e.g., mobile"
                />
                <input
                  type="number"
                  className="form-input"
                  value={seg.control_visitors}
                  onChange={(e) => handleSegmentChange(index, 'control_visitors', e.target.value)}
                  min="0"
                />
                <input
                  type="number"
                  className="form-input"
                  value={seg.control_conversions}
                  onChange={(e) => handleSegmentChange(index, 'control_conversions', e.target.value)}
                  min="0"
                />
                <input
                  type="number"
                  className="form-input"
                  value={seg.variant_visitors}
                  onChange={(e) => handleSegmentChange(index, 'variant_visitors', e.target.value)}
                  min="0"
                />
                <input
                  type="number"
                  className="form-input"
                  value={seg.variant_conversions}
                  onChange={(e) => handleSegmentChange(index, 'variant_conversions', e.target.value)}
                  min="0"
                />
                <button
                  type="button"
                  className="remove-variant-btn"
                  onClick={() => removeSegment(index)}
                  disabled={segments.length <= 1}
                >
                  ✕
                </button>
              </div>
            ))}
          </div>
          <button type="button" className="add-variant-btn" onClick={addSegment} style={{ marginTop: '12px' }}>
            <span>+</span> Add Segment
          </button>
        </div>

        <div className="card" style={{ marginTop: '16px' }}>
          <div className="card-title">Settings</div>
          <div className="form-grid">
            <FormField label="How Strict?" hint="Stricter = fewer false positives, but might miss real effects">
              <select
                className="form-select"
                value={settings.correction_method}
                onChange={(e) => setSettings(prev => ({ ...prev, correction_method: e.target.value }))}
              >
                <option value="bonferroni">Strict - Safest choice, minimizes false positives</option>
                <option value="holm">Balanced - Good middle ground (recommended)</option>
                <option value="none">No adjustment - More findings, but more false positives</option>
              </select>
            </FormField>
            <FormField label="Confidence Level" hint="How sure do you want to be?">
              <select
                className="form-select"
                value={settings.confidence}
                onChange={(e) => setSettings(prev => ({ ...prev, confidence: parseInt(e.target.value) }))}
              >
                <option value={90}>90% - Good for exploration</option>
                <option value={95}>95% - Industry standard</option>
                <option value={99}>99% - High stakes decisions</option>
              </select>
            </FormField>
            <FormField label="Minimum Visitors per Segment" hint="Segments with fewer visitors won't be analyzed">
              <input
                type="number"
                className="form-input"
                value={settings.min_sample_per_segment}
                onChange={(e) => setSettings(prev => ({ ...prev, min_sample_per_segment: parseInt(e.target.value) || 100 }))}
                min="10"
              />
            </FormField>
          </div>
        </div>

        <div style={{ marginTop: '16px' }}>
          <button type="submit" className="btn btn-primary" disabled={loading}>
            {loading ? 'Analyzing...' : 'Analyze Segments'}
          </button>
        </div>
      </form>

      {error && (
        <div className="error-message">{error}</div>
      )}

      {result && (
        <div className="results-card">
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '20px', flexWrap: 'wrap' }}>
            <span style={{ fontSize: '20px', fontWeight: 600 }}>
              Overall: <span style={{ fontFamily: 'var(--font-mono)' }}>{result.overall_lift >= 0 ? '+' : ''}{result.overall_lift?.toFixed(1)}%</span>
            </span>
            {result.heterogeneity_detected && (
              <span className="tag tag-yellow">Results Vary by Segment</span>
            )}
            {result.simpsons_paradox_risk && (
              <span className="tag tag-red">Conflicting Results Warning</span>
            )}
          </div>

          {result.best_segment && (
            <div className="stats-explanation" style={{ marginBottom: '20px' }}>
              <div className="stats-card">
                <div className="stats-card-label">Best Performing</div>
                <div className="stats-card-value" style={{ fontSize: '16px' }}>{result.best_segment}</div>
              </div>
              {result.worst_segment && result.worst_segment !== result.best_segment && (
                <div className="stats-card">
                  <div className="stats-card-label">Worst Performing</div>
                  <div className="stats-card-value" style={{ fontSize: '16px' }}>{result.worst_segment}</div>
                </div>
              )}
            </div>
          )}

          <div className="card-title">Results by Segment</div>
          <div className="summary-table-wrapper">
            <table className="summary-table">
              <thead>
                <tr>
                  <th>Segment</th>
                  <th>Improvement</th>
                  <th>Range</th>
                  <th>Confidence</th>
                  <th>Result</th>
                </tr>
              </thead>
              <tbody>
                {result.segments && result.segments
                  .sort((a, b) => b.lift_percent - a.lift_percent)
                  .map((seg, i) => (
                    <tr key={i}>
                      <td>
                        <strong>{seg.segment_value}</strong>
                        <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>{seg.segment_name}</div>
                      </td>
                      <td className="mono" style={{ color: seg.lift_percent >= 0 ? 'var(--pastel-green-text)' : 'var(--pastel-red-text)' }}>
                        {seg.lift_percent >= 0 ? '+' : ''}{seg.lift_percent.toFixed(2)}%
                      </td>
                      <td className="mono" style={{ fontSize: '12px' }}>
                        {seg.lift_ci_lower != null && seg.lift_ci_upper != null
                          ? `${seg.lift_ci_lower.toFixed(1)}% to ${seg.lift_ci_upper.toFixed(1)}%`
                          : 'N/A'}
                      </td>
                      <td className="mono">{seg.is_significant ? 'High' : 'Low'}</td>
                      <td>
                        {!seg.sample_size_adequate && (
                          <span className="tag tag-yellow" style={{ marginRight: '4px' }}>Need More Data</span>
                        )}
                        {seg.is_significant ? (
                          <span className="tag tag-green">
                            {seg.winner === 'variant' ? 'Variant Wins' : 'Control Wins'}
                          </span>
                        ) : (
                          <span className="tag tag-yellow">No Clear Winner</span>
                        )}
                      </td>
                    </tr>
                  ))}
              </tbody>
            </table>
          </div>

          <div className="stats-explanation" style={{ marginTop: '20px' }}>
            <div className="stats-card">
              <div className="stats-card-label">Analysis Mode</div>
              <div className="stats-card-value">
                {result.correction_method === 'bonferroni' ? 'Strict' :
                 result.correction_method === 'holm' ? 'Balanced' : 'No adjustment'}
              </div>
              <div className="stats-card-explanation">
                {result.correction_method === 'bonferroni' ? 'Safest - minimizes false positives' :
                 result.correction_method === 'holm' ? 'Good balance of accuracy and sensitivity' :
                 'May show more false positives'}
              </div>
            </div>
            <div className="stats-card">
              <div className="stats-card-label">Segments with Clear Winners</div>
              <div className="stats-card-value">{result.segments?.filter(s => s.is_significant).length || 0} of {result.n_segments}</div>
              <div className="stats-card-explanation">
                Segments where we're confident about the winner
              </div>
            </div>
          </div>

          {result.recommendation && (
            <div className="callout callout-info" style={{ marginTop: '20px' }}>
              <div className="callout-text markdown-content">
                <ReactMarkdown>{String(result.recommendation || '')}</ReactMarkdown>
              </div>
            </div>
          )}

          {result.simpsons_paradox_risk && (
            <div className="callout callout-warning" style={{ marginTop: '16px' }}>
              <div className="callout-title">Conflicting Results Warning</div>
              <div className="callout-text">
                Your overall result points one way, but individual segments point the other way.
                This usually happens when segment sizes are very different. Don't trust the overall number -
                look at each segment individually to understand what's really happening.
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default SegmentAnalysisPage
