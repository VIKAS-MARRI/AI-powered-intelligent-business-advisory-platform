import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { authService } from '../services/authService'

export default function Register() {
  const { login } = useAuth()
  const navigate = useNavigate()

  const [form, setForm] = useState({
    full_name: '',
    email: '',
    phone: '',
    password: '',
    confirm_password: '',
    preferred_language: 'en',
  })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }))
    setError('')
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (form.password !== form.confirm_password) {
      setError('Passwords do not match.')
      return
    }
    if (form.password.length < 8) {
      setError('Password must be at least 8 characters.')
      return
    }

    setLoading(true)
    setError('')
    try {
      // Register
      await authService.register({
        email: form.email,
        password: form.password,
        full_name: form.full_name || undefined,
        phone: form.phone || undefined,
        preferred_language: form.preferred_language,
      })
      // Auto-login
      const token = await authService.login({ email: form.email, password: form.password })
      await login(token.access_token)
      navigate('/dashboard', { replace: true })
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
        'Registration failed. Please try again.'
      setError(msg)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-[calc(100vh-4rem)] flex items-center justify-center px-4 py-12">
      <div className="w-full max-w-lg animate-slide-up">
        <div className="card p-8">
          {/* Header */}
          <div className="text-center mb-8">
            <div className="w-16 h-16 rounded-2xl bg-primary-800/60 border border-primary-700/50 flex items-center justify-center mx-auto mb-4 shadow-glow-sm">
              <span className="text-3xl">🚀</span>
            </div>
            <h1 className="text-2xl font-display font-bold text-white">Create your account</h1>
            <p className="text-gray-400 mt-1 text-sm">Start your entrepreneurship journey today</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-5" id="register-form">
            {/* Full name */}
            <div>
              <label htmlFor="reg-name" className="label">Full Name</label>
              <input
                id="reg-name"
                name="full_name"
                type="text"
                autoComplete="name"
                value={form.full_name}
                onChange={handleChange}
                className="input"
                placeholder="Ravi Kumar"
              />
            </div>

            {/* Email */}
            <div>
              <label htmlFor="reg-email" className="label">
                Email address <span className="text-red-400">*</span>
              </label>
              <input
                id="reg-email"
                name="email"
                type="email"
                autoComplete="email"
                required
                value={form.email}
                onChange={handleChange}
                className="input"
                placeholder="ravi@example.com"
              />
            </div>

            {/* Phone */}
            <div>
              <label htmlFor="reg-phone" className="label">Phone Number</label>
              <input
                id="reg-phone"
                name="phone"
                type="tel"
                autoComplete="tel"
                value={form.phone}
                onChange={handleChange}
                className="input"
                placeholder="+91 98765 43210"
              />
            </div>

            {/* Language */}
            <div>
              <label htmlFor="reg-lang" className="label">Preferred Language</label>
              <select
                id="reg-lang"
                name="preferred_language"
                value={form.preferred_language}
                onChange={handleChange}
                className="input"
              >
                <option value="en">English</option>
                <option value="te">Telugu (తెలుగు)</option>
              </select>
            </div>

            {/* Password row */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label htmlFor="reg-password" className="label">
                  Password <span className="text-red-400">*</span>
                </label>
                <input
                  id="reg-password"
                  name="password"
                  type="password"
                  autoComplete="new-password"
                  required
                  value={form.password}
                  onChange={handleChange}
                  className="input"
                  placeholder="Min 8 chars"
                />
              </div>
              <div>
                <label htmlFor="reg-confirm" className="label">
                  Confirm <span className="text-red-400">*</span>
                </label>
                <input
                  id="reg-confirm"
                  name="confirm_password"
                  type="password"
                  autoComplete="new-password"
                  required
                  value={form.confirm_password}
                  onChange={handleChange}
                  className="input"
                  placeholder="Repeat password"
                />
              </div>
            </div>

            {/* Error */}
            {error && (
              <div className="rounded-lg bg-red-900/30 border border-red-700/40 px-4 py-3 text-sm text-red-400">
                {error}
              </div>
            )}

            <button
              id="register-submit"
              type="submit"
              disabled={loading}
              className="btn-primary w-full py-3.5"
            >
              {loading ? (
                <span className="flex items-center gap-2">
                  <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  Creating account…
                </span>
              ) : (
                'Create Free Account'
              )}
            </button>
          </form>

          <p className="mt-6 text-center text-sm text-gray-500">
            Already have an account?{' '}
            <Link to="/login" className="text-primary-400 hover:text-primary-300 font-medium">
              Sign in
            </Link>
          </p>
        </div>
      </div>
    </div>
  )
}
