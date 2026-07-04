import { useMemo, useState } from 'react'
import StatusBadge from '../../components/common/StatusBadge'
import { useHRMS } from '../../hooks/useHRMS'

function AdminLeaveApprovalsPage() {
  const { leaveRequests, employees, reviewLeave } = useHRMS()
  const [commentById, setCommentById] = useState({})
  const [message, setMessage] = useState('')

  const rows = useMemo(
    () =>
      leaveRequests
        .map((row) => {
          const employee = employees.find((item) => item.employeeId === row.employeeId)
          return {
            ...row,
            employeeName: employee?.fullName ?? row.employeeId,
          }
        })
        .sort((a, b) => new Date(b.appliedOn) - new Date(a.appliedOn)),
    [leaveRequests, employees],
  )

  const submitReview = (requestId, status) => {
    const result = reviewLeave({
      requestId,
      status,
      adminComment: commentById[requestId] ?? '',
    })
    setMessage(result.message)
  }

  return (
    <section className="panel">
      <h2>Leave Approval Workflow</h2>
      {message ? <p className="feedback feedback-neutral">{message}</p> : null}

      <table className="data-table">
        <thead>
          <tr>
            <th>Employee</th>
            <th>Leave</th>
            <th>Remarks</th>
            <th>Status</th>
            <th>Comment</th>
            <th>Action</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.id}>
              <td>{row.employeeName}</td>
              <td>
                {row.type} ({row.startDate} to {row.endDate})
              </td>
              <td>{row.remarks}</td>
              <td>
                <StatusBadge status={row.status} />
              </td>
              <td>
                <input
                  type="text"
                  value={commentById[row.id] ?? row.adminComment}
                  onChange={(event) =>
                    setCommentById((prev) => ({ ...prev, [row.id]: event.target.value }))
                  }
                />
              </td>
              <td>
                <div className="inline-actions">
                  <button
                    type="button"
                    className="btn btn-primary"
                    onClick={() => submitReview(row.id, 'Approved')}
                  >
                    Approve
                  </button>
                  <button
                    type="button"
                    className="btn btn-outline"
                    onClick={() => submitReview(row.id, 'Rejected')}
                  >
                    Reject
                  </button>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  )
}

export default AdminLeaveApprovalsPage
