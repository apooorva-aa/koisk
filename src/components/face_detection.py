"""
Face Detection Component using OpenCV.

This module no longer depends on MediaPipe. It uses OpenCV Haar cascades
and opens the video device directly (defaults to /dev/video0). If OpenCV
or the camera cannot be initialized, the detector will be marked disabled
and methods will log warnings and return safely instead of raising at
import time.
"""

import time
import logging
from typing import Optional, Tuple, List

from utils.config import load_config

logger = logging.getLogger(__name__)


class FaceDetector:
    def __init__(self, config):
        face_cfg = config.get("face_detection", {})
        try:
            self.confidence = float(face_cfg.get("min_detection_confidence", 0.6))
        except Exception:
            self.confidence = 0.6

        # Determine camera device. Prefer explicit device path; fall back to camera_index;
        # default to /dev/video0 which is common on Linux systems.
        hw = config.get("hardware", {})
        device = hw.get("camera_device")
        if device is None:
            # camera_index may be provided as int or string; keep as-is if present
            camera_index = hw.get("camera_index", None)
            device = camera_index if camera_index is not None else "/dev/video0"

        self.device = device

        # Delay importing cv2 to avoid ImportError at module import time.
        try:
            import cv2
        except Exception as e:
            logger.warning("OpenCV (cv2) not available — face detection disabled. (%s)", e)
            self.cv2 = None
            self.cap = None
            self.detector = None
            self.disabled = True
            return

        self.cv2 = cv2
        self.disabled = False

        # Open camera (try device path first, fall back to index)
        self.cap = None
        try:
            # If device is an integer-like value, VideoCapture will accept it; otherwise try path
            try:
                self.cap = cv2.VideoCapture(self.device)
            except Exception:
                # fallback to index 0
                self.cap = cv2.VideoCapture(0)

            # If opening failed and device is string of digits, try numeric index
            if not self.cap or not self.cap.isOpened():
                try:
                    idx = int(self.device)
                    self.cap = cv2.VideoCapture(idx)
                except Exception:
                    pass

            if not self.cap or not self.cap.isOpened():
                logger.warning("Unable to open video device %s — face detection disabled.", self.device)
                self.disabled = True
                self.cap = None
        except Exception as e:
            logger.warning("Error opening video device %s: %s — face detection disabled.", self.device, e)
            self.disabled = True
            self.cap = None

        # Load Haar cascade for face detection. Not fatal if it fails; we'll keep running
        # but return no detections.
        self.detector = None
        try:
            cascade_path = face_cfg.get("cascade_path") or (cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
            self.detector = cv2.CascadeClassifier(cascade_path)
            if hasattr(self.detector, "empty") and self.detector.empty():
                logger.warning("Failed to load Haar cascade from %s — detections will be disabled.", cascade_path)
                self.detector = None
        except Exception as e:
            logger.warning("Error initializing Haar cascade: %s — detections will be disabled.", e)
            self.detector = None

    def _get_frame(self) -> Optional["object"]:
        if self.disabled or not self.cap:
            return None
        try:
            ret, frame = self.cap.read()
            if not ret:
                return None
            return frame
        except Exception as e:
            logger.warning("Error reading frame from %s: %s", self.device, e)
            return None

    def _detect_face(self, frame) -> Tuple[bool, List[Tuple[int, int, int, int]]]:
        """Return (face_found, detections) where detections is list of (x,y,w,h)."""
        if self.disabled or not self.detector:
            return False, []

        try:
            gray = self.cv2.cvtColor(frame, self.cv2.COLOR_BGR2GRAY)
            rects = self.detector.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)
            detections = [tuple(map(int, r)) for r in rects] if hasattr(rects, '__len__') and len(rects) else []
            return len(detections) > 0, detections
        except Exception as e:
            logger.warning("Error during face detection: %s", e)
            return False, []

    def _draw_boxes(self, frame, detections):
        if not detections:
            return
        h, w = frame.shape[:2]
        for (x, y, ww, hh) in detections:
            try:
                self.cv2.rectangle(frame, (x, y), (x + ww, y + hh), (0, 255, 0), 2)
            except Exception:
                pass

    def wait_for_face(self):
        """Blocking loop until a face is detected. Returns True if a face was detected."""
        if self.disabled:
            logger.warning("FaceDetector disabled — cannot wait for face.")
            return False

        print("Waiting for face...")
        while True:
            frame = self._get_frame()
            if frame is None:
                # small sleep to avoid busy loop if camera failing
                time.sleep(0.1)
                continue

            face_found, detections = self._detect_face(frame)

            if face_found:
                self._draw_boxes(frame, detections)
                print("Face Detected — Starting Session")
                return True

            try:
                self.cv2.imshow("Camera — Waiting for Face", frame)
                if self.cv2.waitKey(1) & 0xFF == ord('q'):
                    break
            except Exception:
                # If displaying fails (headless), just continue
                pass

        return False

    def monitor_session(self, timeout=10):
        """Returns False if no face is detected for <timeout> seconds."""
        if self.disabled:
            logger.warning("FaceDetector disabled — cannot monitor session.")
            return False

        print("Session Started — Monitoring face presence...")
        last_seen = time.time()

        while True:
            frame = self._get_frame()
            if frame is None:
                time.sleep(0.1)
                continue

            face_found, detections = self._detect_face(frame)

            if face_found:
                last_seen = time.time()
                self._draw_boxes(frame, detections)

            status_text = "Face detected" if face_found else "No face"
            try:
                self.cv2.putText(frame, status_text, (20, 40),
                                 self.cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0) if face_found else (0,0,255), 2)
                self.cv2.imshow("Session Monitoring", frame)
            except Exception:
                # ignore display errors
                pass

            if time.time() - last_seen > timeout:
                print("No face detected for", timeout, "seconds — Ending Session")
                return False

            try:
                if self.cv2.waitKey(1) & 0xFF == ord('q'):
                    break
            except Exception:
                pass

        return False

    def release(self):
        try:
            if getattr(self, 'cap', None):
                try:
                    self.cap.release()
                except Exception:
                    pass
            if getattr(self, 'cv2', None):
                try:
                    self.cv2.destroyAllWindows()
                except Exception:
                    pass
        finally:
            self.disabled = True


if __name__ == "__main__":
    config = load_config()
    face = FaceDetector(config)

    session_start = face.wait_for_face()

    if session_start:
        face.monitor_session(timeout=10)

    face.release()


