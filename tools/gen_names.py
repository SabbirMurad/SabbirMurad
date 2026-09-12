# -*- coding: utf-8 -*-
"""Generates the olive link labels used throughout the README.

GitHub's markdown sanitizer strips style= from every element, drops <font>
and escapes <style>, so link text cannot be coloured -- it renders in the
theme's link blue whatever you do. Math ($\\textcolor{}{}) does render
coloured, but goes inert the moment it sits inside a link.

What does survive is <picture> inside <a>, which GitHub wraps in its own
<themed-picture>, so these follow the GitHub theme setting rather than only
the OS one. Each link's text therefore becomes a tiny text-only SVG.

    python tools/gen_names.py

Vertical alignment is the whole problem here, and the two cases differ.

An inline <img> sits its bottom edge on the text baseline, so a label drawn
with its baseline on the bottom edge lines up exactly, and -- since the box
then rises no higher than an ascender -- it never grows the line box. That
is the good case, and it covers every label without a descender.

It cannot work for "Python backend" or "engine": anything below the
baseline falls outside the box, so the tails of y, p and g get cut off.
Those use align="middle", which the sanitizer permits. Measured against
real text rather than taken from the spec -- it puts the image's midpoint
on the baseline, not on the baseline plus half an x-height, so the glyph
baseline belongs at exactly half the box height. The cost is that a
middle-aligned box hangs H/2 below the baseline where the line box only
allows about 5px, so these nudge their own line taller. That is why only
the labels that actually need a descender are built this way.
"""
import io, os

SIZE = 16.0       # GitHub renders README body text at 16px
FLAT_BOX = 16.0   # no descender: ascender height, baseline on the bottom edge
DROP_BOX = 24.0   # descender: baseline at the midpoint, tails in the lower half
PAD = 2.0         # slack, so a viewer whose font runs wider than the measured
                  # one gets a little extra space rather than a clipped glyph

DESCENDERS = set("gjpqy")

COLOR = {"dark": "#C0C27F", "light": "#6B7135"}

STACK = ("-apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans', "
         "Helvetica, Arial, sans-serif")

# Measured against the matching Segoe UI cut; the metrics only size the box,
# the viewer still renders in whatever the stack resolves to.
FONTS = {600: [r"C:\Windows\Fonts\seguisb.ttf", r"C:\Windows\Fonts\segoeuib.ttf"],
         400: [r"C:\Windows\Fonts\segoeui.ttf"]}

# (slug, text, weight). 600 matches the bold the project names had as
# markdown; 400 matches the body text the prose links sit inside.
LABELS = [
    ("bento",            "Bento",            600),
    ("postura",          "Postura",          600),
    ("fireball",         "Fireball",         600),
    ("scaffold",         "Scaffold",         600),
    ("fanari",           "Fanari",           600),
    ("portfolio",        "Portfolio",        600),
    ("python-backend",   "Python backend",   400),
    ("engine",           "engine",           400),
    ("backend",          "backend",          400),
    ("service",          "service",          400),
    ("sabbirhassan-com", "sabbirhassan.com", 400),
    ("email-me",         "Email me",         400),
    ("discord",          "Discord",          400),
]


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def width(text, weight):
    """Advance width of the text at SIZE, measured from the actual font file."""
    from PIL import ImageFont
    path = next(p for p in FONTS[weight] if os.path.exists(p))
    # truetype() wants an int size, so measure large and scale back down
    return ImageFont.truetype(path, 160).getlength(text) * SIZE / 160.0


def drops(text):
    """Does this label need room below the baseline?"""
    return bool(DESCENDERS & set(text))


def build(text, theme, weight, w):
    box_w = w + PAD
    box_h = DROP_BOX if drops(text) else FLAT_BOX
    baseline = box_h / 2.0 if drops(text) else box_h
    o = io.StringIO()
    o.write('<svg xmlns="http://www.w3.org/2000/svg" width="%.1f" height="%.1f" '
            'viewBox="0 0 %.1f %.1f" role="img" aria-label="%s">\n'
            % (box_w, box_h, box_w, box_h, esc(text)))
    o.write('  <text x="0" y="%.2f" font-family="%s" font-size="%g" font-weight="%d" '
            'fill="%s">%s</text>\n'
            % (baseline, STACK, SIZE, weight, COLOR[theme], esc(text)))
    o.write('</svg>\n')
    return o.getvalue()


if __name__ == "__main__":
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out = os.path.join(root, "assets", "names")
    if not os.path.isdir(out):
        os.makedirs(out)

    keep = set()
    for slug, text, weight in LABELS:
        w = width(text, weight)
        for theme in COLOR:
            name = "%s-%s.svg" % (slug, theme)
            keep.add(name)
            open(os.path.join(out, name), "w", encoding="utf-8").write(
                build(text, theme, weight, w))
        print("  %-18s %5.1fpx  w%d  %s" % (text, w, weight,
              "middle (descender)" if drops(text) else "baseline"))

    for stale in sorted(set(os.listdir(out)) - keep):
        os.remove(os.path.join(out, stale))
        print("  removed stale %s" % stale)
    print("%d labels in %s" % (len(keep), out))
