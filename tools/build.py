#!/usr/bin/env python3
"""Build the অতঃকিম companion website.

    python3 tools/build.py              # writes _site/ (what GitHub Pages serves)
    python3 tools/build.py --preview    # same, but links end in index.html (for local/file previews)

Content lives in content/topics/*.md: YAML front matter + Markdown body.
Graphic blocks inside the body start with a line "@@<kind>" and end with a
line "@@" (YAML inside), or fit on one line: "@@<kind> {yaml flow}".
Kinds: compare, img, map, bars, pie, svg, note. See README.md for examples.
"""
import datetime as dt
import html
import json
import math
import re
import shutil
import sys
import urllib.parse
from pathlib import Path

import markdown
import yaml

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "_site"
SITE_URL = "https://otohkim.github.io/"
REPO = "otohkim/otohkim.github.io"
CHANNEL_URL = "https://www.youtube.com/@otohkim"
SITE_NAME = "অতঃকিম"
SITE_TAGLINE = "পড়াশোনা, কেরিয়ার, বিজ্ঞান আর প্রযুক্তি: প্রশ্নের সোজা উত্তর"
PREVIEW = "--preview" in sys.argv

COLORS = {"teal": "#2FB3A3", "coral": "#E8705F", "yellow": "#F4B740", "ink": "#22303A",
          "paper": "#FBF6EC", "grey": "#E9E1D0", "card": "#FFFDF8"}
BN_DIGITS = str.maketrans("0123456789", "০১২৩৪৫৬৭৮৯")
BN_MONTHS = ["জানুয়ারি", "ফেব্রুয়ারি", "মার্চ", "এপ্রিল", "মে", "জুন", "জুলাই", "আগস্ট",
             "সেপ্টেম্বর", "অক্টোবর", "নভেম্বর", "ডিসেম্বর"]
EM_DASH = "\u2014"


def bn(x):
    return str(x).translate(BN_DIGITS)


def bn_date(d):
    if isinstance(d, str):
        d = dt.date.fromisoformat(d)
    return f"{bn(d.day)} {BN_MONTHS[d.month - 1]} {bn(d.year)}"


def esc(s):
    return html.escape(str(s), quote=True)


def md_inline(s):
    out = markdown.markdown(str(s), extensions=["sane_lists"])
    return re.sub(r"^<p>(.*)</p>$", r"\1", out.strip(), flags=re.S)


def link(root, path):
    """Relative link from a page at depth `root` to a site path like 'tag/x/'."""
    if PREVIEW and (path == "" or path.endswith("/")):
        path += "index.html"
    return root + path


# ---------------------------------------------------------------- content
def load_tags():
    data = yaml.safe_load((ROOT / "content" / "tags.yml").read_text(encoding="utf-8"))
    return {t["name"]: t for t in data}


def load_topics():
    topics = []
    for f in sorted((ROOT / "content" / "topics").glob("*.md")):
        raw = f.read_text(encoding="utf-8")
        m = re.match(r"^---\n(.*?)\n---\n(.*)$", raw, re.S)
        if not m:
            sys.exit(f"{f.name}: missing front matter")
        meta = yaml.safe_load(m.group(1))
        if meta.get("draft"):
            continue
        meta["body_md"] = m.group(2)
        meta["file"] = f.name
        meta.setdefault("slug", f.stem)
        meta.setdefault("published", meta["checked"])
        for key in ("title", "summary", "checked", "tags", "sources"):
            if not meta.get(key):
                sys.exit(f"{f.name}: '{key}' is required")
        topics.append(meta)
    topics.sort(key=lambda t: (str(t["checked"]), str(t["published"])), reverse=True)
    return topics


# ---------------------------------------------------------------- graphics
INDIA = json.loads((ROOT / "assets" / "data" / "india_states.json").read_text(encoding="utf-8"))
K, LON0, LAT0, CX = 20.0, 68.0, 37.2, math.cos(math.radians(22))


def proj(lon, lat):
    return (lon - LON0) * CX * K, (LAT0 - lat) * K


def g_map(spec, ctx):
    fills = {}
    for color, states in (spec.get("fills") or {}).items():
        for s in states:
            if s not in INDIA["states"]:
                sys.exit(f"map: unknown state '{s}'. Known: {', '.join(sorted(INDIA['states']))}")
            fills[s] = COLORS.get(color, color)
    parts = []
    for name, d in INDIA["states"].items():
        fill = fills.get(name)
        if fill:
            parts.append(f'<path d="{d}" fill="{fill}" fill-opacity=".55" stroke="#22303A" stroke-width=".9"><title>{esc(name)}</title></path>')
        else:
            parts.append(f'<path d="{d}" fill="#F3EBDA" stroke="#8C949A" stroke-width=".55"/>')
    for p in spec.get("points") or []:
        x, y = proj(p["lon"], p["lat"])
        c = COLORS.get(p.get("color", "ink"), p.get("color"))
        parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5" fill="{c}" stroke="#22303A" stroke-width="1.4"/>')
        if p.get("label"):
            dx = p.get("dx", 9)
            anchor = "end" if dx < 0 else "start"
            parts.append(f'<text x="{x + dx:.1f}" y="{y + 5:.1f}" font-size="15" text-anchor="{anchor}" class="hand">{esc(p["label"])}</text>')
    for lab in spec.get("labels") or []:
        x, y = proj(lab["lon"], lab["lat"])
        size = lab.get("size", 17)
        parts.append(f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" text-anchor="middle" class="hand" '
                     f'paint-order="stroke" stroke="#FBF6EC" stroke-width="4">{esc(lab["text"])}</text>')
    title = esc(spec.get("alt", "ভারতের মানচিত্র"))
    svg = (f'<svg class="gfx" viewBox="{INDIA["viewBox"]}" role="img" aria-label="{title}">{"".join(parts)}</svg>')
    legend = ""
    if spec.get("legend"):
        legend = '<div class="legend">' + "".join(
            f'<span><i style="background:{COLORS.get(l["color"], l["color"])};opacity:.75"></i>{esc(l["text"])}</span>'
            for l in spec["legend"]) + "</div>"
    cap = esc(spec.get("caption", ""))
    credit = "মানচিত্রের সীমানা: Survey of India (Datameet)"
    return (f'<figure class="map-wrap">{svg}{legend}<figcaption>{cap}{" · " if cap else ""}{credit}</figcaption></figure>')


def g_bars(spec, ctx):
    """Horizontal bars, label above each bar, so it stays readable on phones."""
    items = spec["items"]
    vmax = spec.get("max") or max(i["value"] + i.get("extra", 0) for i in items)
    W, left, rowh, top = 460, 6, 78, 6
    scale = (W - left - 150) / vmax
    H = top + rowh * len(items)
    out = []
    for n, it in enumerate(items):
        y = top + n * rowh
        c = COLORS.get(it.get("color", "teal"), it.get("color"))
        w = it["value"] * scale
        out.append(f'<text x="{left}" y="{y + 20}" font-size="18" class="hand">{esc(it["label"])}</text>')
        out.append(f'<rect data-r="1.2" x="{left}" y="{y + 32}" width="{w:.1f}" height="30" fill="{c}" stroke="#22303A" stroke-width="1.6" data-gap="6"/>')
        endx = left + w
        if it.get("extra"):
            w2 = it["extra"] * scale
            out.append(f'<rect data-r="1.2" x="{endx:.1f}" y="{y + 32}" width="{w2:.1f}" height="30" fill="{COLORS["yellow"]}" stroke="#22303A" stroke-width="1.2" stroke-dasharray="5 4" data-gap="5" data-angle="45"/>')
            endx += w2
        val = it.get("value_label", bn(it["value"]))
        out.append(f'<text x="{endx + 10:.1f}" y="{y + 54}" font-size="18">{esc(val)}</text>')
    legend = ""
    if spec.get("extra_label"):
        legend = (f'<div class="legend"><span><i style="background:{COLORS["yellow"]}"></i>{esc(spec["extra_label"])}</span></div>')
    cap = spec.get("caption", "")
    return (f'<figure><svg class="gfx" viewBox="0 0 {W} {H}" style="max-width:560px;margin:0 auto" role="img" aria-label="{esc(spec.get("alt", cap))}">{"".join(out)}</svg>'
            f'{legend}<figcaption>{esc(cap)}</figcaption></figure>')


def g_pie(spec, ctx):
    items = spec["items"]
    total = sum(i["value"] for i in items)
    cx, cy, r = 150, 150, 120
    a0, out, leg = -math.pi / 2, [], []
    for it in items:
        a1 = a0 + 2 * math.pi * it["value"] / total
        x0, y0 = cx + r * math.cos(a0), cy + r * math.sin(a0)
        x1, y1 = cx + r * math.cos(a1), cy + r * math.sin(a1)
        large = 1 if a1 - a0 > math.pi else 0
        c = COLORS.get(it.get("color", "teal"), it.get("color"))
        out.append(f'<path data-r="1" d="M{cx},{cy} L{x0:.1f},{y0:.1f} A{r},{r} 0 {large} 1 {x1:.1f},{y1:.1f} Z" fill="{c}" stroke="#22303A" stroke-width="1.6"/>')
        leg.append(f'<span><i style="background:{c}"></i>{esc(it["label"])} ({esc(it.get("value_label", bn(it["value"])))})</span>')
        a0 = a1
    return (f'<figure><svg class="gfx" viewBox="0 0 300 300" style="max-width:300px;margin:0 auto" role="img" aria-label="{esc(spec.get("alt", ""))}">{"".join(out)}</svg>'
            f'<div class="legend">{"".join(leg)}</div><figcaption>{esc(spec.get("caption", ""))}</figcaption></figure>')


TICK = ('<svg class="tick" viewBox="0 0 24 24" aria-hidden="true"><path d="M3 13 L9 19 L21 4" fill="none" '
        'stroke="{c}" stroke-width="3.2" stroke-linecap="round" stroke-linejoin="round"/></svg>')


def g_compare(spec, ctx):
    cols = []
    for side in ("left", "right"):
        s = spec[side]
        color = s.get("color", "teal" if side == "left" else "coral")
        items = "".join(
            f'<li>{TICK.format(c=COLORS[color])}<b>{md_inline(i["head"])}</b><span>{md_inline(i["text"])}</span></li>'
            for i in s["items"])
        sub = f'<p class="sub">{md_inline(s["sub"])}</p>' if s.get("sub") else ""
        cols.append(f'<div class="cmp {color}" data-rough="{color} hatch thin"><div><h3>{md_inline(s["title"])}</h3>{sub}<ul>{items}</ul></div></div>')
    return f'<div class="compare">{"".join(cols)}</div>'


def g_img(spec, ctx):
    src = link(ctx["root"], "assets/img/" + spec["src"])
    full = ' class="full"' if spec.get("full") else ""
    zoom = f' class="zoom" data-full="{src}"' if spec.get("zoom", True) else ""
    wh = f' width="{spec["width"]}" height="{spec["height"]}"' if spec.get("width") else ""
    cap = md_inline(spec.get("caption", "")) if spec.get("caption") else ""
    return (f'<figure{full}><img src="{src}" alt="{esc(spec["alt"])}" loading="lazy" decoding="async"{wh}{zoom}>'
            f'{"<figcaption>" + cap + "</figcaption>" if cap else ""}</figure>')


def g_svg(spec, ctx):
    svg = (ROOT / "content" / "graphics" / spec["file"]).read_text(encoding="utf-8")
    cap = spec.get("caption")
    return f'<figure>{svg}{"<figcaption>" + md_inline(cap) + "</figcaption>" if cap else ""}</figure>'


def g_note(spec, ctx):
    kind = spec.get("kind", "info")
    lbl = f'<span class="lbl">{esc(spec["label"])}</span>' if spec.get("label") else ""
    return f'<div class="note {kind}"><p>{lbl}{md_inline(spec["text"])}</p></div>'


GRAPHICS = {"map": g_map, "bars": g_bars, "pie": g_pie, "compare": g_compare,
            "img": g_img, "svg": g_svg, "note": g_note}


def render_body(md_text, ctx):
    lines, out, blocks, i = md_text.split("\n"), [], [], 0
    while i < len(lines):
        line = lines[i]
        m = re.match(r"^@@(\w+)\s*(.*)$", line)
        if m and m.group(1) in GRAPHICS:
            kind, rest = m.group(1), m.group(2).strip()
            if rest:
                spec = yaml.safe_load(rest)
            else:
                j = i + 1
                while j < len(lines) and lines[j].strip() != "@@":
                    j += 1
                spec = yaml.safe_load("\n".join(lines[i + 1:j]))
                i = j
            blocks.append(GRAPHICS[kind](spec, ctx))
            out.append(f"\n\nGFXBLOCK{len(blocks) - 1}X\n\n")
        else:
            out.append(line)
        i += 1
    htm = markdown.markdown("\n".join(out), extensions=["tables", "sane_lists", "attr_list"])
    for n, b in enumerate(blocks):
        htm = htm.replace(f"<p>GFXBLOCK{n}X</p>", b)
    return htm


# ---------------------------------------------------------------- templates
SEARCH_ICON = ('<svg class="icon" viewBox="0 0 24 24" aria-hidden="true"><circle cx="10.5" cy="10.5" r="6.5" fill="none" '
               'stroke="currentColor" stroke-width="2.2"/><path d="M15.5 15.5 L21 21" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"/></svg>')


def search_box(placeholder="খোঁজো: যেমন ইংরেজির টিচার, B.Ed, AI..."):
    return (f'<div class="search" role="search"><div class="rough-box" data-rough="ink thin">'
            f'<label class="sr-only" for="q">খোঁজো</label>'
            f'<input id="q" type="search" autocomplete="off" enterkeyhint="search" placeholder="{esc(placeholder)}">{SEARCH_ICON}</div>'
            f'<div class="search-results" role="listbox"></div></div>')


def page(*, root, path, title, desc, body, og_image=None, keywords=None, head_search=True, jsonld=None):
    canonical = SITE_URL + path
    full_title = title if title == SITE_NAME else f"{title} | {SITE_NAME}"
    og = SITE_URL + (og_image or "assets/img/logo-512.png")
    kw = f'<meta name="keywords" content="{esc(", ".join(keywords))}">' if keywords else ""
    ld = f'<script type="application/ld+json">{json.dumps(jsonld, ensure_ascii=False)}</script>' if jsonld else ""
    hs = f'<div class="head-search">{search_box()}</div>' if head_search else ""
    return f"""<!doctype html>
<html lang="bn" class="no-js" data-root="{root}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(full_title)}</title>
<meta name="description" content="{esc(desc)}">
{kw}
<link rel="canonical" href="{canonical}">
<meta property="og:type" content="article">
<meta property="og:site_name" content="{SITE_NAME} Otohkim">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{canonical}">
<meta property="og:image" content="{og}">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#FBF6EC">
<link rel="icon" type="image/png" href="{root}assets/img/favicon.png">
<link rel="apple-touch-icon" href="{root}assets/img/logo-192.png">
<link rel="preload" href="{root}assets/fonts/noto-bengali-digits.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="{root}assets/fonts/hind-siliguri-bengali-400-normal.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="{root}assets/css/site.css">
{ld}
</head>
<body>
<header class="site-head"><div class="wrap">
<a class="brand" href="{link(root, '')}"><img src="{root}assets/img/logo-96.png" srcset="{root}assets/img/logo-192.png 2x" alt="" width="46" height="46"><span><span class="name">{SITE_NAME}</span><span class="tag">What next? · পড়াশোনা আর কেরিয়ারের প্রশ্ন</span></span></a>
{hs}
</div></header>
<main>
{body}
</main>
<footer class="site-foot"><div class="wrap">
<div class="foot-brand"><img src="{root}assets/img/logo-96.png" alt="" width="36" height="36"><b>{SITE_NAME}</b></div>
<p>পশ্চিমবঙ্গের ছাত্রছাত্রী (দশম শ্রেণি থেকে কলেজ) আর অভিভাবকদের জন্য, ইউটিউব চ্যানেল <a href="{CHANNEL_URL}">অতঃকিম</a>-এর সঙ্গী সাইট। ড. ভিক্টর রায়।</p>
<p>প্রতিটা পাতার তথ্য সরকারি সূত্র থেকে নেওয়া, তারিখ সহ। নিয়ম বদলায়, তাই আবেদনের আগে মূল বিজ্ঞপ্তি দেখে নিও।</p>
<p><a href="{link(root, 'tag/')}">সব বিষয়</a> · <a href="{link(root, 'about/')}">এই সাইট সম্পর্কে</a> · <a href="{CHANNEL_URL}">ইউটিউব চ্যানেল</a></p>
</div></footer>
<script src="{root}assets/js/rough.js" defer></script>
<script src="{root}assets/js/site.js" defer></script>
</body>
</html>
"""


def crumbs(root, items):
    parts = [f'<a href="{link(root, "")}">হোম</a>']
    for name, href in items:
        parts.append(f'<a href="{link(root, href)}">{esc(name)}</a>' if href else f'<span aria-current="page">{esc(name)}</span>')
    return '<nav class="crumbs" aria-label="breadcrumb">' + '<span class="sep">›</span>'.join(parts) + "</nav>"


def tag_chips(root, names, tags, small=False):
    cls = "chip sm" if small else "chip"
    return '<ul class="chips">' + "".join(
        f'<li><a class="{cls}" data-rough="ink thin" href="{link(root, "tag/" + tags[n]["slug"] + "/")}">{esc(n)}</a></li>'
        for n in names) + "</ul>"


def card(root, t, tags):
    return (f'<li class="card" data-rough="ink thin"><div>'
            f'<h3><a href="{link(root, t["slug"] + "/")}">{esc(t["title"])}</a></h3>'
            f'<p>{esc(t["summary"])}</p>'
            f'<div class="meta"><span>তথ্য যাচাই: {bn_date(t["checked"])}</span></div>'
            f'{tag_chips(root, t["tags"], tags, small=True)}</div></li>')


def video_id(url):
    m = re.search(r"(?:shorts/|v=|youtu\.be/|embed/)([\w-]{11})", url)
    return m.group(1) if m else None


def topic_page(t, tags):
    root = "../"
    ctx = {"root": root, "topic": t}
    body_html = render_body(t["body_md"], ctx)
    first_tag = t["tags"][0]
    video = ""
    if t.get("video"):
        v = t["video"]
        vid = video_id(v["url"])
        kind = "Short" if "shorts/" in v["url"] else "ভিডিও"
        thumb = f' style="background-image:url(https://i.ytimg.com/vi/{vid}/hqdefault.jpg)"' if vid else ""
        video = (f'<a class="video" data-rough="coral thin" href="{esc(v["url"])}" target="_blank" rel="noopener"><div style="display:flex;gap:1rem;align-items:center">'
                 f'<span class="thumb"{thumb}></span><span><span class="vs">অতঃকিম-এর {kind} দেখো</span>'
                 f'<span class="vt">{esc(v["title"])}</span></span></div></a>')
    srcs = "".join(
        f'<li><a href="{esc(s["url"])}" target="_blank" rel="noopener">{esc(s["title"])}</a>'
        f'{"<span class=src-note>" + md_inline(s["note"]) + "</span>" if s.get("note") else ""}</li>'
        for s in t["sources"])
    history = f"https://github.com/{REPO}/commits/main/content/topics/{t['file']}"
    url = SITE_URL + t["slug"] + "/"
    wa = "https://wa.me/?text=" + urllib.parse.quote(t["title"] + " " + url)
    body = f"""<article class="wrap">
{crumbs(root, [(first_tag, "tag/" + tags[first_tag]["slug"] + "/"), (t.get("short_title", t["title"]), None)])}
<h1>{esc(t["title"])}</h1>
<p class="lede">{esc(t["summary"])}</p>
<div class="stamp-row"><span class="stamp" data-rough="coral thin"><span>তথ্য যাচাই: {bn_date(t["checked"])}</span></span>{tag_chips(root, t["tags"], tags, small=True)}</div>
<div class="prose">
{body_html}
</div>
{video}
<section class="sources" data-rough="teal thin"><div>
<h2>সরকারি সূত্র</h2>
<ol>{srcs}</ol>
<p class="change-note">তথ্য যাচাই করা হয়েছে {bn_date(t["checked"])}। পরের বিজ্ঞপ্তিতে নিয়ম বদলাতে পারে, তাই আবেদনের আগে মূল বিজ্ঞপ্তিটা নিজে পড়ে নিও। <a href="{history}" target="_blank" rel="noopener">আগের সংস্করণগুলো (কোন তারিখে কী নিয়ম ছিল)</a></p>
</div></section>
<div class="share">
<button class="btn" data-rough="ink thin" data-copy="{url}" type="button"><svg viewBox="0 0 24 24" aria-hidden="true"><rect x="8" y="8" width="12" height="12" rx="2" fill="none" stroke="currentColor" stroke-width="2"/><path d="M4 16V5a1 1 0 0 1 1-1h11" fill="none" stroke="currentColor" stroke-width="2"/></svg><span>লিংক কপি করো</span></button>
<a class="btn" data-rough="ink thin" href="{wa}" target="_blank" rel="noopener"><span>WhatsApp-এ পাঠাও</span></a>
</div>
</article>"""
    jsonld = {"@context": "https://schema.org", "@type": "Article", "headline": t["title"],
              "description": t["summary"], "inLanguage": "bn", "dateModified": str(t["checked"]),
              "datePublished": str(t["published"]), "author": {"@type": "Person", "name": "Dr. Victor Roy"},
              "publisher": {"@type": "Organization", "name": "Otohkim"}, "url": url}
    return page(root=root, path=t["slug"] + "/", title=t["title"], desc=t["summary"], body=body,
                og_image=t.get("image"), keywords=t.get("keywords"), jsonld=jsonld)


HERO_DOODLE = """<svg class="gfx hero-doodle" viewBox="0 0 140 70" aria-hidden="true">
<line data-r="1" x1="70" y1="12" x2="70" y2="68" stroke="#22303A" stroke-width="2.4"/>
<path data-r="1.1" d="M72 14 L118 14 L130 24 L118 34 L72 34 Z" fill="#2FB3A3" stroke="#22303A" stroke-width="1.8" data-gap="5"/>
<path data-r="1.1" d="M68 38 L22 38 L10 48 L22 58 L68 58 Z" fill="#E8705F" stroke="#22303A" stroke-width="1.8" data-gap="5"/>
<line data-r="1" x1="52" y1="68" x2="90" y2="68" stroke="#22303A" stroke-width="2"/>
</svg>"""


def home_page(topics, tags):
    root = ""
    used = [n for n in tags if any(n in t["tags"] for t in topics)]
    counts = {n: sum(n in t["tags"] for t in topics) for n in used}
    chips = '<ul class="chips">' + "".join(
        f'<li><a class="chip" data-rough="ink thin" href="{link(root, "tag/" + tags[n]["slug"] + "/")}">{esc(n)}<small>{bn(counts[n])}</small></a></li>'
        for n in used) + "</ul>"
    latest = "".join(card(root, t, tags) for t in topics[:12])
    body = f"""<div class="wrap">
<section class="hero">
{HERO_DOODLE}
<h1>কী পড়বে? তারপর <span class="hl">কী?</span></h1>
<p>কেরিয়ার, পড়াশোনা, বিজ্ঞান আর প্রযুক্তি নিয়ে ছোট ছোট উত্তর, সরকারি সূত্র আর তারিখ সহ। বাংলায় বা ইংরেজিতে খোঁজো।</p>
{search_box("খোঁজো: ইংরেজির টিচার, CTET, english teacher hote chai...")}
</section>
<section>
<h2>বিষয়</h2>
{chips}
</section>
<section>
<div class="section-title"><h2>সাম্প্রতিক আপডেট</h2></div>
<ul class="cards">{latest}</ul>
</section>
</div>"""
    jsonld = {"@context": "https://schema.org", "@type": "WebSite", "name": "অতঃকিম Otohkim", "url": SITE_URL,
              "inLanguage": "bn", "potentialAction": {"@type": "SearchAction",
              "target": SITE_URL + "search/?q={q}", "query-input": "required name=q"}}
    return page(root=root, path="", title=SITE_NAME, desc="অতঃকিম (What next?): পশ্চিমবঙ্গের ছাত্রছাত্রী আর অভিভাবকদের জন্য কেরিয়ার, পড়াশোনা, বিজ্ঞান ও প্রযুক্তির প্রশ্নের উত্তর, সরকারি সূত্র সহ।",
                body=body, head_search=False, jsonld=jsonld)


def tag_page(name, tag, topics, tags):
    root = "../../"
    items = [t for t in topics if name in t["tags"]]
    body = f"""<div class="wrap">
{crumbs(root, [("বিষয়", "tag/"), (name, None)])}
<h1>{esc(name)}</h1>
<p class="lede">{esc(tag.get("about", ""))}</p>
<ul class="cards">{"".join(card(root, t, tags) for t in items)}</ul>
</div>"""
    return page(root=root, path=f"tag/{tag['slug']}/", title=name, desc=tag.get("about", name), body=body)


def tags_index(topics, tags):
    root = "../"
    rows = []
    for n, tg in tags.items():
        c = sum(n in t["tags"] for t in topics)
        if c:
            rows.append(f'<li class="card" data-rough="ink thin"><div><h3><a href="{link(root, "tag/" + tg["slug"] + "/")}">{esc(n)}</a></h3>'
                        f'<p>{esc(tg.get("about", ""))}</p><div class="meta">{bn(c)}টা পাতা</div></div></li>')
    body = f"""<div class="wrap">{crumbs(root, [("বিষয়", None)])}<h1>সব বিষয়</h1>
<ul class="cards two">{"".join(rows)}</ul></div>"""
    return page(root=root, path="tag/", title="সব বিষয়", desc="অতঃকিম সাইটের সব বিষয়", body=body)


def search_page():
    root = "../"
    body = f"""<div class="wrap">{crumbs(root, [("খোঁজ", None)])}
<h1>খোঁজ: <span id="search-q" class="hl"></span></h1>
<div id="search-page-results"></div></div>"""
    return page(root=root, path="search/", title="খোঁজ", desc="অতঃকিম সাইটে খোঁজো", body=body)


def about_page():
    root = "../"
    body = f"""<div class="wrap prose">{crumbs(root, [("এই সাইট সম্পর্কে", None)])}
<h1>এই সাইট সম্পর্কে</h1>
<p>অতঃকিম মানে "এরপর কী?"। ইউটিউব চ্যানেলে প্রতি সপ্তাহে প্রযুক্তি, বিজ্ঞান আর শিল্প-বাণিজ্যের খবর থেকে কেরিয়ারের কথা বলি। কমেন্টে অনেক প্রশ্ন আসে, যেমন কোন ডিগ্রি লাগবে, বয়স কত পর্যন্ত, কোথায় আবেদন। সেই প্রশ্নগুলোর উত্তর এখানে এক পাতায় একটা করে, ছবি আর ডায়াগ্রামে।</p>
<p>প্রতিটা পাতায় থাকে: কবে তথ্য যাচাই করা হয়েছে, কোন সরকারি সূত্র থেকে, আর আগের সংস্করণের লিংক। নিয়ম প্রতিটা নতুন বিজ্ঞপ্তিতে বদলাতে পারে, তাই আবেদনের আগে মূল বিজ্ঞপ্তি নিজে পড়ে নিও।</p>
<p>ভুল চোখে পড়লে বা নতুন প্রশ্ন থাকলে <a href="{CHANNEL_URL}">চ্যানেলের</a> যেকোনো ভিডিওর কমেন্টে লেখো।</p>
<p>ছবি: শুধু নিজেদের আঁকা গ্রাফিক বা রয়্যালটি-মুক্ত ছবি, প্রতিটার ক্রেডিট সহ। মানচিত্রের সীমানা Survey of India (Datameet)। আঁকার স্টাইল: rough.js (MIT লাইসেন্স)।</p>
</div>"""
    return page(root=root, path="about/", title="এই সাইট সম্পর্কে", desc="অতঃকিম সাইট কী, কেন, কীভাবে", body=body)


def not_found():
    body = """<div class="wrap" style="text-align:center;padding:3rem 0"><h1>পাতাটা পাওয়া গেল না</h1>
<p>লিংকটা হয়তো বদলেছে। ওপরের খোঁজার ঘরে বিষয়টা লিখে দেখো।</p><p><a href="/">হোমে ফেরো</a></p></div>"""
    return page(root="/", path="404.html", title="পাতা পাওয়া যায়নি", desc="পাতা পাওয়া যায়নি", body=body)


def plain(htm):
    t = re.sub(r"<(script|style|svg)[^>]*>.*?</\1>", " ", htm, flags=re.S)
    t = re.sub(r"<[^>]+>", " ", t)
    return re.sub(r"\s+", " ", html.unescape(t)).strip()


# ---------------------------------------------------------------- main
def write(path, text):
    p = OUT / path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def main():
    tags = load_tags()
    topics = load_topics()
    for t in topics:
        for n in t["tags"]:
            if n not in tags:
                sys.exit(f"{t['file']}: tag '{n}' is not in content/tags.yml")
    if OUT.exists():
        shutil.rmtree(OUT)
    shutil.copytree(ROOT / "assets", OUT / "assets", ignore=shutil.ignore_patterns("data"))
    index, problems = [], []
    for t in topics:
        htm = topic_page(t, tags)
        write(f"{t['slug']}/index.html", htm)
        text = plain(re.search(r'<div class="prose">(.*?)</div>\s*(?:<a class="video"|<section class="sources")', htm, re.S).group(1))
        index.append({"t": t["title"], "u": t["slug"] + "/", "s": t["summary"], "tags": t["tags"],
                      "k": " ".join(t.get("keywords", [])), "b": text[:6000], "d": str(t["checked"])})
    write("index.html", home_page(topics, tags))
    for n, tg in tags.items():
        if any(n in t["tags"] for t in topics):
            write(f"tag/{tg['slug']}/index.html", tag_page(n, tg, topics, tags))
    write("tag/index.html", tags_index(topics, tags))
    write("search/index.html", search_page())
    write("about/index.html", about_page())
    write("404.html", not_found())
    write("search-index.json", json.dumps(index, ensure_ascii=False, separators=(",", ":")))
    urls = [""] + [t["slug"] + "/" for t in topics] + ["tag/", "about/"] + \
        [f"tag/{tg['slug']}/" for n, tg in tags.items() if any(n in t["tags"] for t in topics)]
    lastmod = {t["slug"] + "/": str(t["checked"]) for t in topics}
    write("sitemap.xml", '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' +
          "\n".join(f"<url><loc>{SITE_URL}{u}</loc>{'<lastmod>' + lastmod[u] + '</lastmod>' if u in lastmod else ''}</url>" for u in urls) +
          "\n</urlset>\n")
    write("robots.txt", f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}sitemap.xml\n")
    write(".nojekyll", "")
    # house-style checks: no em dashes anywhere in the published text
    for f in OUT.rglob("*.html"):
        if EM_DASH in f.read_text(encoding="utf-8"):
            problems.append(f"em dash in {f.relative_to(OUT)}")
    if problems:
        sys.exit("STYLE CHECK FAILED:\n" + "\n".join(problems))
    print(f"built {len(topics)} topic page(s) into {OUT}{' (preview links)' if PREVIEW else ''}")


if __name__ == "__main__":
    main()
