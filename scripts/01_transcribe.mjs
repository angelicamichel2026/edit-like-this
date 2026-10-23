// Step 1 - transcribe with word timestamps (Whisper, runs locally through transformers.js).
//
//   node scripts/01_transcribe.mjs work/raw16.wav work/raw_words.json [language]
//   node scripts/01_transcribe.mjs work/cut16.wav work/cut_words.json [language]
//
// The first run downloads the Whisper model (~250 MB) from Hugging Face and caches it.
// WHISPER_MODEL=Xenova/whisper-medium for better accuracy (slower).
// WHISPER_LOCAL=/path/to/models to use models already on disk.
import { pipeline, env } from '@huggingface/transformers';
import fs from 'fs';
import wf from 'wavefile';

const [, , wav, out, language = 'english'] = process.argv;
if (!wav || !out) { console.error('usage: node scripts/01_transcribe.mjs <in.wav> <out.json> [language]'); process.exit(1); }
if (process.env.WHISPER_LOCAL) { env.allowRemoteModels = false; env.localModelPath = process.env.WHISPER_LOCAL; }
const model = process.env.WHISPER_MODEL || 'Xenova/whisper-small';

const w = new wf.WaveFile(fs.readFileSync(wav));
w.toBitDepth('32f'); w.toSampleRate(16000);
let s = w.getSamples(); if (Array.isArray(s)) s = s[0];

const asr = await pipeline('automatic-speech-recognition', model, { dtype: 'q8' });
const r = await asr(new Float32Array(s), { language, task: 'transcribe', return_timestamps: 'word', chunk_length_s: 30, stride_length_s: 5 });
const words = r.chunks.map(c => ({ w: c.text.trim(), s: +c.timestamp[0].toFixed(3), e: +((c.timestamp[1] ?? c.timestamp[0] + 0.3)).toFixed(3) }));
fs.writeFileSync(out, JSON.stringify(words, null, 0));
console.log(r.text.trim());
console.log(`\n${words.length} words -> ${out}`);
