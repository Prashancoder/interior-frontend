import { useState } from 'react'
import { Link, NavLink, useNavigate } from 'react-router-dom'
import { homePathForRole, useAuth } from '../auth'

export default function Navbar() {
  const { user, isAuthenticated, logout } = useAuth()
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const navigate = useNavigate()

  function handleLogout() {
    logout()
    setMobileMenuOpen(false)
    navigate('/')
  }

  function closeMenu() {
    setMobileMenuOpen(false)
  }

  const roleDashboardLink = user ? homePathForRole(user.role) : '/decor'
  const roleLabel =
    user?.role === 'admin'
      ? 'Admin Portal'
      : user?.role === 'seller'
        ? 'Seller Portal'
        : 'My Designs'

  return (
    <header className="global-navbar">
      <div className="nav-container">
        <Link to="/" className="nav-logo" onClick={closeMenu}>
          <div className="logo-icon">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="m3 9 9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" />
              <polyline points="9 22 9 12 15 12 15 22" />
            </svg>
          </div>
          <div className="logo-text">
            <span>Decore<span className="logo-ai">AI</span></span>
          </div>
        </Link>

        <nav className="nav-links desktop-only">
          <NavLink to="/" end className={({ isActive }) => (isActive ? 'nav-link active' : 'nav-link')}>
            Home
          </NavLink>
          <NavLink to="/about" className={({ isActive }) => (isActive ? 'nav-link active' : 'nav-link')}>
            About
          </NavLink>
          <NavLink to="/decor" className={({ isActive }) => (isActive ? 'nav-link active' : 'nav-link')}>
            Decor AI
            <span className="nav-tag-badge">AI Design</span>
          </NavLink>
          <NavLink to="/contact" className={({ isActive }) => (isActive ? 'nav-link active' : 'nav-link')}>
            Contact
          </NavLink>
        </nav>

        <div className="nav-auth-actions desktop-only">
          {isAuthenticated ? (
            <div className="nav-user-menu">
              <div className="nav-user-info">
                <span className="user-name">{user?.name || 'User'}</span>
                <span className={`user-role-badge role-${user?.role || 'customer'}`}>
                  {user?.role || 'customer'}
                </span>
              </div>
              <Link to={roleDashboardLink} className="btn-nav-secondary">
                {roleLabel}
              </Link>
              <button type="button" className="btn-nav-ghost" onClick={handleLogout}>
                Logout
              </button>
            </div>
          ) : (
            <div className="nav-guest-actions">
              <Link to="/login" className="btn-nav-ghost">
                Login
              </Link>
              <Link to="/decor" className="btn-nav-primary">
                Design Room
              </Link>
            </div>
          )}
        </div>

        {/* Mobile Hamburger Button */}
        <button
          type="button"
          className={`hamburger-btn mobile-only ${mobileMenuOpen ? 'open' : ''}`}
          onClick={() => setMobileMenuOpen((prev) => !prev)}
          aria-label="Toggle navigation menu"
          aria-expanded={mobileMenuOpen}
        >
          <span className="hamburger-line" />
          <span className="hamburger-line" />
          <span className="hamburger-line" />
        </button>
      </div>

      {/* Mobile Drawer */}
      {mobileMenuOpen && (
        <div className="mobile-nav-drawer mobile-only">
          <nav className="mobile-nav-links">
            <NavLink to="/" end onClick={closeMenu} className={({ isActive }) => (isActive ? 'mobile-link active' : 'mobile-link')}>
              Home
            </NavLink>
            <NavLink to="/about" onClick={closeMenu} className={({ isActive }) => (isActive ? 'mobile-link active' : 'mobile-link')}>
              About
            </NavLink>
            <NavLink to="/decor" onClick={closeMenu} className={({ isActive }) => (isActive ? 'mobile-link active' : 'mobile-link')}>
              Decor AI
            </NavLink>
            <NavLink to="/contact" onClick={closeMenu} className={({ isActive }) => (isActive ? 'mobile-link active' : 'mobile-link')}>
              Contact
            </NavLink>
          </nav>

          <div className="mobile-auth-section">
            {isAuthenticated ? (
              <div className="mobile-user-details">
                <div className="mobile-user-header">
                  <strong>{user?.name}</strong>
                  <span className="user-role-badge">{user?.role}</span>
                </div>
                <Link to={roleDashboardLink} onClick={closeMenu} className="btn-nav-secondary block-btn">
                  {roleLabel}
                </Link>
                <button type="button" className="btn-nav-ghost block-btn" onClick={handleLogout}>
                  Logout
                </button>
              </div>
            ) : (
              <div className="mobile-guest-buttons">
                <Link to="/login" onClick={closeMenu} className="btn-nav-ghost block-btn">
                  Login / Register
                </Link>
                <Link to="/decor" onClick={closeMenu} className="btn-nav-primary block-btn">
                  Start Room Design
                </Link>
              </div>
            )}
          </div>
        </div>
      )}
    </header>
  )
}
