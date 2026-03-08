import cv2
import numpy as np
from ui.button import OpenCVButton
from ui.file_selector import OpenCVFileSelector

WINDOW_NAME = 'File Input'
WINDOW_WIDTH = 600
WINDOW_HEIGHT = 300

class FileInputWindow:
  window = None
  next_button = None
  file_selector = None
  file_name = None
  file_input_callback = None

  def __init__(self):
    self.window = np.zeros((WINDOW_HEIGHT, WINDOW_WIDTH, 3), dtype=np.uint8)
    self.file_selector = OpenCVFileSelector()
    self.file_selector.set_position((50, 50), (500, 50))
    self.file_selector.set_callback(self.handle_file_selected)
    self.next_button = OpenCVButton('Next')
    self.next_button.set_position((100, 150), (400, 100))
    self.next_button.set_callback(self.handle_next_button_click)

  def draw(self):
    cv2.rectangle(self.window, (0, 0), (WINDOW_WIDTH, WINDOW_HEIGHT), (150, 150, 150), -1)
    self.next_button.draw(self.window)
    self.file_selector.draw(self.window)
    cv2.imshow(WINDOW_NAME, self.window)

  def show(self):
    cv2.namedWindow(WINDOW_NAME)
    cv2.setMouseCallback(WINDOW_NAME, self.handle_mouse_event)

  def hide(self):
    cv2.destroyWindow(WINDOW_NAME)

  def set_file_input_callback(self, callback):
    self.file_input_callback = callback

  def handle_mouse_event(self, event, x, y, flags, param):
    self.next_button.handle_mouse_event(event, x, y, flags, param)
    self.file_selector.handle_mouse_event(event, x, y, flags, param)

  def handle_file_selected(self, file_path):
    self.file_name = file_path

  def handle_next_button_click (self):
    if self.file_input_callback:
      self.file_input_callback(self.file_name)