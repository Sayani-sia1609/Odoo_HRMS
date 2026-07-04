import { useLayoutEffect, useRef } from 'react'
import { Link } from 'react-router-dom'
import gsap from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'
import StatCard from '../../components/common/StatCard'
import StatusBadge from '../../components/common/StatusBadge'
import { useHRMS } from '../../hooks/useHRMS'
import { prettyDate, toDateInputValue } from '../../utils/date'

gsap.registerPlugin(ScrollTrigger)

const weekdayLabels = ['MO', 'TU', 'WE', 'TH', 'FR', 'SA', 'SU']
const pulseValues = [58, 72, 49, 84, 66, 91, 73]

function buildCalendar(date) {
  const year = date.getFullYear()
  const month = date.getMonth()
  const firstDayOffset = (new Date(year, month, 1).getDay() + 6) % 7
  const totalDays = new Date(year, month + 1, 0).getDate()
  const cells = []

  for (let index = 0; index < firstDayOffset; index += 1) {
    cells.push({ id: `blank-${index}`, blank: true })
  }

  for (let day = 1; day <= totalDays; day += 1) {
    const current = new Date(year, month, day)
    cells.push({
      id: current.toISOString(),
      label: day,
      isToday: current.toDateString() === date.toDateString(),
      isWeekend: current.getDay() === 0 || current.getDay() === 6,
    })
  }

  return cells
}

function AdminDashboardPage() {
  const scope = useRef(null)
  const { employees, attendance, leaveRequests, payroll, currentUser, currentEmployee } = useHRMS()

  const today = toDateInputValue()
  const todayAttendance = attendance.filter((item) => item.date === today)
  const pendingLeaves = leaveRequests.filter((item) => item.status === 'Pending')
  const payrollReadyCount = Object.keys(payroll).length
  const calendarDate = new Date()
  const calendarCells = buildCalendar(calendarDate)
  const selectedEmployee = currentEmployee ?? employees[0] ?? null
  const adminName = currentUser?.fullName ?? 'Administrator'

  const employeeRows = employees.slice(0, 4).map((employee) => {
    const attendanceRecord = todayAttendance.find(
      (item) => item.employeeId === employee.employeeId,
    )

    return {
      ...employee,
      status: attendanceRecord?.status ?? 'No log',
    }
  })

  const agenda = [
    { time: '09:00', title: 'Payroll sync', detail: 'Finance and HR review the final export.' },
    { time: '11:15', title: 'Approval queue', detail: `${pendingLeaves.length} leave request${pendingLeaves.length === 1 ? '' : 's'} waiting.` },
    { time: '14:30', title: 'Onboarding slot', detail: 'New joiner checklist and access handoff.' },
  ]

  useLayoutEffect(() => {
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      return undefined
    }

    const context = gsap.context(() => {
      gsap.set('.reveal-card', { opacity: 0, y: 24 })

      gsap.from('.dashboard-hero, .metrics-row', {
        opacity: 0,
        y: 18,
        duration: 0.8,
        ease: 'power3.out',
        stagger: 0.12,
      })

      ScrollTrigger.batch('.reveal-card', {
        start: 'top 82%',
        once: true,
        interval: 0.1,
        onEnter: (batch) => {
          gsap.to(batch, {
            opacity: 1,
            y: 0,
            duration: 0.75,
            stagger: 0.08,
            ease: 'power2.out',
            overwrite: true,
          })
        },
      })
    }, scope)

    return () => context.revert()
  }, [])

  return (
    <div ref={scope} className="content-grid admin-dashboard">
      <section className="panel dashboard-hero hero-panel">
        <div className="hero-copy">
          <p className="eyebrow">Operations overview</p>
          <h2>Good morning, {adminName}</h2>
          <p className="muted">
            Keep attendance, leave approvals and payroll in one calm workspace with a clear
            status view and fast access to the day&apos;s priorities.
          </p>

          <div className="inline-actions hero-actions">
            <Link className="btn btn-primary" to="/admin/leaves">
              Review leave queue
            </Link>
            <Link className="btn btn-outline" to="/admin/employees">
              Open employee directory
            </Link>
          </div>
        </div>

        <div className="hero-summary">
          <div className="hero-chip">{prettyDate(calendarDate)}</div>
          <div className="hero-scorecard">
            <span>Attendance marked</span>
            <strong>{todayAttendance.length}</strong>
          </div>
          <div className="hero-scorecard hero-scorecard-dark">
            <span>Pending approvals</span>
            <strong>{pendingLeaves.length}</strong>
          </div>
          <div className="hero-scorecard hero-scorecard-soft">
            <span>Payroll profiles</span>
            <strong>{payrollReadyCount}</strong>
          </div>
        </div>
      </section>

      <section className="stats-grid metrics-row">
        <StatCard title="Employees" value={employees.length} helper="Active employee profiles" />
        <StatCard title="Today Attendance" value={todayAttendance.length} helper="Marked records" />
        <StatCard title="Pending Leaves" value={pendingLeaves.length} helper="Approval queue" />
        <StatCard title="Payroll Ready" value={payrollReadyCount} helper="Updated salary files" />
      </section>

      <section className="dashboard-grid">
        <article className="panel chart-panel reveal-card">
          <div className="panel-heading">
            <div>
              <p className="eyebrow">Weekly pulse</p>
              <h3>Attendance rhythm</h3>
            </div>
            <span className="pill">This week</span>
          </div>

          <div className="mini-chart" aria-label="Weekly attendance chart">
            {pulseValues.map((value, index) => (
              <div key={weekdayLabels[index]} className="mini-bar">
                <span className="mini-bar-track">
                  <span className="mini-bar-fill" style={{ height: `${value}%` }} />
                </span>
                <small>{weekdayLabels[index]}</small>
              </div>
            ))}
          </div>

          <div className="chart-notes">
            <div>
              <strong>Strongest day</strong>
              <span>Thursday recorded the highest check-in rate.</span>
            </div>
            <div>
              <strong>Focus area</strong>
              <span>Review Monday and Tuesday for late arrivals.</span>
            </div>
          </div>
        </article>

        <article className="panel reveal-card">
          <div className="panel-heading">
            <div>
              <p className="eyebrow">Employee queue</p>
              <h3>Today&apos;s roster</h3>
            </div>
            <span className="pill pill-neutral">Live</span>
          </div>

          <div className="roster-list">
            {employeeRows.map((employee) => (
              <div key={employee.employeeId} className="roster-row">
                <div className="roster-avatar" aria-hidden="true">
                  {employee.fullName
                    .split(' ')
                    .map((part) => part[0])
                    .slice(0, 2)
                    .join('')}
                </div>
                <div className="roster-copy">
                  <strong>{employee.fullName}</strong>
                  <span>{employee.department}</span>
                </div>
                <StatusBadge status={employee.status} />
              </div>
            ))}
          </div>

          <div className="subtle-card">
            <p className="eyebrow">Quick action</p>
            <p className="muted">Use the employee list to switch the active profile and update details.</p>
          </div>
        </article>

        <article className="panel reveal-card">
          <div className="panel-heading">
            <div>
              <p className="eyebrow">Calendar</p>
              <h3>{calendarDate.toLocaleString('en-US', { month: 'long', year: 'numeric' })}</h3>
            </div>
            <span className="pill">Plan ahead</span>
          </div>

          <div className="calendar-shell">
            <div className="calendar-weekdays">
              {weekdayLabels.map((label) => (
                <span key={label}>{label}</span>
              ))}
            </div>
            <div className="calendar-grid">
              {calendarCells.map((cell) =>
                cell.blank ? (
                  <div key={cell.id} className="calendar-cell calendar-cell-empty" aria-hidden="true" />
                ) : (
                  <div
                    key={cell.id}
                    className={`calendar-cell ${cell.isToday ? 'calendar-cell-today' : ''} ${cell.isWeekend ? 'calendar-cell-muted' : ''}`.trim()}
                  >
                    <span>{cell.label}</span>
                  </div>
                ),
              )}
            </div>
          </div>
        </article>

        <article className="panel detail-panel reveal-card">
          <div className="panel-heading">
            <div>
              <p className="eyebrow">Selected profile</p>
              <h3>Visit details</h3>
            </div>
            <span className="pill pill-soft">Active</span>
          </div>

          {selectedEmployee ? (
            <div className="profile-summary">
              <div className="profile-summary__header">
                <div className="profile-badge">
                  {selectedEmployee.fullName
                    .split(' ')
                    .map((part) => part[0])
                    .slice(0, 2)
                    .join('')}
                </div>
                <div>
                  <strong>{selectedEmployee.fullName}</strong>
                  <p className="muted">{selectedEmployee.jobTitle}</p>
                </div>
              </div>

              <dl className="key-value key-value-condensed">
                <div>
                  <dt>Employee ID</dt>
                  <dd>{selectedEmployee.employeeId}</dd>
                </div>
                <div>
                  <dt>Department</dt>
                  <dd>{selectedEmployee.department}</dd>
                </div>
                <div>
                  <dt>Joined</dt>
                  <dd>{prettyDate(selectedEmployee.joinDate)}</dd>
                </div>
                <div>
                  <dt>Contact</dt>
                  <dd>{selectedEmployee.email}</dd>
                </div>
              </dl>
            </div>
          ) : (
            <p className="muted">Select an employee to view their details.</p>
          )}

          <div className="agenda-list">
            {agenda.map((item) => (
              <div key={item.time} className="agenda-item">
                <span className="agenda-time">{item.time}</span>
                <div>
                  <strong>{item.title}</strong>
                  <p className="muted">{item.detail}</p>
                </div>
              </div>
            ))}
          </div>

          <div className="inline-actions">
            <Link className="btn btn-outline" to="/admin/attendance">
              Attendance records
            </Link>
            <Link className="btn btn-outline" to="/admin/payroll">
              Payroll control
            </Link>
          </div>
        </article>
      </section>
    </div>
  )
}

export default AdminDashboardPage
