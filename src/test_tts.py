import pyttsx3

engine = pyttsx3.init()

engine.say(
    "Hello. I am EcoSort AI. "
    "This plastic bottle cannot be recycled until it is washed."
)

engine.runAndWait()