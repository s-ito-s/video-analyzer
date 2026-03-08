import cv2

HEIGHT = 120
EVENT_MARKER_GAP_Y = 15
EVENT_MARKER_HEIGHT = 20
EVENT_MARKER_MIN_WIDTH = 10
SEEKBAR_POS_Y = 50
SEEKBAR_HEIGHT = 15
SCALE_LINE_HEIGHT = 8
SCALE_TIME_TEXT_SIZE = 16

BACKGROUND_COLOR = (230, 230, 230)
SEEKBAR_DATA_COLOR = (50,150,50)
SEEKBAR_EMPTY_DATA_COLOR = (150,150,150)
SCALE_COLOR = (80, 80, 80)
CURRENT_TIME_COLOR = (50, 50, 250)
EVENT_MARKER_COLOR = (250, 100, 100)
SELECTED_EVENT_MARKER_BORDER_COLOR = (0, 0, 255)

class OpenCVEventTimeline:
  position = (0, 0)
  size = (300, HEIGHT)

  current_time = 0
  duration = 10 * 60 * 1000  # 10 minutes in milliseconds
  time_per_pixel = 1000 # milliseconds per pixel

  event_markers = [
    # Example event markers
    { "id":"event1", "time_ms": 15000, },
    { "id":"event2", "time_ms": 45000, "durationMs": 10000 },
    { "id":"event3", "time_ms": 90000, },
  ]
  event_marker_rects = []
  selected_event_marker_id = None
  event_markers_selected_callback = None

  is_mouse_down = False
  mouse_pos = (0, 0)
  time_changed_callback = None

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

  def set_event_markers(self, markers):
    self.event_markers = markers

  def set_time_changed_callback(self, callback):
    self.time_changed_callback = callback

  def set_event_markers_selected_callback(self, callback):
    self.event_markers_selected_callback = callback
  
  def handle_mouse_event(self, event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONDOWN:
      self.is_mouse_down = self.is_inside(x, y)
      self.mouse_pos = (x, y)
      for marker_rect in self.event_marker_rects:
        rect = marker_rect["rect"]
        if rect["left"] <= x <= rect["right"] and rect["top"] <= y <= rect["bottom"]:
          self.selected_event_marker_id = marker_rect["marker_id"]
          if self.event_markers_selected_callback:
            self.event_markers_selected_callback(self.selected_event_marker_id)
          break
    elif event == cv2.EVENT_LBUTTONUP:
      if not self.is_mouse_down :
        return
      self.is_mouse_down = False            
      if self.time_changed_callback:
        self.time_changed_callback('mouseUp', self.current_time)
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
    self.event_marker_rects = []
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

    # Draw event markers
    start_time = self.pix_to_time(0)
    end_time = self.pix_to_time(width)
    for marker in self.event_markers:
      marker_pos_left = int(self.time_to_position(marker["time_ms"])) + x
      marker_width = EVENT_MARKER_MIN_WIDTH
      if "durationMs" in marker:
        marker_width = int(marker["durationMs"] / self.time_per_pixel)
      else:
        marker_pos_left -= marker_width // 2
      if (self.pix_to_time(marker_pos_left + marker_width - x) < start_time) or (self.pix_to_time(marker_pos_left - x) > end_time):
        continue # Skip if the marker is out of visible range
      marker_pos_right = marker_pos_left + marker_width
      marker_pos_top = y + EVENT_MARKER_GAP_Y
      marker_pos_bottom = marker_pos_top + EVENT_MARKER_HEIGHT
      cv2.rectangle(window, (marker_pos_left, marker_pos_top), (marker_pos_right, marker_pos_bottom), EVENT_MARKER_COLOR, -1)
      self.event_marker_rects.append({
        "marker_id": marker["id"],
        "rect": {
          "left": marker_pos_left,
          "top": marker_pos_top,
          "right": marker_pos_right,
          "bottom": marker_pos_bottom
        }
      })

    for marker_rect in self.event_marker_rects:
      if self.selected_event_marker_id == marker_rect["marker_id"]:
        rect = marker_rect["rect"]
        cv2.rectangle(window, (rect["left"], rect["top"]), (rect["right"], rect["bottom"]), SELECTED_EVENT_MARKER_BORDER_COLOR, 2)

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
  
  def time_to_str(self, time_ms):
    HOUR_MS = 60 * 60 * 1000
    MIN_MS = 60 * 1000
    SEC_MS = 1000
    hour = str(int(time_ms // HOUR_MS))
    min = str(int((time_ms % HOUR_MS) // MIN_MS)).zfill(2)
    sec = str(int((time_ms % MIN_MS) // SEC_MS)).zfill(2)
    return f"{hour}:{min}:{sec}"