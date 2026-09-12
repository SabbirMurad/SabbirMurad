# -*- coding: utf-8 -*-
"""Generates the olive project-name labels used as links in the README.

GitHub's markdown sanitizer strips style= from every element, drops <font>
and escapes <style>, so link text cannot be coloured -- it renders in the
theme's link blue whatever you do. Math ($\\textcolor{}{}) does render
coloured, but goes inert the moment it sits inside a link.

What does survive is <picture> inside <a>, which GitHub wraps in its own
<themed-picture> element, so these follow the GitHub theme setting rather
than only the OS one. Each name therefore becomes a tiny text-only SVG.

    python tools/gen_names.py

The box is measured from the real font so the label occupies the same width
the text would have, and the baseline sits on the bottom edge so the label
aligns with the prose beside it. None of these names has a descender; one
that did would need the box growing downwards and the baseline lifted off
the bottom, or it would be cut off.
"""
import io, os

NAMES = ["Bento", "Postura", "Fireball", "Scaffold", "Fanari", "Portfolio"]

SIZE = 16.0       # GitHub renders README body text at 16px
WEIGHT = 600
PAD = 2.0         # slack, so a viewer whose font runs wider than the measured
                  # one gets a little extra space rather than a clipped glyph

COLOR = {"dark": "#C0C27F", "light": "#6B7135"}

STACK = ("-apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans', "
         "Helvetica, Arial, sans-serif")

# Measured against Segoe UI Semibold; the metrics only set the box, the viewer
# still renders in whatever the stack resolves to.
FONT_FILE = r"C:\Windows\Fonts\seguisb.ttf"
FALLBACK_FONT = r"C:\Windows\Fonts\segoeuib.ttf"


def widths(names):
    """Advance width of each name at SIZE, measured from the actual font file."""
    from PIL import ImageFont
    path = FONT_FILE if os.path.exists(FONT_FILE) else FALLBACK_FONT
    # size must be an int for truetype(), so measure big and scale down
    f = ImageFont.truetype(path, 160)
    return {n: f.getlength(n) * SIZE / 160.0 for n in names}


def build(name, theme, w):
    box_w, box_h = w + PAD, SIZE
    o = io.StringIO()
    o.write('<svg xmlns="http://www.w3.org/2000/svg" width="%.1f" height="%.1f" '
            'viewBox="0 0 %.1f %.1f" role="img" aria-label="%s">\n'
            % (box_w, box_h, box_w, box_h, name))
    # Baseline on the bottom edge: an inline <img> sits its bottom on the text
    # baseline, so this is what lines the label up with the words around it.
    o.write('  <text x="0" y="%.1f" font-family="%s" font-size="%g" font-weight="%d" '
            'fill="%s">%s</text>\n' % (box_h, STACK, SIZE, WEIGHT, COLOR[theme], name))
    o.write('</svg>\n')
    return o.getvalue()


if __name__ == "__main__":
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out = os.path.join(root, "assets", "names")
    if not os.path.isdir(out):
        os.makedirs(out)
    w = widths(NAMES)
    for name in NAMES:
        for theme in COLOR:
            p = os.path.join(out, "%s-%s.svg" % (name.lower(), theme))
            open(p, "w", encoding="utf-8").write(build(name, theme, w[name]))
    print("%d labels in %s" % (len(NAMES) * len(COLOR), out))
    print("  " + "  ".join("%s %.1fpx" % (n, w[n]) for n in NAMES))
