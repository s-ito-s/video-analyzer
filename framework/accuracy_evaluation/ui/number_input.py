import cv2

BAR_POS_Y = 60
BAR_HEIGHT = 15
SCALE_LINE_HEIGHT = 8
SCALE_TIME_TEXT_SIZE = 16
HEIGHT = 120

BACKGROUND_COLOR = (230, 230, 230)
BAR_VALID_VALUE_RANGE_COLOR = (50,150,50)
BAR_INVALID_VALUE_RANGE_COLOR = (150,150,150)
SCALE_COLOR = (80, 80, 80)
VALUE_COLOR = (50, 50, 250)

class OpenCVNumberInput:
  position = (0, 0)
  size = (300, HEIGHT)

  value = 0
  min = 0
  max = 100
  significant_digit = 1
  number_per_pixel = 1


  is_mouse_down = False
  mouse_pos = (0, 0)
  callback = None

  def __init__(self, value=0, min=0, max=100, significant_digit=1):
    self.value = value
    self.min = min
    self.max = max
    self.significant_digit = significant_digit

  def set_position(self, position, size):
    self.position = position
    self.size = size

  def set_value(self, value):
    self.value = value

  def get_value(self):
    if self.significant_digit >= 0:
      return round(self.value, 1-self.significant_digit)
    else:
      return round(self.value, -self.significant_digit)
  
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
        self.callback('mouse_up', self.get_value())
    elif event == cv2.EVENT_MOUSEMOVE:
      if not self.is_mouse_down :
        return
      prev_mouse_pos_x = self.mouse_pos[0]
      mouse_pos_x = x
      diff_x = prev_mouse_pos_x - mouse_pos_x
      new_value = self.value + diff_x * self.number_per_pixel
      self.value = max(self.min, min(self.max, new_value))
      self.mouse_pos = (x, y)
    elif event == cv2.EVENT_MOUSEWHEEL:
      if not self.is_inside(x, y):
        return
      new_number_per_pixel = self.number_per_pixel
      if flags > 0:
        new_number_per_pixel *= 0.9
      else:
        new_number_per_pixel *= 1.1
      self.number_per_pixel = new_number_per_pixel

  def draw(self, window):
    x, y = self.position
    width, height = self.size
      
    # Draw the background
    cv2.rectangle(window, (x, y), (x + width, y + height), BACKGROUND_COLOR, -1)

    # Draw the bar
    bar_pos_y = y + BAR_POS_Y
    cv2.rectangle(window, (x, bar_pos_y), (x + width, bar_pos_y + BAR_HEIGHT), BAR_INVALID_VALUE_RANGE_COLOR, -1)
    value_start_x = int(min(x + width, max(x, self.value_to_position(self.min) + x)))
    value_end_x = int(min(x + width, max(x, self.value_to_position(self.max) + x)))
    cv2.rectangle(window, (value_start_x, bar_pos_y), (value_end_x, bar_pos_y + BAR_HEIGHT), BAR_VALID_VALUE_RANGE_COLOR, -1)

    # Draw the scale lines and time texts
    scale_info = self.adjust_scale()
    scale_interval = scale_info["scale_interval"]
    text_interval = scale_info["text_interval"]
    start_value = self.pix_to_value(0)
    end_value = self.pix_to_value(width)
    first_scale_value = (start_value // scale_interval) * scale_interval
    i = 0

    while True:
      scale_value = first_scale_value + i * scale_interval
      if scale_value > end_value:
        break
      if scale_value > self.max:
        break
      if scale_value < self.min:
        i += 1
        continue

      # Draw scale line
      scale_pos_x = int(self.value_to_position(scale_value)) + x
      scale_pos_start_y = bar_pos_y + BAR_HEIGHT
      if scale_value % text_interval == 0:
        scale_pos_end_y = scale_pos_start_y + SCALE_LINE_HEIGHT * 2
      else:
        scale_pos_end_y = scale_pos_start_y + SCALE_LINE_HEIGHT
      cv2.line(window, (scale_pos_x, scale_pos_start_y), (scale_pos_x, scale_pos_end_y), SCALE_COLOR, 1)

      # Draw time text
      if scale_interval < 1:
        print('scale', scale_interval, round(scale_value / text_interval, 1))

      if self.is_integer_num(round(scale_value / text_interval, 1)):
        text_size, _ = cv2.getTextSize(str(scale_value), cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
        text_x = scale_pos_x - text_size[0] // 2
        text_y = scale_pos_end_y + 5 + text_size[1]
        cv2.putText(window, str(scale_value), (text_x, text_y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, SCALE_COLOR, 1)

      i += 1

    # Draw value indicator
    current_value_text_pos_x = int(width / 2) + x
    cv2.line(window, (current_value_text_pos_x, y), (current_value_text_pos_x, y + height), VALUE_COLOR, 2)
    current_value_text = str(self.get_value())
    text_size, _ = cv2.getTextSize(current_value_text, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)
    text_x = current_value_text_pos_x - text_size[0] // 2
    text_y = y + int((BAR_POS_Y - text_size[1]) // 2) + text_size[1]
    text_bg_rect_l = text_x - 4
    text_bg_rect_t = text_y - text_size[1] - 4
    text_bg_rect_r = text_bg_rect_l + text_size[0] + 8
    text_bg_rect_b = text_bg_rect_t + text_size[1] + 8
    cv2.rectangle(window, (text_bg_rect_l, text_bg_rect_t), (text_bg_rect_r, text_bg_rect_b), BACKGROUND_COLOR, -1)
    cv2.putText(window, current_value_text, (text_x, text_y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, VALUE_COLOR, 2)

    # Draw the border
    cv2.rectangle(window, (x, y), (x + width, y + height), (0, 0, 0), 1)

  def is_inside(self, x, y):
    pos_x = self.position[0]
    pos_y = self.position[1]
    width = self.size[0]
    height = self.size[1]
    return pos_x <= x <= pos_x + width and pos_y <= y <= pos_y + height

  def value_to_position(self, value):
    start_value = self.value - self.size[0] / 2 * self.number_per_pixel
    return (value - start_value) / self.number_per_pixel
  
  def pix_to_value(self, pix):
    start_value = self.value - self.size[0] / 2 * self.number_per_pixel
    return pix * self.number_per_pixel + start_value

  def adjust_scale(self):
    map = [
      { "number_per_pixel":0.01, "scale_interval":0.1, "text_interval":1,    },
      { "number_per_pixel":0.02, "scale_interval":0.2, "text_interval":2,    },
      { "number_per_pixel":0.05, "scale_interval":0.5, "text_interval":5,    },
      { "number_per_pixel":0.1,  "scale_interval":1,   "text_interval":10,   },
      { "number_per_pixel":0.2,  "scale_interval":2,   "text_interval":20,   },
      { "number_per_pixel":0.5,  "scale_interval":5,   "text_interval":50,   },
      { "number_per_pixel":1,    "scale_interval":10,  "text_interval":100,  },
      { "number_per_pixel":2,    "scale_interval":20,  "text_interval":200,  },
      { "number_per_pixel":5,    "scale_interval":50,  "text_interval":500,  },
      { "number_per_pixel":10,   "scale_interval":100, "text_interval":1000, },
      { "number_per_pixel":20,   "scale_interval":200, "text_interval":2000, },
      { "number_per_pixel":50,   "scale_interval":500, "text_interval":5000, },
      { "number_per_pixel":100,  "scale_interval":1000, "text_interval":10000, },
    ]
    for m in map:
      if m["number_per_pixel"] > self.number_per_pixel:
        return {
          "scale_interval": m["scale_interval"],
          "text_interval": m["text_interval"],
        }      
    return {
      "scale_interval": 1000,
      "text_interval": 10000,
    }
      
  def is_integer_num(self, n):
    if isinstance(n, int):
      return True
    if isinstance(n, float):
      return n.is_integer()
    return False
