import cv2
import numpy as np
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[3] / "src"))
from ui.slider import OpenCVSlider
from StreamAnalyzer import StreamAnalyzer
import threading

WINDOW_NAME = 'Processing'
WINDOW_WIDTH = 600
WINDOW_HEIGHT = 250

class ProcessingWindow:
  window = None
  progress_bar = None
  stream_analyzer = None
  video = None
  processing_complete_callback = None
  worker_thread = None
  start_time_ms = 0
  end_time_ms = 0
  analysis_interval = 1000
  is_process_complete = False
  result = []

  def __init__(self):
    self.window = np.zeros((WINDOW_HEIGHT, WINDOW_WIDTH, 3), dtype=np.uint8)
    self.progress_bar = OpenCVSlider(0, 0, 100)
    self.progress_bar.set_position((50, 100), (500, 50))
    self.stream_analyzer = StreamAnalyzer()
    self.stream_analyzer.open()

  def draw(self):
    cv2.rectangle(self.window, (0, 0), (WINDOW_WIDTH, WINDOW_HEIGHT), (150, 150, 150), -1)
    self.progress_bar.draw(self.window)
    cv2.imshow(WINDOW_NAME, self.window)

  def show(self):
    cv2.namedWindow(WINDOW_NAME)

  def hide(self):
    if self.worker_thread and self.worker_thread.is_alive():
      self.worker_thread.join()
    cv2.destroyWindow(WINDOW_NAME)

  def start_processing(self, video, start_time_ms, end_time_ms, analysis_interval=1000):
    self.video = video
    self.start_time_ms = start_time_ms
    self.end_time_ms = end_time_ms
    self.analysis_interval = analysis_interval
    self.is_process_complete = False
    self.worker_thread = threading.Thread(target=self.process_frame)
    self.worker_thread.start()  

  def is_processing_complete(self):
    return self.is_process_complete
  
  def get_result(self):
    if not self.is_process_complete:
      return None
    return self.result

  def process_frame(self):
    if self.video is None:
      return

    frame_rate = self.video.get(cv2.CAP_PROP_FPS)
    duration_ms = self.end_time_ms - self.start_time_ms
    time_ms = self.start_time_ms

    while time_ms < self.end_time_ms:
      frame_number = time_ms / 1000 * frame_rate
      self.video.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
      ret, frame = self.video.read()
      if ret:
        bboxes = self.stream_analyzer.analyze(frame)
        if len(bboxes) > 0:
          self.result.append({
            'time_ms': time_ms - self.start_time_ms,
            'bboxes': bboxes,
          })
      time_ms += self.analysis_interval
      progress = int(((time_ms - self.start_time_ms) / duration_ms) * 100)
      self.progress_bar.set_value(progress)

    self.is_process_complete = True