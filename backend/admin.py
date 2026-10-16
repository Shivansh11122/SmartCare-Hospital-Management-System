
from werkzeug.security import generate_password_hash
from getpass import getpass

from db import get_connection


def create_admin():
    name = input("Enter admin name: ").strip()
    email = input("Enter admin email: ").strip().lower()
    password = getpass("Create admin password: ")

    if not name or not email or not password:
        print("All fields are required.")
        return

    if len(password) < 12:
        print("Use a password of at least 12 characters.")
        return

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "SELECT user_id FROM Users WHERE email = %s",
            (email,)
        )

        if cursor.fetchone():
            print("An account with this email already exists.")
            return

        password_hash = generate_password_hash(password)

        cursor.execute("""
            INSERT INTO Users (name, email, password, role)
            VALUES (%s, %s, %s, %s)
        """, (name, email, password_hash, "admin"))

        conn.commit()
        print("Admin account created successfully.")

    except Exception as error:
        conn.rollback()
        print("Could not create admin account:", error)

    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    create_admin()
