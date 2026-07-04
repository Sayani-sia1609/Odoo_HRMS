import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useHRMS } from '../../hooks/useHRMS'

function SignupPage() {
  const navigate = useNavigate()
  const { signUp } = useHRMS()

  const [form, setForm] = useState({
    employeeId: '',
    fullName: '',
    email: '',
    password: '',
    role: 'employee',
  })
  const [feedback, setFeedback] = useState('')
  const [feedbackType, setFeedbackType] = useState('neutral')

  const updateField = (event) => {
    const { name, value } = event.target
    setForm((prev) => ({ ...prev, [name]: value }))
  }

  const onSubmit = (event) => {
    event.preventDefault()
    const result = signUp(form)
    setFeedback(result.message)
    setFeedbackType(result.ok ? 'success' : 'danger')

    if (result.ok) {
      setTimeout(() => navigate('/login'), 900)
    }
  }

  return (
    <main className="auth-page">
      <section className="auth-card">
        <p className="eyebrow">Secure Authentication</p>
        <h1>Create HRMS Account</h1>
        <p className="muted">Register with employee ID, role, email and strong password.</p>

        <form className="form-grid" onSubmit={onSubmit}>
          <label>
            Employee ID
            <input
              type="text"
              name="employeeId"
              value={form.employeeId}
              onChange={updateField}
              placeholder="EMP1020"
              required
            />
          </label>

          <label>
            Full Name
            <input
              type="text"
              name="fullName"
              value={form.fullName}
              onChange={updateField}
              placeholder="Your full name"
              required
            />
          </label>

          <label>
            Email
            <input
              type="email"
              name="email"
              value={form.email}
              onChange={updateField}
              placeholder="you@hrms.com"
              required
            />
          </label>

          <label>
            Password
            <input
              type="password"
              name="password"
              value={form.password}
              onChange={updateField}
              placeholder="At least 8 chars with uppercase, lowercase, number, symbol"
              required
            />
          </label>

          <label>
            Role
            <select name="role" value={form.role} onChange={updateField}>
              <option value="employee">Employee</option>
              <option value="admin">Admin / HR Officer</option>
            </select>
          </label>

          <button type="submit" className="btn btn-primary">
            Sign Up
          </button>
        </form>

        {feedback ? (
          <p className={`feedback feedback-${feedbackType}`}>{feedback}</p>
        ) : null}

        <p className="muted">
          Already registered? <Link to="/login">Sign In</Link>
        </p>
      </section>
    </main>
  )
}

export default SignupPage
