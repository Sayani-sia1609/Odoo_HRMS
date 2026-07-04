# 🚀 Odoo HRMS

A modern **Human Resource Management System (HRMS)** built for the **Odoo Hackathon**. The platform simplifies HR operations by providing employee management, attendance tracking, leave management, payroll, and secure role-based authentication through a clean and intuitive web interface.

---

## 📌 Features

- 🔐 JWT-based Authentication
- 👤 Employee & Admin Roles
- 📋 Employee Profile Management
- 📅 Attendance Tracking
- 📝 Leave Request & Approval System
- 💰 Payroll Management
- 📊 HR Dashboard
- 🔒 Secure REST APIs
- ⚡ Fast and Responsive UI

---

## 🛠️ Tech Stack

### Frontend
- React
- Vite
- Tailwind CSS

### Backend
- FastAPI
- SQLAlchemy
- Pydantic

### Database
- PostgreSQL

### Authentication
- JWT (JSON Web Tokens)
- Password Hashing (bcrypt)

---

## 📂 Project Structure

```
Odoo_HRMS/
│
├── frontend/                 # React Frontend
│
├── hrms_api/                 # FastAPI Backend
│   ├── app/
│   ├── auth/
│   ├── routers/
│   ├── models/
│   ├── database.py
│   ├── main.py
│   └── requirements.txt
│
├── files/                    # Uploaded files (if any)
│
├── .gitignore
└── README.md
```

---

## ⚙️ Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/Sayani-sia1609/Odoo_HRMS.git

cd Odoo_HRMS
```

---

## 🖥️ Backend Setup

```bash
cd hrms_api

python -m venv venv
```

### Activate Virtual Environment

#### macOS/Linux

```bash
source venv/bin/activate
```

#### Windows

```bash
venv\Scripts\activate
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Create a `.env` file

```
DATABASE_URL=postgresql://<username>:<password>@localhost:5432/hrms_db

SECRET_KEY=your_secret_key

ALGORITHM=HS256

ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### Run Backend

```bash
uvicorn app.main:app --reload
```

Backend will run on:

```
http://127.0.0.1:8000
```

---

## 💻 Frontend Setup

```bash
cd frontend

npm install

npm run dev
```

Frontend will run on:

```
http://localhost:5173
```

---

## 🗄️ Database

The project uses **PostgreSQL** as the primary database.

Configure the database credentials inside the `.env` file before running the backend.

Example:

```env
DATABASE_URL=postgresql://postgres:password@localhost:5432/hrms_db
```

---

## 🔐 Authentication

- JWT Authentication
- Password Hashing
- Protected Routes
- Role-Based Access Control (Admin & Employee)

---

## 👥 Team

| Member | Role |
|---------|------|
| **Sayani Das** | Authentication and Database |
| **Rohit XED** | Frontend Development |
| **Srinik G-bit** | Backend Services|
| **D-Luvgood** | API,Readme|

---

## 🎯 Future Enhancements

- Email Notifications
- Document Management
- Performance Analytics
- AI-powered HR Insights
- Employee Self-Service Portal
- Payroll Reports & Exports

---

## 📄 License

This project was developed as part of the **Odoo Hackathon** and is intended for educational and demonstration purposes.

---

### ⭐ If you like this project, consider giving it a star!
