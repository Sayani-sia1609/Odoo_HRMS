import { createContext, useContext, useMemo, useState } from 'react'
import {
  seedAccounts,
  seedAttendance,
  seedEmployees,
  seedLeaves,
  seedPayroll,
} from '../services/hrmsSeed'
import { nowTime, toDateInputValue } from '../utils/date'

const AuthContext = createContext(null)
const PASSWORD_REGEX = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^\w\s]).{8,}$/

const STORAGE_KEYS = {
  accounts: 'hrms.accounts',
  employees: 'hrms.employees',
  attendance: 'hrms.attendance',
  leaves: 'hrms.leaves',
  payroll: 'hrms.payroll',
  session: 'hrms.session',
}

function readStorage(key, fallback) {
  try {
    const raw = window.localStorage.getItem(key)
    return raw ? JSON.parse(raw) : fallback
  } catch {
    return fallback
  }
}

function saveStorage(key, value) {
  window.localStorage.setItem(key, JSON.stringify(value))
}

function createEmployeeFromSignup({ employeeId, fullName, email }) {
  return {
    employeeId,
    fullName,
    email,
    phone: '',
    address: '',
    profilePicture: '',
    jobTitle: 'Not Assigned',
    department: 'Not Assigned',
    joinDate: toDateInputValue(),
    documents: [],
  }
}

export function AuthProvider({ children }) {
  const [accounts, setAccounts] = useState(() =>
    readStorage(STORAGE_KEYS.accounts, seedAccounts),
  )
  const [employees, setEmployees] = useState(() =>
    readStorage(STORAGE_KEYS.employees, seedEmployees),
  )
  const [attendance, setAttendance] = useState(() =>
    readStorage(STORAGE_KEYS.attendance, seedAttendance),
  )
  const [leaveRequests, setLeaveRequests] = useState(() =>
    readStorage(STORAGE_KEYS.leaves, seedLeaves),
  )
  const [payroll, setPayroll] = useState(() =>
    readStorage(STORAGE_KEYS.payroll, seedPayroll),
  )
  const [sessionUserId, setSessionUserId] = useState(() =>
    readStorage(STORAGE_KEYS.session, null),
  )
  const [activeEmployeeId, setActiveEmployeeId] = useState(() =>
    seedEmployees[0]?.employeeId ?? null,
  )

  const persistAndSet = (key, setter) => (nextValue) => {
    setter(nextValue)
    saveStorage(key, nextValue)
  }

  const setPersistedAccounts = persistAndSet(STORAGE_KEYS.accounts, setAccounts)
  const setPersistedEmployees = persistAndSet(
    STORAGE_KEYS.employees,
    setEmployees,
  )
  const setPersistedAttendance = persistAndSet(
    STORAGE_KEYS.attendance,
    setAttendance,
  )
  const setPersistedLeaves = persistAndSet(STORAGE_KEYS.leaves, setLeaveRequests)
  const setPersistedPayroll = persistAndSet(STORAGE_KEYS.payroll, setPayroll)

  const currentUser = useMemo(
    () => accounts.find((item) => item.id === sessionUserId) ?? null,
    [accounts, sessionUserId],
  )

  const isAuthenticated = Boolean(currentUser)
  const role = currentUser?.role ?? null

  const currentEmployeeId =
    role === 'admin' ? activeEmployeeId : currentUser?.employeeId ?? null

  const currentEmployee = useMemo(
    () => employees.find((item) => item.employeeId === currentEmployeeId) ?? null,
    [employees, currentEmployeeId],
  )

  const signIn = ({ email, password }) => {
    const normalizedEmail = email.trim().toLowerCase()
    const account = accounts.find((item) => item.email.toLowerCase() === normalizedEmail)

    if (!account || account.password !== password) {
      return { ok: false, message: 'Incorrect email or password.' }
    }

    if (!account.verified) {
      return { ok: false, message: 'Email verification is required before sign in.' }
    }

    setSessionUserId(account.id)
    saveStorage(STORAGE_KEYS.session, account.id)

    if (account.role === 'admin') {
      setActiveEmployeeId((prev) => prev ?? employees[0]?.employeeId ?? null)
    } else {
      setActiveEmployeeId(account.employeeId)
    }

    return { ok: true, role: account.role }
  }

  const signUp = ({ employeeId, fullName, email, password, role: selectedRole }) => {
    const normalizedEmail = email.trim().toLowerCase()
    const normalizedEmployeeId = employeeId.trim().toUpperCase()

    if (!PASSWORD_REGEX.test(password)) {
      return {
        ok: false,
        message:
          'Password must be 8+ chars with uppercase, lowercase, number and special character.',
      }
    }

    if (accounts.some((item) => item.email.toLowerCase() === normalizedEmail)) {
      return { ok: false, message: 'Email already exists.' }
    }

    if (accounts.some((item) => item.employeeId === normalizedEmployeeId)) {
      return { ok: false, message: 'Employee ID already exists.' }
    }

    const account = {
      id: `acc-${Date.now()}`,
      employeeId: normalizedEmployeeId,
      fullName: fullName.trim(),
      email: normalizedEmail,
      password,
      role: selectedRole,
      verified: false,
    }

    const nextAccounts = [...accounts, account]
    setPersistedAccounts(nextAccounts)

    if (selectedRole === 'employee') {
      const nextEmployees = [
        ...employees,
        createEmployeeFromSignup({
          employeeId: normalizedEmployeeId,
          fullName: fullName.trim(),
          email: normalizedEmail,
        }),
      ]
      setPersistedEmployees(nextEmployees)
      setPersistedPayroll({
        ...payroll,
        [normalizedEmployeeId]: {
          basic: 0,
          hra: 0,
          bonus: 0,
          deductions: 0,
          updatedAt: toDateInputValue(),
        },
      })
    }

    return {
      ok: true,
      message: 'Registration successful. Verify your email before signing in.',
    }
  }

  const verifyEmail = (email) => {
    const normalizedEmail = email.trim().toLowerCase()
    const account = accounts.find((item) => item.email.toLowerCase() === normalizedEmail)

    if (!account) {
      return { ok: false, message: 'No account found for this email.' }
    }

    const nextAccounts = accounts.map((item) =>
      item.id === account.id ? { ...item, verified: true } : item,
    )
    setPersistedAccounts(nextAccounts)
    return { ok: true, message: 'Email verified. You can sign in now.' }
  }

  const logout = () => {
    setSessionUserId(null)
    saveStorage(STORAGE_KEYS.session, null)
  }

  const updateProfile = ({ employeeId, payload }) => {
    if (!isAuthenticated) {
      return { ok: false, message: 'Unauthorized request.' }
    }

    const targetId = employeeId ?? currentEmployeeId
    if (!targetId) {
      return { ok: false, message: 'Employee not found.' }
    }

    if (role === 'employee' && targetId !== currentUser?.employeeId) {
      return { ok: false, message: 'You can edit only your own profile.' }
    }

    const allowedFieldsByRole =
      role === 'admin'
        ? ['fullName', 'email', 'phone', 'address', 'profilePicture', 'jobTitle', 'department', 'joinDate']
        : ['phone', 'address', 'profilePicture']

    const safePayload = Object.fromEntries(
      Object.entries(payload).filter(([key]) => allowedFieldsByRole.includes(key)),
    )

    const nextEmployees = employees.map((item) =>
      item.employeeId === targetId ? { ...item, ...safePayload } : item,
    )
    setPersistedEmployees(nextEmployees)
    return { ok: true, message: 'Profile updated successfully.' }
  }

  const checkIn = () => {
    if (!currentUser?.employeeId) {
      return { ok: false, message: 'Only employees can check in.' }
    }

    const today = toDateInputValue()
    const existing = attendance.find(
      (item) => item.employeeId === currentUser.employeeId && item.date === today,
    )

    const nextAttendance = existing
      ? attendance.map((item) =>
          item.id === existing.id
            ? {
                ...item,
                checkIn: item.checkIn || nowTime(),
                status: item.status === 'Absent' ? 'Present' : item.status,
              }
            : item,
        )
      : [
          ...attendance,
          {
            id: `att-${Date.now()}`,
            employeeId: currentUser.employeeId,
            date: today,
            status: 'Present',
            checkIn: nowTime(),
            checkOut: '',
          },
        ]

    setPersistedAttendance(nextAttendance)
    return { ok: true, message: 'Checked in successfully.' }
  }

  const checkOut = () => {
    if (!currentUser?.employeeId) {
      return { ok: false, message: 'Only employees can check out.' }
    }

    const today = toDateInputValue()
    const existing = attendance.find(
      (item) => item.employeeId === currentUser.employeeId && item.date === today,
    )

    if (!existing) {
      return { ok: false, message: 'Please check in before check out.' }
    }

    const nextAttendance = attendance.map((item) =>
      item.id === existing.id ? { ...item, checkOut: nowTime() } : item,
    )
    setPersistedAttendance(nextAttendance)
    return { ok: true, message: 'Checked out successfully.' }
  }

  const setAttendanceStatus = ({ employeeId, date, status }) => {
    if (role !== 'admin') {
      return { ok: false, message: 'Only admin can modify attendance status.' }
    }

    const existing = attendance.find(
      (item) => item.employeeId === employeeId && item.date === date,
    )

    const nextAttendance = existing
      ? attendance.map((item) =>
          item.id === existing.id ? { ...item, status } : item,
        )
      : [
          ...attendance,
          {
            id: `att-${Date.now()}`,
            employeeId,
            date,
            status,
            checkIn: '',
            checkOut: '',
          },
        ]

    setPersistedAttendance(nextAttendance)
    return { ok: true, message: 'Attendance status updated.' }
  }

  const applyLeave = ({ type, startDate, endDate, remarks }) => {
    if (!currentUser?.employeeId) {
      return { ok: false, message: 'Only employees can apply for leave.' }
    }

    const nextLeaves = [
      ...leaveRequests,
      {
        id: `leave-${Date.now()}`,
        employeeId: currentUser.employeeId,
        type,
        startDate,
        endDate,
        remarks,
        status: 'Pending',
        adminComment: '',
        appliedOn: toDateInputValue(),
      },
    ]
    setPersistedLeaves(nextLeaves)
    return { ok: true, message: 'Leave request submitted.' }
  }

  const reviewLeave = ({ requestId, status, adminComment }) => {
    if (role !== 'admin') {
      return { ok: false, message: 'Only admin can review leave requests.' }
    }

    const nextLeaves = leaveRequests.map((item) =>
      item.id === requestId ? { ...item, status, adminComment: adminComment ?? '' } : item,
    )
    setPersistedLeaves(nextLeaves)
    return { ok: true, message: `Leave request ${status.toLowerCase()}.` }
  }

  const updatePayroll = ({ employeeId, payload }) => {
    if (role !== 'admin') {
      return { ok: false, message: 'Only admin can update payroll.' }
    }

    const previous = payroll[employeeId] ?? {
      basic: 0,
      hra: 0,
      bonus: 0,
      deductions: 0,
    }

    const nextPayroll = {
      ...payroll,
      [employeeId]: {
        ...previous,
        ...payload,
        updatedAt: toDateInputValue(),
      },
    }
    setPersistedPayroll(nextPayroll)
    return { ok: true, message: 'Payroll updated successfully.' }
  }

  const value = useMemo(
    () => ({
      currentUser,
      role,
      isAuthenticated,
      accounts,
      employees,
      attendance,
      leaveRequests,
      payroll,
      currentEmployee,
      activeEmployeeId,
      signIn,
      signUp,
      verifyEmail,
      logout,
      updateProfile,
      checkIn,
      checkOut,
      setAttendanceStatus,
      applyLeave,
      reviewLeave,
      updatePayroll,
      setActiveEmployeeId,
    }),
    [
      currentUser,
      role,
      isAuthenticated,
      accounts,
      employees,
      attendance,
      leaveRequests,
      payroll,
      currentEmployee,
      activeEmployeeId,
    ],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const context = useContext(AuthContext)

  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }

  return context
}
