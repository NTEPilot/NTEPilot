from NTEPilot.ocr import Ocr
from utils.logger import logger

class CharaOcr(Ocr):
    def ocr(self, *args, **kwargs):
        result = super().ocr(*args, **kwargs)

        # 狗狗人是驱（
        if result == '驱':
            logger.info('Detected 驱, correcting to 翳')
            result = '翳'
        elif result == '得':
            logger.info('Detected 得, correcting to 浔')
            result = '浔'
        elif result == '小':
            logger.info('Detected 小, correcting to 小吱')
            result = '小吱'

        return result