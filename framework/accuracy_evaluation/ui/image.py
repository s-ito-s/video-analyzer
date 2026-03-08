import cv2

class OpenCVImage:
  position = (0, 0)
  size = (300, 300)
  img = None
  img_width = 0
  img_height = 0 

  def __init__(self):
    pass

  def set_position(self, position, size):
    self.position = position
    self.size = size

  def set_image(self, img):
    if img is None:
      print("No image data provided.")
      return

    height, width, channels = img.shape[:3]
    w = self.size[0]
    h = self.size[1]
    aspect_ratio_img = width / height
    if w / h > aspect_ratio_img:
      self.img_width = int(h * aspect_ratio_img)
      self.img_height = h
    else:
      self.img_height = int(w / aspect_ratio_img)
      self.img_width = w
    self.img = cv2.resize(img, (self.img_width, self.img_height))

  def get_image(self):
    return self.img
  
  def draw(self, window):
    x, y = self.position
    w, h = self.size
    cv2.rectangle(window, (x, y), (x + w, y + h), (0, 0, 0), -1)       

    if self.img is None:
      return
    
    offset_x = (self.size[0] - self.img_width) // 2
    offset_y = (self.size[1] - self.img_height) // 2
    l = self.position[0] + offset_x
    t = self.position[1] + offset_y
    r = l + self.img_width
    b = t + self.img_height    
    window[t:b, l:r] = self.img

