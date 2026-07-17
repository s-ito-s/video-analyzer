from typing import final

# StreamAnalyzerResponse
# https://github.com/SafieDev/aipf-sample-stream-analyzer/blob/main/proto/stream/v1/analyzer.proto

class BaseStreamAnalyzer:
  events = []
  objects = []
  metrics = []

  def __init__(self):
    pass

  def open(self):
    pass

  def analyze(self, frame, time_ms):
    pass

  def close(self):
    pass

  # event = {
  #   time_ms: number,
  #   data: {
  #     event_index: string,
  #     type: string,
  #     labels: string[],
  #     score: number,
  #     picture: Image
  #     geometry_config_ids: number[]
  #     data: any,
  #   }
  # }
  @final
  def detect_event(self, time_ms, data):
    self.events.append({
      "time_ms": time_ms,
      "data": data
    })

  # object = {
  #   time_ms: number,
  #   data: {
  #     start_timestamp: string
  #     end_timestamp: string
  #     duration_ms: number,
  #     object_index: string,
  #     type: string,
  #     labels: string[],
  #     score: number,
  #     picture: Image
  #     geometry_config_ids: number[]
  #     data: any,
  #   }
  # }
  @final
  def detect_object(self, time_ms, data):
    self.objects.append({
      "time_ms": time_ms,
      "data": data
    })

  # metrics = {
  #   time_ms: number,
  #   data: {
  #     timestamp: string,
  #     units: string[],
  #     metrics: map[string, number],
  #   }
  # }
  @final
  def record_metric(self, time_ms, data):
    self.metrics.append({
      "time_ms": time_ms,
      "data": data
    })  

  @final
  def pop_event(self):
    if len(self.events) > 0:
      return self.events.pop(0)
    else:
      return None
    
  @final
  def pop_object(self):
    if len(self.objects) > 0:
      return self.objects.pop(0)
    else:
      return None
    
  @final
  def pop_metric(self):
    if len(self.metrics) > 0:
      return self.metrics.pop(0)
    else:
      return None
