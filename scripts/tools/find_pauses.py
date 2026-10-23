"""Suggest the "keep" segments: everything you say, minus the dead air.

    python3 scripts/tools/find_pauses.py            # print the suggestion
    python3 scripts/tools/find_pauses.py --write    # write it into project.json

It listens to the voice band (250-3500 Hz), so room noise and traffic count less.
Stumbles and repeated words still need you (or Claude) to remove them by hand:
read work/raw_words.json, find the bad take, and split that segment around it.
"""
import argparse, json, numpy as np
from scipy.io import wavfile
from scipy.signal import butter, sosfilt
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common import load, wpath

ap = argparse.ArgumentParser()
ap.add_argument('--min-gap', type=float, default=0.30, help='silences longer than this (s) are cut')
ap.add_argument('--pad', type=float, default=0.08, help='breathing room kept around speech (s)')
ap.add_argument('--keep-gap', type=float, default=0.12, help='silence left in place of each cut pause (s)')
ap.add_argument('--above', type=float, default=14.0, help='speech = this many dB above the noise floor')
ap.add_argument('--write', action='store_true')
a = ap.parse_args()

cfg = load()
sr, x = wavfile.read(wpath(cfg, 'raw48.wav'))
x = x.astype(np.float32) / (32768 if x.dtype == np.int16 else 1)
v = sosfilt(butter(4, [250, 3500], btype='band', fs=sr, output='sos'), x)
hop = int(sr * 0.01); n = len(v) // hop
db = 20 * np.log10(np.sqrt(np.mean(v[:n * hop].reshape(n, hop) ** 2, axis=1)) + 1e-9)
floor = np.percentile(db, 10)
speech = db > floor + a.above
# close tiny holes (consonants, short breaths)
k = int(a.min_gap / 0.01)
idx = np.where(speech)[0]
segs = []
if len(idx):
    s0 = p = idx[0]
    for i in idx[1:]:
        if i - p > k:
            segs.append((s0, p)); s0 = i
        p = i
    segs.append((s0, p))
keep = []
for s0, s1 in segs:
    a0 = max(0, s0 * 0.01 - a.pad); a1 = min(n * 0.01, (s1 + 1) * 0.01 + a.pad)
    if keep and a0 - keep[-1][1] < a.keep_gap:
        keep[-1][1] = a1
    else:
        keep.append([round(a0, 2), round(a1, 2)])
total = sum(b - a for a, b in keep)
print(f'noise floor {floor:.1f} dB | {len(keep)} segments | {total:.1f}s kept of {n * 0.01:.1f}s')
print(json.dumps(keep))
if a.write:
    raw = json.load(open(cfg['_path']))
    raw['keep'] = keep
    json.dump(raw, open(cfg['_path'], 'w'), indent=2)
    print('written to', cfg['_path'])
