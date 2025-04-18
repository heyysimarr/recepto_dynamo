import os
import cv2
import numpy as np
import requests
import re
import json
import urllib.request
import os
import cv2

def download_and_load_models():
    if not os.path.exists("deploy.prototxt"):
        urllib.request.urlretrieve(
            "https://raw.githubusercontent.com/opencv/opencv/master/samples/dnn/face_detector/deploy.prototxt",
            "deploy.prototxt"
        )
    if not os.path.exists("res10_300x300_ssd_iter_140000.caffemodel"):
        urllib.request.urlretrieve(
            "https://github.com/opencv/opencv_3rdparty/raw/dnn_samples_face_detector_20170830/res10_300x300_ssd_iter_140000.caffemodel",
            "res10_300x300_ssd_iter_140000.caffemodel"
        )
    if not os.path.exists("nn4.small2.v1.t7"):
        urllib.request.urlretrieve(
            "https://storage.cmusatyalab.org/openface-models/nn4.small2.v1.t7",
            "nn4.small2.v1.t7"
        )

    detector = cv2.dnn.readNetFromCaffe("deploy.prototxt", "res10_300x300_ssd_iter_140000.caffemodel")
    embedder = cv2.dnn.readNetFromTorch("nn4.small2.v1.t7")
    return detector, embedder

def drive_to_direct(url: str) -> str:
    m = re.search(r'/d/([^/]+)', url)
    return f"https://drive.google.com/uc?export=view&id={m.group(1)}" if m else url

def url_to_image(url: str) -> np.ndarray:
    resp = requests.get(url, timeout=10)
    arr = np.frombuffer(resp.content, np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError(f"Unable to load image from {url}")
    return img

def get_embedding(image: np.ndarray, detector, embedder) -> np.ndarray:
    h, w = image.shape[:2]
    blob = cv2.dnn.blobFromImage(cv2.resize(image, (300, 300)), 1.0, (300, 300), (104.0, 177.0, 123.0))
    detector.setInput(blob)
    detections = detector.forward()
    if detections.shape[2] == 0:
        raise ValueError("No faces detected")
    i = np.argmax(detections[0, 0, :, 2])
    if detections[0, 0, i, 2] < 0.5:
        raise ValueError("No high-confidence face detected")
    box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
    x1, y1, x2, y2 = box.astype(int)
    face = image[y1:y2, x1:x2]
    face_blob = cv2.dnn.blobFromImage(cv2.resize(face, (96, 96)), 1.0 / 255, (96, 96), (0, 0, 0), swapRB=True, crop=False)
    embedder.setInput(face_blob)
    return embedder.forward().flatten()

# 2. Load models
detector, embedder = download_and_load_models()

# 3. Load dataset
with open("temp/all_linkedin_profiles.json", "r") as f:
    data = json.load(f)

# 4. Add image similarity score per entry
for person in data:
    url1 = person.get("image")
    url2 = drive_to_direct(person.get("drive_link"))

    try:
        img1 = url_to_image(url1)
        img2 = url_to_image(url2)
        emb1 = get_embedding(img1, detector, embedder)
        emb2 = get_embedding(img2, detector, embedder)

        emb1n = emb1 / np.linalg.norm(emb1)
        emb2n = emb2 / np.linalg.norm(emb2)

        cos_sim = float(np.dot(emb1n, emb2n))
        sim_score = (cos_sim + 1) / 2
    except Exception as e:
        print(f"Index {person['index']} error: {e} — similarity set to 0")
        sim_score = 0


    person["image_similarity"] = sim_score

# 5. Save updated dataset
with open("temp/all_linkedin_profiles_similarity.json", "w") as f:
    json.dump(data, f, indent=2)

print("Updated JSON")
