"""
Face Detection Component using OpenCV.
Simplified implementation for initial development.
"""

import asyncio
import logging
from typing import Optional, Tuple
import cv2
import numpy as np

logger = logging.getLogger(__name__)


class FaceDetectionComponent:
    """Face detection component using OpenCV Haar cascades."""
    
    def __init__(self, config):
        self.config = config
        self.camera = None
        self.face_cascade = None
        self.is_initialized = False
        
    async def initialize(self):
        """Initialize the face detection component."""
        try:
            logger.info("Initializing face detection component...")
            
            # Load Haar cascade for face detection
            self.face_cascade = cv2.CascadeClassifier(
                cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            )
            
            # Initialize camera
            camera_index = self.config.get('hardware', {}).get('camera_index', 0)
            self.camera = cv2.VideoCapture(camera_index)
            
            if not self.camera.isOpened():
                logger.warning(f"Could not open camera {camera_index}, using mock mode")
                self.camera = None
            
            self.is_initialized = True
            logger.info("Face detection component initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize face detection: {e}")
            raise
    
    async def detect_face(self) -> Tuple[bool, Optional[dict]]:
        """
        Detect if a face is present in the camera feed.
        
        Returns:
            Tuple of (face_detected, face_info)
        """
        if not self.is_initialized:
            logger.warning("Face detection not initialized")
            return False, None
        
        try:
            if self.camera is None:
                # Mock mode for development
                logger.debug("Mock face detection - returning True")
                return True, {"confidence": 0.8, "bbox": (100, 100, 200, 200)}
            
            # Capture frame
            ret, frame = self.camera.read()
            if not ret:
                logger.warning("Failed to capture frame")
                return False, None
            
            # Convert to grayscale
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Detect faces
            faces = self.face_cascade.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(30, 30)
            )
            
            if len(faces) > 0:
                # Return the largest face
                largest_face = max(faces, key=lambda x: x[2] * x[3])
                x, y, w, h = largest_face
                
                face_info = {
                    "confidence": 0.9,
                    "bbox": (x, y, w, h),
                    "center": (x + w//2, y + h//2)
                }
                
                logger.debug(f"Face detected: {face_info}")
                return True, face_info
            
            return False, None
            
        except Exception as e:
            logger.error(f"Error in face detection: {e}")
            return False, None
    
    async def cleanup(self):
        """Cleanup resources."""
        if self.camera:
            self.camera.release()
        cv2.destroyAllWindows()
        logger.info("Face detection component cleaned up")
