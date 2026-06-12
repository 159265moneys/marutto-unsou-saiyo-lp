#!/usr/bin/env python3
"""運送版: マスターPNG→透過PNG（外周flood-fill）＋JPEG最適化＋旧アセット掃除"""
from PIL import Image, ImageDraw, ImageFilter
import pathlib, subprocess, os

ROOT = pathlib.Path(__file__).resolve().parent.parent
M = ROOT / 'assets' / '_masters'

ALPHA_JOBS = [
    ('gen/secret-1.png',  'assets/gen/secret-1.png',  680, 24),
    ('gen/secret-2.png',  'assets/gen/secret-2.png',  680, 24),
    ('gen/secret-3.png',  'assets/gen/secret-3.png',  680, 24),
    ('illust/job-ogata.png',   'assets/illust/job-ogata.png',   240, 24),
    ('illust/job-route.png',   'assets/illust/job-route.png',   240, 24),
    ('illust/job-chugata.png', 'assets/illust/job-chugata.png', 240, 24),
    ('illust/job-souko.png',   'assets/illust/job-souko.png',   240, 24),
    ('illust/stat-chart.png',     'assets/illust/stat-chart.png',     520, 24),
    ('illust/stat-handshake.png', 'assets/illust/stat-handshake.png', 520, 24),
    ('illust/stat-stars.png',     'assets/illust/stat-stars.png',     520, 24),
    ('illust/worry-1.png', 'assets/illust/worry-1.png', 400, 24),
]

JPEG_JOBS = [
    ('gen/fv-crowd.png', 'assets/gen/fv-crowd.jpg', 1536, 82),
    ('gen/final-bg.png', 'assets/gen/final-bg.jpg', 1400, 84),
    ('jirei/jirei-a.png', 'assets/jirei/jirei-a.jpg', 1320, 84),
    ('jirei/jirei-b.png', 'assets/jirei/jirei-b.jpg', 1320, 84),
    ('jirei/jirei-c.png', 'assets/jirei/jirei-c.jpg', 1320, 84),
]

REMOVE = [
    'assets/illust/job-sekkan.png', 'assets/illust/job-genba.png',
    'assets/illust/job-denki.png', 'assets/illust/job-cad.png',
    'assets/construction-hero.png', 'assets/hero-direct.png',
]

for src, dst, w, thresh in ALPHA_JOBS:
    im = Image.open(M / src).convert('RGB')
    im = im.resize((w, round(im.height * w / im.width)), Image.LANCZOS)
    bordered = Image.new('RGB', (im.width + 2, im.height + 2), (255, 255, 255))
    bordered.paste(im, (1, 1))
    ImageDraw.floodfill(bordered, (0, 0), (255, 0, 255), thresh=thresh)
    px = bordered.load()
    mask = Image.new('L', bordered.size, 255)
    mp = mask.load()
    for y in range(bordered.height):
        for x in range(bordered.width):
            if px[x, y] == (255, 0, 255):
                mp[x, y] = 0
    mask = mask.filter(ImageFilter.GaussianBlur(0.7))
    out = Image.new('RGBA', bordered.size)
    out.paste(im, (1, 1))
    out.putalpha(mask)
    out = out.crop((1, 1, 1 + im.width, 1 + im.height))
    (ROOT / dst).parent.mkdir(parents=True, exist_ok=True)
    out.save(ROOT / dst)
    a = out.getchannel('A')
    tr = sum(1 for v in a.getdata() if v < 16) * 100 // (out.width * out.height)
    print(f"ALPHA {dst} {out.width}x{out.height} transparent={tr}%")

for src, dst, w, q in JPEG_JOBS:
    subprocess.run(['sips', '-s', 'format', 'jpeg', '-s', 'formatOptions', str(q),
                    '-Z', str(w), str(M / src), '--out', str(ROOT / dst)],
                   check=True, capture_output=True)
    kb = (ROOT / dst).stat().st_size // 1024
    print(f"JPEG  {dst} ({kb}KB)")

for r in REMOVE:
    p = ROOT / r
    if p.exists():
        p.unlink()
        print(f"RM    {r}")

print("FINALIZE DONE")
