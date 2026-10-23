"""Step 5 - draw the graphics: renders overlay/overlay.html to transparent PNG layers.

    python3 scripts/05_render_layers.py back      # worlds + big words BEHIND you
    python3 scripts/05_render_layers.py front     # captions, cards, stickers IN FRONT of you
    python3 scripts/05_render_layers.py front 0 30 60   # only some frames (quick check)

in : overlay/overlay.html + overlay/timeline.js (step 4), work/plan.json
out: work/layers/back_XXXXX.png, work/layers/front_XXXXX.png  (frames with nothing are skipped)
Needs Playwright's Chromium:  python3 -m playwright install chromium
"""
import sys, os, json, time
from playwright.sync_api import sync_playwright
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import load, wpath, ROOT

cfg = load()
FPS = cfg.get('fps', 30)
N = json.load(open(wpath(cfg, 'plan.json')))['NFRAMES']
layer = sys.argv[1] if len(sys.argv) > 1 else 'front'
outdir = os.environ.get('OUT', wpath(cfg, 'layers'))
frames = [int(x) for x in sys.argv[2:]] or list(range(N))
os.makedirs(outdir, exist_ok=True)
page_url = 'file://' + os.path.join(ROOT, 'overlay', 'overlay.html') + f'?layer={layer}'
with sync_playwright() as p:
    b = p.chromium.launch(args=['--font-render-hinting=none', '--disable-lcd-text', '--allow-file-access-from-files'])
    pg = b.new_page(viewport={'width': 1080, 'height': 1920}, device_scale_factor=1)
    errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.on('console', lambda m: errs.append('console: ' + m.text) if m.type == 'error' else None)
    pg.goto(page_url)
    pg.evaluate('window.ready'); pg.wait_for_timeout(400)
    if errs: print('PAGE ERRORS', errs[:5], flush=True)
    n = 0; t0 = time.time()
    for k, i in enumerate(frames):
        out = os.path.join(outdir, f'{layer}_{i:05d}.png')
        if not pg.evaluate(f'renderAt({i / FPS:.5f})'):
            if os.path.exists(out): os.remove(out)
            continue
        pg.screenshot(path=out, omit_background=True); n += 1
        if k % 100 == 0: print(f'{layer} {k}/{len(frames)} {time.time() - t0:.0f}s', flush=True)
    if errs: print('PAGE ERRORS', errs[:5], flush=True)
    b.close()
print('done', layer, n, 'frames ->', outdir)
