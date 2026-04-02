import cv2
from config.settings import WINDOW_NAME, FONT_SCALE, FONT_THICKNESS, TEXT_COLOR

# Simple pose connections to draw a skeleton without relying on mp.solutions
POSE_CONNECTIONS = [
    (11, 12), (11, 13), (13, 15), (12, 14), (14, 16), # Arms and shoulders
    (11, 23), (12, 24), (23, 24), # Torso
    (23, 25), (25, 27), (27, 29), (29, 31), (31, 27), # Left leg
    (24, 26), (26, 28), (28, 30), (30, 32), (32, 28)  # Right leg
]

def draw_landmarks(frame, results):
    """Draws MediaPipe pose landmarks and connections on the frame using basic OpenCV."""
    if not results or not results.pose_landmarks:
        return frame
        
    landmarks = results.pose_landmarks[0]
    h, w, _ = frame.shape
    
    # Draw connections
    for connection in POSE_CONNECTIONS:
        start_idx = connection[0]
        end_idx = connection[1]
        
        if start_idx < len(landmarks) and end_idx < len(landmarks):
            start_lm = landmarks[start_idx]
            end_lm = landmarks[end_idx]
            
            start_point = (int(start_lm.x * w), int(start_lm.y * h))
            end_point = (int(end_lm.x * w), int(end_lm.y * h))
            cv2.line(frame, start_point, end_point, (245,66,230), 2)
            
    # Draw keypoints
    for lm in landmarks:
        pt = (int(lm.x * w), int(lm.y * h))
        cv2.circle(frame, pt, 2, (245,117,66), -1)

    return frame

def overlay_direction(frame, direction):
    """Overlays the directional command text onto the frame."""
    cv2.putText(
        frame, 
        f"CMD: {direction}", 
        (50, 50), 
        cv2.FONT_HERSHEY_SIMPLEX, 
        FONT_SCALE, 
        TEXT_COLOR, 
        FONT_THICKNESS, 
        cv2.LINE_AA
    )
    return frame

def show_frame(frame):
    """Displays the frame in an OpenCV window."""
    cv2.imshow(WINDOW_NAME, frame)
