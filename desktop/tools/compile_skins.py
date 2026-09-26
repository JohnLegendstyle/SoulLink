"""Convert Imagegen sheets to DS I4 textures; never reads a game ROM.

Development only: Pillow is not needed by the distributed application.
"""
import json
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[1] / 'assets' / 'skins'


def compile_sheet(name):
    source = Image.open(ROOT / f'{name}-source.png').convert('RGBA')
    frames = []
    for row in range(4):
        for column in range(4):
            column = 0 if column == 2 else column
            cell = source.crop(tuple(round(v) for v in (
                column * source.width / 4, row * source.height / 4,
                (column + 1) * source.width / 4, (row + 1) * source.height / 4)))
            frames.append(cell.resize((32, 32), Image.Resampling.NEAREST))
    opaque = [rgb[:3] for frame in frames for rgb in frame.getdata() if rgb[3] >= 128]
    colors = Image.new('RGB', (len(opaque), 1))
    colors.putdata(opaque)
    quantized = colors.quantize(colors=15, method=Image.Quantize.MEDIANCUT)
    palette8 = [tuple(quantized.getpalette()[i:i+3]) for i in range(0, 45, 3)]
    palette5 = [[0, 0, 0]] + [[round(c * 31 / 255) for c in rgb] for rgb in palette8]
    encoded = []
    preview = Image.new('RGBA', (128, 128))
    for index, frame in enumerate(frames):
        pixels = []
        for r, g, b, a in frame.getdata():
            pixels.append(0 if a < 128 else 1 + min(range(15), key=lambda i:
                sum((x-y)**2 for x, y in zip((r,g,b), palette8[i]))))
        encoded.append(bytes(pixels[i] | pixels[i+1] << 4 for i in range(0, 1024, 2)).hex())
        rendered = Image.new('RGBA', (32,32))
        rendered.putdata([tuple(round(c*255/31) for c in palette5[p]) + (255 if p else 0,) for p in pixels])
        preview.paste(rendered, ((index%4)*32, (index//4)*32))
    (ROOT / f'{name}.json').write_text(json.dumps({'format':1,'size':32,'palette':palette5,'frames':encoded}, separators=(',',':'))+'\n')
    preview.resize((512,512),Image.Resampling.NEAREST).save(ROOT / f'{name}-preview.png')


if __name__ == '__main__':
    for name in ('optimus-prime','bumblebee'):
        compile_sheet(name)
