import cv2
import mediapipe as mp
from vision.pose_detector import PoseDetector
from logic.decision import get_direction
import utils.display as display
from config.settings import CAMERA_INDEX, FRAME_WIDTH, FRAME_HEIGHT

def main():
    # 1. Initialize Video Capture
    cap = cv2.VideoCapture(CAMERA_INDEX)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)

    if not cap.isOpened():
        print("Error: Could not open webcam.")
        return

    # 2. Initialize Pose Detector
    detector = PoseDetector()

    print("Starting Quadruped Vision Module...")
    print("Press 'q' to exit.")

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Error: Could not read frame.")
                break

            # Mirror the frame horizontally for selfie-view
            # frame = cv2.flip(frame, 1) # Uncomment if you want selfie mode

            # 3. Process frame -> return landmarks
            results = detector.process_frame(frame)

            # 4. Extract nose coordinate (MediaPipe Pose Nose is index 0)
            nose_x = None
            if results and results.pose_landmarks:
                coords = detector.get_keypoint(results, 0) # 0 is NOSE
                if coords:
                    nose_x, nose_y = coords

            # 5. Extract direction logic
            direction = get_direction(nose_x)
            
            # Print decision to console (for debugging)
            if nose_x is not None:
                # We'll avoid printing every frame to not flood the console entirely, 
                # but the instructions requested logging so we keep it simple.
                print(f"Nose X: {nose_x:.3f} | Decision: {direction}")
            else:
                print(f"Nose: Not detected | Decision: {direction}")

            # 6. Build the visual output
            frame = display.draw_landmarks(frame, results)
            frame = display.overlay_direction(frame, direction)

            # 7. Display
            display.show_frame(frame)

            # Exit condition
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
