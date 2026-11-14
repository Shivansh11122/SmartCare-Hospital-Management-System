# 🏥 SmartCare – Hospital Management System

A web-based Hospital Management System developed using **Python Flask, MySQL, HTML, CSS, and JavaScript**. The project aims to simplify hospital operations while demonstrating practical concepts of Database Management Systems (DBMS) and Operating Systems (OS).

## 📌 Project Overview

SmartCare provides a centralized platform to manage hospital activities such as patient registration, doctor details, appointments, ward assignments, medical records, prescriptions, billing, and payments.

It also demonstrates database transactions, concurrency control, and process synchronization.

## ✨ Key Features

- Patient Registration and Management
- Doctor and Department Management
- Appointment Booking
- Ward Management and Patient Assignment
- Medical Records Management
- Prescription and Medicine Management
- Billing and Payment Management
- Family Health Sharing
- Audit Trail and Activity History
- Live Appointment Queue Analytics
- Admin Dashboard

## 🛠️ Technologies Used

| Technology | Purpose |
|---|---|
| Python | Backend Programming |
| Flask | Web Framework |
| MySQL | Database |
| HTML | Structure |
| CSS | Styling |
| JavaScript | Frontend Functionality |
| SQL | Database Queries |

## 🗄️ Database Concepts

The project demonstrates:

- Primary Keys and Foreign Keys
- Database Relationships
- SQL Joins
- Normalization Principles (1NF, 2NF, 3NF)
- Transactions
- ACID Properties
- Row-Level Locking
- Data Integrity

## ⚙️ Operating System Concepts

- **Mutex Lock:** Used for synchronization during ward assignment within a Flask process.
- **Semaphore:** Limits concurrent appointment operations to three within a Flask process.
- **FCFS Scheduling:** Used in appointment queue management.
- **Priority Scheduling:** Supports priority-based appointment handling.
- **Deadlock Handling:** Demonstrates deadlock detection through MySQL and transaction rollback.

## 🚀 Installation and Setup

### 1. Clone the Repository

```bash
git clone https://github.com/Shivansh11122/SmartCare-Hospital-Management-System.git
```

### 2. Open the Project Folder

```bash
cd SmartCare-Hospital-Management-System
```

### 3. Create a Virtual Environment

```bash
python -m venv venv
```

Activate it on Windows:

```bash
venv\Scripts\activate
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Configure MySQL

- Open MySQL Workbench.
- Create the project database.
- Execute your database SQL script.
- Configure the MySQL connection details in the Flask application.

### 6. Run the Application

```bash
python SmartCare_app.py
```

Open the local URL displayed in your terminal.

## 🎯 Project Objective

The main objective of SmartCare is to develop a practical hospital management solution while implementing real-world DBMS and Operating System concepts, including transaction management, concurrency control, synchronization, and database integrity.

## 👨‍💻 Developed By

**SmartCare Project Team**

B.Tech – Computer Science and Engineering

## 📄 License

This project is developed for academic and educational purposes.
