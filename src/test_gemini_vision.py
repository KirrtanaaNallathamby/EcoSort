import os
import cv2
from dotenv import load_dotenv
from google import genai

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

cap = cv2.VideoCapture(0)

print("Press SPACE to capture image, or Q to quit.")

while True:
    ret, frame = cap.read()

    if not ret:
        print("Camera error.")
        break

    cv2.imshow("Gemini Vision Test", frame)

    key = cv2.waitKey(1) & 0xFF

    if key == ord("q"):
        break

    if key == 32:  # SPACE key
        image_path = "../captures/test_gemini_image.jpg"
        cv2.imwrite(image_path, frame)
        print("Image saved:", image_path)

        uploaded_image = client.files.upload(file=image_path)

        response = client.models.generate_content(
            model="gemini-3.1-flash-lite",
            contents=[
                uploaded_image,
                """
                Look at this image.
                Identify the waste item if visible.
                Explain whether it can be recycled.
                If not, explain what the user should do.
                Keep it short.
                """
            ],
        )

        print("\nGemini Vision Response:")
        print(response.text)

cap.release()
cv2.destroyAllWindows()