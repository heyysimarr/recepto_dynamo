import cv2
import numpy as np
import requests

face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

def convert_drive_url_to_direct(url):
    if "drive.google.com" in url:
        if "id=" in url:
            file_id = url.split("id=")[-1]
        elif "/file/d/" in url:
            file_id = url.split("/file/d/")[1].split("/")[0]
        else:
            raise ValueError("Unrecognized Google Drive URL format.")
        return f"https://drive.google.com/uc?export=download&id={file_id}"
    return url

def detect_human_in_image(image_url):
    image_url = convert_drive_url_to_direct(image_url)

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    try:
        response = requests.get(image_url, headers=headers, timeout=15)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise ValueError(f"Failed to download image from URL: {e}")

    image_array = np.asarray(bytearray(response.content), dtype=np.uint8)
    img = cv2.imdecode(image_array, cv2.IMREAD_COLOR)

    if img is None:
        raise ValueError("Failed to decode the image from the downloaded data.")

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=4)

    if len(faces) > 0:
        print("✅ Face detected!")
        return True
    else:
        print("❌ No face detected.")
        return False
