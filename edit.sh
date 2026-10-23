#!/usr/bin/env bash
# Runs the whole edit, step by step. Put your video at the path in project.json ("video"), then:
#   bash edit.sh            # everything
#   bash edit.sh 4          # start again from step 4 (after you change the timeline or the graphics)
set -euo pipefail
cd "$(dirname "$0")"
FROM=${1:-0}
LANG_=$(python3 -c "import json;print(json.load(open('project.json')).get('language','english'))")
step() { [ "$1" -ge "$FROM" ]; }

step 0 && { echo "== 0. prepare";            python3 scripts/00_prepare.py; }
step 1 && { echo "== 1. transcribe the raw video"; node scripts/01_transcribe.mjs work/raw16.wav work/raw_words.json "$LANG_"; }
step 2 && { echo "== 2. cut pauses + bleeps (edit \"keep\" in project.json first, or run scripts/tools/find_pauses.py --write)";
            python3 scripts/02_cut.py
            node scripts/01_transcribe.mjs work/cut16.wav work/cut_words.json "$LANG_"; }
step 3 && { echo "== 3. cut yourself out (slow: ~4 s per frame, resumable)"; node scripts/03_cutout.mjs; }
step 4 && { echo "== 4. timeline";           python3 scripts/04_timeline.py; }
step 5 && { echo "== 5. graphics layers";    python3 scripts/05_render_layers.py back; python3 scripts/05_render_layers.py front; }
step 6 && { echo "== 6. music + sfx + mix";  python3 scripts/06_sound.py; }
step 7 && { echo "== 7. final video";        python3 scripts/07_compose.py; }
echo "done -> $(python3 -c "import json;print(json.load(open('project.json')).get('output','out/reel.mp4'))")"
