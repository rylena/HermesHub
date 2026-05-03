from datetime import datetime
from pathlib import Path


class Camera:
    def __init__(self, config):
        self.config = config

    def capture(self):
        if not self.config.enabled:
            return None

        import cv2

        capture_dir = Path(self.config.capture_dir)
        capture_dir.mkdir(parents=True, exist_ok=True)

        camera = cv2.VideoCapture(self.config.device_index)
        if not camera.isOpened():
            return None

        ok, frame = camera.read()
        camera.release()
        if not ok:
            return None

        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        output = capture_dir / f"frame-{stamp}.jpg"
        cv2.imwrite(str(output), frame, [int(cv2.IMWRITE_JPEG_QUALITY), self.config.jpeg_quality])
        return str(output)

    def can_open(self):
        if not self.config.enabled:
            return True

        import cv2

        camera = cv2.VideoCapture(self.config.device_index)
        opened = camera.isOpened()
        camera.release()
        return opened
