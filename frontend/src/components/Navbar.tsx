/**
 * Navbar — Phase 10 update.
 * Added: LanguageSelector, react-i18next for navigation labels.
 * All Phase 1–9 routes preserved.
 */
import { useState } from 'react'
import { Link, useNavigate, useLocation } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useAuth } from '../context/AuthContext'
import LanguageSelector from './LanguageSelector'

export default function Navbar() {
  const { user, isAuthenticated, logout } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const { t } = useTranslation()
  const [mobileOpen, setMobileOpen] = useState(false)

  const handleLogout = () => {
    logout()
    navigate('/')
  }

  const navLinks = isAuthenticated
    ? [
        { to: '/dashboard',             label: t('nav.dashboard') },
        { to: '/analytics',             label: `📊 ${t('nav.analytics')}` },
        { to: '/advisor',               label: `🤖 ${t('nav.aiAdvisor')}` },
        { to: '/businesses',            label: t('nav.businesses') },
        { to: '/recommendations',       label: t('nav.recommendations') },
        { to: '/goals',                 label: `🎯 ${t('nav.goals')}` },
        { to: '/financial-progress',    label: `💰 ${t('nav.financialProgress')}` },
        { to: '/financial-analysis',    label: `📈 ${t('nav.financialAnalysis')}` },
        { to: '/investment-optimizer',  label: `⚡ ${t('nav.optimizer')}` },
        { to: '/market-intelligence',   label: `🗺️ ${t('nav.market')}` },
        { to: '/scheme-support',        label: `🏛️ ${t('nav.schemes')}` },
        { to: '/profile',               label: t('nav.profile') },
      ]
    : []

  // Public quick links (demo & architecture)
  const publicLinks = [
    { to: '/demo', label: 'Demo' },
    { to: '/architecture', label: 'Architecture' },
  ]

  const isActive = (path: string) => location.pathname === path

  return (
    <nav className="sticky top-0 z-50 bg-surface-900/80 backdrop-blur-md border-b border-primary-900/40">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-2 group">
            <div className="w-8 h-8 rounded-lg bg-primary-600 flex items-center justify-center shadow-glow-sm group-hover:shadow-glow transition-all duration-300">
              <span className="text-white font-bold text-sm">R</span>
            </div>
            <span className="font-display font-bold text-white text-lg">
              RuralBiz<span className="text-primary-400"> AI</span>
            </span>
          </Link>

          {/* Desktop nav */}
          <div className="hidden md:flex items-center gap-1">
            {navLinks.map((link) => (
              <Link
                key={link.to}
                to={link.to}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
                  isActive(link.to)
                    ? 'bg-primary-800/60 text-primary-300'
                    : 'text-gray-400 hover:text-white hover:bg-surface-700'
                }`}
              >
                {link.label}
              </Link>
            ))}
            {publicLinks.map((link) => (
              <Link key={link.to} to={link.to} className="px-3 py-2 rounded-lg text-sm font-medium text-gray-400 hover:text-white hover:bg-surface-700 transition-all duration-200">
                {link.label}
              </Link>
            ))}
          </div>

          {/* Right side — language selector + auth */}
          <div className="hidden md:flex items-center gap-3">
            {/* Phase 10 — Language Selector */}
            <LanguageSelector />

            {isAuthenticated ? (
              <>
                <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-surface-700 border border-primary-800/30">
                  <div className="w-7 h-7 rounded-full bg-primary-700 flex items-center justify-center text-xs font-bold text-white">
                    {user?.full_name?.[0]?.toUpperCase() ?? user?.email?.[0]?.toUpperCase() ?? 'U'}
                  </div>
                  <span className="text-sm text-gray-300 max-w-[120px] truncate">
                    {user?.full_name ?? user?.email}
                  </span>
                </div>
                <button onClick={handleLogout} className="btn-ghost text-sm">
                  {t('nav.logout')}
                </button>
              </>
            ) : (
              <>
                <Link to="/login" className="btn-ghost text-sm">{t('nav.login')}</Link>
                <Link to="/register" className="btn-primary text-sm py-2 px-4">
                  {t('auth.registerBtn')}
                </Link>
              </>
            )}
          </div>

          {/* Mobile toggle */}
          <button
            className="md:hidden btn-ghost p-2"
            onClick={() => setMobileOpen(!mobileOpen)}
            aria-label="Toggle menu"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              {mobileOpen ? (
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              ) : (
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              )}
            </svg>
          </button>
        </div>
      </div>

      {/* Mobile menu */}
      {mobileOpen && (
        <div className="md:hidden bg-surface-800 border-t border-primary-900/40 px-4 py-3 space-y-1 animate-slide-up">
          {navLinks.map((link) => (
            <Link
              key={link.to}
              to={link.to}
              className="block px-3 py-2 rounded-lg text-sm text-gray-300 hover:text-white hover:bg-surface-700 transition-colors"
              onClick={() => setMobileOpen(false)}
            >
              {link.label}
            </Link>
          ))}
          <div className="pt-2 border-t border-primary-900/30 flex flex-col gap-2">
            {/* Phase 10 — Language Selector in mobile menu */}
            <div className="flex items-center justify-between">
              <span className="text-xs text-gray-500">🌐 Language</span>
              <LanguageSelector compact />
            </div>
            {isAuthenticated ? (
              <button onClick={handleLogout} className="btn-ghost text-sm justify-start">
                {t('nav.logout')}
              </button>
            ) : (
              <>
                <Link to="/login" className="btn-ghost text-sm" onClick={() => setMobileOpen(false)}>{t('nav.login')}</Link>
                <Link to="/register" className="btn-primary text-sm" onClick={() => setMobileOpen(false)}>{t('auth.registerBtn')}</Link>
              </>
            )}
          </div>
        </div>
      )}
    </nav>
  )
}
