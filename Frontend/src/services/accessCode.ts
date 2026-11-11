// Only relevant when the backend has ACCESS_CODE set (see Backend/.env) —
// gates public demo deployments against strangers running up the AI provider
// bill. Session-scoped so it doesn't linger in the browser after the tab closes.
const STORAGE_KEY = 'campaignStudio.accessCode'

export function getStoredAccessCode(): string | null {
  return sessionStorage.getItem(STORAGE_KEY)
}

export function setStoredAccessCode(code: string): void {
  sessionStorage.setItem(STORAGE_KEY, code)
}

export function clearStoredAccessCode(): void {
  sessionStorage.removeItem(STORAGE_KEY)
}
