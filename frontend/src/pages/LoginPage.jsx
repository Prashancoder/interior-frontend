import { useState } from 'react'
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom'
import { homePathForRole, useAuth } from '../auth'

export default function LoginPage() {
  const { login, register, isAuthenticated, user } = useAuth()
  const location = useLocation()
  const navigate = useNavigate()
  const isRegister = location.pathname === '/register'

  const [form, setForm] = useState({
    name: '',
    email: '',
    password: '',
    role: 'customer',
    business_name: '',
    phone: '',
  })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  if (isAuthenticated && user) {
    const fromPath = location.state?.from
    if (fromPath && fromPath !== '/login' && fromPath !== '/register') {
      return <Navigate to={fromPath} replace />
    }
    return <Navigate to={homePathForRole(user.role)} replace />
  }

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      if (isRegister) {
        const payload = {
          name: form.name,
          email: form.email,
          password: form.password,
          role: form.role,
        }
        if (form.role === 'seller') {
          payload.business_name = form.business_name || form.name
          payload.phone = form.phone || undefined
        }
        const newUser = await register(payload)
        navigate(homePathForRole(newUser.role))
      } else {
        const loggedUser = await login({ email: form.email, password: form.password })
        const target = location.state?.from || homePathForRole(loggedUser.role)
        navigate(target)
      }
    } catch (err) {
      setError(err.message || 'Authentication failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="auth-page-wrapper">
      <div className="auth-card">
        <div className="auth-card-head">
          <Link to="/" className="back-home-link">
            ← Back to Home
          </Link>
          <div className="auth-brand-logo">
            <div className="logo-icon">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="m3 9 9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" />
                <polyline points="9 22 9 12 15 12 15 22" />
              </svg>
            </div>
            <span>Decore<span className="logo-ai">AI</span></span>
          </div>
          <h1>{isRegister ? 'Create Your Account' : 'Welcome Back'}</h1>
          <p className="muted">
            {isRegister
              ? 'Join as a Customer to save designs, or as a Seller to list products.'
              : 'Sign in to access your saved interior designs and seller catalog.'}
          </p>
        </div>

        {error && <div className="alert-box error">{error}</div>}

        <form onSubmit={handleSubmit} className="auth-form">
          {isRegister && (
            <>
              <div className="form-field">
                <label htmlFor="auth-name">Your Full Name</label>
                <input
                  id="auth-name"
                  type="text"
                  value={form.name}
                  onChange={(e) => setForm({ ...form, name: e.target.value })}
                  placeholder="e.g. Priya Sharma"
                  required
                />
              </div>

              <div className="form-field">
                <label htmlFor="auth-role">Account Type</label>
                <select
                  id="auth-role"
                  value={form.role}
                  onChange={(e) => setForm({ ...form, role: e.target.value })}
                >
                  <option value="customer">Customer (AI Interior Designer)</option>
                  <option value="seller">Seller (Furniture Store & Catalog)</option>
                  <option value="admin">Administrator (Platform Management)</option>
                </select>
              </div>

              {form.role === 'seller' && (
                <div className="form-row-2">
                  <div className="form-field">
                    <label htmlFor="auth-biz">Business / Store Name</label>
                    <input
                      id="auth-biz"
                      type="text"
                      value={form.business_name}
                      onChange={(e) => setForm({ ...form, business_name: e.target.value })}
                      placeholder="e.g. Heritage Teak Furnishings"
                    />
                  </div>
                  <div className="form-field">
                    <label htmlFor="auth-phone">Business Phone</label>
                    <input
                      id="auth-phone"
                      type="tel"
                      value={form.phone}
                      onChange={(e) => setForm({ ...form, phone: e.target.value })}
                      placeholder="+91 9876543210"
                    />
                  </div>
                </div>
              )}
            </>
          )}

          <div className="form-field">
            <label htmlFor="auth-email">Email Address</label>
            <input
              id="auth-email"
              type="email"
              value={form.email}
              onChange={(e) => setForm({ ...form, email: e.target.value })}
              placeholder="name@example.com"
              required
            />
          </div>

          <div className="form-field">
            <label htmlFor="auth-password">Password</label>
            <input
              id="auth-password"
              type="password"
              value={form.password}
              onChange={(e) => setForm({ ...form, password: e.target.value })}
              placeholder="••••••••"
              required
              minLength={6}
            />
          </div>

          <button type="submit" className="btn-primary block-btn" disabled={loading}>
            {loading ? 'Please wait...' : isRegister ? 'Create Account' : 'Sign In'}
          </button>
        </form>

        <div className="auth-card-footer">
          {isRegister ? (
            <p>
              Already have an account?{' '}
              <Link to="/login" className="auth-toggle-link">
                Sign in here
              </Link>
            </p>
          ) : (
            <p>
              Don’t have an account yet?{' '}
              <Link to="/register" className="auth-toggle-link">
                Register now
              </Link>
            </p>
          )}
        </div>
      </div>
    </div>
  )
}
