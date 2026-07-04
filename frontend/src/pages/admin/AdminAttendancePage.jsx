import { useMemo, useState } from 'react'
import StatusBadge from '../../components/common/StatusBadge'
import { useHRMS } from '../../hooks/useHRMS'
import { toDateInputValue } from '../../utils/date'

function AdminAttendancePage() {
  const { attendance, employees, setAttendanceStatus } = useHRMS()
  const [form, setForm] = useState({
    employeeId: employees[0]?.employeeId ?? '',
    date: toDateInputValue(),
    status: 'Present',
  })
  const [message, setMessage] = useState('')

  const rows = useMemo(
    () =>
      attendance
        .map((item) => {
          const employee = employees.find((emp) => emp.employeeId === item.employeeId)
          return {
            ...item,
            employeeName: employee?.fullName ?? item.employeeId,
          }
        })
        .sort((a, b) => new Date(b.date) - new Date(a.date)),
    [attendance, employees],
  )

  const onSubmit = (event) => {
    event.preventDefault()
    const result = setAttendanceStatus(form)
    setMessage(result.message)
  }

  return (
    <section className="panel">
      <h2>Attendance Records</h2>

      <form className="form-grid form-inline" onSubmit={onSubmit}>
        <label>
          Employee
          <select
            value={form.employeeId}
            onChange={(event) => setForm((prev) => ({ ...prev, employeeId: event.target.value }))}
          >
            {employees.map((employee) => (
              <option key={employee.employeeId} value={employee.employeeId}>
                {employee.fullName} ({employee.employeeId})
              </option>
            ))}
          </select>
        </label>

        <label>
          Date
          <input
            type="date"
            value={form.date}
            onChange={(event) => setForm((prev) => ({ ...prev, date: event.target.value }))}
          />
        </label>

        <label>
          Status
          <select
            value={form.status}
            onChange={(event) => setForm((prev) => ({ ...prev, status: event.target.value }))}
          >
            <option>Present</option>
            <option>Absent</option>
            <option>Half-day</option>
            <option>Leave</option>
          </select>
        </label>

        <button type="submit" className="btn btn-primary">
          Save Status
        </button>
      </form>

      {message ? <p className="feedback feedback-neutral">{message}</p> : null}

      <table className="data-table">
        <thead>
          <tr>
            <th>Date</th>
            <th>Employee</th>
            <th>Status</th>
            <th>Check In</th>
            <th>Check Out</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.id}>
              <td>{row.date}</td>
              <td>{row.employeeName}</td>
              <td>
                <StatusBadge status={row.status} />
              </td>
              <td>{row.checkIn || '-'}</td>
              <td>{row.checkOut || '-'}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  )
}

export default AdminAttendancePage
