import React from 'react'
import { ErrorBoundary as UBErrorBoundary } from './UIStates'

// Lightweight wrapper to provide a named `ErrorBoundary` export as requested in Phase 11.
export default function ErrorBoundary({ children }: { children: React.ReactNode }) {
  return <UBErrorBoundary>{children}</UBErrorBoundary>
}
