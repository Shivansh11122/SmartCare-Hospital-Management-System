CREATE DATABASE IF NOT EXISTS smart_hospital;
USE smart_hospital;

CREATE TABLE Users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    role VARCHAR(30) NOT NULL
);

CREATE TABLE Departments (
    department_id INT AUTO_INCREMENT PRIMARY KEY,
    department_name VARCHAR(100) NOT NULL UNIQUE,
    description VARCHAR(255)
);

CREATE TABLE Wards (
    ward_id INT AUTO_INCREMENT PRIMARY KEY,
    ward_name VARCHAR(100) NOT NULL,
    ward_type ENUM('General','Emergency','ICU','OPD') NOT NULL,
    capacity INT NOT NULL,
    available_capacity INT NOT NULL,
    floor_no INT,
    status VARCHAR(30) DEFAULT 'Available',
    CHECK (capacity >= 0),
    CHECK (available_capacity >= 0),
    CHECK (available_capacity <= capacity)
);

CREATE TABLE Rooms (
    room_id INT AUTO_INCREMENT PRIMARY KEY,
    ward_id INT,
    room_number VARCHAR(20) NOT NULL UNIQUE,
    room_type VARCHAR(50),
    floor_no INT,
    capacity INT DEFAULT 1,
    status VARCHAR(30) DEFAULT 'Available',
    FOREIGN KEY (ward_id) REFERENCES Wards(ward_id)
);

CREATE TABLE Patients (
    patient_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT UNIQUE,
    name VARCHAR(100) NOT NULL,
    gender VARCHAR(20),
    date_of_birth DATE,
    phone VARCHAR(15),
    address VARCHAR(255),
    blood_group VARCHAR(5),
    FOREIGN KEY (user_id) REFERENCES Users(user_id)
);

CREATE TABLE Doctors (
    doctor_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT UNIQUE,
    department_id INT NOT NULL,
    name VARCHAR(100) NOT NULL,
    specialization VARCHAR(100),
    phone VARCHAR(15),
    email VARCHAR(120),
    FOREIGN KEY (user_id) REFERENCES Users(user_id),
    FOREIGN KEY (department_id)
        REFERENCES Departments(department_id)
);

CREATE TABLE Appointments (
    appointment_id INT AUTO_INCREMENT PRIMARY KEY,
    patient_id INT NOT NULL,
    doctor_id INT NOT NULL,
    appointment_date DATE NOT NULL,
    appointment_time TIME NOT NULL,
    reason VARCHAR(255),
    status VARCHAR(30) DEFAULT 'Scheduled',
    FOREIGN KEY (patient_id) REFERENCES Patients(patient_id),
    FOREIGN KEY (doctor_id) REFERENCES Doctors(doctor_id)
);

CREATE TABLE `Medical Records` (
    record_id INT AUTO_INCREMENT PRIMARY KEY,
    patient_id INT NOT NULL,
    doctor_id INT NOT NULL,
    diagnosis VARCHAR(255),
    treatment TEXT,
    record_date DATE NOT NULL,
    notes TEXT,
    FOREIGN KEY (patient_id) REFERENCES Patients(patient_id),
    FOREIGN KEY (doctor_id) REFERENCES Doctors(doctor_id)
);

CREATE TABLE Medicines (
    medicine_id INT AUTO_INCREMENT PRIMARY KEY,
    medicine_name VARCHAR(100) NOT NULL,
    category VARCHAR(100),
    quantity INT DEFAULT 0,
    price DECIMAL(10,2) DEFAULT 0,
    expiry_date DATE,
    CHECK (quantity >= 0),
    CHECK (price >= 0)
);

CREATE TABLE Prescriptions (
    prescription_id INT AUTO_INCREMENT PRIMARY KEY,
    patient_id INT NOT NULL,
    doctor_id INT NOT NULL,
    medicine_id INT,
    prescription_date DATE NOT NULL,
    dosage VARCHAR(100),
    duration VARCHAR(100),
    instructions VARCHAR(255),
    FOREIGN KEY (patient_id) REFERENCES Patients(patient_id),
    FOREIGN KEY (doctor_id) REFERENCES Doctors(doctor_id),
    FOREIGN KEY (medicine_id) REFERENCES Medicines(medicine_id)
);

CREATE TABLE Bills (
    bill_id INT AUTO_INCREMENT PRIMARY KEY,
    patient_id INT NOT NULL,
    bill_date DATE NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    description VARCHAR(255),
    status VARCHAR(30) DEFAULT 'Unpaid',
    FOREIGN KEY (patient_id) REFERENCES Patients(patient_id),
    CHECK (amount >= 0)
);

CREATE TABLE Payments (
    payment_id INT AUTO_INCREMENT PRIMARY KEY,
    bill_id INT NOT NULL,
    payment_date DATE NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    payment_method VARCHAR(30),
    status VARCHAR(30) DEFAULT 'Pending',
    FOREIGN KEY (bill_id) REFERENCES Bills(bill_id),
    CHECK (amount > 0)
);