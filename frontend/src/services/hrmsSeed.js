export const seedAccounts = [
  {
    id: 'acc-admin-1',
    employeeId: 'HR1000',
    fullName: 'Aisha Khan',
    email: 'admin@hrms.com',
    password: 'Admin@123',
    role: 'admin',
    verified: true,
  },
  {
    id: 'acc-emp-1',
    employeeId: 'EMP1001',
    fullName: 'Rohit Verma',
    email: 'rohit@hrms.com',
    password: 'Employee@123',
    role: 'employee',
    verified: true,
  },
  {
    id: 'acc-emp-2',
    employeeId: 'EMP1002',
    fullName: 'Neha Sharma',
    email: 'neha@hrms.com',
    password: 'Employee@123',
    role: 'employee',
    verified: true,
  },
]

export const seedEmployees = [
  {
    employeeId: 'EMP1001',
    fullName: 'Rohit Verma',
    email: 'rohit@hrms.com',
    phone: '+91 9876543210',
    address: 'Bengaluru, Karnataka',
    profilePicture: '',
    jobTitle: 'Frontend Engineer',
    department: 'Engineering',
    joinDate: '2024-02-12',
    documents: ['Offer Letter', 'Aadhaar', 'PAN'],
  },
  {
    employeeId: 'EMP1002',
    fullName: 'Neha Sharma',
    email: 'neha@hrms.com',
    phone: '+91 9988776655',
    address: 'Pune, Maharashtra',
    profilePicture: '',
    jobTitle: 'Product Designer',
    department: 'Design',
    joinDate: '2023-11-02',
    documents: ['Offer Letter', 'Passport'],
  },
]

export const seedAttendance = [
  {
    id: 'att-1',
    employeeId: 'EMP1001',
    date: '2026-07-01',
    status: 'Present',
    checkIn: '09:15',
    checkOut: '18:07',
  },
  {
    id: 'att-2',
    employeeId: 'EMP1001',
    date: '2026-07-02',
    status: 'Present',
    checkIn: '09:08',
    checkOut: '18:00',
  },
  {
    id: 'att-3',
    employeeId: 'EMP1002',
    date: '2026-07-02',
    status: 'Half-day',
    checkIn: '11:35',
    checkOut: '16:01',
  },
]

export const seedLeaves = [
  {
    id: 'leave-1',
    employeeId: 'EMP1001',
    type: 'Paid',
    startDate: '2026-07-11',
    endDate: '2026-07-12',
    remarks: 'Family event',
    status: 'Pending',
    adminComment: '',
    appliedOn: '2026-07-03',
  },
]

export const seedPayroll = {
  EMP1001: {
    basic: 78000,
    hra: 22000,
    bonus: 7000,
    deductions: 8000,
    updatedAt: '2026-06-30',
  },
  EMP1002: {
    basic: 72000,
    hra: 19000,
    bonus: 5000,
    deductions: 7100,
    updatedAt: '2026-06-30',
  },
}
