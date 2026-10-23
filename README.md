# Edit Like This

The code that edited my "Go crazy" reel. A raw phone video goes in, and a finished 1080×1920 reel comes out:

- the pauses and stumbles are cut, and swear words are bleeped
- word-by-word captions are synced to your voice
- you're cut out of your background, so a new world sits behind you on every line
- animated cards, stickers, cartoon doodles, comment and DM mockups, and a code screen are drawn on top
- the camera moves: punch-in zooms, shakes, whip pans, glitches and flashes
- a beat with a drop and sound effects on every pop are mixed to -14 LUFS (Instagram/TikTok loudness)

No editing app and no editor. Each of the seven steps is a script you can read.

## Two ways to use it

### 1. Let Claude run it (easiest)

Open Claude in a mode that can run code, attach your vertical video and paste this:

```text
Edit my attached video like the "Edit Like This" reel, using this repo: https://github.com/angelicamichel2026/edit-like-this
My comment keyword is: EDIT        My name for the DM card is: <your name>
Follow the README step by step:
1. Run steps 0-2. Cut the pauses with scripts/tools/find_pauses.py and remove any stumbles or
   repeated words (check work/raw_words.json). Bleep swear words.
2. Start step 3 (the person cut-out) in the background. It is the slow step.
3. Rewrite scripts/04_timeline.py and the scenes in overlay/overlay.html for MY words:
   a new visual on every line, a big word behind my head on the key lines, a beat drop
   on my biggest line, and the "Comment <keyword>" end card.
4. Run steps 5-7, check a contact sheet for anything covering my face, fix it,
   and send me the MP4.
```

### 2. Run it yourself

You need **Python 3.10+**, **Node 18+** and **FFmpeg**.

```bash
git clone https://github.com/angelicamichel2026/edit-like-this edit-like-this && cd edit-like-this
pip install -r requirements.txt
python3 -m playwright install chromium
npm install
```

Put your video at `input/raw.mp4` and run the steps in order. `bash edit.sh` runs all of them, and `bash edit.sh 4` starts again from step 4.

## The steps

| Step | Command | What it does | Time for a 30 s reel |
|---|---|---|---|
| 0 | `python3 scripts/00_prepare.py` | Converts to a steady 30 fps at 1080×1920 and pulls out the audio | ~1 min |
| 1 | `node scripts/01_transcribe.mjs work/raw16.wav work/raw_words.json` | Whisper transcript with a time for every word | ~1 min (the first run downloads the model) |
| 2 | `python3 scripts/tools/find_pauses.py --write` then `python3 scripts/02_cut.py` | Cuts the dead air frame-exact, bleeps, cleans the voice | ~1 min |
| 2b | `node scripts/01_transcribe.mjs work/cut16.wav work/cut_words.json` | Transcript of the cut, for the captions | ~1 min |
| 3 | `node scripts/03_cutout.mjs` | AI mask of you on every frame | **45–75 min** (resumable) |
| 4 | `python3 scripts/04_timeline.py` | **Your reel:** words, caption lines, scenes, pops, zooms | instant |
| 5 | `python3 scripts/05_render_layers.py back` and `python3 scripts/05_render_layers.py front` | Draws the graphics behind you and in front of you | ~5 min |
| 6 | `python3 scripts/06_sound.py` | Beat, riser, drop, sound effects, voice, master to -14 LUFS | seconds |
| 7 | `python3 scripts/07_compose.py` | Puts it all together and exports `out/reel.mp4` | ~5–8 min |

Check before the full render: `python3 scripts/07_compose.py preview 0 150 300 450` writes a few finished frames to `work/preview/`. `python3 scripts/tools/contact_sheet.py out/reel.mp4 work/sheet.jpg` shows the whole reel on one image.

Step 3 doesn't have to finish first: `WAIT=1 python3 scripts/07_compose.py` composites frames as soon as their masks exist.

## Make it yours

**`project.json`**

| Field | What it is |
|---|---|
| `video` | your raw video |
| `keep` | the seconds of the raw video to keep, as `[start, end]` pairs (written by `find_pauses.py --write`, then fix the stumbles by hand) |
| `bleeps` | `[start, end]` seconds to bleep, in raw-video time |
| `brand` | your name and initial for the DM cards, the comment `keyword`, the DM line and the file name |
| `music` | `bpm` and `volume` of the beat |
| `loudness` | target LUFS (-14 for Instagram, TikTok and YouTube Shorts) |

**`scripts/04_timeline.py`** is the creative step. It's written for my script, so change it for yours:

- `W` holds your words with their times in the cut. Print them with `python3 scripts/tools/words_skeleton.py`, fix misheard words, and mark accent words with `'em'` and bleeped words with `'x'`.
- `BREAKS` is the first word of each caption line.
- `S` sets when each scene starts and ends.
- `TL` sets when each card, sticker or stamp pops. Most pops are tied to a word with `ws('word')`.
- `FACE` is roughly where your face sits in the frame, so the zooms aim at it.

**`overlay/overlay.html`** holds every scene: the prompt-box intro, the wall of your videos, the bleep bubble, the cartoon world with the bouncing word, the DM, the comments, the split-screen code, the cancelled invoice, the DIY scene, the drop with "LET'S GO", the alarm clock, the giant "AI" and the "Comment EDIT" end card. Open `overlay/overlay.html?layer=front&t=12` in a browser to see any moment. Change the words, or ask Claude to write new scenes for your script.

**The content wall** fills from your own videos: `python3 scripts/tools/wall_thumbs.py reel1.mp4 reel2.mp4`.

## Filming tips

- Use a plain, light wall and good light on your face. The cut-out is cleaner, so the new backgrounds look real.
- Hold the phone at eye level and keep your head in the middle third of the frame.
- Fast hand moves over your head blur. They still work, but keep the big gestures below your chin.
- iPhone: turn off HDR video (Settings > Camera > Record Video > HDR Video).
- Say your comment keyword clearly at the end.

## Credits and licenses

- Code in this repo: MIT (see `LICENSE`).
- Transcription: [Whisper](https://github.com/openai/whisper) through [transformers.js](https://github.com/huggingface/transformers.js) (Apache-2.0).
- Person cut-out: [@imgly/background-removal-node](https://github.com/imgly/background-removal-js) (AGPL-3.0). It's installed by `npm install` and isn't part of this repo. Using it to edit your own videos is fine. Read its license before you build a product or service on it.
- Rendering: Playwright, OpenCV, NumPy/SciPy and FFmpeg.
- Fonts: Anton, Inter, Instrument Serif, JetBrains Mono and Caveat Brush, all under the SIL Open Font License (`overlay/fonts/licenses`).
- Music and sound effects: synthesized by `scripts/06_sound.py`. No samples and no licensed audio.
