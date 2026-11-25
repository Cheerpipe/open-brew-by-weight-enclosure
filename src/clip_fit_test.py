"""Fit-test plate: four clips with growing socket clearance, to print together and find the size that slides onto
the bridge horns. Run: python clip_fit_test.py [out.stl]. Left to right the clearance grows; the number of grooves
on the back of each clip is its position (1 = tightest)."""
import sys
from pathlib import Path
import numpy as np
import trimesh
from manifold3d import Manifold
import case as c

CLEARANCES = (0.17, 0.19, 0.21, 0.23)
GAP = 4.0

parts = []
x = 0.0
for i, cl in enumerate(CLEARANCES, 1):
    m = c.to_trimesh(c.clip(clear=cl))
    m.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, (1, 0, 0)))  # socket mouths on the bed
    m.apply_translation(-m.bounds[0])
    w, d, h = m.extents
    # grooves on the back (top face), one per position
    cuts = [trimesh.creation.box((w * 0.6, 0.5, 0.8), trimesh.transformations.translation_matrix((w / 2, d / 2 + (k - (i - 1) / 2) * 1.4, h)))
            for k in range(i)]
    to_m = lambda t: Manifold(c.m3d.Mesh(vert_properties=np.asarray(t.vertices, np.float32), tri_verts=np.asarray(t.faces, np.uint32)))
    mf = to_m(m)
    for g in cuts:
        mf = mf - to_m(g)
    t = c.to_trimesh(mf)
    t.apply_translation((x, 0, 0))
    x += w + GAP
    parts.append(t)
    print(f"clip {i}: clearance {cl} mm, size {np.round(m.extents, 2)}")

out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent / "print" / "clip-fit-test" / "openbrewbyweight-clip-fit-test.stl"
out.parent.mkdir(parents=True, exist_ok=True)
plate = trimesh.util.concatenate(parts)
plate.export(out)
print("wrote", out, "extents", np.round(plate.extents, 1))
