import { Link } from 'react-router-dom'
import StatCard from '../../components/common/StatCard'
import StatusBadge from '../../components/common/StatusBadge'
import { useHRMS } from '../../hooks/useHRMS'

function AdminDashboardPage() {
  const { employees, attendance, leaveRequests } = useHRMS()

  const pendingLeaves = leaveRequests.filter((item) => item.status === 'Pending')
  const today = new Date().toISOString().slice(0, 10)
  const todayAttendance = attendance.filter((item) => item.date === today)

  return (
    <div className="content-grid">
      <section className="panel">
        <h2>Admin / HR Dashboard</h2>
        <p className="muted">Manage employees, attendance, leave approvals and payroll from one workspace.</p>

        <div className="stats-grid">
          <StatCard title="Employees" value={employees.length} helper="Active employee profiles" />
          <StatCard title="Today Attendance" value={todayAttendance.length} helper="Marked records" />
          <StatCard title="Pending Leaves" value={pendingLeaves.length} helper="Approval queue" />
        </div>
      </section>

      <section className="panel">
        <h2>Quick Access</h2>
        <div className="inline-actions">
          <Link className="btn btn-outline" to="/admin/employees">
            Employee List
          </Link>
          <Link className="btn btn-outline" to="/admin/attendance">
            Attendance Records
          </Link>
          <Link className="btn btn-outline" to="/admin/leaves">
            Leave Approvals
          </Link>
          <Link className="btn btn-outline" to="/admin/payroll">
            Payroll Control
          </Link>
        </div>
      </section>

      <section className="panel">
        <h2>Recent Pending Leave Requests</h2>
        {pendingLeaves.length === 0 ? (
          <p className="muted">No pending leave approvals.</p>
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th>Employee ID</th>
                <th>Type</th>
                <th>Range</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {pendingLeaves.slice(0, 5).map((item) => (
                <tr key={item.id}>
                  <td>{item.employeeId}</td>
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

export default AdminDashboardPage
