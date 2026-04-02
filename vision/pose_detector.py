import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

class PoseDetector:
    def __init__(self, model_path='pose_landmarker_lite.task'):
        # Using the new MediaPipe Tasks API natively avoiding legacy solutions module
        base_options = python.BaseOptions(model_asset_path=model_path)
        options = vision.PoseLandmarkerOptions(
            base_options=base_options,
            output_segmentation_masks=False,
            running_mode=vision.RunningMode.IMAGE
        )
        self.detector = vision.PoseLandmarker.create_from_options(options)

    def process_frame(self, frame):
        """Processes an OpenCV frame and returns MediaPipe pose results."""
        # Convert the BGR image to RGB
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        # Create MediaPipe Image object required by the Tasks API
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)
        
        # Detect pose
        results = self.detector.detect(mp_image)
        return results

    def get_keypoint(self, detection_result, index):
        """
        Helper function to get a specific keypoint's normalized (x, y).
        """
        if detection_result and detection_result.pose_landmarks:
            # We assume the first detected pose structure
            pose_landmarks = detection_result.pose_landmarks[0]
            if len(pose_landmarks) > index:
                landmark = pose_landmarks[index]
                return landmark.x, landmark.y
        return None
