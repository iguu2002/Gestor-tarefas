"""Gera as legendas palavra por palavra (1 a 3 palavras) a partir de words.json.
Uso: python3 legendas.py <projeto>
Lê <projeto>/legenda.json: {"corrigir": {"errado": "certo"}, "destaques": ["palavra", "duas palavras"]}
Escreve "captions" e "duration" dentro de <projeto>/spec.json."""
import sys, json, os, re
proj = sys.argv[1]
words = json.load(open(os.path.join(proj, '.cache', 'words.json')))
cfg = json.load(open(os.path.join(proj, 'legenda.json'))) if os.path.exists(os.path.join(proj, 'legenda.json')) else {}
fix = cfg.get('corrigir', {}); hls = [h.lower().split() for h in cfg.get('destaques', [])]
for w in words:
    core = re.sub(r'[^\wÀ-ÿ€]', '', w['w'])
    if core in fix: w['w'] = w['w'].replace(core, fix[core])
norm = lambda s: re.sub(r'[^\wÀ-ÿ€]', '', s).lower()
# marca destaques e junta cada destaque numa unidade só (nunca quebra "Nico | Paz")
toks, i = [], 0
while i < len(words):
    m = next((h for h in sorted(hls, key=len, reverse=True) if [norm(x['w']) for x in words[i:i+len(h)]] == h), None)
    if m:
        g = words[i:i+len(m)]; toks.append({'w': ' '.join(x['w'] for x in g), 's': g[0]['s'], 'e': g[-1]['e'], 'hl': True}); i += len(m)
    else:
        toks.append(words[i]); i += 1
caps, cur = [], []
def flush():
    if not cur: return
    text = ' '.join(f"*{x['w']}*" if x.get('hl') else x['w'] for x in cur)
    caps.append({'t': cur[0]['s'], 'end': cur[-1]['e'], 'text': text}); cur.clear()
for i, w in enumerate(toks):
    chars = sum(len(x['w']) + 1 for x in cur)
    if cur and (w['s'] - cur[-1]['e'] > 0.35 or len(cur) >= 3 or chars + len(w['w']) > 18): flush()
    cur.append(w)
    if re.search(r'[.,!?:;]$', w['w']): flush()
flush()
for c in caps: c['text'] = re.sub(r'[,;:]', '', c['text']).replace('.', '') if not c['text'].endswith('?') else c['text'].replace(',', '')
sp = os.path.join(proj, 'spec.json'); spec = json.load(open(sp))
spec['captions'] = caps; spec['duration'] = round(words[-1]['e'] + 0.6, 2)
json.dump(spec, open(sp, 'w'), ensure_ascii=False, indent=1)
print(len(caps), 'legendas'); print(' | '.join(c['text'] for c in caps))
