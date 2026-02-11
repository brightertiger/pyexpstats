import { useState } from 'react'
import ReactMarkdown from 'react-markdown'
import FormField from '../components/FormField'

function ImpactProjectionPage() {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [result, setResult] = useState(null)

  const [formData, setFormData] = useState({
    // Test results
    control_visitors: 10000,
    control_conversions: 500,
    variant_visitors: 10000,
    variant_conversions: 575,
    confidence: 95,

    // Business metrics
    average_order_value: 50,
    annual_traffic: 1000000,
    profit_margin: 0.3,
  })

  const handleChange = (e) => {
    const { name, value } = e.target
    setFormData(prev => ({ ...prev, [name]: parseFloat(value) || 0 }))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError(null)
    setResult(null)

    try {
      const res = await fetch('/api/business/impact', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData),
      })

      if (!res.ok) {
        const data = await res.json()
        throw new Error(data.detail || 'Projection failed')
      }

      const data = await res.json()
      setResult(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const controlRate = formData.control_visitors > 0 ? (formData.control_conversions / formData.control_visitors * 100).toFixed(2) : 0
  const variantRate = formData.variant_visitors > 0 ? (formData.variant_conversions / formData.variant_visitors * 100).toFixed(2) : 0
  const liftPercent = controlRate > 0 ? (((variantRate - controlRate) / controlRate) * 100).toFixed(1) : 0

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Impact Projection</h1>
        <p className="page-description">
          Translate your A/B test results into projected business impact and revenue.
        </p>
      </div>

      <div className="info-box">
        <span className="info-box-icon">💰</span>
        <div className="info-box-content">
          <div className="info-box-title">Why project impact?</div>
          <div className="info-box-text">
            A/B test results show statistical significance, but stakeholders need to understand
            the business value. This calculator helps you communicate the expected revenue impact
            and make better decisions about which changes to ship.
          </div>
        </div>
      </div>

      <form onSubmit={handleSubmit}>
        <div className="card">
          <div className="card-title">Test Results</div>
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
                  value={formData.control_visitors}
                  onChange={handleChange}
                  min="1"
                />
              </FormField>
              <div style={{ marginTop: '12px' }}>
                <FormField label="Conversions" hint="Conversions in control">
                  <input
                    type="number"
                    name="control_conversions"
                    className="form-input"
                    value={formData.control_conversions}
                    onChange={handleChange}
                    min="0"
                  />
                </FormField>
              </div>
              <div style={{ marginTop: '12px', padding: '10px 12px', background: 'var(--bg-hover)', borderRadius: 'var(--radius)' }}>
                <span style={{ color: 'var(--text-muted)', fontSize: '12px' }}>Rate: </span>
                <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 500 }}>{controlRate}%</span>
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
                  value={formData.variant_visitors}
                  onChange={handleChange}
                  min="1"
                />
              </FormField>
              <div style={{ marginTop: '12px' }}>
                <FormField label="Conversions" hint="Conversions in variant">
                  <input
                    type="number"
                    name="variant_conversions"
                    className="form-input"
                    value={formData.variant_conversions}
                    onChange={handleChange}
                    min="0"
                  />
                </FormField>
              </div>
              <div style={{ marginTop: '12px', padding: '10px 12px', background: 'var(--bg-hover)', borderRadius: 'var(--radius)' }}>
                <span style={{ color: 'var(--text-muted)', fontSize: '12px' }}>Rate: </span>
                <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 500 }}>{variantRate}%</span>
                <span style={{ marginLeft: '8px', color: liftPercent >= 0 ? 'var(--pastel-green-text)' : 'var(--pastel-red-text)', fontWeight: 500 }}>
                  ({liftPercent >= 0 ? '+' : ''}{liftPercent}%)
                </span>
              </div>
            </div>
          </div>
        </div>

        <div className="card" style={{ marginTop: '16px' }}>
          <div className="card-title">Business Metrics</div>
          <div className="form-grid">
            <FormField label="Average Order Value ($)" hint="Average revenue per conversion">
              <input
                type="number"
                name="average_order_value"
                className="form-input"
                value={formData.average_order_value}
                onChange={handleChange}
                min="0"
                step="0.01"
              />
            </FormField>
            <FormField label="Annual Traffic" hint="Expected visitors per year">
              <input
                type="number"
                name="annual_traffic"
                className="form-input"
                value={formData.annual_traffic}
                onChange={handleChange}
                min="1"
              />
            </FormField>
            <FormField label="Profit Margin" hint="Profit as decimal (0.3 = 30%)">
              <input
                type="number"
                name="profit_margin"
                className="form-input"
                value={formData.profit_margin}
                onChange={handleChange}
                min="0"
                max="1"
                step="0.01"
              />
            </FormField>
            <FormField label="Confidence Level" hint="Statistical confidence">
              <select
                name="confidence"
                className="form-select"
                value={formData.confidence}
                onChange={handleChange}
              >
                <option value={90}>90%</option>
                <option value={95}>95%</option>
                <option value={99}>99%</option>
              </select>
            </FormField>
          </div>
        </div>

        <div style={{ marginTop: '16px' }}>
          <button type="submit" className="btn btn-primary" disabled={loading}>
            {loading ? 'Calculating...' : 'Project Impact'}
          </button>
        </div>
      </form>

      {error && (
        <div className="error-message">{error}</div>
      )}

      {result && (
        <div className="results-card">
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '20px' }}>
            <span className={`tag ${result.is_significant ? 'tag-green' : 'tag-yellow'}`}>
              {result.is_significant ? '✓ High Confidence Result' : '○ Low Confidence - Need More Data'}
            </span>
            <span style={{ fontSize: '24px', fontWeight: 600, fontFamily: 'var(--font-mono)' }}>
              {result.lift_percent >= 0 ? '+' : ''}{result.lift_percent?.toFixed(2)}% improvement
            </span>
          </div>

          <div className="card-title">Projected Annual Impact</div>
          <div className="result-grid" style={{ marginTop: '12px' }}>
            <div className="result-item">
              <div className="result-label">Additional Conversions</div>
              <div className="result-value success">+{result.additional_conversions?.toLocaleString()}</div>
              <div className="result-unit">per year</div>
            </div>
            <div className="result-item">
              <div className="result-label">Additional Revenue</div>
              <div className="result-value success">${result.additional_revenue?.toLocaleString()}</div>
              <div className="result-unit">per year</div>
            </div>
            <div className="result-item">
              <div className="result-label">Additional Profit</div>
              <div className="result-value success">${result.additional_profit?.toLocaleString()}</div>
              <div className="result-unit">per year</div>
            </div>
            <div className="result-item">
              <div className="result-label">ROI Potential</div>
              <div className="result-value">{result.roi_percent?.toFixed(0)}%</div>
              <div className="result-unit">annualized</div>
            </div>
          </div>

          {result.confidence_interval && (
            <div className="stats-explanation" style={{ marginTop: '20px' }}>
              <div className="stats-card">
                <div className="stats-card-label">Expected Revenue Range</div>
                <div className="stats-card-value">
                  ${result.confidence_interval?.revenue_lower?.toLocaleString() ?? 'N/A'} to ${result.confidence_interval?.revenue_upper?.toLocaleString() ?? 'N/A'}
                </div>
                <div className="stats-card-explanation">
                  We're {result.confidence}% confident the real impact falls in this range.
                </div>
              </div>
              <div className="stats-card">
                <div className="stats-card-label">Chance of Positive Impact</div>
                <div className="stats-card-value">{result.probability_positive != null ? (result.probability_positive * 100).toFixed(1) : 'N/A'}%</div>
                <div className="stats-card-explanation">
                  Likelihood that shipping the variant will increase revenue.
                </div>
              </div>
            </div>
          )}

          <div className="callout callout-info" style={{ marginTop: '20px' }}>
            <div className="callout-text">
              <strong>Bottom Line:</strong> Shipping this variant could generate approximately{' '}
              <strong>{result.additional_conversions?.toLocaleString()}</strong> extra conversions per year,
              worth about <strong>${result.additional_revenue?.toLocaleString()}</strong> in revenue
              and <strong>${result.additional_profit?.toLocaleString()}</strong> in profit.
              {!result.is_significant && (
                <span style={{ color: 'var(--pastel-yellow-text)' }}>
                  {' '}Note: We're not highly confident in these numbers yet - consider running the test longer before making a decision.
                </span>
              )}
            </div>
          </div>

          {result.recommendation && (
            <div className={`callout ${result.is_significant ? 'callout-success' : 'callout-warning'}`} style={{ marginTop: '16px' }}>
              <div className="callout-text markdown-content">
                <ReactMarkdown>{String(result.recommendation || '')}</ReactMarkdown>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default ImpactProjectionPage
