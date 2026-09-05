# -*- coding: utf-8 -*-
"""Generates the language-breakdown chart in dark + light variants.

Plots two smoothed series over the same set of languages -- share of code
written, and share of repositories led -- so the gap between them is the
interesting part: where the two lines diverge is where a language does a lot
of work in a few places, or a little work in many.

    python tools/gen_langs.py            # redraw from the stored counts
    python tools/gen_langs.py --fetch    # re-read the counts from GitHub first

The stored counts are a snapshot: the chart does not update itself, so re-run
with --fetch when the language mix has moved enough to matter.
"""
import json, io, os

TOP = 7          # languages on the x axis
W, H = 1000, 300
L, R = 92, 940   # gridlines span this
PL, PR = 128, 904  # points sit inset from the gridlines, so the outer x labels
                   # clear the y-axis figures and the card edge
T, B = 84, 236   # plot band, top (= YMAX) and baseline (= 0%)
YMAX, YSTEP = 40.0, 10.0

THEMES = {
    "dark":  dict(bg1="#090D15", bg2="#101825", border="#1E2839", grid="#1B2434",
                  label="#5E6B7D", name="#C6D0DC", axis="#8E9EB2",
                  a="#4D9DFF", b="#3DD6C0"),
    "light": dict(bg1="#FFFFFF", bg2="#F1F5FA", border="#DFE7F1", grid="#E7EDF5",
                  label="#8996A8", name="#2C3646", axis="#6B7889",
                  a="#1565D8", b="#0E9C8A"),
}

FONT = ("font-family: 'Segoe UI', Inter, system-ui, -apple-system, "
        "BlinkMacSystemFont, Helvetica, Arial, sans-serif")


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def axis_langs(data):
    """The languages worth an x slot, ordered by share of code.

    Ranked on whichever of the two shares is larger, so a language that leads
    several repos still earns a slot even when it is a thin slice by bytes.

    Both sorts carry full tie-breaks. Ranking on the larger share alone ties
    readily -- one repo out of 21 is 4.76% for every language that leads
    exactly one -- and leaving those ties to set iteration order would let the
    chart pick a different language each time it is regenerated.
    """
    tb = float(sum(data["by_bytes"].values()))
    tr = float(sum(data["by_repo"].values()))
    keys = set(data["by_bytes"]) | set(data["by_repo"])
    code = lambda k: 100.0 * data["by_bytes"].get(k, 0) / tb
    repo = lambda k: 100.0 * data["by_repo"].get(k, 0) / tr
    top = sorted(keys, key=lambda k: (-max(code(k), repo(k)), -code(k), k))[:TOP]
    top.sort(key=lambda k: (-code(k), k))
    return top, [code(k) for k in top], [repo(k) for k in top]


def xy(i, n, pct):
    return (PL + (PR - PL) * i / float(n - 1), B - (B - T) * min(pct, YMAX) / YMAX)


def smooth(pts):
    """Catmull-Rom through the points, emitted as cubic beziers.

    Control points are clamped to the plot band: a spline through an uneven
    series will happily overshoot, and a curve that dips under 0% or climbs
    past the top gridline would be reading as data that is not there.
    """
    clip = lambda y: max(T, min(B, y))
    d = ["M%.1f %.1f" % pts[0]]
    for i in range(len(pts) - 1):
        p0 = pts[i - 1] if i else pts[0]
        p1, p2 = pts[i], pts[i + 1]
        p3 = pts[i + 2] if i + 2 < len(pts) else p2
        d.append("C%.1f %.1f %.1f %.1f %.1f %.1f" % (
            p1[0] + (p2[0] - p0[0]) / 6.0, clip(p1[1] + (p2[1] - p0[1]) / 6.0),
            p2[0] - (p3[0] - p1[0]) / 6.0, clip(p2[1] - (p3[1] - p1[1]) / 6.0),
            p2[0], p2[1]))
    return " ".join(d)


def plot(w, series):
    """Both series, one layer at a time: fills, then lines, then markers.

    Drawn series by series instead, the second area wash would tint the first
    line wherever the two cross. Markers are solid rather than knocked out of
    the card colour -- the two shares land within a couple of points of each
    other at the thin end, and a knockout dot there punches a hole in its
    neighbour and reads as a rendering fault.
    """
    laid = []
    for vals, colour, key in series:
        pts = [xy(i, len(vals), v) for i, v in enumerate(vals)]
        laid.append((smooth(pts), pts, colour, key))

    for line, pts, colour, key in laid:
        w('    <path d="%s L%.1f %d L%.1f %d Z" fill="url(#fill%s)"/>\n'
          % (line, pts[-1][0], B, pts[0][0], B, key))
    for line, pts, colour, key in laid:
        w('    <path d="%s" fill="none" stroke="%s" stroke-width="2.4" '
          'stroke-linecap="round" stroke-linejoin="round"/>\n' % (line, colour))
    for line, pts, colour, key in laid:
        for x, y in pts:
            w('    <circle cx="%.1f" cy="%.1f" r="3.2" fill="%s"/>\n' % (x, y, colour))


def legend(w, x, y, colour, text, c):
    w('    <circle cx="%d" cy="%d" r="4" fill="%s"/>\n' % (x, y - 4, colour))
    w('    <text x="%d" y="%d" font-size="12.5" font-weight="500" fill="%s">%s</text>\n'
      % (x + 12, y, c["axis"], text))


def build(theme, data):
    c = THEMES[theme]
    langs, by_code, by_repo = axis_langs(data)
    o = io.StringIO(); w = o.write

    w('<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d" '
      'role="img" aria-label="Share of code written and share of repositories led, '
      'per language, across %d public repositories">\n' % (W, H, W, H, data["n_repos"]))

    w('  <defs>\n')
    w('    <linearGradient id="lbg" x1="0" y1="0" x2="1" y2="1">'
      '<stop offset="0%%" stop-color="%s"/><stop offset="100%%" stop-color="%s"/>'
      '</linearGradient>\n' % (c["bg1"], c["bg2"]))
    for key, colour, top in (("A", c["a"], "0.26"), ("B", c["b"], "0.16")):
        w('    <linearGradient id="fill%s" x1="0" y1="0" x2="0" y2="1">'
          '<stop offset="0%%" stop-color="%s" stop-opacity="%s"/>'
          '<stop offset="100%%" stop-color="%s" stop-opacity="0"/></linearGradient>\n'
          % (key, colour, top, colour))
    w('  </defs>\n')
    w('  <rect width="%d" height="%d" rx="18" fill="url(#lbg)"/>\n' % (W, H))
    w('  <g style="%s">\n' % FONT)

    w('    <text x="60" y="46" font-size="12" font-weight="600" letter-spacing="1.6" fill="%s">'
      'LANGUAGE MIX · %d PUBLIC REPOS</text>\n' % (c["label"], data["n_repos"]))
    legend(w, 640, 46, c["a"], "Share of code", c)
    legend(w, 800, 46, c["b"], "Share of repos", c)

    # horizontal rules, labelled on the left; the 0% rule doubles as the axis
    v = 0.0
    while v <= YMAX + 0.01:
        y = B - (B - T) * v / YMAX
        w('    <line x1="%d" y1="%.1f" x2="%d" y2="%.1f" stroke="%s" stroke-width="1"/>\n'
          % (L, y, R, y, c["grid"]))
        w('    <text x="%d" y="%.1f" font-size="11.5" font-weight="500" text-anchor="end" '
          'fill="%s">%d%%</text>\n' % (L - 14, y + 4, c["label"], int(v)))
        v += YSTEP

    plot(w, [(by_repo, c["b"], "B"), (by_code, c["a"], "A")])

    for i, nm in enumerate(langs):
        w('    <text x="%.1f" y="%d" font-size="13" font-weight="600" text-anchor="middle" '
          'fill="%s">%s</text>\n' % (xy(i, len(langs), 0)[0], B + 30, c["name"], esc(nm)))

    w('  </g>\n')
    w('  <rect x="0.5" y="0.5" width="%d" height="%d" rx="18" fill="none" stroke="%s"/>\n'
      % (W - 1, H - 1, c["border"]))
    w('</svg>\n')
    return o.getvalue()


def fetch(user="SabbirMurad"):
    """Re-read the language split from the GitHub API into langs.json.

    Unauthenticated requests are limited to 60/hour and this makes one per repo,
    so set GITHUB_TOKEN if it starts coming back 403.
    """
    import urllib.request, collections
    tok = os.environ.get("GITHUB_TOKEN")
    def get(u):
        h = {"User-Agent": "gen_langs", "Accept": "application/vnd.github+json"}
        if tok:
            h["Authorization"] = "Bearer " + tok
        return json.load(urllib.request.urlopen(urllib.request.Request(u, headers=h), timeout=30))

    repos = [r for r in get("https://api.github.com/users/%s/repos?per_page=100" % user)
             if not r["fork"]]
    by_bytes, by_repo = collections.Counter(), collections.Counter()
    for r in repos:
        if r["language"]:
            by_repo[r["language"]] += 1
        for lang, b in get(r["languages_url"]).items():
            by_bytes[lang] += b
    return {"by_bytes": dict(by_bytes), "by_repo": dict(by_repo), "n_repos": len(repos)}


if __name__ == "__main__":
    import sys
    here = os.path.dirname(os.path.abspath(__file__))
    root = os.path.dirname(here)
    store = os.path.join(here, "langs.json")

    if "--fetch" in sys.argv:
        data = fetch()
        json.dump(data, open(store, "w"), indent=1)
        print("refreshed %s from the GitHub API (%d repos)" % (store, data["n_repos"]))
    else:
        data = json.load(open(store))

    for t in THEMES:
        p = os.path.join(root, "assets", "languages-%s.svg" % t)
        open(p, "w", encoding="utf-8").write(build(t, data))
        print("%s  %d bytes" % (p, os.path.getsize(p)))
