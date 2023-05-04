import sqlite3
import time
import os
import pickle

class FaceDatabase:
    def __init__(self, db_path='faces.db', known_faces_dir='known_faces'):
        if not os.path.exists(known_faces_dir):
            os.makedirs(known_faces_dir)
        self.db_path = db_path
        self.known_faces_dir = known_faces_dir
        self.conn = self.create_database_connection()


    def create_database_connection(self):
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        return conn

    def create_table(self):
        cursor = self.conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS faces (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            context TEXT,
            last_talked TIMESTAMP
        )
        """)
        self.conn.commit()

    def insert_row(self, id, name):
        cursor = self.conn.cursor()
        cursor.execute("""
        INSERT INTO faces (id, name, last_talked) VALUES (?, ?, ?)
        """, (id, name, int(time.time())))
        self.conn.commit()

    def update_name(self, id, name):
        print("updating name")
        cursor = self.conn.cursor()
        cursor.execute("""
        UPDATE faces SET name = ? WHERE id = ?
        """, (str(name), str(id)))
        self.conn.commit()

    def update_last_talked(self, id, context):
        print("updating last talked")
        cursor = self.conn.cursor()
        cursor.execute("""
        UPDATE faces SET last_talked = ?, context = ? WHERE id = ?
        """, (int(time.time()), str(context), str(id)))
        self.conn.commit()

    def query_face_row(self, id):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM faces WHERE id=?", (id,))
        return cursor.fetchone()

    def print_row_details(self, row):
        print(str(row))
        print(f"ID: {row[0]}\nName: {row[1]}\nContext: {row[2]}\n")

    def save_face_encoding(self, id, face_encoding):
        with open(os.path.join(self.known_faces_dir, f"{id}.pickle"), "wb") as f:
            pickle.dump(face_encoding, f)

    def load_known_face_encodings(self):
        face_encodings = []
        uuids = []

        for filename in os.listdir(self.known_faces_dir):
            with open(os.path.join(self.known_faces_dir, filename), "rb") as f:
                face_encodings.append(pickle.load(f))
                uuids.append(filename[:-7])  # Remove '.pickle' extension

        return uuids, face_encodings
