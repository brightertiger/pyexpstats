import { useState } from 'react'
import FormField from '../components/FormField'
import { EffectSizeBar, PowerCurveChart } from '../components/charts'

const TEST_TYPES = {
  conversion: {
    id: 'conversion',
    label: 'Conversion Rate',
    description: 'Compare rates (click-through, sign-up, purchase)',
    icon: '🎯',
  },
  magnitude: {
    id: 'magnitude',
    label: 'Continuous Value',
    description: 'Compare averages (revenue, time, score)',
    icon: '📊',
  },
  timing: {
    id: 'timing',
    label: 'Time-to-Event',
    description: 'Compare survival times (time to purchase, churn)',
    icon: '⏱️',
  },
}

const CONFIDENCE_OPTIONS = [
  { value: 90, label: '90%', description: 'Lower bar for significance, faster tests, higher false positive risk (10%)' },
  { value: 95, label: '95%', description: 'Industry standard. Good balance of speed and reliability (5% false positive risk)' },
  { value: 99, label: '99%', description: 'Very strict. Longer tests but highly reliable (1% false positive risk)' },
]

const POWER_OPTIONS = [
  { value: 70, label: '70%', description: '30% chance of missing a real effect. Use when speed matters more than certainty' },
  { value: 80, label: '80%', description: 'Standard choice. 20% chance of missing a real effect' },
  { value: 90, label: '90%', description: 'High sensitivity. Only 10% chance of missing a real effect, but requires more samples' },
]

function SampleSizeCalculator() {
  const [testType, setTestType] = useState('conversion')
  const [formData, setFormData] = useState({
    current_rate: 5,
    lift_percent: 10,
    confidence: 95,
    power: 80,
    daily_visitors: '',
    current_mean: 50,
    current_std: 25,
    num_variants: 2,
    control_median: 30,
    treatment_median: 24,
    dropout_rate: 10,
  })
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [showAdvanced, setShowAdvanced] = useState(false)

  const handleChange = (e) => {
    const { name, value } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: value === '' ? '' : parseFloat(value)
    }))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError(null)
    
    let endpoint, payload

    if (testType === 'conversion') {
      endpoint = '/api/conversion/sample-size'
      payload = {
        current_rate: formData.current_rate,
        lift_percent: formData.lift_percent,
        confidence: formData.confidence,
        power: formData.power,
        daily_visitors: formData.daily_visitors || null,
        num_variants: formData.num_variants,
      }
    } else if (testType === 'magnitude') {
      endpoint = '/api/magnitude/sample-size'
      payload = {
        current_mean: formData.current_mean,
        current_std: formData.current_std,
        lift_percent: formData.lift_percent,
        confidence: formData.confidence,
        power: formData.power,
        daily_visitors: formData.daily_visitors || null,
        num_variants: formData.num_variants,
      }
    } else {
      endpoint = '/api/timing/sample-size'
      payload = {
        control_median: formData.control_median,
        treatment_median: formData.treatment_median,
        confidence: formData.confidence,
        power: formData.power,
        dropout_rate: formData.dropout_rate / 100,
      }
    }
    
    try {
      const res = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })
      
      if (!res.ok) {
        const data = await res.json()
        throw new Error(data.detail || 'Calculation failed')
      }
      
      const data = await res.json()
      setResult({ ...data, type: testType })
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const selectedConfidence = CONFIDENCE_OPTIONS.find(c => c.value === formData.confidence)
  const selectedPower = POWER_OPTIONS.find(p => p.value === formData.power)

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Sample Size Calculator</h1>
        <p className="page-description">
          Calculate how many visitors you need before starting your A/B test to detect a meaningful difference.
        </p>
      </div>

      <div className="info-box">
        <span className="info-box-icon">💡</span>
        <div className="info-box-content">
          <div className="info-box-title">Why calculate sample size first?</div>
          <div className="info-box-text">
            Running a test without enough visitors leads to inconclusive results. Too many visitors wastes time. 
            This calculator tells you exactly how many visitors you need to reliably detect your target improvement.
          </div>
        </div>
      </div>

      <div className="card">
        <div className="card-title">What are you measuring?</div>
        <div className="test-type-options">
          {Object.values(TEST_TYPES).map((type) => (
            <button
              key={type.id}
              type="button"
              className={`test-type-option ${testType === type.id ? 'active' : ''}`}
              onClick={() => { setTestType(type.id); setResult(null); setError(null); }}
            >
              <span className="test-type-icon">{type.icon}</span>
              <div className="test-type-content">
                <div className="test-type-label">{type.label}</div>
                <div className="test-type-description">{type.description}</div>
              </div>
            </button>
          ))}
        </div>
      </div>

      <form onSubmit={handleSubmit}>
        {testType === 'timing' ? (
          <div className="card">
            <div className="card-title">Expected Median Times</div>
            <div className="form-grid">
              <FormField
                label="Control Group Median Time"
                hint="Expected median time-to-event for control group"
                required
              >
                <input
                  type="number"
                  name="control_median"
                  className="form-input"
                  value={formData.control_median}
                  onChange={handleChange}
                  step="any"
                  min="0.01"
                />
              </FormField>
              <FormField
                label="Treatment Group Median Time"
                hint="Expected median time-to-event for treatment group"
                required
              >
                <input
                  type="number"
                  name="treatment_median"
                  className="form-input"
                  value={formData.treatment_median}
                  onChange={handleChange}
                  step="any"
                  min="0.01"
                />
              </FormField>
              <FormField
                label="Expected Dropout Rate (%)"
                hint="Percentage of subjects expected to drop out before the event"
              >
                <input
                  type="number"
                  name="dropout_rate"
                  className="form-input"
                  value={formData.dropout_rate}
                  onChange={handleChange}
                  step="1"
                  min="0"
                  max="90"
                />
              </FormField>
            </div>
            <div style={{ marginTop: '16px', padding: '12px', background: 'var(--bg-secondary)', borderRadius: 'var(--radius)' }}>
              <span style={{ color: 'var(--text-muted)', fontSize: '12px' }}>Expected hazard ratio: </span>
              <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 600 }}>
                {(formData.control_median / formData.treatment_median).toFixed(3)}
              </span>
              <span style={{ color: 'var(--text-muted)', fontSize: '12px', marginLeft: '8px' }}>
                ({formData.treatment_median < formData.control_median ? 'faster in treatment' : 'slower in treatment'})
              </span>
            </div>
          </div>
        ) : (
          <div className="card">
            <div className="card-title">Current Performance</div>
            <div className="form-grid">
              {testType === 'conversion' ? (
                <FormField 
                  label="Current Conversion Rate (%)" 
                  hint="Your baseline conversion rate before any changes"
                  required
                >
                  <input
                    type="number"
                    name="current_rate"
                    className="form-input"
                    value={formData.current_rate}
                    onChange={handleChange}
                    step="any"
                    min="0.01"
                    max="99"
                    placeholder="e.g., 5 for 5%"
                  />
                </FormField>
              ) : (
                <>
                  <FormField 
                    label="Current Average Value" 
                    hint="Average value per visitor (e.g., average order value)"
                    required
                  >
                    <input
                      type="number"
                      name="current_mean"
                      className="form-input"
                      value={formData.current_mean}
                      onChange={handleChange}
                      step="any"
                      placeholder="e.g., 50"
                    />
                  </FormField>
                  <FormField 
                    label="Standard Deviation" 
                    hint="How spread out your values are. If unsure, use 50-100% of the mean"
                    required
                  >
                    <input
                      type="number"
                      name="current_std"
                      className="form-input"
                      value={formData.current_std}
                      onChange={handleChange}
                      step="any"
                      min="0.01"
                      placeholder="e.g., 25"
                    />
                  </FormField>
                </>
              )}

              <FormField 
                label="Minimum Lift to Detect (%)" 
                hint="The smallest improvement worth detecting. Smaller lifts need more visitors"
                required
              >
                <input
                  type="number"
                  name="lift_percent"
                  className="form-input"
                  value={formData.lift_percent}
                  onChange={handleChange}
                  step="1"
                  min="1"
                  placeholder="e.g., 10 for 10% improvement"
                />
              </FormField>

              <FormField 
                label="Daily Visitors (optional)" 
                hint="Enter to calculate test duration"
              >
                <input
                  type="number"
                  name="daily_visitors"
                  className="form-input"
                  value={formData.daily_visitors}
                  onChange={handleChange}
                  step="100"
                  min="1"
                  placeholder="e.g., 10000"
                />
              </FormField>
            </div>
          </div>
        )}

        <div className="card">
          <div className="card-title">Statistical Settings</div>
          
          <FormField 
            label="Confidence Level" 
            hint={selectedConfidence?.description}
          >
            <select
              name="confidence"
              className="form-select"
              value={formData.confidence}
              onChange={handleChange}
            >
              {CONFIDENCE_OPTIONS.map(opt => (
                <option key={opt.value} value={opt.value}>{opt.label}</option>
              ))}
            </select>
          </FormField>

          <div style={{ marginTop: '16px' }}>
            <FormField 
              label="Statistical Power" 
              hint={selectedPower?.description}
            >
              <select
                name="power"
                className="form-select"
                value={formData.power}
                onChange={handleChange}
              >
                {POWER_OPTIONS.map(opt => (
                  <option key={opt.value} value={opt.value}>{opt.label}</option>
                ))}
              </select>
            </FormField>
          </div>

          {testType !== 'timing' && (
            <>
              <div className="section-divider">
                <div className="section-divider-line"></div>
                <button 
                  type="button" 
                  className="section-divider-text"
                  onClick={() => setShowAdvanced(!showAdvanced)}
                  style={{ background: 'none', border: 'none', cursor: 'pointer' }}
                >
                  {showAdvanced ? '▼ Hide Advanced' : '▶ Show Advanced'}
                </button>
                <div className="section-divider-line"></div>
              </div>

              {showAdvanced && (
                <FormField 
                  label="Number of Variants" 
                  hint="Including control. More variants = more visitors needed per variant"
                >
                  <select
                    name="num_variants"
                    className="form-select"
                    value={formData.num_variants}
                    onChange={handleChange}
                    style={{ maxWidth: '200px' }}
                  >
                    <option value={2}>2 (A/B test)</option>
                    <option value={3}>3 (A/B/C test)</option>
                    <option value={4}>4 variants</option>
                    <option value={5}>5 variants</option>
                  </select>
                </FormField>
              )}
            </>
          )}

          <div style={{ marginTop: '24px' }}>
            <button type="submit" className="btn btn-primary" disabled={loading}>
              {loading ? 'Calculating...' : 'Calculate Sample Size'}
            </button>
          </div>
        </div>
      </form>

      {error && (
        <div className="error-message">{error}</div>
      )}

      {result && result.type === 'timing' && (
        <div className="results-card">
          <div className="result-grid">
            <div className="result-item">
              <div className="result-label">Per Group</div>
              <div className="result-value">{result.subjects_per_group.toLocaleString()}</div>
              <div className="result-unit">subjects</div>
            </div>
            <div className="result-item">
              <div className="result-label">Total</div>
              <div className="result-value">{result.total_subjects.toLocaleString()}</div>
              <div className="result-unit">subjects</div>
            </div>
            <div className="result-item">
              <div className="result-label">Events Needed</div>
              <div className="result-value">{result.total_expected_events.toLocaleString()}</div>
              <div className="result-unit">total events</div>
            </div>
            <div className="result-item">
              <div className="result-label">Hazard Ratio</div>
              <div className="result-value">{result.hazard_ratio.toFixed(3)}</div>
            </div>
          </div>

          <div className="stats-explanation">
            <div className="stats-card">
              <div className="stats-card-label">Control Median</div>
              <div className="stats-card-value">{result.control_median} units</div>
              <div className="stats-card-explanation">
                Expected time for 50% of control subjects to experience the event.
              </div>
            </div>
            <div className="stats-card">
              <div className="stats-card-label">Treatment Median</div>
              <div className="stats-card-value">{result.treatment_median} units</div>
              <div className="stats-card-explanation">
                Expected time for 50% of treatment subjects to experience the event.
              </div>
            </div>
          </div>

          <div className="callout callout-info" style={{ marginTop: '16px' }}>
            <div className="callout-text">
              <strong>Interpretation:</strong> You need {result.subjects_per_group.toLocaleString()} subjects per group 
              ({result.total_subjects.toLocaleString()} total) and approximately {result.total_expected_events.toLocaleString()} events 
              to detect a hazard ratio of {result.hazard_ratio.toFixed(2)} with {result.power}% power at {result.confidence}% confidence.
            </div>
          </div>
        </div>
      )}

      {result && result.type !== 'timing' && (
        <div className="results-card">
          <div className="result-grid">
            <div className="result-item">
              <div className="result-label">Per Variant</div>
              <div className="result-value">{result.visitors_per_variant.toLocaleString()}</div>
              <div className="result-unit">visitors</div>
            </div>
            <div className="result-item">
              <div className="result-label">Total</div>
              <div className="result-value">{result.total_visitors.toLocaleString()}</div>
              <div className="result-unit">visitors</div>
            </div>
            {result.test_duration_days && (
              <div className="result-item">
                <div className="result-label">Duration</div>
                <div className="result-value">{result.test_duration_days}</div>
                <div className="result-unit">days</div>
              </div>
            )}
            <div className="result-item">
              <div className="result-label">Expected {result.type === 'conversion' ? 'Rate' : 'Value'}</div>
              <div className="result-value">
                {result.type === 'conversion' 
                  ? `${(result.expected_rate * 100).toFixed(2)}%`
                  : `$${result.expected_mean?.toFixed(2)}`
                }
              </div>
            </div>
          </div>

          <EffectSizeBar
            baseline={result.type === 'conversion' ? result.current_rate * 100 : result.current_mean}
            mde={result.lift_percent}
            expectedValue={result.type === 'conversion' ? result.expected_rate * 100 : result.expected_mean}
            label={result.type === 'conversion' ? 'Conversion Rate' : 'Average Value'}
            formatValue={(v) => result.type === 'conversion' ? `${v.toFixed(2)}%` : `$${v.toFixed(2)}`}
          />

          <PowerCurveChart
            requiredN={result.visitors_per_variant}
            power={result.power}
            confidence={result.confidence}
          />

          <div className="stats-explanation">
            <div className="stats-card">
              <div className="stats-card-label">What you're testing</div>
              <div className="stats-card-value">
                {result.type === 'conversion' 
                  ? `${(result.current_rate * 100).toFixed(1)}% → ${(result.expected_rate * 100).toFixed(1)}%`
                  : `$${result.current_mean?.toFixed(0)} → $${result.expected_mean?.toFixed(0)}`
                }
              </div>
              <div className="stats-card-explanation">
                You want to detect if your variant achieves at least a {result.lift_percent}% improvement 
                over current performance.
              </div>
            </div>
            <div className="stats-card">
              <div className="stats-card-label">Reliability</div>
              <div className="stats-card-value">{result.power}% power</div>
              <div className="stats-card-explanation">
                If the variant truly improves by {result.lift_percent}% or more, this test has a {result.power}% 
                chance of detecting it.
              </div>
            </div>
          </div>

          <div className="callout callout-info" style={{ marginTop: '16px' }}>
            <div className="callout-text">
              <strong>How to interpret:</strong> Run your test until you have {result.visitors_per_variant.toLocaleString()} visitors 
              in each variant ({result.total_visitors.toLocaleString()} total). 
              {result.test_duration_days && ` At your traffic level, this takes about ${result.test_duration_days} days.`}
              {' '}Stopping early increases the risk of false conclusions.
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default SampleSizeCalculator
