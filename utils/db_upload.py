# db_upload.py

import mysql.connector
from config.db_config import DB_HOST, DB_USER, DB_PASSWORD, DB_NAME

def upload_to_mysql(data):
    try:
        conn = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS labeled_data (
                id INT AUTO_INCREMENT PRIMARY KEY,
                filename VARCHAR(255),
                transcription TEXT,
                labels VARCHAR(255),
                start_time VARCHAR(50),
                end_time VARCHAR(50)
            )
        """)

        for entry in data:
            cursor.execute("""
                INSERT INTO labeled_data (filename, transcription, labels, start_time, end_time)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                entry["filename"],
                entry["transcription"],
                entry["labels"],
                entry["start_time"],
                entry["end_time"]
            ))

        conn.commit()
        cursor.close()
        conn.close()
    except mysql.connector.Error as err:
        print(f"MySQL Error: {err}")
    except Exception as e:
        print(f"Unexpected error: {e}")
