import re

from pathlib import Path

# 获取项目根目录
ROOT_DIR = Path(__file__).parent.parent
BOOK_TRANSLATION_DIR = ROOT_DIR / 'book_translation'

def search(s):
    match_list=re.match(r'^#+',s)
    if match_list:
        return len(match_list.group())
    else:
        return 0

def process(line):
    layer = search(line)
    if layer != 0:
        while layer < len(cur_loc) + 1:
            cur_loc.pop()
        cur_loc.append(line.replace('#', '').strip().replace('/', '_').replace('\\', '_'))
        folder_path = BOOK_TRANSLATION_DIR / '/'.join(cur_loc)
        folder_path.mkdir(parents=True, exist_ok=True)
    else:
        file_path = BOOK_TRANSLATION_DIR / '/'.join(cur_loc) / 'content.txt'
        with open(file_path, 'a', encoding='utf-8') as file:
            file.write(line + '\n')

input_file_path = BOOK_TRANSLATION_DIR / 'Real Analysis(Stein)_3_translated.md'
with open(input_file_path, mode='r', encoding='utf-8') as f:
    cur_loc = []
    for line in f:
        process(line.strip())
