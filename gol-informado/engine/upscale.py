"""Melhora (upscale 4x) fotos pequenas com Real-ESRGAN (realesr-general-x4v3, ONNX).
Uso: python3 upscale.py foto.jpg [saida.jpg]   (padrão: sobrescreve com sufixo _hd)"""
import sys, os, numpy as np, onnxruntime as ort
from PIL import Image
src = sys.argv[1]; out = sys.argv[2] if len(sys.argv) > 2 else os.path.splitext(src)[0] + '_hd.jpg'
sess = ort.InferenceSession(os.path.join(os.path.dirname(__file__), 'models', 'realesr-general-x4v3.onnx'))
im = np.asarray(Image.open(src).convert('RGB')).astype(np.float32) / 255.0
H, W, _ = im.shape; T, P = 256, 16; res = np.zeros((H * 4, W * 4, 3), np.float32)
for y in range(0, H, T):
    for x in range(0, W, T):
        y0, x0, y1, x1 = max(0, y - P), max(0, x - P), min(H, y + T + P), min(W, x + T + P)
        tile = im[y0:y1, x0:x1].transpose(2, 0, 1)[None]
        o = sess.run(None, {'input': tile})[0][0].transpose(1, 2, 0)
        oy, ox = (y - y0) * 4, (x - x0) * 4; h, w = (min(y + T, H) - y) * 4, (min(x + T, W) - x) * 4
        res[y * 4:y * 4 + h, x * 4:x * 4 + w] = o[oy:oy + h, ox:ox + w]
Image.fromarray((np.clip(res, 0, 1) * 255).round().astype(np.uint8)).save(out, quality=94)
print(out, res.shape[1], 'x', res.shape[0])
