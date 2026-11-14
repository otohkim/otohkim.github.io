"""Make a hand-drawn-style mind map SVG for a topic page.

Usage: python3 tools/make_mindmap.py spec.json content/graphics/<name>.svg
spec: {"center": "...", "center_sub": "...", "aria": "...",
       "branches": [{"title": "...", "sub": "...", "color": "teal|coral|yellow|ink"}, ...]}
Up to 6 branches, placed around the centre. Shapes carry data-r so site.js redraws them with rough.js.
"""
import json, math, sys
from xml.sax.saxutils import escape

COL = {"teal": "#2FB3A3", "coral": "#E8705F", "yellow": "#D9A02E", "ink": "#22303A"}
W, H = 540, 700
CX, CY = W / 2, H / 2

# box centres for up to 6 branches (top-left, top-right, right, bottom-right, bottom-left, left)
# phone-friendly: two columns, centre bubble in the middle row
SLOTS = {
    3: [(138, 78), (402, 78), (270, 600)],
    4: [(138, 78), (402, 78), (138, 440), (402, 440)],
    5: [(138, 78), (402, 78), (138, 440), (402, 440), (270, 620)],
    6: [(138, 78), (402, 78), (138, 440), (402, 440), (138, 620), (402, 620)],
}
BW, BH = 252, 104
CY = 255


def main(spec_path, out):
    s = json.load(open(spec_path, encoding="utf-8"))
    br = s["branches"]
    slots = SLOTS[len(br)]
    parts = [f'<svg class="gfx" viewBox="0 0 {W} {H}" style="max-width:560px;margin:0 auto" role="img" '
             f'aria-label="{escape(s.get("aria", s["center"]))}">']
    # connectors first (under the boxes)
    parts.append('<g fill="none" stroke-linecap="round">')
    for (x, y), b in zip(slots, br):
        c = COL.get(b.get("color", "ink"))
        mx, my = (CX + x) / 2, (CY + y) / 2
        # gentle curve: bend perpendicular to the line
        dx, dy = x - CX, y - CY
        n = math.hypot(dx, dy) or 1
        bx, by = mx - dy / n * 28, my + dx / n * 28
        parts.append(f'<path data-r="1.1" d="M{CX:.0f},{CY:.0f} Q{bx:.0f},{by:.0f} {x:.0f},{y:.0f}" '
                     f'stroke="{c}" stroke-width="2.6"/>')
    parts.append('</g>')
    # centre
    parts.append(f'<ellipse data-r="1.4" cx="{CX:.0f}" cy="{CY:.0f}" rx="150" ry="66" fill="#F8D98A" '
                 f'stroke="#22303A" stroke-width="2.2" data-fill="solid"/>')
    cy_title = CY + (8 if not s.get("center_sub") else -4)
    parts.append(f'<text x="{CX:.0f}" y="{cy_title:.0f}" font-size="30" text-anchor="middle" class="hand">{escape(s["center"])}</text>')
    if s.get("center_sub"):
        parts.append(f'<text x="{CX:.0f}" y="{CY + 30:.0f}" font-size="19" text-anchor="middle">{escape(s["center_sub"])}</text>')
    # branch boxes
    for (x, y), b in zip(slots, br):
        c = COL.get(b.get("color", "ink"))
        parts.append(f'<rect data-r="1.2" x="{x - BW / 2:.0f}" y="{y - BH / 2:.0f}" width="{BW}" height="{BH}" '
                     f'fill="#FFFDF8" stroke="{c}" stroke-width="2.4" data-fill="solid"/>')
        parts.append(f'<text x="{x:.0f}" y="{y - 8:.0f}" font-size="25" text-anchor="middle" class="hand">{escape(b["title"])}</text>')
        if b.get("sub"):
            parts.append(f'<text x="{x:.0f}" y="{y + 28:.0f}" font-size="18" text-anchor="middle">{escape(b["sub"])}</text>')
    parts.append('</svg>')
    open(out, "w", encoding="utf-8").write("\n".join(parts) + "\n")
    print("wrote", out)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
