from utils.logger import logger

class Fish:
    def __init__(self, device):
        self.device = device
    
    def run(self):
        logger.hr('FISH', level=1)