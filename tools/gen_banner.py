# -*- coding: utf-8 -*-
"""Generates the animated constellation banner in dark + light variants.

Animation uses SMIL (<animate>) rather than CSS keyframes: GitHub serves the
README image through camo into an <img>, and SMIL is the better-supported of
the two in that context.

Every animated element carries a static attribute value that is correct on its
own, so if animation never runs the banner still renders complete.
"""
import math, io, os

CYCLE       = 9.0     # seconds; every animation shares this period so flares stay in sync with pulses
TRAVEL_FRAC = 0.44    # fraction of the cycle a pulse spends travelling its path
TRAVEL_S    = CYCLE * TRAVEL_FRAC

SPINE   = [(575,88),(632,150),(700,106),(818,142),(902,96),(952,140),(884,190),(976,210)]
BRANCH1 = [(575,88),(690,44),(806,68),(902,96),(944,46)]
BRANCH2 = [(632,150),(600,214),(770,226),(742,182),(818,142),(884,190)]
PATHS   = [(SPINE, 0.0), (BRANCH1, 2.2), (BRANCH2, 4.4)]   # (polyline, start time in cycle)

STUBS = [[(952,140),(1014,116)], [(944,46),(1008,16)],
         [(600,214),(554,262)],  [(976,210),(1020,246)]]

RADIUS = {(575,88):2.2,(632,150):2.6,(700,106):2.4,(818,142):4.6,(902,96):3.0,
          (952,140):2.0,(884,190):2.8,(976,210):2.2,(690,44):1.6,(806,68):2.2,
          (944,46):1.6,(600,214):1.8,(770,226):1.8,(742,182):2.0}
ACCENT_STARS = {(818,142),(902,96),(884,190)}
HERO = (818,142)

FAINT = [(508,120),(534,196),(560,44),(596,120),(618,72),(654,244),(676,166),
         (722,58),(736,132),(764,20),(792,206),(838,34),(860,110),(872,242),
         (916,160),(930,222),(962,84),(986,166)]

THEMES = {
 "dark":  dict(bg1="#090D15", bg2="#101825", border="#1E2839", accent="#4D9DFF",
               star="#8E9EB2", faint="#26324A", strong=".42", soft=".20", glow=".30",
               name="#E9EEF4", role="#98A4B4", meta="#5E6B7D"),
 "light": dict(bg1="#FFFFFF", bg2="#F1F5FA", border="#DFE7F1", accent="#1565D8",
               star="#93A5BC", faint="#DCE5F1", strong=".38", soft=".18", glow=".15",
               name="#0B0E14", role="#4A5567", meta="#8996A8"),
}

# Readers who ask for less motion get the static constellation.
REDUCED = """  <style>
    @media (prefers-reduced-motion: reduce) { .pulse, .halo { display: none } }
  </style>
"""


def anim(attr, values, keytimes, begin, dur=CYCLE):
    return ('<animate attributeName="%s" values="%s" keyTimes="%s" dur="%gs" '
            'begin="%gs" repeatCount="indefinite" calcMode="linear"/>'
            % (attr, values, keytimes, dur, begin))


def d_attr(pts):
    return "M" + " L".join("%g %g" % p for p in pts)


def arrivals(poly, start):
    """Wall-clock time within the cycle at which the pulse reaches each vertex."""
    segs = [math.dist(poly[i], poly[i + 1]) for i in range(len(poly) - 1)]
    total = sum(segs)
    out, run = [], 0.0
    for i, p in enumerate(poly):
        out.append((p, start + (run / total) * TRAVEL_S))
        if i < len(segs):
            run += segs[i]
    return out


def build(t):
    c = THEMES[t]
    # first path to reach a node owns its flare timing
    flare_at = {}
    for poly, start in PATHS:
        for pt, when in arrivals(poly, start):
            flare_at.setdefault(pt, when)

    o = io.StringIO()
    w = o.write
    w('<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="260" viewBox="0 0 1000 260" '
      'role="img" aria-label="Sabbir Hassan \u2014 Full-stack developer and designer">\n')

    w('  <defs>\n')
    w('    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">'
      '<stop offset="0%%" stop-color="%s"/><stop offset="100%%" stop-color="%s"/></linearGradient>\n'
      % (c["bg1"], c["bg2"]))
    w('    <linearGradient id="rule" x1="0" y1="0" x2="1" y2="0">'
      '<stop offset="0%%" stop-color="%s"/><stop offset="100%%" stop-color="%s" stop-opacity="0.15"/></linearGradient>\n'
      % (c["accent"], c["accent"]))
    w('    <radialGradient id="glow"><stop offset="0%%" stop-color="%s" stop-opacity="%s"/>'
      '<stop offset="100%%" stop-color="%s" stop-opacity="0"/></radialGradient>\n'
      % (c["accent"], c["glow"], c["accent"]))
    w('    <radialGradient id="flash"><stop offset="0%%" stop-color="%s" stop-opacity="0.85"/>'
      '<stop offset="100%%" stop-color="%s" stop-opacity="0"/></radialGradient>\n'
      % (c["accent"], c["accent"]))
    w('    <clipPath id="card"><rect x="0.5" y="0.5" width="999" height="259" rx="18"/></clipPath>\n')
    # Blur turns the stacked beam layers into one seamless falloff instead of
    # steps you can pick out. userSpaceOnUse keeps the region off the path bbox.
    w('    <filter id="beamGlow" filterUnits="userSpaceOnUse" x="0" y="0" width="1000" height="260">'
      '<feGaussianBlur stdDeviation="3.2"/></filter>\n')
    w('    <filter id="beamCore" filterUnits="userSpaceOnUse" x="0" y="0" width="1000" height="260">'
      '<feGaussianBlur stdDeviation="0.7"/></filter>\n')
    w('  </defs>\n')
    w(REDUCED)

    w('  <g clip-path="url(#card)">\n')
    w('    <rect width="1000" height="260" fill="url(#bg)"/>\n')

    # faint background field, slow uncorrelated twinkle
    w('    <g fill="%s">\n' % c["faint"])
    for i, (x, y) in enumerate(FAINT):
        w('      <circle cx="%g" cy="%g" r="%g" opacity="1">%s</circle>\n'
          % (x, y, 1 + (i % 3) * 0.1,
             anim("opacity", "0.35;1;0.35", "0;0.5;1", (i * 0.83) % 7, dur=7)))
    w('    </g>\n')

    # static beams
    w('    <g stroke="%s" fill="none" stroke-linecap="round">\n' % c["accent"])
    w('      <g stroke-width="1" stroke-opacity="%s"><path d="%s"/></g>\n' % (c["strong"], d_attr(SPINE)))
    w('      <g stroke-width="0.9" stroke-opacity="%s">\n' % c["soft"])
    for poly in [BRANCH1, BRANCH2] + STUBS:
        w('        <path d="%s"/>\n' % d_attr(poly))
    w('      </g>\n    </g>\n')

    # Travelling pulses. A single dash of fixed length renders as a solid capsule,
    # which reads as a moving bar rather than light. Each beam is instead a stack of
    # dashes sharing one centre: long+thin+faint through to short+wide+bright, so the
    # beam is hot and thick in the middle and tapers away at both head and tail.
    #
    # Stacking alone leaves visible steps where one layer ends and the next begins, so
    # the whole envelope goes through a Gaussian blur -- that turns the discrete layers
    # into one continuous falloff. The crisp filament is drawn separately on top, only
    # lightly softened, so the centre still reads as a hot core.
    #
    # (dash length, stroke width, peak opacity) -- painted back to front
    envelope = [(30.0, 3.0, 0.28), (18.0, 4.0, 0.40), (10.0, 5.0, 0.55), (4.0, 6.0, 0.64)]
    core     = [(5.0, 1.5, 0.78)]

    def emit_beams(spec, filt):
        w('    <g stroke="%s" fill="none" stroke-linecap="round" filter="url(#%s)">\n' % (c["accent"], filt))
        for poly, start in PATHS:
            for length, width, peak in spec:
                # Dash period is longer than the path so the pattern cannot repeat and
                # leave a stray copy at the far end. Centre travels 0 -> 100.
                head, tail = length / 2.0, length / 2.0 - 100.0
                w('      <path class="pulse" d="%s" pathLength="100" stroke-width="%g" '
                  'stroke-dasharray="%g 300" opacity="0">%s%s</path>\n'
                  % (d_attr(poly), width, length,
                     anim("stroke-dashoffset", "%g;%g;%g" % (head, tail, tail), "0;0.44;1", start),
                     anim("opacity", "0;%s;%s;0;0" % (peak, peak), "0;0.04;0.4;0.44;1", start)))
        w('    </g>\n')

    emit_beams(envelope, "beamGlow")
    emit_beams(core, "beamCore")

    # hero glow, slow breath
    w('    <circle cx="%g" cy="%g" r="26" fill="url(#glow)" opacity="1">%s</circle>\n'
      % (HERO[0], HERO[1], anim("opacity", "0.7;1;0.7", "0;0.5;1", 0, dur=6)))

    # halo flash as the pulse arrives at each star
    w('    <g>\n')
    for pt, when in sorted(flare_at.items()):
        r = max(10.0, RADIUS[pt] * 4.0)
        w('      <circle class="halo" cx="%g" cy="%g" r="%g" fill="url(#flash)" opacity="0">%s</circle>\n'
          % (pt[0], pt[1], r, anim("opacity", "0;0.7;0;0", "0;0.03;0.18;1", when)))
    w('    </g>\n')

    # stars, dimmed between arrivals
    for fill, group in ((c["star"], [p for p in RADIUS if p not in ACCENT_STARS]),
                        (c["accent"], [p for p in RADIUS if p in ACCENT_STARS])):
        w('    <g fill="%s">\n' % fill)
        for pt in sorted(group):
            w('      <circle cx="%g" cy="%g" r="%g" opacity="1">%s</circle>\n'
              % (pt[0], pt[1], RADIUS[pt],
                 anim("opacity", "0.5;1;0.5;0.5", "0;0.02;0.14;1", flare_at[pt])))
        w('    </g>\n')

    w('  </g>\n')
    w('  <rect x="0.5" y="0.5" width="999" height="259" rx="18" fill="none" stroke="%s"/>\n' % c["border"])

    w("  <g style=\"font-family: 'Segoe UI', Inter, system-ui, -apple-system, BlinkMacSystemFont, Helvetica, Arial, sans-serif\">\n")
    w('    <rect x="60" y="62" width="46" height="4" rx="2" fill="url(#rule)"/>\n')
    w('    <text x="60" y="128" font-size="46" font-weight="700" letter-spacing="-1.2" fill="%s">Sabbir Hassan</text>\n' % c["name"])
    w('    <text x="60" y="164" font-size="19" font-weight="500" letter-spacing="0.1" fill="%s">Full-stack developer &amp; designer</text>\n' % c["role"])
    w('    <text x="60" y="199" font-size="13.5" font-weight="500" letter-spacing="1.6" fill="%s">RUST  \u00b7  FLUTTER  \u00b7  TYPESCRIPT  \u00b7  SABBIRHASSAN.COM</text>\n' % c["meta"])
    w('  </g>\n</svg>\n')
    return o.getvalue()


if __name__ == "__main__":
    out = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")
    for t in THEMES:
        p = os.path.join(out, "banner-%s.svg" % t)
        open(p, "w", encoding="utf-8").write(build(t))
        print("%s  %d bytes" % (p, os.path.getsize(p)))
