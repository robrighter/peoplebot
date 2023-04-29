from gtts import gTTS
from playsound import playsound
import os
import tempfile
import cv2
import face_recognition
import sqlite3
import uuid
import pickle
import time
import openai


KNOWN_FACES_DIR = "known_faces"
NAME = "Radar"
# Set up API key and library
openai.api_key = os.getenv("OPENAI_API_KEY")


def chat_with_gpt(user_input, conversation_history):
    if not conversation_history:
        conversation_history.append({
            "role": "assistant",
            "content": "You're name is  "+NAME+". It's time to make a new friend. You are speaking with a person you have never met. Your goal is to learn as much as possible about the person and be a good friend."
        })

    conversation_history.append({"role": "user", "content": user_input})

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=conversation_history,
        max_tokens=150,
        n=1,
        stop=None,
        temperature=0.5,
    )

    message = response.choices[0].message["content"]
    conversation_history.append({"role": "assistant", "content": message})
    return message


def summarize_conversation(conversation_history):
    system_prompt = {
        "role": "system",
        "content": "Your task is to summarize the conversation, capturing important parts to be reused as context the next time we talk with this person."
    }
    conversation_history.append(system_prompt)

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=conversation_history,
        max_tokens=100,
        n=1,
        stop=None,
        temperature=0.5,
    )

    summary = response.choices[0].message["content"]
    return summary


def speak_text(text):
    print("SPEAKING:: " + text)
    tts = gTTS(text=text, lang='en', slow=False)
    with tempfile.NamedTemporaryFile(delete=True) as fp:
        temp_file = f"{fp.name}.mp3"
    tts.save(temp_file)
    playsound(temp_file)
    os.remove(temp_file)


def create_database_connection():
    conn = sqlite3.connect('faces.db')
    return conn

def create_table(conn):
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS faces (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        context TEXT,
        last_talked TIMESTAMP
    )
    """)
    conn.commit()

def insert_row(conn, id, name):
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO faces (id, name, last_talked) VALUES (?, ?, ?)
    """, (id, name, int(time.time())))
    conn.commit()

def update_last_talked(conn, id, context):
    cursor = conn.cursor()
    cursor.execute("""
    UPDATE faces SET last_talked = ?, context = ? WHERE id = ?
    """, (int(time.time()), context, id))
    conn.commit()

def query_face_row(conn, id):
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM faces WHERE id=?", (id,))
    return cursor.fetchone()

def print_row_details(row):
    # print(str(row))
    print(f"ID: {row[0]}\nName: {row[1]}\nContext: {row[2]}\n")


def save_face_encoding(id, face_encoding):
    with open(os.path.join(KNOWN_FACES_DIR, f"{id}.pickle"), "wb") as f:
        pickle.dump(face_encoding, f)


def load_known_face_encodings():
    face_encodings = []
    uuids = []

    for filename in os.listdir(KNOWN_FACES_DIR):
        with open(os.path.join(KNOWN_FACES_DIR, filename), "rb") as f:
            face_encodings.append(pickle.load(f))
            uuids.append(filename[:-7])  # Remove '.pickle' extension

    return uuids, face_encodings


def have_a_conversation(face_row, conn):
    print("Face details:")
    print_row_details(face_row)
    speak_text("Hello " + face_row[1] + ", it's nice to see you again.")
    
    conversation_history = []
    user_input = ""

    while True:
        user_input = input("You: ")
        if user_input.lower() == "exit":
            break

        ai_response = chat_with_gpt(user_input, conversation_history)
        print("AI: " + ai_response)
        speak_text(ai_response)

    context = summarize_conversation(conversation_history)
    update_last_talked(conn, face_row[0], context)


def main():
    if not os.path.exists(KNOWN_FACES_DIR):
        os.makedirs(KNOWN_FACES_DIR)
    conn = create_database_connection()
    create_table(conn)

    known_uuids, known_face_encodings = load_known_face_encodings()

    video_capture = cv2.VideoCapture(0)
    start_time = None

    while True:
        ret, frame = video_capture.read()

        if not ret:
            break

        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)

        face_locations = face_recognition.face_locations(small_frame)   

        if len(face_locations) == 1:
            if start_time is None:
                start_time = time.time()
            elif time.time() - start_time >= 3:
                face_encodings = face_recognition.face_encodings(small_frame, face_locations)

                if len(face_encodings) == 1:
                    matches = face_recognition.compare_faces(known_face_encodings, face_encodings[0], tolerance=0.6)

                    if any(matches):
                        print("Face already exists in the database.")
                        matched_uuid = known_uuids[matches.index(True)]
                        print("Face already exists in the database.")
                        face_row = query_face_row(conn, matched_uuid)
                        have_a_conversation(face_row, conn)
                    else:
                        speak_text("Please input your name.")
                        name = input()
                        unique_id = str(uuid.uuid4())
                        save_face_encoding(unique_id, face_encodings[0])
                        insert_row(conn, unique_id, name)
                        speak_text("Nice to meet you " + name)
                        print(f"Face encoding saved as {unique_id}.pickle and added to the database.")
                start_time = None

        elif len(face_locations) > 1:
            speak_text("I can only talk to one person at a time. I see more than one person in front of me.")
            start_time = None
        else:
            start_time = None

        cv2.imshow("Video", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    video_capture.release()
    cv2.destroyAllWindows()
    conn.close()




if __name__ == "__main__":
    main()