# Gol Informado: identidade visual e gerador de vídeos

Gera Shorts/Reels verticais (1080×1920, 30fps) com a identidade do canal, sem editor de vídeo.
Tudo é renderizado em código: HTML/CSS animado no Chromium (Playwright), quadro a quadro, e montado com ffmpeg.

## Identidade visual

| Item | Definição |
|---|---|
| Paleta | **Dourado Troféu**: destaque `#FFC845`, fundo das cenas gráficas azul-marinho (`#070B18` → `#18234A`) com textura de linhas, vitória `#3DFF8B`, derrota `#FF3D57` |
| Legenda | Palavra por palavra (1 a 3 palavras), Baloo 2 ExtraBold, branca com contorno preto, palavra-chave em dourado sólido com glow suave. Entra com "pop" leve |
| Títulos | Anton, dourado **sólido** com glow suave da mesma cor (nunca branco com brilho colorido). Entram com impacto (escala 1.35 → 1) |
| Marca d'água | `GOL INFORMADO`, Archivo Black, branca com 26% de opacidade, abaixo da legenda |
| Figurinha | Bandeira/imagem em cartão branco arredondado, borda dourada, pop com overshoot e leve flutuação |
| Círculo | **Só para chamar atenção**: na primeira menção do jogador (rosto) ou num detalhe citado (ex.: escudo do time novo). **Anel redondo (nunca oval), grosso, em cor sólida e viva** (dourado, roxo, azul, verde, vermelho, laranja, ciano, rosa; varia de vídeo para vídeo com `"ringColor"` no spec ou `"color"` no efeito), com brilho discreto só de charme. Aparece em "relógio" a partir das 12h em 0,75s, **começando lento e terminando rápido** (tipo time remapping), fica ~1,6s, some |
| Pixelado | Único efeito permitido sobre o rosto: esconder o jogador até a revelação |
| Câmera | Zoom lento em toda cena + "punch" de zoom com desfoque na troca de cena |
| Sons | Whoosh nas transições, pop nas figurinhas, batida no placar e no título |

**Regras do canal (aprendidas nos vídeos):**
- **Círculo só em foto**, nunca em vídeo (em vídeo o rosto se mexe e o círculo fica "bugado").
- **Não repetir o mesmo trecho de vídeo** no mesmo Short. Cada clipe aparece uma vez; se faltar material, pedir mais vídeos ao canal.
- **Não repetir a mesma foto** em cenas seguidas; no máximo 2 vezes no vídeo, com enquadramento diferente.
- **Sem tela dividida.**

**Regra de ouro:** nenhum elemento cobre o rosto do jogador. O gerador detecta rostos (face-api)
em cada foto e vídeo e posiciona título, figurinha, legenda e círculo nos espaços livres.

Guia de roteiro (estrutura, ganchos, marcações de cena): veja [`ROTEIRO.md`](ROTEIRO.md).

## Como produzir um vídeo

1. Criar `projetos/<nome-do-video>/` com `media/` (fotos e vídeos) e um `spec.json`.
2. Rodar:

```bash
cd engine
npm install          # primeira vez (Playwright e ffmpeg precisam estar instalados no sistema)
node build.js ../projetos/<nome-do-video>
```

O vídeo sai em `projetos/<nome-do-video>/video.mp4`.


### Narração e legenda

```bash
python3 transcrever.py ../projetos/<video>            # tempo de cada palavra
python3 cortar_silencios.py ../projetos/<video>       # opcional: corta pausas longas e reajusta tudo
python3 legendas.py ../projetos/<video>               # legenda palavra por palavra (destaques em legenda.json)
node build.js ../projetos/<video>
```

## Formato do `spec.json`

Veja `projetos/exemplo/spec.json`. Cada cena tem:

- `dur`: duração em segundos.
- `bg`: fundo da cena.
  - `{ "type": "photo", "src": "media/x.jpg", "kb": "in" | "out" }`
  - `{ "type": "clip", "src": "media/x.mp4", "start": 12.5 }`
  - `{ "type": "board", "tag": "LIGA DAS NAÇÕES", "home": {"name","flag","score"}, "away": {...} }` (placar animado; `flag` = código do país, ex. `br`, `no`)
- `caps`: legendas `{ "t": segundos, "text": "texto com *destaque*" }`. Cada uma fica até a próxima.
- `fx`: efeitos.
  - `{ "type": "sticker", "t": 1.3, "flag": "no", "label": "NORUEGA" }`
  - `{ "type": "circle", "t": 1.3, "target": "face" }`
  - `{ "type": "title", "t": 1.6, "text": "FRIEZA" }`
  - `{ "type": "pixelate", "until": 1.25 }`

Mídia de terceiros (fotos e lances) não vai para o repositório (`.gitignore`).
