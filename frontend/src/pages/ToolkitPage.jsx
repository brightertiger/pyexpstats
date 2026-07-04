import { Link } from 'react-router-dom'

const TOOLS = [
  {
    to: '/segments',
    when: 'After a test',
    title: 'Segment Analysis',
    description: 'Slice a finished test by device, country, or cohort to see who the change helped — and who it hurt.',
  },
  {
    to: '/impact',
    when: 'After a test',
    title: 'Revenue Impact',
    description: 'Turn a winning lift into projected annual revenue and profit you can put in front of stakeholders.',
  },
  {
    to: '/diff-in-diff',
    when: "When you can't randomize",
    title: 'Before / After',
    description: 'Measure causal impact with difference-in-differences when a proper A/B test is not an option.',
  },
  {
    to: '/timing',
    when: 'Time-based metrics',
    title: 'Timing & Rates',
    description: 'Compare time-to-event outcomes (time to purchase, churn) or event rates per unit of time.',
  },
  {
    to: '/confidence-interval',
    when: 'One metric',
    title: 'Metric Ranges',
    description: 'Put a confidence interval around a single conversion rate or average from sampled data.',
  },
]

function ToolkitPage() {
  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Toolkit</h1>
        <p className="page-description">
          Specialist tools for the questions that come up around an experiment —
          after it ends, when you can't run one, or when the metric needs special handling.
        </p>
      </div>

      <div className="toolkit-grid">
        {TOOLS.map(({ to, when, title, description }) => (
          <Link key={to} to={to} className="toolkit-card">
            <span className="toolkit-card-when">{when}</span>
            <span className="toolkit-card-title">{title}</span>
            <span className="toolkit-card-desc">{description}</span>
            <span className="toolkit-card-cta" aria-hidden="true">Open →</span>
          </Link>
        ))}
      </div>
    </div>
  )
}

export default ToolkitPage
