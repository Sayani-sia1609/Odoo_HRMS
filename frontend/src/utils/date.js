export function toDateInputValue(date = new Date()) {
  return new Date(date).toISOString().slice(0, 10)
}

export function prettyDate(dateValue) {
  if (!dateValue) {
    return '-'
  }

  return new Date(dateValue).toLocaleDateString('en-IN', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  })
}

export function nowTime() {
  return new Date().toLocaleTimeString('en-IN', {
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  })
}

export function between(start, end) {
  const startDate = new Date(start)
  const endDate = new Date(end)
  const day = 24 * 60 * 60 * 1000
  return Math.floor((endDate - startDate) / day) + 1
}
