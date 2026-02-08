from ultralytics import YOLO
import cv2
import torch
import numpy as np

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

def draw_depth_at_point(frame, depth_map, point, label):
    x, y = int(point[0]), int(point[1])
    if 0 <= x < depth_map.shape[1] and 0 <= y < depth_map.shape[0]:
        d = depth_map[y, x]
        cv2.putText(
            frame,
            f"{label}: {d}",
            (x + 5, y - 5),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (255, 255, 255),
            2
        )


# First run will download the model automatically
model = YOLO('yolov8n-pose.pt')

cap = cv2.VideoCapture(0)

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break
    depth_map = estimate_depth(frame)
    
    results = model(frame, verbose=False)
    
    annotated_frame = results[0].plot()
    
    for result in results:
        if result.keypoints is not None:
            keypoints = result.keypoints.xy[0] 
            left_hip = keypoints[11]
            right_hip = keypoints[12]
            left_knee = keypoints[13]
            right_knee = keypoints[14]
            left_ankle = keypoints[15]
            right_ankle = keypoints[16]
            cv2.circle(frame, (int(left_hip[0]), int(left_hip[1])), 8, (255, 0, 0), -1)
            cv2.circle(frame, (int(right_hip[0]), int(right_hip[1])), 8, (255, 0, 0), -1)
            cv2.circle(frame, (int(left_knee[0]), int(left_knee[1])), 8, (0, 255, 0), -1)
            cv2.circle(frame, (int(right_knee[0]), int(right_knee[1])), 8, (0, 255, 0), -1)
            cv2.circle(frame, (int(left_ankle[0]), int(left_ankle[1])), 8, (0, 0, 255), -1)
            cv2.circle(frame, (int(right_ankle[0]), int(right_ankle[1])), 8, (0, 0, 255), -1)
            cv2.line(frame, tuple(left_hip.int().tolist()), tuple(left_knee.int().tolist()), (255, 255, 0), 3)
            cv2.line(frame, tuple(left_knee.int().tolist()), tuple(left_ankle.int().tolist()), (255, 255, 0), 3)
            cv2.line(frame, tuple(right_hip.int().tolist()), tuple(right_knee.int().tolist()), (255, 255, 0), 3)
            cv2.line(frame, tuple(right_knee.int().tolist()), tuple(right_ankle.int().tolist()), (255, 255, 0), 3)

            # depth
            draw_depth_at_point(frame, depth_map, left_ankle, "LA")
            draw_depth_at_point(frame, depth_map, right_ankle, "RA")
            draw_depth_at_point(frame, depth_map, left_knee, "LK")
            draw_depth_at_point(frame, depth_map, right_knee, "RK")

            

    cv2.imshow('Pose Tracking', frame)
    cv2.imshow("Depth", depth_map)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
    
cap.release()

cv2.destroyAllWindows()