import { useMemo, useState } from 'react'
import { useHRMS } from '../../hooks/useHRMS'

function AdminPayrollPage() {
  const { employees, payroll, updatePayroll } = useHRMS()
  const [employeeId, setEmployeeId] = useState(employees[0]?.employeeId ?? '')
  const [message, setMessage] = useState('')

  const initial = payroll[employeeId] ?? {
    basic: 0,
    hra: 0,
    bonus: 0,
    deductions: 0,
  }

  const [form, setForm] = useState(initial)

  const currentSheet = useMemo(() => payroll[employeeId] ?? initial, [payroll, employeeId])

  const syncFromSheet = (id) => {
    const next = payroll[id] ?? {
      basic: 0,
      hra: 0,
      bonus: 0,
      deductions: 0,
    }
    setForm(next)
  }

  const onSubmit = (event) => {
    event.preventDefault()
    const payload = Object.fromEntries(
      Object.entries(form).map(([key, value]) => [key, Number(value)]),
    )
    const result = updatePayroll({ employeeId, payload })
    setMessage(result.message)
  }

  return (
    <section className="panel">
      <h2>Admin Payroll Control</h2>

      <label>
        Select Employee
        <select
          value={employeeId}
          onChange={(event) => {
            const nextId = event.target.value
            setEmployeeId(nextId)
            syncFromSheet(nextId)
          }}
        >
          {employees.map((employee) => (
            <option key={employee.employeeId} value={employee.employeeId}>
              {employee.fullName} ({employee.employeeId})
            </option>
          ))}
        </select>
      </label>

      <form className="form-grid form-inline" onSubmit={onSubmit}>
        {['basic', 'hra', 'bonus', 'deductions'].map((field) => (
          <label key={field}>
            {field.toUpperCase()}
            <input
              type="number"
              value={form[field]}
              onChange={(event) =>
                setForm((prev) => ({ ...prev, [field]: event.target.value }))
              }
            />
          </label>
        ))}
        <button type="submit" className="btn btn-primary">
          Update Payroll
        </button>
      </form>

      {message ? <p className="feedback feedback-neutral">{message}</p> : null}

      <p className="muted">Last Updated: {currentSheet.updatedAt || '-'}</p>
    </section>
  )
}

export default AdminPayrollPage
