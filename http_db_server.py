import http.server
import argparse
import json
import mysql.connector
from urllib.parse import urlparse

# ----------------------------
# Configure your database here
# ----------------------------
DB_CONFIG = {
    "host": "your_db_host",
    "user": "your_db_user",
    "password": "your_db_password",
    "database": "mydb"
}

# ----------------------------
# HTTP Request Handler
# ----------------------------
class DBRequestHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urlparse(self.path)
        
        # Only handle /data endpoint
        if parsed_path.path != "/data":
            self.send_error(404, "Not Found")
            return
        
        try:
            # Connect to MariaDB
            conn = mysql.connector.connect(**DB_CONFIG)
            cursor = conn.cursor(dictionary=True)
            
            # Query your installs table
            cursor.execute("""
                SELECT hostname, mq_install_type, mq_version, date, time, install_status, install_result 
                FROM installs
            """)
            rows = cursor.fetchall()
            
            # Close DB connection
            cursor.close()
            conn.close()
            
            # Send JSON response
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(rows, default=str).encode())
        
        except mysql.connector.Error as e:
            self.send_error(500, f"Database error: {str(e)}")
    
    def log_message(self, format, *args):
        # Optional: suppress default logging
        return

# ----------------------------
# Run the HTTP server
# ----------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--ip", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8080)
    args = parser.parse_args()

    server = http.server.HTTPServer((args.ip, args.port), DBRequestHandler)
    print(f"Server running on http://{args.ip}:{args.port}")
    server.serve_forever()
