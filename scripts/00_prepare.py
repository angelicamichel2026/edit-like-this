"""Step 0 - prepare the raw video: constant 30 fps, 1080x1920, plus clean audio tracks.

    python3 scripts/00_prepare.py

in : project.json "video"            (any phone video, vertical)
out: work/cfr.mp4                    (every frame numbered, so cuts are frame-exact)
     work/raw48.wav, work/raw16.wav  (audio for editing / for transcription)
"""
import subprocess
from common import load, wpath, rpath

cfg = load()
src = rpath(cfg, cfg['video'])
fps = cfg.get('fps', 30)
vf = (f'fps={fps},scale=1080:1920:force_original_aspect_ratio=increase:out_range=tv,'
      'crop=1080:1920,format=yuv420p')
print('-> constant frame rate copy (this takes a minute or two)')
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', src, '-vf', vf, '-an', '-c:v', 'libx264', '-preset', 'fast',
                '-crf', '10', '-g', str(fps), wpath(cfg, 'cfr.mp4')], check=True)
for sr, name in ((48000, 'raw48.wav'), (16000, 'raw16.wav')):
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', src, '-vn', '-ac', '1', '-ar', str(sr), wpath(cfg, name)], check=True)
n = subprocess.run(['ffprobe', '-v', 'error', '-count_frames', '-select_streams', 'v:0', '-show_entries', 'stream=nb_read_frames',
                    '-of', 'csv=p=0', wpath(cfg, 'cfr.mp4')], capture_output=True, text=True).stdout.strip()
print(f'done: {n} frames at {fps} fps')
