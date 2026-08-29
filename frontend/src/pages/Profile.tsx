/**
 * Profile — Phase 10 update.
 * Added: Hindi language option, Simple Language Mode toggle, react-i18next labels,
 *        language sync with languageService on save.
 */
import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useAuth } from '../context/AuthContext'
import { authService } from '../services/authService'
import type { User } from '../services/authService'
import { languageService, accessibilityService } from '../services/languageService'
import type { LanguageCode } from '../types/language'

const STATES = [
  'Andhra Pradesh', 'Telangana', 'Karnataka', 'Tamil Nadu', 'Maharashtra',
  'Gujarat', 'Rajasthan', 'Uttar Pradesh', 'Bihar', 'West Bengal',
  'Madhya Pradesh', 'Odisha', 'Jharkhand', 'Chhattisgarh', 'Other',
]

export default function Profile() {
  const { user, refreshUser } = useAuth()
  const { t } = useTranslation()
  const [form, setForm] = useState<Partial<User>>({
    full_name: user?.full_name ?? '',
    phone: user?.phone ?? '',
    preferred_language: user?.preferred_language ?? 'en',
    state: user?.state ?? '',
    district: user?.district ?? '',
    village_town: user?.village_town ?? '',
    available_capital: user?.available_capital ?? undefined,
    skills: user?.skills ?? '',
    experience_years: user?.experience_years ?? undefined,
    business_interests: user?.business_interests ?? '',
    monthly_income_goal: user?.monthly_income_goal ?? undefined,
  })
  const [simpleLanguage, setSimpleLanguage] = useState(false)
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)
  const [error, setError] = useState('')

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>
  ) => {
    const { name, value, type } = e.target
    setForm((prev) => ({
      ...prev,
      [name]: type === 'number' ? (value === '' ? undefined : Number(value)) : value,
    }))
    setError('')
    setSaved(false)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setSaving(true)
    setError('')
    try {
      await authService.updateProfile(form)
      // Phase 10 — sync language preference locally + to backend
      if (form.preferred_language) {
        await languageService.changeLanguage(form.preferred_language as LanguageCode, true)
      }
      // Phase 10 — sync simple language mode
      try {
        await accessibilityService.setSimpleLanguage(simpleLanguage)
      } catch { /* ok if fails */ }
      await refreshUser()
      setSaved(true)
      setTimeout(() => setSaved(false), 3000)
    } catch (err: unknown) {
      setError(
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
          'Failed to save profile. Please try again.'
      )
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="max-w-3xl mx-auto px-4 py-8 animate-fade-in">
      <div className="mb-8">
        <h1 className="text-3xl font-display font-bold text-white">{t('profile.title')}</h1>
        <p className="text-gray-400 mt-1">{t('profile.subtitle')}</p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6" id="profile-form">
        {/* ── Basic Info ── */}
        <div className="card p-6 space-y-5">
          <h2 className="text-lg font-display font-semibold text-white border-b border-primary-900/30 pb-3">
            Basic Information
          </h2>

          <div className="grid sm:grid-cols-2 gap-5">
            <div>
              <label htmlFor="p-name" className="label">Full Name</label>
              <input id="p-name" name="full_name" type="text" className="input" value={form.full_name ?? ''} onChange={handleChange} placeholder="Ravi Kumar" />
            </div>
            <div>
              <label htmlFor="p-phone" className="label">Phone Number</label>
              <input id="p-phone" name="phone" type="tel" className="input" value={form.phone ?? ''} onChange={handleChange} placeholder="+91 98765 43210" />
            </div>
          </div>

          {/* Phase 10 — Language preference with all 3 options */}
          <div>
            <label htmlFor="p-lang" className="label">{t('profile.language')}</label>
            <select id="p-lang" name="preferred_language" className="input" value={form.preferred_language ?? 'en'} onChange={handleChange}>
              <option value="en">🇬🇧 English</option>
              <option value="hi">🇮🇳 हिन्दी (Hindi)</option>
              <option value="te">🇮🇳 తెలుగు (Telugu)</option>
            </select>
          </div>

          {/* Phase 10 — Simple Language Mode */}
          <div className="flex items-start gap-3 p-4 rounded-xl bg-surface-700/20 border border-surface-600/20">
            <input
              id="p-simple-lang"
              type="checkbox"
              checked={simpleLanguage}
              onChange={e => setSimpleLanguage(e.target.checked)}
              className="mt-0.5 w-4 h-4 accent-primary-500 cursor-pointer"
            />
            <div>
              <label htmlFor="p-simple-lang" className="text-sm font-medium text-white cursor-pointer">
                📝 {t('profile.simpleLanguage')}
              </label>
              <p className="text-xs text-gray-500 mt-0.5">{t('profile.simpleLanguageHint')}</p>
            </div>
          </div>
        </div>

        {/* ── Location ── */}
        <div className="card p-6 space-y-5">
          <h2 className="text-lg font-display font-semibold text-white border-b border-primary-900/30 pb-3">
            {t('profile.location')}
          </h2>

          <div className="grid sm:grid-cols-3 gap-5">
            <div>
              <label htmlFor="p-state" className="label">State</label>
              <select id="p-state" name="state" className="input" value={form.state ?? ''} onChange={handleChange}>
                <option value="">Select state</option>
                {STATES.map((s) => <option key={s} value={s}>{s}</option>)}
              </select>
            </div>
            <div>
              <label htmlFor="p-district" className="label">District</label>
              <input id="p-district" name="district" type="text" className="input" value={form.district ?? ''} onChange={handleChange} placeholder="e.g. Guntur" />
            </div>
            <div>
              <label htmlFor="p-village" className="label">Village / Town</label>
              <input id="p-village" name="village_town" type="text" className="input" value={form.village_town ?? ''} onChange={handleChange} placeholder="e.g. Tenali" />
            </div>
          </div>
        </div>

        {/* ── Business Profile ── */}
        <div className="card p-6 space-y-5">
          <h2 className="text-lg font-display font-semibold text-white border-b border-primary-900/30 pb-3">
            Business Profile
          </h2>

          <div className="grid sm:grid-cols-2 gap-5">
            <div>
              <label htmlFor="p-capital" className="label">{t('profile.capital')} (₹)</label>
              <input
                id="p-capital"
                name="available_capital"
                type="number"
                min={0}
                step={1000}
                className="input"
                value={form.available_capital ?? ''}
                onChange={handleChange}
                placeholder="200000"
              />
            </div>
            <div>
              <label htmlFor="p-goal" className="label">{t('profile.incomeGoal')} (₹)</label>
              <input
                id="p-goal"
                name="monthly_income_goal"
                type="number"
                min={0}
                step={500}
                className="input"
                value={form.monthly_income_goal ?? ''}
                onChange={handleChange}
                placeholder="30000"
              />
            </div>
          </div>

          <div>
            <label htmlFor="p-experience" className="label">{t('profile.experience')}</label>
            <input
              id="p-experience"
              name="experience_years"
              type="number"
              min={0}
              max={50}
              className="input"
              value={form.experience_years ?? ''}
              onChange={handleChange}
              placeholder="3"
            />
          </div>

          <div>
            <label htmlFor="p-skills" className="label">{t('profile.skills')}</label>
            <textarea
              id="p-skills"
              name="skills"
              rows={2}
              className="input resize-none"
              value={form.skills ?? ''}
              onChange={handleChange}
              placeholder="e.g. tailoring, mobile repair, cooking, farming…"
            />
          </div>

          <div>
            <label htmlFor="p-interests" className="label">{t('profile.businessInterests')}</label>
            <textarea
              id="p-interests"
              name="business_interests"
              rows={2}
              className="input resize-none"
              value={form.business_interests ?? ''}
              onChange={handleChange}
              placeholder="e.g. dairy farming, kirana store, tailoring shop…"
            />
          </div>
        </div>

        {/* Error / Success */}
        {error && (
          <div className="rounded-lg bg-red-900/30 border border-red-700/40 px-4 py-3 text-sm text-red-400">
            {error}
          </div>
        )}
        {saved && (
          <div className="rounded-lg bg-primary-900/30 border border-primary-700/40 px-4 py-3 text-sm text-primary-400">
            ✓ Profile saved successfully
          </div>
        )}

        <button id="save-profile" type="submit" disabled={saving} className="btn-primary w-full py-3.5">
          {saving ? (
            <span className="flex items-center gap-2">
              <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              {t('common.loading')}
            </span>
          ) : (
            t('common.save') + ' Profile'
          )}
        </button>
      </form>
    </div>
  )
}
