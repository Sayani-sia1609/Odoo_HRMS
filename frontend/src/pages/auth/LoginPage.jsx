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
      <section className="auth-card">
        <p className="eyebrow">Welcome Back</p>
        <h1>Sign In to HRMS</h1>
        <p className="muted">Use your email and password to access your dashboard.</p>

        <form className="form-grid" onSubmit={onSubmit}>
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

        <p className="muted">
          Don&apos;t have an account? <Link to="/signup">Create one</Link>
        </p>

        <p className={`feedback feedback-${feedbackType}`}>Demo users: admin@hrms.com / Admin@123 and rohit@hrms.com / Employee@123</p>

        {feedback ? <p className={`feedback feedback-${feedbackType}`}>{feedback}</p> : null}
      </section>
    </main>
  )
}

export default LoginPage
