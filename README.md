Start Python HTTP Data Writer Server: 

python3 simple_data_writer.py


Write data to the Python HTTP CSV Server with the following:

curl -X POST http://localhost:8080/submit
-H "Authorization: Bearer your_secure_token_here"
-H "Content-Type: application/json"
-d '{ "hostname": "mq-host-01", "mq_install_type": "client", "mq_version": "9.3.5", "date": "2025-07-04", "time": "19:00", "install_status": "success", "install_result": "N/A" }'

SystemD File Details:

WorkingDirectory: Set this to the directory you want the server to serve (like /var/www/html or your project folder). ExecStart: Launches Python’s built-in HTTP server on port 8000. ExecStop: Sends a SIGTERM to the process to stop it cleanly. Restart=on-failure: Restarts the server if it crashes (optional).


MySQL DB Setup:

CREATE TABLE installs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    hostname VARCHAR(63) NOT NULL,
    mq_install_type ENUM('MQ Client', 'MQ Server') NOT NULL,
    mq_version VARCHAR(20) NOT NULL,
    date DATE NOT NULL,
    time TIME NOT NULL,
    install_status ENUM('Success', 'Fail') NOT NULL,
    install_result TEXT NOT NULL
);
