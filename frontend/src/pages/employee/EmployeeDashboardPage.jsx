import { Link } from 'react-router-dom'
import StatCard from '../../components/common/StatCard'
import StatusBadge from '../../components/common/StatusBadge'
import { useHRMS } from '../../hooks/useHRMS'

function EmployeeDashboardPage() {
  const { currentEmployee, attendance, leaveRequests, currentUser } = useHRMS()

  const ownAttendance = attendance.filter(
    (item) => item.employeeId === currentUser?.employeeId,
  )
  const ownLeaves = leaveRequests.filter(
    (item) => item.employeeId === currentUser?.employeeId,
  )
  const pendingLeaves = ownLeaves.filter((item) => item.status === 'Pending')
  const recentAlerts = ownLeaves.slice(0, 3)

  return (
    <div className="content-grid">
      <section className="panel">
        <h2>Hello, {currentEmployee?.fullName ?? 'Employee'}</h2>
        <p className="muted">Every workday, perfectly aligned.</p>

        <div className="stats-grid">
          <StatCard title="Attendance Entries" value={ownAttendance.length} helper="Daily and weekly view" />
          <StatCard title="Leave Requests" value={ownLeaves.length} helper="Track approvals" />
          <StatCard title="Pending Approvals" value={pendingLeaves.length} helper="Needs admin review" />
        </div>
      </section>

      <section className="panel">
        <h2>Quick Access</h2>
        <div className="inline-actions">
          <Link className="btn btn-outline" to="/employee/profile">
            Profile
          </Link>
          <Link className="btn btn-outline" to="/employee/attendance">
            Attendance
          </Link>
          <Link className="btn btn-outline" to="/employee/leave">
            Leave Requests
          </Link>
          <Link className="btn btn-outline" to="/employee/payroll">
            Payroll
          </Link>
        </div>
      </section>

      <section className="panel">
        <h2>Recent Activity / Alerts</h2>
        {recentAlerts.length === 0 ? (
          <p className="muted">No recent leave activity.</p>
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th>Type</th>
                <th>Date Range</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {recentAlerts.map((item) => (
                <tr key={item.id}>
                  <td>{item.type}</td>
                  <td>
                    {item.startDate} to {item.endDate}
                  </td>
                  <td>
                    <StatusBadge status={item.status} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
    </div>
  )
}

export default EmployeeDashboardPage
