import { useEffect, useState } from 'react'
import { useHRMS } from '../../hooks/useHRMS'

function EmployeeProfilePage() {
  const { currentEmployee, payroll, updateProfile } = useHRMS()
  const [form, setForm] = useState({
    phone: '',
    address: '',
    profilePicture: '',
  })
  const [message, setMessage] = useState('')

  useEffect(() => {
    setForm({
      phone: currentEmployee?.phone ?? '',
      address: currentEmployee?.address ?? '',
      profilePicture: currentEmployee?.profilePicture ?? '',
    })
  }, [currentEmployee])

  if (!currentEmployee) {
    return <p>Profile data is not available.</p>
  }

  const salary = payroll[currentEmployee.employeeId] ?? {
    basic: 0,
    hra: 0,
    bonus: 0,
    deductions: 0,
  }

  const onSubmit = (event) => {
    event.preventDefault()
    const result = updateProfile({ payload: form })
    setMessage(result.message)
  }

  return (
    <div className="content-grid content-grid-two">
      <section className="panel">
        <h2>Profile Details</h2>
        <dl className="key-value">
          <div>
            <dt>Employee ID</dt>
            <dd>{currentEmployee.employeeId}</dd>
          </div>
          <div>
            <dt>Name</dt>
            <dd>{currentEmployee.fullName}</dd>
          </div>
          <div>
            <dt>Email</dt>
            <dd>{currentEmployee.email}</dd>
          </div>
          <div>
            <dt>Department</dt>
            <dd>{currentEmployee.department}</dd>
          </div>
          <div>
            <dt>Designation</dt>
            <dd>{currentEmployee.jobTitle}</dd>
          </div>
          <div>
            <dt>Documents</dt>
            <dd>{currentEmployee.documents.join(', ') || 'No documents uploaded'}</dd>
          </div>
        </dl>
      </section>

      <section className="panel">
        <h2>Edit Contact Fields</h2>
        <form className="form-grid" onSubmit={onSubmit}>
          <label>
            Phone
            <input
              type="text"
              value={form.phone}
              onChange={(event) => setForm((prev) => ({ ...prev, phone: event.target.value }))}
            />
          </label>

          <label>
            Address
            <input
              type="text"
              value={form.address}
              onChange={(event) => setForm((prev) => ({ ...prev, address: event.target.value }))}
            />
          </label>

          <label>
            Profile Picture URL
            <input
              type="text"
              value={form.profilePicture}
              onChange={(event) =>
                setForm((prev) => ({ ...prev, profilePicture: event.target.value }))
              }
            />
          </label>

          <button type="submit" className="btn btn-primary">
            Save Changes
          </button>
        </form>

        {message ? <p className="feedback feedback-neutral">{message}</p> : null}
      </section>

      <section className="panel panel-full">
        <h2>Salary Structure Read-only</h2>
        <div className="payroll-grid">
          <div>
            <span>Basic</span>
            <strong>{salary.basic}</strong>
          </div>
          <div>
            <span>HRA</span>
            <strong>{salary.hra}</strong>
          </div>
          <div>
            <span>Bonus</span>
            <strong>{salary.bonus}</strong>
          </div>
          <div>
            <span>Deductions</span>
            <strong>{salary.deductions}</strong>
          </div>
        </div>
      </section>
    </div>
  )
}

export default EmployeeProfilePage
