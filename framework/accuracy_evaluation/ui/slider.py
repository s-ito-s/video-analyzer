import cv2

class OpenCVSlider:
  position = (0, 0)
  size = (100, 30)
  min_value = 0
  max_value = 100
  value = 50
  is_mouse_down = False
  mouse_pos = (0, 0)
  callback = None

  def __init__(self, initial_value=50, min_value=0, max_value=100):
    self.value = initial_value
    self.min_value = min_value
    self.max_value = max_value

  def set_position(self, position, size):
    self.position = position
    self.size = size

  def set_value(self, value):
    if self.min_value <= value <= self.max_value:
      self.value = value

  def get_value(self):
    return self.value
  
  def set_callback(self, callback):
    self.callback = callback
  
  def handle_mouse_event(self, event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONDOWN:
      self.mouse_pos = (x, y)
      slider_x, slider_y = self.position
      slider_width, slider_height = self.size
      if slider_x <= x <= slider_x + slider_width and slider_y <= y <= slider_y + slider_height:
        self.is_mouse_down = True

    elif event == cv2.EVENT_LBUTTONUP:
      if not self.is_mouse_down :
        return
      else :
        self.is_mouse_down = False
            
      if self.callback:
        self.callback('mouseUp', self.value)
    elif event == cv2.EVENT_MOUSEMOVE and self.is_mouse_down:
      if not self.is_mouse_down :
        return
      
      self.mouse_pos = (x, y)
      slider_x, slider_y = self.position
      slider_width, slider_height = self.size
      if slider_x <= x <= slider_x + slider_width and slider_y <= y <= slider_y + slider_height:
        relative_x = x - slider_x
        new_value = self.min_value + (relative_x / slider_width) * (self.max_value - self.min_value)
        self.set_value(int(new_value))
        if self.callback:
          self.callback('mouseMove', self.value)

  def draw(self, window):
    x, y = self.position
    width, height = self.size
    fill_width = int((self.value - self.min_value) / (self.max_value - self.min_value) * width)

    # Draw the slider background
    cv2.rectangle(window, (x, y), (x + width, y + height), (200, 200, 200), -1)
    # Draw the filled part of the slider
    cv2.rectangle(window, (x, y), (x + fill_width, y + height), (100, 100, 250), -1)
    # Draw the border
    cv2.rectangle(window, (x, y), (x + width, y + height), (0, 0, 0), 1)