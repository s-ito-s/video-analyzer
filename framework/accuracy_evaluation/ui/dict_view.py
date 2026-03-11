import cv2

BACKGROUND_COLOR = (40, 40, 40)
KEY_COLOR = (180, 220, 255)
VALUE_COLOR = (255, 255, 255)
SEPARATOR_COLOR = (80, 80, 80)
NESTED_INDENT = 20
LINE_HEIGHT = 24
FONT = cv2.FONT_HERSHEY_SIMPLEX
FONT_SCALE = 0.45
FONT_THICKNESS = 1
PADDING_X = 10
PADDING_Y = 10
SCROLL_SPEED = 3

class OpenCVDictView:
  position = (0, 0)
  size = (300, 300)
  data = None
  scroll_offset = 0
  max_scroll = 0

  def __init__(self):
    pass

  def set_position(self, position, size):
    self.position = position
    self.size = size

  def set_data(self, data):
    self.data = data
    self.scroll_offset = 0
    self._update_max_scroll()

  def _update_max_scroll(self):
    if self.data is None:
      self.max_scroll = 0
      return
    lines = self._flatten(self.data, 0)
    total_height = len(lines) * LINE_HEIGHT + PADDING_Y * 2
    self.max_scroll = max(0, total_height - self.size[1])

  def _flatten(self, data, depth):
    lines = []
    if isinstance(data, dict):
      for key, value in data.items():
        if isinstance(value, (dict, list)):
          lines.append((depth, str(key), None))
          lines.extend(self._flatten(value, depth + 1))
        else:
          lines.append((depth, str(key), str(value)))
    elif isinstance(data, list):
      for i, item in enumerate(data):
        if isinstance(item, (dict, list)):
          lines.append((depth, f"[{i}]", None))
          lines.extend(self._flatten(item, depth + 1))
        else:
          lines.append((depth, f"[{i}]", str(item)))
    else:
      lines.append((depth, str(data), None))
    return lines

  def handle_mouse_event(self, event, x, y, flags, param):
    px, py = self.position
    w, h = self.size
    if not (px <= x <= px + w and py <= y <= py + h):
      return
    if event == cv2.EVENT_MOUSEWHEEL:
      if flags > 0:
        self.scroll_offset = max(0, self.scroll_offset - LINE_HEIGHT * SCROLL_SPEED)
      else:
        self.scroll_offset = min(self.max_scroll, self.scroll_offset + LINE_HEIGHT * SCROLL_SPEED)

  def draw(self, window):
    x, y = self.position
    w, h = self.size
    cv2.rectangle(window, (x, y), (x + w, y + h), BACKGROUND_COLOR, -1)

    if self.data is None:
      return

    lines = self._flatten(self.data, 0)
    clip_top = y
    clip_bottom = y + h

    for i, (depth, key, value) in enumerate(lines):
      line_y = y + PADDING_Y + i * LINE_HEIGHT - self.scroll_offset
      text_y = line_y + LINE_HEIGHT - 6

      if text_y < clip_top or line_y > clip_bottom:
        continue

      indent = PADDING_X + depth * NESTED_INDENT
      text_x = x + indent

      if value is not None:
        label = f"{key}: "
        cv2.putText(window, label, (text_x, text_y),
                    FONT, FONT_SCALE, KEY_COLOR, FONT_THICKNESS, cv2.LINE_AA)
        (label_w, _), _ = cv2.getTextSize(label, FONT, FONT_SCALE, FONT_THICKNESS)
        max_value_w = w - indent - label_w - PADDING_X
        display_value = self._truncate_text(value, max_value_w)
        cv2.putText(window, display_value, (text_x + label_w, text_y),
                    FONT, FONT_SCALE, VALUE_COLOR, FONT_THICKNESS, cv2.LINE_AA)
      else:
        cv2.putText(window, key, (text_x, text_y),
                    FONT, FONT_SCALE, KEY_COLOR, FONT_THICKNESS, cv2.LINE_AA)

      separator_y = line_y + LINE_HEIGHT - 1
      if clip_top <= separator_y <= clip_bottom:
        cv2.line(window, (x + indent, separator_y), (x + w - PADDING_X, separator_y),
                 SEPARATOR_COLOR, 1)

  def _truncate_text(self, text, max_width):
    if max_width <= 0:
      return ""
    (text_w, _), _ = cv2.getTextSize(text, FONT, FONT_SCALE, FONT_THICKNESS)
    if text_w <= max_width:
      return text
    for end in range(len(text) - 1, 0, -1):
      truncated = text[:end] + "..."
      (tw, _), _ = cv2.getTextSize(truncated, FONT, FONT_SCALE, FONT_THICKNESS)
      if tw <= max_width:
        return truncated
    return "..."
