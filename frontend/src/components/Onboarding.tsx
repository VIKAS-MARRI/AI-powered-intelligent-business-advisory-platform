/**
 * Phase 11 — Section 11: Guided Onboarding
 * 8-step skippable wizard that collects entrepreneur profile data.
 * Shows a progress indicator and saves to the backend on completion.
 */
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { authService } from '../services/authService'
import { useAuth } from '../context/AuthContext'

interface OnboardingData {
  full_name:           string
  skills:              string
  available_capital:   string
  business_interests:  string
  state:               string
  district:            string
  monthly_income_goal: string
  experience_years:    string
}

const EMPTY: OnboardingData = {
  full_name: '', skills: '', available_capital: '', business_interests: '',
  state: '', district: '', monthly_income_goal: '', experience_years: '',
}

const STATES = [
  'Andhra Pradesh', 'Telangana', 'Karnataka', 'Tamil Nadu', 'Maharashtra',
  'Gujarat', 'Rajasthan', 'Uttar Pradesh', 'Bihar', 'West Bengal',
  'Madhya Pradesh', 'Odisha', 'Jharkhand', 'Chhattisgarh', 'Other',
]

const BUSINESS_SUGGESTIONS = [
  'Tailoring', 'Dairy Farming', 'Kirana Store', 'Mobile Repair',
  'Tiffin Service', 'Agro-Processing', 'Beauty Parlour', 'Transport',
]

interface Step {
  id:          number
  icon:        string
  title:       string
  subtitle:    string
}

const STEPS: Step[] = [
  { id: 1, icon: '👋', title: 'Welcome to RuralBiz AI',      subtitle: "Let's set up your entrepreneur profile" },
  { id: 2, icon: '🙋', title: 'Tell Us About Yourself',       subtitle: 'Your name helps us personalise advice' },
  { id: 3, icon: '🛠️', title: 'Your Skills',                  subtitle: 'What are you good at?' },
  { id: 4, icon: '💰', title: 'Available Capital',            subtitle: 'How much can you invest?' },
  { id: 5, icon: '💼', title: 'Business Interests',          subtitle: 'What kind of business interests you?' },
  { id: 6, icon: '📍', title: 'Your Location',               subtitle: 'Helps us give local market advice' },
  { id: 7, icon: '🎯', title: 'Income Goal',                 subtitle: 'Monthly income you want to earn' },
  { id: 8, icon: '🚀', title: "You're All Set!",             subtitle: 'Get your personalized AI recommendations' },
]

interface Props {
  onComplete?: () => void
  onSkip?:     () => void
}

export default function Onboarding({ onComplete, onSkip }: Props) {
  const { refreshUser } = useAuth()
  const navigate        = useNavigate()
  const [step, setStep] = useState(1)
  const [data, setData] = useState<OnboardingData>(EMPTY)
  const [saving, setSaving] = useState(false)
  const [error, setError]   = useState('')

  const total = STEPS.length
  const progress = ((step - 1) / (total - 1)) * 100
  const currentStep = STEPS[step - 1]

  const set = (field: keyof OnboardingData, value: string) =>
    setData(prev => ({ ...prev, [field]: value }))

  const next = () => {
    if (step < total) setStep(s => s + 1)
  }

  const back = () => {
    if (step > 1) setStep(s => s - 1)
  }

  const handleSkip = () => {
    onSkip ? onSkip() : navigate('/dashboard')
  }

  const handleFinish = async () => {
    setSaving(true)
    setError('')
    try {
      await authService.updateProfile({
        full_name:           data.full_name || undefined,
        skills:              data.skills || undefined,
        available_capital:   data.available_capital ? Number(data.available_capital) : undefined,
        business_interests:  data.business_interests || undefined,
        state:               data.state || undefined,
        district:            data.district || undefined,
        monthly_income_goal: data.monthly_income_goal ? Number(data.monthly_income_goal) : undefined,
        experience_years:    data.experience_years ? Number(data.experience_years) : undefined,
      })
      await refreshUser()
      onComplete ? onComplete() : navigate('/recommendations')
    } catch {
      setError('Could not save profile. You can update it later from Settings.')
      // Still allow proceeding
      setTimeout(() => {
        onComplete ? onComplete() : navigate('/dashboard')
      }, 2000)
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-surface-900 px-4 py-8">
      <div className="w-full max-w-lg">

        {/* Progress bar */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs text-gray-500">Step {step} of {total}</span>
            <button onClick={handleSkip} className="text-xs text-gray-600 hover:text-gray-400 transition-colors">
              Skip setup →
            </button>
          </div>
          <div className="h-1.5 bg-surface-700 rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-primary-500 to-primary-400 rounded-full transition-all duration-500"
              style={{ width: `${progress}%` }}
            />
          </div>
          {/* Step dots */}
          <div className="flex justify-between mt-2">
            {STEPS.map(s => (
              <div
                key={s.id}
                className={`w-1.5 h-1.5 rounded-full transition-colors duration-300 ${
                  s.id <= step ? 'bg-primary-400' : 'bg-surface-600'
                }`}
              />
            ))}
          </div>
        </div>

        {/* Card */}
        <div className="card p-8 animate-fade-in">
          <div className="text-center mb-8">
            <div className="text-5xl mb-4" aria-hidden="true">{currentStep.icon}</div>
            <h1 className="text-2xl font-display font-bold text-white mb-1">{currentStep.title}</h1>
            <p className="text-sm text-gray-400">{currentStep.subtitle}</p>
          </div>

          {/* Step content */}
          <div className="space-y-4 mb-8">
            {step === 1 && (
              <div className="space-y-3 text-center">
                <p className="text-gray-300 text-sm leading-relaxed">
                  RuralBiz AI helps rural entrepreneurs like you find the right business,
                  plan your investment, and access government support.
                </p>
                <div className="grid grid-cols-3 gap-3 mt-6">
                  {[['💼','Business Ideas'],['📊','Financial Plans'],['🏛️','Govt Schemes']].map(([icon, label]) => (
                    <div key={label} className="rounded-xl bg-surface-700/30 p-3 text-center">
                      <div className="text-2xl mb-1">{icon}</div>
                      <p className="text-[11px] text-gray-400">{label}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {step === 2 && (
              <div>
                <label htmlFor="ob-name" className="label">Your Name</label>
                <input
                  id="ob-name"
                  type="text" value={data.full_name} onChange={e => set('full_name', e.target.value)}
                  className="input" placeholder="e.g. Priya Devi"
                  autoFocus
                />
              </div>
            )}

            {step === 3 && (
              <div>
                <label htmlFor="ob-skills" className="label">Your Skills</label>
                <textarea
                  id="ob-skills"
                  value={data.skills} onChange={e => set('skills', e.target.value)}
                  className="input resize-none" rows={2}
                  placeholder="e.g. tailoring, cooking, mobile repair…"
                />
                <div className="flex flex-wrap gap-1.5 mt-3">
                  {['Tailoring','Farming','Cooking','Mobile Repair','Beauty','Transport','Dairy','Trading'].map(s => (
                    <button key={s} type="button"
                      onClick={() => set('skills', data.skills ? `${data.skills}, ${s}` : s)}
                      className="text-xs px-2 py-1 rounded-full border border-surface-600/40 text-gray-500 hover:text-white hover:border-primary-500/50 transition-all">
                      + {s}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {step === 4 && (
              <div>
                <label htmlFor="ob-capital" className="label">Available Capital (₹)</label>
                <input
                  id="ob-capital"
                  type="number" min={0} step={5000}
                  value={data.available_capital} onChange={e => set('available_capital', e.target.value)}
                  className="input" placeholder="e.g. 100000"
                />
                <div className="flex flex-wrap gap-1.5 mt-3">
                  {[['₹25k','25000'],['₹50k','50000'],['₹1L','100000'],['₹2L','200000'],['₹5L','500000']].map(([label, val]) => (
                    <button key={val} type="button" onClick={() => set('available_capital', val)}
                      className={`text-xs px-3 py-1 rounded-full border transition-all ${
                        data.available_capital === val
                          ? 'border-primary-500 text-primary-300 bg-primary-900/30'
                          : 'border-surface-600/40 text-gray-500 hover:text-white'
                      }`}>
                      {label}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {step === 5 && (
              <div>
                <label htmlFor="ob-interests" className="label">Business Interests</label>
                <textarea
                  id="ob-interests"
                  value={data.business_interests} onChange={e => set('business_interests', e.target.value)}
                  className="input resize-none" rows={2}
                  placeholder="e.g. tailoring shop, dairy farming, kirana store…"
                />
                <div className="flex flex-wrap gap-1.5 mt-3">
                  {BUSINESS_SUGGESTIONS.map(b => (
                    <button key={b} type="button"
                      onClick={() => set('business_interests', data.business_interests ? `${data.business_interests}, ${b}` : b)}
                      className="text-xs px-2 py-1 rounded-full border border-surface-600/40 text-gray-500 hover:text-white hover:border-primary-500/50 transition-all">
                      + {b}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {step === 6 && (
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label htmlFor="ob-state" className="label">State</label>
                  <select id="ob-state" value={data.state} onChange={e => set('state', e.target.value)} className="input">
                    <option value="">Select…</option>
                    {STATES.map(s => <option key={s} value={s}>{s}</option>)}
                  </select>
                </div>
                <div>
                  <label htmlFor="ob-district" className="label">District</label>
                  <input id="ob-district" type="text" value={data.district}
                    onChange={e => set('district', e.target.value)}
                    className="input" placeholder="e.g. Guntur" />
                </div>
              </div>
            )}

            {step === 7 && (
              <div>
                <label htmlFor="ob-goal" className="label">Monthly Income Goal (₹)</label>
                <input
                  id="ob-goal"
                  type="number" min={0} step={1000}
                  value={data.monthly_income_goal} onChange={e => set('monthly_income_goal', e.target.value)}
                  className="input" placeholder="e.g. 20000"
                />
                <div className="flex flex-wrap gap-1.5 mt-3">
                  {[['₹10k','10000'],['₹15k','15000'],['₹25k','25000'],['₹50k','50000']].map(([label, val]) => (
                    <button key={val} type="button" onClick={() => set('monthly_income_goal', val)}
                      className={`text-xs px-3 py-1 rounded-full border transition-all ${
                        data.monthly_income_goal === val
                          ? 'border-primary-500 text-primary-300 bg-primary-900/30'
                          : 'border-surface-600/40 text-gray-500 hover:text-white'
                      }`}>
                      {label}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {step === 8 && (
              <div className="space-y-3">
                <p className="text-sm text-gray-300 text-center leading-relaxed">
                  Your profile is ready! RuralBiz AI will now generate personalized recommendations based on your inputs.
                </p>
                {/* Summary */}
                <div className="rounded-xl bg-surface-700/20 border border-surface-600/20 p-4 space-y-2">
                  {data.full_name && <div className="flex justify-between text-sm"><span className="text-gray-500">Name</span><span className="text-white">{data.full_name}</span></div>}
                  {data.available_capital && <div className="flex justify-between text-sm"><span className="text-gray-500">Capital</span><span className="text-white">₹{Number(data.available_capital).toLocaleString('en-IN')}</span></div>}
                  {data.state && <div className="flex justify-between text-sm"><span className="text-gray-500">Location</span><span className="text-white">{data.state}</span></div>}
                  {data.monthly_income_goal && <div className="flex justify-between text-sm"><span className="text-gray-500">Income Goal</span><span className="text-white">₹{Number(data.monthly_income_goal).toLocaleString('en-IN')}/mo</span></div>}
                </div>
                {error && <p className="text-xs text-red-400 text-center">{error}</p>}
              </div>
            )}
          </div>

          {/* Navigation */}
          <div className="flex gap-3">
            {step > 1 && (
              <button onClick={back} className="btn-ghost px-5 py-2.5 flex-1">
                ← Back
              </button>
            )}
            {step < total ? (
              <button onClick={next} className="btn-primary px-5 py-2.5 flex-1">
                Continue →
              </button>
            ) : (
              <button onClick={handleFinish} disabled={saving} className="btn-primary px-5 py-2.5 flex-1">
                {saving ? (
                  <span className="flex items-center justify-center gap-2">
                    <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    Saving…
                  </span>
                ) : '🚀 Get My Recommendations'}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
