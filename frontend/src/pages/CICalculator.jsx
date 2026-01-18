import { useState } from 'react'
import TestTypeSelector from '../components/TestTypeSelector'
import FormField from '../components/FormField'

function CICalculator() {
  const [testType, setTestType] = useState('conversion')
  const [formData, setFormData] = useState({
    visitors: 1000,
    conversions: 50,
    confidence: 95,
    mean: 50,
    std: 25,
  })
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const handleChange = (e) => {
    const { name, value } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: parseFloat(value)
    }))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError(null)
    
    const endpoint = testType === 'conversion' 
      ? '/api/conversion/confidence-interval'
      : '/api/magnitude/confidence-interval'
    
    const payload = testType === 'conversion'
      ? {
          visitors: formData.visitors,
          conversions: formData.conversions,
          confidence: formData.confidence,
        }
      : {
          visitors: formData.visitors,
          mean: formData.mean,
          std: formData.std,
          confidence: formData.confidence,
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
      setResult(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const currentRate = formData.conversions / formData.visitors

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Metric Range Calculator</h1>
        <p className="page-description">
          Find out the likely range for your true metric value based on the data you've collected.
        </p>
      </div>

      <div className="info-box">
        <span className="info-box-icon">📏</span>
        <div className="info-box-content">
          <div className="info-box-title">Why calculate a range?</div>
          <div className="info-box-text">
            Your observed metric (like a 5% conversion rate) is based on a sample of users.
            The true rate might be slightly higher or lower. This calculator tells you the likely range -
            for example, "we're 95% confident the real rate is between 4.5% and 5.5%."
          </div>
        </div>
      </div>

      <div className="card">
        <div className="card-title">What are you measuring?</div>
        <TestTypeSelector value={testType} onChange={setTestType} />
      </div>

      <form onSubmit={handleSubmit}>
        <div className="card">
          <div className="card-title">Your Data</div>
          <div className="form-grid">
            {testType === 'conversion' ? (
              <>
                <FormField 
                  label="Total Visitors" 
                  hint="The total number of users in your sample"
                  required
                >
                  <input
                    type="number"
                    name="visitors"
                    className="form-input"
                    value={formData.visitors}
                    onChange={handleChange}
                    min="1"
                  />
                </FormField>
                <FormField 
                  label="Conversions" 
                  hint="Number of users who took the desired action"
                  required
                >
                  <input
                    type="number"
                    name="conversions"
                    className="form-input"
                    value={formData.conversions}
                    onChange={handleChange}
                    min="0"
                  />
                </FormField>
              </>
            ) : (
              <>
                <FormField 
                  label="Sample Size" 
                  hint="Number of observations in your data"
                  required
                >
                  <input
                    type="number"
                    name="visitors"
                    className="form-input"
                    value={formData.visitors}
                    onChange={handleChange}
                    min="2"
                  />
                </FormField>
                <FormField 
                  label="Mean" 
                  hint="Average value in your sample"
                  required
                >
                  <input
                    type="number"
                    name="mean"
                    className="form-input"
                    value={formData.mean}
                    onChange={handleChange}
                    step="any"
                  />
                </FormField>
                <FormField 
                  label="Standard Deviation" 
                  hint="How spread out your values are"
                  required
                >
                  <input
                    type="number"
                    name="std"
                    className="form-input"
                    value={formData.std}
                    onChange={handleChange}
                    step="any"
                    min="0"
                  />
                </FormField>
              </>
            )}

            <FormField
              label="How confident do you want to be?"
              hint="Higher confidence = wider range but more reliable"
            >
              <select
                name="confidence"
                className="form-select"
                value={formData.confidence}
                onChange={handleChange}
              >
                <option value={90}>90% - Narrower range, good for quick estimates</option>
                <option value={95}>95% - Recommended - good balance</option>
                <option value={99}>99% - Widest range, highest reliability</option>
              </select>
            </FormField>
          </div>

          {testType === 'conversion' && formData.visitors > 0 && (
            <div style={{ marginTop: '16px', padding: '12px 14px', background: 'var(--bg-secondary)', borderRadius: 'var(--radius-lg)', display: 'inline-block' }}>
              <span style={{ color: 'var(--text-muted)', fontSize: '12px' }}>Observed conversion rate: </span>
              <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 600, fontSize: '16px' }}>{(currentRate * 100).toFixed(2)}%</span>
            </div>
          )}

          <div style={{ marginTop: '24px' }}>
            <button type="submit" className="btn btn-primary" disabled={loading}>
              {loading ? 'Calculating...' : 'Calculate Confidence Interval'}
            </button>
          </div>
        </div>
      </form>

      {error && (
        <div className="error-message">{error}</div>
      )}

      {result && (
        <div className="results-card">
          <div style={{ textAlign: 'center', marginBottom: '24px' }}>
            <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: '8px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Your Likely Range ({result.confidence}% confident)
            </div>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '16px' }}>
              <span style={{ fontSize: '28px', fontFamily: 'var(--font-mono)', fontWeight: 600 }}>
                {testType === 'conversion' 
                  ? `${(result.lower * 100).toFixed(2)}%`
                  : `$${result.lower.toFixed(2)}`
                }
              </span>
              <span style={{ color: 'var(--text-muted)', fontSize: '18px' }}>to</span>
              <span style={{ fontSize: '28px', fontFamily: 'var(--font-mono)', fontWeight: 600 }}>
                {testType === 'conversion' 
                  ? `${(result.upper * 100).toFixed(2)}%`
                  : `$${result.upper.toFixed(2)}`
                }
              </span>
            </div>
          </div>

          <div className="ci-bar">
            {(() => {
              const range = testType === 'conversion' ? 1 : Math.max(result.upper * 1.5, result.mean * 2)
              const lowerPos = Math.max(0, (result.lower / range) * 100)
              const upperPos = Math.min(100, (result.upper / range) * 100)
              const pointPos = ((testType === 'conversion' ? result.rate : result.mean) / range) * 100
              
              return (
                <>
                  <div className="ci-bar-fill" style={{ left: `${lowerPos}%`, width: `${upperPos - lowerPos}%` }} />
                  <div className="ci-bar-point" style={{ left: `${pointPos}%` }} />
                </>
              )
            })()}
          </div>

          <div className="stats-explanation">
            <div className="stats-card">
              <div className="stats-card-label">Your Measured Value</div>
              <div className="stats-card-value">
                {testType === 'conversion'
                  ? `${(result.rate * 100).toFixed(2)}%`
                  : `$${result.mean.toFixed(2)}`
                }
              </div>
              <div className="stats-card-explanation">
                What you observed in your data. This is your best estimate, but may not be exact.
              </div>
            </div>
            <div className="stats-card">
              <div className="stats-card-label">Possible Variation</div>
              <div className="stats-card-value">
                ±{testType === 'conversion'
                  ? `${(result.margin_of_error * 100).toFixed(2)}%`
                  : `$${result.margin_of_error.toFixed(2)}`
                }
              </div>
              <div className="stats-card-explanation">
                How much the real value could differ from what you measured. More data = smaller variation.
              </div>
            </div>
          </div>

          <div className="callout callout-info" style={{ marginTop: '20px' }}>
            <div className="callout-text">
              <strong>What this means:</strong> Based on {formData.visitors.toLocaleString()} {testType === 'conversion' ? 'visitors' : 'observations'},
              we're {result.confidence}% confident the real {testType === 'conversion' ? 'conversion rate' : 'average'} is between{' '}
              <strong>
                {testType === 'conversion'
                  ? `${(result.lower * 100).toFixed(2)}%`
                  : `$${result.lower.toFixed(2)}`
                }
              </strong> and{' '}
              <strong>
                {testType === 'conversion'
                  ? `${(result.upper * 100).toFixed(2)}%`
                  : `$${result.upper.toFixed(2)}`
                }
              </strong>.
            </div>
          </div>

          <div style={{ marginTop: '20px', padding: '14px 16px', background: 'var(--bg-secondary)', borderRadius: 'var(--radius-lg)' }}>
            <div style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '8px' }}>
              Want a narrower range?
            </div>
            <div style={{ fontSize: '13px', color: 'var(--text-secondary)', lineHeight: '1.5' }}>
              • <strong>Collect more data</strong> — The best way to get more precise estimates<br/>
              • <strong>Accept less certainty</strong> — Use 90% instead of 95% for a tighter range<br/>
              • Note: Conversion rates near 50% naturally have wider ranges than rates near 0% or 100%
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default CICalculator
