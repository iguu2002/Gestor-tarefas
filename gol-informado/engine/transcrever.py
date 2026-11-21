"""Transcreve a narração com o tempo de cada palavra.
Uso: python3 transcrever.py <projeto> [arquivo_de_audio]   ->  <projeto>/.cache/words.json"""
import sys, json, os, subprocess, numpy as np
from faster_whisper import WhisperModel
proj = sys.argv[1]; audio = sys.argv[2] if len(sys.argv) > 2 else 'media/narracao.mp3'
raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', os.path.join(proj, audio), '-f', 'f32le', '-ac', '1', '-ar', '16000', '-'], capture_output=True, check=True).stdout
model = WhisperModel('medium', device='cpu', compute_type='int8')
segs, _ = model.transcribe(np.frombuffer(raw, np.float32), language='pt', word_timestamps=True)
words = [{'w': w.word.strip(), 's': round(w.start, 2), 'e': round(w.end, 2)} for s in segs for w in s.words]
os.makedirs(os.path.join(proj, '.cache'), exist_ok=True)
json.dump(words, open(os.path.join(proj, '.cache', 'words.json'), 'w'), ensure_ascii=False, indent=0)
print(' '.join(f"{w['w']}[{w['s']}]" for w in words))
