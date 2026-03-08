import cv2
import numpy as np
from ui.button import OpenCVButton
from ui.slider import OpenCVSlider
from ui.number_input import OpenCVNumberInput
from ui.image import OpenCVImage
from ui.timeline import OpenCVTimeline

WINDOW_NAME = 'Parameter Setup'
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 700

MARGIN = 20
LABEL_MARGIN = 8
TEXT_HEIGHT = 20
THUMBNAIL_WIDTH = 240
THUMBNAIL_HEIGHT = 160
TIMELINE_WIDTH = WINDOW_WIDTH - THUMBNAIL_WIDTH - 3 * MARGIN
TIMELINE_HEIGHT = 120
ANALYSIS_INTERVAL_SLIDER_WIDTH = WINDOW_WIDTH - 2 * MARGIN
ANALYSIS_INTERVAL_SLIDER_HEIGHT = 120
ANALYSIS_START_BUTTON_WIDTH = 200
ANALYSIS_START_BUTTON_HEIGHT = 60

START_LABEL_X = MARGIN
START_LABEL_Y = MARGIN + TEXT_HEIGHT - LABEL_MARGIN
START_FRAME_X = MARGIN
START_FRAME_Y = MARGIN + TEXT_HEIGHT
START_TIMELINE_X = MARGIN + THUMBNAIL_WIDTH + MARGIN
START_TIMELINE_Y = START_FRAME_Y + (THUMBNAIL_HEIGHT - TIMELINE_HEIGHT) // 2
END_LABEL_X = MARGIN
END_LABEL_Y = START_FRAME_Y + THUMBNAIL_HEIGHT + MARGIN + TEXT_HEIGHT - LABEL_MARGIN
END_FRAME_X = MARGIN
END_FRAME_Y = END_LABEL_Y + LABEL_MARGIN
END_TIMELINE_X = MARGIN + THUMBNAIL_WIDTH + MARGIN
END_TIMELINE_Y = END_FRAME_Y + (THUMBNAIL_HEIGHT - TIMELINE_HEIGHT) // 2
ANALYSIS_INTERVAL_LABEL_X = MARGIN
ANALYSIS_INTERVAL_LABEL_Y = END_FRAME_Y + THUMBNAIL_HEIGHT + MARGIN + TEXT_HEIGHT - LABEL_MARGIN
ANALYSIS_INTERVAL_SLIDER_X = MARGIN
ANALYSIS_INTERVAL_SLIDER_Y = ANALYSIS_INTERVAL_LABEL_Y + LABEL_MARGIN
ANALYSIS_START_BUTTON_X = (WINDOW_WIDTH - ANALYSIS_START_BUTTON_WIDTH) // 2
ANALYSIS_START_BUTTON_Y = ANALYSIS_INTERVAL_SLIDER_Y + ANALYSIS_INTERVAL_SLIDER_HEIGHT + MARGIN + 20

class ParameterSetupWindow:
  window = None
  video = None
  analyze_start_button = None
  start_frame_image = None
  start_frame_timeline = None
  end_frame_image = None
  end_frame_timeline = None
  analysis_interval = 50
  analysis_interval_slider = None
  analyze_start_callback = None

  def __init__(self):
    self.window = np.zeros((WINDOW_HEIGHT, WINDOW_WIDTH, 3), dtype=np.uint8)
    self.start_frame_image = OpenCVImage()
    self.start_frame_image.set_position((START_FRAME_X, START_FRAME_Y), (THUMBNAIL_WIDTH, THUMBNAIL_HEIGHT))
    self.start_frame_timeline = OpenCVTimeline()
    self.start_frame_timeline.set_position((START_TIMELINE_X, START_TIMELINE_Y), (TIMELINE_WIDTH, TIMELINE_HEIGHT))
    self.start_frame_timeline.set_callback(self.handle_start_frame_timeline_time_changed)
    self.end_frame_image = OpenCVImage()    
    self.end_frame_image.set_position((END_FRAME_X, END_FRAME_Y), (THUMBNAIL_WIDTH, THUMBNAIL_HEIGHT))
    self.end_frame_timeline = OpenCVTimeline()
    self.end_frame_timeline.set_position((END_TIMELINE_X, END_TIMELINE_Y), (TIMELINE_WIDTH, TIMELINE_HEIGHT))
    self.end_frame_timeline.set_callback(self.handle_end_frame_timeline_time_changed)
    self.analysis_interval_slider = OpenCVNumberInput(self.analysis_interval, 0, 5000, 1)
    self.analysis_interval_slider.set_position((ANALYSIS_INTERVAL_SLIDER_X, ANALYSIS_INTERVAL_SLIDER_Y), (ANALYSIS_INTERVAL_SLIDER_WIDTH, ANALYSIS_INTERVAL_SLIDER_HEIGHT))
    self.analysis_interval_slider.set_callback(self.handle_analysis_interval_slider_changed)
    self.analyze_start_button = OpenCVButton('Start Analysis')
    self.analyze_start_button.set_position((ANALYSIS_START_BUTTON_X, ANALYSIS_START_BUTTON_Y), (ANALYSIS_START_BUTTON_WIDTH, ANALYSIS_START_BUTTON_HEIGHT))
    self.analyze_start_button.set_callback(self.handle_analyze_start_button_click)

  def draw(self):
    cv2.rectangle(self.window, (0, 0), (WINDOW_WIDTH, WINDOW_HEIGHT), (150, 150, 150), -1)
    cv2.putText(self.window, 'Start', (START_LABEL_X, START_LABEL_Y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (20,20,20), 1)
    self.start_frame_timeline.draw(self.window)
    self.start_frame_image.draw(self.window)
    cv2.putText(self.window, 'End', (END_LABEL_X, END_LABEL_Y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (20,20,20), 1)
    self.end_frame_timeline.draw(self.window)
    self.end_frame_image.draw(self.window)
    cv2.putText(self.window, 'Analysis Interval (ms)', (ANALYSIS_INTERVAL_LABEL_X, ANALYSIS_INTERVAL_LABEL_Y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (20,20,20), 1)
    self.analysis_interval_slider.draw(self.window)
    self.analyze_start_button.draw(self.window)
    cv2.imshow(WINDOW_NAME, self.window)

  def show(self):
    cv2.namedWindow(WINDOW_NAME)
    cv2.setMouseCallback(WINDOW_NAME, self.handle_mouse_event)

  def hide(self):
    cv2.destroyWindow(WINDOW_NAME)

  def set_video(self, video):
    self.video = video
    frame_count = video.get(cv2.CAP_PROP_FRAME_COUNT)
    frame_rate = video.get(cv2.CAP_PROP_FPS)
    duration = frame_count / frame_rate * 1000
    self.start_frame_timeline.set_current_time(0)
    self.start_frame_timeline.set_duration(duration)
    self.video.set(cv2.CAP_PROP_POS_FRAMES, 0)
    ret, frame = video.read()
    if ret:
      self.start_frame_image.set_image(frame)    
    self.video.set(cv2.CAP_PROP_POS_FRAMES, frame_count-1)
    self.end_frame_timeline.set_current_time(duration)
    self.end_frame_timeline.set_duration(duration)
    ret, frame = video.read()
    if ret:
      self.end_frame_image.set_image(frame)

  def set_analyze_start_callback(self, callback):
    self.analyze_start_callback = callback

  def handle_mouse_event(self, event, x, y, flags, param):
    self.start_frame_timeline.handle_mouse_event(event, x, y, flags, param)
    self.end_frame_timeline.handle_mouse_event(event, x, y, flags, param)
    self.analysis_interval_slider.handle_mouse_event(event, x, y, flags, param)
    self.analyze_start_button.handle_mouse_event(event, x, y, flags, param)

  def handle_start_frame_timeline_time_changed(self, event_type, current_time):
    if self.video is None:
      return
    frame_number = int(current_time / 1000 * self.video.get(cv2.CAP_PROP_FPS))
    self.video.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
    ret, frame = self.video.read()
    if ret:
      self.start_frame_image.set_image(frame)

  def handle_end_frame_timeline_time_changed(self, event_type, current_time):
    if self.video is None:
      return
    frame_number = int(current_time / 1000 * self.video.get(cv2.CAP_PROP_FPS))
    self.video.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
    ret, frame = self.video.read()
    if ret:
      self.end_frame_image.set_image(frame)

  def handle_analysis_interval_slider_changed(self, event_type, value):
    if event_type == 'mouse_up':
      self.analysis_interval = value
      print(f'Analysis Interval set to: {self.analysis_interval} ms')

  def handle_analyze_start_button_click(self):
    if self.analyze_start_callback:
      self.analyze_start_callback({
        'start_time_ms': self.start_frame_timeline.get_current_time(),
        'end_time_ms': self.end_frame_timeline.get_current_time(),
        'analysis_interval': self.analysis_interval,
      })