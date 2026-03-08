import cv2
import numpy as np
import tkinter.filedialog

class OpenCVFileSelector:
  position = (0, 0)
  size = (100, 30)
  file_path = ""
  is_mouse_down = False
  is_mouse_hover = False
  callback = None

  def __init__(self):
    pass

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
        self.file_path = tkinter.filedialog.askopenfilename()
        if self.callback:
          self.callback(self.file_path)
      self.is_mouse_down = False
    elif event == cv2.EVENT_MOUSEMOVE:
      self.mouse_pos = (x, y)
      self.is_mouse_hover = self.is_inside(x, y)

  def draw(self, window):
    x, y = self.position
    width, height = self.size
    display_text = self.file_path if self.file_path else "Select File"
    cv2.rectangle(window, (x, y), (x + width, y + height), (230, 230, 230), -1)
    cv2.rectangle(window, (x, y), (x + width, y + height), (40, 40, 40), 1)
    self.draw_text_with_ellipsis(window, display_text, (x + 10, y + height // 2 + 5), width - 20, font_scale=0.6, color=(0, 0, 0), thickness=1)

  def is_inside(self, x, y):
    pos_x = self.position[0]
    pos_y = self.position[1]
    width = self.size[0]
    height = self.size[1]
    return pos_x <= x <= pos_x + width and pos_y <= y <= pos_y + height
  
  def draw_text_with_ellipsis(
    self,
    img: np.ndarray,
    text: str,
    position: tuple[int, int],
    max_width: int,
    font: int = cv2.FONT_HERSHEY_SIMPLEX,
    font_scale: float = 1.0,
    color: tuple[int, int, int] = (255, 255, 255),
    thickness: int = 1,
    line_type: int = cv2.LINE_AA
) -> np.ndarray:
    # テキストサイズを取得
    (text_width, text_height), baseline = cv2.getTextSize(
        text, font, font_scale, thickness
    )

    # テキストが最大幅に収まる場合はそのまま描画
    if text_width <= max_width:
        cv2.putText(
            img, text, position, font, font_scale,
            color, thickness, line_type
        )
        return img

    # 「...」のサイズを取得
    ellipsis = "..."
    (ellipsis_width, _), _ = cv2.getTextSize(
        ellipsis, font, font_scale, thickness
    )

    # 「...」を含めた状態で収まる文字数を二分探索で見つける
    left, right = 0, len(text)
    best_length = 0

    while left <= right:
        mid = (left + right) // 2
        test_text = text[:mid] + ellipsis
        (test_width, _), _ = cv2.getTextSize(
            test_text, font, font_scale, thickness
        )

        if test_width <= max_width:
            best_length = mid
            left = mid + 1
        else:
            right = mid - 1

    # 省略されたテキストを描画
    truncated_text = text[:best_length] + ellipsis
    cv2.putText(
        img, truncated_text, position, font, font_scale,
        color, thickness, line_type
    )

