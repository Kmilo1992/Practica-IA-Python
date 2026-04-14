import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import serial
 
# 🔧 Model path (same folder recommended)
MODEL_PATH = "hand_landmarker.task"
 
# 🔌 Arduino connection (change COM port if needed)
arduino = serial.Serial('COM3', 9600)
 
# AI Model configuration
base_options = python.BaseOptions(model_asset_path=MODEL_PATH)
 
options = vision.HandLandmarkerOptions(
    base_options=base_options,
    num_hands=1,
    min_hand_detection_confidence=0.7,
    min_hand_presence_confidence=0.7,
    min_tracking_confidence=0.7
)
 
landmarker = vision.HandLandmarker.create_from_options(options)
 
# Finger counting function
def count_fingers(landmarks):
    fingers = []
 
    # Thumb
    if landmarks[4].x < landmarks[3].x:
        fingers.append(1)
    else:
        fingers.append(0)
 
    # Other fingers
    for tip in [8, 12, 16, 20]:
        if landmarks[tip].y < landmarks[tip - 2].y:
            fingers.append(1)
        else:
            fingers.append(0)
 
    return sum(fingers)
 
#Camera setup (Windows fix included)
cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
 
if not cap.isOpened():
    print("❌ Camera error")
    exit()
else:
    print("✅ Camera working")
 
last_value = -1  # Avoid sending repeated values
 
while True:
    ret, frame = cap.read()
 
    if not ret:
        print("⚠️ Frame not read")
        continue
 
    # Mirror effect
    frame = cv2.flip(frame, 1)
 
    # Convert to RGB
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
 
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
 
    # AI detection
    result = landmarker.detect(mp_image)
 
    if result.hand_landmarks:
        for hand_landmarks in result.hand_landmarks:
 
            finger_count = count_fingers(hand_landmarks)
 
            # Send only if value changes (prevents flickering)
            if finger_count != last_value:
                print("Fingers:", finger_count)
                arduino.write(bytes(str(finger_count) + '\n', 'utf-8'))
                last_value = finger_count
 
            # Draw landmarks
            h, w, _ = frame.shape
            for lm in hand_landmarks:
                cx, cy = int(lm.x * w), int(lm.y * h)
                cv2.circle(frame, (cx, cy), 5, (0, 255, 0), -1)
 
            # Display text
            cv2.putText(frame, f"Fingers: {finger_count}",
                        (20, 50),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        1,
                        (0, 255, 0),
                        2)
 
    cv2.imshow("AI LED Control", frame)
 
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
 
cap.release()
arduino.close()
cv2.destroyAllWindows()
