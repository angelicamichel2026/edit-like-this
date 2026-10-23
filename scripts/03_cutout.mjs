// Step 3 - cut yourself out of the background, frame by frame (AI person mask).
//
//   node scripts/03_cutout.mjs            (run it from the repo folder)
//
// in : work/frames_src/f_XXXXX.jpg (from step 2), work/fmap.json
// out: work/masks/m_XXXXX.png  (one alpha mask per kept frame)
//
// This is the slow step: about 3-5 s per frame on a laptop CPU (a 30 s reel = ~900 frames).
// It is resumable: stop it any time and run it again, finished masks are skipped.
// MODEL=medium gives slightly cleaner edges and runs about 1.6x slower.
import { segmentForeground } from '@imgly/background-removal-node';
import fs from 'fs';
import path from 'path';

const cfg = JSON.parse(fs.readFileSync(process.env.PROJECT || 'project.json', 'utf8'));
const work = path.resolve(cfg.work || 'work');
const fmap = JSON.parse(fs.readFileSync(path.join(work, 'fmap.json'), 'utf8'));
const inDir = path.join(work, 'frames_src'), outDir = path.join(work, 'masks');
fs.mkdirSync(outDir, { recursive: true });
const model = process.env.MODEL || 'small';
const t0 = Date.now(); let done = 0;
for (const n of fmap) {
  const id = String(n).padStart(5, '0');
  const inp = path.join(inDir, `f_${id}.jpg`), out = path.join(outDir, `m_${id}.png`);
  if (fs.existsSync(out)) { done++; continue; }
  const blob = await segmentForeground('file://' + inp, { model, output: { format: 'image/png' } });
  fs.writeFileSync(out + '.tmp', Buffer.from(await blob.arrayBuffer()));
  fs.renameSync(out + '.tmp', out);
  done++;
  if (done % 10 === 0) {
    const el = (Date.now() - t0) / 1000;
    console.log(`${done}/${fmap.length} masks  ${el.toFixed(0)}s`);
  }
}
console.log('done', done);
