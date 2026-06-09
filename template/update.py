from pathlib import Path
import json

from utils.exceptions import ScriptError
from utils.logger import logger

BASE_DIR = Path(__file__).parent
IGNORE_DIR = ['__pycache__']

class TemplateFile:
    def __init__(self, genre_name):
        self.content = 'from template.load_template import load_template\n'
        self.genre_name = genre_name

    def append(self, filename, override=None):
        template_name = filename.split('.')[0]
        override_str = ''
        if override is not None:
            for key, value in override.items():
                if key == 'rect':
                    value = tuple(value)
                elif key == 'method':
                    value = f'\"{value}\"'
                else:
                    raise ScriptError(f'Invalid template key: {key}')

                override_str += f', {key}={value}'

            self.content += f'\n{template_name} = load_template(\"./template/{self.genre_name}/assets/{filename}\"{override_str})'
            logger.info(f'Template {template_name} with ({override_str[2:]}) loaded')
        else:
            self.content += f'\n{template_name} = load_template(\"./template/{self.genre_name}/assets/{filename}\")'
            logger.info(f'Template {template_name} loaded')

    def write(self):
        with open(BASE_DIR / f'{self.genre_name}/__init__.py', 'w') as f:
            f.write(self.content)
            logger.info(f'File {self.genre_name}/__init__.py written')


def update(path):
    genre_name = path.name
    logger.hr(f'Update {genre_name}')
    template_file = TemplateFile(genre_name)

    override = {}
    if (path / 'override.json').exists():
        with open(path / 'override.json', 'r') as f:
            override = json.load(f)

    for item in (path / 'assets').iterdir():
        template_file.append(item.name, override=override.get(item.name, None))
    
    template_file.write()

def main():
    for item in BASE_DIR.iterdir():
        if not item.is_dir() or item.name in IGNORE_DIR:
            continue
        update(item)

if __name__ == '__main__':
    main()