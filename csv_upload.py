import mysql.connector
import csv

conn = mysql.connector.connect(
    host="your_host",
    user="your_user",
    password="your_password",
    database="your_db"
)
cursor = conn.cursor()

with open("yourfile.csv", newline='') as csvfile:
    reader = csv.reader(csvfile)
    next(reader)  # skip header if exists
    for row in reader:
        cursor.execute(
            "INSERT INTO your_table (col1, col2, col3) VALUES (%s, %s, %s)",
            row
        )

conn.commit()
cursor.close()
conn.close()
