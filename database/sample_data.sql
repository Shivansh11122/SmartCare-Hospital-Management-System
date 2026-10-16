USE smart_hospital;

INSERT INTO Departments (department_name, description) VALUES
('Cardiology', 'Heart care'),
('Neurology', 'Brain and nervous system care'),
('Orthopedics', 'Bone and joint care'),
('General Medicine', 'General medical services'),
('Emergency', 'Emergency care');

INSERT INTO Wards
(ward_name, ward_type, capacity, available_capacity, floor_no)
VALUES
('General Ward', 'General', 50, 35, 1),
('Emergency Ward', 'Emergency', 20, 8, 1),
('ICU Ward', 'ICU', 15, 5, 2),
('Outpatient Department', 'OPD', 30, 20, 1);

INSERT INTO Rooms
(ward_id, room_number, room_type, floor_no, capacity, status)
VALUES
(1, 'G101', 'General', 1, 2, 'Available'),
(2, 'E101', 'Emergency', 1, 1, 'Occupied'),
(3, 'I201', 'ICU', 2, 1, 'Available');

INSERT INTO Patients
(name, gender, date_of_birth, phone, address, blood_group)
VALUES
('Aman Kumar', 'Male', '2003-05-15',
 '9876543210', 'Meerut', 'B+'),
('Priya Sharma', 'Female', '2002-08-20',
 '9876543211', 'Delhi', 'O+'),
('Rohit Singh', 'Male', '2001-11-10',
 '9876543212', 'Noida', 'A+');

INSERT INTO Doctors
(department_id, name, specialization, phone, email)
VALUES
(1, 'Dr. Rahul Sharma', 'Cardiology',
 '9876543220', 'rahul@hospital.com'),
(2, 'Dr. Neha Verma', 'Neurology',
 '9876543221', 'neha@hospital.com'),
(3, 'Dr. Amit Singh', 'Orthopedics',
 '9876543222', 'amit@hospital.com');

INSERT INTO Appointments
(patient_id, doctor_id, appointment_date,
 appointment_time, reason, status)
VALUES
(1, 1, '2026-10-15', '10:00:00',
 'Routine checkup', 'Scheduled'),
(2, 2, '2026-10-16', '11:30:00',
 'Headache consultation', 'Scheduled');

INSERT INTO Medicines
(medicine_name, category, quantity, price, expiry_date)
VALUES
('Paracetamol', 'Pain relief', 100, 2.50, '2027-12-31'),
('Antacid', 'Digestive', 60, 5.00, '2027-06-30');