import { useState } from 'react'
import { Outlet } from 'react-router-dom'
import Sidebar from './Sidebar'

export default function DashboardLayout({ role }) {
  const [open, setOpen] = useState(false)

  return (
    <div className="dash-shell">
      <Sidebar role={role} open={open} onClose={() => setOpen(false)} />
      {open && <button type="button" className="sidebar-scrim" aria-label="Close menu" onClick={() => setOpen(false)} />}
      <div className="dash-main">
        <header className="dash-topbar">
          <button type="button" className="btn ghost menu-btn" onClick={() => setOpen(true)}>
            Menu
          </button>
          <span>DECORE AI</span>
        </header>
        <div className="dash-content">
          <Outlet />
        </div>
      </div>
    </div>
  )
}
