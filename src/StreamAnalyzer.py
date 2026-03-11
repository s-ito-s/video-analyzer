from ultralytics import YOLO
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))
from framework.util.RectTracker import RectTracker

class StreamAnalyzer:
  model = None
  rectTracker = None
  time_series_rect_data = []

  def __init__(self):
    pass

  def open(self):
    self.model = YOLO('yolo26n.pt')
    self.rectTracker = RectTracker(0.5, 5, 5)

  def analyze(self, frame, time_ms):
    results = self.model.predict(source=frame)

    personsRects = []
    for result in results:
      for box in result.boxes:
        x1, y1, x2, y2 = map(int, box.xyxy[0])
        if box.cls[0] == 0 and box.conf[0] > 0.7: # Person class
          personsRects.append([x1, y1, x2-x1, y2-y1])

    tracking_results = self.rectTracker.update(personsRects)
    appeared_rects = tracking_results["appeared"]
    
    # debug
    # disappeared_rects = tracking_results["disappeared"]
    # self.time_series_rect_data.append({
    #   "time_ms": time_ms,
    #   "rects": personsRects,
    #   "appeared": appeared_rects,
    #   "disappeared": disappeared_rects
    # })

    return list(map( lambda rect: [rect.x, rect.y, rect.w, rect.h], appeared_rects))

  def close(self):
    pass
    # debug
    # for data in self.time_series_rect_data:
    #   print(data)
  