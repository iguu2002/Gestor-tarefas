# Gol Informado: identidade visual e gerador de vídeos

Gera Shorts/Reels verticais (1080×1920, 30fps) com a identidade do canal, sem editor de vídeo.
Tudo é renderizado em código: HTML/CSS animado no Chromium (Playwright), quadro a quadro, e montado com ffmpeg.

## Identidade visual

| Item | Definição |
|---|---|
| Paleta | **Dourado Troféu**: destaque `#FFC845`, fundo das cenas gráficas azul-marinho (`#070B18` → `#18234A`) com textura de linhas, vitória `#3DFF8B`, derrota `#FF3D57` |
| Legenda | **Padrão atual: sem legenda no vídeo** (`"noCaptions": true`); o canal coloca as legendas no CapCut. A marca d'água fica fixa embaixo. |
| Legenda (opcional, motor) | **Uma palavra por vez (single word)**, centralizada (um pouco abaixo do meio, desviando de rosto e escudo), Baloo 2 ExtraBold 128px, branca com contorno preto. Pop com rastro pequeno. Destaques alternam entre a cor do canal e a cor alternativa do vídeo (`altColor`); **dinheiro sempre em verde**. Gerada por `legendas.py`. |
| Títulos | Cor e peso variam com a cena: usar a cor do clube/foto (`"color": "vermelho"`, azul, grena, celeste...) e `"font": "black"` (Archivo Black, mais grossa) quando pedir mais impacto. Sempre cor sólida + glow da mesma cor. |
| Títulos (base) | Anton, dourado **sólido** com glow suave da mesma cor (nunca branco com brilho colorido). Entram com impacto (escala 1.35 → 1) |
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
- **Círculo aparece inteiro:** entra, segura e sai antes da troca de cena (o motor ajusta sozinho; se a cena for curta demais, não tem círculo). Nunca cortar a cena no meio da animação.
- **Lance de gol sempre até a bola na rede** antes de trocar de cena (conferir o trecho exato no vídeo).
- **Abertura aprovada pelo canal:** a 1ª cena entra com zoom + desfoque que vai revelando a imagem nas primeiras palavras. Manter; variar entre zoom-in (`"kb": "in"`) e zoom-out (`"kb": "out"`) de vídeo para vídeo.
- **Foto sempre preenche 100% da tela** (recorte + upscale). Foto pequena: `python3 engine/upscale.py foto.jpg saida.jpg` (Real-ESRGAN 4x, modelo em `engine/models/`). Nada de faixa desfocada em cima/embaixo nem card pequeno.
- **Nenhuma foto repetida no mesmo vídeo.** Se faltar imagem, pedir mais ao canal antes de montar.
- **Pessoa pouco conhecida** (dirigente, presidente): preferir vídeo de entrevista/lance em vez de foto parada.
- **Cards/gráficos ficam na tela até o fim da fala correspondente** (não cortar no meio para uma foto rápida).
- **SFX discretos**, bem abaixo da narração; whoosh só curto/suave (motion), nunca longo tipo onda.

**Regra de ouro:** nenhum elemento cobre o rosto do jogador. O gerador detecta rostos (face-api)
em cada foto e vídeo e posiciona título, figurinha, legenda e círculo nos espaços livres.

Guia de roteiro (estrutura, ganchos, marcações de cena): veja [`ROTEIRO.md`](ROTEIRO.md).

## Sons e transições do canal

- `engine/sfx/`: **marker** (lápis, sempre junto do círculo), **riser_metallic** (troca de cena logo depois do gancho; `"riser": true` na cena seguinte), whoosh1-3, pop1-2. Recortados dos packs enviados pelo canal.
- `engine/transicoes/`: film burn / light leak (laranja, azul, vermelho, amarelo), aplicados em modo *screen* no começo da cena com `"trans": "laranja"`. Usar em algumas trocas, não em todas; alternar com o punch-in. **Cada film burn toca o próprio som** (`sfx/burn_*.wav`), nunca whoosh por cima.
- **Todo valor em dinheiro falado leva card de número + caixa registradora**, inclusive no gancho.
- **Abertura sempre com o zoom desfocado + som de zoom (whoosh)** — automático na 1ª cena (`"kb": "in"` ou `"out"` alterna o sentido).
- **Dinheiro/salário → som de caixa registradora** (`sfx/cash.wav` e `sfx/cash2.wav`, enviados pelo canal, alternando): toca sozinho em cards de número com €, R$, milhões, salário, euros.
- **Whoosh só em parte das trocas** (nem toda troca tem som). Efeitos sempre discretos, abaixo da narração.

## Trilha e efeitos extras

- `engine/musica/`: trilhas hip hop enviadas pelo canal (talk, alias, where_the_trap_is). Alternar entre vídeos com `"music": "talk"` no spec. Fica baixa (`musicVolume`, padrão 0.10) e abaixa sozinha quando a narração fala (ducking).
- `sfx/vineboom.wav`: Vine Boom, só em momento de impacto (`{"type":"sfx","k":"vineboom","t":...}`), volume bem baixo. Opcional, charme.

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
