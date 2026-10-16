import { NavLink } from 'react-router-dom'
import { useAuth } from '../auth'

const SELLER_LINKS = [
  { to: '/seller/dashboard', label: 'Dashboard' },
  { to: '/seller/products', label: 'Products' },
  { to: '/seller/products/new', label: 'Add Product' },
  { to: '/seller/orders', label: 'Orders' },
  { to: '/seller/profile', label: 'Store Profile' },
]

const ADMIN_LINKS = [
  { to: '/admin/dashboard', label: 'Dashboard' },
  { to: '/admin/products', label: 'Products' },
  { to: '/admin/sellers', label: 'Sellers' },
  { to: '/admin/customers', label: 'Customers' },
  { to: '/admin/orders', label: 'Orders' },
  { to: '/admin/settings', label: 'Settings' },
]

export default function Sidebar({ role, open, onClose }) {
  const { user, logout } = useAuth()
  const links = role === 'admin' ? ADMIN_LINKS : SELLER_LINKS

  return (
    <aside className={`sidebar ${open ? 'open' : ''}`}>
      <div className="sidebar-brand">
        <strong>DECORE AI</strong>
        <span>{role === 'admin' ? 'Admin' : 'Seller'} Console</span>
      </div>
      <nav>
        {links.map((link) => (
          <NavLink key={link.to} to={link.to} onClick={onClose} end={link.to === '/seller/products' || link.to.endsWith('dashboard')}>
            {link.label}
          </NavLink>
        ))}
      </nav>
      <div className="sidebar-user">
        <p>{user?.name}</p>
        <p className="muted">{user?.email}</p>
        <button type="button" className="btn ghost" onClick={logout}>
          Logout
        </button>
      </div>
    </aside>
  )
}
