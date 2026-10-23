"""Step 7 - put it all together: background world + you (cut out) + graphics + camera moves.

    python3 scripts/07_compose.py                       # the whole reel -> project.json "output"
    python3 scripts/07_compose.py preview 0 150 300     # a few frames as JPGs in work/preview (fast check)

Per frame: grade the video -> lay the BACK layer -> sticker outline (cartoon scenes) -> you, with
clean edges (the white-wall fringe is removed) -> FRONT layer -> whip / glitch / shake / flash.
in : work/cut.mp4, work/masks, work/layers, work/plan.json, work/mix.wav
"""
import sys, os, json, subprocess, math, numpy as np, cv2
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import load, wpath, rpath

CFG = load()
W, H, FPS = 1080, 1920, CFG.get('fps', 30)
PLAN = json.load(open(wpath(CFG, 'plan.json')))
FR, N, CUTN = PLAN['frames'], PLAN['NFRAMES'], PLAN['CUT_FRAMES']
FMAP = json.load(open(wpath(CFG, 'fmap.json')))
OV = os.environ.get('OV', wpath(CFG, 'layers'))
MASKS = wpath(CFG, 'masks')
INK = np.array([13, 23, 18], np.float32)
WHITE = np.array([255, 255, 255], np.float32)

# ---------------------------------------------------------------- grades (LUT per channel)
x = np.arange(256, dtype=np.float32) / 255
def curve(c, lift=0.0, gain=1.0, s=0.0, gamma=1.0):
    y = np.clip(x, 0, 1) ** gamma
    y = y + s * 0.035 * np.sin(2 * np.pi * (y - 0.5))      # gentle S-curve
    y = lift + y * (gain - lift)
    return (np.clip(y, 0, 1) * 255).astype(np.uint8)
LUTS = {
    'base': np.stack([curve(0, 0.0, 1.0, 0.55, 1.02), curve(1, 0.0, 0.985, 0.55, 1.03), curve(2, 0.0, 0.965, 0.5, 1.05)], 1),
    'raw': np.stack([curve(0, 0.04, 0.97, 0.0, 1.0)] * 3, 1),
    'tense': np.stack([curve(0, 0.0, 0.78, 0.9, 1.15), curve(1, 0.0, 0.76, 0.9, 1.15), curve(2, 0.0, 0.74, 0.9, 1.12)], 1),
}
SAT = {'base': 1.10, 'raw': 0.82, 'tense': 0.45}
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
VIG = np.clip(1 - 0.55 * (((xx - 540) / 760) ** 2 + ((yy - 1000) / 1250) ** 2), 0, 1)[..., None]

def grade(img, kind):
    lut = LUTS[kind]
    o = np.empty_like(img)
    for c in range(3):
        o[..., c] = cv2.LUT(img[..., c], lut[:, c])
    o = o.astype(np.float32)
    g = o.mean(axis=2, keepdims=True)
    o = g + (o - g) * SAT[kind]
    if kind == 'tense':
        o = o * (0.55 + 0.45 * VIG)
    return np.clip(o, 0, 255)

# ---------------------------------------------------------------- matte helpers
def load_alpha(src_idx):
    p = os.path.join(MASKS, f'm_{FMAP[src_idx]:05d}.png')
    if os.environ.get('WAIT') == '1':
        import time
        while not os.path.exists(p):
            time.sleep(2)
        time.sleep(0.05)
    if not os.path.exists(p):
        return None
    a = cv2.imread(p, cv2.IMREAD_UNCHANGED)
    a = a[..., 3] if a.ndim == 3 else a
    a = a.astype(np.float32) / 255
    a = np.clip((a - 0.06) / 0.88, 0, 1)
    return cv2.GaussianBlur(a, (0, 0), 0.9)

def decontaminate(img, a):
    """estimate the clean foreground colour at soft matte edges (removes the white-wall fringe)."""
    q = 4
    sm = cv2.resize(img, (W // q, H // q), interpolation=cv2.INTER_AREA)
    wa = cv2.resize(1 - a, (W // q, H // q), interpolation=cv2.INTER_AREA)
    wa = np.clip((wa - 0.5) * 2.2, 0, 1)            # only trust clear background pixels
    num = cv2.GaussianBlur(sm * wa[..., None], (0, 0), 9)
    den = cv2.GaussianBlur(wa, (0, 0), 9)[..., None] + 1e-4
    B = cv2.resize(num / den, (W, H), interpolation=cv2.INTER_LINEAR)
    am = np.maximum(a, 0.08)[..., None]
    F = (img - (1 - a[..., None]) * B) / am
    F = np.clip(F, 0, 255)
    hard = (a > 0.96)[..., None]
    return np.where(hard, img, F)

def warp(img, M, border=cv2.BORDER_REPLICATE, interp=cv2.INTER_LINEAR):
    return cv2.warpAffine(img, M, (W, H), flags=interp, borderMode=border)

def zoomM(z, ax, ay):
    return np.float32([[z, 0, ax - z * ax], [0, z, ay - z * ay]])

def rrect(x, y, w, h, r):
    """anti-aliased rounded-rect mask"""
    cx, cy = x + w / 2, y + h / 2
    dx = np.abs(xx - cx) - (w / 2 - r); dy = np.abs(yy - cy) - (h / 2 - r)
    d = np.sqrt(np.maximum(dx, 0) ** 2 + np.maximum(dy, 0) ** 2) + np.minimum(np.maximum(dx, dy), 0) - r
    return np.clip(0.5 - d, 0, 1)[..., None]

KER = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (27, 27))
def sticker(base, a):
    m = (a > 0.45).astype(np.uint8)
    d = cv2.dilate(m, KER).astype(np.float32)
    d = cv2.GaussianBlur(d, (0, 0), 1.0)[..., None]
    sh = np.zeros_like(d); sh[16:, 14:] = d[:-16, :-14]
    base = base * (1 - sh * 0.92) + INK * sh * 0.92
    return base * (1 - d) + WHITE * d

def load_png(kind, i):
    p = os.path.join(OV, f'{kind}_{i:05d}.png')
    if not os.path.exists(p):
        return None
    im = cv2.imread(p, cv2.IMREAD_UNCHANGED)
    if im.shape[2] == 4:
        return im[..., 2::-1].astype(np.float32), im[..., 3:4].astype(np.float32) / 255
    return im[..., ::-1].astype(np.float32), np.ones((H, W, 1), np.float32)

# ---------------------------------------------------------------- post FX
def whip_fx(img, amt, dirn, sign):
    if amt <= 0.02 or dirn == 'none':
        return img
    if dirn == 'zoom':
        acc = img.copy(); n = 4
        for k in range(1, n):
            z = 1 + 0.035 * k * amt
            acc += warp(img, zoomM(z, 540, 900))
        return acc / n
    L = int(10 + 150 * amt)
    k = (L, 1) if dirn == 'x' else (1, L)
    out = cv2.blur(img, k)
    off = sign * 140 * amt
    M = np.float32([[1, 0, off if dirn == 'x' else 0], [0, 1, off if dirn == 'y' else 0]])
    return warp(out, M, cv2.BORDER_REFLECT)

def glitch_fx(img, g, seed):
    if g <= 0.02:
        return img
    rs = np.random.RandomState(seed)
    out = img.copy()
    sh = int(28 * g)
    out[..., 0] = np.roll(img[..., 0], sh, axis=1)
    out[..., 2] = np.roll(img[..., 2], -sh, axis=1)
    for _ in range(int(4 + 6 * g)):
        y0 = rs.randint(0, H - 40); hh = rs.randint(18, 140); dx = int(rs.choice([-1, 1]) * rs.randint(40, 190) * g)
        out[y0:y0 + hh] = np.roll(out[y0:y0 + hh], dx, axis=1)
    if g > 0.5:
        for _ in range(3):
            y0 = rs.randint(0, H - 30); x0 = rs.randint(0, W - 300); hh = rs.randint(8, 26); ww = rs.randint(120, 420)
            out[y0:y0 + hh, x0:x0 + ww] = [216, 255, 62] if rs.rand() < .5 else [13, 23, 18]
    return out

def shake_fx(img, s, t):
    if s <= 0.3:
        return img
    dx = s * (math.sin(t * 71.0) * 0.6 + math.sin(t * 113.0 + 1.3) * 0.4)
    dy = s * (math.sin(t * 89.0 + 0.7) * 0.6 + math.sin(t * 131.0 + 2.1) * 0.4)
    rot = s * 0.035 * math.sin(t * 97.0)
    z = 1 + s / 420
    M = cv2.getRotationMatrix2D((540, 960), rot, z); M[0, 2] += dx; M[1, 2] += dy
    return warp(img, M.astype(np.float32), cv2.BORDER_REFLECT)

# ---------------------------------------------------------------- frame composite
def compose(i, src_rgb):
    P = FR[i]
    t = P['t']
    img = grade(src_rgb, P['grade'])
    back = load_png('back', i)
    if P['mode'] == 'win':
        canvas = back[0] if back is not None else np.tile(INK, (H, W, 1))
        if back is not None and back[1].min() < 0.999:
            canvas = np.tile(INK, (H, W, 1)) * (1 - back[1]) + back[0] * back[1]
        s, tx, ty = P['map']
        vid = warp(img, np.float32([[s, 0, tx], [0, s, ty]]))
        x, y, w, h, r = P['win']
        wm = rrect(x, y, w, h, max(r, 0.01))
        out = canvas * (1 - wm) + vid * wm
    else:
        z = P['z']; ax, ay = P['anchor']
        M = zoomM(z, ax, ay)
        img_t = warp(img, M) if abs(z - 1) > 1e-4 else img
        if back is None and P['sticker'] <= 0:
            out = img_t
        else:
            a = load_alpha(P['src'])
            if a is None:
                a = np.zeros((H, W), np.float32)
            F = decontaminate(img, a)
            if abs(z - 1) > 1e-4:
                F = warp(F, M); a = warp(a, M, cv2.BORDER_CONSTANT)
            base = img_t
            if back is not None:
                base = base * (1 - back[1]) + back[0] * back[1]
            if P['sticker'] > 0:
                base = sticker(base, a)
            out = base * (1 - a[..., None]) + F * a[..., None]
    front = load_png('front', i)
    if front is not None:
        out = out * (1 - front[1]) + front[0] * front[1]
    out = whip_fx(out, P['whip'], P['whipDir'], P.get('whipSign', 1))
    out = glitch_fx(out, P['glitch'], i * 7 + 3)
    out = shake_fx(out, P['shake'], t)
    if P['flash'] > 0:
        f = P['flash']; out = out * (1 - f) + np.array(P['flashColor'], np.float32) * f
    return np.clip(out + 0.5, 0, 255).astype(np.uint8)

def frames_iter(maxi=None):
    p = subprocess.Popen(['ffmpeg', '-v', 'error', '-i', wpath(CFG, 'cut.mp4'), '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], stdout=subprocess.PIPE)
    sz = W * H * 3; last = None
    for i in range(N if maxi is None else maxi + 1):
        if i < CUTN:
            buf = p.stdout.read(sz)
            if len(buf) == sz:
                last = np.frombuffer(buf, np.uint8).reshape(H, W, 3)
        yield i, last
    p.kill()

if __name__ == '__main__':
    args = sys.argv[1:]
    if args and args[0] == 'preview':
        outdir = wpath(CFG, 'preview'); want = sorted(int(v) for v in args[1:])
        os.makedirs(outdir, exist_ok=True)
        for i, fr in frames_iter(max(want)):
            if i in want:
                im = compose(i, fr)
                cv2.imwrite(os.path.join(outdir, f'p_{i:05d}.jpg'), im[..., ::-1], [cv2.IMWRITE_JPEG_QUALITY, 88])
        print('preview frames ->', outdir)
    else:
        out = rpath(CFG, CFG.get('output', 'out/reel.mp4')); os.makedirs(os.path.dirname(out), exist_ok=True)
        audio = wpath(CFG, 'mix.wav')
        enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                                '-i', audio, '-map', '0:v', '-map', '1:a', '-c:v', 'libx264', '-preset', 'medium', '-crf', '18',
                                '-pix_fmt', 'yuv420p', '-profile:v', 'high', '-c:a', 'aac', '-b:a', '192k', '-shortest',
                                '-movflags', '+faststart', out], stdin=subprocess.PIPE)
        for i, fr in frames_iter():
            enc.stdin.write(compose(i, fr).tobytes())
            if i % 100 == 0:
                print(f'frame {i}/{N}', flush=True)
        enc.stdin.close(); enc.wait()
        print('done ->', out)
