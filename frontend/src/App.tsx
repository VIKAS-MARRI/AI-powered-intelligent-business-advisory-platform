/**
 * App.tsx — Phase 11: Lazy-loaded routes, ErrorBoundary, new /demo and /architecture routes.
 */
import { Suspense, lazy } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider } from './context/AuthContext'
import Navbar from './components/Navbar'
import DemoBadge from './components/DemoBadge'
import ProtectedRoute from './components/ProtectedRoute'
import ErrorBoundary from './components/ErrorBoundary'
import { LoadingState } from './components/UIStates'

// ── Eager-loaded (small, always needed) ──────────────────────────────────────
import Landing  from './pages/Landing'
import Login    from './pages/Login'
import Register from './pages/Register'

// ── Lazy-loaded (code-split for performance) ──────────────────────────────────
const Dashboard            = lazy(() => import('./pages/Dashboard'))
const Profile              = lazy(() => import('./pages/Profile'))
const Businesses           = lazy(() => import('./pages/Businesses'))
const Recommendations      = lazy(() => import('./pages/Recommendations'))
const FinancialAnalysis    = lazy(() => import('./pages/FinancialAnalysis'))
const InvestmentOptimizer  = lazy(() => import('./pages/InvestmentOptimizer'))
const MarketIntelligence   = lazy(() => import('./pages/MarketIntelligence'))
const SchemeSupport        = lazy(() => import('./pages/SchemeSupport'))
const AIAdvisor            = lazy(() => import('./pages/AIAdvisor'))
const SavedBusinesses      = lazy(() => import('./pages/SavedBusinesses'))
const AnalyticsDashboard   = lazy(() => import('./pages/AnalyticsDashboard'))
const Goals                = lazy(() => import('./pages/Goals'))
const FinancialProgress    = lazy(() => import('./pages/FinancialProgress'))
// Phase 11
const Demo                 = lazy(() => import('./pages/Demo'))
const Architecture         = lazy(() => import('./pages/Architecture'))
const FinalActionPlan      = lazy(() => import('./pages/FinalActionPlan'))

const PageLoader = () => (
  <div className="min-h-[50vh] flex items-center justify-center">
    <LoadingState message="Loading page…" />
  </div>
)

export default function App() {
  return (
    <ErrorBoundary>
      <AuthProvider>
        <BrowserRouter>
          <div className="min-h-screen flex flex-col bg-surface-900">
            <Navbar />
              <DemoBadge />
            <main className="flex-1">
              <Suspense fallback={<PageLoader />}>
                <Routes>
                  {/* ── Public ── */}
                  <Route path="/"             element={<Landing />} />
                  <Route path="/login"        element={<Login />} />
                  <Route path="/register"     element={<Register />} />
                  {/* Phase 11 — public demo & architecture pages */}
                  <Route path="/demo"         element={<Demo />} />
                  <Route path="/architecture" element={<Architecture />} />

                  {/* ── Protected ── */}
                  <Route path="/dashboard"          element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
                  <Route path="/profile"             element={<ProtectedRoute><Profile /></ProtectedRoute>} />
                  <Route path="/businesses"          element={<ProtectedRoute><Businesses /></ProtectedRoute>} />
                  <Route path="/recommendations"     element={<ProtectedRoute><Recommendations /></ProtectedRoute>} />
                  <Route path="/financial-analysis"  element={<ProtectedRoute><FinancialAnalysis /></ProtectedRoute>} />
                  <Route path="/investment-optimizer" element={<ProtectedRoute><InvestmentOptimizer /></ProtectedRoute>} />
                  <Route path="/market-intelligence" element={<ProtectedRoute><MarketIntelligence /></ProtectedRoute>} />
                  <Route path="/scheme-support"      element={<ProtectedRoute><SchemeSupport /></ProtectedRoute>} />
                  <Route path="/advisor"             element={<ProtectedRoute><AIAdvisor /></ProtectedRoute>} />
                  <Route path="/demo/final"          element={<ProtectedRoute><FinalActionPlan /></ProtectedRoute>} />
                  <Route path="/saved-businesses"    element={<ProtectedRoute><SavedBusinesses /></ProtectedRoute>} />
                  <Route path="/analytics"           element={<ProtectedRoute><AnalyticsDashboard /></ProtectedRoute>} />
                  <Route path="/goals"               element={<ProtectedRoute><Goals /></ProtectedRoute>} />
                  <Route path="/financial-progress"  element={<ProtectedRoute><FinancialProgress /></ProtectedRoute>} />

                  {/* ── Legacy aliases ── */}
                  <Route path="/finance" element={<Navigate to="/financial-analysis" replace />} />

                  {/* ── Fallback ── */}
                  <Route path="*" element={<Navigate to="/" replace />} />
                </Routes>
              </Suspense>
            </main>
          </div>
        </BrowserRouter>
      </AuthProvider>
    </ErrorBoundary>
  )
}
