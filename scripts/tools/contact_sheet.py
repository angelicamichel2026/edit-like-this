"""A contact sheet of any video, to check an edit at a glance.

    python3 scripts/tools/contact_sheet.py out/reel.mp4 work/sheet.jpg --fps 2 --cols 10
"""
import argparse, subprocess, numpy as np, cv2
ap = argparse.ArgumentParser()
ap.add_argument('video'); ap.add_argument('out')
ap.add_argument('--fps', type=float, default=2); ap.add_argument('--cols', type=int, default=10)
a = ap.parse_args()
w, h = 216, 384
p = subprocess.run(['ffmpeg', '-v', 'error', '-i', a.video, '-vf', f'fps={a.fps}:round=down,scale={w}:{h}', '-f', 'rawvideo',
                    '-pix_fmt', 'bgr24', '-'], capture_output=True).stdout
n = len(p) // (w * h * 3)
ims = [np.frombuffer(p, np.uint8, w * h * 3, k * w * h * 3).reshape(h, w, 3).copy() for k in range(n)]
for k, im in enumerate(ims):
    cv2.putText(im, f'{k / a.fps:.1f}s', (5, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 255), 2)
while len(ims) % a.cols: ims.append(np.zeros((h, w, 3), np.uint8))
rows = [np.hstack(ims[i:i + a.cols]) for i in range(0, len(ims), a.cols)]
cv2.imwrite(a.out, np.vstack(rows), [cv2.IMWRITE_JPEG_QUALITY, 82])
print(n, 'frames ->', a.out)
