export default function ErrorBoundaryFallback({ reset }: { reset?: () => void }) {
  return (
    <div className="min-h-[50vh] flex flex-col items-center justify-center p-8 text-center">
      <div className="text-6xl mb-4">⚠️</div>
      <h2 className="text-2xl font-display font-bold text-white mb-2">Something went wrong</h2>
      <p className="text-sm text-gray-400 mb-4">An unexpected error occurred. Please try refreshing the page.</p>
      <div className="flex gap-3">
        <button onClick={() => window.location.reload()} className="btn-primary px-6 py-2.5">Refresh</button>
        {reset && <button onClick={reset} className="btn-ghost px-6 py-2.5">Try Again</button>}
      </div>
    </div>
  )
}
