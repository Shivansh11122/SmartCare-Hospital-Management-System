
from db import get_connection

try:
    conn = get_connection()
    print("MySQL connected successfully!")

    cursor = conn.cursor()
    cursor.execute("SHOW TABLES")

    print("\nTables in smart_hospital:")
    for table in cursor.fetchall():
        print(table[0])

    cursor.close()
    conn.close()

except Exception as e:
    print("Connection failed:", e)
