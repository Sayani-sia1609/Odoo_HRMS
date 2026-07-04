import { NavLink, Outlet } from 'react-router-dom'

function DashboardLayout({ title, links, onLogout, profileName, roleLabel }) {
  return (
    <div className="app-shell dashboard-shell">
      <div className="dashboard-frame">
        <aside className="sidebar">
          <div className="brand-stack">
            <div className="brand-lockup">
              <span className="brand-mark" aria-hidden="true">
                O
              </span>
              <div>
                <p className="eyebrow brand-eyebrow">Odoo HRMS</p>
                <h2>{title}</h2>
              </div>
            </div>
            <p className="sidebar-copy">A calm control room for attendance, leave, payroll and employee oversight.</p>
          </div>

          <nav className="nav-stack" aria-label="Primary">
            {links.map((link) => (
              <NavLink
                key={link.to}
                to={link.to}
                className={({ isActive }) =>
                  isActive ? 'nav-link nav-link-active' : 'nav-link'
                }
              >
                <span className="nav-link-label">{link.label}</span>
                <span className="nav-link-caret" aria-hidden="true">
                  ›
                </span>
              </NavLink>
            ))}
          </nav>

          <div className="sidebar-footer">
            <div className="sidebar-footer-card">
              <p className="eyebrow">Session</p>
              <strong>{profileName}</strong>
              <span>{roleLabel}</span>
            </div>
            <button type="button" className="btn btn-ghost sidebar-logout" onClick={onLogout}>
              Logout
            </button>
          </div>
        </aside>

        <main className="workspace">
          <header className="workspace-header">
            <div className="workspace-titleblock">
              <p className="eyebrow">Human Resource Management System</p>
              <h1>{roleLabel} workspace</h1>
              <p className="muted">Operational overview, live approvals and day-to-day HR controls in one place.</p>
            </div>

            <div className="header-actions">
              <div className="header-chip" aria-label={`Signed in as ${profileName}`}>
                <span className="header-chip-label">Signed in</span>
                <strong>{profileName}</strong>
              </div>
              <button type="button" className="btn btn-outline" onClick={onLogout}>
                Logout
              </button>
            </div>
          </header>

          <section className="workspace-body">
            <Outlet />
          </section>
        </main>
      </div>
    </div>
  )
}

export default DashboardLayout
