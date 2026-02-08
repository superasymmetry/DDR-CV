from ultralytics import YOLO
import cv2
import torch
import numpy as np
import requests
import time

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

midas = torch.hub.load("intel-isl/MiDaS", "MiDaS_small")
midas.to(device)
midas.eval()

midas_transforms = torch.hub.load("intel-isl/MiDaS", "transforms")
transform = midas_transforms.small_transform

def estimate_depth(frame):
    img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    input_batch = transform(img).to(device)

    with torch.no_grad():
        prediction = midas(input_batch)
        prediction = torch.nn.functional.interpolate(
            prediction.unsqueeze(1),
            size=img.shape[:2],
            mode="bicubic",
            align_corners=False,
        ).squeeze()

    depth = prediction.cpu().numpy()
    depth = cv2.normalize(depth, None, 0, 255, cv2.NORM_MINMAX)
    return depth.astype(np.uint8)

def get_depth_at_point(depth_map, point):
    x, y = int(point[0]), int(point[1])
    if 0 <= x < depth_map.shape[1] and 0 <= y < depth_map.shape[0]:
        return int(depth_map[y, x])
    return 0

model = YOLO('yolov8n-pose.pt')
cap = cv2.VideoCapture(0)

# Server endpoint
SERVER_URL = "http://localhost:8000/api/cv/pose"
last_send_time = time.time()
SEND_INTERVAL = 0.033  # ~30 FPS

print("🎥 CV Server starting - sending pose data to game server")

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break
    
    depth_map = estimate_depth(frame)
    results = model(frame, verbose=False)
    
    for result in results:
        if result.keypoints is not None:
            keypoints = result.keypoints.xy[0]
            
            left_ankle = keypoints[15]
            right_ankle = keypoints[16]
            left_knee = keypoints[13]
            right_knee = keypoints[14]
            
            # Send pose data to server
            current_time = time.time()
            if current_time - last_send_time >= SEND_INTERVAL:
                pose_data = {
                    "left_ankle": {
                        "x": float(left_ankle[0]),
                        "y": float(left_ankle[1]),
                        "depth": get_depth_at_point(depth_map, left_ankle)
                    },
                    "right_ankle": {
                        "x": float(right_ankle[0]),
                        "y": float(right_ankle[1]),
                        "depth": get_depth_at_point(depth_map, right_ankle)
                    },
                    "left_knee": {
                        "x": float(left_knee[0]),
                        "y": float(left_knee[1]),
                        "depth": get_depth_at_point(depth_map, left_knee)
                    },
                    "right_knee": {
                        "x": float(right_knee[0]),
                        "y": float(right_knee[1]),
                        "depth": get_depth_at_point(depth_map, right_knee)
                    },
                    "timestamp": current_time
                }
                
                try:
                    requests.post(SERVER_URL, json=pose_data, timeout=0.1)
                    last_send_time = current_time
                except:
                    pass  # Continue even if send fails
            
            # Draw visualization
            cv2.circle(frame, tuple(left_ankle.int().tolist()), 8, (0, 0, 255), -1)
            cv2.circle(frame, tuple(right_ankle.int().tolist()), 8, (0, 0, 255), -1)
            cv2.circle(frame, tuple(left_knee.int().tolist()), 8, (0, 255, 0), -1)
            cv2.circle(frame, tuple(right_knee.int().tolist()), 8, (0, 255, 0), -1)

    cv2.imshow('CV Server', frame)
    
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()