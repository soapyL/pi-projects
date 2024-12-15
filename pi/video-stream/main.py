import io
import logging
import socketserver
from http import server
from threading import Condition, Thread
import cv2
import numpy as np

from picamera2 import Picamera2
from picamera2.encoders import JpegEncoder
from picamera2.outputs import FileOutput

# HTML page for the MJPEG streaming demo
PAGE = """\
<html>
<head>
<title>Pi Stream</title>
</head>
<body>
<img src="stream.mjpg" width="640" height="480" />
</body>
</html>
"""

class StreamingOutput(io.BufferedIOBase):
    def __init__(self):
        self.frame = None
        self.condition = Condition()

    def write(self, buf):
        with self.condition:
            self.frame = buf
            self.condition.notify_all()

class StreamingHandler(server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(301)
            self.send_header('Location', '/index.html')
            self.end_headers()
        elif self.path == '/index.html':
            content = PAGE.encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.send_header('Content-Length', len(content))
            self.end_headers()
            self.wfile.write(content)
        elif self.path == '/stream.mjpg':
            self.send_response(200)
            self.send_header('Age', 0)
            self.send_header('Cache-Control', 'no-cache, private')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=FRAME')
            self.end_headers()
            try:
                while True:
                    with output.condition:
                        output.condition.wait()
                        frame = output.frame
                    self.wfile.write(b'--FRAME\r\n')
                    self.send_header('Content-Type', 'image/jpeg')
                    self.send_header('Content-Length', len(frame))
                    self.end_headers()
                    self.wfile.write(frame)
                    self.wfile.write(b'\r\n')
            except Exception as e:
                logging.warning(
                    'Removed streaming client %s: %s',
                    self.client_address, str(e))
        else:
            self.send_error(404)
            self.end_headers()

class StreamingServer(socketserver.ThreadingMixIn, server.HTTPServer):
    allow_reuse_address = True
    daemon_threads = True

def motion_detection(output):
    """Detect motion using OpenCV."""
    print("Starting motion detection...")
    prev_frame = None
    motion_has_been_detected = False
    frame_counter = 0  # Initialize a frame counter

    while True:
        with output.condition:
            output.condition.wait()
            frame = output.frame

        # Increment the frame counter
        frame_counter += 1

        # Only check motion every 60 frames
        if frame_counter < 60:
            continue
        frame_counter = 0  # Reset counter after 60 frames

        # Convert JPEG frame to numpy array
        frame_array = np.frombuffer(frame, dtype=np.uint8)
        img = cv2.imdecode(frame_array, cv2.IMREAD_COLOR)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)

        if prev_frame is None:
            prev_frame = gray
            continue

        # Compute frame difference
        frame_diff = cv2.absdiff(prev_frame, gray)
        thresh = cv2.threshold(frame_diff, 50, 255, cv2.THRESH_BINARY)[1]  # Adjust threshold value
        thresh = cv2.dilate(thresh, None, iterations=2)
        contours, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        motion_detected = any(cv2.contourArea(contour) > 1000 for contour in contours)  # Check if any contour exceeds threshold

        if motion_detected:
            if not motion_has_been_detected:
                print("Motion detected!")
                motion_has_been_detected = True
        else:
            if motion_has_been_detected:
                print("Motion stopped.")
                motion_has_been_detected = False

        prev_frame = gray



# Create Picamera2 instance and configure it
picam2 = Picamera2()
picam2.configure(picam2.create_video_configuration(main={"size": (640, 480)}))
output = StreamingOutput()
picam2.start_recording(JpegEncoder(), FileOutput(output))

try:
    # Start motion detection in a separate thread
    motion_thread = Thread(target=motion_detection, args=(output,), daemon=True)
    motion_thread.start()

    # Set up and start the streaming server
    address = ('', 8000)
    server = StreamingServer(address, StreamingHandler)
    server.serve_forever()
finally:
    picam2.stop_recording()
