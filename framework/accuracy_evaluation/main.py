import cv2
from window.file_input_window import FileInputWindow
from window.parameter_setup_window import ParameterSetupWindow
from window.processing_window import ProcessingWindow
from window.analysis_result_window import AnalysisResultWindow

file_input_window = FileInputWindow()
parameter_setup_window = ParameterSetupWindow()
processing_window =  ProcessingWindow()
analysis_result_window = AnalysisResultWindow()
video = None
settings = {
  "start_time_ms": 0,
  "end_time_ms": 0,
  "analysis_interval": 1000,
}
step = 'file_input' # 'file_input' => 'parameter_setup' => 'processing' => 'analysis_result'
result = None

def init():
  file_input_window.show()
  file_input_window.set_file_input_callback(handle_file_input)
  parameter_setup_window.set_analyze_start_callback(handle_start_analyze_button_click)

def event_loop():
  while True:
    if step == 'processing' and processing_window.is_processing_complete():
      handle_processing_complete()
    draw()  
    if cv2.waitKey(1) & 0xFF == ord('q'):
      break
  cv2.destroyAllWindows()

def draw():
  if step == 'file_input':
    file_input_window.draw()
  elif step == 'parameter_setup':
    parameter_setup_window.draw()
  elif step == 'processing':
    processing_window.draw()
  elif step == 'analysis_result':
    analysis_result_window.draw()

def handle_file_input(file_path):
  file_input_window.hide()
  global step
  step = 'parameter_setup'
  global video
  video = cv2.VideoCapture(file_path)
  parameter_setup_window.set_video(video)
  parameter_setup_window.show()

def handle_start_analyze_button_click(params):
  global settings
  settings["start_time_ms"] = params["start_time_ms"]
  settings["end_time_ms"] = params["end_time_ms"]
  settings["analysis_interval"] = params["analysis_interval"]
  parameter_setup_window.hide()
  global step
  step = 'processing'
  global video
  processing_window.start_processing(video, settings["start_time_ms"], settings["end_time_ms"], settings["analysis_interval"])
  processing_window.show()

def handle_processing_complete():
  global result
  result = processing_window.get_result()
  processing_window.hide()
  global step
  step = 'analysis_result'
  global video
  analysis_result_window.set_video(video, settings["start_time_ms"], settings["end_time_ms"])
  analysis_result_window.set_analysis_result(result)
  analysis_result_window.show()

def main():
  init()
  event_loop()

if __name__ == "__main__":
  main()
