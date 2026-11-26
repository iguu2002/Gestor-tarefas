"""Legenda single-word (uma palavra por vez) a partir de words.json.
Uso: python3 legendas.py <projeto> [--blocos]   (--blocos = modo antigo de 1-3 palavras)
<projeto>/legenda.json: {"corrigir": {"errado": "certo"}, "destaques": ["palavra", "duas palavras"], "dinheiro": ["440 milhões", ...]}
- destaques alternam entre a cor do canal (*) e a cor alternativa (^)
- valores em dinheiro ficam verdes ($), automático para números + milhões/mil/euros/reais/R$/€
Escreve "captions" e "duration" em <projeto>/spec.json."""
import sys, json, os, re
proj = sys.argv[1]; blocos = '--blocos' in sys.argv
words = json.load(open(os.path.join(proj, '.cache', 'words.json')))
cfg = json.load(open(os.path.join(proj, 'legenda.json'))) if os.path.exists(os.path.join(proj, 'legenda.json')) else {}
fix = cfg.get('corrigir', {})
norm = lambda s: re.sub(r'[^\wÀ-ÿĀ-ž€$]', '', s).lower()
for w in words:
    core = re.sub(r'[^\wÀ-ÿĀ-ž€]', '', w['w'])
    if core in fix: w['w'] = w['w'].replace(core, fix[core])
def groups(lst): return [[norm(t) for t in h.split()] for h in lst]
hls = groups(cfg.get('destaques', [])); money = groups(cfg.get('dinheiro', []))
MONEY_W = re.compile(r'^(milh(ão|ões)|mil|bilh(ão|ões)|euros?|reais|dólares|r\$|€.*|\$.*)$', re.I)
# marca destaques/dinheiro por palavra
for lst, tag in ((money, 'money'), (hls, 'hl')):
    for i in range(len(words)):
        for h in sorted(lst, key=len, reverse=True):
            if [norm(x['w']) for x in words[i:i+len(h)]] == h:
                for x in words[i:i+len(h)]: x.setdefault('tag', tag)
for i, w in enumerate(words):   # dinheiro automático: número seguido de milhões/euros...
    n = words[i+1]['w'] if i + 1 < len(words) else ''
    if re.match(r'^\d', norm(w['w'])) and MONEY_W.match(norm(n)): w['tag'] = 'money'; words[i+1]['tag'] = 'money'
    if MONEY_W.match(norm(w['w'])) and i > 0 and words[i-1].get('tag') == 'money': w['tag'] = 'money'
    if norm(w['w']) == 'de' and i > 0 and words[i-1].get('tag') == 'money' and MONEY_W.match(norm(n)): w['tag'] = 'money'; words[i+1]['tag'] = 'money'
clean = lambda t: re.sub(r'[,;:.]+$', '', t) if not t.endswith('?') else t
caps = []
if not blocos:
    alt = 0
    for i, w in enumerate(words):
        t = clean(w['w']); tag = w.get('tag')
        if tag == 'hl':
            # alterna a cor a cada novo destaque (grupo)
            if i == 0 or words[i-1].get('tag') != 'hl': alt ^= 1
            t = f'*{t}*' if alt else f'^{t}^'
        elif tag == 'money': t = f'${t}$'
        nxt = words[i+1]['s'] if i + 1 < len(words) else w['e'] + 0.4
        caps.append({'t': w['s'], 'end': min(nxt, w['e'] + 0.35), 'text': t, 'sw': True})
else:
    raise SystemExit('modo --blocos removido; use o single-word')
sp = os.path.join(proj, 'spec.json'); spec = json.load(open(sp))
spec['captions'] = caps; spec['duration'] = round(words[-1]['e'] + 0.6, 2)
json.dump(spec, open(sp, 'w'), ensure_ascii=False, indent=1)
print(len(caps), 'legendas'); print(' '.join(c['text'] for c in caps))
