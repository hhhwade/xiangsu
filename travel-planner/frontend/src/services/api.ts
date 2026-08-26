import { demoPlan } from '../data/sample'
import { destinationSuggestions } from '../data/sample'
import type { DestinationSuggestion, PlanResponse, TravelForm } from '../types'

const configuredBase = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/$/, '')
// A Vite dev server remains reviewable without a separate API process. Production
// always calls same-origin /api, which Nginx proxies to FastAPI.
const standaloneDemo = import.meta.env.DEV && !configuredBase
const planEndpoint = `${configuredBase}/api/v1/plans`

function asBackendPayload(form: TravelForm) {
  return {
    destination: form.destination,
    duration: { value: form.duration, unit: form.durationUnit },
    preferences: form.preferences,
    transportMode: form.transportMode,
    dailyHours: form.dailyHours,
    budget: form.budgetMin || form.budgetMax ? { min: form.budgetMin, max: form.budgetMax } : undefined,
    groupSize: {
      adults: form.adults,
      children: form.children,
      elderly: form.elderly,
      accessible: form.accessible,
    },
    startDate: form.startDate || undefined,
    specialNeeds: form.specialNeeds || undefined,
  }
}

/** Creates a route through FastAPI; Vite-only review mode uses the bundled demo plan. */
export async function createPlan(form: TravelForm): Promise<PlanResponse> {
  if (standaloneDemo) {
    await new Promise((resolve) => window.setTimeout(resolve, 700))
    return demoPlan(form)
  }

  const response = await fetch(planEndpoint, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(asBackendPayload(form)),
  })

  if (!response.ok) {
    const detail = await response.text()
    throw new Error(detail || '路线服务暂时不可用，请稍后重试。')
  }

  return response.json() as Promise<PlanResponse>
}

export async function autocompleteDestination(keyword: string): Promise<DestinationSuggestion[]> {
  const normalized = keyword.trim()
  const local = destinationSuggestions
    .filter((item) => item.name.includes(normalized))
    .map((item) => ({ name: item.name, district: item.detail }))
  if (!normalized || standaloneDemo) return local
  try {
    const response = await fetch(`${configuredBase}/api/v1/destinations/autocomplete?q=${encodeURIComponent(normalized)}`)
    if (!response.ok) return local
    const remote = await response.json() as DestinationSuggestion[]
    return remote.length ? remote : local
  } catch {
    return local
  }
}
