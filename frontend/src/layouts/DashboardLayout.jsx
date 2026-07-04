import { NavLink, Outlet } from 'react-router-dom'

function DashboardLayout({ title, links, onLogout, profileName, roleLabel }) {
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <h2>{title}</h2>
        <nav className="nav-stack">
          {links.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              className={({ isActive }) =>
                isActive ? 'nav-link nav-link-active' : 'nav-link'
              }
            >
              {link.label}
            </NavLink>
          ))}
        </nav>
      </aside>

      <main className="workspace">
        <header className="workspace-header">
          <div>
            <p className="eyebrow">Human Resource Management System</p>
            <h1>{roleLabel} Workspace</h1>
          </div>
          <div className="header-actions">
            <div className="profile-pill">
              <span>{profileName}</span>
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
  )
}

export default DashboardLayout
