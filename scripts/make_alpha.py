#!/usr/bin/env python3
"""マスターPNGから本物の透過PNGを作る（multiply合成の白枠問題の根治）
外周からのflood-fillで「背景に連結した白」だけをアルファ0にする。
被写体内部の白（白シャツ・ヘルメット等）は保護される。"""
from PIL import Image, ImageDraw, ImageFilter
import pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
M = ROOT / 'assets' / '_masters'

JOBS = [
    # (master, out, width, thresh)
    ('gen/cta-woman.png',      'assets/gen/cta-woman.png',      640, 28),
    ('gen/solution-woman.png', 'assets/gen/solution-woman.png', 640, 28),
    ('gen/secret-1.png',       'assets/gen/secret-1.png',       680, 24),
    ('gen/secret-2.png',       'assets/gen/secret-2.png',       680, 24),
    ('gen/secret-3.png',       'assets/gen/secret-3.png',       680, 24),
    ('illust/job-sekkan.png',  'assets/illust/job-sekkan.png',  240, 24),
    ('illust/job-genba.png',   'assets/illust/job-genba.png',   240, 24),
    ('illust/job-denki.png',   'assets/illust/job-denki.png',   240, 24),
    ('illust/job-cad.png',     'assets/illust/job-cad.png',     240, 24),
    ('illust/stat-chart.png',  'assets/illust/stat-chart.png',  520, 24),
    ('illust/stat-handshake.png', 'assets/illust/stat-handshake.png', 520, 24),
    ('illust/stat-stars.png',  'assets/illust/stat-stars.png',  520, 24),
    ('illust/worry-1.png',     'assets/illust/worry-1.png',     400, 24),
    ('illust/worry-2.png',     'assets/illust/worry-2.png',     400, 24),
    ('illust/worry-3.png',     'assets/illust/worry-3.png',     400, 24),
]

MAGENTA = (255, 0, 255)

for src, dst, w, thresh in JOBS:
    im = Image.open(M / src).convert('RGB')
    ratio = w / im.width
    im = im.resize((w, round(im.height * ratio)), Image.LANCZOS)
    # 1px白枠を足して四隅が必ず背景に連結するようにする
    bordered = Image.new('RGB', (im.width + 2, im.height + 2), (255, 255, 255))
    bordered.paste(im, (1, 1))
    ImageDraw.floodfill(bordered, (0, 0), MAGENTA, thresh=thresh)
    px = bordered.load()
    mask = Image.new('L', bordered.size, 255)
    mp = mask.load()
    for y in range(bordered.height):
        for x in range(bordered.width):
            if px[x, y] == MAGENTA:
                mp[x, y] = 0
    mask = mask.filter(ImageFilter.GaussianBlur(0.7))
    out = Image.new('RGBA', bordered.size)
    out.paste(im, (1, 1))
    out.putalpha(mask)
    out = out.crop((1, 1, 1 + im.width, 1 + im.height))
    outp = ROOT / dst
    out.save(outp)
    # 透過率レポート（背景が抜けたかの確認）
    a = out.getchannel('A')
    transparent = sum(1 for v in a.getdata() if v < 16)
    print(f"{dst}  {out.width}x{out.height}  transparent={transparent*100//(out.width*out.height)}%")
print("DONE")
