import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useHRMS } from '../../hooks/useHRMS'

function LoginPage() {
  const navigate = useNavigate()
  const { signIn, verifyEmail } = useHRMS()

  const [form, setForm] = useState({ email: '', password: '' })
  const [feedback, setFeedback] = useState('')
  const [feedbackType, setFeedbackType] = useState('neutral')

  const onSubmit = (event) => {
    event.preventDefault()
    const result = signIn(form)

    if (!result.ok) {
      setFeedback(result.message)
      setFeedbackType('danger')
      return
    }

    setFeedback('Signed in successfully.')
    setFeedbackType('success')

    if (result.role === 'admin') {
      navigate('/admin/dashboard', { replace: true })
    } else {
      navigate('/employee/dashboard', { replace: true })
    }
  }

  const onVerify = () => {
    const result = verifyEmail(form.email)
    setFeedback(result.message)
    setFeedbackType(result.ok ? 'success' : 'danger')
  }

  return (
    <main className="auth-page">
      <section className="auth-card auth-card--split">
        <aside className="auth-aside">
          <p className="eyebrow">Human Resource Management System</p>
          <h1>Coordinate work without the clutter.</h1>
          <p className="muted">
            A focused workspace for attendance, leave, payroll and employee records with a calm,
            professional finish.
          </p>

          <div className="auth-metrics">
            <div>
              <strong>Live roster</strong>
              <span>Monitor active employees in real time.</span>
            </div>
            <div>
              <strong>Fast approvals</strong>
              <span>Review leave and payroll without switching screens.</span>
            </div>
            <div>
              <strong>Secure access</strong>
              <span>Verify accounts before sign-in and keep roles separate.</span>
            </div>
          </div>

          <p className="auth-note">Demo users: admin@hrms.com / Admin@123 and rohit@hrms.com / Employee@123</p>
        </aside>

        <section className="auth-form-panel">
          <p className="eyebrow">Welcome back</p>
          <h2>Sign in to HRMS</h2>
          <p className="muted">Use your email and password to access the workspace.</p>

          <form className="form-grid auth-form" onSubmit={onSubmit}>
            <label>
              Email
              <input
                type="email"
                value={form.email}
                onChange={(event) =>
                  setForm((prev) => ({ ...prev, email: event.target.value }))
                }
                placeholder="you@hrms.com"
                required
              />
            </label>

            <label>
              Password
              <input
                type="password"
                value={form.password}
                onChange={(event) =>
                  setForm((prev) => ({ ...prev, password: event.target.value }))
                }
                placeholder="Enter password"
                required
              />
            </label>

            <div className="inline-actions">
              <button type="submit" className="btn btn-primary">
                Sign In
              </button>
              <button type="button" className="btn btn-outline" onClick={onVerify}>
                Verify Email
              </button>
            </div>
          </form>

          <p className="muted auth-cta">
            Don&apos;t have an account? <Link to="/signup">Create one</Link>
          </p>

          <p className={`feedback feedback-${feedbackType}`}>{feedback || 'Sign in to continue.'}</p>
        </section>
      </section>
    </main>
  )
}

export default LoginPage
