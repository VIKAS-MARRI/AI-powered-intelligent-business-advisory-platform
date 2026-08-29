/**
 * Phase 11 — Section 15: Reusable UI State Components
 *
 * ErrorBoundary    — catches React render errors
 * LoadingState     — consistent loading spinner
 * EmptyState       — no-data placeholder
 * APIErrorState    — backend/network errors with retry
 */
import React, { Component, type ReactNode } from 'react'

// ── ErrorBoundary ─────────────────────────────────────────────────────────────

interface ErrorBoundaryProps {
  children: ReactNode
  fallback?: ReactNode
}
interface ErrorBoundaryState {
  hasError: boolean
  error?: Error
}

export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props)
    this.state = { hasError: false }
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, info: React.ErrorInfo) {
    console.error('[ErrorBoundary]', error, info)
  }

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) return this.props.fallback
      return (
        <div className="flex flex-col items-center justify-center min-h-[300px] p-8 text-center">
          <div className="text-5xl mb-4">⚠️</div>
          <h2 className="text-xl font-display font-bold text-white mb-2">Something went wrong</h2>
          <p className="text-gray-400 text-sm mb-6">
            An unexpected error occurred. Please refresh the page.
          </p>
          <button
            onClick={() => window.location.reload()}
            className="btn-primary px-6 py-2.5"
          >
            Refresh Page
          </button>
        </div>
      )
    }
    return this.props.children
  }
}

// ── LoadingState ──────────────────────────────────────────────────────────────

interface LoadingStateProps {
  message?: string
  size?: 'sm' | 'md' | 'lg'
  className?: string
}

export function LoadingState({ message = 'Loading…', size = 'md', className = '' }: LoadingStateProps) {
  const sizes = { sm: 'w-5 h-5', md: 'w-8 h-8', lg: 'w-12 h-12' }
  const textSizes = { sm: 'text-xs', md: 'text-sm', lg: 'text-base' }

  return (
    <div className={`flex flex-col items-center justify-center gap-3 py-12 ${className}`}>
      <div
        className={`${sizes[size]} border-2 border-surface-600 border-t-primary-400 rounded-full animate-spin`}
        role="status"
        aria-label="Loading"
      />
      <p className={`${textSizes[size]} text-gray-400`}>{message}</p>
    </div>
  )
}

// ── EmptyState ────────────────────────────────────────────────────────────────

interface EmptyStateProps {
  icon?: string
  title: string
  description?: string
  action?: { label: string; onClick: () => void }
  className?: string
}

export function EmptyState({ icon = '📭', title, description, action, className = '' }: EmptyStateProps) {
  return (
    <div className={`flex flex-col items-center justify-center gap-4 py-16 text-center ${className}`}>
      <div className="text-5xl" aria-hidden="true">{icon}</div>
      <div>
        <h3 className="text-lg font-display font-semibold text-white mb-1">{title}</h3>
        {description && <p className="text-sm text-gray-400 max-w-sm">{description}</p>}
      </div>
      {action && (
        <button onClick={action.onClick} className="btn-primary px-5 py-2 mt-2">
          {action.label}
        </button>
      )}
    </div>
  )
}

// ── APIErrorState ─────────────────────────────────────────────────────────────

interface APIErrorStateProps {
  error?: string | null
  onRetry?: () => void
  title?: string
  className?: string
}

export function APIErrorState({
  error,
  onRetry,
  title = 'Unable to load data',
  className = '',
}: APIErrorStateProps) {
  // Map known technical errors to user-friendly messages
  const friendlyMessage = (() => {
    if (!error) return 'An unexpected error occurred. Please try again.'
    const e = error.toLowerCase()
    if (e.includes('network') || e.includes('fetch') || e.includes('econnrefused'))
      return 'Unable to connect to the server. Please check your connection.'
    if (e.includes('overpass') || e.includes('openstreetmap'))
      return 'Map data is temporarily unavailable. You can try again in a moment.'
    if (e.includes('503') || e.includes('service unavailable'))
      return 'The service is temporarily unavailable. Please try again shortly.'
    if (e.includes('429') || e.includes('rate limit'))
      return 'Too many requests. Please wait a moment before trying again.'
    if (e.includes('401') || e.includes('unauthorized'))
      return 'Your session may have expired. Please log in again.'
    return 'An error occurred while loading data. Please try again.'
  })()

  return (
    <div className={`rounded-xl bg-red-900/20 border border-red-700/30 p-6 text-center ${className}`}>
      <div className="text-3xl mb-3" aria-hidden="true">🔌</div>
      <h3 className="text-base font-semibold text-red-300 mb-1">{title}</h3>
      <p className="text-sm text-red-400/80 mb-4">{friendlyMessage}</p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="px-5 py-2 text-sm font-medium rounded-lg bg-red-800/40 hover:bg-red-700/50 text-red-300 border border-red-700/40 transition-colors"
        >
          🔄 Try Again
        </button>
      )}
    </div>
  )
}
