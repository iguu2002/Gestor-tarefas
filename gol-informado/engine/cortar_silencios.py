"""Corta os silêncios da narração e reajusta o vídeo inteiro à nova linha do tempo.
Uso: python3 cortar_silencios.py <projeto> [--min 0.2] [--manter 0.15] [--db -35]

- Na primeira vez, guarda spec_original.json e .cache/words_original.json (linha do tempo da narração original).
- Sempre parte desses originais, então pode rodar de novo com outros valores sem acumular cortes.
- Cada silêncio maior que --min vira uma pausa de --manter segundos.
- Gera media/narracao_cortada.wav, reescreve spec.json e .cache/words.json.
- Clipes de lance perdem tempo do COMEÇO (o final, com o gol, é preservado).
Depois rode: python3 legendas.py <projeto>"""
import sys, os, json, re, subprocess, shutil, argparse
ap = argparse.ArgumentParser(); ap.add_argument('proj'); ap.add_argument('--min', type=float, default=0.2)
ap.add_argument('--manter', type=float, default=0.15); ap.add_argument('--db', type=float, default=-35)
a = ap.parse_args(); P = a.proj
orig_spec = os.path.join(P, 'spec_original.json'); orig_words = os.path.join(P, '.cache', 'words_original.json')
if not os.path.exists(orig_spec): shutil.copy(os.path.join(P, 'spec.json'), orig_spec)
if not os.path.exists(orig_words): shutil.copy(os.path.join(P, '.cache', 'words.json'), orig_words)
spec = json.load(open(orig_spec)); words = json.load(open(orig_words))
audio = os.path.join(P, spec['audio'])
log = subprocess.run(['ffmpeg', '-hide_banner', '-i', audio, '-af', f'silencedetect=noise={a.db}dB:d={a.min}', '-f', 'null', '-'], capture_output=True, text=True).stderr
st = [float(x) for x in re.findall(r'silence_start: ([\d.]+)', log)]; en = [float(x) for x in re.findall(r'silence_end: ([\d.]+)', log)]
dur = float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', audio], capture_output=True, text=True).stdout)
h = a.manter / 2
cuts = [(s + h, e - h) for s, e in zip(st, en) if e - s > a.manter + 0.02]   # trechos removidos
def T(t):  # tempo original -> tempo novo
    r = 0.0
    for s, e in cuts:
        if t >= e: r += e - s
        elif t > s: r += t - s
    return round(t - r, 3)
# 1. áudio cortado (micro-fades para não estalar)
keep, last = [], 0.0
for s, e in cuts: keep.append((last, s)); last = e
keep.append((last, dur))
fc = ''.join(f'[0]atrim={s:.3f}:{e:.3f},asetpts=PTS-STARTPTS,afade=t=in:d=0.006,afade=t=out:st={max(0, e - s - 0.006):.3f}:d=0.006[k{i}];' for i, (s, e) in enumerate(keep))
fc += ''.join(f'[k{i}]' for i in range(len(keep))) + f'concat=n={len(keep)}:v=0:a=1[o]'
out_audio = 'media/narracao_cortada.wav'
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', audio, '-filter_complex', fc, '-map', '[o]', os.path.join(P, out_audio)], check=True)
# 2. palavras na nova linha do tempo
for w in words: w['s'], w['e'] = T(w['s']), T(w['e'])
json.dump(words, open(os.path.join(P, '.cache', 'words.json'), 'w'), ensure_ascii=False)
# 3. cenas e efeitos na nova linha do tempo
t0 = 0.0
for sc in spec['scenes']:
    a0, a1 = t0, t0 + sc['dur']; n0, n1 = T(a0), T(a1); t0 = a1
    lost = (a1 - a0) - (n1 - n0); sc['dur'] = round(n1 - n0, 3)
    for f in sc.get('fx', []):
        if 't' in f: f['t'] = round(max(0, T(a0 + f['t']) - n0), 3)
        if 'until' in f: f['until'] = round(max(0, T(a0 + f['until']) - n0), 3)
    b = sc['bg']
    if b['type'] == 'split':
        for k in ('left', 'right'):
            if b.get(k) and b[k].get('t'): b[k]['t'] = round(T(a0 + b[k]['t']) - n0, 3)
    if b['type'] == 'clip': b['start'] = round(b.get('start', 0) + lost * b.get('speed', 1), 3)
spec['audio'] = out_audio; spec.pop('captions', None); spec.pop('duration', None)
json.dump(spec, open(os.path.join(P, 'spec.json'), 'w'), ensure_ascii=False, indent=1)
print(f'{len(cuts)} silêncios cortados: {dur:.1f}s -> {T(dur):.1f}s')
