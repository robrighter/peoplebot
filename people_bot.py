import cv2
import face_recognition
import uuid
import time
import threading
import json

from db import FaceDatabase
from speechio import SpeechIO
from chatgpt import ChatGPTWrap


KNOWN_FACES_DIR = "known_faces"
DATABASE_FILE = "faces.db"
NAME = "Radar"
speech = SpeechIO()
chat = ChatGPTWrap(NAME)


def have_a_conversation(db, faces_in_frame):
    while True:
        print("We have " + str(len(faces_in_frame)) + " faces in context")
        #for now we are only going to talk to the first person we see. If multiple people are in frame we ignore everyone but 1
        face = ""
        if len(faces_in_frame) > 0:
            key = list(faces_in_frame.keys())[0]
            face = faces_in_frame[key]
            context = face[2]
            face_id = face[0]
            db.print_row_details(face)
            conversation_history = []
            user_input = ""
            if context is None:
                user_input = "This is the start of a new friendship. We have never met before. Let's get to know each other and be friends."
            else:
                user_input = "Let's continue our previous discussion. Remember only to repspond with that JSON object format. Here is a quick summary of what we talked about last time  " + context
            ai_response = chat.chat_with_gpt(conversation_history, user_input )
            print("AI: " + ai_response['reply'])
            speech.speak_text(ai_response['reply'])
            while True:
                user_input = speech.listen_to_speech()
                ai_response = chat.chat_with_gpt(conversation_history, user_input)
                print("AI: " + ai_response['reply'])
                speech.speak_text(ai_response['reply'])
                if bool(str(ai_response['name'])):
                    db.update_name(face_id, ai_response['name'])
                db.update_last_talked(face_id, ai_response['summary'])
                if ai_response['should_end']:
                    print('AI thinks that the conversation is over.')
                    break

            
        time.sleep(10)


def main():
    db = FaceDatabase(db_path=DATABASE_FILE, known_faces_dir=KNOWN_FACES_DIR)
    db.create_table()
    faces_in_frame = {}

    known_uuids, known_face_encodings = db.load_known_face_encodings()

    video_capture = cv2.VideoCapture(0)
    start_time = None

    convesation_thread = threading.Thread(target=have_a_conversation, args=(db, faces_in_frame, ))
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
                        face_row = db.query_face_row(matched_uuid)
                        faces_in_frame[matched_uuid] = face_row
                    else:
                        name = "unknown"
                        unique_id = str(uuid.uuid4())
                        known_face_encodings.append(face_encodings[0])
                        known_uuids.append(unique_id)
                        db.save_face_encoding(unique_id, face_encodings[0])
                        db.insert_row(unique_id, name)
                        face_row = db.query_face_row(unique_id)
                        faces_in_frame[unique_id] = face_row
                start_time = None

        else:
            faces_in_frame.clear()
            start_time = None

        cv2.imshow("Video", frame)
        time.sleep(3)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    video_capture.release()
    cv2.destroyAllWindows()
    conn.close()



if __name__ == "__main__":
    main()