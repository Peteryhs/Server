#!/usr/bin/env python3
import math, base64, pathlib, subprocess

GOLD = "#f2b800"; BLUE = "#2662d6"; RED = "#c3372b"; GREEN = "#3aa86b"
ORBIT = "#c9cdd4"; INK = "#161616"; BG = "#fafafa"; GRID = "#e7e9ee"

def b64(p):
    return base64.b64encode(pathlib.Path(p).read_bytes()).decode()

def style_fonts():
    mc = b64("/home/peter/.hermes/attachments/Minecraft.ttf")
    return (f'<style>'
            f'@font-face{{font-family:"Minecraft";src:url(data:font/ttf;base64,{mc});}}'
            f'</style>')

def measure(s, size=64):
    out = subprocess.run(
        ["magick", "-background", "none", "-font", "Minecraft", "-pointsize", str(size),
         "label:" + s, "-trim", "-format", "%w %h", "info:"],
        capture_output=True, text=True)
    w, h = out.stdout.split()
    return int(w), int(h)

def grid(w, h, step=28):
    out = []
    for x in range(step, w, step):
        out.append(f'<line x1="{x}" y1="0" x2="{x}" y2="{h}" stroke="{GRID}" stroke-width="1"/>')
    for y in range(step, h, step):
        out.append(f'<line x1="0" y1="{y}" x2="{w}" y2="{y}" stroke="{GRID}" stroke-width="1"/>')
    return out

def sat_xy(cx, cy, R, deg):
    r = math.radians(deg)
    return (cx + R * math.cos(r), cy + R * math.sin(r))

def orbit_mark(cx, cy, R, center=60, sat=36):
    els = []
    els.append(f'<circle cx="{cx}" cy="{cy}" r="{R}" fill="none" stroke="{ORBIT}" stroke-width="1.5"/>')
    els.append(f'<rect x="{cx-center/2:.1f}" y="{cy-center/2:.1f}" width="{center}" height="{center}" fill="{GOLD}"/>')
    # symmetric equilateral rotated +20deg along the orbit: blue 10:40, red 2:40, green 6:40
    for deg, color in ((230, BLUE), (350, RED), (110, GREEN)):
        x, y = sat_xy(cx, cy, R, deg)
        els.append(f'<rect x="{x-sat/2:.1f}" y="{y-sat/2:.1f}" width="{sat}" height="{sat}" fill="{color}"/>')
    return els

def lockup(fs=93, gap=100):
    W, H = 1100, 300
    cx0 = W / 2                # frame centre (composite is centred as a whole)
    wx, _ = measure("Sun", fs)
    wy, _ = measure("Systems", fs)
    R = 84
    cy = 150
    ty = cy + fs * 0.312       # measured: ink centre sits 0.312*fs below mark centre (Minecraft font)
    # composite = Sun-text + gap + mark(width 2R) + gap + Systems-text
    total = wx + gap + 2 * R + gap + wy
    left = cx0 - total / 2
    sun_x = left                          # left edge of "Sun"
    mark_x = left + wx + gap + R          # centre of the logo mark
    sys_x = left + wx + gap + 2 * R + gap # left edge of "Systems"
    els = [f'<rect x="0" y="0" width="{W}" height="{H}" fill="{BG}"/>']
    els += grid(W, H)
    # wide elliptical fade to white along the whole bottom row; stretches across the
    # full width (objectBoundingBox becomes an ellipse on this wide canvas) and falls
    # off quickly upward so the top grid stays visible
    els.append('<defs><radialGradient id="bfade" cx="50%" cy="100%" r="100%" fx="50%" fy="100%">'
               '<stop offset="0%" stop-color="#ffffff" stop-opacity="1"/>'
               '<stop offset="45%" stop-color="#ffffff" stop-opacity="0.55"/>'
               '<stop offset="78%" stop-color="#ffffff" stop-opacity="0.12"/>'
               '<stop offset="100%" stop-color="#ffffff" stop-opacity="0"/>'
               '</radialGradient></defs>')
    els.append(f'<rect x="0" y="0" width="{W}" height="{H}" fill="url(#bfade)"/>')
    els.append(style_fonts())
    els.append(f'<text x="{sun_x:.1f}" y="{ty:.1f}" font-family="Minecraft" font-size="{fs}" fill="{INK}">Sun</text>')
    els.append(f'<text x="{sys_x:.1f}" y="{ty:.1f}" font-family="Minecraft" font-size="{fs}" fill="{INK}">Systems</text>')
    els += orbit_mark(mark_x, cy, R)
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">' + "".join(els) + '</svg>', wx, wy

svg, wx, wy = lockup()
pathlib.Path("/tmp/ss-lockup.svg").write_text(svg)
print(f"Sun width={wx}px, Systems width={wy}px")
print("gap each side of mark:", 46)

def mark_only():
    S = 260; cx = S/2; cy = S/2; R = 92
    els = [f'<rect x="0" y="0" width="{S}" height="{S}" fill="{BG}"/>']
    els += grid(S, S, 26)
    els.append(style_fonts())
    els += orbit_mark(cx, cy, R, center=68, sat=40)
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{S}" height="{S}" viewBox="0 0 {S} {S}">' + "".join(els) + '</svg>'
pathlib.Path("/tmp/ss-mark.svg").write_text(mark_only())
print("wrote ss-mark.svg")

def mark_clear():
    # transparent-background mark: no bg rect, no grid -- real asset use
    S = 260; cx = S/2; cy = S/2; R = 92
    els = []
    els += orbit_mark(cx, cy, R, center=68, sat=40)
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{S}" height="{S}" viewBox="0 0 {S} {S}">' + "".join(els) + '</svg>'
pathlib.Path("/tmp/ss-mark-clear.svg").write_text(mark_clear())
print("wrote ss-mark-clear.svg")

def wordmark(fs=93, gap=64):
    W, H = 900, 260
    wx, _ = measure("Sun", fs)
    wy, _ = measure("Systems", fs)
    ty = H / 2 + fs * 0.5
    total = wx + gap + wy
    left = (W - total) / 2
    els = [f'<rect x="0" y="0" width="{W}" height="{H}" fill="{BG}"/>']
    els += grid(W, H)
    els.append('<defs><radialGradient id="bfade" cx="50%" cy="100%" r="100%" fx="50%" fy="100%">'
               '<stop offset="0%" stop-color="#ffffff" stop-opacity="1"/>'
               '<stop offset="45%" stop-color="#ffffff" stop-opacity="0.4"/>'
               '<stop offset="100%" stop-color="#ffffff" stop-opacity="0"/>'
               '</radialGradient></defs>')
    els.append(f'<rect x="0" y="0" width="{W}" height="{H}" fill="url(#bfade)"/>')
    els.append(style_fonts())
    els.append(f'<text x="{left:.1f}" y="{ty:.1f}" font-family="Minecraft" font-size="{fs}" fill="{INK}">Sun</text>')
    els.append(f'<text x="{left+wx+gap:.1f}" y="{ty:.1f}" font-family="Minecraft" font-size="{fs}" fill="{INK}">Systems</text>')
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">' + "".join(els) + '</svg>'
pathlib.Path("/tmp/ss-wordmark.svg").write_text(wordmark())
print("wrote ss-wordmark.svg")

def wordmark_clear(fs=93, gap=64, pad=40):
    # transparent-background wordmark: tight canvas around the text
    wx, _ = measure("Sun", fs)
    wy, _ = measure("Systems", fs)
    total = wx + gap + wy
    W = int(total + pad * 2); H = 260
    left = pad
    # measured: Minecraft font ink spans ~0.758*fs above baseline, ~0.134*fs below,
    # so the visually-centered baseline is H/2 + fs*(0.758-0.134)/2
    ty = H / 2 + fs * 0.312
    els = []
    els.append(style_fonts())
    els.append(f'<text x="{left:.1f}" y="{ty:.1f}" font-family="Minecraft" font-size="{fs}" fill="{INK}">Sun</text>')
    els.append(f'<text x="{left+wx+gap:.1f}" y="{ty:.1f}" font-family="Minecraft" font-size="{fs}" fill="{INK}">Systems</text>')
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">' + "".join(els) + '</svg>'
pathlib.Path("/tmp/ss-wordmark-clear.svg").write_text(wordmark_clear())
print("wrote ss-wordmark-clear.svg")

def lockup_clear(fs=93, gap=100, pad=30):
    # transparent-background full lockup: Sun + mark + Systems, no bg/grid/fade,
    # tight canvas around the whole composite
    wx, _ = measure("Sun", fs)
    wy, _ = measure("Systems", fs)
    R = 84
    total = wx + gap + 2 * R + gap + wy
    W = int(total + pad * 2); H = 300
    cy = H / 2
    left = pad
    sun_x = left
    mark_x = left + wx + gap + R
    sys_x = left + wx + gap + 2 * R + gap
    ty = cy + fs * 0.312
    els = []
    els.append(style_fonts())
    els.append(f'<text x="{sun_x:.1f}" y="{ty:.1f}" font-family="Minecraft" font-size="{fs}" fill="{INK}">Sun</text>')
    els.append(f'<text x="{sys_x:.1f}" y="{ty:.1f}" font-family="Minecraft" font-size="{fs}" fill="{INK}">Systems</text>')
    els += orbit_mark(mark_x, cy, R)
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">' + "".join(els) + '</svg>'
pathlib.Path("/tmp/ss-lockup-clear.svg").write_text(lockup_clear())
print("wrote ss-lockup-clear.svg")