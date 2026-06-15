from NTEPilot.map.map import Map
from NTEPilot.bond.ocr import CharaOcr
from template.bond import *
from template.ui import INTERACT, CHAT, EXIT
from utils.logger import logger
from utils.image import xywh2xyxy


class Movie(Map, CharaOcr):
    def goto_movie(self):
        logger.hr('GOTO MOVIE')
        for attempt in range(3):
            logger.info(f'Attempt {attempt + 1}/3')
            self.teleport_to(44)
            self.device.sleep((2, 2.2))
            self.device.move_forward(2)
            self.device.move_right(3)
            self.device.move_backward_left(5)
            self.device.move(160, 2)
            self.device.move_backward_left(1.2)
            self.device.move_backward(10)
            self.device.screenshot()
            if self.appear(INTERACT):
                logger.info(f'Successfully reached')
                return

    def _get_name(self, pos):
        rect = (pos[0] - 189, pos[1] - 24, 120, 30)
        rect = xywh2xyxy(rect)
        return self.ocr(rect, model='cn')

    def _movie(self):
        while True:
            self.device.screenshot()
            charas = DATE_TELEPHONE.match_all(self.device.image)
            last_name = ''
            for chara in charas:
                name = self._get_name(chara)
                if name == self.chara:
                    self.device.click(chara)
                    self.wait_until_appear_then_click(INVITE_CONFIRM)
                    self.wait_until_appear(CHAT)
                    self.device.sleep((2, 2.2))
                    self.device.click(EXIT)
                    self.device.sleep((2, 2.2))
                    return
                last_name = name
            if self._last_name == last_name:
                logger.error(f'Cannot find {self.chara}')
                return
            self._last_name = last_name
            self.device.drag((1070, 620), (1070, 210))

    def run(self):
        logger.hr('MOVIE', level=1)

        self.chara = self.config['schedule.movie.character']

        self.goto_movie()
        self.device.click(INTERACT)
        self.wait_until_appear_then_click(MOVIE_CHAT)
        with self.device.temporary_screenshot_interval(0.5):
            while True:
                self.device.screenshot()
                if self.appear(DATE):
                    break
                self.device.click((640, 500))
        self._last_name = ''
        self._movie()