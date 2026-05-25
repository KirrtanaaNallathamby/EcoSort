import cv2


def get_camera(index=0):
    cap = cv2.VideoCapture(index)

    if not cap.isOpened():
        raise RuntimeError("Camera could not be opened. Try camera index 1 or 2.")

    return cap