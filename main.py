"""
VIGIL-RQ – Quadruped Robot Vision & Navigation System
======================================================

Entry point for the VIGIL-RQ robot.

Architecture
------------
┌──────────────┐     frames      ┌───────────────┐
│  Camera      │ ──────────────► │ ObjectDetector│
│  (OpenCV)    │                 │  (YOLO / HOG) │
└──────────────┘                 └───────┬───────┘
                                         │ stable detections
                                         ▼
                                 ┌───────────────┐
                                 │MultiObject    │
                                 │ Tracker       │ ◄── Kalman filter / track
                                 └───────┬───────┘
                                         │ tracks + depth
                                         ▼
                           ┌─────────────────────────┐
                           │   ObstacleAvoider        │
                           │   PathPlanner            │
                           └──────────┬──────────────┘
                                      │ motion command
                                      ▼
                             ┌─────────────────┐
                             │ RobotController  │
                             │  (GaitEngine +  │
                             │   ServoCtrl)    │
                             └─────────────────┘

Usage
-----
    python main.py [--simulation] [--camera <index>] [--gait <trot|walk|crawl>]

Flags
-----
--simulation    Run without real hardware (servo commands are printed only).
--camera INT    Camera index (default: 0).
--gait STR      Gait pattern to use: trot / walk / crawl (default: trot).
--debug         Enable DEBUG-level logging.
"""

from __future__ import annotations

import argparse
import signal
import sys
import time

import config
from utils import get_logger
from vision import ObjectDetector, MultiObjectTracker, DepthEstimator
from robot import RobotController
from navigation import ObstacleAvoider, PathPlanner

log = get_logger(__name__)

# ── graceful shutdown ─────────────────────────────────────────────────────────
_SHUTDOWN = False


def _handle_signal(signum, _frame):
    global _SHUTDOWN
    log.info("Signal %s received – shutting down.", signal.Signals(signum).name)
    _SHUTDOWN = True


signal.signal(signal.SIGINT,  _handle_signal)
signal.signal(signal.SIGTERM, _handle_signal)
# ─────────────────────────────────────────────────────────────────────────────


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="VIGIL-RQ quadruped robot controller",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--simulation", action="store_true",
        help="Run without real hardware",
    )
    parser.add_argument(
        "--camera", type=int, default=config.CAMERA_INDEX,
        metavar="INDEX", help="Camera index",
    )
    parser.add_argument(
        "--gait", default=config.GAIT_DEFAULT,
        choices=["trot", "walk", "crawl"],
        help="Gait pattern",
    )
    parser.add_argument(
        "--debug", action="store_true",
        help="Enable DEBUG-level logging",
    )
    return parser.parse_args(argv)


def open_camera(index: int):
    """Open a camera capture device; return None in simulation / no-OpenCV mode."""
    try:
        import cv2  # type: ignore
        cap = cv2.VideoCapture(index)
        if not cap.isOpened():
            log.warning("Camera %d could not be opened – running without live video.", index)
            return None
        cap.set(cv2.CAP_PROP_FRAME_WIDTH,  config.FRAME_WIDTH)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.FRAME_HEIGHT)
        cap.set(cv2.CAP_PROP_FPS,          config.FRAME_RATE)
        log.info("Camera %d opened (%dx%d @ %d fps).",
                 index, config.FRAME_WIDTH, config.FRAME_HEIGHT, config.FRAME_RATE)
        return cap
    except ImportError:
        log.warning("OpenCV not available – running in headless mode.")
        return None


def annotate_frame(frame, tracks, depth_est, frame_w: int):
    """Draw bounding boxes, track IDs, and depth labels onto *frame* in-place."""
    try:
        import cv2  # type: ignore
    except ImportError:
        return

    for tid, track in tracks.items():
        x, y, w, h = track.bbox
        depth_m = depth_est.estimate_from_bbox(tid, track.bbox)
        label = f"#{tid} {track.class_name}"
        if depth_m is not None:
            label += f"  {depth_m:.2f} m"

        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 220, 0), 2)
        cv2.putText(
            frame, label,
            (x, y - 8),
            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 220, 0), 1,
        )

    # Frame-center crosshair
    cx, cy = frame_w // 2, config.FRAME_HEIGHT // 2
    cv2.line(frame, (cx - 15, cy), (cx + 15, cy), (200, 200, 200), 1)
    cv2.line(frame, (cx, cy - 15), (cx, cy + 15), (200, 200, 200), 1)


def main(argv: list[str] | None = None) -> int:
    global _SHUTDOWN

    args = parse_args(argv)

    if args.debug:
        import logging
        logging.getLogger().setLevel(logging.DEBUG)

    log.info("Starting %s v%s", config.PROJECT_NAME, config.VERSION)
    log.info("Gait: %s | Simulation: %s", args.gait, args.simulation)

    # ── Initialise subsystems ────────────────────────────────────────────────
    detector  = ObjectDetector()
    tracker   = MultiObjectTracker()
    depth_est = DepthEstimator()
    avoider   = ObstacleAvoider()
    planner   = PathPlanner(arrival_radius=0.1)
    robot     = RobotController(simulation=args.simulation)

    cap = open_camera(args.camera)

    # Example patrol route (metric offsets from start – adjust to real layout)
    planner.load([(0.5, 0.0), (0.5, 0.5), (0.0, 0.5), (0.0, 0.0)])

    # Robot position estimate (simple dead-reckoning – replace with real odometry)
    robot_x, robot_y = 0.0, 0.0
    step_dist = config.GAIT_STEP_LENGTH

    try:
        with robot:
            while not _SHUTDOWN:
                # ── Capture frame ────────────────────────────────────────────
                frame = None
                if cap is not None:
                    ret, frame = cap.read()
                    if not ret:
                        log.warning("Frame capture failed – retrying.")
                        time.sleep(0.1)
                        continue

                # ── Detection & tracking ─────────────────────────────────────
                if frame is not None:
                    detections = detector.detect(frame)
                else:
                    detections = []

                tracks = tracker.update(detections)

                # ── Depth estimation & obstacle list ─────────────────────────
                obstacle_list = []
                for tid, track in tracks.items():
                    d = depth_est.estimate_from_bbox(tid, track.bbox)
                    if d is not None:
                        obstacle_list.append((track.center, d))

                # Prune depth history for deregistered tracks
                active_ids = set(tracks.keys())
                for tid in list(depth_est._smoothed.keys()):
                    if tid not in active_ids:
                        depth_est.remove_track(tid)

                # ── Obstacle avoidance ───────────────────────────────────────
                motion_cmd = avoider.evaluate(obstacle_list)

                # ── Execute motion ───────────────────────────────────────────
                if motion_cmd == ObstacleAvoider.CMD_STOP:
                    robot.stop()
                elif motion_cmd == ObstacleAvoider.CMD_TURN_LEFT:
                    robot.turn_left(steps=1)
                elif motion_cmd == ObstacleAvoider.CMD_TURN_RIGHT:
                    robot.turn_right(steps=1)
                elif motion_cmd in (ObstacleAvoider.CMD_SLOW, ObstacleAvoider.CMD_FORWARD):
                    speed = 0.5 if motion_cmd == ObstacleAvoider.CMD_SLOW else 1.0

                    # Path-planner: check if we've reached the current waypoint
                    wp = planner.update((robot_x, robot_y))
                    if wp is None:
                        # All waypoints done – stand still
                        robot.stop()
                    else:
                        robot.move_forward(steps=1, gait=args.gait)
                        robot_x += step_dist * speed

                # ── Annotate and display (development mode) ──────────────────
                if frame is not None:
                    annotate_frame(frame, tracks, depth_est, config.FRAME_WIDTH)
                    try:
                        import cv2  # type: ignore
                        cv2.imshow("VIGIL-RQ", frame)
                        if cv2.waitKey(1) & 0xFF == ord("q"):
                            _SHUTDOWN = True
                    except Exception:  # noqa: BLE001
                        pass

                log.debug(
                    "cmd=%s  tracks=%d  pos=(%.2f, %.2f)",
                    motion_cmd, len(tracks), robot_x, robot_y,
                )

    except Exception as exc:  # noqa: BLE001
        log.exception("Unhandled exception in main loop: %s", exc)
        return 1
    finally:
        if cap is not None:
            cap.release()
        try:
            import cv2  # type: ignore
            cv2.destroyAllWindows()
        except Exception:  # noqa: BLE001
            pass
        log.info("VIGIL-RQ stopped.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
