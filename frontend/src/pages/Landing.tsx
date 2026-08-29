import { Link } from 'react-router-dom'

const features = [
  {
    icon: '🎯',
    title: 'Business Recommendations',
    desc: 'AI-powered suggestions matched to your skills, capital, and local market.',
  },
  {
    icon: '📍',
    title: 'Hyper-Local Market Analysis',
    desc: 'Discover nearby competitors, markets, and opportunities using OpenStreetMap.',
  },
  {
    icon: '💰',
    title: 'Financial Planning',
    desc: 'Deterministic calculators for revenue, expenses, ROI, and break-even.',
  },
  {
    icon: '🏛️',
    title: 'Government Schemes',
    desc: 'Find schemes you qualify for — PMEGP, Mudra Loan, and more.',
  },
  {
    icon: '🔮',
    title: 'What-If Simulator',
    desc: 'Test different scenarios: "What if sales drop 20%?" — instant answers.',
  },
  {
    icon: '🤖',
    title: 'AI Chat Assistant',
    desc: 'Ask anything in English or Telugu. Get verified, data-backed answers.',
  },
]

const stats = [
  { value: '30+', label: 'Business Types' },
  { value: '₹50K–₹5L', label: 'Capital Ranges' },
  { value: '2', label: 'Languages' },
  { value: '100%', label: 'Free to Use' },
]

export default function Landing() {
  return (
    <div className="min-h-screen">
      {/* ── Hero ── */}
      <section className="relative overflow-hidden pt-20 pb-32 px-4">
        {/* Gradient background */}
        <div className="absolute inset-0 bg-hero-gradient" />
        <div className="absolute inset-0 bg-glow-green opacity-60" />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] rounded-full bg-primary-800/10 blur-3xl" />

        <div className="relative max-w-5xl mx-auto text-center animate-fade-in">
          {/* Badge */}
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-primary-900/60 border border-primary-700/50 text-primary-400 text-sm font-medium mb-8">
            <span className="w-2 h-2 rounded-full bg-primary-400 animate-pulse-slow" />
            AI-Powered Business Advisory for Rural India
          </div>

          <h1 className="text-5xl sm:text-6xl lg:text-7xl font-display font-extrabold text-white leading-tight mb-6">
            Your AI{' '}
            <span className="text-gradient">Business Partner</span>
            <br />
            for Rural India
          </h1>

          <p className="text-xl text-gray-400 max-w-2xl mx-auto mb-10 leading-relaxed">
            RuralBiz AI helps micro-entrepreneurs discover the right business, plan their finances,
            find government schemes, and grow — all powered by AI and hyper-local data.
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link to="/register" className="btn-primary text-base px-8 py-4">
              Start Free →
            </Link>
            <Link to="/login" className="btn-secondary text-base px-8 py-4">
              Sign In
            </Link>
          </div>

          {/* Hero illustration text */}
          <div className="mt-16 text-8xl animate-float select-none">🌾</div>
        </div>
      </section>

      {/* ── Stats ── */}
      <section className="py-12 border-y border-primary-900/30 bg-surface-800/50">
        <div className="max-w-5xl mx-auto px-4 grid grid-cols-2 md:grid-cols-4 gap-6">
          {stats.map((s) => (
            <div key={s.label} className="text-center">
              <div className="text-3xl font-display font-bold text-gradient">{s.value}</div>
              <div className="text-sm text-gray-500 mt-1">{s.label}</div>
            </div>
          ))}
        </div>
      </section>

      {/* ── Features ── */}
      <section className="py-24 px-4">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-display font-bold text-white mb-4">
              Everything you need to{' '}
              <span className="text-gradient">succeed</span>
            </h2>
            <p className="text-gray-400 text-lg">
              A complete AI toolkit designed for the unique challenges of rural entrepreneurship.
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {features.map((f) => (
              <div key={f.title} className="card-hover p-6 animate-fade-in">
                <div className="text-4xl mb-4">{f.icon}</div>
                <h3 className="text-lg font-display font-semibold text-white mb-2">{f.title}</h3>
                <p className="text-gray-400 text-sm leading-relaxed">{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── CTA ── */}
      <section className="py-24 px-4">
        <div className="max-w-3xl mx-auto text-center">
          <div className="card p-12">
            <h2 className="text-3xl font-display font-bold text-white mb-4">
              Ready to build your business?
            </h2>
            <p className="text-gray-400 mb-8">
              Join thousands of rural entrepreneurs making smarter decisions with AI guidance.
            </p>
            <Link to="/register" className="btn-primary text-base px-10 py-4">
              Create Free Account →
            </Link>
          </div>
        </div>
      </section>

      {/* ── Footer ── */}
      <footer className="border-t border-primary-900/30 py-8 px-4 text-center text-gray-600 text-sm">
        <p>© 2026 RuralBiz AI · Built for Rural India · Demo MVP</p>
      </footer>
    </div>
  )
}
