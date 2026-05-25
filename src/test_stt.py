import speech_recognition as sr

recognizer = sr.Recognizer()
mic = sr.Microphone()

print("Adjusting background noise...")
with mic as source:
    recognizer.adjust_for_ambient_noise(source, duration=1)

print("Say something now...")

try:
    with mic as source:
        audio = recognizer.listen(source, timeout=6, phrase_time_limit=6)

    text = recognizer.recognize_google(audio)
    print("You said:", text)

except sr.WaitTimeoutError:
    print("No speech detected.")

except sr.UnknownValueError:
    print("Could not understand the audio.")

except sr.RequestError as e:
    print("Speech recognition service error:", e)