"""Render each kit in print/ assembled on the board to images/<kit>.png,
using a small numpy z-buffer rasterizer. Pass kit names to render only those."""
import sys
from pathlib import Path
import numpy as np

repo = Path(__file__).resolve().parent.parent
outdir = repo / "images"
sys.path.insert(0, str(repo / "src"))
import case as c
from board import board
from PIL import Image

SS = 2
W, H = 1000 * SS, 700 * SS


def hexrgb(h):
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], float) / 255


ORANGE, BRIDGE, CLIP = hexrgb("ff6a2a"), hexrgb("ffa64d"), hexrgb("ffd24d")
BLUE, BLACK = hexrgb("2b6cd4"), hexrgb("333333")


def board_parts():
    b = board()
    return [(b["board"], BLUE), (b["housing"], BLACK), (b["module"], BLUE), (b["plug"], BLACK)]


def render(parts, path, el=38, az=-125, dist=175, target=(-46, -22, 8)):
    tgt = np.array(target, float)
    e, a = np.radians(el), np.radians(az)
    eye = tgt + dist * np.array([np.cos(e) * np.cos(a), np.cos(e) * np.sin(a), np.sin(e)])
    f = tgt - eye
    f /= np.linalg.norm(f)
    r = np.cross(f, [0, 0, 1.0])
    r /= np.linalg.norm(r)
    u = np.cross(r, f)
    fy = 1 / np.tan(np.radians(30) / 2)
    light1 = np.array([0.45, -0.6, 0.75]); light1 /= np.linalg.norm(light1)
    light2 = np.array([-0.6, 0.3, 0.4]); light2 /= np.linalg.norm(light2)

    zbuf = np.full((H, W), np.inf)
    img = np.zeros((H, W, 3))
    for solid, col in parts:
        tm = c.to_trimesh(solid)
        v = tm.vertices - eye
        cam = np.stack([v @ r, v @ u, v @ f], 1)
        sx = (cam[:, 0] / cam[:, 2]) * fy * H / 2 + W / 2
        sy = -(cam[:, 1] / cam[:, 2]) * fy * H / 2 + H / 2
        n = tm.face_normals
        shade = 0.38 + 0.55 * np.clip(n @ light1, 0, 1) + 0.18 * np.clip(n @ light2, 0, 1)
        for fi, (i0, i1, i2) in enumerate(tm.faces):
            if n[fi] @ (tm.vertices[i0] - eye) >= 0:  # back face
                continue
            xs, ys, zs = sx[[i0, i1, i2]], sy[[i0, i1, i2]], cam[[i0, i1, i2], 2]
            x0, x1 = max(int(xs.min()), 0), min(int(xs.max()) + 1, W - 1)
            y0, y1 = max(int(ys.min()), 0), min(int(ys.max()) + 1, H - 1)
            if x1 < x0 or y1 < y0:
                continue
            px, py = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
            d = (ys[1] - ys[2]) * (xs[0] - xs[2]) + (xs[2] - xs[1]) * (ys[0] - ys[2])
            if abs(d) < 1e-12:
                continue
            w0 = ((ys[1] - ys[2]) * (px - xs[2]) + (xs[2] - xs[1]) * (py - ys[2])) / d
            w1 = ((ys[2] - ys[0]) * (px - xs[2]) + (xs[0] - xs[2]) * (py - ys[2])) / d
            w2 = 1 - w0 - w1
            inside = (w0 >= 0) & (w1 >= 0) & (w2 >= 0)
            if not inside.any():
                continue
            z = 1 / (w0 / zs[0] + w1 / zs[1] + w2 / zs[2])
            zb = zbuf[y0:y1 + 1, x0:x1 + 1]
            m = inside & (z < zb)
            zb[m] = z[m]
            img[y0:y1 + 1, x0:x1 + 1][m] = np.clip(col * shade[fi], 0, 1)

    hit = np.isfinite(zbuf)
    # Dark outlines where depth jumps, so edges read clearly.
    zf = np.where(hit, zbuf, zbuf[hit].max() + 50)
    gx = np.abs(np.diff(zf, axis=1, prepend=zf[:, :1]))
    gy = np.abs(np.diff(zf, axis=0, prepend=zf[:1]))
    edge = np.maximum(gx, gy) > 1.2
    img[edge & hit] *= 0.35
    rgba = np.dstack([img, hit.astype(float)])
    im = Image.fromarray((rgba * 255).astype(np.uint8), "RGBA")
    im = im.resize((W // SS, H // SS), Image.LANCZOS)
    bbox = im.getbbox()
    pad = 16
    im = im.crop((max(bbox[0] - pad, 0), max(bbox[1] - pad, 0), min(bbox[2] + pad, im.width), min(bbox[3] + pad, im.height)))
    im.save(path, optimize=True)
    print("wrote", path, im.size)


kits = {
    "1-full-case": [(c.case(), ORANGE), (c.bridge(), BRIDGE), (c.clip(), CLIP)],
    "2-minimal-case-and-bridge": [(c.case(minimal=True), ORANGE), (c.bridge(), BRIDGE), (c.clip(), CLIP)],
    "3-minimal-case-only": [(c.case(minimal=True, towers=False), ORANGE)],
}
outdir.mkdir(parents=True, exist_ok=True)
only = sys.argv[1:] or list(kits)
for name in only:
    render(kits[name] + board_parts(), outdir / f"{name}.png")
