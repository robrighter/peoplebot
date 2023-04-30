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
import threading
import json


KNOWN_FACES_DIR = "known_faces"
NAME = "Radar"
# Set up API key and library
openai.api_key = os.getenv("OPENAI_API_KEY")

GPT_SYSTEM_ROLE_PROMPT = ("You're name is  "+NAME+". You are either speaking with a person you have never met or"
                          " continuing a conversation with an existing friend. Your goal"
                          " is to learn as much as possible about the person and be a good friend."
                          " THIS IS VERY IMPORTANT: Each time you respond only reply with a JSON object that has 4"
                          " properties: 'reply' which is your conversational reply in the conversation,"
                          " 'name' which is the name of the person you are talking to if you know it (otherwise null),"
                          " 'should_end' which is a boolean value that is true if the conversation"
                          " has come to a reasonable stopping point, and 'summary' which is a full summary"
                          " of what you know about the person. This summary will be used to remember details about this"
                          " person the next time you speak with them.")


def chat_with_gpt(conversation_history, user_input):
    print('The conversation history is:')
    print(conversation_history)

    if not conversation_history:
        conversation_history.append({
            "role": "system",
            "content": GPT_SYSTEM_ROLE_PROMPT 
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
    print("GOT BACK THIS MESSAGE:")
    print(message)
    parsedDict = json.loads(message)
    conversation_history.append({"role": "assistant", "content": message })
    return parsedDict


def speak_text(text):
    print("SPEAKING:: " + text)
    tts = gTTS(text=text, lang='en', slow=False)
    with tempfile.NamedTemporaryFile(delete=True) as fp:
        temp_file = f"{fp.name}.mp3"
    tts.save(temp_file)
    playsound(temp_file)
    os.remove(temp_file)


def create_database_connection():
    conn = sqlite3.connect('faces.db', check_same_thread=False)
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

def update_name(conn, id, name):
    print("updating name")
    cursor = conn.cursor()
    cursor.execute("""
    UPDATE faces SET name = ? WHERE id = ?
    """, (str(name), str(id)))
    conn.commit()

def update_last_talked(conn, id, context):
    print("updating last talked")
    cursor = conn.cursor()
    cursor.execute("""
    UPDATE faces SET last_talked = ?, context = ? WHERE id = ?
    """, (int(time.time()), str(context), str(id)))
    conn.commit()

def query_face_row(conn, id):
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM faces WHERE id=?", (id,))
    return cursor.fetchone()

def print_row_details(row):
    print(str(row))
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


def have_a_conversation(conn, faces_in_frame):
    while True:
        print("We have " + str(len(faces_in_frame)) + " faces in context")
        #for now we are only going to talk to the first person we see. If multiple people are in frame we ignore everyone but 1
        face = ""
        if len(faces_in_frame) > 0:
            key = list(faces_in_frame.keys())[0]
            face = faces_in_frame[key]
            context = face[2]
            face_id = face[0]
            print_row_details(face)
            conversation_history = []
            user_input = ""
            if context is None:
                user_input = "This is the start of a new friendship. We have never met before. Let's get to know each other and be friends."
            else:
                user_input = "Let's continue our previous discussion. Remember only to repspond with that JSON object format. Here is a quick summary of what we talked about last time  " + context
            ai_response = chat_with_gpt(conversation_history, user_input )
            print("AI: " + ai_response['reply'])
            speak_text(ai_response['reply'])
            while True:
                user_input = input("You: ")
                ai_response = chat_with_gpt(conversation_history, user_input)
                print("AI: " + ai_response['reply'])
                speak_text(ai_response['reply'])
                if bool(str(ai_response['name'])):
                    update_name(conn, face_id, ai_response['name'])
                update_last_talked(conn, face_id, ai_response['summary'])
                if ai_response['should_end']:
                    print('AI thinks that the conversation is over.')
                    break

            
        time.sleep(10)
        


def main():
    if not os.path.exists(KNOWN_FACES_DIR):
        os.makedirs(KNOWN_FACES_DIR)
    conn = create_database_connection()
    create_table(conn)
    faces_in_frame = {}

    known_uuids, known_face_encodings = load_known_face_encodings()

    video_capture = cv2.VideoCapture(0)
    start_time = None

    convesation_thread = threading.Thread(target=have_a_conversation, args=(conn, faces_in_frame, ))
    convesation_thread.start()

    while True:
        ret, frame = video_capture.read()

        if not ret:
            break

        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)

        face_locations = face_recognition.face_locations(small_frame)   

        if len(face_locations) > 0:
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
                        faces_in_frame[matched_uuid] = face_row
                    else:
                        name = "unknown"
                        unique_id = str(uuid.uuid4())
                        known_face_encodings.append(face_encodings[0])
                        known_uuids.append(unique_id)
                        save_face_encoding(unique_id, face_encodings[0])
                        insert_row(conn, unique_id, name)
                        face_row = query_face_row(conn, unique_id)
                        faces_in_frame[unique_id] = face_row
                start_time = None

        else:
            faces_in_frame.clear()
            start_time = None

        #cv2.imshow("Video", frame)
        time.sleep(3)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    video_capture.release()
    cv2.destroyAllWindows()
    conn.close()



if __name__ == "__main__":
    main()