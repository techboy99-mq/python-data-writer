import http.server
import argparse
import sys
import json
import csv
import re
import socket
from urllib.parse import urlparse
from datetime import datetime
import mysql.connector

# -----------------------------
# Config
# -----------------------------
AUTH_TOKEN = "secure_token_here"
CSV_FILE_PATH = "name_of_csv_file_here.csv"
LOG_FILE_PATH = f"path_to_log_file/{hostname}_data_writer.log"

DB_CONFIG = {
    "host": "192.168.0.50",   # Change this to your DB host
    "user": "youruser",
    "password": "yourpassword",
    "database": "yourdb"
}

# -----------------------------
# Logging setup
# -----------------------------
LOG_FILE = open(LOG_FILE_PATH, "a")
sys.stdout = LOG_FILE
sys.stderr = LOG_FILE
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

# -----------------------------
# Request Handler
# -----------------------------
class DataRequestHandler(http.server.BaseHTTPRequestHandler):

    def do_POST(self):
        # Simple route check
        if self.path != "/submit":
            self.send_error(404, "Not Found")
            return

        # Auth check
        auth = self.headers.get("Authorization")
        if not auth or auth != f"Bearer {AUTH_TOKEN}":
            self.send_response(401)
            self.end_headers()
            self.wfile.write(b"Unauthorized")
            return

        # Read and parse JSON body
        content_length = int(self.headers.get("Content-Length", 0))
        raw_body = self.rfile.read(content_length)

        try:
            data = json.loads(raw_body)
        except json.JSONDecodeError:
            self.send_json_error("Invalid JSON")
            return

        # Extract and validate fields
        hostname = data.get("hostname", "").strip()
        mq_install_type = data.get("mq_install_type", "").strip()
        mq_version = data.get("mq_version", "").strip()
        date_str = data.get("date", "").strip()
        time_str = data.get("time", "").strip()
        install_status = data.get("install_status", "").strip()
        install_result = data.get("install_result", "").strip()

        if not (0 < len(hostname) <= 63):
            return self.send_json_error("Invalid hostname length")
        if not re.match(r"^[a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?$", hostname):
            return self.send_json_error("Invalid hostname format")
        if mq_install_type not in {"MQ Client", "MQ Server"}:
            return self.send_json_error("Invalid install type")
        if not re.match(r"^\d+\.\d+\.\d+(?:\.\d+)?$", mq_version):
            return self.send_json_error("Invalid MQ version format")
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            return self.send_json_error("Invalid date format. Expected YYYY-MM-DD")
        try:
            datetime.strptime(time_str, "%H:%M")
        except ValueError:
            return self.send_json_error("Invalid time format. Expected HH:MM")
        if install_status not in {"Success", "Fail"}:
            return self.send_json_error("Invalid install status")

        # -----------------------------
        # Write to CSV
        # -----------------------------
        try:
            with open(CSV_FILE_PATH, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    hostname,
                    mq_install_type,
                    mq_version,
                    date_str,
                    time_str,
                    install_status,
                    install_result
                ])
        except Exception as e:
            return self.send_json_error(f"Failed to write to CSV: {str(e)}", status=500)

        # -----------------------------
        # Write to MariaDB
        # -----------------------------
        try:
            conn = mysql.connector.connect(**DB_CONFIG)
            cursor = conn.cursor()
            sql = """
                INSERT INTO installs
                (hostname, mq_install_type, mq_version, date, time, install_status, install_result)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(sql, (
                hostname,
                mq_install_type,
                mq_version,
                date_str,
                time_str,
                install_status,
                install_result
            ))
            conn.commit()
            cursor.close()
            conn.close()
        except Exception as e:
            return self.send_json_error(f"Failed to write to DB: {str(e)}", status=500)

        # Success response
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"status": "success"}).encode())

    def send_json_error(self, message, status=400):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"error": message}).encode())

# -----------------------------
# Main
# -----------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--ip", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8080)
    args = parser.parse_args()

    server = http.server.HTTPServer((args.ip, args.port), DataRequestHandler)
    print(f"Server running on http://{args.ip}:{args.port}")
    server.serve_forever()
