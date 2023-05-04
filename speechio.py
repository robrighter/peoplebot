import tempfile
import os
from gtts import gTTS
from playsound import playsound
import speech_recognition as sr

class SpeechIO:
    def __init__(self):
        pass

    def speak_text(self, text):
        print("SPEAKING:: " + text)
        tts = gTTS(text=text, lang='en', slow=False)
        with tempfile.NamedTemporaryFile(delete=True) as fp:
            temp_file = f"{fp.name}.mp3"
        tts.save(temp_file)
        playsound(temp_file)
        os.remove(temp_file)

    def listen_to_speech(self):
        # Create a recognizer object
        r = sr.Recognizer()
        with sr.Microphone() as source:
            print("Listening...")
            # Use the recognizer to listen to the audio from the microphone
            audio = r.listen(source)
        # Try to recognize the speech using Google's speech recognition service
        try:
            print("Processing...")
            text = r.recognize_google(audio)
            return text
        except sr.UnknownValueError:
            return "Google Speech Recognition could not understand audio"
        except sr.RequestError as e:
            return "Could not request results from Google Speech Recognition service; {0}".format(e)


