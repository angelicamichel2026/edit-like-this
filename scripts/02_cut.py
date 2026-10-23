"""Step 2 - cut the pauses (frame-exact), bleep the swear words, clean the voice.

    python3 scripts/02_cut.py

in : work/cfr.mp4, work/raw48.wav, project.json "keep" + "bleeps" (seconds of the RAW video)
out: work/cut.mp4            the cut video (no audio)
     work/voice.wav          cleaned voice, same length as cut.mp4
     work/bleep.wav          the bleep tones (mixed in step 6)
     work/cut16.wav          for transcribing the cut (captions)
     work/fmap.json          output frame -> raw frame
     work/frames_src/*.jpg   the kept frames, for the person cut-out (step 3)
"""
import json, os, subprocess, numpy as np
from scipy.io import wavfile
from common import load, wpath

cfg = load()
FPS, SR = cfg.get('fps', 30), 48000
SPF = SR // FPS
SEGS = [(round(a * FPS), round(b * FPS)) for a, b in cfg['keep']]
BLEEPS = cfg.get('bleeps', [])

sr, x = wavfile.read(wpath(cfg, 'raw48.wav'))
x = x.astype(np.float32) / 32768
assert sr == SR, 'run step 0 first'
# bleeps go on the raw track, so they survive any change to the cut
bleep = np.zeros_like(x)
for a, b in BLEEPS:
    i0, i1 = int(a * SR), int(b * SR)
    n = i1 - i0; t = np.arange(n) / SR
    env = np.ones(n); f = int(0.006 * SR); env[:f] = np.linspace(0, 1, f); env[-f:] = np.linspace(1, 0, f)
    bleep[i0:i1] = 0.22 * np.sin(2 * np.pi * 1000 * t) * env
    duck = np.zeros(n); g = int(0.008 * SR); duck[:g] = np.linspace(1, 0, g); duck[-g:] = np.linspace(0, 1, g)
    x[i0:i1] *= duck
parts, bparts = [], []
fade = int(0.012 * SR)
for fa, fb in SEGS:
    seg = x[fa * SPF: fb * SPF].copy()
    seg[:fade] *= np.linspace(0, 1, fade); seg[-fade:] *= np.linspace(1, 0, fade)
    parts.append(seg); bparts.append(bleep[fa * SPF: fb * SPF].copy())
y, yb = np.concatenate(parts), np.concatenate(bparts)
wavfile.write(wpath(cfg, 'voice_raw.wav'), SR, (y * 32767).astype(np.int16))
wavfile.write(wpath(cfg, 'bleep.wav'), SR, (yb * 32767).astype(np.int16))
# voice cleanup: rumble out, less boxy, more presence, light denoise, compression
chain = ('highpass=f=85,equalizer=f=250:width_type=q:w=1.0:g=-3,equalizer=f=3200:width_type=q:w=1.2:g=2.5,'
         'equalizer=f=9000:width_type=q:w=0.8:g=1.5,afftdn=nr=8:nf=-42:tn=1,'
         'acompressor=threshold=-20dB:ratio=3.2:attack=4:release=80:makeup=2.5,alimiter=limit=0.89:attack=2:release=40')
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', wpath(cfg, 'voice_raw.wav'), '-af', chain, '-ar', str(SR), wpath(cfg, 'voice.wav')], check=True)
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', wpath(cfg, 'voice_raw.wav'), '-ac', '1', '-ar', '16000', wpath(cfg, 'cut16.wav')], check=True)

expr = '+'.join(f'between(n\\,{fa}\\,{fb - 1})' for fa, fb in SEGS)
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', wpath(cfg, 'cfr.mp4'), '-vf', f"select='{expr}',setpts=N/{FPS}/TB",
                '-r', str(FPS), '-an', '-c:v', 'libx264', '-preset', 'fast', '-crf', '8', '-g', str(FPS), wpath(cfg, 'cut.mp4')], check=True)
fmap = [f for fa, fb in SEGS for f in range(fa, fb)]
json.dump(fmap, open(wpath(cfg, 'fmap.json'), 'w'))
# kept frames as JPGs for the cut-out step
fs = wpath(cfg, 'frames_src'); os.makedirs(fs, exist_ok=True)
for f in os.listdir(fs):
    os.remove(os.path.join(fs, f))
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', wpath(cfg, 'cut.mp4'), '-q:v', '2', '-start_number', '0',
                os.path.join(fs, 'o_%05d.jpg')], check=True)
for i, src in enumerate(fmap):          # name each JPG by its raw frame number
    os.rename(os.path.join(fs, f'o_{i:05d}.jpg'), os.path.join(fs, f'f_{src:05d}.jpg'))
print(f'cut: {len(fmap)} frames = {len(fmap) / FPS:.2f}s (from {len(SEGS)} segments)')
