#!/usr/bin/env python3
"""まるっと建設採用LP 画像一括生成（gpt-image-2）

- OPENAI_API_KEY は環境変数から読む（実行例は下記）
- 既に生成済み（>10KB）のファイルはスキップ＝何度でも再実行OK
- 白背景で生成し、LP側は mix-blend-mode: multiply で白を溶かす設計

実行:
  set -a; source ~/Desktop/運送くん/.env; set +a
  python3 scripts/gen_images.py
"""
import os, json, base64, time, sys, pathlib, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed

ROOT = pathlib.Path(__file__).resolve().parent.parent
KEY = os.environ.get("OPENAI_API_KEY")
if not KEY:
    sys.exit("OPENAI_API_KEY not set")

MODEL = "gpt-image-2"

PHOTO = ("Photorealistic, professional Japanese commercial recruiting-advertisement "
         "photography, bright even studio lighting, vivid clean colors, sharp focus. "
         "No text, no letters, no logos, no watermark.")
CUTOUT = (PHOTO + " Subject isolated on a pure white #FFFFFF seamless studio "
          "background, whole subject fully inside the frame, centered composition.")
YCIRCLE = (" The subject is positioned in front of a single large soft pale-yellow "
           "(#FDF6B5) flat circle backdrop; everything outside the circle is pure "
           "white #FFFFFF.")
FLAT = ("Simple flat vector-style corporate illustration, soft rounded geometry, "
        "smooth solid color fills, no outlines, faceless people without facial "
        "features, minimal clean detail, consistent corporate illustration set. "
        "Brand palette: primary blue #2E6FD0, navy #16243E, accent yellow #F7C703, "
        "teal #2EC4B6, light blue #D8E6F4, skin tone #F4C9A3. "
        "No text, no letters, no watermark.")
WHITEBG = " Pure white #FFFFFF background."
MUTED = " Muted desaturated blue-gray clothing palette to express worry."

ITEMS = [
    # ---- 写真スロット（gen/）----
    dict(path="assets/gen/fv-crowd.png", size="1536x1024", quality="high",
         prompt=("Wide group photo of eight cheerful Japanese construction-industry "
                 "workers celebrating toward the camera under a bright clear blue sky "
                 "at a construction site: a site manager in a navy suit with a white "
                 "safety helmet, male construction workers in gray and teal work "
                 "uniforms with helmets, an electrician with a tool belt, a young "
                 "female site engineer holding a tablet, and a veteran foreman. "
                 "Everyone smiling broadly with fists raised in triumph, a few "
                 "holding plain blank blue placards with nothing written on them. "
                 "Slight low-angle hero shot, scaffolding and a tower crane softly "
                 "blurred behind, sunny daylight, joyful energetic mood. ") + PHOTO),
    dict(path="assets/gen/cta-woman.png", size="1024x1536", quality="high",
         prompt=("Upper-body shot of a cheerful Japanese businesswoman in her late "
                 "twenties wearing a navy suit over a white blouse, neat short bob "
                 "hair, looking at the camera with a big bright smile, pointing "
                 "upward to her upper right with her index finger as if presenting "
                 "a special offer. ") + CUTOUT),
    dict(path="assets/gen/solution-woman.png", size="1024x1024", quality="high",
         prompt=("Upper-body shot of a delighted, surprised Japanese businesswoman "
                 "in her twenties in a dark suit, mouth open in a joyful gasp, eyes "
                 "wide with excitement, both hands spread open beside her face with "
                 "palms facing forward. ") + CUTOUT),
    dict(path="assets/gen/secret-1.png", size="1024x1024", quality="high",
         prompt=("Upper-body shot of a smiling Japanese businesswoman in a black "
                 "suit holding a fanned-out spread of stylized fictional pale-green "
                 "prop banknotes in one hand (clearly fictional stage-prop money, "
                 "not real currency) and making an OK hand sign with the other "
                 "hand, joyful confident expression. ") + PHOTO + YCIRCLE),
    dict(path="assets/gen/secret-2.png", size="1024x1024", quality="high",
         prompt=("Upper-body shot of an astonished Japanese businessman in his "
                 "thirties in a dark suit staring at an open silver laptop in front "
                 "of him, jaw dropped in amazement, both hands raised beside his "
                 "head. ") + PHOTO + YCIRCLE),
    dict(path="assets/gen/secret-3.png", size="1024x1024", quality="high",
         prompt=("A relaxed middle-aged Japanese businessman in a gray suit leaning "
                 "back comfortably in a black office chair, hands clasped behind "
                 "his head, eyes closed with a contented smile. ") + PHOTO + YCIRCLE),
    dict(path="assets/gen/plan-duo.png", size="1536x1024", quality="high",
         prompt=("Waist-up shot of two cheerful Japanese business people standing "
                 "side by side, a man in a navy suit and a woman in a dark jacket, "
                 "both smiling at the camera and giving enthusiastic double "
                 "thumbs-up, light airy pale-cyan studio background with soft "
                 "celebratory confetti bokeh. ") + PHOTO),
    # ---- 単価アイコン（illust/）----
    dict(path="assets/illust/job-sekkan.png", size="1024x1024", quality="medium",
         prompt=("Bust illustration of a Japanese construction site manager wearing "
                 "a white safety helmet and a navy work jacket over a white shirt, "
                 "holding a clipboard. ") + FLAT + WHITEBG),
    dict(path="assets/illust/job-genba.png", size="1024x1024", quality="medium",
         prompt=("Bust illustration of a construction field worker wearing a yellow "
                 "safety helmet and a teal work uniform, carrying an orange lumber "
                 "beam on one shoulder. ") + FLAT + WHITEBG),
    dict(path="assets/illust/job-denki.png", size="1024x1024", quality="medium",
         prompt=("Bust illustration of an electrician wearing a white safety helmet "
                 "with a blue stripe and a gray-blue work uniform, holding a coiled "
                 "cable, a yellow lightning bolt symbol floating beside the "
                 "shoulder. ") + FLAT + WHITEBG),
    dict(path="assets/illust/job-cad.png", size="1024x1024", quality="medium",
         prompt=("Bust illustration of a female CAD operator with dark bob hair "
                 "sitting behind a large monitor that displays a simple white "
                 "architectural blueprint line drawing on a blue screen. ")
                 + FLAT + WHITEBG),
    # ---- 実績イラスト（illust/）----
    dict(path="assets/illust/stat-chart.png", size="1536x1024", quality="medium",
         prompt=("Isometric flat illustration of a rising blue 3D bar chart with "
                 "three ascending bars standing on a light-blue isometric floor "
                 "tile, a small faceless business person beside it, and a bold "
                 "golden upward swoosh arrow above the bars. ") + FLAT + WHITEBG),
    dict(path="assets/illust/stat-handshake.png", size="1536x1024", quality="medium",
         prompt=("Isometric flat illustration of two faceless business people, one "
                 "in a navy suit and one in a blue work uniform with a white safety "
                 "helmet, firmly shaking hands while standing on a light-blue "
                 "isometric floor tile, a small golden sparkle above the joined "
                 "hands. ") + FLAT + WHITEBG),
    dict(path="assets/illust/stat-stars.png", size="1536x1024", quality="medium",
         prompt=("Isometric flat illustration of three faceless people, a suited "
                 "man, a worker with a white helmet, and a craftsman in teal "
                 "overalls, standing on a light-blue isometric floor tile, each "
                 "raising both arms to hold up a large golden five-pointed star "
                 "overhead. ") + FLAT + WHITEBG),
    # ---- 悩み人物（illust/）----
    dict(path="assets/illust/worry-1.png", size="1024x1536", quality="medium",
         prompt=("Full-body illustration of a troubled faceless Japanese male "
                 "construction worker in a work shirt and work pants, standing with "
                 "one hand on his chin in a worried thinking pose, shoulders "
                 "slightly dropped. ") + FLAT + MUTED + WHITEBG),
    dict(path="assets/illust/worry-2.png", size="1024x1536", quality="medium",
         prompt=("Full-body illustration of a troubled faceless Japanese office "
                 "woman in a blouse and skirt, standing with one hand on her cheek "
                 "and head tilted in worry. ") + FLAT + MUTED + WHITEBG),
    dict(path="assets/illust/worry-3.png", size="1024x1536", quality="medium",
         prompt=("Full-body illustration of a troubled faceless older Japanese "
                 "company president in a suit, standing with arms crossed and head "
                 "lowered slightly in worry. ") + FLAT + MUTED + WHITEBG),
    # ---- 事例シーン（illust/）----
    dict(path="assets/illust/voice-a.png", size="1536x1024", quality="medium",
         prompt=("Flat illustration of a friendly business interview scene: two "
                 "faceless Japanese men sitting across a small white table, one in "
                 "a navy suit listening, one in a blue work uniform talking with "
                 "one hand raised, a white construction safety helmet placed on "
                 "the table. Bright modern construction-company office background "
                 "with large windows filling the whole frame in soft light-blue "
                 "and white tones. ") + FLAT),
    dict(path="assets/illust/voice-b.png", size="1536x1024", quality="medium",
         prompt=("Flat illustration of a friendly business interview scene: two "
                 "faceless Japanese men sitting across a small white table, one in "
                 "a dark jacket listening, one craftsman in a teal coverall talking "
                 "with one hand raised, a flat tool board with wrench and pliers "
                 "silhouettes on the wall behind. Warm light-beige workshop "
                 "interior filling the whole frame. ") + FLAT),
    dict(path="assets/illust/voice-c.png", size="1536x1024", quality="medium",
         prompt=("Flat illustration of a friendly business interview scene: two "
                 "faceless Japanese men sitting across a small white table, one in "
                 "a gray-blue jacket listening, one carpenter in a navy traditional "
                 "work jacket talking with one hand raised, a simple wooden house "
                 "frame structure and stacked lumber behind them. Light warm "
                 "carpentry-workshop interior filling the whole frame. ") + FLAT),
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
            # パラメータ非対応はqualityフォールバック
            if e.code == 400 and "quality" in msg and body["quality"] != "auto":
                body["quality"] = "auto"
                continue
            break
        except Exception as e:  # timeout等
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
