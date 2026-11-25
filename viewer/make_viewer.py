import base64, sys
from pathlib import Path
here = Path(__file__).resolve().parent
sys.path.insert(0, str(here.parent / 'src'))
import case as c
from board import board
b = board()
def b64(m):
    return base64.b64encode(c.to_trimesh(m).export(file_type='stl')).decode()
parts = [  # name, solid, colour, opacity, group
    ('case', c.case(), '0xff6a2a', 1, 'alt'),
    ('case minimal', c.case(minimal=True, towers=False), '0xff6a2a', 1, 'alt'),
    ('case minimal bridge', c.case(minimal=True), '0xff6a2a', 1, 'new'),
    ('bridge', c.bridge(), '0xffa64d', 1, 'new'),
    ('clip', c.clip(), '0xffd24d', 1, 'new'),
    ('board', b['board'], '0x2b6cd4', 1, 'board'),
    ('housing', b['housing'], '0x222222', 1, 'board'),
    ('module', b['module'], '0x2b6cd4', 1, 'board'),
    ('plug', b['plug'], '0x222222', 1, 'board'),
]
js = ',\n'.join(f"['{n}','{b64(m)}',{col},{a},'{g}']" for n, m, col, a, g in parts)
(here / 'viewer.html').write_text((here / 'template.html').read_text().replace('%PARTS%', js))
