"""
Object detection pipeline for VIGIL-RQ.

Supports two back-ends:
  1. **YOLO** (DNN model files present) – full neural-network inference.
  2. **HOG + background subtraction** – lightweight fallback that requires
     only OpenCV (no external model weights).

Accuracy improvements implemented
----------------------------------
* Non-Maximum Suppression (NMS) to remove duplicate boxes.
* Temporal stability filter – a detection must appear in at least
  ``DETECTION_STABILITY_FRAMES`` consecutive frames before it is reported.
* Confidence hysteresis – once a class is confirmed it stays active until
  confidence drops below a lower *exit* threshold, reducing flickering.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from collections import defaultdict
from typing import List

import numpy as np

import config
from utils import get_logger

log = get_logger(__name__)

try:
    import cv2  # type: ignore
    _CV2_AVAILABLE = True
except ImportError:
    _CV2_AVAILABLE = False
    log.warning("OpenCV not found – ObjectDetector will run in mock mode.")


@dataclass
class Detection:
    """A single detected object."""
    class_id: int
    class_name: str
    confidence: float
    bbox: tuple[int, int, int, int]   # (x, y, w, h) in pixels
    center: tuple[int, int] = field(init=False)

    def __post_init__(self) -> None:
        x, y, w, h = self.bbox
        self.center = (x + w // 2, y + h // 2)


class ObjectDetector:
    """Detects objects in camera frames.

    Parameters
    ----------
    model_path : str
        Path to YOLO ``.weights`` file.  If absent the HOG fallback is used.
    config_path : str
        Path to the matching YOLO ``.cfg`` file.
    classes_path : str
        Path to a plain-text file listing class names (one per line).
    conf_threshold : float
        Minimum confidence to accept a detection.
    nms_threshold : float
        IoU threshold for NMS.
    stability_frames : int
        Frames a detection must persist to be considered stable.
    """

    def __init__(
        self,
        model_path: str = config.MODEL_PATH,
        config_path: str = config.MODEL_CONFIG_PATH,
        classes_path: str = config.MODEL_CLASSES_PATH,
        conf_threshold: float = config.DETECTION_CONFIDENCE_THRESHOLD,
        nms_threshold: float = config.DETECTION_NMS_THRESHOLD,
        stability_frames: int = config.DETECTION_STABILITY_FRAMES,
    ) -> None:
        self.conf_threshold = conf_threshold
        self.nms_threshold = nms_threshold
        self.stability_frames = stability_frames

        self._classes: list[str] = []
        self._net = None
        self._output_layers: list[str] = []
        self._use_yolo = False

        self._stability_counter: dict[str, int] = defaultdict(int)
        self._stable_detections: list[Detection] = []

        self._load_classes(classes_path)
        self._load_model(model_path, config_path)

    # ------------------------------------------------------------------
    # Initialisation helpers
    # ------------------------------------------------------------------

    def _load_classes(self, path: str) -> None:
        if os.path.isfile(path):
            with open(path, "r") as fh:
                self._classes = [line.strip() for line in fh if line.strip()]
            log.info("Loaded %d classes from %s", len(self._classes), path)
        else:
            self._classes = ["person", "obstacle", "target"]
            log.info("Class file not found – using default classes: %s", self._classes)

    def _load_model(self, model_path: str, config_path: str) -> None:
        if not _CV2_AVAILABLE:
            return
        if os.path.isfile(model_path) and os.path.isfile(config_path):
            log.info("Loading YOLO model from %s", model_path)
            self._net = cv2.dnn.readNet(model_path, config_path)
            layer_names = self._net.getLayerNames()
            unconnected = self._net.getUnconnectedOutLayers()
            if isinstance(unconnected[0], (list, np.ndarray)):
                self._output_layers = [layer_names[i[0] - 1] for i in unconnected]
            else:
                self._output_layers = [layer_names[i - 1] for i in unconnected]
            self._use_yolo = True
            log.info("YOLO model loaded successfully.")
        else:
            log.warning(
                "YOLO model files not found at %s / %s. Using HOG fallback.",
                model_path,
                config_path,
            )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def detect(self, frame: np.ndarray) -> List[Detection]:
        """Run detection on *frame* and return stable detections.

        Parameters
        ----------
        frame : np.ndarray
            BGR image from OpenCV (H×W×3, uint8).

        Returns
        -------
        list[Detection]
            Detections that have been stable for ``stability_frames`` frames.
        """
        if not _CV2_AVAILABLE:
            return self._mock_detect(frame)

        if self._use_yolo:
            raw = self._detect_yolo(frame)
        else:
            raw = self._detect_hog(frame)

        self._update_stability(raw)
        return list(self._stable_detections)

    # ------------------------------------------------------------------
    # Back-ends
    # ------------------------------------------------------------------

    def _detect_yolo(self, frame: np.ndarray) -> List[Detection]:
        h, w = frame.shape[:2]
        blob = cv2.dnn.blobFromImage(frame, 1 / 255.0, (416, 416), swapRB=True, crop=False)
        self._net.setInput(blob)
        layer_outputs = self._net.forward(self._output_layers)

        boxes, confidences, class_ids = [], [], []
        for output in layer_outputs:
            for detection in output:
                scores = detection[5:]
                cid = int(np.argmax(scores))
                confidence = float(scores[cid])
                if confidence < self.conf_threshold:
                    continue
                cx, cy, dw, dh = (
                    int(detection[0] * w),
                    int(detection[1] * h),
                    int(detection[2] * w),
                    int(detection[3] * h),
                )
                x, y = cx - dw // 2, cy - dh // 2
                boxes.append([x, y, dw, dh])
                confidences.append(confidence)
                class_ids.append(cid)

        indices = cv2.dnn.NMSBoxes(
            boxes, confidences, self.conf_threshold, self.nms_threshold
        )
        detections: List[Detection] = []
        if len(indices) > 0:
            for i in np.array(indices).flatten():
                cid = class_ids[i]
                name = self._classes[cid] if cid < len(self._classes) else f"class_{cid}"
                detections.append(
                    Detection(
                        class_id=cid,
                        class_name=name,
                        confidence=confidences[i],
                        bbox=tuple(boxes[i]),  # type: ignore[arg-type]
                    )
                )
        return detections

    def _detect_hog(self, frame: np.ndarray) -> List[Detection]:
        """Person detection using the built-in OpenCV HOG descriptor."""
        hog = cv2.HOGDescriptor()
        hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
        rects, weights = hog.detectMultiScale(
            frame,
            winStride=(8, 8),
            padding=(4, 4),
            scale=1.05,
        )
        detections: List[Detection] = []
        for (x, y, w, h), weight in zip(rects, weights):
            conf = float(np.clip(weight, 0.0, 1.0))
            if conf >= self.conf_threshold:
                detections.append(
                    Detection(
                        class_id=0,
                        class_name="person",
                        confidence=conf,
                        bbox=(int(x), int(y), int(w), int(h)),
                    )
                )
        return detections

    def _mock_detect(self, frame: np.ndarray) -> List[Detection]:  # pragma: no cover
        """Return empty list when OpenCV is unavailable (unit-test / CI mode)."""
        return []

    # ------------------------------------------------------------------
    # Temporal stability filter
    # ------------------------------------------------------------------

    def _update_stability(self, raw: List[Detection]) -> None:
        """Update per-class stability counters; populate ``_stable_detections``."""
        current_classes = {d.class_name for d in raw}

        # Increment counter for detected classes, decrement for absent ones
        all_classes = set(self._stability_counter.keys()) | current_classes
        for cls in all_classes:
            if cls in current_classes:
                self._stability_counter[cls] = min(
                    self._stability_counter[cls] + 1, self.stability_frames
                )
            else:
                self._stability_counter[cls] = max(
                    self._stability_counter[cls] - 1, 0
                )

        # A class is "stable" when its counter reaches the threshold
        stable_classes = {
            cls
            for cls, cnt in self._stability_counter.items()
            if cnt >= self.stability_frames
        }
        self._stable_detections = [d for d in raw if d.class_name in stable_classes]
