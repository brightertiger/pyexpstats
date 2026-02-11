import { useState, useRef, useEffect } from 'react'
import { Routes, Route, NavLink } from 'react-router-dom'
import SampleSizeCalculator from './pages/SampleSizeCalculator'
import SignificanceCalculator from './pages/SignificanceCalculator'
import DiffInDiffCalculator from './pages/DiffInDiffCalculator'
import TimingCalculator from './pages/TimingCalculator'
import CICalculator from './pages/CICalculator'
import DiagnosticsPage from './pages/DiagnosticsPage'
import SegmentAnalysisPage from './pages/SegmentAnalysisPage'
import ImpactProjectionPage from './pages/ImpactProjectionPage'

function App() {
  const [moreOpen, setMoreOpen] = useState(false)
  const moreRef = useRef(null)

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event) {
      if (moreRef.current && !moreRef.current.contains(event.target)) {
        setMoreOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  return (
    <div className="app-container">
      <header className="top-header">
        <div className="header-left">
          <img src="/logo.png" alt="pyexpstats" className="header-logo" />
        </div>

        <nav className="header-nav">
          <NavLink to="/" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`} end>
            Plan
          </NavLink>
          <NavLink to="/analyze" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
            Analyze
          </NavLink>
          <NavLink to="/diagnostics" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
            Diagnose
          </NavLink>

          <div className="nav-dropdown" ref={moreRef}>
            <button
              className={`nav-item nav-dropdown-trigger ${moreOpen ? 'active' : ''}`}
              onClick={() => setMoreOpen(!moreOpen)}
            >
              More
              <svg width="12" height="12" viewBox="0 0 12 12" fill="currentColor" style={{ marginLeft: '4px' }}>
                <path d="M3 4.5L6 7.5L9 4.5" stroke="currentColor" strokeWidth="1.5" fill="none" />
              </svg>
            </button>
            {moreOpen && (
              <div className="nav-dropdown-menu">
                <NavLink
                  to="/segments"
                  className="nav-dropdown-item"
                  onClick={() => setMoreOpen(false)}
                >
                  <span className="nav-dropdown-icon">🎯</span>
                  <div>
                    <div className="nav-dropdown-label">Segments</div>
                    <div className="nav-dropdown-desc">Results by user group</div>
                  </div>
                </NavLink>
                <NavLink
                  to="/impact"
                  className="nav-dropdown-item"
                  onClick={() => setMoreOpen(false)}
                >
                  <span className="nav-dropdown-icon">💰</span>
                  <div>
                    <div className="nav-dropdown-label">Revenue Impact</div>
                    <div className="nav-dropdown-desc">Estimate business value</div>
                  </div>
                </NavLink>
                <NavLink
                  to="/diff-in-diff"
                  className="nav-dropdown-item"
                  onClick={() => setMoreOpen(false)}
                >
                  <span className="nav-dropdown-icon">📈</span>
                  <div>
                    <div className="nav-dropdown-label">Before/After</div>
                    <div className="nav-dropdown-desc">Compare pre vs post periods</div>
                  </div>
                </NavLink>
                <NavLink
                  to="/timing"
                  className="nav-dropdown-item"
                  onClick={() => setMoreOpen(false)}
                >
                  <span className="nav-dropdown-icon">⏱️</span>
                  <div>
                    <div className="nav-dropdown-label">Time-Based</div>
                    <div className="nav-dropdown-desc">Time-to-event tests</div>
                  </div>
                </NavLink>
                <NavLink
                  to="/confidence-interval"
                  className="nav-dropdown-item"
                  onClick={() => setMoreOpen(false)}
                >
                  <span className="nav-dropdown-icon">📏</span>
                  <div>
                    <div className="nav-dropdown-label">Metric Range</div>
                    <div className="nav-dropdown-desc">Range for a single metric</div>
                  </div>
                </NavLink>
              </div>
            )}
          </div>
        </nav>

        <a
          href="https://github.com/pyexptest/pyexptest"
          target="_blank"
          rel="noopener noreferrer"
          className="github-link"
          aria-label="GitHub"
        >
          <svg viewBox="0 0 24 24" width="22" height="22" fill="currentColor">
            <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
          </svg>
        </a>
      </header>

      <main className="main-content">
        <Routes>
          <Route path="/" element={<SampleSizeCalculator />} />
          <Route path="/analyze" element={<SignificanceCalculator />} />
          <Route path="/diagnostics" element={<DiagnosticsPage />} />
          <Route path="/timing" element={<TimingCalculator />} />
          <Route path="/diff-in-diff" element={<DiffInDiffCalculator />} />
          <Route path="/segments" element={<SegmentAnalysisPage />} />
          <Route path="/impact" element={<ImpactProjectionPage />} />
          <Route path="/confidence-interval" element={<CICalculator />} />
        </Routes>
      </main>
    </div>
  )
}

export default App
