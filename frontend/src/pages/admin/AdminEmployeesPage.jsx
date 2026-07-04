import { useEffect, useState } from 'react'
import { useHRMS } from '../../hooks/useHRMS'

function AdminEmployeesPage() {
  const {
    employees,
    activeEmployeeId,
    setActiveEmployeeId,
    currentEmployee,
    updateProfile,
  } = useHRMS()

  const [form, setForm] = useState({
    fullName: '',
    email: '',
    phone: '',
    address: '',
    jobTitle: '',
    department: '',
    joinDate: '',
    profilePicture: '',
  })
  const [message, setMessage] = useState('')

  useEffect(() => {
    if (!currentEmployee) {
      return
    }

    setForm({
      fullName: currentEmployee.fullName,
      email: currentEmployee.email,
      phone: currentEmployee.phone,
      address: currentEmployee.address,
      jobTitle: currentEmployee.jobTitle,
      department: currentEmployee.department,
      joinDate: currentEmployee.joinDate,
      profilePicture: currentEmployee.profilePicture,
    })
  }, [currentEmployee])

  const onSubmit = (event) => {
    event.preventDefault()
    const result = updateProfile({ employeeId: activeEmployeeId, payload: form })
    setMessage(result.message)
  }

  return (
    <div className="content-grid content-grid-two">
      <section className="panel">
        <h2>Employee List</h2>
        <table className="data-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Name</th>
              <th>Department</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {employees.map((employee) => (
              <tr key={employee.employeeId}>
                <td>{employee.employeeId}</td>
                <td>{employee.fullName}</td>
                <td>{employee.department}</td>
                <td>
                  <button
                    type="button"
                    className="btn btn-outline"
                    onClick={() => setActiveEmployeeId(employee.employeeId)}
                  >
                    {employee.employeeId === activeEmployeeId ? 'Selected' : 'Manage'}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      <section className="panel">
        <h2>Edit Employee Details</h2>
        {currentEmployee ? (
          <form className="form-grid" onSubmit={onSubmit}>
            {Object.entries(form).map(([field, value]) => (
              <label key={field}>
                {field}
                <input
                  type={field === 'joinDate' ? 'date' : 'text'}
                  value={value}
                  onChange={(event) =>
                    setForm((prev) => ({ ...prev, [field]: event.target.value }))
                  }
                />
              </label>
            ))}
            <button type="submit" className="btn btn-primary">
              Save Employee
            </button>
          </form>
        ) : (
          <p className="muted">Select an employee to edit.</p>
        )}

        {message ? <p className="feedback feedback-neutral">{message}</p> : null}
      </section>
    </div>
  )
}

export default AdminEmployeesPage
