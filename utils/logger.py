import logging
import os
from datetime import datetime
from rich.logging import RichHandler
from rich.console import Console
from rich.rule import Rule

console = Console()


class CustomLogger(logging.Logger):
    def rule(self, title="", *, characters="─", style="rule.line", end="\n", align="center"):
        rule = Rule(title=title, characters=characters,
                    style=style, end=end, align=align)
        print(rule)

    def hr(self, title, level=3):
        title = str(title).upper()
        if level == 1:
            self.rule(title, characters='═')
            self.info(title)
        if level == 2:
            self.rule(title, characters='─')
            self.info(title)
        if level == 3:
            self.info(f"[bold]<<< {title} >>>[/bold]", extra={"markup": True})
        if level == 0:
            self.rule(characters='═')
            self.rule(title, characters=' ')
            self.rule(characters='═')

    def attr(self, name, text):
        self.info(f"[{name}] {text}")


logging.setLoggerClass(CustomLogger)


def setup_logger(name="NTEPilot", level=logging.DEBUG, log_dir="logs") -> CustomLogger:
    logger = logging.getLogger(name)
    logger.setLevel(level)

    if not logger.handlers:
        rich_handler = RichHandler(
            console=console,
            show_time=True,
            show_path=True,
            markup=True,
            rich_tracebacks=True,
            tracebacks_show_locals=True
        )
        rich_formatter = logging.Formatter("%(message)s")
        rich_handler.setFormatter(rich_formatter)
        logger.addHandler(rich_handler)

        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
            
        log_file = os.path.join(log_dir, f"{name}_{datetime.now().strftime('%Y-%m-%d')}.log")
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        
        file_formatter = logging.Formatter(
            "[%(asctime)s] [%(levelname)s] [%(name)s] [%(filename)s:%(lineno)d] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    return logger

logger = setup_logger()