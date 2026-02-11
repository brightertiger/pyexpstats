import { useState } from 'react'
import ReactMarkdown from 'react-markdown'
import TestTypeSelector from '../components/TestTypeSelector'
import FormField from '../components/FormField'
import { CIComparisonChart, DistributionChart } from '../components/charts'

function SignificanceCalculator() {
  const [testType, setTestType] = useState('conversion')
  const [analysisMode, setAnalysisMode] = useState('ab')
  const [analysisMethod, setAnalysisMethod] = useState('frequentist')
  const [formData, setFormData] = useState({
    control_visitors: 10000,
    control_conversions: 500,
    variant_visitors: 10000,
    variant_conversions: 550,
    confidence: 95,
    control_mean: 50,
    control_std: 25,
    variant_mean: 52.5,
    variant_std: 25,
    // Sequential settings
    max_visitors: 50000,
    spending_function: 'obrien_fleming',
    // Bayesian settings
    prior_alpha: 1,
    prior_beta: 1,
  })
  const [variants, setVariants] = useState([
    { name: 'Control', visitors: 10000, conversions: 500, mean: 50, std: 25 },
    { name: 'Variant A', visitors: 10000, conversions: 550, mean: 52.5, std: 25 },
    { name: 'Variant B', visitors: 10000, conversions: 480, mean: 49, std: 24 },
  ])
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const handleChange = (e) => {
    const { name, value, type } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: type === 'number' ? parseFloat(value) : value
    }))
  }

  const handleVariantChange = (index, field, value) => {
    setVariants(prev => prev.map((v, i) =>
      i === index ? { ...v, [field]: field === 'name' ? value : parseFloat(value) || 0 } : v
    ))
  }

  const addVariant = () => {
    const letter = String.fromCharCode(65 + variants.length - 1)
    setVariants(prev => [...prev, {
      name: `Variant ${letter}`,
      visitors: 10000,
      conversions: 500,
      mean: 50,
      std: 25
    }])
  }

  const removeVariant = (index) => {
    if (variants.length > 2) {
      setVariants(prev => prev.filter((_, i) => i !== index))
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError(null)
    setResult(null)

    let endpoint, payload

    if (analysisMethod === 'frequentist') {
      if (analysisMode === 'ab') {
        endpoint = testType === 'conversion'
          ? '/api/conversion/analyze'
          : '/api/magnitude/analyze'

        payload = testType === 'conversion'
          ? {
              control_visitors: formData.control_visitors,
              control_conversions: formData.control_conversions,
              variant_visitors: formData.variant_visitors,
              variant_conversions: formData.variant_conversions,
              confidence: formData.confidence,
            }
          : {
              control_visitors: formData.control_visitors,
              control_mean: formData.control_mean,
              control_std: formData.control_std,
              variant_visitors: formData.variant_visitors,
              variant_mean: formData.variant_mean,
              variant_std: formData.variant_std,
              confidence: formData.confidence,
            }
      } else {
        endpoint = testType === 'conversion'
          ? '/api/conversion/analyze-multi'
          : '/api/magnitude/analyze-multi'

        payload = testType === 'conversion'
          ? {
              variants: variants.map(v => ({
                name: v.name,
                visitors: v.visitors,
                conversions: v.conversions,
              })),
              confidence: formData.confidence,
              correction: 'bonferroni',
            }
          : {
              variants: variants.map(v => ({
                name: v.name,
                visitors: v.visitors,
                mean: v.mean,
                std: v.std,
              })),
              confidence: formData.confidence,
              correction: 'bonferroni',
            }
      }
    } else if (analysisMethod === 'bayesian') {
      endpoint = '/api/bayesian/analyze'
      payload = {
        control_visitors: formData.control_visitors,
        control_conversions: formData.control_conversions,
        variant_visitors: formData.variant_visitors,
        variant_conversions: formData.variant_conversions,
        prior_alpha: formData.prior_alpha,
        prior_beta: formData.prior_beta,
      }
    } else if (analysisMethod === 'sequential') {
      endpoint = '/api/sequential/analyze'
      payload = {
        control_visitors: formData.control_visitors,
        control_conversions: formData.control_conversions,
        variant_visitors: formData.variant_visitors,
        variant_conversions: formData.variant_conversions,
        expected_visitors_per_variant: formData.max_visitors,
        alpha: (100 - formData.confidence) / 100,
        method: formData.spending_function === 'obrien_fleming' ? 'obrien-fleming' : 'pocock',
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
        throw new Error(data.detail || 'Analysis failed')
      }

      const data = await res.json()
      setResult({ ...data, mode: analysisMode, method: analysisMethod })
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const controlRate = formData.control_conversions / formData.control_visitors
  const variantRate = formData.variant_conversions / formData.variant_visitors

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Analyze Results</h1>
        <p className="page-description">
          Check if your A/B test has a statistically significant winner.
        </p>
      </div>

      <div className="info-box">
        <span className="info-box-icon">📊</span>
        <div className="info-box-content">
          <div className="info-box-title">What is statistical significance?</div>
          <div className="info-box-text">
            Statistical significance tells you whether the difference you observe is real or just due to random chance.
            A "significant" result means you can confidently say the variant performs differently from the control.
          </div>
        </div>
      </div>

      <div className="card">
        <div className="card-title">How do you want to analyze?</div>
        <div className="method-selector">
          <button
            type="button"
            className={`method-option ${analysisMethod === 'frequentist' ? 'active' : ''}`}
            onClick={() => { setAnalysisMethod('frequentist'); setResult(null); setError(null); }}
          >
            <span className="method-icon">📈</span>
            <div className="method-content">
              <div className="method-label">Classic</div>
              <div className="method-desc">Is there a real difference?</div>
            </div>
          </button>
          <button
            type="button"
            className={`method-option ${analysisMethod === 'bayesian' ? 'active' : ''}`}
            onClick={() => { setAnalysisMethod('bayesian'); setAnalysisMode('ab'); setResult(null); setError(null); }}
          >
            <span className="method-icon">🎲</span>
            <div className="method-content">
              <div className="method-label">Chance to Win</div>
              <div className="method-desc">What's the probability variant wins?</div>
            </div>
          </button>
          <button
            type="button"
            className={`method-option ${analysisMethod === 'sequential' ? 'active' : ''}`}
            onClick={() => { setAnalysisMethod('sequential'); setAnalysisMode('ab'); setResult(null); setError(null); }}
          >
            <span className="method-icon">⏱️</span>
            <div className="method-content">
              <div className="method-label">Early Stopping</div>
              <div className="method-desc">Can I stop the test now?</div>
            </div>
          </button>
        </div>
      </div>

      {analysisMethod === 'frequentist' && (
        <div className="card">
          <div className="card-title">What are you measuring?</div>
          <TestTypeSelector value={testType} onChange={(val) => { setTestType(val); setResult(null); setError(null); }} />
        </div>
      )}

      {analysisMethod === 'frequentist' && (
        <div className="card">
          <div className="card-title">Analysis Type</div>
          <div className="tabs">
            <button
              type="button"
              className={`tab ${analysisMode === 'ab' ? 'active' : ''}`}
              onClick={() => { setAnalysisMode('ab'); setResult(null); }}
            >
              A/B Test (2 variants)
            </button>
            <button
              type="button"
              className={`tab ${analysisMode === 'multi' ? 'active' : ''}`}
              onClick={() => { setAnalysisMode('multi'); setResult(null); }}
            >
              Multi-Variant (3+ variants)
            </button>
          </div>
          <div className="form-hint" style={{ marginTop: '-8px' }}>
            {analysisMode === 'ab'
              ? 'Compare one variant against a control group'
              : 'Compare multiple variants at once with automatic correction for multiple comparisons'
            }
          </div>
        </div>
      )}

      <form onSubmit={handleSubmit}>
        {/* Frequentist A/B form */}
        {analysisMethod === 'frequentist' && analysisMode === 'ab' && (
          testType === 'conversion' ? (
            <div className="variant-cards-grid">
              <div className="variant-card">
                <div className="variant-card-header">
                  <span className="variant-badge control">Control</span>
                </div>
                <FormField label="Visitors" hint="Number of users who saw the control">
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
                  <FormField label="Conversions" hint="Number of users who converted">
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
                  <span style={{ color: 'var(--text-muted)', fontSize: '12px' }}>Conversion Rate: </span>
                  <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 500 }}>{(controlRate * 100).toFixed(2)}%</span>
                </div>
              </div>

              <div className="variant-card">
                <div className="variant-card-header">
                  <span className="variant-badge variant">Variant</span>
                </div>
                <FormField label="Visitors" hint="Number of users who saw the variant">
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
                  <FormField label="Conversions" hint="Number of users who converted">
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
                  <span style={{ color: 'var(--text-muted)', fontSize: '12px' }}>Conversion Rate: </span>
                  <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 500 }}>{(variantRate * 100).toFixed(2)}%</span>
                </div>
              </div>
            </div>
          ) : (
            <div className="variant-cards-grid">
              <div className="variant-card">
                <div className="variant-card-header">
                  <span className="variant-badge control">Control</span>
                </div>
                <FormField label="Sample Size" hint="Number of observations">
                  <input
                    type="number"
                    name="control_visitors"
                    className="form-input"
                    value={formData.control_visitors}
                    onChange={handleChange}
                    min="2"
                  />
                </FormField>
                <div style={{ marginTop: '12px' }}>
                  <FormField label="Mean" hint="Average value (e.g., avg order value)">
                    <input
                      type="number"
                      name="control_mean"
                      className="form-input"
                      value={formData.control_mean}
                      onChange={handleChange}
                      step="any"
                    />
                  </FormField>
                </div>
                <div style={{ marginTop: '12px' }}>
                  <FormField label="Standard Deviation" hint="Spread of the data">
                    <input
                      type="number"
                      name="control_std"
                      className="form-input"
                      value={formData.control_std}
                      onChange={handleChange}
                      step="any"
                      min="0"
                    />
                  </FormField>
                </div>
              </div>

              <div className="variant-card">
                <div className="variant-card-header">
                  <span className="variant-badge variant">Variant</span>
                </div>
                <FormField label="Sample Size" hint="Number of observations">
                  <input
                    type="number"
                    name="variant_visitors"
                    className="form-input"
                    value={formData.variant_visitors}
                    onChange={handleChange}
                    min="2"
                  />
                </FormField>
                <div style={{ marginTop: '12px' }}>
                  <FormField label="Mean" hint="Average value (e.g., avg order value)">
                    <input
                      type="number"
                      name="variant_mean"
                      className="form-input"
                      value={formData.variant_mean}
                      onChange={handleChange}
                      step="any"
                    />
                  </FormField>
                </div>
                <div style={{ marginTop: '12px' }}>
                  <FormField label="Standard Deviation" hint="Spread of the data">
                    <input
                      type="number"
                      name="variant_std"
                      className="form-input"
                      value={formData.variant_std}
                      onChange={handleChange}
                      step="any"
                      min="0"
                    />
                  </FormField>
                </div>
              </div>
            </div>
          )
        )}

        {/* Frequentist Multi-variant form */}
        {analysisMethod === 'frequentist' && analysisMode === 'multi' && (
          <div className="card">
            <div className="card-title">Variant Data</div>
            <div className="variant-list">
              {variants.map((variant, index) => (
                <div key={index} className="variant-row">
                  <FormField label={index === 0 ? 'Name' : ''}>
                    <input
                      type="text"
                      className="form-input variant-name-input"
                      value={variant.name}
                      onChange={(e) => handleVariantChange(index, 'name', e.target.value)}
                      placeholder="Variant name"
                    />
                  </FormField>
                  <FormField label={index === 0 ? 'Visitors' : ''}>
                    <input
                      type="number"
                      className="form-input"
                      value={variant.visitors}
                      onChange={(e) => handleVariantChange(index, 'visitors', e.target.value)}
                      min="1"
                    />
                  </FormField>
                  {testType === 'conversion' ? (
                    <FormField label={index === 0 ? 'Conversions' : ''}>
                      <input
                        type="number"
                        className="form-input"
                        value={variant.conversions}
                        onChange={(e) => handleVariantChange(index, 'conversions', e.target.value)}
                        min="0"
                      />
                    </FormField>
                  ) : (
                    <>
                      <FormField label={index === 0 ? 'Mean' : ''}>
                        <input
                          type="number"
                          className="form-input"
                          value={variant.mean}
                          onChange={(e) => handleVariantChange(index, 'mean', e.target.value)}
                          step="any"
                        />
                      </FormField>
                      <FormField label={index === 0 ? 'Std Dev' : ''}>
                        <input
                          type="number"
                          className="form-input"
                          value={variant.std}
                          onChange={(e) => handleVariantChange(index, 'std', e.target.value)}
                          step="any"
                          min="0"
                        />
                      </FormField>
                    </>
                  )}
                  <div style={{ paddingBottom: index === 0 ? '0' : '0' }}>
                    <button
                      type="button"
                      className="remove-variant-btn"
                      onClick={() => removeVariant(index)}
                      disabled={variants.length <= 2}
                      title={variants.length <= 2 ? 'Minimum 2 variants required' : 'Remove variant'}
                    >
                      ✕
                    </button>
                  </div>
                </div>
              ))}
            </div>
            <button type="button" className="add-variant-btn" onClick={addVariant}>
              <span>+</span> Add Variant
            </button>
          </div>
        )}

        {/* Bayesian form */}
        {analysisMethod === 'bayesian' && (
          <>
            <div className="variant-cards-grid">
              <div className="variant-card">
                <div className="variant-card-header">
                  <span className="variant-badge control">Control</span>
                </div>
                <FormField label="Visitors" hint="Number of users who saw the control">
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
                  <FormField label="Conversions" hint="Number of users who converted">
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
                  <span style={{ color: 'var(--text-muted)', fontSize: '12px' }}>Conversion Rate: </span>
                  <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 500 }}>{(controlRate * 100).toFixed(2)}%</span>
                </div>
              </div>

              <div className="variant-card">
                <div className="variant-card-header">
                  <span className="variant-badge variant">Variant</span>
                </div>
                <FormField label="Visitors" hint="Number of users who saw the variant">
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
                  <FormField label="Conversions" hint="Number of users who converted">
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
                  <span style={{ color: 'var(--text-muted)', fontSize: '12px' }}>Conversion Rate: </span>
                  <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 500 }}>{(variantRate * 100).toFixed(2)}%</span>
                </div>
              </div>
            </div>

            <div className="card" style={{ marginTop: '16px' }}>
              <div className="card-title">Prior Belief (Optional)</div>
              <div className="form-hint" style={{ marginBottom: '12px' }}>
                Do you have existing data about your conversion rate? Leave as "No prior belief" if this is a new test.
              </div>
              <div className="form-grid">
                <FormField label="Prior Strength" hint="How confident are you in your prior belief?">
                  <select
                    className="form-select"
                    value={formData.prior_alpha === 1 && formData.prior_beta === 1 ? 'none' :
                           formData.prior_alpha === 10 ? 'weak' :
                           formData.prior_alpha === 50 ? 'moderate' : 'strong'}
                    onChange={(e) => {
                      const presets = {
                        none: { alpha: 1, beta: 1 },
                        weak: { alpha: 10, beta: 190 },      // ~5% rate, weak belief
                        moderate: { alpha: 50, beta: 950 },  // ~5% rate, moderate belief
                        strong: { alpha: 100, beta: 1900 },  // ~5% rate, strong belief
                      }
                      const preset = presets[e.target.value]
                      handleChange({ target: { name: 'prior_alpha', value: preset.alpha, type: 'number' } })
                      handleChange({ target: { name: 'prior_beta', value: preset.beta, type: 'number' } })
                    }}
                  >
                    <option value="none">No prior belief (recommended for new tests)</option>
                    <option value="weak">Weak belief (~100 past visitors worth)</option>
                    <option value="moderate">Moderate belief (~1,000 past visitors worth)</option>
                    <option value="strong">Strong belief (~2,000 past visitors worth)</option>
                  </select>
                </FormField>
              </div>
            </div>
          </>
        )}

        {/* Sequential form */}
        {analysisMethod === 'sequential' && (
          <>
            <div className="variant-cards-grid">
              <div className="variant-card">
                <div className="variant-card-header">
                  <span className="variant-badge control">Control</span>
                </div>
                <FormField label="Visitors So Far" hint="Current visitors in control">
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
                  <FormField label="Conversions So Far" hint="Current conversions in control">
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
              </div>

              <div className="variant-card">
                <div className="variant-card-header">
                  <span className="variant-badge variant">Variant</span>
                </div>
                <FormField label="Visitors So Far" hint="Current visitors in variant">
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
                  <FormField label="Conversions So Far" hint="Current conversions in variant">
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
              </div>
            </div>

            <div className="card" style={{ marginTop: '16px' }}>
              <div className="card-title">Test Settings</div>
              <div className="form-grid">
                <FormField label="Planned Total Visitors (per variant)" hint="How many visitors do you plan to include?">
                  <input
                    type="number"
                    name="max_visitors"
                    className="form-input"
                    value={formData.max_visitors}
                    onChange={handleChange}
                    min="1000"
                    step="1000"
                  />
                </FormField>
                <FormField label="Stopping Strategy" hint="When should we let you stop early?">
                  <select
                    name="spending_function"
                    className="form-select"
                    value={formData.spending_function}
                    onChange={handleChange}
                  >
                    <option value="obrien_fleming">Conservative - Harder to stop early, more reliable results</option>
                    <option value="pocock">Flexible - Easier to stop early, slightly less reliable</option>
                  </select>
                </FormField>
                <FormField label="Confidence Level" hint="How sure do you want to be?">
                  <select
                    name="confidence"
                    className="form-select"
                    value={formData.confidence}
                    onChange={handleChange}
                  >
                    <option value={90}>90% - Good for quick decisions</option>
                    <option value={95}>95% - Industry standard (recommended)</option>
                    <option value={99}>99% - High stakes decisions</option>
                  </select>
                </FormField>
              </div>
            </div>
          </>
        )}

        {/* Confidence level for frequentist */}
        {analysisMethod === 'frequentist' && (
          <div className="card" style={{ marginTop: '16px' }}>
            <FormField
              label="Confidence Level"
              hint="Higher confidence = stricter threshold. 95% is industry standard."
            >
              <select
                name="confidence"
                className="form-select"
                value={formData.confidence}
                onChange={handleChange}
                style={{ maxWidth: '200px' }}
              >
                <option value={90}>90% (α = 0.10)</option>
                <option value={95}>95% (α = 0.05)</option>
                <option value={99}>99% (α = 0.01)</option>
              </select>
            </FormField>
            <div style={{ marginTop: '16px' }}>
              <button type="submit" className="btn btn-primary" disabled={loading}>
                {loading ? 'Analyzing...' : 'Analyze Results'}
              </button>
            </div>
          </div>
        )}

        {/* Submit button for other methods */}
        {analysisMethod !== 'frequentist' && (
          <div style={{ marginTop: '16px' }}>
            <button type="submit" className="btn btn-primary" disabled={loading}>
              {loading ? 'Analyzing...' : analysisMethod === 'bayesian' ? 'Run Bayesian Analysis' : 'Check If I Can Stop'}
            </button>
          </div>
        )}
      </form>

      {error && (
        <div className="error-message">{error}</div>
      )}

      {/* Frequentist A/B Results */}
      {result && result.method === 'frequentist' && result.mode === 'ab' && (
        <div className="results-card">
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '20px' }}>
            <span className={`tag ${result.is_significant ? (result.winner === 'variant' ? 'tag-green' : 'tag-red') : 'tag-yellow'}`}>
              {result.is_significant
                ? (result.winner === 'variant' ? '✓ Variant Wins' : '✓ Control Wins')
                : '○ Not Significant'
              }
            </span>
            <span style={{ fontSize: '24px', fontWeight: 600, fontFamily: 'var(--font-mono)' }}>
              {result.lift_percent > 0 ? '+' : ''}{result.lift_percent.toFixed(2)}%
            </span>
          </div>

          <div className="result-grid">
            <div className="result-item">
              <div className="result-label">Control</div>
              <div className="result-value">
                {testType === 'conversion'
                  ? `${(result.control_rate * 100).toFixed(2)}%`
                  : `$${result.control_mean.toFixed(2)}`
                }
              </div>
            </div>
            <div className="result-item">
              <div className="result-label">Variant</div>
              <div className="result-value">
                {testType === 'conversion'
                  ? `${(result.variant_rate * 100).toFixed(2)}%`
                  : `$${result.variant_mean.toFixed(2)}`
                }
              </div>
            </div>
            <div className="result-item">
              <div className="result-label">P-Value</div>
              <div className="result-value">{result.p_value < 0.0001 ? '<0.0001' : result.p_value.toFixed(4)}</div>
            </div>
            <div className="result-item">
              <div className="result-label">Confidence</div>
              <div className="result-value">{result.confidence}%</div>
            </div>
          </div>

          <CIComparisonChart
            controlValue={testType === 'conversion' ? result.control_rate : result.control_mean}
            variantValue={testType === 'conversion' ? result.variant_rate : result.variant_mean}
            controlCI={result.control_ci}
            variantCI={result.variant_ci}
            label={testType === 'conversion' ? 'Conversion Rate' : 'Average Value'}
            formatValue={(v) => testType === 'conversion' ? `${(v * 100).toFixed(2)}%` : `$${v.toFixed(2)}`}
            isConversion={testType === 'conversion'}
          />

          <DistributionChart
            controlMean={testType === 'conversion' ? result.control_rate : result.control_mean}
            variantMean={testType === 'conversion' ? result.variant_rate : result.variant_mean}
            controlStd={testType === 'conversion' ? null : formData.control_std}
            variantStd={testType === 'conversion' ? null : formData.variant_std}
            controlN={formData.control_visitors}
            variantN={formData.variant_visitors}
            isConversion={testType === 'conversion'}
          />

          <div className="stats-explanation">
            <div className="stats-card">
              <div className="stats-card-label">P-Value Explained</div>
              <div className="stats-card-value">{result.p_value < 0.0001 ? '<0.01%' : `${(result.p_value * 100).toFixed(2)}%`}</div>
              <div className="stats-card-explanation">
                {result.p_value < 0.05
                  ? `There's only a ${(result.p_value * 100).toFixed(2)}% chance this result is due to random chance.`
                  : `There's a ${(result.p_value * 100).toFixed(1)}% chance this result is due to random chance—too high to be confident.`
                }
              </div>
            </div>
            <div className="stats-card">
              <div className="stats-card-label">Confidence Interval</div>
              <div className="stats-card-value">
                [{testType === 'conversion'
                  ? `${(result.confidence_interval[0] * 100).toFixed(2)}%, ${(result.confidence_interval[1] * 100).toFixed(2)}%`
                  : `$${result.confidence_interval[0].toFixed(2)}, $${result.confidence_interval[1].toFixed(2)}`
                }]
              </div>
              <div className="stats-card-explanation">
                The true difference likely falls within this range with {result.confidence}% confidence.
              </div>
            </div>
          </div>

          <div className={`callout ${result.is_significant ? 'callout-success' : 'callout-warning'}`} style={{ marginTop: '16px' }}>
            <div className="callout-text markdown-content">
              <ReactMarkdown>{String(result.recommendation || '')}</ReactMarkdown>
            </div>
          </div>
        </div>
      )}

      {/* Frequentist Multi-variant Results */}
      {result && result.method === 'frequentist' && result.mode === 'multi' && (
        <div className="results-card">
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '20px' }}>
            <span className={`tag ${result.is_significant ? 'tag-green' : 'tag-yellow'}`}>
              {result.is_significant
                ? '✓ Significant Differences Found'
                : '○ No Significant Differences'
              }
            </span>
            {result.is_significant && (
              <span style={{ fontSize: '16px', fontWeight: 500 }}>
                Best: <strong>{result.best_variant}</strong>
              </span>
            )}
          </div>

          <div className="card-title">Variant Performance</div>
          <div className="summary-table-wrapper">
            <table className="summary-table">
              <thead>
                <tr>
                  <th>Variant</th>
                  <th>Visitors</th>
                  <th>{testType === 'conversion' ? 'Conversions' : 'Mean'}</th>
                  <th>{testType === 'conversion' ? 'Rate' : 'Std Dev'}</th>
                </tr>
              </thead>
              <tbody>
                {result.variants
                  .sort((a, b) => testType === 'conversion' ? b.rate - a.rate : b.mean - a.mean)
                  .map((v, i) => (
                    <tr key={v.name}>
                      <td>
                        {v.name}
                        {v.name === result.best_variant && <span style={{ marginLeft: '8px' }}>🏆</span>}
                      </td>
                      <td className="mono">{v.visitors.toLocaleString()}</td>
                      <td className="mono">
                        {testType === 'conversion'
                          ? v.conversions.toLocaleString()
                          : `$${v.mean.toFixed(2)}`
                        }
                      </td>
                      <td className="mono">
                        {testType === 'conversion'
                          ? `${(v.rate * 100).toFixed(2)}%`
                          : `$${v.std.toFixed(2)}`
                        }
                      </td>
                    </tr>
                  ))}
              </tbody>
            </table>
          </div>

          {result.pairwise_comparisons.filter(p => p.is_significant).length > 0 && (
            <>
              <div className="card-title" style={{ marginTop: '24px' }}>Significant Pairwise Comparisons</div>
              <div className="summary-table-wrapper">
                <table className="summary-table">
                  <thead>
                    <tr>
                      <th>Comparison</th>
                      <th>Lift</th>
                      <th>P-Value (adjusted)</th>
                    </tr>
                  </thead>
                  <tbody>
                    {result.pairwise_comparisons
                      .filter(p => p.is_significant)
                      .map((p, i) => {
                        const winner = p.lift_percent > 0 ? p.variant_b : p.variant_a
                        const loser = p.lift_percent > 0 ? p.variant_a : p.variant_b
                        return (
                          <tr key={i}>
                            <td><strong>{winner}</strong> beats {loser}</td>
                            <td className="mono">{Math.abs(p.lift_percent).toFixed(2)}%</td>
                            <td className="mono">{p.p_value_adjusted.toFixed(4)}</td>
                          </tr>
                        )
                      })}
                  </tbody>
                </table>
              </div>
            </>
          )}

          <div className="stats-explanation" style={{ marginTop: '20px' }}>
            <div className="stats-card">
              <div className="stats-card-label">Overall Test P-Value</div>
              <div className="stats-card-value">{result.p_value.toFixed(4)}</div>
              <div className="stats-card-explanation">
                {testType === 'conversion' ? 'Chi-square test' : 'ANOVA'} for overall differences between variants.
              </div>
            </div>
            <div className="stats-card">
              <div className="stats-card-label">Multiple Comparison Correction</div>
              <div className="stats-card-value">Bonferroni</div>
              <div className="stats-card-explanation">
                P-values are adjusted to prevent false positives when making multiple comparisons.
              </div>
            </div>
          </div>

          <div className={`callout ${result.is_significant ? 'callout-success' : 'callout-warning'}`} style={{ marginTop: '16px' }}>
            <div className="callout-text markdown-content">
              <ReactMarkdown>{String(result.recommendation || '')}</ReactMarkdown>
            </div>
          </div>
        </div>
      )}

      {/* Bayesian Results */}
      {result && result.method === 'bayesian' && (
        <div className="results-card">
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '20px' }}>
            <span className={`tag ${result.probability_variant_better > 95 ? 'tag-green' : result.probability_variant_better < 5 ? 'tag-red' : 'tag-yellow'}`}>
              {result.probability_variant_better > 95 ? '✓ Variant Wins' :
               result.probability_variant_better < 5 ? '✓ Control Wins' :
               '○ Too Close to Call'}
            </span>
            <span style={{ fontSize: '24px', fontWeight: 600, fontFamily: 'var(--font-mono)' }}>
              {result.probability_variant_better.toFixed(1)}% chance variant wins
            </span>
          </div>

          <div className="result-grid">
            <div className="result-item">
              <div className="result-label">Chance Variant Wins</div>
              <div className="result-value success">{result.probability_variant_better.toFixed(1)}%</div>
            </div>
            <div className="result-item">
              <div className="result-label">Chance Control Wins</div>
              <div className="result-value">{result.probability_control_better.toFixed(1)}%</div>
            </div>
            <div className="result-item">
              <div className="result-label">Expected Improvement</div>
              <div className="result-value">{result.lift_percent >= 0 ? '+' : ''}{result.lift_percent.toFixed(2)}%</div>
            </div>
            <div className="result-item">
              <div className="result-label">Recommendation</div>
              <div className="result-value" style={{ textTransform: 'capitalize' }}>
                {result.winner === 'variant' ? 'Ship Variant' : result.winner === 'control' ? 'Keep Control' : 'Wait for more data'}
              </div>
            </div>
          </div>

          <div className="stats-explanation" style={{ marginTop: '20px' }}>
            <div className="stats-card">
              <div className="stats-card-label">Risk of Choosing Variant</div>
              <div className="stats-card-value">{(result.expected_loss_choosing_variant * 100).toFixed(2)}%</div>
              <div className="stats-card-explanation">
                If you ship the variant and it's actually worse, this is how much you might lose in conversion rate.
              </div>
            </div>
            <div className="stats-card">
              <div className="stats-card-label">Risk of Keeping Control</div>
              <div className="stats-card-value">{(result.expected_loss_choosing_control * 100).toFixed(2)}%</div>
              <div className="stats-card-explanation">
                If you keep the control and variant was actually better, this is how much you might miss out on.
              </div>
            </div>
          </div>

          <div className="stats-explanation" style={{ marginTop: '16px' }}>
            <div className="stats-card">
              <div className="stats-card-label">Likely Improvement Range</div>
              <div className="stats-card-value">
                {result.lift_credible_interval[0].toFixed(2)}% to {result.lift_credible_interval[1].toFixed(2)}%
              </div>
              <div className="stats-card-explanation">
                We're 95% confident the true improvement falls in this range.
              </div>
            </div>
            <div className="stats-card">
              <div className="stats-card-label">Conversion Rates</div>
              <div className="stats-card-value">
                {(result.control_rate * 100).toFixed(2)}% vs {(result.variant_rate * 100).toFixed(2)}%
              </div>
              <div className="stats-card-explanation">
                Control vs Variant conversion rates from your data.
              </div>
            </div>
          </div>

          <div className={`callout ${result.probability_variant_better > 95 || result.probability_variant_better < 5 ? 'callout-success' : 'callout-warning'}`} style={{ marginTop: '20px' }}>
            <div className="callout-text">
              <strong>What this means:</strong> There's a {result.probability_variant_better.toFixed(1)}% chance
              the variant performs better than control. The expected improvement is {result.lift_percent.toFixed(2)}%,
              and we're 95% confident the real improvement is between {result.lift_credible_interval[0].toFixed(2)}% and {result.lift_credible_interval[1].toFixed(2)}%.
              {result.winner !== 'none' && result.winner === 'variant' && ' We recommend shipping the variant.'}
              {result.winner !== 'none' && result.winner === 'control' && ' We recommend keeping the control.'}
              {result.winner === 'none' && ' We recommend waiting for more data before deciding.'}
            </div>
          </div>
        </div>
      )}

      {/* Sequential Results */}
      {result && result.method === 'sequential' && (
        <div className="results-card">
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '20px' }}>
            <span className={`tag ${result.can_stop ? 'tag-green' : 'tag-yellow'}`}>
              {result.can_stop ? '✓ You Can Stop!' : '○ Keep Running'}
            </span>
            {result.can_stop && result.decision === 'variant_wins' && (
              <span className="tag tag-green">Variant Wins</span>
            )}
            {result.can_stop && result.decision === 'control_wins' && (
              <span className="tag tag-red">Control Wins</span>
            )}
          </div>

          <div className="result-grid">
            <div className="result-item">
              <div className="result-label">Test Progress</div>
              <div className="result-value">{(result.information_fraction * 100).toFixed(0)}%</div>
              <div className="result-unit">of planned visitors</div>
            </div>
            <div className="result-item">
              <div className="result-label">Current Improvement</div>
              <div className="result-value" style={{ color: result.lift_percent >= 0 ? 'var(--pastel-green-text)' : 'var(--pastel-red-text)' }}>
                {result.lift_percent >= 0 ? '+' : ''}{result.lift_percent.toFixed(2)}%
              </div>
            </div>
            <div className="result-item">
              <div className="result-label">Confidence (Variant Better)</div>
              <div className="result-value">{result.confidence_variant_better.toFixed(1)}%</div>
            </div>
            <div className="result-item">
              <div className="result-label">Visitors Remaining</div>
              <div className="result-value">{result.estimated_remaining_visitors?.toLocaleString() || 'N/A'}</div>
              <div className="result-unit">per variant</div>
            </div>
          </div>

          {/* Visual progress indicator */}
          <div style={{ marginTop: '24px', padding: '20px', background: 'var(--bg-secondary)', borderRadius: 'var(--radius-lg)' }}>
            <div className="card-title">Can You Stop Early?</div>
            <div style={{ marginTop: '12px', marginBottom: '8px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', color: 'var(--text-muted)', marginBottom: '4px' }}>
                <span>Test progress</span>
                <span>{(result.information_fraction * 100).toFixed(0)}% complete</span>
              </div>
              <div style={{ height: '8px', background: 'var(--bg-active)', borderRadius: '4px', overflow: 'hidden' }}>
                <div style={{
                  height: '100%',
                  width: `${result.information_fraction * 100}%`,
                  background: result.can_stop ? 'var(--pastel-green-text)' : 'var(--accent)',
                  borderRadius: '4px',
                  transition: 'width 0.3s ease'
                }} />
              </div>
            </div>
            <div style={{ marginTop: '16px', fontSize: '14px', color: 'var(--text-secondary)' }}>
              {result.can_stop ? (
                <span style={{ color: 'var(--pastel-green-text)', fontWeight: 500 }}>
                  The difference is strong enough to call the test early!
                </span>
              ) : (
                <span>
                  The difference isn't strong enough yet. Keep running until you reach {(result.information_fraction * 100).toFixed(0) < 50 ? 'at least 50%' : '100%'} or the results become clearer.
                </span>
              )}
            </div>
          </div>

          <div className={`callout ${result.can_stop ? 'callout-success' : 'callout-info'}`} style={{ marginTop: '20px' }}>
            <div className="callout-text">
              {result.can_stop ? (
                result.decision === 'variant_wins' ? (
                  <><strong>You can stop the test!</strong> The variant is performing significantly better than control ({result.lift_percent.toFixed(2)}% improvement). You can confidently ship the variant.</>
                ) : result.decision === 'control_wins' ? (
                  <><strong>You can stop the test!</strong> The control is performing better than the variant. We recommend not shipping this change.</>
                ) : (
                  <><strong>You can stop the test.</strong> There's no meaningful difference between control and variant. Consider stopping to save time and resources.</>
                )
              ) : (
                <><strong>Keep running the test.</strong> You've tested {(result.information_fraction * 100).toFixed(0)}% of your planned visitors. The current improvement is {result.lift_percent.toFixed(2)}%, but we need more data to be confident this is real and not random noise.</>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default SignificanceCalculator
