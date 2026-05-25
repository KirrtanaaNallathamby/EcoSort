import queue
import threading
import time
import pyttsx3
import speech_recognition as sr


class VoiceNode:
    def __init__(self):
        self.text_queue = queue.Queue()

        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()

        self.running = True
        self.is_speaking = False

        print("[VOICE] Adjusting background noise...")
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=1)

        self.listen_thread = threading.Thread(
            target=self._listen_loop,
            daemon=True
        )
        self.listen_thread.start()

    def speak(self, text):
        print(f"[ROBOT]: {text}")

        self.is_speaking = True

        try:
            engine = pyttsx3.init()
            engine.setProperty("rate", 165)
            engine.say(text)
            engine.runAndWait()
            engine.stop()
        except Exception as e:
            print("[TTS ERROR]", e)

        time.sleep(0.5)
        self.is_speaking = False

    def _listen_loop(self):
        while self.running:
            if self.is_speaking:
                time.sleep(0.1)
                continue

            try:
                with self.microphone as source:
                    print("[VOICE] Listening in background...")
                    audio = self.recognizer.listen(
                        source,
                        timeout=5,
                        phrase_time_limit=5
                    )

                text = self.recognizer.recognize_google(audio).lower()
                print(f"[USER]: {text}")
                self.text_queue.put(text)

            except sr.WaitTimeoutError:
                continue
            except sr.UnknownValueError:
                continue
            except sr.RequestError as e:
                print("[VOICE ERROR]", e)

    def get_latest_speech(self):
        try:
            return self.text_queue.get_nowait()
        except queue.Empty:
            return ""

    def stop(self):
        self.running = False