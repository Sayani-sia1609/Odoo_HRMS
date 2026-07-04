import { useMemo, useState } from 'react'
import StatusBadge from '../../components/common/StatusBadge'
import { useHRMS } from '../../hooks/useHRMS'
import { toDateInputValue } from '../../utils/date'

function EmployeeAttendancePage() {
  const { attendance, currentUser, checkIn, checkOut } = useHRMS()
  const [message, setMessage] = useState('')
  const [viewMode, setViewMode] = useState('daily')

  const ownRows = useMemo(() => {
    if (!currentUser?.employeeId) {
      return []
    }

    return attendance
      .filter((item) => item.employeeId === currentUser.employeeId)
      .sort((a, b) => new Date(b.date) - new Date(a.date))
  }, [attendance, currentUser])

  const today = toDateInputValue()
  const todayEntry = ownRows.find((item) => item.date === today)

  const visibleRows =
    viewMode === 'weekly'
      ? ownRows.filter(
          (item) =>
            new Date(today).getTime() - new Date(item.date).getTime() <= 6 * 24 * 60 * 60 * 1000,
        )
      : ownRows.slice(0, 1)

  const runAction = (action) => {
    const result = action()
    setMessage(result.message)
  }

  return (
    <section className="panel">
      <div className="panel-heading">
        <h2>Attendance Tracking</h2>
        <div className="inline-actions">
          <button
            type="button"
            className={viewMode === 'daily' ? 'btn btn-outline active' : 'btn btn-outline'}
            onClick={() => setViewMode('daily')}
          >
            Daily
          </button>
          <button
            type="button"
            className={viewMode === 'weekly' ? 'btn btn-outline active' : 'btn btn-outline'}
            onClick={() => setViewMode('weekly')}
          >
            Weekly
          </button>
        </div>
      </div>

      <div className="inline-actions">
        <button type="button" className="btn btn-primary" onClick={() => runAction(checkIn)}>
          Check In
        </button>
        <button type="button" className="btn btn-outline" onClick={() => runAction(checkOut)}>
          Check Out
        </button>
      </div>

      {todayEntry ? (
        <p className="muted">
          Today: <StatusBadge status={todayEntry.status} /> {todayEntry.checkIn || '-'} to{' '}
          {todayEntry.checkOut || '-'}
        </p>
      ) : (
        <p className="muted">No attendance entry for today yet.</p>
      )}

      {message ? <p className="feedback feedback-neutral">{message}</p> : null}

      <table className="data-table">
        <thead>
          <tr>
            <th>Date</th>
            <th>Status</th>
            <th>Check In</th>
            <th>Check Out</th>
          </tr>
        </thead>
        <tbody>
          {visibleRows.map((row) => (
            <tr key={row.id}>
              <td>{row.date}</td>
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

export default EmployeeAttendancePage
