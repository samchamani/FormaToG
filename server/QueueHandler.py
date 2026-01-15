import logging
import queue


class QueueHandler(logging.Handler):
    def __init__(self, log_queue: queue.Queue, level=0):
        super().__init__(level)
        self.log_queue = log_queue

    def emit(self, record):
        formatted = self.format(record)
        message_start = formatted.find("{")
        self.log_queue.put(f"{formatted[message_start:]}\n")
