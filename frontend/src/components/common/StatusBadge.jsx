const toneByStatus = {
  Pending: 'warning',
  Approved: 'success',
  Rejected: 'danger',
  Present: 'success',
  Absent: 'danger',
  'Half-day': 'warning',
  Leave: 'neutral',
}

function StatusBadge({ status }) {
  const tone = toneByStatus[status] ?? 'neutral'
  return <span className={`status-badge status-${tone}`}>{status}</span>
}

export default StatusBadge
