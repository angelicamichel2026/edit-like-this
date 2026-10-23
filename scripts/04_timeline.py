"""Step 4 - YOUR REEL: words, captions, scenes and camera moves.  <-- the creative step

    python3 scripts/04_timeline.py

in : project.json, work/fmap.json (from step 2)
out: overlay/timeline.js  (read by overlay/overlay.html to draw the graphics)
     work/plan.json       (read by step 7: zoom, shake, flashes, glitches, split screen per frame)

Everything below is written for MY reel ("Go crazy on editing this video...").
For your video:
  1. W     = your words with their times IN THE CUT (seconds). Get them with
             node scripts/01_transcribe.mjs work/cut16.wav work/cut_words.json
             python3 scripts/tools/words_skeleton.py      (prints W lines to paste here)
             style: ''  normal caption word   'em' serif accent word (lime)
                    'x' bleeped word (#@%!)    'hide' not captioned (used by the prompt intro)
  2. BREAKS = the first word of each caption line.
  3. S     = when each scene starts/ends. Scenes live in overlay/overlay.html.
  4. TL    = when each card, sticker, stamp... pops (most are tied to a word with ws('word')).
  5. FACE  = roughly where your face is in the raw frame (x, y in pixels) - zooms aim there.
Or hand this file + your transcript to Claude and ask it to rewrite it for your script.
"""
import json, math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import load, wpath, ROOT

CFG = load()
FPS = CFG.get('fps', 30)
_fmap = wpath(CFG, 'fmap.json')
CUT_FRAMES = len(json.load(open(_fmap))) if os.path.exists(_fmap) else 754   # frames in the cut
END_FRAMES = 90                                                               # 3 s end card
NFRAMES = CUT_FRAMES + END_FRAMES
DUR = NFRAMES / FPS
T_END = CUT_FRAMES / FPS            # 25.133

# ---------------------------------------------------------------- words (output seconds)
# (display text, start, end, style)   style: '' normal, 'em' serif-italic accent, 'x' grawlix, 'hide' not captioned
W = [
    ('Go', 0.10, 0.30, 'hide'), ('crazy', 0.31, 1.02, 'hide'), ('on', 1.06, 1.28, 'hide'), ('editing', 1.28, 1.54, 'hide'),
    ('this', 1.54, 1.80, 'hide'), ('video.', 1.80, 2.12, 'hide'),
    ("Let's", 2.24, 2.38, ''), ('show', 2.38, 2.56, ''), ('them', 2.56, 2.78, ''),
    ('how', 2.78, 3.00, ''), ('you', 3.00, 3.50, ''), ('can', 3.50, 4.08, ''), ('just', 4.08, 4.28, ''), ('get', 4.28, 4.52, ''),
    ('all', 4.78, 5.04, ''), ('the', 5.04, 5.16, ''), ('videos', 5.16, 5.46, 'em'),
    ('and', 5.46, 5.62, ''), ('social', 5.62, 5.78, 'em'), ('media,', 5.78, 6.04, 'em'),
    ('put', 6.04, 6.22, ''), ('it', 6.22, 6.32, ''), ('right', 6.32, 6.44, ''), ('here.', 6.44, 6.72, 'em'),
    ("Let's", 6.91, 7.30, ''), ('#@%!', 7.37, 7.96, 'x'),
    ('show', 8.28, 8.46, ''), ('them', 8.46, 8.62, ''), ('how', 8.62, 8.80, ''), ('we', 8.80, 8.94, ''), ('can', 8.94, 9.04, ''),
    ('create', 9.04, 9.22, ''), ('animations,', 9.22, 9.72, 'em'),
    ('and', 9.72, 9.96, ''), ('then', 9.96, 10.08, ''), ('DM', 10.08, 10.42, 'em'), ('them.', 10.42, 10.78, ''),
    ('They', 10.82, 11.04, ''), ('comment', 11.04, 11.16, ''), ('the', 11.16, 11.30, ''), ('word', 11.30, 11.44, ''),
    ('EDIT,', 11.44, 11.76, 'em'),
    ('and', 11.76, 12.08, ''), ('show', 12.18, 12.32, ''), ('them', 12.32, 12.46, ''),
    ('the', 12.46, 12.58, ''), ('same', 12.58, 12.80, ''), ('code', 12.80, 13.06, 'em'),
    ("I'm", 13.20, 13.32, ''), ('using', 13.32, 13.48, ''), ('right', 13.48, 13.70, 'em'), ('now,', 13.70, 13.98, 'em'),
    ('for', 13.98, 14.34, ''), ('them', 14.34, 14.64, ''), ('not', 14.64, 14.90, ''), ('to', 14.90, 15.12, ''), ('pay', 15.12, 15.50, ''),
    ('any', 15.53, 15.99, ''), ('editor', 15.99, 16.41, 'em'),
    ('anymore,', 16.41, 16.85, ''),
    ('or', 16.85, 17.15, ''), ('edit', 17.31, 17.55, 'em'), ('themselves.', 17.55, 18.17, 'em'),
    ('Okay,', 18.41, 18.70, ''),
    ("let's", 19.26, 19.40, ''), ('#@%!', 19.41, 19.75, 'x'), ('GO.', 19.76, 20.03, 'em'),
    ('What', 20.08, 20.20, ''), ('are', 20.20, 20.32, ''), ('you', 20.32, 20.46, ''), ('waiting', 20.46, 20.68, 'em'), ('for?', 20.68, 21.04, ''),
    ('Start', 21.34, 21.44, ''), ('using', 21.44, 21.68, ''),
    ('artificial', 21.68, 21.96, 'em'), ('intelligence.', 21.96, 22.66, 'em'),
    ('Comment', 22.84, 22.94, ''), ('the', 22.94, 23.06, ''), ('word', 23.06, 23.30, ''),
    ('EDIT', 23.30, 23.54, 'em'),
    ('and', 23.54, 23.80, ''), ("I'll", 23.80, 23.86, ''), ('send', 23.86, 24.00, ''), ('it', 24.00, 24.10, ''),
    ('over', 24.10, 24.20, ''), ('to', 24.20, 24.40, ''), ('you.', 24.40, 24.58, 'em'),
    ("Let's", 24.70, 24.84, ''), ('go.', 24.84, 25.05, 'em'),
]
WORDS = [{'w': w, 's': s, 'e': e, 'st': st} for w, s, e, st in W]
def wi(text, after=0.0):
    for i, x in enumerate(WORDS):
        if x['s'] >= after - 1e-6 and x['w'].lower().strip('.,?!') == text.lower().strip('.,?!'):
            return i
    raise KeyError(text)
def ws(text, after=0.0): return WORDS[wi(text, after)]['s']

# phrases: [first word, last word] by index + caption position
BREAKS = ["Let's", 'how', 'all', 'and', 'put', "Let's", 'show', 'create', 'and', 'They', 'EDIT,', 'and', 'the', "I'm", 'for', 'any',
          'anymore,', 'or', 'Okay,', "let's", 'What', 'Start', 'artificial', 'Comment', 'EDIT', 'and', 'over', "Let's"]
starts = []
t = 2.0
for b in BREAKS:
    i = wi(b, t); starts.append(i); t = WORDS[i]['s'] + 0.01
PHR = []
for k, i0 in enumerate(starts):
    i1 = (starts[k + 1] - 1) if k + 1 < len(starts) else len(WORDS) - 1
    s = WORDS[i0]['s']
    e = WORDS[starts[k + 1]]['s'] if k + 1 < len(starts) else T_END
    e = min(e, WORDS[i1]['e'] + 0.55)
    PHR.append({'a': i0, 'b': i1, 's': round(s, 3), 'e': round(e, 3)})

# ---------------------------------------------------------------- scenes (output seconds)
S = {
    'prompt': (0.0, 2.24),
    'wall': (2.24, 6.87),
    'bleep': (6.87, 8.27),
    'toon': (8.27, 10.82),
    'cmts': (10.82, 11.96),
    'code': (11.96, 14.34),
    'invoice': (14.34, 17.27),
    'diy': (17.27, 18.37),
    'tense': (18.37, 19.76),
    'drop': (19.76, 20.08),
    'clock': (20.08, 21.30),
    'ai': (21.30, 22.80),
    'cta': (22.80, T_END),
    'end': (T_END, DUR + 1),
}
R = lambda x: round(x, 3)
WIN0 = {'x': 60, 'y': 236, 'w': 960, 'h': 1060, 'r': 40}       # prompt-beat video window
SPLIT_Y = 940

WALL_DIR = os.path.join(ROOT, 'overlay', 'img', 'wall')
WALL = sorted(f for f in os.listdir(WALL_DIR) if f.lower().endswith(('.jpg', '.jpeg', '.png'))) if os.path.isdir(WALL_DIR) else []
TL = {
    'brand': CFG.get('brand', {}), 'wallImages': WALL,
    'dur': DUR, 'fps': FPS, 'tEnd': T_END, 'S': S, 'win0': WIN0, 'splitY': SPLIT_Y,
    'prompt': {'typeA': 0.10, 'typeB': 2.12, 'cursorA': 1.62, 'cursorB': 2.00, 'click': 2.04, 'expandA': 2.08, 'expandB': 2.24},
    'wall': {'in': 2.24, 'videos': ws('videos'), 'social': ws('social'), 'put': ws('put'), 'here': ws('here.')},
    'bleep': {'balloonIn': ws('#@%!') - 0.02, 'balloonOut': 8.18},
    'toon': {'in': 8.27, 'create': ws('create'), 'anim': ws('animations,'), 'dm': ws('and', 9.6), 'dmMsg': ws('DM'), 'out': 10.82},
    'cmts': {'in': 10.82, 'edit': ws('EDIT,'), 'out': 11.96},
    'code': {'in': 11.96, 'code': ws('code'), 'now': ws('right', 13.4), 'out': 14.34},
    'invoice': {'in': ws('not', 14.5), 'editor': ws('editor'), 'stamp': ws('anymore,'), 'out': ws('or', 16.8)},
    'diy': {'in': 17.27, 'edit': ws('edit', 17.2), 'out': 18.37},
    'tense': {'in': 18.37, 'okay': ws('Okay,'), 'lets': ws("let's", 19.0), 'bleep': 19.41, 'drop': 19.76},
    'clock': {'in': 20.08, 'q1': ws('waiting'), 'q2': ws('for?', 20.5), 'out': 21.30},
    'ai': {'in': 21.30, 'click': ws('using', 21.3) - 0.02, 'big': ws('artificial'), 'out': 22.80},
    'cta': {'in': 22.80, 'typeA': ws('EDIT', 23.0) - 0.04, 'typeB': ws('EDIT', 23.0) + 0.14, 'post': ws('and', 23.4),
            'dm': ws('send', 23.5) - 0.06, 'lets': ws("Let's", 24.6)},
    'end': {'in': T_END, 'stamp': T_END + 0.22, 'bar': T_END + 0.62, 'typeA': T_END + 0.85, 'typeB': T_END + 1.15,
            'post': T_END + 1.3, 'line': T_END + 1.45, 'stats': T_END + 1.75},
}

# ---------------------------------------------------------------- edit counter events
EV = set()
for w in WORDS:
    if w['st'] != 'hide': EV.add(round(w['s'], 2))
for k, v in TL.items():
    if isinstance(v, dict):
        for kk, x in v.items():
            if isinstance(x, (int, float)) and 2.2 <= x <= T_END: EV.add(round(x, 2))
for a, b in S.values():
    if 2.2 <= a <= T_END: EV.add(round(a, 2))
EV = sorted(e for e in EV if e <= T_END)
# extra micro-edits: the wall tiles, doodles, comments, code lines etc. each count
EXTRA = [2.3 + 0.12 * k for k in range(12)] + [8.3 + 0.07 * k for k in range(14)] + [10.86 + 0.12 * k for k in range(6)] + \
        [12.0 + 0.16 * k for k in range(13)] + [19.76 + 0.05 * k for k in range(10)] + [21.70 + 0.08 * k for k in range(8)]
EV = sorted(set(EV + [round(x, 2) for x in EXTRA]))
TL['events'] = EV
TL['nEdits'] = len(EV)

# ---------------------------------------------------------------- compositor params per frame
def ease_io(x): x = min(1, max(0, x)); return x * x * (3 - 2 * x)
def ease_out(x): x = min(1, max(0, x)); return 1 - (1 - x) ** 3
def ease_in(x): x = min(1, max(0, x)); return x ** 3
def lerp(a, b, p): return a + (b - a) * p

FACE = (620, 1110)          # rough face centre in source px (cut footage)

def zoom_at(t):
    """camera zoom for full-frame scenes (anchor = FACE)."""
    if t < S['wall'][1]:
        return 1.0 + 0.06 * ease_io((t - 2.24) / 4.6)
    if t < S['bleep'][1]:
        b = TL['bleep']['balloonIn']
        if t < b: return 1.10
        return 1.10 + 0.12 * ease_out((t - b) / 0.12) - 0.04 * ease_io((t - b - 0.2) / 0.6)
    if t < S['toon'][1]:
        return 1.0 + 0.10 * (1 - ease_out((t - 8.27) / 0.35))
    if t < S['cmts'][1]:
        return 1.08 + 0.04 * ease_io((t - 10.82) / 1.1)
    if t < S['invoice'][1]:
        st = TL['invoice']['stamp']
        z = 1.0 + 0.03 * ease_io((t - 14.34) / 2)
        if t >= st: z += 0.10 * (1 - ease_out((t - st) / 0.5))
        return z
    if t < S['diy'][1]:
        return 1.04 + 0.08 * (1 - ease_out((t - 17.27) / 0.3))
    if t < S['tense'][1]:
        return 1.0 + 0.14 * ease_io((t - 18.37) / 1.39)
    if t < S['drop'][1] + 0.6:
        return 1.04 + 0.20 * (1 - ease_out((t - 19.76) / 0.45))
    if t < S['clock'][1]:
        return 1.0 + 0.02 * ease_io((t - 20.08) / 1.2)
    if t < S['ai'][1]:
        z = 1.05
        if t >= TL['ai']['big']: z += 0.08 * (1 - ease_out((t - TL['ai']['big']) / 0.4))
        return z
    if t < T_END:
        lt = TL['cta']['lets']
        z = 1.0 + 0.03 * ease_io((t - 22.8) / 1.8)
        if t >= lt: z += 0.12 * ease_out((t - lt) / 0.2)
        return z
    return 1.12

def frame_params(i):
    t = i / FPS
    P = {'t': round(t, 4), 'src': min(i, CUT_FRAMES - 1), 'mode': 'full', 'z': zoom_at(t), 'anchor': FACE, 'grade': 'base',
         'sticker': 0.0, 'shake': 0.0, 'flash': 0.0, 'flashColor': [255, 255, 255], 'glitch': 0.0, 'whip': 0.0, 'whipDir': 'x',
         'person': True}
    # --- prompt beat: raw video inside a window that explodes to full frame
    if t < S['prompt'][1]:
        P['mode'] = 'win'; P['grade'] = 'raw'
        p = ease_in((t - TL['prompt']['expandA']) / (TL['prompt']['expandB'] - TL['prompt']['expandA']))
        x = lerp(WIN0['x'], 0, p); y = lerp(WIN0['y'], 0, p); w = lerp(WIN0['w'], 1080, p); h = lerp(WIN0['h'], 1920, p)
        r = lerp(WIN0['r'], 0, p)
        s0 = WIN0['w'] / 1080.0
        # map source face centre to window centre
        cy0 = WIN0['y'] + WIN0['h'] / 2 + 40
        s = lerp(s0, 1.0, p)
        tx = lerp(WIN0['x'], 0, p); ty = lerp(cy0 - s0 * FACE[1], 0, p)
        P['win'] = [x, y, w, h, r]; P['map'] = [s, tx, ty]
        if t >= TL['prompt']['expandA']: P['whip'] = 0.5 * p; P['whipDir'] = 'zoom'
    # --- split screen with code on top
    elif S['code'][0] <= t < S['code'][1] + 0.24:
        P['mode'] = 'win'
        s = 1.18; tx = 540 - s * FACE[0]; ty = (SPLIT_Y + 140) - s * 780
        if t < S['code'][1]:
            P['win'] = [0, SPLIT_Y, 1080, 1920 - SPLIT_Y, 0]; P['map'] = [s, tx, ty]
        else:   # split closes: window grows to full frame
            p = ease_io((t - S['code'][1]) / 0.24)
            z = zoom_at(t)
            P['win'] = [0, lerp(SPLIT_Y, 0, p), 1080, lerp(1920 - SPLIT_Y, 1920, p), 0]
            P['map'] = [lerp(s, z, p), lerp(tx, FACE[0] * (1 - z), p), lerp(ty, FACE[1] * (1 - z), p)]
    # grades
    if S['tense'][0] <= t < S['tense'][1]:
        P['grade'] = 'tense'
    # sticker outline on the person in cartoon worlds
    if S['toon'][0] <= t < S['toon'][1] or S['diy'][0] <= t < S['diy'][1] or S['clock'][0] <= t < S['clock'][1]:
        P['sticker'] = 1.0
    # flashes
    def flash(at, n=3, amt=0.9, col=(255, 255, 255)):
        d = t - at
        if 0 <= d < n / FPS:
            P['flash'] = max(P['flash'], amt * (1 - d * FPS / n)); P['flashColor'] = list(col)
    flash(2.24, 4, 1.0, (232, 255, 120))
    flash(8.27, 3, 0.85)
    flash(17.27, 3, 0.7, (216, 255, 62))
    flash(19.76, 5, 1.0)
    flash(21.68, 3, 0.6, (216, 255, 62))
    flash(TL['cta']['typeA'] + 0.2, 2, 0.35, (216, 255, 62))
    # shakes
    def shake(at, dur, amp):
        d = t - at
        if 0 <= d < dur: P['shake'] = max(P['shake'], amp * (1 - d / dur) ** 1.5)
    shake(TL['bleep']['balloonIn'], 0.45, 16)
    shake(TL['invoice']['stamp'], 0.4, 22)
    shake(19.41, 0.3, 10)
    shake(19.76, 0.9, 34)
    shake(TL['ai']['big'], 0.35, 14)
    # glitches
    def glitch(at, n=5):
        d = t - at
        if -1 / FPS <= d < n / FPS: P['glitch'] = max(P['glitch'], 1 - max(0, d) * FPS / n)
    glitch(11.96 - 0.07, 5)
    glitch(21.30 - 0.05, 4)
    glitch(19.41, 3)
    # whips
    def whip(at, dirn, n=5):
        d = t - at
        if -n / FPS / 2 <= d < n / FPS / 2:
            P['whip'] = 1 - abs(d) / (n / FPS / 2); P['whipDir'] = dirn
            P['whipSign'] = 1 if d < 0 else -1
    whip(6.87, 'x'); whip(10.82, 'y'); whip(22.80, 'y'); whip(14.34, 'none', 1)
    # zoom-blur 'suck in' while the stickers fly into the timeline (also hides the hand smear)
    d = t - 6.17
    if abs(d) < 0.2:
        P['whip'] = max(P['whip'], 0.85 * (1 - abs(d) / 0.2)); P['whipDir'] = 'zoom'
    # the end card is opaque: video frozen underneath
    if t >= T_END:
        P['src'] = CUT_FRAMES - 1
    return P

if __name__ == '__main__':
    open(os.path.join(ROOT, 'overlay', 'timeline.js'), 'w').write(
        'window.TL=' + json.dumps(TL) + ';\nwindow.WORDS=' + json.dumps(WORDS) + ';\nwindow.PHR=' + json.dumps(PHR) + ';\n')
    plan = [frame_params(i) for i in range(NFRAMES)]
    json.dump({'NFRAMES': NFRAMES, 'CUT_FRAMES': CUT_FRAMES, 'frames': plan}, open(wpath(CFG, 'plan.json'), 'w'))
    for p in PHR:
        print(f"{p['s']:6.2f}-{p['e']:6.2f}  " + ' '.join(WORDS[k]['w'] for k in range(p['a'], p['b'] + 1)))
    print('events', len(EV), 'frames', NFRAMES, 'dur', round(DUR, 3))
