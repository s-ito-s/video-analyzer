import cv2

SEEKBAR_POS_Y = 60
SEEKBAR_HEIGHT = 15
SCALE_LINE_HEIGHT = 8
SCALE_TIME_TEXT_SIZE = 16
HEIGHT = 120

BACKGROUND_COLOR = (230, 230, 230)
SEEKBAR_DATA_COLOR = (50,150,50)
SEEKBAR_EMPTY_DATA_COLOR = (150,150,150)
SCALE_COLOR = (80, 80, 80)
CURRENT_TIME_COLOR = (50, 50, 250)

class OpenCVTimeline:
  position = (0, 0)
  size = (300, HEIGHT)

  current_time = 0
  duration = 10 * 60 * 1000  # 10 minutes in milliseconds
  time_per_pixel = 1000 # milliseconds per pixel

  is_mouse_down = False
  mouse_pos = (0, 0)
  callback = None

  def __init__(self):
    pass

  def set_position(self, position, size):
    self.position = position
    self.size = size

  def set_current_time(self, time):
    self.current_time = time

  def get_current_time(self):
    return self.current_time
  
  def set_duration(self, duration):
    self.duration = duration

  def get_duration(self):
    return self.duration

  def set_callback(self, callback):
    self.callback = callback
  
  def handle_mouse_event(self, event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONDOWN:
      self.is_mouse_down = self.is_inside(x, y)
      self.mouse_pos = (x, y)
    elif event == cv2.EVENT_LBUTTONUP:
      if not self.is_mouse_down :
        return
      self.is_mouse_down = False            
      if self.callback:
        self.callback('mouseUp', self.current_time)
    elif event == cv2.EVENT_MOUSEMOVE:
      if not self.is_mouse_down :
        return
      prev_mouse_pos_x = self.mouse_pos[0]
      mouse_pos_x = x
      diff_x = prev_mouse_pos_x - mouse_pos_x
      new_current_time = self.current_time + diff_x * self.time_per_pixel
      self.current_time = max(0, min(self.duration, new_current_time))
      self.mouse_pos = (x, y)
    elif event == cv2.EVENT_MOUSEWHEEL:
      if not self.is_inside(x, y):
        return
      new_time_per_pixel = self.time_per_pixel
      if flags > 0:
        new_time_per_pixel *= 0.9
      else:
        new_time_per_pixel *= 1.1
      self.time_per_pixel = new_time_per_pixel

  def draw(self, window):
    x, y = self.position
    width, height = self.size
      
    # Draw the background
    cv2.rectangle(window, (x, y), (x + width, y + height), BACKGROUND_COLOR, -1)
    
    # Draw the seekbar
    seek_bar_pos_y = y + SEEKBAR_POS_Y
    cv2.rectangle(window, (x, seek_bar_pos_y), (x + width, seek_bar_pos_y + SEEKBAR_HEIGHT), SEEKBAR_EMPTY_DATA_COLOR, -1)
    data_start_x = int(min(x + width, max(x, self.time_to_position(0) + x)))
    data_end_x = int(min(x + width, max(x, self.time_to_position(self.duration) + x)))
    cv2.rectangle(window, (data_start_x, seek_bar_pos_y), (data_end_x, seek_bar_pos_y + SEEKBAR_HEIGHT), SEEKBAR_DATA_COLOR, -1)

    # Draw the scale lines and time texts
    scale_info = self.adjust_scale()
    scale_interval = scale_info["scaleInterval"]
    text_interval = scale_info["textInterval"]
    start_time = self.pix_to_time(0)
    end_time = self.pix_to_time(width)
    first_scale_time = (start_time // scale_interval) * scale_interval
    i = 0

    while True:
      scale_time = first_scale_time + i * scale_interval
      if scale_time > end_time:
        break
      if scale_time > self.duration:
        break
      if scale_time < 0:
        i += 1
        continue

      # Draw scale line
      scale_pos_x = int(self.time_to_position(scale_time)) + x
      scale_pos_start_y = seek_bar_pos_y + SEEKBAR_HEIGHT
      if scale_time % text_interval == 0:
        scale_pos_end_y = scale_pos_start_y + SCALE_LINE_HEIGHT * 2
      else:
        scale_pos_end_y = scale_pos_start_y + SCALE_LINE_HEIGHT
      cv2.line(window, (scale_pos_x, scale_pos_start_y), (scale_pos_x, scale_pos_end_y), SCALE_COLOR, 1)

      # Draw time text
      if scale_time % text_interval == 0:
        time_text = self.time_to_str(scale_time)
        text_size, _ = cv2.getTextSize(time_text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
        text_x = scale_pos_x - text_size[0] // 2
        text_y = scale_pos_end_y + 5 + text_size[1]
        cv2.putText(window, time_text, (text_x, text_y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, SCALE_COLOR, 1)

      i += 1

    # Draw current time indicator
    current_time_text_pos_x = int(self.time_to_position(self.current_time)) + x
    cv2.line(window, (current_time_text_pos_x, y), (current_time_text_pos_x, y + height), CURRENT_TIME_COLOR, 2)
    current_time_text = self.time_to_str(self.current_time)
    text_size, _ = cv2.getTextSize(current_time_text, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)
    text_x = current_time_text_pos_x - text_size[0] // 2
    text_y = y + int((SEEKBAR_POS_Y - text_size[1]) // 2) + text_size[1]
    text_bg_rect_l = text_x - 4
    text_bg_rect_t = text_y - text_size[1] - 4
    text_bg_rect_r = text_bg_rect_l + text_size[0] + 8
    text_bg_rect_b = text_bg_rect_t + text_size[1] + 8
    cv2.rectangle(window, (text_bg_rect_l, text_bg_rect_t), (text_bg_rect_r, text_bg_rect_b), BACKGROUND_COLOR, -1)
    cv2.putText(window, current_time_text, (text_x, text_y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, CURRENT_TIME_COLOR, 2)

    # Draw the border
    cv2.rectangle(window, (x, y), (x + width, y + height), (0, 0, 0), 1)

  def is_inside(self, x, y):
    pos_x = self.position[0]
    pos_y = self.position[1]
    width = self.size[0]
    height = self.size[1]
    return pos_x <= x <= pos_x + width and pos_y <= y <= pos_y + height

  def time_to_position(self, time):
    start_time_ms = self.current_time - self.size[0] / 2 * self.time_per_pixel
    return (time - start_time_ms) / self.time_per_pixel
  
  def pix_to_time(self, pix):
    start_time_ms = self.current_time - self.size[0] / 2 * self.time_per_pixel
    return pix * self.time_per_pixel + start_time_ms

  def adjust_scale(self):
    map = [
      { "timePerPix":14,     "scaleInterval":100,        "textInterval":1000,  },
      { "timePerPix":50,     "scaleInterval":1000,       "textInterval":5*1000,  },
      { "timePerPix":120,    "scaleInterval":1000,       "textInterval":10*1000, },
      { "timePerPix":240,    "scaleInterval":1000*5,     "textInterval":30*1000, },
      { "timePerPix":700,    "scaleInterval":1000*10,    "textInterval":60*1000, },
      { "timePerPix":2500,   "scaleInterval":1000*30,    "textInterval":5*60*1000, },
      { "timePerPix":8000,   "scaleInterval":1000*60,    "textInterval":10*60*1000, },
      { "timePerPix":24000,  "scaleInterval":1000*60*5,  "textInterval":30*60*1000, },
      { "timePerPix":80000,  "scaleInterval":1000*60*10, "textInterval":60*60*1000, },
      { "timePerPix":120000, "scaleInterval":1000*60*60, "textInterval":3*60*60*1000 },
      { "timePerPix":400000, "scaleInterval":1000*60*60, "textInterval":6*60*60*1000 },
    ]
    for m in map:
      if m["timePerPix"] > self.time_per_pixel:
        return {
          "scaleInterval": m["scaleInterval"],
          "textInterval": m["textInterval"],
        }      
    return {
      "scaleInterval": 1000*60*60,
      "textInterval": 6*60*60*1000,
    }
  
  def time_to_str(self, timeMs):
    HOUR_MS = 60 * 60 * 1000
    MIN_MS = 60 * 1000
    SEC_MS = 1000
    hour = str(int(timeMs // HOUR_MS))
    min = str(int((timeMs % HOUR_MS) // MIN_MS)).zfill(2)
    sec = str(int((timeMs % MIN_MS) // SEC_MS)).zfill(2)
    return f"{hour}:{min}:{sec}"

