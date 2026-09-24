#!/usr/bin/env python3
"""
Terminal-style GitHub profile card generator.
Builds dark.svg + light.svg: ASCII portrait (left) + neofetch-style info (right),
with live GitHub stats. Only dependency: Pillow  (pip install pillow)
"""
import os, json, datetime, urllib.request
from xml.sax.saxutils import escape
from PIL import Image, ImageOps, ImageEnhance

# ===================== EDIT THIS BLOCK =====================
GITHUB_USER = "pradip25215-sudo"
PHOTO       = "photo.jpg"
PROMPT      = "pradip@iiitd"
ASCII_COLS  = 60          # width of the portrait in characters
CONTRAST    = 1.0         # raise if the face looks washed out

INFO = [
    ("header",  "pradip@computational-bio"),
    ("kv", "Name",       "Pradip Palekar"),
    ("kv", "Role",       "M.Tech Computational Biology"),
    ("kv", "Institute",  "IIIT Delhi (2025-2027)"),
    ("kv", "Lab",        "Computational Genomics, Dr. Vibhor Kumar"),
    ("kv", "Focus",      "AI for drug discovery & cancer genomics"),
    ("kv", "Status",     "Open to work + building + learning"),
    ("gap",),
    ("kv", "Languages",  "Python, R, SQL, Bash"),
    ("kv", "Deep Learn", "PyTorch, TensorFlow, Transformers"),
    ("kv", "LLM / NLP",  "BioBERT, ESM-2, Whisper, GNNs"),
    ("kv", "Bioinfo",    "Scanpy, RDKit, BioPython, Trinity"),
    ("kv", "Infra",      "Linux, HPC, Git, Colab"),
    ("gap",),
    ("section", "Contact"),
    ("kv", "Email",      "pradip25215@iiitd.ac.in"),
    ("kv", "GitHub",     f"github.com/{GITHUB_USER}"),
    ("gap",),
    ("section", "Live stats"),
    ("stats",),
]
# ===========================================================

THEMES = {
    "dark": dict(bg="#0d1117", panel="#0b1220", edge="#1f2a3a", g1="#8b5cf6", g2="#22d3ee",
                 text="#c9d1d9", key="#a78bfa", dots="#2d3748", head="#22d3ee",
                 sect="#f472b6", ascii="#7dd3fc", muted="#6e7681", scan="#22d3ee"),
    "light": dict(bg="#ffffff", panel="#f6f8fa", edge="#d0d7de", g1="#7c3aed", g2="#0891b2",
                  text="#1f2328", key="#6d28d9", dots="#c9d1d9", head="#0e7490",
                  sect="#be185d", ascii="#1e3a5f", muted="#57606a", scan="#0891b2"),
}

RAMP = " .:-=+*#%@"
FS_A, CW_A, LH_A = 10, 6.0, 11      # ascii font size, char width, line height
FS_I, CW_I, LH_I = 13, 7.8, 21      # info font size, char width, line height
INFO_CHARS = 64
W, LEFT_W, PAD = 1000, 400, 20


def fetch_stats(user):
    headers = {"User-Agent": "profile-card", "Accept": "application/vnd.github+json"}
    if os.getenv("GITHUB_TOKEN"):
        headers["Authorization"] = f"Bearer {os.environ['GITHUB_TOKEN']}"
    def get(url):
        with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=20) as r:
            return json.load(r)
    try:
        u = get(f"https://api.github.com/users/{user}")
        stars, page = 0, 1
        while True:
            repos = get(f"https://api.github.com/users/{user}/repos?per_page=100&page={page}")
            if not repos:
                break
            stars += sum(r["stargazers_count"] for r in repos if not r.get("fork"))
            page += 1
        return dict(repos=u["public_repos"], stars=stars, followers=u["followers"])
    except Exception as e:
        print("! stats fetch failed:", e)
        return dict(repos="-", stars="-", followers="-")


def image_to_ascii(path, cols, invert):
    img = ImageOps.exif_transpose(Image.open(path)).convert("L")
    img = ImageEnhance.Contrast(ImageOps.autocontrast(img)).enhance(CONTRAST)
    w, h = img.size
    rows = max(1, round(h / w * cols * (CW_A / LH_A)))
    img = img.resize((cols, rows))
    pix = img.load()
    n = len(RAMP)
    out = []
    for r in range(rows):
        line = ""
        for c in range(cols):
            v = pix[c, r] / 256
            v = 1 - v if invert else v          # dense chars = bright on dark bg
            line += RAMP[min(n - 1, int(v * n))]
        out.append(line)
    return out


def kv_line(key, val):
    val = val[: INFO_CHARS - len(key) - 5]
    dots = max(3, INFO_CHARS - len(key) - len(val) - 2)
    return [("k", key + " "), ("d", "." * dots), ("v", " " + val)]


def build_info(stats):
    lines = []
    for item in INFO:
        kind = item[0]
        if kind == "header":
            lines += [[("h", item[1])], [("d", "-" * len(item[1]))]]
        elif kind == "section":
            lines.append([("s", "- " + item[1])])
        elif kind == "kv":
            lines.append(kv_line(item[1], item[2]))
        elif kind == "gap":
            lines.append([])
        elif kind == "stats":
            lines.append(kv_line("Repos", str(stats["repos"])))
            lines.append(kv_line("Stars", str(stats["stars"])))
            lines.append(kv_line("Followers", str(stats["followers"])))
            lines.append(kv_line("Updated", datetime.date.today().isoformat()))
    lines.append([])
    lines.append([("h", f"{PROMPT}:~$ "), ("cursor", "\u2588")])
    return lines


def render(theme, ascii_lines, info_lines):
    t = THEMES[theme]
    top = 52
    ascii_h = len(ascii_lines) * LH_A
    info_h = len(info_lines) * LH_I
    ph = max(ascii_h, info_h) + 56
    H = top + ph + PAD
    rx0, rw = PAD + LEFT_W + PAD, W - LEFT_W - 3 * PAD
    ax = PAD + (LEFT_W - ASCII_COLS * CW_A) / 2
    ay = top + 40 + (ph - 56 - ascii_h) / 2

    s = [f'<svg xmlns="http://www.w3.org/2000/svg" xml:space="preserve" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
         f'''<defs>
  <linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{t["g1"]}"/><stop offset="1" stop-color="{t["g2"]}"/></linearGradient>
  <linearGradient id="sl" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{t["scan"]}" stop-opacity="0"/><stop offset=".5" stop-color="{t["scan"]}" stop-opacity=".55"/><stop offset="1" stop-color="{t["scan"]}" stop-opacity="0"/></linearGradient>
  <filter id="glow" x="-5%" y="-5%" width="110%" height="110%"><feGaussianBlur stdDeviation="5"/></filter>
  <clipPath id="lc"><rect x="{PAD}" y="{top}" width="{LEFT_W}" height="{ph}" rx="10"/></clipPath>
</defs>
<style>
  text {{ font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, "Liberation Mono", monospace; white-space: pre; }}
  .a {{ fill: {t["ascii"]}; font-size: {FS_A}px; }}
  .i {{ font-size: {FS_I}px; }}
  .k {{ fill: {t["key"]}; font-weight: 600; }} .d {{ fill: {t["dots"]}; }} .v {{ fill: {t["text"]}; }}
  .h {{ fill: {t["head"]}; font-weight: 700; }} .s {{ fill: {t["sect"]}; font-weight: 700; }}
  .lbl {{ fill: {t["muted"]}; font-size: 10px; letter-spacing: 1px; }}
  .ttl {{ fill: {t["muted"]}; font-size: 12px; }}
  .ln {{ animation: in .35s ease both; }}
  .scan {{ animation: scan 3.5s linear infinite; }}
  .cur {{ fill: {t["head"]}; animation: blink 1s step-end infinite; }}
  @keyframes in {{ from {{ opacity: 0; }} to {{ opacity: 1; }} }}
  @keyframes scan {{ from {{ transform: translateY(0); }} to {{ transform: translateY({ph}px); }} }}
  @keyframes blink {{ 50% {{ opacity: 0; }} }}
  @media (prefers-reduced-motion: reduce) {{ .scan, .cur {{ animation: none; }} .ln {{ animation: none; }} }}
</style>''',
         f'<rect x="4" y="4" width="{W-8}" height="{H-8}" rx="16" fill="none" stroke="url(#g)" stroke-width="4" filter="url(#glow)" opacity=".7"/>',
         f'<rect x="4" y="4" width="{W-8}" height="{H-8}" rx="16" fill="{t["bg"]}" stroke="url(#g)" stroke-width="1.5"/>',
         '<circle cx="28" cy="28" r="6" fill="#ff5f57"/><circle cx="48" cy="28" r="6" fill="#febc2e"/><circle cx="68" cy="28" r="6" fill="#28c840"/>',
         f'<text x="{W/2}" y="32" text-anchor="middle" class="ttl">{escape(PROMPT)}: ~/profile.sh --live</text>',
         # panels
         f'<rect x="{PAD}" y="{top}" width="{LEFT_W}" height="{ph}" rx="10" fill="{t["panel"]}" stroke="{t["edge"]}"/>',
         f'<rect x="{rx0}" y="{top}" width="{rw}" height="{ph}" rx="10" fill="{t["panel"]}" stroke="{t["edge"]}"/>',
         f'<text x="{PAD+14}" y="{top+22}" class="lbl">VISUAL_MAP</text>',
         f'<text x="{rx0+14}" y="{top+22}" class="lbl">SYSTEM_INFO</text>']

    for i, line in enumerate(ascii_lines):
        s.append(f'<text x="{ax:.1f}" y="{ay + i*LH_A:.1f}" class="a" textLength="{ASCII_COLS*CW_A:.0f}" lengthAdjust="spacingAndGlyphs">{escape(line)}</text>')
    s.append(f'<g clip-path="url(#lc)"><rect class="scan" x="{PAD}" y="{top-40}" width="{LEFT_W}" height="40" fill="url(#sl)"/></g>')

    iy = top + 50
    for i, parts in enumerate(info_lines):
        if not parts:
            continue
        spans = "".join(
            f'<tspan class="cur">{escape(txt)}</tspan>' if cls == "cursor"
            else f'<tspan class="{cls}">{escape(txt)}</tspan>' for cls, txt in parts)
        fit = f' textLength="{INFO_CHARS*CW_I:.0f}" lengthAdjust="spacingAndGlyphs"' if parts[0][0] == "k" else ""
        s.append(f'<text x="{rx0+22}" y="{iy + i*LH_I}" class="i ln"{fit} style="animation-delay:{0.2+i*0.07:.2f}s">{spans}</text>')

    s.append("</svg>")
    return "\n".join(s)


def main():
    stats = fetch_stats(GITHUB_USER)
    info = build_info(stats)
    for theme, invert in (("dark", False), ("light", False)):
        art = image_to_ascii(PHOTO, ASCII_COLS, invert)
        with open(f"{theme}.svg", "w", encoding="utf-8") as f:
            f.write(render(theme, art, info))
        print(f"wrote {theme}.svg")


if __name__ == "__main__":
    main()
