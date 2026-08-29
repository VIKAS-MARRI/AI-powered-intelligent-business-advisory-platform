/** Format a number as Indian currency: ₹2,00,000 */
export function inr(amount: number): string {
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0,
  }).format(amount)
}

/** Shorten large INR amounts: ₹2L, ₹50K */
export function inrShort(amount: number): string {
  if (amount >= 100000) return `₹${(amount / 100000).toFixed(1)}L`
  if (amount >= 1000)   return `₹${(amount / 1000).toFixed(0)}K`
  return `₹${amount}`
}

export const RISK_COLORS: Record<string, string> = {
  Low:    'text-emerald-400 bg-emerald-900/30 border-emerald-700/40',
  Medium: 'text-amber-400  bg-amber-900/30  border-amber-700/40',
  High:   'text-red-400    bg-red-900/30    border-red-700/40',
}

export const RISK_DOT: Record<string, string> = {
  Low:    'bg-emerald-400',
  Medium: 'bg-amber-400',
  High:   'bg-red-400',
}
