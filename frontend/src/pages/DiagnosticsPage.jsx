import { useState } from 'react'
import ReactMarkdown from 'react-markdown'
import FormField from '../components/FormField'

function DiagnosticsPage() {
  const [activeTab, setActiveTab] = useState('health')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [result, setResult] = useState(null)

  // Health check form data
  const [healthData, setHealthData] = useState({
    control_visitors: 5000,
    control_conversions: 250,
    variant_visitors: 5000,
    variant_conversions: 275,
  })

  // SRM form data
  const [srmData, setSrmData] = useState({
    control_visitors: 5000,
    variant_visitors: 5000,
    expected_ratio: 0.5,
  })

  // Novelty form data
  const [noveltyData, setNoveltyData] = useState({
    daily_data: [
      { day: 1, control_visitors: 1000, control_conversions: 50, variant_visitors: 1000, variant_conversions: 55 },
      { day: 2, control_visitors: 1000, control_conversions: 48, variant_visitors: 1000, variant_conversions: 54 },
      { day: 3, control_visitors: 1000, control_conversions: 52, variant_visitors: 1000, variant_conversions: 53 },
      { day: 4, control_visitors: 1000, control_conversions: 50, variant_visitors: 1000, variant_conversions: 52 },
      { day: 5, control_visitors: 1000, control_conversions: 51, variant_visitors: 1000, variant_conversions: 51 },
      { day: 6, control_visitors: 1000, control_conversions: 49, variant_visitors: 1000, variant_conversions: 50 },
      { day: 7, control_visitors: 1000, control_conversions: 50, variant_visitors: 1000, variant_conversions: 50 },
    ]
  })

  const handleHealthChange = (e) => {
    const { name, value } = e.target
    setHealthData(prev => ({ ...prev, [name]: parseFloat(value) || 0 }))
  }

  const handleSrmChange = (e) => {
    const { name, value } = e.target
    setSrmData(prev => ({ ...prev, [name]: parseFloat(value) || 0 }))
  }

  const handleNoveltyDayChange = (index, field, value) => {
    setNoveltyData(prev => ({
      ...prev,
      daily_data: prev.daily_data.map((day, i) =>
        i === index ? { ...day, [field]: parseInt(value) || 0 } : day
      )
    }))
  }

  const addNoveltyDay = () => {
    const newDay = noveltyData.daily_data.length + 1
    setNoveltyData(prev => ({
      ...prev,
      daily_data: [...prev.daily_data, {
        day: newDay,
        control_visitors: 1000,
        control_conversions: 50,
        variant_visitors: 1000,
        variant_conversions: 50
      }]
    }))
  }

  const removeNoveltyDay = (index) => {
    if (noveltyData.daily_data.length > 3) {
      setNoveltyData(prev => ({
        ...prev,
        daily_data: prev.daily_data.filter((_, i) => i !== index).map((d, i) => ({ ...d, day: i + 1 }))
      }))
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError(null)
    setResult(null)

    try {
      let endpoint, payload

      if (activeTab === 'health') {
        endpoint = '/api/diagnostics/health'
        payload = healthData
      } else if (activeTab === 'srm') {
        endpoint = '/api/diagnostics/srm'
        payload = srmData
      } else {
        endpoint = '/api/diagnostics/novelty'
        payload = { daily_results: noveltyData.daily_data }
      }

      const res = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })

      if (!res.ok) {
        const data = await res.json()
        throw new Error(data.detail || 'Analysis failed')
      }

      const data = await res.json()
      setResult({ ...data, type: activeTab })
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const getStatusColor = (status) => {
    if (status === 'healthy' || status === 'ok') return 'tag-green'
    if (status === 'warning') return 'tag-yellow'
    return 'tag-red'
  }

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Experiment Diagnostics</h1>
        <p className="page-description">
          Check for common issues that can invalidate your A/B test results.
        </p>
      </div>

      <div className="info-box">
        <span className="info-box-icon">🔍</span>
        <div className="info-box-content">
          <div className="info-box-title">Why run diagnostics?</div>
          <div className="info-box-text">
            Even statistically significant results can be misleading if your experiment has underlying issues.
            Run these checks to ensure your results are trustworthy before making decisions.
          </div>
        </div>
      </div>

      <div className="tabs">
        <button
          type="button"
          className={`tab ${activeTab === 'health' ? 'active' : ''}`}
          onClick={() => { setActiveTab('health'); setResult(null); setError(null); }}
        >
          Overall Health
        </button>
        <button
          type="button"
          className={`tab ${activeTab === 'srm' ? 'active' : ''}`}
          onClick={() => { setActiveTab('srm'); setResult(null); setError(null); }}
        >
          Traffic Balance
        </button>
        <button
          type="button"
          className={`tab ${activeTab === 'novelty' ? 'active' : ''}`}
          onClick={() => { setActiveTab('novelty'); setResult(null); setError(null); }}
        >
          Effect Over Time
        </button>
      </div>

      <form onSubmit={handleSubmit}>
        {activeTab === 'health' && (
          <>
            <div className="card">
              <div className="card-title">Experiment Data</div>
              <p className="page-description" style={{ marginBottom: '16px' }}>
                Enter your current experiment data to check for potential issues.
              </p>
              <div className="variant-cards-grid">
                <div className="variant-card">
                  <div className="variant-card-header">
                    <span className="variant-badge control">Control</span>
                  </div>
                  <FormField label="Visitors" hint="Total visitors in control">
                    <input
                      type="number"
                      name="control_visitors"
                      className="form-input"
                      value={healthData.control_visitors}
                      onChange={handleHealthChange}
                      min="1"
                    />
                  </FormField>
                  <div style={{ marginTop: '12px' }}>
                    <FormField label="Conversions" hint="Conversions in control">
                      <input
                        type="number"
                        name="control_conversions"
                        className="form-input"
                        value={healthData.control_conversions}
                        onChange={handleHealthChange}
                        min="0"
                      />
                    </FormField>
                  </div>
                </div>
                <div className="variant-card">
                  <div className="variant-card-header">
                    <span className="variant-badge variant">Variant</span>
                  </div>
                  <FormField label="Visitors" hint="Total visitors in variant">
                    <input
                      type="number"
                      name="variant_visitors"
                      className="form-input"
                      value={healthData.variant_visitors}
                      onChange={handleHealthChange}
                      min="1"
                    />
                  </FormField>
                  <div style={{ marginTop: '12px' }}>
                    <FormField label="Conversions" hint="Conversions in variant">
                      <input
                        type="number"
                        name="variant_conversions"
                        className="form-input"
                        value={healthData.variant_conversions}
                        onChange={handleHealthChange}
                        min="0"
                      />
                    </FormField>
                  </div>
                </div>
              </div>
            </div>
          </>
        )}

        {activeTab === 'srm' && (
          <>
            <div className="card">
              <div className="card-title">Is Traffic Split Evenly?</div>
              <p className="page-description" style={{ marginBottom: '16px' }}>
                Check if visitors are being split between control and variant as expected.
                Uneven splits can indicate bugs or issues with your test setup.
              </p>
              <div className="form-grid">
                <FormField label="Control Visitors" hint="How many visitors saw the control?">
                  <input
                    type="number"
                    name="control_visitors"
                    className="form-input"
                    value={srmData.control_visitors}
                    onChange={handleSrmChange}
                    min="1"
                  />
                </FormField>
                <FormField label="Variant Visitors" hint="How many visitors saw the variant?">
                  <input
                    type="number"
                    name="variant_visitors"
                    className="form-input"
                    value={srmData.variant_visitors}
                    onChange={handleSrmChange}
                    min="1"
                  />
                </FormField>
                <FormField label="Expected Split" hint="How should traffic be divided?">
                  <select
                    name="expected_ratio"
                    className="form-select"
                    value={srmData.expected_ratio}
                    onChange={handleSrmChange}
                  >
                    <option value={0.5}>50% / 50% (equal split)</option>
                    <option value={0.33}>33% / 67%</option>
                    <option value={0.25}>25% / 75%</option>
                    <option value={0.2}>20% / 80%</option>
                    <option value={0.1}>10% / 90%</option>
                  </select>
                </FormField>
              </div>
              <div style={{ marginTop: '16px', padding: '12px', background: 'var(--bg-secondary)', borderRadius: 'var(--radius)' }}>
                <span style={{ color: 'var(--text-muted)', fontSize: '12px' }}>Actual split: </span>
                <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 600 }}>
                  {((srmData.control_visitors / (srmData.control_visitors + srmData.variant_visitors)) * 100).toFixed(1)}% /
                  {((srmData.variant_visitors / (srmData.control_visitors + srmData.variant_visitors)) * 100).toFixed(1)}%
                </span>
              </div>
            </div>
          </>
        )}

        {activeTab === 'novelty' && (
          <>
            <div className="card">
              <div className="card-title">Daily Results</div>
              <p className="page-description" style={{ marginBottom: '16px' }}>
                Enter your daily test data to see if results are changing over time.
                Sometimes early results fade away, or effects grow stronger as users adapt.
              </p>
              <div className="novelty-data-table">
                <div className="novelty-header">
                  <span>Day</span>
                  <span>Control Visitors</span>
                  <span>Control Conv.</span>
                  <span>Variant Visitors</span>
                  <span>Variant Conv.</span>
                  <span></span>
                </div>
                {noveltyData.daily_data.map((day, index) => (
                  <div key={index} className="novelty-row">
                    <span className="novelty-day">{day.day}</span>
                    <input
                      type="number"
                      className="form-input"
                      value={day.control_visitors}
                      onChange={(e) => handleNoveltyDayChange(index, 'control_visitors', e.target.value)}
                      min="0"
                    />
                    <input
                      type="number"
                      className="form-input"
                      value={day.control_conversions}
                      onChange={(e) => handleNoveltyDayChange(index, 'control_conversions', e.target.value)}
                      min="0"
                    />
                    <input
                      type="number"
                      className="form-input"
                      value={day.variant_visitors}
                      onChange={(e) => handleNoveltyDayChange(index, 'variant_visitors', e.target.value)}
                      min="0"
                    />
                    <input
                      type="number"
                      className="form-input"
                      value={day.variant_conversions}
                      onChange={(e) => handleNoveltyDayChange(index, 'variant_conversions', e.target.value)}
                      min="0"
                    />
                    <button
                      type="button"
                      className="remove-variant-btn"
                      onClick={() => removeNoveltyDay(index)}
                      disabled={noveltyData.daily_data.length <= 3}
                    >
                      ✕
                    </button>
                  </div>
                ))}
              </div>
              <button type="button" className="add-variant-btn" onClick={addNoveltyDay} style={{ marginTop: '12px' }}>
                <span>+</span> Add Day
              </button>
            </div>
          </>
        )}

        <div style={{ marginTop: '16px' }}>
          <button type="submit" className="btn btn-primary" disabled={loading}>
            {loading ? 'Analyzing...' : 'Run Diagnostics'}
          </button>
        </div>
      </form>

      {error && (
        <div className="error-message">{error}</div>
      )}

      {result && result.type === 'health' && (
        <div className="results-card">
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '20px' }}>
            <span className={`tag ${getStatusColor(result.overall_status)}`}>
              {result.overall_status === 'healthy' ? '✓ Healthy' :
               result.overall_status === 'warning' ? '⚠ Warning' : '✕ Issues Detected'}
            </span>
            <span style={{ fontSize: '20px', fontWeight: 600, fontFamily: 'var(--font-mono)' }}>
              Score: {result.score}/100
            </span>
          </div>

          <div className="card-title">Health Checks</div>
          <div className="health-checks-list">
            {result.checks && result.checks.map((check, i) => (
              <div key={i} className="health-check-item">
                <span className={`health-check-status ${check.status}`}>
                  {check.status === 'pass' ? '✓' : check.status === 'warning' ? '⚠' : '✕'}
                </span>
                <div className="health-check-content">
                  <div className="health-check-name">{check.name}</div>
                  {check.message && <div className="health-check-message">{check.message}</div>}
                </div>
              </div>
            ))}
          </div>

          <div className={`callout ${result.can_trust_results ? 'callout-success' : 'callout-warning'}`} style={{ marginTop: '20px' }}>
            <div className="callout-text">
              {result.can_trust_results
                ? 'Your experiment appears healthy. Results can be trusted assuming no external factors affected the test.'
                : 'There are issues with your experiment. Address the warnings above before drawing conclusions from your results.'}
            </div>
          </div>
        </div>
      )}

      {result && result.type === 'srm' && (
        <div className="results-card">
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '20px' }}>
            <span className={`tag ${result.is_valid ? 'tag-green' : 'tag-red'}`}>
              {result.is_valid ? '✓ Traffic Split Looks Good' : '✕ Uneven Traffic Split'}
            </span>
            {!result.is_valid && (
              <span className={`tag ${getStatusColor(result.severity)}`}>
                {result.severity === 'severe' ? 'Major Issue' : result.severity === 'warning' ? 'Minor Issue' : 'OK'}
              </span>
            )}
          </div>

          <div className="result-grid" style={{ gridTemplateColumns: 'repeat(3, 1fr)' }}>
            <div className="result-item">
              <div className="result-label">Expected Split</div>
              <div className="result-value">{(result.expected_ratio * 100).toFixed(0)}%</div>
            </div>
            <div className="result-item">
              <div className="result-label">Actual Split</div>
              <div className="result-value">{(result.observed_ratio * 100).toFixed(1)}%</div>
            </div>
            <div className="result-item">
              <div className="result-label">Difference</div>
              <div className="result-value" style={{ color: Math.abs(result.deviation_percent) > 1 ? 'var(--pastel-red-text)' : 'var(--pastel-green-text)' }}>
                {result.deviation_percent >= 0 ? '+' : ''}{result.deviation_percent.toFixed(2)}%
              </div>
            </div>
          </div>

          <div className={`callout ${result.is_valid ? 'callout-success' : 'callout-warning'}`} style={{ marginTop: '20px' }}>
            <div className="callout-text">
              {result.is_valid
                ? 'Traffic is being split as expected. Your test setup looks correct.'
                : `Traffic isn't being split evenly (${Math.abs(result.deviation_percent).toFixed(1)}% off from expected). This could mean there's a bug in your test setup, some visitors are being filtered incorrectly, or certain user types aren't being included. We recommend investigating before trusting your results.`}
            </div>
          </div>
        </div>
      )}

      {result && result.type === 'novelty' && (
        <div className="results-card">
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '20px' }}>
            <span className={`tag ${result.effect_detected ? 'tag-yellow' : 'tag-green'}`}>
              {result.effect_type === 'novelty' ? '⚠ Results Are Fading' :
               result.effect_type === 'primacy' ? '📈 Results Are Growing' :
               result.effect_type === 'stable' ? '✓ Results Are Stable' :
               '○ Need More Data'}
            </span>
          </div>

          {result.effect_type !== 'insufficient_data' && (
            <div className="result-grid" style={{ gridTemplateColumns: 'repeat(3, 1fr)' }}>
              <div className="result-item">
                <div className="result-label">Early Results</div>
                <div className="result-value">{result.initial_lift >= 0 ? '+' : ''}{result.initial_lift?.toFixed(1) || 'N/A'}%</div>
                <div className="result-unit">first few days</div>
              </div>
              <div className="result-item">
                <div className="result-label">Recent Results</div>
                <div className="result-value">{result.current_lift >= 0 ? '+' : ''}{result.current_lift?.toFixed(1) || 'N/A'}%</div>
                <div className="result-unit">latest data</div>
              </div>
              <div className="result-item">
                <div className="result-label">Trend</div>
                <div className="result-value" style={{ color: result.effect_type === 'stable' ? 'var(--pastel-green-text)' : 'var(--pastel-yellow-text)' }}>
                  {result.effect_type === 'novelty' ? 'Declining' :
                   result.effect_type === 'primacy' ? 'Increasing' : 'Flat'}
                </div>
              </div>
            </div>
          )}

          <div className={`callout ${result.effect_detected ? 'callout-warning' : 'callout-success'}`} style={{ marginTop: '20px' }}>
            <div className="callout-text">
              {result.effect_type === 'stable' &&
                'Good news! Your results are consistent over time. The improvement you\'re seeing is likely real and will continue after you ship.'}
              {result.effect_type === 'novelty' &&
                'Warning: Your early results were stronger than recent results. This often happens when users are excited by something new, but the excitement fades. The long-term impact may be smaller than your current numbers suggest. Consider running longer to see where results stabilize.'}
              {result.effect_type === 'primacy' &&
                'Interesting: Your results are getting stronger over time. This can happen when users need time to discover or learn a new feature. The long-term impact may be larger than current numbers suggest.'}
              {result.effect_type === 'insufficient_data' &&
                'We need at least 7 days of data to check if results are changing over time. Keep running your test and check back later.'}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default DiagnosticsPage
