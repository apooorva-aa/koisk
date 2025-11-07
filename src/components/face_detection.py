"""
Face Detection Component using OpenCV.
"""

import cv2
import mediapipe as mp
import time
import logging
from utils.config import load_config

logger = logging.getLogger(__name__)

class FaceDetector:
    def __init__(self, config):
        face_cfg = config.get("face_detection", {})
        self.model_selection = int(face_cfg.get("model_selection", 0))

        conf = face_cfg.get("min_detection_confidence", 0.6)
        try:
            self.confidence = float(conf)
        except:
            self.confidence = 0.6

        self.mp_face = mp.solutions.face_detection
        self.detector = self.mp_face.FaceDetection(
            model_selection=self.model_selection,
            min_detection_confidence=self.confidence
        )
        self.cap = cv2.VideoCapture(config.get("hardware", {}).get("camera_index", 0))

    def _get_frame(self):
        ret, frame = self.cap.read()
        if not ret:
            return None
        return frame

    def _detect_face(self, frame):
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = self.detector.process(rgb)
        detections = result.detections if result.detections else []
        return len(detections) > 0, detections
    
    def _draw_boxes(self, frame, detections):
        h, w, _ = frame.shape
        for det in detections:
            box = det.location_data.relative_bounding_box
            x1 = int(box.xmin * w)
            y1 = int(box.ymin * h)
            x2 = int((box.xmin + box.width) * w)
            y2 = int((box.ymin + box.height) * h)

            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)


    def wait_for_face(self):
        """Blocking loop until a face is detected."""
        
        print("Waiting for face...")

        while True:
            frame = self._get_frame()
            if frame is None:
                continue
            
            face_found, detections = self._detect_face(frame)
            
            if face_found:
                self._draw_boxes(frame, detections)
                print("Face Detected — Starting Session")
                return True

            cv2.imshow("Camera — Waiting for Face", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        return False

    def monitor_session(self, timeout=10):
        """Returns False if no face is detected for <timeout> seconds."""
        
        print("Session Started — Monitoring face presence...")
        last_seen = time.time()

        while True:
            frame = self._get_frame()
            if frame is None:
                continue
            
            face_found, detections = self._detect_face(frame)

            if face_found:
                last_seen = time.time()
                self._draw_boxes(frame, detections)

            status_text = "Face detected" if face_found else "No face"
            cv2.putText(frame, status_text, (20, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0) if face_found else (0,0,255), 2)

            cv2.imshow("Session Monitoring", frame)

            # Timeout check
            if time.time() - last_seen > timeout:
                print("No face detected for", timeout, "seconds — Ending Session")
                return False
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        return False

    def release(self):
        self.cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    config = load_config()
    face = FaceDetector(config)
    
    session_start = face.wait_for_face()

    if session_start:
        face.monitor_session(timeout=10)

    face.release()


