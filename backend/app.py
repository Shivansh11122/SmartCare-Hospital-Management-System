import os
import threading
ward_assignment_lock = threading.Lock()
appointment_semaphore = threading.Semaphore(3)
from pathlib import Path
from functools import wraps
from dotenv import load_dotenv
from flask import Flask, jsonify, request, send_from_directory, session
from werkzeug.security import generate_password_hash, check_password_hash
from db import get_connection
PROJECT_ROOT = Path(__file__).resolve().parent.parent
FRONTEND = PROJECT_ROOT / "frontend"
load_dotenv(PROJECT_ROOT / ".env")
app = Flask(
    __name__,
    static_folder=str(FRONTEND),
    static_url_path="/static",
)
app.secret_key = os.environ.get("FLASK_SECRET_KEY")
if not app.secret_key:
    raise RuntimeError("FLASK_SECRET_KEY is missing from .env")
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
)
def admin_required(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        if session.get("user_role") != "admin":
            return jsonify(error="Admin login required"), 401
        return function(*args, **kwargs)
    return wrapper
def login_required(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        if not session.get("user_id"):
            return jsonify(error="Login required"), 401
        return function(*args, **kwargs)
    return wrapper
@app.route("/")
def home():
    role = session.get("user_role")
    if role == "admin":
        return send_from_directory(str(FRONTEND), "index.html")
    if role == "user":
        return send_from_directory(str(FRONTEND), "user_dashboard.html")
    return send_from_directory(str(FRONTEND), "home.html")
@app.route("/admin-login")
def admin_login_page():
    role = session.get("user_role")
    if role == "admin":
        return send_from_directory(str(FRONTEND), "index.html")
    if role == "user":
        return send_from_directory(str(FRONTEND), "user_dashboard.html")
    return send_from_directory(str(FRONTEND), "login.html")
@app.route("/user")
def user_portal():
    if session.get("user_role") == "user":
        return send_from_directory(str(FRONTEND), "user_dashboard.html")
    if session.get("user_role") == "admin":
        return send_from_directory(str(FRONTEND), "index.html")
    return send_from_directory(str(FRONTEND), "user.html")
@app.route("/user/dashboard")
def user_dashboard():
    if session.get("user_role") == "user":
        return send_from_directory(str(FRONTEND), "user_dashboard.html")
    if session.get("user_role") == "admin":
        return send_from_directory(str(FRONTEND), "index.html")
    return send_from_directory(str(FRONTEND), "user.html")
@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    if not password:
        return jsonify(error="Password is required"), 400
    if not email and not name:
        return jsonify(error="Name and password are required"), 400
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        if email:
            cursor.execute(
                """
                SELECT user_id, name, email, password, role
                FROM Users
                WHERE email = %s AND role = 'admin'
                """,
                (email,),
            )
            users = cursor.fetchall()
        else:
            cursor.execute(
                """
                SELECT user_id, name, email, password, role
                FROM Users
                WHERE name = %s AND role = 'user'
                """,
                (name,),
            )
            users = cursor.fetchall()
        if not email and len(users) > 1:
            return jsonify(
                error="This name belongs to multiple accounts. Contact the administrator."
            ), 409
        if not users or not check_password_hash(users[0]["password"], password):
            return jsonify(error="Invalid name/email or password"), 401
        user = users[0]
        if user["role"] not in ("admin", "user"):
            return jsonify(error="Account role is not permitted"), 403
        session.clear()
        session["user_id"] = user["user_id"]
        session["user_name"] = user["name"]
        session["user_role"] = user["role"]
        return jsonify(
            success=True,
            role=user["role"],
            name=user["name"],
            message="Login successful",
        ), 200
    except Exception:
        app.logger.exception("Login failed")
        return jsonify(error="Unable to log in. Please try again."), 500
    finally:
        cursor.close()
        conn.close()
@app.route("/api/signup", methods=["POST"])
def user_signup():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    password = data.get("password") or ""
    if not name or not password:
        return jsonify(error="Name and password are required"), 400
    if len(name) > 100:
        return jsonify(error="Name must be at most 100 characters"), 400
    if len(password) < 8:
        return jsonify(error="Password must be at least 8 characters"), 400
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT user_id FROM Users WHERE name = %s AND role = 'user'",
            (name,),
        )
        if cursor.fetchone():
            return jsonify(
                error="This name is already registered. Please use a different name."
            ), 409
        password_hash = generate_password_hash(password)
        cursor.execute(
            """
            INSERT INTO Users (name, email, password, role)
            VALUES (%s, NULL, %s, %s)
            """,
            (name, password_hash, "user"),
        )
        conn.commit()
        return jsonify(
            success=True,
            message="Account created successfully. Please log in.",
        ), 201
    except Exception:
        conn.rollback()
        app.logger.exception("User signup failed")
        return jsonify(error="Could not create account. Please try again."), 500
    finally:
        cursor.close()
        conn.close()
@app.route("/api/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify(success=True, message="Logged out successfully"), 200
@app.route("/api/me", methods=["GET"])
def current_user():
    if not session.get("user_id"):
        return jsonify(user=None), 200
    return jsonify(
        user_id=session["user_id"],
        name=session["user_name"],
        role=session["user_role"],
    ), 200
@app.route("/api/dashboard", methods=["GET"])
@admin_required
def dashboard():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        counts = {}
        tables = {
            "patients": "Patients",
            "doctors": "Doctors",
            "wards": "Wards",
            "departments": "Departments",
            "appointments": "Appointments",
        }
        for key, table in tables.items():
            cursor.execute(f"SELECT COUNT(*) AS total FROM `{table}`")
            counts[key] = cursor.fetchone()["total"]
        return jsonify(counts)
    finally:
        cursor.close()
        conn.close()
@app.route("/api/patients", methods=["GET"])
@admin_required
def get_patients():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT patient_id, name, gender, phone, blood_group
            FROM Patients
            ORDER BY patient_id DESC
            """
        )
        return jsonify(cursor.fetchall())
    finally:
        cursor.close()
        conn.close()
@app.route("/api/patients", methods=["POST"])
@login_required
def add_patient():
    if session.get("user_role") != "user":
        return jsonify(error="Please log in as a user to register a patient"), 401
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    gender = data.get("gender") or None
    date_of_birth = data.get("date_of_birth") or None
    phone = (data.get("phone") or "").strip() or None
    address = (data.get("address") or "").strip() or None
    blood_group = data.get("blood_group") or None
    if not name:
        return jsonify(error="Patient name is required"), 400
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT patient_id FROM Patients WHERE user_id = %s",
            (session["user_id"],)
        )
        if cursor.fetchone():
            return jsonify(
                error="You already have a patient profile."
            ), 409
        cursor.execute("""
            INSERT INTO Patients
                (user_id, name, gender, date_of_birth,
                 phone, address, blood_group)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            session["user_id"],
            name,
            gender,
            date_of_birth,
            phone,
            address,
            blood_group
        ))
        conn.commit()
        return jsonify({
            "message": "Patient registered successfully",
            "patient_id": cursor.lastrowid
        }), 201
    except Exception:
        conn.rollback()
        app.logger.exception("Patient registration failed")
        return jsonify(
            error="Patient registration failed. Please try again."
        ), 500
    finally:
        cursor.close()
        conn.close()
@app.route("/api/patients/<int:patient_id>", methods=["DELETE"])
@admin_required
def delete_patient(patient_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT patient_id FROM Patients WHERE patient_id = %s",
            (patient_id,)
        )
        patient = cursor.fetchone()
        if not patient:
            return jsonify(error="Patient not found"), 404
        cursor.execute(
            "SELECT COUNT(*) AS total FROM Appointments WHERE patient_id = %s",
            (patient_id,)
        )
        if cursor.fetchone()["total"] > 0:
            return jsonify(
                error="This patient has appointment history and cannot be removed."
            ), 409
        linked_tables = [
            ("Medical Records", "patient_id"),
            ("Prescriptions", "patient_id"),
            ("Bills", "patient_id"),
        ]
        for table_name, column_name in linked_tables:
            cursor.execute(
                f"SELECT COUNT(*) AS total FROM `{table_name}` "
                f"WHERE `{column_name}` = %s",
                (patient_id,)
            )
            if cursor.fetchone()["total"] > 0:
                return jsonify(
                    error=(
                        f"This patient has linked {table_name.lower()} "
                        "and cannot be removed."
                    )
                ), 409
        cursor.execute(
            "DELETE FROM Patients WHERE patient_id = %s",
            (patient_id,)
        )
        conn.commit()
        return jsonify(message="Patient removed successfully"), 200
    except Exception:
        conn.rollback()
        app.logger.exception("Patient removal failed")
        return jsonify(
            error="Patient could not be removed because linked records may exist."
        ), 409
    finally:
        cursor.close()
        conn.close()
@app.route("/api/doctors", methods=["GET"])
def get_doctors():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        query = """
            SELECT d.doctor_id, d.name, d.specialization,
                   d.phone, d.email, d.department_id,
                   dep.department_name, d.status
            FROM Doctors d
            JOIN Departments dep
                ON d.department_id = dep.department_id
        """
        if session.get("user_role") != "admin":
            query += " WHERE d.status = 'Active'"
        query += " ORDER BY d.doctor_id DESC"
        cursor.execute(query)
        return jsonify(cursor.fetchall())
    finally:
        cursor.close()
        conn.close()
@app.route("/api/doctors", methods=["POST"])
@admin_required
def add_doctor():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    department_id = data.get("department_id")
    if not name or not department_id:
        return jsonify(error="Doctor name and department are required"), 400
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO Doctors
                (name, department_id, specialization, phone, email)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (
                name,
                department_id,
                data.get("specialization") or None,
                data.get("phone") or None,
                data.get("email") or None,
            ),
        )
        conn.commit()
        return jsonify(
            message="Doctor registered successfully",
            doctor_id=cursor.lastrowid,
        ), 201
    except Exception:
        conn.rollback()
        app.logger.exception("Doctor registration failed")
        return jsonify(error="Could not register doctor"), 500
    finally:
        cursor.close()
        conn.close()
@app.route("/api/doctors/<int:doctor_id>", methods=["DELETE"])
@admin_required
def delete_doctor(doctor_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT doctor_id FROM Doctors WHERE doctor_id = %s",
            (doctor_id,)
        )
        doctor = cursor.fetchone()
        if not doctor:
            return jsonify(error="Doctor not found"), 404
        cursor.execute(
            "SELECT COUNT(*) AS total FROM Appointments WHERE doctor_id = %s",
            (doctor_id,)
        )
        appointment_count = cursor.fetchone()["total"]
        if appointment_count > 0:
            return jsonify(
                error="This doctor has appointment history and cannot be removed."
            ), 409
        cursor.execute(
            "DELETE FROM Doctors WHERE doctor_id = %s",
            (doctor_id,)
        )
        conn.commit()
        return jsonify(message="Doctor removed successfully"), 200
    except Exception:
        conn.rollback()
        app.logger.exception("Doctor removal failed")
        return jsonify(error="Could not remove doctor"), 500
    finally:
        cursor.close()
        conn.close()
@app.route(
    "/api/doctors/<int:doctor_id>/deactivate",
    methods=["PATCH"]
)
@admin_required
def deactivate_doctor(doctor_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT doctor_id, status FROM Doctors WHERE doctor_id = %s",
            (doctor_id,)
        )
        doctor = cursor.fetchone()
        if not doctor:
            return jsonify(error="Doctor not found"), 404
        if doctor["status"] == "Inactive":
            return jsonify(message="Doctor is already inactive."), 200
        cursor.execute(
            "UPDATE Doctors SET status = 'Inactive' WHERE doctor_id = %s",
            (doctor_id,)
        )
        conn.commit()
        return jsonify(
            message="Doctor deactivated. Appointment history has been preserved."
        ), 200
    except Exception:
        conn.rollback()
        app.logger.exception("Doctor deactivation failed")
        return jsonify(error="Could not deactivate doctor"), 500
    finally:
        cursor.close()
        conn.close()
@app.route("/api/departments", methods=["GET"])
def get_departments():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT department_id, department_name
            FROM Departments
            ORDER BY department_name
            """
        )
        return jsonify(cursor.fetchall())
    finally:
        cursor.close()
        conn.close()
@app.route("/api/appointments", methods=["GET"])
@admin_required
def get_appointments():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT a.appointment_id, a.patient_id,
                   p.name AS patient_name, a.doctor_id,
                   d.name AS doctor_name, d.specialization,
                   DATE_FORMAT(a.appointment_date, '%Y-%m-%d') AS appointment_date,
                   TIME_FORMAT(a.appointment_time, '%H:%i:%s') AS appointment_time,
                   a.reason, a.status, a.requested_priority,
                   a.queue_priority, a.queue_status,
                   DATE_FORMAT(a.arrival_time, '%Y-%m-%d %H:%i:%s') AS arrival_time,
                   DATE_FORMAT(a.queue_service_start, '%Y-%m-%d %H:%i:%s') AS queue_service_start
            FROM Appointments a
            JOIN Patients p ON a.patient_id = p.patient_id
            JOIN Doctors d ON a.doctor_id = d.doctor_id
            ORDER BY a.appointment_date DESC, a.appointment_time DESC
            """
        )
        return jsonify(cursor.fetchall())
    finally:
        cursor.close()
        conn.close()
@app.route(
    "/api/appointments/<int:appointment_id>/status",
    methods=["PATCH"]
)
@admin_required
def update_appointment_status(appointment_id):
    data = request.get_json(silent=True) or {}
    status = (data.get("status") or "").strip()
    allowed_statuses = {"Scheduled", "Completed", "Cancelled"}
    if status not in allowed_statuses:
        return jsonify(
            error="Invalid status. Choose Scheduled, Completed, or Cancelled."
        ), 400
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT appointment_id FROM Appointments "
            "WHERE appointment_id = %s",
            (appointment_id,)
        )
        if not cursor.fetchone():
            return jsonify(error="Appointment not found"), 404
        cursor.execute(
            "UPDATE Appointments SET status = %s "
            "WHERE appointment_id = %s",
            (status, appointment_id)
        )
        conn.commit()
        return jsonify(
            message=f"Appointment status updated to {status}."
        ), 200
    except Exception:
        conn.rollback()
        app.logger.exception("Appointment status update failed")
        return jsonify(error="Could not update appointment status"), 500
    finally:
        cursor.close()
        conn.close()
from datetime import datetime, timedelta
@app.route("/api/patient-queue", methods=["GET"])
@admin_required
def get_patient_queue():
    algorithm = (request.args.get("algorithm") or "fcfs").lower()
    if algorithm not in {"fcfs", "priority"}:
        return jsonify(error="Choose fcfs or priority"), 400
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:

        if algorithm == "priority":
            scheduling_order = """
                CASE
                    WHEN a.queue_status = 'In Service' THEN 0
                    WHEN a.queue_status = 'Waiting' THEN 1
                    WHEN a.queue_status = 'Not Arrived' THEN 2
                    WHEN a.queue_status = 'Completed' THEN 3
                    ELSE 4
                END ASC,
                CASE
                    WHEN a.queue_status = 'Waiting'
                    THEN COALESCE(a.queue_priority, 99)
                    ELSE 0
                END ASC,
                COALESCE(
                    a.arrival_time,
                    TIMESTAMP(a.appointment_date, a.appointment_time)
                ) ASC,
                a.appointment_id ASC
            """
        else:
            scheduling_order = """
                CASE
                    WHEN a.queue_status = 'In Service' THEN 0
                    WHEN a.queue_status = 'Waiting' THEN 1
                    WHEN a.queue_status = 'Not Arrived' THEN 2
                    WHEN a.queue_status = 'Completed' THEN 3
                    ELSE 4
                END ASC,
                COALESCE(
                    a.arrival_time,
                    TIMESTAMP(a.appointment_date, a.appointment_time)
                ) ASC,
                a.appointment_id ASC
            """

        cursor.execute(f"""
            SELECT
                a.appointment_id,
                a.patient_id,
                p.name AS patient_name,
                a.doctor_id,
                d.name AS doctor_name,
                DATE_FORMAT(
                    a.appointment_date, '%Y-%m-%d'
                ) AS appointment_date,
                TIME_FORMAT(
                    a.appointment_time, '%H:%i'
                ) AS appointment_time,
                a.status AS appointment_status,
                DATE_FORMAT(
                    a.arrival_time, '%Y-%m-%d %H:%i:%s'
                ) AS arrival_time,
                a.requested_priority,
                a.queue_priority,
                a.queue_status,
                DATE_FORMAT(
                    a.queue_service_start, '%Y-%m-%d %H:%i:%s'
                ) AS queue_service_start,
                CASE
                    WHEN a.arrival_time IS NOT NULL
                     AND a.queue_service_start IS NOT NULL
                    THEN TIMESTAMPDIFF(
                        MINUTE, a.arrival_time, a.queue_service_start
                    )
                    ELSE NULL
                END AS waiting_minutes
            FROM Appointments AS a
            JOIN Patients AS p
                ON p.patient_id = a.patient_id
            JOIN Doctors AS d
                ON d.doctor_id = a.doctor_id
            WHERE a.appointment_date = CURDATE()
              AND (
                  a.status = 'Scheduled'
                  OR a.queue_status IN (
                      'Waiting', 'In Service', 'Completed'
                  )
              )
            ORDER BY {scheduling_order}
        """)
        appointments = cursor.fetchall()
        cursor.execute("""
            SELECT
                COUNT(CASE
                    WHEN queue_status = 'Waiting' THEN 1
                END) AS waiting_count,
                COUNT(CASE
                    WHEN queue_status = 'In Service' THEN 1
                END) AS in_service_count,
                COUNT(CASE
                    WHEN queue_status = 'Completed' THEN 1
                END) AS completed_count,
                ROUND(COALESCE(AVG(CASE
                    WHEN queue_status = 'Completed'
                     AND arrival_time IS NOT NULL
                     AND queue_service_start IS NOT NULL
                    THEN TIMESTAMPDIFF(
                        MINUTE, arrival_time, queue_service_start
                    )
                END), 0), 1) AS average_wait_minutes
            FROM Appointments
            WHERE appointment_date = CURDATE()
              AND (
                  status = 'Scheduled'
                  OR queue_status IN (
                      'Waiting', 'In Service', 'Completed'
                  )
              )
        """)
        stats = cursor.fetchone()
        stats["average_wait_minutes"] = float(
            stats["average_wait_minutes"] or 0
        )
        return jsonify({
            "algorithm": algorithm,
            "appointments": appointments,
            "stats": stats
        }), 200
    except Exception:
        app.logger.exception("Could not load patient queue")
        return jsonify(error="Could not load patient queue"), 500
    finally:
        cursor.close()
        conn.close()
@app.route(
    "/api/patient-queue/<int:appointment_id>/check-in",
    methods=["POST"]
)
@admin_required
def check_in_queue_patient(appointment_id):
    data = request.get_json(silent=True) or {}
    try:
        priority = int(data.get("priority", 2))
    except (TypeError, ValueError):
        return jsonify(error="Priority must be 1, 2, or 3"), 400
    if priority not in (1, 2, 3):
        return jsonify(error="Priority must be 1, 2, or 3"), 400
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        conn.start_transaction()
        cursor.execute("""
            SELECT
                appointment_id,
                status,
                queue_status,
                (appointment_date = CURDATE()) AS is_today
            FROM Appointments
            WHERE appointment_id = %s
            FOR UPDATE
        """, (appointment_id,))
        appointment = cursor.fetchone()
        if not appointment:
            conn.rollback()
            return jsonify(error="Appointment not found"), 404
        if not appointment["is_today"]:
            conn.rollback()
            return jsonify(
                error="A patient can only check in on the appointment date."
            ), 409
        if appointment["status"] != "Scheduled":
            conn.rollback()
            return jsonify(
                error="Only scheduled appointments can check in."
            ), 409
        if appointment["queue_status"] != "Not Arrived":
            conn.rollback()
            return jsonify(
                error="This appointment has already checked in or been processed."
            ), 409
        cursor.execute("""
            UPDATE Appointments
            SET arrival_time = NOW(),
                queue_priority = %s,
                queue_status = 'Waiting',
                queue_service_start = NULL
            WHERE appointment_id = %s
        """, (priority, appointment_id))
        conn.commit()
        return jsonify(
            message="Patient checked in and added to the queue."
        ), 200
    except Exception:
        conn.rollback()
        app.logger.exception("Patient queue check-in failed")
        return jsonify(error="Could not check in patient"), 500
    finally:
        cursor.close()
        conn.close()
@app.route(
    "/api/patient-queue/<int:appointment_id>/status",
    methods=["PATCH"]
)
@admin_required
def update_patient_queue_status(appointment_id):
    data = request.get_json(silent=True) or {}
    new_status = (data.get("queue_status") or "").strip()
    if new_status not in {"In Service", "Completed"}:
        return jsonify(
            error="Queue status must be In Service or Completed."
        ), 400
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        conn.start_transaction()
        cursor.execute("""
            SELECT
                appointment_id,
                status,
                queue_status,
                (appointment_date = CURDATE()) AS is_today
            FROM Appointments
            WHERE appointment_id = %s
            FOR UPDATE
        """, (appointment_id,))
        appointment = cursor.fetchone()
        if not appointment:
            conn.rollback()
            return jsonify(error="Appointment not found"), 404
        if not appointment["is_today"]:
            conn.rollback()
            return jsonify(
                error="Only today's appointments can be processed."
            ), 409
        if appointment["status"] != "Scheduled":
            conn.rollback()
            return jsonify(
                error="This appointment is no longer scheduled."
            ), 409
        current_status = appointment["queue_status"]
        if new_status == "In Service":
            if current_status != "Waiting":
                conn.rollback()
                return jsonify(
                    error="Only waiting patients can be started."
                ), 409
            cursor.execute("""
                UPDATE Appointments
                SET queue_status = 'In Service',
                    queue_service_start = NOW()
                WHERE appointment_id = %s
            """, (appointment_id,))
        else:
            if current_status != "In Service":
                conn.rollback()
                return jsonify(
                    error="Start the service before completing it."
                ), 409
            cursor.execute("""
                UPDATE Appointments
                SET queue_status = 'Completed',
                    status = 'Completed'
                WHERE appointment_id = %s
            """, (appointment_id,))
        conn.commit()
        return jsonify(
            message=f"Patient queue status updated to {new_status}."
        ), 200
    except Exception:
        conn.rollback()
        app.logger.exception("Patient queue status update failed")
        return jsonify(error="Could not update queue status"), 500
    finally:
        cursor.close()
        conn.close()
@app.route("/api/appointments", methods=["POST"])
@login_required
def add_appointment():
    if session.get("user_role") != "user":
        return jsonify(
            error="Please log in as a user to book an appointment"
        ), 401
    with appointment_semaphore:
        data = request.get_json(silent=True) or {}
        doctor_id = data.get("doctor_id")
        appointment_date = data.get("appointment_date")
        appointment_time = data.get("appointment_time")
        reason = (data.get("reason") or "").strip()
        try:
            requested_priority = int(data.get("requested_priority", 3))
        except (TypeError, ValueError):
            return jsonify(error="Invalid requested priority"), 400
        if requested_priority not in (1, 2, 3):
            return jsonify(
                error="Priority must be 1 (Emergency), 2 (Urgent), or 3 (Regular)"
            ), 400
        if not all([doctor_id, appointment_date, appointment_time]):
            return jsonify(
                error="Doctor, date, and time are required"
            ), 400
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            conn.start_transaction()
            cursor.execute(
                """
                SELECT doctor_id, status
                FROM Doctors
                WHERE doctor_id = %s
                FOR UPDATE
                """,
                (doctor_id,)
            )
            doctor = cursor.fetchone()
            if not doctor:
                conn.rollback()
                return jsonify(
                    error="Selected doctor does not exist"
                ), 400
            if doctor["status"] != "Active":
                conn.rollback()
                return jsonify(
                    error="This doctor is inactive and cannot accept new appointments."
                ), 400
            cursor.execute(
                "SELECT patient_id FROM Patients WHERE user_id = %s",
                (session["user_id"],)
            )
            patient = cursor.fetchone()
            if not patient:
                conn.rollback()
                return jsonify(
                    error="Please register your patient details first"
                ), 400
            cursor.execute(
                """
                SELECT appointment_id
                FROM Appointments
                WHERE doctor_id = %s
                  AND appointment_date = %s
                  AND appointment_time = %s
                  AND status <> 'Cancelled'
                LIMIT 1
                """,
                (doctor_id, appointment_date, appointment_time)
            )
            if cursor.fetchone():
                cursor.execute(
                    """
                    SELECT appointment_time
                    FROM Appointments
                    WHERE doctor_id = %s
                      AND appointment_date = %s
                      AND status <> 'Cancelled'
                    """,
                    (doctor_id, appointment_date)
                )
                booked_times = set()
                for row in cursor.fetchall():
                    value = row["appointment_time"]
                    if hasattr(value, "total_seconds"):
                        value = str(value)
                    booked_times.add(str(value)[:8])
                requested = datetime.strptime(
                    str(appointment_time)[:5], "%H:%M"
                )
                start = datetime.strptime("09:00", "%H:%M")
                end = datetime.strptime("17:00", "%H:%M")
                candidates = []
                slot = start
                while slot < end:
                    slot_text = slot.strftime("%H:%M:%S")
                    if (
                        slot >= requested
                        and slot_text not in booked_times
                    ):
                        candidates.append(slot.strftime("%I:%M %p"))
                    slot += timedelta(minutes=30)
                conn.rollback()
                return jsonify(
                    error="This doctor is already booked at the selected time.",
                    available_slots=candidates[:3]
                ), 409
            cursor.execute(
                """
                INSERT INTO Appointments
                    (patient_id, doctor_id, appointment_date,
                     appointment_time, reason, status, requested_priority)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    patient["patient_id"],
                    doctor_id,
                    appointment_date,
                    appointment_time,
                    reason or None,
                    "Scheduled",
                    requested_priority
                )
            )
            appointment_id = cursor.lastrowid
            conn.commit()
            return jsonify({
                "message": "Appointment booked successfully",
                "appointment_id": appointment_id
            }), 201
        except Exception:
            conn.rollback()
            app.logger.exception("Appointment booking failed")
            return jsonify(
                error="Could not book appointment. Check the date and time."
            ), 500
        finally:
            cursor.close()
            conn.close()
@app.route("/api/wards", methods=["POST"])
@admin_required
def add_ward():
    data = request.get_json(silent=True) or {}
    ward_name = (data.get("ward_name") or "").strip()
    ward_type = (data.get("ward_type") or "").strip()
    capacity = data.get("capacity")
    floor_no = data.get("floor_no")
    if not ward_name or not ward_type or capacity is None:
        return jsonify(
            error="Ward name, type, and capacity are required"
        ), 400
    try:
        capacity = int(capacity)
        floor_no = int(floor_no) if floor_no not in (None, "") else None
        if capacity <= 0:
            return jsonify(
                error="Additional capacity must be greater than zero"
            ), 400
    except (TypeError, ValueError):
        return jsonify(
            error="Capacity and floor must be valid numbers"
        ), 400
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT ward_id, capacity, available_capacity
            FROM Wards
            WHERE LOWER(TRIM(ward_name)) = LOWER(TRIM(%s))
              AND ward_type = %s
            LIMIT 1
            FOR UPDATE
            """,
            (ward_name, ward_type)
        )
        existing_ward = cursor.fetchone()
        if existing_ward:
            new_capacity = int(existing_ward["capacity"]) + capacity
            new_available = (
                int(existing_ward["available_capacity"]) + capacity
            )
            cursor.execute(
                """
                UPDATE Wards
                SET capacity = %s,
                    available_capacity = %s
                WHERE ward_id = %s
                """,
                (
                    new_capacity,
                    new_available,
                    existing_ward["ward_id"]
                )
            )
            conn.commit()
            return jsonify(
                message="Existing ward capacity increased successfully.",
                ward_id=existing_ward["ward_id"],
                capacity=new_capacity,
                available_capacity=new_available
            ), 200
        cursor.execute(
            """
            INSERT INTO Wards
                (ward_name, ward_type, capacity, available_capacity,
                 floor_no, status)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (
                ward_name,
                ward_type,
                capacity,
                capacity,
                floor_no,
                "Available"
            )
        )
        new_ward_id = cursor.lastrowid
        conn.commit()
        return jsonify(
            message="New ward added successfully.",
            ward_id=new_ward_id
        ), 201
    except Exception:
        conn.rollback()
        app.logger.exception("Ward creation or capacity update failed")
        return jsonify(
            error="Could not update or add ward. Check the server log."
        ), 500
    finally:
        cursor.close()
        conn.close()
@app.route("/api/wards", methods=["GET"])
def get_wards():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT ward_id, ward_name, ward_type, capacity,
                   available_capacity, floor_no, status
            FROM Wards
            ORDER BY ward_id
        """)
        wards = cursor.fetchall()
        return jsonify(wards), 200
    except Exception:
        app.logger.exception("Failed to fetch wards")
        return jsonify(error="Could not load wards"), 500
    finally:
        cursor.close()
        conn.close()
@app.route("/api/wards/<int:ward_id>", methods=["DELETE"])
@admin_required
def delete_ward(ward_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT ward_id FROM Wards WHERE ward_id = %s",
            (ward_id,)
        )
        ward = cursor.fetchone()
        if not ward:
            return jsonify(error="Ward not found"), 404
        cursor.execute(
            "SELECT COUNT(*) AS total FROM Patients WHERE ward_id = %s",
            (ward_id,)
        )
        patient_count = cursor.fetchone()["total"]
        if patient_count > 0:
            return jsonify(
                error="This ward has assigned patients. Reassign them before removing the ward."
            ), 409
        cursor.execute(
            "DELETE FROM Wards WHERE ward_id = %s",
            (ward_id,)
        )
        conn.commit()
        return jsonify(message="Ward removed successfully"), 200
    except Exception:
        conn.rollback()
        app.logger.exception("Ward removal failed")
        return jsonify(
            error="Ward could not be removed because linked records may exist."
        ), 409
    finally:
        cursor.close()
        conn.close()
@app.route("/api/ward-assignments", methods=["GET"])
@admin_required
def get_ward_assignments():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT
                p.patient_id,
                p.name AS patient_name,
                p.ward_id,
                w.ward_name,
                w.ward_type,
                'Assigned' AS status
            FROM Patients AS p
            INNER JOIN Wards AS w
                ON p.ward_id = w.ward_id
            ORDER BY p.patient_id DESC
        """)
        return jsonify(cursor.fetchall()), 200
    except Exception:
        app.logger.exception("Failed to fetch ward assignments")
        return jsonify(
            error="Could not load ward assignments"
        ), 500
    finally:
        cursor.close()
        conn.close()
@app.route("/api/my-ward", methods=["POST"])
def request_my_ward():
    if session.get("user_role") != "user":
        return jsonify(error="Please log in as a user"), 401
    data = request.get_json(silent=True) or {}
    ward_id = data.get("ward_id")
    if not ward_id:
        return jsonify(error="Please select a ward"), 400
    try:
        ward_id = int(ward_id)
    except (TypeError, ValueError):
        return jsonify(error="Invalid ward selected"), 400
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        conn.start_transaction()
        cursor.execute("""
            SELECT patient_id, ward_id
            FROM Patients
            WHERE user_id = %s
            FOR UPDATE
        """, (session["user_id"],))
        patient = cursor.fetchone()
        if not patient:
            conn.rollback()
            return jsonify(
                error="Please register your patient details first"
            ), 400
        old_ward_id = patient["ward_id"]
        if old_ward_id is not None and int(old_ward_id) == ward_id:
            conn.rollback()
            return jsonify(
                error="You are already assigned to this ward"
            ), 409
        cursor.execute("""
            SELECT ward_id, ward_name, available_capacity
            FROM Wards
            WHERE ward_id = %s
            FOR UPDATE
        """, (ward_id,))
        new_ward = cursor.fetchone()
        if not new_ward:
            conn.rollback()
            return jsonify(error="Ward not found"), 404
        if int(new_ward["available_capacity"]) <= 0:
            conn.rollback()
            return jsonify(error="This ward is full"), 409
        if old_ward_id is not None:
            cursor.execute("""
                UPDATE Wards
                SET available_capacity = available_capacity + 1
                WHERE ward_id = %s
            """, (old_ward_id,))
        cursor.execute("""
            UPDATE Patients
            SET ward_id = %s
            WHERE patient_id = %s
        """, (ward_id, patient["patient_id"]))
        cursor.execute("""
            UPDATE Wards
            SET available_capacity = available_capacity - 1
            WHERE ward_id = %s
        """, (ward_id,))
        conn.commit()
        return jsonify(
            success=True,
            message=(
                "Ward changed successfully"
                if old_ward_id is not None
                else "Ward reserved successfully"
            ),
            ward_name=new_ward["ward_name"]
        ), 200 if old_ward_id is not None else 201
    except Exception:
        conn.rollback()
        app.logger.exception("User ward selection failed")
        return jsonify(error="Unable to reserve or change ward"), 500
    finally:
        cursor.close()
        conn.close()



@app.route("/api/my-bookings", methods=["GET"])
@login_required
def my_bookings():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT
                a.appointment_id,
                d.name AS doctor_name,
                d.specialization,
                a.appointment_date,
                a.appointment_time,
                a.reason,
                a.status,
                a.requested_priority,
                a.queue_priority,
                a.queue_status,
                a.arrival_time,
                a.queue_service_start
            FROM Patients p
            JOIN Appointments a ON a.patient_id = p.patient_id
            JOIN Doctors d ON d.doctor_id = a.doctor_id
            WHERE p.user_id = %s
            ORDER BY a.appointment_date DESC, a.appointment_time DESC
        """, (session["user_id"],))

        appointments = cursor.fetchall()

        for appointment in appointments:
            for key, value in appointment.items():
                if hasattr(value, "isoformat"):
                    appointment[key] = value.isoformat()
                elif key == "appointment_time" and value is not None:
                    appointment[key] = str(value)

        cursor.execute("""
            SELECT w.ward_name, w.ward_type
            FROM Patients p
            JOIN Wards w ON w.ward_id = p.ward_id
            WHERE p.user_id = %s
        """, (session["user_id"],))

        ward = cursor.fetchone()

        return jsonify({
            "appointments": appointments,
            "ward": ward
        })
    except Exception:
        app.logger.exception("Could not load user bookings")
        return jsonify(error="Unable to load your bookings"), 500
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    app.run(debug=True)
