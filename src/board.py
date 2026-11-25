"""Approximate model of the ESP32-S3 Relay X1 board and buzzer module, in the case frame.

Positions come from the dimensioned layout and photos (about +/-1 mm). Board frame:
u = mm from the board's left edge and v = mm from its top edge with the relay at
top-left, mapped to the case as x = -17.2 - v, y = 12.9 - u.
"""
from manifold3d import Manifold
from case import SUPPORT_TOP, PCB_T, HEADER_BASE, HOUSING_C, HOUSING_W, HOUSING_L, HOUSING_H, PCB_HOLES, BULK_CAP, SMALL_CAP, SPK_HOLE, SPK_SIZE, SPK_END_X, box, union

TOP = SUPPORT_TOP + PCB_T
PITCH = 2.54


def uv_box(u0, v0, u1, v1, h, z0=TOP):
    return box(-17.2 - v1, 12.9 - u1, z0, -17.2 - v0, 12.9 - u0, z0 + h)


def can(x, y, d, h, z0=TOP):
    return Manifold.cylinder(h, d / 2, circular_segments=48).translate((x, y, z0))


def pins(xs, ys, h, z0):
    return union([box(x - 0.32, y - 0.32, z0, x + 0.32, y + 0.32, z0 + h) for x in xs for y in ys])


def header_2x10(x_rows, y_first):
    ys = [y_first - i * PITCH for i in range(10)]
    base = box(min(x_rows) - 1.27, ys[-1] - 1.27, TOP, max(x_rows) + 1.27, ys[0] + 1.27, TOP + HEADER_BASE)
    return base + pins(x_rows, ys, 8.5, TOP)


def board():
    pcb = box(-74.7, -40.8, SUPPORT_TOP, -17.2, 12.9, TOP)
    pcb -= union([Manifold.cylinder(3, 1.5, circular_segments=32).translate((x, y, SUPPORT_TOP - 1)) for x, y in PCB_HOLES])
    parts = [
        uv_box(0.3, 7.8, 17.4, 28.7, 15.5),          # relay
        uv_box(0.6, 0.3, 17.4, 7.8, 10.0),           # relay terminal
        uv_box(6.2, 49.7, 17.7, 57.5, 10.0),         # power terminal
        uv_box(31.9, 49.4, 40.1, 57.8, 3.3),         # USB-C receptacle
        uv_box(26.8, 9.2, 53.7, 27.9, 3.2),          # ESP32-S3 module
        header_2x10((-18.9, -21.44), 10.4),          # upper header
        header_2x10((-53.26, -50.83), -10.22),       # lower header (dupont)
        pins([-29.5 - i * PITCH for i in range(6)], [-10.0], 8.5, TOP) + box(-44.0, -11.27, TOP, -28.2, -8.73, TOP + HEADER_BASE),  # P4
        can(*SMALL_CAP),                              # small electrolytic
        can(*BULK_CAP),                               # bulk electrolytic, at the board edge
        uv_box(20.0, 45.0, 26.0, 51.0, 4.0),         # inductor
    ]
    hx, hy = HOUSING_C
    z = TOP + HEADER_BASE
    housing = box(hx - HOUSING_W / 2, hy - HOUSING_L / 2, z, hx + HOUSING_W / 2, hy + HOUSING_L / 2, z + HOUSING_H)
    # Buzzer module board on its pad and end rest, buzzer at the far end, right-angle header towards the relay wall.
    (hx0, hy0), (ml, mw) = SPK_HOLE, SPK_SIZE
    module = box(SPK_END_X, hy0 - mw / 2, SUPPORT_TOP, SPK_END_X + ml, hy0 + mw / 2, TOP)
    module -= Manifold.cylinder(3, 1.5, circular_segments=32).translate((hx0, hy0, SUPPORT_TOP - 1))   # mounting hole, like the main board's
    module += can(SPK_END_X + 6.5, hy0, 12.0, 9.5)
    module += box(-44.0, -53.9, TOP, -41.5, -45.8, TOP + 2.5)              # right-angle header body
    plug = box(-42.4, -53.9, TOP, -28.4, -45.8, TOP + 2.6)                 # 1x3 dupont plug, ends 11.4 mm from the relay wall
    return {"board": union([pcb] + parts), "housing": housing, "module": module, "plug": plug}
