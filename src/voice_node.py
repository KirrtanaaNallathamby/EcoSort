import queue
import threading
import time

import pyttsx3
import speech_recognition as sr


class VoiceNode:
    def __init__(self, backend="desktop"):
        self.backend = backend
        self.text_queue = queue.Queue()
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.running = True
        self.is_speaking = False
        self._sound_client = None

        if self.backend == "robot":
            self._init_robot_tts()

        print("[VOICE] Adjusting background noise...")
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=1)

        self.listen_thread = threading.Thread(target=self._listen_loop, daemon=True)
        self.listen_thread.start()

    def _init_robot_tts(self):
        try:
            from sound_play.libsoundplay import SoundClient

            self._sound_client = SoundClient()
            time.sleep(1)
            print("[VOICE] Using Juno sound_play TTS backend.")
        except ImportError:
            print("[VOICE] sound_play not found, falling back to pyttsx3.")
            self.backend = "desktop"

    def speak(self, text):
        print("[ROBOT]: {text}".format(text=text))
        self.is_speaking = True

        try:
            if self.backend == "robot" and self._sound_client is not None:
                self._sound_client.stopAll()
                self._sound_client.say(text)
                time.sleep(max(2.0, len(text) * 0.06))
            else:
                engine = pyttsx3.init()
                engine.setProperty("rate", 165)
                engine.say(text)
                engine.runAndWait()
                engine.stop()
        except Exception as error:
            print("[TTS ERROR]", error)

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
                        phrase_time_limit=5,
                    )

                text = self.recognizer.recognize_google(audio).lower()
                print("[USER]: {text}".format(text=text))
                self.text_queue.put(text)

            except sr.WaitTimeoutError:
                continue
            except sr.UnknownValueError:
                continue
            except sr.RequestError as error:
                print("[VOICE ERROR]", error)

    def get_latest_speech(self):
        try:
            return self.text_queue.get_nowait()
        except queue.Empty:
            return ""

    def stop(self):
        self.running = False
