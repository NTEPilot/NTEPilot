from pathlib import Path
import json

from utils.logger import logger

BASE_DIR = Path(__file__).parent
IGNORE_DIR = ['__pycache__']

class TemplateFile:
    def __init__(self, genre_name):
        self.content = 'from template.load_template import LoadTemplate\n'
        self.genre_name = genre_name

    def append(self, filename, rect=None):
        template_name = filename.split('.')[0]
        if rect is not None:
            rect = tuple(rect)
            self.content += f'\n{template_name} = LoadTemplate(\"./template/{self.genre_name}/assets/{filename}\", rect={rect})'
            logger.info(f'Template {template_name} with rect={rect} loaded')
        else:
            self.content += f'\n{template_name} = LoadTemplate(\"./template/{self.genre_name}/assets/{filename}\")'
            logger.info(f'Template {template_name} loaded')

    def write(self):
        with open(BASE_DIR / f'{self.genre_name}/__init__.py', 'w') as f:
            f.write(self.content)
            logger.info(f'File {self.genre_name}/__init__.py written')


def update(path):
    genre_name = path.name
    logger.hr(f'Update {genre_name}')
    template_file = TemplateFile(genre_name)

    rect = {}
    if (path / 'rect.json').exists():
        with open(path / 'rect.json', 'r') as f:
            rect = json.load(f)

    for item in (path / 'assets').iterdir():
        template_file.append(item.name, rect=rect.get(item.name, None))
    
    template_file.write()

def main():
    for item in BASE_DIR.iterdir():
        if not item.is_dir() or item.name in IGNORE_DIR:
            continue
        update(item)

if __name__ == '__main__':
    main()