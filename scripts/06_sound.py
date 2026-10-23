"""Step 6 - the sound: a beat with a drop, sound effects on every pop, your voice on top.

    python3 scripts/06_sound.py            (add --stats to print levels per second)

Everything is synthesized here (no samples, no licensed music): kick, clap, hats, bass,
pads, plucks, a riser into the drop, plus whooshes, pops, typing, stamps, dings.
The sound effects are placed on the same times as the graphics (they read step 4).
in : work/voice.wav, work/bleep.wav, scripts/04_timeline.py
out: work/mix.wav  (mastered to project.json "loudness", -14 LUFS = Instagram/TikTok level)
"""
import json, os, sys, subprocess, importlib.util, numpy as np
from scipy.io import wavfile
from scipy.signal import butter, sosfilt, fftconvolve
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import load, wpath
CFG = load()

SR = 48000
spec = importlib.util.spec_from_file_location('tl', os.path.join(os.path.dirname(os.path.abspath(__file__)), '04_timeline.py'))
tl = importlib.util.module_from_spec(spec); spec.loader.exec_module(tl)
TL, S, WORDS, DUR, T_END = tl.TL, tl.S, tl.WORDS, tl.DUR, tl.T_END
NS = int(round(DUR * SR))
rs = np.random.RandomState(7)

def T(n): return np.arange(n) / SR
def bp(x, lo, hi, order=2): return sosfilt(butter(order, [lo, hi], btype='band', fs=SR, output='sos'), x)
def hp(x, f, order=2): return sosfilt(butter(order, f, btype='high', fs=SR, output='sos'), x)
def lp(x, f, order=2): return sosfilt(butter(order, f, btype='low', fs=SR, output='sos'), x)
def env_exp(n, tau): return np.exp(-T(n) / tau)
def add(buf, x, t, g=1.0):
    i = int(round(t * SR))
    if i < 0: x = x[-i:]; i = 0
    j = min(len(buf), i + len(x))
    if j > i: buf[i:j] += g * x[:j - i]
def noise(n): return rs.randn(n)
def fade(x, a=0.003, b=0.01):
    na, nb = int(a * SR), int(b * SR)
    if na: x[:na] *= np.linspace(0, 1, na)
    if nb: x[-nb:] *= np.linspace(1, 0, nb)
    return x
def norm(x, peak=1.0): return x / (np.abs(x).max() + 1e-9) * peak

# ---------------------------------------------------------------- instruments
def kick(dur=0.42):
    n = int(dur * SR); t = T(n)
    f = 46 + 120 * np.exp(-t / 0.028)
    ph = 2 * np.pi * np.cumsum(f) / SR
    x = np.sin(ph) * env_exp(n, 0.22) * (1 - np.exp(-t / 0.002))
    click = hp(noise(n), 3000) * env_exp(n, 0.004) * 0.35
    return fade(np.tanh(1.6 * (x + click)) / np.tanh(1.6), 0.0005, 0.03)
def clap(dur=0.32):
    n = int(dur * SR); x = np.zeros(n); src = bp(noise(n), 900, 2600)
    for k, d in enumerate([0, 0.011, 0.022]):
        i = int(d * SR); m = n - i
        x[i:] += src[:m] * env_exp(m, 0.006 if k < 2 else 0.11)
    return fade(norm(x, 0.9), 0.0005, 0.03)
def hat(dur=0.06, open_=False):
    n = int((0.22 if open_ else dur) * SR)
    x = hp(noise(n), 7500, 3) * env_exp(n, 0.07 if open_ else 0.014)
    return fade(norm(x, 0.5), 0.0005, 0.005)
def saw(f, t): return 2 * ((f * t) % 1.0) - 1
def pad_chord(freqs, dur, cutoff=1800):
    n = int(dur * SR); t = T(n); x = np.zeros(n)
    for f in freqs:
        for det in (-0.12, 0, 0.11):
            x += saw(f * 2 ** (det / 12), t + rs.rand())
    x = lp(x, cutoff, 2)
    return x / len(freqs) / 3
def bass_note(f, dur):
    n = int(dur * SR); t = T(n)
    x = np.sin(2 * np.pi * f * t) + 0.35 * np.sin(4 * np.pi * f * t) + 0.12 * np.sin(6 * np.pi * f * t)
    x = np.tanh(1.8 * x) * (1 - np.exp(-t / 0.004)) * np.exp(-t / 0.35)
    return fade(x, 0.001, 0.02)
def pluck(f, dur=0.25):
    n = int(dur * SR); t = T(n)
    x = (np.sin(2 * np.pi * f * t) + 0.4 * np.sin(4 * np.pi * f * t) + 0.15 * np.sin(6 * np.pi * f * t)) * env_exp(n, 0.07)
    return fade(x, 0.001, 0.02)
def stab(freqs, dur=0.22):
    n = int(dur * SR); t = T(n); x = np.zeros(n)
    for f in freqs:
        for det in (-0.15, 0.0, 0.14): x += saw(f * 2 ** (det / 12), t + rs.rand())
    x = lp(x, 3200, 2) * env_exp(n, 0.09)
    return fade(x / len(freqs) / 3, 0.001, 0.02)

# ---------------------------------------------------------------- sfx
def whoosh(dur=0.35, f0=400, f1=4000, rev=False):
    n = int(dur * SR); t = T(n); x = noise(n)
    # sweep a band through the noise by crossfading filtered copies
    out = np.zeros(n); K = 8
    for k in range(K):
        fc = f0 * (f1 / f0) ** (k / (K - 1))
        w = np.exp(-((t / dur - k / (K - 1)) ** 2) / 0.02)
        out += bp(x, fc * 0.7, min(fc * 1.4, 20000)) * w
    e = np.sin(np.pi * t / dur) ** 1.5
    out = out * e
    if rev: out = out[::-1]
    return fade(norm(out, 0.8), 0.002, 0.02)
def impact(dur=1.4, big=True):
    n = int(dur * SR); t = T(n)
    f = 30 + 70 * np.exp(-t / 0.12)
    sub = np.sin(2 * np.pi * np.cumsum(f) / SR) * env_exp(n, 0.45 if big else 0.25)
    crack = hp(noise(n), 1500) * env_exp(n, 0.05) * 0.6
    crash = hp(noise(n), 5000, 3) * env_exp(n, 0.55 if big else 0.25) * 0.35
    return fade(np.tanh(1.4 * (sub + crack + crash)), 0.0005, 0.05)
def pop(f=900, dur=0.09):
    n = int(dur * SR); t = T(n)
    ff = f * (1 + 1.2 * np.exp(-t / 0.012))
    x = np.sin(2 * np.pi * np.cumsum(ff) / SR) * env_exp(n, 0.025)
    return fade(x, 0.0005, 0.01)
def click(dur=0.03):
    n = int(dur * SR)
    x = bp(noise(n), 2500, 7000) * env_exp(n, 0.003) + np.sin(2 * np.pi * 180 * T(n)) * env_exp(n, 0.008) * 0.6
    return fade(norm(x, 0.8), 0.0002, 0.005)
def key(seed):
    r = np.random.RandomState(seed); n = int(0.035 * SR)
    x = bp(r.randn(n), 1800 + 900 * r.rand(), 6500) * env_exp(n, 0.004) + 0.5 * np.sin(2 * np.pi * (140 + 60 * r.rand()) * T(n)) * env_exp(n, 0.01)
    return fade(norm(x, 0.7), 0.0002, 0.005)
def ding(f1=1320, f2=1760, dur=0.7):
    n = int(dur * SR); t = T(n)
    a = np.sin(2 * np.pi * f1 * t) * env_exp(n, 0.25)
    b = np.zeros(n); i = int(0.09 * SR); b[i:] = np.sin(2 * np.pi * f2 * t[:n - i]) * env_exp(n - i, 0.3)
    return fade(0.6 * a + 0.6 * b, 0.001, 0.05)
def boing(f0=220, dur=0.32):
    n = int(dur * SR); t = T(n)
    f = f0 * (1 + 0.9 * (1 - np.exp(-t / 0.05))) * (1 + 0.06 * np.sin(2 * np.pi * 18 * t))
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * env_exp(n, 0.11)
    return fade(x, 0.001, 0.03)
def stamp():
    n = int(0.6 * SR); t = T(n)
    thud = np.sin(2 * np.pi * np.cumsum(55 + 90 * np.exp(-t / 0.03)) / SR) * env_exp(n, 0.16)
    crack = bp(noise(n), 400, 5000) * env_exp(n, 0.02)
    return fade(np.tanh(2.2 * (thud + 0.9 * crack)), 0.0003, 0.05)
def scribble(dur=0.35):
    n = int(dur * SR); t = T(n)
    am = 0.5 + 0.5 * np.sign(np.sin(2 * np.pi * 14 * t + 3 * np.sin(2 * np.pi * 3 * t)))
    x = bp(noise(n), 2200, 7000) * (0.3 + 0.7 * am) * np.sin(np.pi * t / dur)
    return fade(norm(x, 0.6), 0.002, 0.02)
def glitchs(dur=0.18):
    n = int(dur * SR); x = np.zeros(n); r = np.random.RandomState(11)
    blk = int(0.012 * SR)
    for i in range(0, n, blk):
        f = r.choice([180, 360, 720, 1440, 2880])
        seg = np.sign(np.sin(2 * np.pi * f * T(min(blk, n - i)))) * (0.4 + 0.6 * r.rand())
        if r.rand() < .35: seg = r.randn(len(seg)) * 0.6
        x[i:i + len(seg)] = seg
    return fade(lp(x, 9000) * 0.6, 0.001, 0.01)
def tick(f=2600):
    n = int(0.03 * SR)
    return fade(np.sin(2 * np.pi * f * T(n)) * env_exp(n, 0.004) + 0.4 * bp(noise(n), 3000, 9000) * env_exp(n, 0.002), 0.0002, 0.005)
def bell(dur=1.0):
    n = int(dur * SR); t = T(n)
    x = sum(a * np.sin(2 * np.pi * f * t) for f, a in [(2400, 1), (3100, .5), (4700, .3)])
    am = 0.5 + 0.5 * np.sign(np.sin(2 * np.pi * 22 * t))
    return fade(x * am * np.sin(np.pi * t / dur) ** 0.4 * 0.35, 0.005, 0.05)
def chirp(f0=300, f1=2400, dur=0.28):
    n = int(dur * SR); t = T(n)
    f = f0 * (f1 / f0) ** (t / dur)
    return fade(np.sin(2 * np.pi * np.cumsum(f) / SR) * np.sin(np.pi * t / dur), 0.002, 0.02)
def shimmer(dur=0.8):
    n = int(dur * SR); x = np.zeros(n); r = np.random.RandomState(5)
    for k in range(18):
        i = int(r.rand() * 0.6 * SR); f = 2000 + 4000 * r.rand(); m = n - i
        x[i:] += np.sin(2 * np.pi * f * T(m)) * env_exp(m, 0.06)
    return fade(x / 6, 0.002, 0.05)
def riser(dur):
    n = int(dur * SR); t = T(n)
    f = 180 * (8.0) ** (t / dur)
    tone = np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.25
    nz = noise(n); out = np.zeros(n); K = 10
    for k in range(K):
        fc = 500 * (16) ** (k / (K - 1)); w = np.exp(-((t / dur - k / (K - 1)) ** 2) / 0.015)
        out += bp(nz, fc * 0.7, min(fc * 1.5, 20000)) * w
    e = (t / dur) ** 2.2
    return fade(norm(out, 0.7) * e + tone * e, 0.01, 0.005)

# ---------------------------------------------------------------- music arrangement
BPM = CFG.get('music', {}).get('bpm', 120); BEAT = 60 / BPM; T0 = 2.24   # T0 = first downbeat (when the edit explodes)
BREAK_A, DROP = S['tense'][0], 19.74
END_HIT = T0 + 51 * BEAT           # 27.74
CH = [(57, [220.0, 261.63, 329.63]), (43.65, [174.61, 220.0, 261.63]), (65.41, [261.63, 329.63, 392.0]), (49.0, [196.0, 246.94, 293.66])]
music = np.zeros(NS); drums = np.zeros(NS); bassb = np.zeros(NS); padb = np.zeros(NS); leadb = np.zeros(NS)
K, CL, HC, HO = kick(), clap(), hat(), hat(open_=True)
nbeats = int((END_HIT - T0) / BEAT) + 1
for b in range(nbeats):
    t = T0 + b * BEAT
    if BREAK_A - 0.02 <= t < DROP - 0.01: continue
    if t > END_HIT + 0.01: break
    add(drums, K, t, 1.0)
    if b % 2 == 1: add(drums, CL, t, 0.55)
    add(drums, HC, t + BEAT / 2, 0.30)
    if b % 4 == 3: add(drums, HO, t + BEAT / 2, 0.22)
    for q in (0.25, 0.75): add(drums, HC, t + BEAT * q, 0.12)
# snare roll building into the drop
roll_t = BREAK_A + 0.3
while roll_t < DROP - 0.02:
    p = (roll_t - BREAK_A) / (DROP - BREAK_A)
    add(drums, CL, roll_t, 0.15 + 0.4 * p)
    roll_t += BEAT / (4 if p < 0.55 else 8)
# bass + pad + stabs per bar
for bar in range(int((END_HIT - T0) / (4 * BEAT)) + 2):
    t_bar = T0 + bar * 4 * BEAT
    root, chord = CH[bar % 4]
    for e8 in range(8):
        t = t_bar + e8 * BEAT / 2
        if t >= END_HIT or (BREAK_A - 0.02 <= t < DROP - 0.01): continue
        add(bassb, bass_note(root * (2 if e8 % 2 else 1), BEAT / 2 * 0.95), t, 0.55 if e8 % 2 == 0 else 0.35)
    if t_bar < END_HIT:
        pc = pad_chord(chord, 4 * BEAT, 1500 if t_bar < DROP else 2600)
        add(padb, pc, t_bar, 0.32)
    if t_bar >= DROP - 0.1 and t_bar < END_HIT:
        for b2 in (1.5, 3.5):
            add(leadb, stab([f * 2 for f in chord]), t_bar + b2 * BEAT, 0.33)
# intro: filtered pad swell before the first downbeat
intro = pad_chord(CH[0][1], T0 + 0.1, 700) * np.linspace(0, 1, int((T0 + 0.1) * SR)) ** 2
add(padb, intro, 0.0, 0.5)
# cartoon section: bouncy pentatonic plucks
PENT = [440.0, 523.25, 587.33, 659.25, 783.99, 880.0]
r2 = np.random.RandomState(3)
tt = S['toon'][0]
while tt < S['toon'][1] - 0.05:
    add(leadb, pluck(PENT[r2.randint(len(PENT))] * (1 if r2.rand() < .7 else 2)), tt, 0.32)
    tt += BEAT / 4
# breakdown pad (tension, filtered) under the riser
add(padb, pad_chord([220.0, 261.63, 329.63], DROP - BREAK_A, 600) * np.linspace(1, 0.3, int((DROP - BREAK_A) * SR)), BREAK_A, 0.5)
# sidechain pump from the kick
sc = np.ones(NS)
for b in range(nbeats):
    t = T0 + b * BEAT
    if BREAK_A - 0.02 <= t < DROP - 0.01: continue
    i = int(t * SR); n = int(0.22 * SR)
    if i + n < NS: sc[i:i + n] = np.minimum(sc[i:i + n], 0.35 + 0.65 * (1 - np.exp(-T(n) / 0.07)))
music = drums * 0.9 + bassb * sc + padb * (0.4 + 0.6 * sc) + leadb * (0.5 + 0.5 * sc)
# final tail
endi = int((END_HIT + 0.02) * SR)
tail = np.linspace(1, 0, NS - endi) ** 2 if NS > endi else None
if tail is not None:
    music[endi:] = music[endi:] * tail
music = lp(music, 15000)

# ---------------------------------------------------------------- sfx track
fx = np.zeros(NS)
PW = [w for w in WORDS if w['st'] == 'hide']
k = 0
for w in PW:
    nch = len(w['w']) + 1
    for c in range(nch):
        add(fx, key(k), w['s'] + (w['e'] - w['s']) * c / nch, 0.30); k += 1
P0 = TL['prompt']
add(fx, click(), P0['click'], 0.8)
add(fx, whoosh(0.22, 300, 6000), P0['expandA'] - 0.02, 0.55)
add(fx, impact(1.6, True), 2.24, 0.95)
add(fx, whoosh(0.5, 2000, 300), 2.28, 0.25)
for j in range(6):
    add(fx, pop(700 + 120 * j), TL['wall']['social'] - .02 + j * .065, 0.42)
add(fx, whoosh(0.3, 5000, 400, rev=True), TL['wall']['put'] - 0.12, 0.5)
for j in range(6):
    add(fx, click(), TL['wall']['put'] + .1 + j * .045, 0.35)
add(fx, ding(1568, 2093, 0.5), TL['wall']['here'], 0.32)
add(fx, whoosh(0.24, 600, 7000), 6.87 - 0.12, 0.6)
add(fx, pop(500, 0.12), TL['bleep']['balloonIn'], 0.55)
add(fx, boing(160, 0.4), 8.27, 0.45)
add(fx, impact(0.6, False), 8.27, 0.4)
for j in range(10):
    add(fx, pop(PENT[j % 6] * 1.5, 0.11), TL['toon']['create'] + .02 + j * .05 + .16, 0.30)
add(fx, whoosh(0.5, 800, 5000), TL['toon']['dm'] - 0.02, 0.35)
add(fx, ding(), TL['toon']['dmMsg'], 0.42)
add(fx, whoosh(0.22, 7000, 500), 10.82 - 0.11, 0.55)
for j in range(5):
    add(fx, pop(1100 + 90 * j, 0.07), S['cmts'][0] + .04 + j * .11, 0.33)
add(fx, pop(1500, 0.1), TL['cmts']['edit'] - .02, 0.5)
add(fx, pop(1900, 0.06), TL['cmts']['edit'] + .18, 0.3)
add(fx, glitchs(0.2), 11.96 - 0.08, 0.5)
tk = 12.0; j = 0
while tk < 13.9:
    add(fx, key(500 + j), tk, 0.16); tk += 0.05 + 0.02 * ((j * 7) % 3) / 2; j += 1
for j in range(2): add(fx, tick(1900), TL['code']['now'] + j * 0.14, 0.4)
add(fx, whoosh(0.26, 400, 3000), S['code'][1] - 0.02, 0.45)
add(fx, whoosh(0.3, 2500, 500), TL['invoice']['in'] - 0.03, 0.35)
add(fx, scribble(0.22), TL['invoice']['editor'], 0.3)
add(fx, stamp(), TL['invoice']['stamp'], 0.95)
add(fx, scribble(0.3), TL['invoice']['stamp'] + 0.08, 0.35)
add(fx, whoosh(0.28, 500, 6000), TL['invoice']['out'] - 0.02, 0.4)
add(fx, boing(260, 0.35), S['diy'][0], 0.45)
add(fx, scribble(0.25), S['diy'][0] + 0.2, 0.3)
add(fx, impact(0.5, False), S['tense'][0], 0.35)
add(fx, riser(DROP - S['tense'][0] - 0.05), S['tense'][0] + 0.03, 0.55)
lt = TL['tense']['okay']; j = 0
while lt < DROP - 0.05:
    add(fx, tick(900 + 60 * j), lt, 0.18); lt += 0.11; j += 1
add(fx, impact(2.0, True), DROP + 0.02, 1.0)
add(fx, whoosh(0.4, 7000, 300, rev=True), DROP - 0.4, 0.4)
for j in range(8): add(fx, pop(600 + 160 * j, 0.06), DROP + 0.03 + j * 0.03, 0.18)
tc = S['clock'][0]; j = 0
while tc < S['clock'][1] - 0.05:
    add(fx, tick(2600 if j % 2 else 2100), tc, 0.35); tc += 0.125; j += 1
add(fx, bell(0.9), S['clock'][0] + 0.15, 0.3)
add(fx, glitchs(0.15), S['ai'][0] - 0.05, 0.45)
add(fx, click(), TL['ai']['click'], 0.8)
add(fx, chirp(300, 2400, 0.26), TL['ai']['click'] + 0.02, 0.3)
add(fx, impact(0.9, False), TL['ai']['big'], 0.55)
add(fx, shimmer(0.8), TL['ai']['big'] + 0.02, 0.5)
add(fx, whoosh(0.22, 7000, 500), 22.80 - 0.11, 0.55)
for j in range(4): add(fx, key(900 + j), TL['cta']['typeA'] + j * 0.05, 0.4)
add(fx, click(), TL['cta']['post'], 0.6)
add(fx, whoosh(0.25, 800, 6000), TL['cta']['post'] + 0.02, 0.3)
add(fx, ding(), TL['cta']['dm'], 0.45)
add(fx, impact(0.7, False), TL['cta']['lets'], 0.45)
E = TL['end']
add(fx, whoosh(0.3, 500, 6000), E['in'] - 0.06, 0.5)
for j in range(4): add(fx, stamp(), E['stamp'] + j * 0.07, 0.22)
for j in range(4): add(fx, key(1300 + j), E['typeA'] + j * (E['typeB'] - E['typeA']) / 4, 0.4)
add(fx, click(), E['post'], 0.6)
add(fx, pop(1200, 0.1), E['line'], 0.3)
add(fx, pop(900, 0.12), E['stats'], 0.4)
for j in range(10): add(fx, tick(1800 + 70 * j), E['stats'] + 0.05 + j * 0.05, 0.12)

# ---------------------------------------------------------------- mix
def rd(p):
    sr, x = wavfile.read(p); x = x.astype(np.float32) / 32768
    return x if x.ndim == 1 else x.mean(1)
voice = np.zeros(NS); v = rd(wpath(CFG, 'voice.wav')); voice[:min(NS, len(v))] = v[:NS]
bleep = np.zeros(NS); bl = rd(wpath(CFG, 'bleep.wav')); bleep[:min(NS, len(bl))] = bl[:NS]
# voice-activity ducking for the music
hop = int(0.01 * SR); nh = NS // hop
ve = np.sqrt(np.mean(voice[:nh * hop].reshape(nh, hop) ** 2, axis=1) + 1e-12)
act = np.clip((20 * np.log10(ve) + 42) / 14, 0, 1)
sm = np.zeros_like(act); a_att, a_rel = 0.5, 0.06
for i in range(nh):
    prev = sm[i - 1] if i else 0
    sm[i] = prev + (act[i] - prev) * (a_att if act[i] > prev else a_rel)
duck = np.repeat(1 - 0.45 * sm, hop); duck = np.concatenate([duck, np.ones(NS - len(duck))])
music_n = norm(music, 1.0)
MV = CFG.get('music', {}).get('volume', 0.32)
mix = voice * 1.0 + bleep * 0.9 + music_n * MV * duck + fx * 0.30
mix = np.tanh(mix * 1.1) / 1.1
wavfile.write(wpath(CFG, 'mix_pre.wav'), SR, (np.clip(mix, -1, 1) * 32767).astype(np.int16))
# master: two-pass loudness normalisation to the target (linear, keeps the dynamics)
L = CFG.get('loudness', -14)
r = subprocess.run(['ffmpeg', '-hide_banner', '-i', wpath(CFG, 'mix_pre.wav'), '-af', f'loudnorm=I={L}:TP=-1.5:LRA=9:print_format=json',
                    '-f', 'null', '-'], capture_output=True, text=True).stderr
m = json.loads(r[r.rindex('{'):r.rindex('}') + 1])
af = (f"loudnorm=I={L}:TP=-1.5:LRA=9:measured_I={m['input_i']}:measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}:"
      f"measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true")
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', wpath(CFG, 'mix_pre.wav'), '-af', af, '-ar', str(SR), wpath(CFG, 'mix.wav')], check=True)
print(f'mix.wav ready: {NS / SR:.2f}s at {L} LUFS')

if '--stats' in sys.argv:
    def rms_db(x, a, b):
        seg = x[int(a * SR):int(b * SR)]
        return 20 * np.log10(np.sqrt(np.mean(seg ** 2)) + 1e-9)
    st = [("voice", voice), ("music", music_n * MV * duck), ('fx', fx * 0.30)]
    print('   t   ' + '  '.join(f'{n:>7s}' for n, _ in st))
    for a in np.arange(0, DUR, 1.0):
        print(f'{a:5.1f}  ' + '  '.join(f'{rms_db(x, a, a + 1):7.1f}' for _, x in st))
    
