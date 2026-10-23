"""Print your transcript as W lines to paste into scripts/04_timeline.py.

    node scripts/01_transcribe.mjs work/cut16.wav work/cut_words.json
    python3 scripts/tools/words_skeleton.py

Fix any misheard word by hand, then mark accent words with 'em' and bleeped ones with 'x'.
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common import load, wpath

cfg = load()
words = json.load(open(wpath(cfg, 'cut_words.json')))
line = []
print('W = [')
for k, w in enumerate(words):
    style = 'em' if len(w['w'].strip('.,?!')) >= 8 else ''
    line.append(f"({w['w']!r}, {w['s']:.2f}, {w['e']:.2f}, {style!r})")
    if w['w'].endswith(('.', '?', '!')) or len(line) == 4:
        print('    ' + ', '.join(line) + ','); line = []
if line:
    print('    ' + ', '.join(line) + ',')
print(']')
