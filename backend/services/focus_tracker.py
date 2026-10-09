"""
In-memory focus tracking using OpenCV + MediaPipe face mesh.

MediaPipe ≥ 1.0 removed the legacy `mp.solutions` API. This module
falls back to a no-op tracker if the legacy API is unavailable, so the
server always starts and the /interview/focus/frame endpoint degrades
gracefully instead of crashing at import time.
"""
from __future__ import annotations

import threading
from dataclasses import dataclass

from config import FOCUS_SMOOTHING

try:
    import cv2
    import numpy as np
    _OPENCV_OK = True
except ImportError:
    cv2 = None
    np = None
    _OPENCV_OK = False

# ── Check whether the legacy mediapipe solutions API is available ─────────────
try:
    import mediapipe as mp
    _FaceMesh = mp.solutions.face_mesh.FaceMesh  # raises AttributeError on mp ≥ 1.0
    _MEDIAPIPE_OK = _OPENCV_OK
except (AttributeError, ImportError):
    _MEDIAPIPE_OK = False


@dataclass
class FocusResult:
    focus_score: float
    face_present: bool
    yaw: float | None
    pitch: float | None


class FocusTracker:
    """Process one frame at a time and smooth a per-session focus score.

    If mediapipe's legacy face-mesh API is not available the tracker
    returns face_present=False and a neutral score for every frame.
    """

    def __init__(self) -> None:
        self._scores: dict[str, float] = {}
        self._lock = threading.Lock()
        if _MEDIAPIPE_OK:
            import mediapipe as mp  # local re-import to keep type-checker happy
            self._mesh = mp.solutions.face_mesh.FaceMesh(
                static_image_mode=True,
                max_num_faces=1,
                refine_landmarks=True,
                min_detection_confidence=0.5,
            )
        else:
            self._mesh = None

    def process_frame(self, session_id: str, frame_bytes: bytes) -> FocusResult:
        if not _OPENCV_OK:
            return self._update(session_id, False, None, None)
        image = cv2.imdecode(np.frombuffer(frame_bytes, dtype=np.uint8), cv2.IMREAD_COLOR)
        if image is None:
            raise ValueError("Invalid image frame")

        # Graceful no-op if mediapipe legacy API unavailable
        if self._mesh is None:
            return self._update(session_id, False, None, None)

        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        result = self._mesh.process(rgb)
        if not result.multi_face_landmarks:
            return self._update(session_id, False, None, None)

        landmarks = result.multi_face_landmarks[0].landmark
        height, width = image.shape[:2]
        points = np.array(
            [[landmarks[index].x * width, landmarks[index].y * height] for index in (1, 152, 33, 263, 61, 291)],
            dtype=np.float64,
        )
        model_points = np.array(
            [(0.0, 0.0, 0.0), (0.0, -63.6, -12.5), (-43.3, 32.7, -26.0),
             (43.3, 32.7, -26.0), (-28.9, -28.9, -24.1), (28.9, -28.9, -24.1)],
            dtype=np.float64,
        )
        focal_length = width
        camera_matrix = np.array(
            [[focal_length, 0, width / 2], [0, focal_length, height / 2], [0, 0, 1]],
            dtype=np.float64,
        )
        success, rotation_vector, _ = cv2.solvePnP(
            model_points, points, camera_matrix, np.zeros((4, 1)),
            flags=cv2.SOLVEPNP_ITERATIVE,
        )
        if not success:
            return self._update(session_id, True, None, None)

        rotation_matrix, _ = cv2.Rodrigues(rotation_vector)
        _, _, _, _, _, _, euler = cv2.decomposeProjectionMatrix(
            np.hstack((rotation_matrix, np.zeros((3, 1))))
        )
        pitch, yaw = float(euler[0]), float(euler[1])
        return self._update(session_id, True, yaw, pitch)

    def _update(self, session_id: str, face_present: bool, yaw: float | None, pitch: float | None) -> FocusResult:
        attentive = face_present and yaw is not None and pitch is not None and abs(yaw) <= 25 and abs(pitch) <= 20
        observation = 100.0 if attentive else 0.0
        with self._lock:
            previous = self._scores.get(session_id, observation)
            score = previous + FOCUS_SMOOTHING * (observation - previous)
            self._scores[session_id] = score
        return FocusResult(
            round(score, 1), face_present,
            round(yaw, 1) if yaw is not None else None,
            round(pitch, 1) if pitch is not None else None,
        )

    def clear(self, session_id: str) -> None:
        with self._lock:
            self._scores.pop(session_id, None)


tracker = FocusTracker()
