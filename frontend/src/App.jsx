import { Routes, Route, NavLink } from 'react-router-dom'
import SampleSizeCalculator from './pages/SampleSizeCalculator'
import ConfidenceIntervalCalculator from './pages/PowerCalculator'
import SignificanceCalculator from './pages/SignificanceCalculator'
import DiffInDiffCalculator from './pages/DiffInDiffCalculator'
import TimingCalculator from './pages/TimingCalculator'

function App() {
  return (
    <div className="app-container">
      <nav className="sidebar">
        <div className="sidebar-header">
          <img src="/logo.png" alt="expstats" className="sidebar-logo" />
        </div>
        
        <div className="nav-section">
          <div className="nav-section-title">Pre-Test Planning</div>
          <NavLink 
            to="/" 
            className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
            end
          >
            <span className="nav-icon">📐</span>
            Sample Size
          </NavLink>
        </div>

        <div className="nav-section">
          <div className="nav-section-title">Results Analysis</div>
          <NavLink 
            to="/analyze" 
            className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
          >
            <span className="nav-icon">📊</span>
            A/B Test Results
          </NavLink>
          <NavLink 
            to="/timing" 
            className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
          >
            <span className="nav-icon">⏱️</span>
            Timing & Rates
          </NavLink>
          <NavLink 
            to="/diff-in-diff" 
            className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
          >
            <span className="nav-icon">🔬</span>
            Diff-in-Diff
          </NavLink>
        </div>

        <div className="nav-section">
          <div className="nav-section-title">Utilities</div>
          <NavLink 
            to="/confidence" 
            className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
          >
            <span className="nav-icon">📏</span>
            Confidence Interval
          </NavLink>
        </div>

        <div className="nav-divider"></div>

        <div className="nav-section">
          <div className="nav-section-title">Help</div>
          <a 
            href="https://github.com/expstats/expstats"
            target="_blank"
            rel="noopener noreferrer"
            className="nav-link"
          >
            <span className="nav-icon">📖</span>
            Documentation
          </a>
        </div>
      </nav>
      
      <main className="main-content">
        <Routes>
          <Route path="/" element={<SampleSizeCalculator />} />
          <Route path="/analyze" element={<SignificanceCalculator />} />
          <Route path="/timing" element={<TimingCalculator />} />
          <Route path="/diff-in-diff" element={<DiffInDiffCalculator />} />
          <Route path="/confidence" element={<ConfidenceIntervalCalculator />} />
        </Routes>
      </main>
    </div>
  )
}

export default App
