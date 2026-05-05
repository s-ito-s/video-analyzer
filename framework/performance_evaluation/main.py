import tkinter.filedialog
import subprocess

serverProcess = subprocess.Popen(['uv', 'run', 'python', './framework/performance_evaluation/server.py'], encoding='UTF-8', stdin=subprocess.PIPE, stdout=subprocess.PIPE)
print('server.py started')

file_path = tkinter.filedialog.askopenfilename()
clientProcess = subprocess.Popen(['uv', 'run', 'python', './framework/performance_evaluation/client.py', '--in-filename', file_path], encoding='UTF-8', stdin=subprocess.PIPE, stdout=subprocess.PIPE)
print('client.py started')

try:
  serverProcess.communicate(timeout=20)
except:
  print('process timeout. killing processes...')
  serverProcess.kill()
  clientProcess.kill()

print('finished.')