import time

class Timer:
    def __init__(self, duration=60):
        self.duration = duration
        self.reset()

    def reset(self):
        self.start_time = time.time()
        return self

    def force_reached(self):
        self.start_time -= self.duration
        return self

    @property
    def reached(self):
        return time.time() - self.start_time > self.duration

    def wait(self):
        diff = self.duration - (time.time() - self.start_time)
        if diff > 0:
            time.sleep(diff)