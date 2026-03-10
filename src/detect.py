import cv2
import mediapipe as mp
import numpy as np
import threading
import subprocess
import os
import time

# ---------- SOUND PATH ----------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ALARM_PATH = os.path.join(BASE_DIR, "sounds", "alarm.mp3")

# ---------- EYE LANDMARK INDICES ----------
LEFT_EYE  = [33, 160, 158, 133, 153, 144]
RIGHT_EYE = [362, 385, 387, 263, 373, 380]

# ---------- TUNABLE SETTINGS ----------
EAR_THRESHOLD   = 0.25   # raised from 0.20 — catches real closes more reliably
CLOSED_FRAME_LIMIT = 90  # 3s at 30fps before alert fires
ALERT_COOLDOWN  = 3.0    # seconds before alert can fire again

# ---------- STATE ----------
CLOSED_FRAMES   = 0
ALERT_ACTIVE    = False
LAST_ALERT_TIME = 0.0
alarm_process   = None   # subprocess handle so we can kill it when eyes open


def play_alarm():
    global alarm_process
    sound = ALARM_PATH if os.path.exists(ALARM_PATH) else "/System/Library/Sounds/Funk.aiff"
    alarm_process = subprocess.Popen(["afplay", sound])
    alarm_process.wait()  # block thread until sound finishes naturally
    alarm_process = None


def stop_alarm():
    global alarm_process
    if alarm_process and alarm_process.poll() is None:
        alarm_process.terminate()
        alarm_process = None


def alert_user():
    try:
        os.system("""osascript -e 'display notification "Eyes closed detected!" with title "VisionAlert"'""")
    except Exception as e:
        print(f"Notification error: {e}")
    play_alarm()


def euclidean(p1, p2):
    return np.linalg.norm(np.array(p1) - np.array(p2))


def eye_aspect_ratio(landmarks, eye_indices, w, h):
    pts = [(landmarks[i].x * w, landmarks[i].y * h) for i in eye_indices]
    p1, p2, p3, p4, p5, p6 = pts

    vertical   = euclidean(p2, p6) + euclidean(p3, p5)
    horizontal = euclidean(p1, p4)

    return vertical / (2.0 * horizontal)


def draw_eye_outline(frame, landmarks, eye_indices, w, h, color):
    pts = np.array(
        [(int(landmarks[i].x * w), int(landmarks[i].y * h)) for i in eye_indices],
        dtype=np.int32
    )
    # draw filled polygon outline
    cv2.polylines(frame, [pts], isClosed=True, color=color, thickness=1)
    for pt in pts:
        cv2.circle(frame, tuple(pt), 2, color, -1)


# ---------- MEDIAPIPE SETUP ----------
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(
    static_image_mode=False,
    max_num_faces=1,
    refine_landmarks=True,       # enables iris landmarks for better accuracy
    min_detection_confidence=0.6,
    min_tracking_confidence=0.6
)

cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    h, w, _ = frame.shape
    rgb     = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = face_mesh.process(rgb)

    if results.multi_face_landmarks:
        for face_landmarks in results.multi_face_landmarks:
            landmarks = face_landmarks.landmark

            left_ear  = eye_aspect_ratio(landmarks, LEFT_EYE,  w, h)
            right_ear = eye_aspect_ratio(landmarks, RIGHT_EYE, w, h)
            ear       = (left_ear + right_ear) / 2.0

            eyes_closed = ear < EAR_THRESHOLD

            # ---------- EYE OUTLINE (green=open, red=closed) ----------
            outline_color = (0, 0, 255) if eyes_closed else (0, 255, 0)
            draw_eye_outline(frame, landmarks, LEFT_EYE,  w, h, outline_color)
            draw_eye_outline(frame, landmarks, RIGHT_EYE, w, h, outline_color)

            # ---------- CLOSED FRAME COUNTER ----------
            if eyes_closed:
                CLOSED_FRAMES += 1
            else:
                CLOSED_FRAMES = 0
                if ALERT_ACTIVE:
                    stop_alarm()   # kill sound as soon as eyes open
                ALERT_ACTIVE  = False

            # ---------- ALERT LOGIC ----------
            now = time.time()
            if (CLOSED_FRAMES > CLOSED_FRAME_LIMIT
                    and not ALERT_ACTIVE
                    and (now - LAST_ALERT_TIME) > ALERT_COOLDOWN):

                ALERT_ACTIVE    = True
                LAST_ALERT_TIME = now
                threading.Thread(target=alert_user, daemon=True).start()

            # ---------- ON-SCREEN OVERLAY ----------
            # Show EYES CLOSED banner every frame while eyes are shut
            if CLOSED_FRAMES > CLOSED_FRAME_LIMIT:
                cv2.rectangle(frame, (0, 60), (w, 130), (0, 0, 180), -1)
                cv2.putText(frame, "EYES CLOSED!", (50, 115),
                            cv2.FONT_HERSHEY_SIMPLEX, 1.8, (255, 255, 255), 3)

            # EAR value + frame count
            cv2.putText(frame, f"EAR: {ear:.2f}",
                        (30, 45), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            cv2.putText(frame, f"Closed frames: {CLOSED_FRAMES}",
                        (30, h - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)

    cv2.imshow("VisionAlert", frame)

    if cv2.waitKey(1) & 0xFF == 27:  # ESC to quit
        break


cap.release()
cv2.destroyAllWindows()