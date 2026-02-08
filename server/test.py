import cv2
import mediapipe as mp
import numpy as np

# Initialize MediaPipe Pose
BaseOptions = mp.tasks.BaseOptions
PoseLandmarker = mp.tasks.vision.PoseLandmarker
PoseLandmarkerOptions = mp.tasks.vision.PoseLandmarkerOptions
VisionRunningMode = mp.tasks.vision.RunningMode

# Download model: https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/latest/pose_landmarker_lite.task
options = PoseLandmarkerOptions(
    base_options=BaseOptions(model_asset_path='pose_landmarker_lite.task'),
    running_mode=VisionRunningMode.VIDEO,
    num_poses=2,
    min_pose_detection_confidence=0.5,
    min_pose_presence_confidence=0.5,
    min_tracking_confidence=0.5
)

# Define pose connections manually
POSE_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 7), (0, 4), (4, 5), (5, 6), (6, 8),
    (9, 10), (11, 12), (11, 13), (13, 15), (15, 17), (15, 19), (15, 21),
    (17, 19), (12, 14), (14, 16), (16, 18), (16, 20), (16, 22), (18, 20),
    (11, 23), (12, 24), (23, 24), (23, 25), (24, 26), (25, 27), (26, 28),
    (27, 29), (28, 30), (27, 31), (28, 32), (29, 31), (30, 32)
]

detector = PoseLandmarker.create_from_options(options)

cap = cv2.VideoCapture(0)
timestamp = 0

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break
    
    # Convert to RGB
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
    
    # Detect pose
    results = detector.detect_for_video(mp_image, timestamp)
    timestamp += 33  # Simulate 30fps
    
    # Draw results
    if results.pose_landmarks:
        h, w = frame.shape[:2]
        
        for pose_landmarks in results.pose_landmarks:
            # Draw connections
            for connection in POSE_CONNECTIONS:
                start_idx, end_idx = connection
                if start_idx < len(pose_landmarks) and end_idx < len(pose_landmarks):
                    start = pose_landmarks[start_idx]
                    end = pose_landmarks[end_idx]
                    
                    start_point = (int(start.x * w), int(start.y * h))
                    end_point = (int(end.x * w), int(end.y * h))
                    
                    cv2.line(frame, start_point, end_point, (0, 255, 0), 2)
            
            # Draw landmarks
            for landmark in pose_landmarks:
                x, y = int(landmark.x * w), int(landmark.y * h)
                cv2.circle(frame, (x, y), 5, (0, 0, 255), -1)
    
    cv2.imshow('Pose Tracking', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()