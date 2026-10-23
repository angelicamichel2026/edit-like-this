"""Fill the "content wall" with thumbnails from your own videos.

    python3 scripts/tools/wall_thumbs.py my_reel1.mp4 my_reel2.mp4 --per-video 8

Writes small JPGs to overlay/img/wall/ (the wall scene and the timeline strip use them).
Run step 4 again afterwards so the timeline picks up the new list.
"""
import argparse, os, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common import ROOT

ap = argparse.ArgumentParser()
ap.add_argument('videos', nargs='+')
ap.add_argument('--per-video', type=int, default=8)
a = ap.parse_args()
out = os.path.join(ROOT, 'overlay', 'img', 'wall'); os.makedirs(out, exist_ok=True)
k = len([f for f in os.listdir(out) if f.endswith('.jpg')])
for v in a.videos:
    dur = float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', v],
                               capture_output=True, text=True).stdout.strip())
    for j in range(a.per_video):
        t = dur * (j + 0.5) / a.per_video
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', f'{t:.2f}', '-i', v, '-frames:v', '1',
                        '-vf', 'scale=240:427:force_original_aspect_ratio=increase,crop=240:427', '-q:v', '3',
                        os.path.join(out, f'w{k:02d}.jpg')], check=True)
        k += 1
print(k, 'thumbnails in', out)
