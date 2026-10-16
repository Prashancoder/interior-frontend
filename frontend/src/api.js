const TOKEN_KEY = 'decore_token'
const USER_KEY = 'decore_user'

export function getStoredToken() {
  return localStorage.getItem(TOKEN_KEY) || ''
}

export function getStoredUser() {
  try {
    const raw = localStorage.getItem(USER_KEY)
    return raw ? JSON.parse(raw) : null
  } catch {
    return null
  }
}

export function storeSession(token, user) {
  if (token) localStorage.setItem(TOKEN_KEY, token)
  else localStorage.removeItem(TOKEN_KEY)
  if (user) localStorage.setItem(USER_KEY, JSON.stringify(user))
  else localStorage.removeItem(USER_KEY)
}

export function clearSession() {
  localStorage.removeItem(TOKEN_KEY)
  localStorage.removeItem(USER_KEY)
}

function formatDetail(detail) {
  if (!detail) return 'Request failed'
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) {
    return detail
      .map((item) => item.msg || item.message || JSON.stringify(item))
      .join(' ')
  }
  if (typeof detail === 'object') {
    return detail.message || JSON.stringify(detail)
  }
  return String(detail)
}

export class ApiError extends Error {
  constructor(status, message) {
    super(message)
    this.status = status
  }
}

export async function apiRequest(path, options = {}) {
  const token = getStoredToken()
  const headers = { ...(options.headers || {}) }

  if (token && !headers.Authorization) {
    headers.Authorization = `Bearer ${token}`
  }

  if (options.body && !(options.body instanceof FormData) && !headers['Content-Type']) {
    headers['Content-Type'] = 'application/json'
  }

  const res = await fetch(path, { ...options, headers })
  const contentType = res.headers.get('content-type') || ''
  const data = contentType.includes('application/json')
    ? await res.json().catch(() => ({}))
    : await res.text()

  if (!res.ok) {
    const message = formatDetail(data?.detail || data?.message || data) || `HTTP ${res.status}`
    const error = new ApiError(res.status, message)
    if (res.status === 401 && typeof window !== 'undefined') {
      window.dispatchEvent(new CustomEvent('decore:unauthorized'))
    }
    throw error
  }

  return data
}

export function assetUrl(path) {
  if (!path) return ''
  if (path.startsWith('http')) return path
  return `/${path.replace(/^\/+/, '')}`
}

export function formatINR(value) {
  const n = Number(value) || 0
  return `₹${n.toLocaleString('en-IN')}`
}

export const authApi = {
  login: (payload) =>
    apiRequest('/api/auth/login', { method: 'POST', body: JSON.stringify(payload) }),
  register: (payload) =>
    apiRequest('/api/auth/register', { method: 'POST', body: JSON.stringify(payload) }),
  me: () => apiRequest('/api/auth/me'),
}

export const sellerApi = {
  stats: async () => {
    try {
      return await apiRequest('/api/seller/stats')
    } catch (err) {
      if (err.status === 404) {
        return apiRequest('/api/seller/dashboard/stats')
      }
      throw err
    }
  },
  listProducts: (params = {}) => {
    const query = new URLSearchParams()
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') query.set(key, value)
    })
    const suffix = query.toString() ? `?${query.toString()}` : ''
    return apiRequest(`/api/seller/products${suffix}`)
  },
  getProduct: (productId) => apiRequest(`/api/seller/products/${productId}`),
  createProduct: (formData) =>
    apiRequest('/api/seller/products', { method: 'POST', body: formData }),
  updateProduct: (productId, formData) =>
    apiRequest(`/api/seller/products/${productId}`, { method: 'PUT', body: formData }),
  deleteProduct: (productId) =>
    apiRequest(`/api/seller/products/${productId}`, { method: 'DELETE' }),
}
