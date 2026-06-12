#!/usr/bin/env python3
"""まるっと運送採用LP 画像一括生成（gpt-image-2）
実行: set -a; source ~/Desktop/運送くん/.env; set +a; python3 scripts/gen_images.py
生成先: assets/_masters/ （後段で scripts/make_alpha.py が最終配置）"""
import os, json, base64, time, sys, pathlib, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed

ROOT = pathlib.Path(__file__).resolve().parent.parent
KEY = os.environ.get("OPENAI_API_KEY")
if not KEY:
    sys.exit("OPENAI_API_KEY not set")

MODEL = "gpt-image-2"

PHOTO = ("Photorealistic, professional Japanese commercial recruiting-advertisement "
         "photography, bright even lighting, vivid clean colors, sharp focus. "
         "No text, no letters, no logos, no watermark.")
CUTOUT = (PHOTO + " Subject isolated on a pure white #FFFFFF seamless studio "
          "background, whole subject fully inside the frame, centered composition.")
BCIRCLE = (" The subject is positioned in front of a single large soft pale-blue "
           "(#D6E9FF) flat circle backdrop; everything outside the circle is pure "
           "white #FFFFFF.")
FLAT = ("Simple flat vector-style corporate illustration, soft rounded geometry, "
        "smooth solid color fills, no outlines, faceless people without facial "
        "features, minimal clean detail, consistent corporate illustration set. "
        "Brand palette: primary blue #2E6FD0, navy #16243E, light blue #9FD4FF, "
        "blue-purple #7C8AF5, cyan #44DDF7, light gray #D8E2EC, skin tone #F4C9A3. "
        "No yellow or orange. No text, no letters, no watermark.")
WHITEBG = " Pure white #FFFFFF background."
MUTED = " Muted desaturated blue-gray clothing palette to express worry."

ITEMS = [
    # ---- 写真（マスター→jpg化） ----
    dict(path="assets/_masters/gen/fv-crowd.png", size="1536x1024", quality="high",
         prompt=("Wide group photo of eight cheerful Japanese logistics workers "
                 "celebrating toward the camera in front of white and blue delivery "
                 "trucks at a logistics depot under a clear blue sky: truck drivers "
                 "in crisp uniforms and caps, a sales driver, a young female "
                 "logistics manager holding a tablet, a warehouse staff member in a "
                 "safety vest, and a veteran driver. Everyone smiling broadly with "
                 "fists raised in triumph, a few holding plain blank blue placards "
                 "with nothing written on them. Slight low-angle hero shot, trucks "
                 "and loading docks softly blurred behind, sunny daylight, joyful "
                 "energetic mood. ") + PHOTO),
    dict(path="assets/_masters/gen/final-bg.png", size="1024x1536", quality="high",
         prompt=("Vertical photo of a Japanese truck driver in a clean navy uniform "
                 "and cap standing beside a large white truck at a logistics yard, "
                 "seen from a slight low angle, looking up toward the bright sky "
                 "with hope, rows of delivery trucks and a modern distribution "
                 "center softly blurred in the background, late afternoon light, "
                 "inspirational recruiting-advertisement mood, calm open sky in "
                 "the upper half of the frame. ") + PHOTO),
    # ---- 秘訣（水色サークル版） ----
    dict(path="assets/_masters/gen/secret-1.png", size="1024x1024", quality="high",
         prompt=("Upper-body shot of a smiling Japanese businesswoman in a black "
                 "suit holding a fanned-out spread of stylized fictional pale-green "
                 "prop banknotes in one hand (clearly fictional stage-prop money, "
                 "not real currency) and making an OK hand sign with the other "
                 "hand, joyful confident expression. ") + PHOTO + BCIRCLE),
    dict(path="assets/_masters/gen/secret-2.png", size="1024x1024", quality="high",
         prompt=("Upper-body shot of an astonished Japanese businessman in his "
                 "thirties in a dark suit staring at an open silver laptop in front "
                 "of him, jaw dropped in amazement, both hands raised beside his "
                 "head. ") + PHOTO + BCIRCLE),
    dict(path="assets/_masters/gen/secret-3.png", size="1024x1024", quality="high",
         prompt=("A relaxed middle-aged Japanese businessman in a gray suit leaning "
                 "back comfortably in a black office chair, hands clasped behind "
                 "his head, eyes closed with a contented smile. ") + PHOTO + BCIRCLE),
    # ---- 単価職種アイコン ----
    dict(path="assets/_masters/illust/job-ogata.png", size="1024x1024", quality="medium",
         prompt=("Bust illustration of a Japanese heavy-duty truck driver wearing "
                 "a navy cap and blue work uniform, one hand raised in a confident "
                 "thumbs-up, the white cab of a large truck visible behind his "
                 "shoulder. ") + FLAT + WHITEBG),
    dict(path="assets/_masters/illust/job-route.png", size="1024x1024", quality="medium",
         prompt=("Bust illustration of a friendly Japanese route-delivery driver "
                 "in a light blue uniform and cap, carrying a small stack of brown "
                 "cardboard boxes with both hands. ") + FLAT + WHITEBG),
    dict(path="assets/_masters/illust/job-chugata.png", size="1024x1024", quality="medium",
         prompt=("Bust illustration of a Japanese mid-size truck driver in a cyan "
                 "work uniform and cap holding a delivery clipboard, the front of "
                 "a small box truck visible behind the shoulder. ") + FLAT + WHITEBG),
    dict(path="assets/_masters/illust/job-souko.png", size="1024x1024", quality="medium",
         prompt=("Bust illustration of a Japanese warehouse staff member wearing a "
                 "light gray uniform, a cap and a blue safety vest, holding a "
                 "handheld barcode scanner, stacked cardboard boxes behind the "
                 "shoulder. ") + FLAT + WHITEBG),
    # ---- 実績イラスト ----
    dict(path="assets/_masters/illust/stat-chart.png", size="1536x1024", quality="medium",
         prompt=("Isometric flat illustration of a rising blue 3D bar chart with "
                 "three ascending bars standing on a light-blue isometric floor "
                 "tile, a small faceless business person beside it, and a bold "
                 "cyan upward swoosh arrow above the bars. ") + FLAT + WHITEBG),
    dict(path="assets/_masters/illust/stat-handshake.png", size="1536x1024", quality="medium",
         prompt=("Isometric flat illustration of two faceless people, one in a "
                 "navy suit and one truck driver in a blue uniform and cap, firmly "
                 "shaking hands while standing on a light-blue isometric floor "
                 "tile, a small light-blue sparkle above the joined hands. ")
                 + FLAT + WHITEBG),
    dict(path="assets/_masters/illust/stat-stars.png", size="1536x1024", quality="medium",
         prompt=("Isometric flat illustration of three faceless people, a suited "
                 "man, a truck driver in a blue uniform and cap, and a warehouse "
                 "worker in a safety vest, standing on a light-blue isometric "
                 "floor tile, each raising both arms to hold up a large shiny "
                 "silver-blue five-pointed star overhead. ") + FLAT + WHITEBG),
    # ---- 悩み人物1（ドライバー版） ----
    dict(path="assets/_masters/illust/worry-1.png", size="1024x1536", quality="medium",
         prompt=("Full-body illustration of a troubled faceless Japanese male "
                 "truck driver in a work uniform and cap, standing with one hand "
                 "on his chin in a worried thinking pose, shoulders slightly "
                 "dropped. ") + FLAT + MUTED + WHITEBG),
    # ---- 事例 仮イラスト（文字なしインタビューシーン） ----
    dict(path="assets/_masters/jirei/jirei-a.png", size="1536x1024", quality="medium",
         prompt=("Flat illustration of a friendly business interview scene: two "
                 "faceless Japanese men sitting across a small white table, one in "
                 "a navy suit listening, one truck driver in a blue uniform and "
                 "cap talking with one hand raised, a large white delivery truck "
                 "visible through the office window behind them. Bright modern "
                 "logistics-company office filling the whole frame in soft "
                 "light-blue and white tones. ") + FLAT),
    dict(path="assets/_masters/jirei/jirei-b.png", size="1536x1024", quality="medium",
         prompt=("Flat illustration of a friendly business interview scene: two "
                 "faceless Japanese people at a small white table, one in a dark "
                 "jacket listening, one warehouse manager in a safety vest talking "
                 "with one hand raised, tall warehouse shelves with cardboard "
                 "boxes behind them. Light gray-blue warehouse interior filling "
                 "the whole frame. ") + FLAT),
    dict(path="assets/_masters/jirei/jirei-c.png", size="1536x1024", quality="medium",
         prompt=("Flat illustration of a friendly business interview scene: two "
                 "faceless Japanese men sitting across a small white table, one in "
                 "a gray-blue jacket listening, one delivery driver in a cyan "
                 "uniform talking with one hand raised, several small delivery "
                 "vans parked in a depot visible behind them. Light cool-toned "
                 "delivery depot interior filling the whole frame. ") + FLAT),
]


def generate(item):
    out = ROOT / item["path"]
    if out.exists() and out.stat().st_size > 10_000:
        return f"SKIP {item['path']}"
    body = {
        "model": MODEL,
        "prompt": item["prompt"],
        "size": item["size"],
        "quality": item["quality"],
        "output_format": "png",
        "n": 1,
    }
    last = None
    for attempt in range(4):
        req = urllib.request.Request(
            "https://api.openai.com/v1/images/generations",
            data=json.dumps(body).encode(),
            headers={"Authorization": f"Bearer {KEY}",
                     "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=420) as r:
                d = json.load(r)
            b64 = d["data"][0]["b64_json"]
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_bytes(base64.b64decode(b64))
            kb = out.stat().st_size // 1024
            return f"OK   {item['path']} ({kb}KB)"
        except urllib.error.HTTPError as e:
            msg = e.read().decode()[:300]
            last = f"HTTP{e.code} {msg}"
            if e.code in (429, 500, 502, 503):
                time.sleep(8 * (attempt + 1))
                continue
            if e.code == 400 and "quality" in msg and body["quality"] != "auto":
                body["quality"] = "auto"
                continue
            break
        except Exception as e:
            last = repr(e)[:200]
            time.sleep(6 * (attempt + 1))
    return f"FAIL {item['path']} :: {last}"


with ThreadPoolExecutor(max_workers=3) as ex:
    futs = {ex.submit(generate, it): it for it in ITEMS}
    done = 0
    for f in as_completed(futs):
        done += 1
        print(f"[{done}/{len(ITEMS)}] {f.result()}", flush=True)

print("ALL DONE", flush=True)
