import { useMemo, useState } from 'react'
import StatusBadge from '../../components/common/StatusBadge'
import { useHRMS } from '../../hooks/useHRMS'
import { between, prettyDate, toDateInputValue } from '../../utils/date'

function EmployeeLeavePage() {
  const { applyLeave, leaveRequests, attendance, currentUser } = useHRMS()
  const [form, setForm] = useState({
    type: 'Paid',
    startDate: toDateInputValue(),
    endDate: toDateInputValue(),
    remarks: '',
  })
  const [message, setMessage] = useState('')

  const ownLeaves = useMemo(
    () =>
      leaveRequests
        .filter((item) => item.employeeId === currentUser?.employeeId)
        .sort((a, b) => new Date(b.appliedOn) - new Date(a.appliedOn)),
    [leaveRequests, currentUser],
  )

  const monthStatus = useMemo(() => {
    const map = new Map()
    const now = new Date()
    const month = now.getMonth()
    const year = now.getFullYear()

    attendance
      .filter(
        (item) =>
          item.employeeId === currentUser?.employeeId &&
          new Date(item.date).getMonth() === month &&
          new Date(item.date).getFullYear() === year,
      )
      .forEach((item) => map.set(new Date(item.date).getDate(), item.status))

    return map
  }, [attendance, currentUser])

  const onSubmit = (event) => {
    event.preventDefault()
    const result = applyLeave(form)
    setMessage(result.message)

    if (result.ok) {
      setForm((prev) => ({ ...prev, remarks: '' }))
    }
  }

  const daysInMonth = new Date(new Date().getFullYear(), new Date().getMonth() + 1, 0).getDate()

  return (
    <div className="content-grid content-grid-two">
      <section className="panel">
        <h2>Apply for Leave</h2>
        <form className="form-grid" onSubmit={onSubmit}>
          <label>
            Leave Type
            <select
              value={form.type}
              onChange={(event) => setForm((prev) => ({ ...prev, type: event.target.value }))}
            >
              <option>Paid</option>
              <option>Sick</option>
              <option>Unpaid</option>
            </select>
          </label>

          <label>
            Start Date
            <input
              type="date"
              value={form.startDate}
              onChange={(event) =>
                setForm((prev) => ({ ...prev, startDate: event.target.value }))
              }
              required
            />
          </label>

          <label>
            End Date
            <input
              type="date"
              value={form.endDate}
              onChange={(event) => setForm((prev) => ({ ...prev, endDate: event.target.value }))}
              required
            />
          </label>

          <label>
            Remarks
            <textarea
              value={form.remarks}
              onChange={(event) => setForm((prev) => ({ ...prev, remarks: event.target.value }))}
              rows={4}
              required
            />
          </label>

          <button type="submit" className="btn btn-primary">
            Submit Leave Request
          </button>
        </form>

        {message ? <p className="feedback feedback-neutral">{message}</p> : null}
      </section>

      <section className="panel">
        <h2>Attendance Markers (Monthly)</h2>
        <div className="calendar-grid">
          {Array.from({ length: daysInMonth }).map((_, index) => {
            const day = index + 1
            const status = monthStatus.get(day)
            return (
              <div key={day} className="calendar-cell">
                <span>{day}</span>
                <small>{status ? status[0] : '-'}</small>
              </div>
            )
          })}
        </div>
      </section>

      <section className="panel panel-full">
        <h2>Leave Request Status</h2>
        <table className="data-table">
          <thead>
            <tr>
              <th>Type</th>
              <th>Range</th>
              <th>Days</th>
              <th>Status</th>
              <th>Comment</th>
            </tr>
          </thead>
          <tbody>
            {ownLeaves.map((row) => (
              <tr key={row.id}>
                <td>{row.type}</td>
                <td>
                  {prettyDate(row.startDate)} to {prettyDate(row.endDate)}
                </td>
                <td>{between(row.startDate, row.endDate)}</td>
                <td>
                  <StatusBadge status={row.status} />
                </td>
                <td>{row.adminComment || '-'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </div>
  )
}

export default EmployeeLeavePage
