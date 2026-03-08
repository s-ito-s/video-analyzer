import cv2

class OpenCVButton:
  position = (0, 0)
  size = (100, 30)
  label = "Button" 
  is_mouse_down = False
  is_mouse_hover = False
  callback = None

  def __init__(self, label="Button"):
    self.label = label

  def set_position(self, position, size):
    self.position = position
    self.size = size

  def set_callback(self, callback):
    self.callback = callback
  
  def handle_mouse_event(self, event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONDOWN:
      self.mouse_pos = (x, y)
      self.is_mouse_down = self.is_inside(x, y)
    elif event == cv2.EVENT_LBUTTONUP:
      self.mouse_pos = (x, y)
      self.is_mouse_down = self.is_inside(x, y)
      if self.is_mouse_down and self.is_mouse_hover:
        if self.callback:
          self.callback()
      self.is_mouse_down = False
    elif event == cv2.EVENT_MOUSEMOVE:
      self.mouse_pos = (x, y)
      self.is_mouse_hover = self.is_inside(x, y)

  def draw(self, window):
    x, y = self.position
    width, height = self.size
      
    if self.is_mouse_down:
      cv2.rectangle(window, (x, y), (x + width, y + height), (150, 150, 150), -1)
    elif self.is_mouse_hover:
      cv2.rectangle(window, (x, y), (x + width, y + height), (180, 180, 180), -1)
    else:
      cv2.rectangle(window, (x, y), (x + width, y + height), (200, 200, 200), -1)
    cv2.putText(window, self.label, (x + 10, y + height // 2 + 5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 1)

  def is_inside(self, x, y):
    pos_x = self.position[0]
    pos_y = self.position[1]
    width = self.size[0]
    height = self.size[1]
    return pos_x <= x <= pos_x + width and pos_y <= y <= pos_y + height
