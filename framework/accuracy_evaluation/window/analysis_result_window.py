import cv2
import numpy as np
from ui.image import OpenCVImage
from ui.event_timeline import OpenCVEventTimeline
from ui.dict_view import OpenCVDictView

WINDOW_NAME = 'Analysis Result'
WINDOW_WIDTH = 1000
WINDOW_HEIGHT = 600

class AnalysisResultWindow:
  window = None
  video_image = None
  analysis_result_image = None
  result_view = None
  timeline = None
  video = None
  start_time_ms = 0
  end_time_ms = 0
  result = None

  def __init__(self):
    self.window = np.zeros((WINDOW_HEIGHT, WINDOW_WIDTH, 3), dtype=np.uint8)
    self.timeline = OpenCVEventTimeline()
    self.video_image = OpenCVImage()
    self.video_image.set_position((0, 0), (600, 480))    
    self.analysis_result_image = OpenCVImage()
    self.analysis_result_image.set_position((620, 20), (360, 240))
    self.result_view = OpenCVDictView()
    self.result_view.set_position((620, 280), (360, 300))
    self.timeline.set_position((0, 480), (600, 120))
    self.timeline.set_time_changed_callback(self.time_changed_callback)
    self.timeline.set_event_markers_selected_callback(self.event_marker_selected_callback)

  def set_video(self, video, start_time_ms=0, end_time_ms=0):
    self.video = video
    self.start_time_ms = start_time_ms
    self.end_time_ms = end_time_ms
    frame_count = video.get(cv2.CAP_PROP_FRAME_COUNT)
    frame_rate = video.get(cv2.CAP_PROP_FPS)
    duration = frame_count / frame_rate * 1000
    if start_time_ms > 0 and end_time_ms == 0:
      duration -= start_time_ms
    elif end_time_ms > 0 and start_time_ms == 0:
      duration = end_time_ms
    elif start_time_ms > 0 and end_time_ms > 0:
      duration = end_time_ms - start_time_ms
    self.timeline.set_duration(duration)
    frame_number = (self.start_time_ms) / 1000 * self.video.get(cv2.CAP_PROP_FPS)
    self.video.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
    ret, frame = video.read()
    if ret:
      self.video_image.set_image(frame)

  def set_analysis_result(self, result):
    self.result = result
    event_markers = []
    for item in result:
      event_markers.append({
        "id": item["time_ms"],
        "time_ms": item["time_ms"],
      })
    self.timeline.set_event_markers(event_markers)     

  def draw(self):
    cv2.rectangle(self.window, (0, 0), (WINDOW_WIDTH, WINDOW_HEIGHT), (150, 150, 150), -1)
    self.timeline.draw(self.window)
    self.video_image.draw(self.window)
    self.analysis_result_image.draw(self.window)
    self.result_view.draw(self.window)
    cv2.imshow(WINDOW_NAME, self.window)

  def show(self):
    cv2.namedWindow(WINDOW_NAME)
    cv2.setMouseCallback(WINDOW_NAME, self.handle_mouse_event)

  def hide(self):
    cv2.destroyWindow(WINDOW_NAME)

  def handle_mouse_event(self, event, x, y, flags, param):
    self.timeline.handle_mouse_event(event, x, y, flags, param)
    self.result_view.handle_mouse_event(event, x, y, flags, param)

  def time_changed_callback(self, event, time):
    if self.video is None:
      return
    if event == 'mouseUp':
      frame_number = (self.start_time_ms + time) / 1000 * self.video.get(cv2.CAP_PROP_FPS)
      self.video.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
      ret, frame = self.video.read()
      if ret:
        self.video_image.set_image(frame)

  def event_marker_selected_callback(self, marker_id):
    for item in self.result:
      time_ms = item["time_ms"]
      bboxes = item["bboxes"]
      if time_ms == marker_id:
        self.result_view.set_data(item)        
        frame_number = (self.start_time_ms + time_ms) / 1000 * self.video.get(cv2.CAP_PROP_FPS)
        self.video.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        ret, frame = self.video.read()
        if ret:
          for bbox in bboxes:
            x, y, w, h = bbox
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 4)
            self.analysis_result_image.set_image(frame)
