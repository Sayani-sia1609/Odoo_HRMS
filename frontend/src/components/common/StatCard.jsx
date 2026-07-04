function StatCard({ title, value, helper }) {
  return (
    <article className="stat-card">
      <p className="stat-title">{title}</p>
      <p className="stat-value">{value}</p>
      {helper ? <p className="stat-helper">{helper}</p> : null}
    </article>
  )
}

export default StatCard
