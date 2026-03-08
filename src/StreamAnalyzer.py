from ultralytics import YOLO
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))
from framework.util.RectTracker import RectTracker

class StreamAnalyzer:
  model = None
  rectTracker = None

  def __init__(self):
    pass

  def open(self):
    self.model = YOLO('yolov5s.pt')
    self.rectTracker = RectTracker(0.5, 1, 3)

  def analyze(self, frame):
    results = self.model.predict(source=frame)     

    personsRects = []
    for result in results:
      for box in result.boxes:
        x1, y1, x2, y2 = map(int, box.xyxy[0])
        if box.cls[0] == 0: # Person class
          personsRects.append([x1, y1, x2-x1, y2-y1])

    appeared_rects = self.rectTracker.update(personsRects)["appeared"]
    return list(map( lambda rect: [rect.x, rect.y, rect.w, rect.h], appeared_rects))

  def close(self):
    pass
  