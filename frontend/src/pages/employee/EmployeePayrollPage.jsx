import { useMemo } from 'react'
import { useHRMS } from '../../hooks/useHRMS'

function EmployeePayrollPage() {
  const { currentUser, payroll } = useHRMS()

  const sheet = payroll[currentUser?.employeeId] ?? {
    basic: 0,
    hra: 0,
    bonus: 0,
    deductions: 0,
    updatedAt: '-',
  }

  const { gross, net } = useMemo(() => {
    const grossValue = Number(sheet.basic) + Number(sheet.hra) + Number(sheet.bonus)
    return {
      gross: grossValue,
      net: grossValue - Number(sheet.deductions),
    }
  }, [sheet])

  return (
    <section className="panel">
      <h2>Payroll Visibility</h2>
      <p className="muted">Payroll data is read-only for employees.</p>

      <div className="payroll-grid">
        <div>
          <span>Basic</span>
          <strong>{sheet.basic}</strong>
        </div>
        <div>
          <span>HRA</span>
          <strong>{sheet.hra}</strong>
        </div>
        <div>
          <span>Bonus</span>
          <strong>{sheet.bonus}</strong>
        </div>
        <div>
          <span>Deductions</span>
          <strong>{sheet.deductions}</strong>
        </div>
      </div>

      <div className="pay-summary">
        <p>
          Gross Salary: <strong>{gross}</strong>
        </p>
        <p>
          Net Salary: <strong>{net}</strong>
        </p>
        <p className="muted">Last Updated: {sheet.updatedAt}</p>
      </div>
    </section>
  )
}

export default EmployeePayrollPage
