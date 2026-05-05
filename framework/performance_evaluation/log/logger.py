import datetime

class Singleton:
  _instance = None

  def __new__(cls):
    if cls._instance is None:
      cls._instance = super().__new__(cls)
    return cls._instance

class Logger(Singleton):
  _logs = {}
  _count = 0
  
  def start(self, func_name, memo=None):
    log_id = self._count
    self._logs[log_id] = {
      'func_name': func_name,
      'start': {
        'time': datetime.datetime.now(),
        'memo': memo,
      },
      'stop': {
        'time': None,
        'memo': None,
      },
    }
    self._count += 1
    return log_id

  def stop(self, log_id, memo=None):
    if log_id in self._logs:
      log = self._logs[log_id]
      log['stop']['time'] = datetime.datetime.now()
      if memo:
        log['stop']['memo'] = memo

  def output(self):
    text = 'id,func_name,start,stop,duration,memo(start),memo(stop)\n'
    for log_id, log in self._logs.items():
      if log['stop']['time'] is not None:
        duration = log['stop']['time'] - log['start']['time']
        text += f"{log_id},{log['func_name']},{log['start']['time']},{log['stop']['time']},{duration},{log['start']['memo']},{log['stop']['memo']}\n"
    return text

  def print(self):
    text = 'id, func_name, start, stop, duration, memo(start), memo(stop)\n'
    for log_id, log in self._logs.items():
      if log['stop']['time'] is not None:
        duration = log['stop']['time'] - log['start']['time']
        print(f"Task {log_id}: {log['func_name']}")
        print(f"  Start: {log['start']['time']} {log['start']['memo']}")
        print(f"  Stop: {log['stop']['time']} {log['stop']['memo']}")
        print(f"  Duration: {duration}")
    return text

def log(func):
  def wrapper(*args, **kwargs):
    id = Logger().start(func.__name__)
    result = func(*args, **kwargs)
    Logger().stop(id)
    return result
  return wrapper