"""Parametric case and dupont bridge for the ESP32-S3 Relay X1 board plus buzzer module.

Every dimension is measured from the original Tinkercad parts and kept in their
frame (case x -78..-14, y -60..16, z up from the bed) so new and old parts overlay.
Exports are moved to the origin and the bridge is flipped onto its top face for printing.
Run: python case.py [out_dir]
"""
from pathlib import Path
import numpy as np
import trimesh
import manifold3d as m3d
from manifold3d import CrossSection, Manifold, JoinType

SEG = 64

# --- Case (measured) -------------------------------------------------------
X0, X1, Y0, Y1 = -78.0, -14.0, -60.0, 16.0
WALL = 3.0
FLOOR = 3.2            # thick base: heat shield and warp resistance next to the hot boiler side
HEIGHT = 18.1
R_OUT, R_IN = 3.0, 1.0
CHAMFER_BOTTOM, CHAMFER_TOP = 0.5, 0.6
SUPPORT_TOP = 5.1      # PCB and buzzer module rest here: 1.9 mm under the board for solder joints
PCB_T = 1.6

# Fasteners: M2.5 everywhere (4x M2.5 x 4 screws).
SCREW_MODE = "selftap"  # "insert" = heat-set M2.5 x L3 x OD3.5, "selftap" = screw straight into PETG
INSERT_HOLE, SELFTAP_HOLE = 3.4, 2.4   # self-tap holes go all the way through boss and floor
BOSS_D = 6.5
PCB_HOLES = [(-72.2, 10.4), (-72.2, -38.6), (-19.7, -38.6)]
SPK_HOLE = (-57.2, -50.1)
SPK_PAD = (-63.4, -52.6, -51.4, -47.6)
# Buzzer module: 31.5 x 13 mm, hole 15.8 mm from the buzzer end. A second rest under the
# buzzer end keeps it from hanging; it stays clear of the buzzer solder joints (4.5 mm in).
SPK_SIZE, SPK_HOLE_FROM_END = (31.5, 13.0), 15.8
SPK_END_X = SPK_HOLE[0] - SPK_HOLE_FROM_END
SPK_REST = (SPK_END_X + 1.0, SPK_HOLE[1] - SPK_SIZE[1] / 2 + 0.5, SPK_END_X + 3.0, SPK_HOLE[1] + SPK_SIZE[1] / 2 - 0.5)

# Wall openings as (y0, y1, z0, z1, radius, x_from, x_to).
OPENINGS = [(-3.8, 6.2, 6.2, 13.2, 0.0, X0 - 1, X0 + WALL + 1),          # power terminal
            (-33.3, -14.3, 3.2, 14.2, 2.0, X0 - 1, X0 + 2.0),           # USB-C plug recess
            (-30.14, -17.46, 6.26, 11.14, 1.5, X0 + 1.9, X0 + WALL + 1),  # USB-C receptacle
            (-4.06, 11.84, 6.3, 16.3, 0.0, X1 - WALL - 1, X1 + 1)]      # relay terminal
# Cable labyrinth in the y = 16 wall, as (x0, x1, z0, z1) rectangles.
SLOT = [(-69.3, -67.3, 9.0, HEIGHT + 1), (-69.3, -64.1, 9.0, 11.0),
        (-65.9, -59.1, 10.6, 12.6), (-60.9, -51.3, 9.0, 11.0)]

# Snap joint between bridge legs and case walls.
SNAP_Y = (-35.4, -9.9)
SNAP_BUMP = [(0.0, 15.0), (1.2, 16.0), (1.2, 16.4), (0.0, 16.7)]   # (depth into wall, z): 1.2 mm hook, ~40 deg lead-in, retaining face only ~14 deg off flat
SNAP_CLEAR = 0.1

# Stop behind the buzzer module's right-angle dupont plugs, whose ends sit 11.4 mm from the
# relay-side wall (x -28.4). 1.5 mm of play absorbs measuring error and still keeps the pins
# engaged; the top stays under the wires leaving the plugs. None disables it.
SPK_STOP_FACE_X = -28.4 + 1.5
SPK_STOP_Y, SPK_STOP_TOP, SPK_STOP_T = (-55.0, -44.6), 7.3, 2.0

# --- Bridge (measured profile, z in case frame) ----------------------------
# The bridge prints on its side: the profile is extruded along y and the closed cap end (-y) sits on
# the bed, so legs, ledges and snaps need no supports. The snap bumps keep the measured groove length.
BRIDGE_START_Y = -38.6
SNAP_BUMP_Y = (-34.98, -10.32)
LEG_X = (-75.0, -74.0)            # left leg; the right one is mirrored about BRIDGE_AXIS
BRIDGE_AXIS = -46.0
LEG_BOTTOM = 14.9
# 2x10 dupont housing on the lower header (pin rows at x -53.26 / -50.83, average of layout and photo).
HOUSING_C = (-52.05, -21.65)
HOUSING_W, HOUSING_L, HOUSING_H = 5.1, 25.6, 14.0
HEADER_BASE = 2.5
CAP_CLEAR, CAP_WALL, CAP_LIP, CAP_BOTTOM = 0.45, 1.2, 0.45, 17.0
# The plate sits on the lips that hold the housing down: height = housing top + CAP_CLEAR + LIP_T +
# gap + plate thickness. Wires leave through the slit in the plate and bend there; a bigger gap gives them
# a longer straight run before the bend, at the cost of that much height.
LIP_T = 0.9
HOUSING_TOP = SUPPORT_TOP + PCB_T + HEADER_BASE + HOUSING_H
# Low profile with tunnel: no slit through the plate. A closed roof sits DUCT_H above the lips, and the wires, which
# bend over after rising through the slit between the lips, leave along y through the open ends of
# the duct under it, so they never cross the top. The duct has the same section along its whole length (y is the
# print axis), so it prints without supports. Plug the connector, fold the wires into a bundle towards the end
# you want, then lower the bridge over them.
DUCT_H, DUCT_W, DUCT_ROOF = 5.5, 8.0, 2.0
MIN_PLATE_T = 1.6     # plate of the minimal bridge
VARIANTS = {"original": dict(gap=3.45, t=3.0),      # gap above the lips, plate thickness: plate 28..31, top 31.0
            "lowprofile": dict(gap=0.0, t=2.0),     # plate on the lips, top 26.55
            "lowprofile-tunnel": dict(gap=DUCT_H, t=DUCT_ROOF, duct=True),
            # Lowest the housing allows: a thin plate flush with the lip tops, so the bridge tops out at 24.55.
            "minimal": dict(gap=-MIN_PLATE_T, t=MIN_PLATE_T, flush=True)}
DEFAULT_VARIANT = "lowprofile"


def plate_z(variant):
    """(underside, top) of the plate."""
    v = VARIANTS[variant]
    z0 = HOUSING_TOP + CAP_CLEAR + LIP_T + v["gap"]
    return (z0, z0 + v["t"])


def horn_z(variant):
    """Horns for the clip: short stubs from HORN_BOTTOM to HORN_TOP, the same on every variant and centred on the notch,
    so the clip, which is symmetric about the notch, fits any way up."""
    return (HORN_BOTTOM, HORN_TOP)


def bridge_profile(variant):
    """Left half, outer loop. The legs rise at 45 deg with a constant 3 mm strut: the outer edge passes through
    (-77, 20.3) and the inner one through (-74, 19.1), so both follow the plate height."""
    z0, z1 = plate_z(variant)
    if VARIANTS[variant].get("duct"):   # the strut ends in a square cut under the plate, which overlaps it
        return [(-77.0, 18.1), (-77.0, 20.3), (z1 - 97.3, z1), (z0 - 93.1, z0), (-74.0, 19.1),
                (-74.0, LEG_BOTTOM), (-75.0, LEG_BOTTOM), (-75.0, 18.1)]
    return [(-77.0, 18.1), (-77.0, 20.3), (z1 - 97.3, z1), (-64.0, z1), (-64.0, z0), (z0 - 93.1, z0),
            (-74.0, 19.1), (-74.0, LEG_BOTTOM), (-75.0, LEG_BOTTOM), (-75.0, 18.1)]


TIE_SLOT = (3.4, 1.8)             # cable-tie slot (along x, along y)
TIE_SLOTS = [(-61.0, -13.6), (-61.0, -31.5), (-38.0, -13.6), (-38.0, -31.5)]
# P4 header (1x6, pins from x -29.5 every 2.54 at y -10) takes a dupont plug that only has wires on some pins. The bridge
# covers the whole top of the plug (P4_GAP above it, so it holds the plug down) and opens a slot only over the wired
# pins, running out of the +y end of the bridge so the wires pass and the bridge lowers over them. Pins are counted
# from 1 at x -29.5, the one nearest the case's right wall. Plug footprint is (x0, x1, y0, y1).
P4_PLUG = (-43.47, -28.23, -11.27, -8.73)
P4_PIN1_X, P4_PITCH, P4_WIRES = -29.5, 2.54, (1, 5)
P4_GAP = 0.2            # gap between the plug top and the cover; the 2x10 lips use CAP_CLEAR
P4_SLOT_HALF = 1.0      # half width of the slot over a wired pin
P4_LIP, P4_LIP_OUT = 0.4, 0.8   # slot starts P4_LIP inside the plug's -y edge; the cover reaches P4_LIP_OUT past its ends
# Tall parts under the bridge, as (x, y, diameter, height above the PCB); the bridge
# keeps CAP_MARGIN of air around them. The bulk capacitor sits under the USB-side leg.
BULK_CAP = (-70.4, -11.0, 8.0, 12.0)
SMALL_CAP = (-57.5, -5.6, 5.0, 11.0)
CAP_MARGIN = 1.0
# Brand mark (resources/icons/brand-mark.svg) engraved in the plate top, between the right tie slots.
LOGO_C, LOGO_H, LOGO_DEPTH = (-38.0, -22.0), 14.0, 0.6
# Optional clip that ties the two halves of the open bridge together after installation: the cap
# rails run on as horns past the plate end, and a press-on clip grips their notched outer faces.
HORN_L, HORN_BOTTOM, HORN_TOP = 2.4, 20.0, 23.0     # horns: length past the bridge end, bottom and top (centred on NOTCH_Z)
NOTCH_Z, NOTCH_DEPTH = (21.0, 22.0), 0.4
# The clip is a short bar with a through hole for each horn: it slides onto the horns from the open end and its holes
# hold them apart and together. A ridge in each hole rides in the horn notch. It is symmetric left-right, top-bottom
# and front-back (the notch runs the whole horn), so it fits any way round. CLIP_CLEAR is the fit (0.19 mm printed well);
# CLIP_WALL is the wall at the sides of the holes and CLIP_T above and below them. The bottom stays thin because the
# small capacitor is just below, and the sides because of the relay, whose corner is 0.8 mm from the clip.
CLIP_CLEAR, CLIP_WALL, CLIP_T = 0.19, 1.4, 1.35


def rrect(x0, y0, x1, y1, r=0.0):
    sq = CrossSection.square((x1 - x0, y1 - y0)).translate((x0, y0))
    return sq.offset(-r, JoinType.Square).offset(r, JoinType.Round, circular_segments=SEG) if r else sq


def slab(cs, z0, z1):
    return Manifold.extrude(cs, z1 - z0).translate((0, 0, z0))


def box(x0, y0, z0, x1, y1, z1):
    (x0, x1), (y0, y1), (z0, z1) = sorted((x0, x1)), sorted((y0, y1)), sorted((z0, z1))
    return Manifold.cube((x1 - x0, y1 - y0, z1 - z0)).translate((x0, y0, z0))


def yz_prism(cs, x0, x1):
    """Extrude a (y, z) cross-section along x."""
    return Manifold.extrude(cs, x1 - x0).transform([[0, 0, 1, x0], [1, 0, 0, 0], [0, 1, 0, 0]])


def xz_prism(cs, y0, y1):
    """Extrude an (x, z) cross-section along y."""
    return Manifold.extrude(cs, y1 - y0).transform([[1, 0, 0, 0], [0, 0, -1, y1], [0, 1, 0, 0]])


def union(parts):
    return Manifold.batch_boolean(parts, m3d.OpType.Add)


def snap_profile(side, grow):
    """Bump (grow=0) or groove (grow=SNAP_CLEAR) as an (x, z) polygon on the left or right leg face."""
    face, sign = (LEG_X[0], -1) if side == "L" else (2 * BRIDGE_AXIS - LEG_X[0], 1)
    pts = [(face + sign * (d + (grow if d else -grow)), z) for d, z in SNAP_BUMP]
    cs = CrossSection([np.array(pts)], m3d.FillRule.EvenOdd)
    return cs.offset(grow, JoinType.Miter) if grow else cs


def body(height=HEIGHT, fillet=0.0):
    """Shell with chamfered bottom; the top edge is chamfered, or with fillet > 0 rounded inside and out."""
    outer = rrect(X0, Y0, X1, Y1, R_OUT)
    inner = rrect(X0 + WALL, Y0 + WALL, X1 - WALL, Y1 - WALL, R_IN)
    c, t = CHAMFER_BOTTOM, CHAMFER_TOP
    inset = lambda d: outer.offset(-d, JoinType.Round, circular_segments=SEG)
    # Chamfers and fillets as hulls of inset/outset slices keep the rounded corners intact.
    bottom = Manifold.batch_hull([slab(inset(c), 0, 0.01), slab(outer, c, c + 0.01)])
    if not fillet:
        solid = union([bottom, slab(outer, c, height - t),
                       Manifold.batch_hull([slab(outer, height - t - 0.01, height - t), slab(inset(t), height - 0.01, height)])])
        return solid - slab(inner, FLOOR, height + 1)
    n, z0 = 8, height - fillet
    steps = [(z0 + fillet * np.sin(a), fillet * (1 - np.cos(a))) for a in np.linspace(0, np.pi / 2, n + 1)]
    layer = lambda cs, z, top: slab(cs, z - 0.01, z) if top else slab(cs, z, z + 0.01)
    solid = union([bottom, slab(outer, c, z0)] +
                  [Manifold.batch_hull([layer(inset(da), za, False), layer(inset(db), zb, True)])
                   for (za, da), (zb, db) in zip(steps, steps[1:])])
    grow = lambda d: inner.offset(d, JoinType.Round, circular_segments=SEG)
    hole = union([slab(inner, FLOOR, z0 + 0.01)] +
                 [Manifold.batch_hull([layer(grow(da), za, False), layer(grow(db), zb, True)])
                  for (za, da), (zb, db) in zip(steps, steps[1:])] + [slab(grow(fillet), height - 0.01, height + 1)])
    return solid - hole


def round_corner(y, z, r, side, x0, x1):
    """Cut that rounds a wall's top corner at (y, z) in the yz plane; side = +1 if the wall lies on the +y side."""
    sq = rrect(min(y, y + side * r), z - r, max(y, y + side * r), z + 0.01)
    return yz_prism(sq - CrossSection.circle(r, SEG).translate((y + side * r, z - r)), x0, x1)


def screw_hole(x, y, top):
    d = INSERT_HOLE if SCREW_MODE == "insert" else SELFTAP_HOLE
    depth = top if SCREW_MODE == "selftap" else 3.2   # self-tap: through boss and floor; insert: blind pocket
    hole = Manifold.cylinder(depth + 0.02, d / 2, circular_segments=SEG).translate((x, y, top - depth - 0.01))
    lead = Manifold.cylinder(0.5, d / 2, d / 2 + 0.5, circular_segments=SEG).translate((x, y, top - 0.49))
    return hole + lead


# Minimal case: keeps only what protects and insulates. The full floor (insulation and heat shield from the machine),
# the board and module rests, and a low rim RIM_ABOVE_PCB over the PCB top that guards the board edges and the
# solder side from sideways contact. The walls stay full height only where the bridge snaps in and rests on them.
RIM_ABOVE_PCB = 2.0
TOWER_MARGIN = 2.0     # extra wall length past each end of the bridge
RIM_FILLET, NOTCH_FILLET, TOWER_FILLET = 1.0, 1.0, 2.0   # rounded top edges, notch corners and tower ends


def case(minimal=False, towers=True):
    """minimal=True keeps the floor, the rests and a low rim; towers=False also drops the bridge walls (no bridge)."""
    cavity = slab(rrect(X0 + WALL - 0.5, Y0 + WALL - 0.5, X1 - WALL + 0.5, Y1 - WALL + 0.5), FLOOR - 0.01, HEIGHT)
    supports = [Manifold.cylinder(SUPPORT_TOP - FLOOR + 0.01, BOSS_D / 2, circular_segments=SEG).translate((x, y, FLOOR - 0.01))
                for x, y in PCB_HOLES + [SPK_HOLE]]
    supports += [slab(rrect(*SPK_PAD, 1.0), FLOOR - 0.01, SUPPORT_TOP), slab(rrect(*SPK_REST, 0.5), FLOOR - 0.01, SUPPORT_TOP)]
    if SPK_STOP_FACE_X is not None:
        supports.append(box(SPK_STOP_FACE_X, SPK_STOP_Y[0], FLOOR - 0.01, SPK_STOP_FACE_X + SPK_STOP_T, SPK_STOP_Y[1], SPK_STOP_TOP))
    rim = SUPPORT_TOP + PCB_T + RIM_ABOVE_PCB
    ty0, ty1 = BRIDGE_START_Y - TOWER_MARGIN, HOUSING_C[1] + HOUSING_L / 2 + CAP_CLEAR + CAP_WALL + TOWER_MARGIN
    keep = [box(X0 - 1, ty0, rim - 1, X0 + WALL, ty1, HEIGHT + 1), box(X1 - WALL, ty0, rim - 1, X1 + 1, ty1, HEIGHT + 1)]
    if minimal:  # a low rounded rim, plus the full-height walls the bridge needs
        shell = body(rim, RIM_FILLET) + (body() ^ union(keep) if towers else body(rim, RIM_FILLET))
    else:
        shell = body()
    part = shell + (union(supports) ^ cavity)

    cuts = [screw_hole(x, y, SUPPORT_TOP) for x, y in PCB_HOLES + [SPK_HOLE]]
    cuts += [yz_prism(rrect(y0, z0, y1, z1, r), xa, xb) for y0, y1, z0, z1, r, xa, xb in OPENINGS]
    slot = CrossSection.batch_boolean([rrect(*r) for r in [(a, z0, b, z1) for a, b, z0, z1 in SLOT]], m3d.OpType.Add)
    cuts.append(xz_prism(slot, Y1 - WALL - 1, Y1 + 1))
    cuts += [xz_prism(snap_profile(s, SNAP_CLEAR), *SNAP_Y) for s in "LR"]
    if minimal:
        # Round the top corners where a connector opening notches the rim, except inside the towers.
        for y0, y1, z0, z1, r, xa, xb in OPENINGS:
            if z0 < rim < z1 and not (towers and y1 > ty0 and y0 < ty1):
                cuts += [round_corner(y0, rim, NOTCH_FILLET, -1, xa, xb), round_corner(y1, rim, NOTCH_FILLET, 1, xa, xb)]
        if towers:  # and the top corners at both ends of each tower
            for xa, xb in ((X0 - 1, X0 + WALL + 0.01), (X1 - WALL - 0.01, X1 + 1)):
                cuts += [round_corner(ty0, HEIGHT, TOWER_FILLET, 1, xa, xb), round_corner(ty1, HEIGHT, TOWER_FILLET, -1, xa, xb)]
    return part - union(cuts)


def bridge(closed=False, variant=DEFAULT_VARIANT):
    """closed=True closes the cap and the wire slit at both ends: thread the wires before seating the pins."""
    duct = VARIANTS[variant].get("duct", False)
    closed = closed or duct   # the slit stays short; the duct is open at both ends
    PLATE_Z = plate_z(variant)
    HORN_Z = horn_z(variant)
    left = CrossSection([np.array(bridge_profile(variant))], m3d.FillRule.EvenOdd)
    right = left.mirror((1, 0)).translate((2 * BRIDGE_AXIS, 0))
    plate = rrect(-65.1, PLATE_Z[0], 2 * BRIDGE_AXIS + 65.1, PLATE_Z[1])
    hx, hy = HOUSING_C
    top = HOUSING_TOP
    ix, iy = HOUSING_W / 2 + CAP_CLEAR, HOUSING_L / 2 + CAP_CLEAR
    ox, oy = ix + CAP_WALL, iy + CAP_WALL
    frame = xz_prism(CrossSection.batch_boolean([left, right, plate], m3d.OpType.Add), BRIDGE_START_Y, hy + oy)
    frame += union([xz_prism(snap_profile(s, 0), *SNAP_BUMP_Y) for s in "LR"])
    lip_top = top + CAP_CLEAR + LIP_T
    if VARIANTS[variant].get("flush"):  # the plate runs at housing height: clear the housing, the lips hold it
        frame -= box(hx - ix, hy - iy, 0, hx + ix, hy + oy + 1, top + CAP_CLEAR)
    # The duct is wider than the cap: the lips become a shelf out to the duct walls, which rise from it to the roof.
    dw = DUCT_W / 2 + CAP_WALL if duct else ox
    rail_top = lip_top if duct else PLATE_Z[0] + 0.01
    rails = [box(hx + s * ix, BRIDGE_START_Y, CAP_BOTTOM, hx + s * ox, hy + oy, rail_top) for s in (-1, 1)]
    lips = [box(hx + s * (HOUSING_W / 2 - CAP_LIP), hy - iy, top + CAP_CLEAR, hx + s * dw, hy + iy, lip_top) for s in (-1, 1)]
    posts = [box(hx - dw, hy - iy, CAP_BOTTOM, hx + dw, BRIDGE_START_Y, rail_top)]
    if duct:
        posts += [box(hx + s * DUCT_W / 2, BRIDGE_START_Y, lip_top - 0.01, hx + s * dw, hy + oy, PLATE_Z[0] + 0.01) for s in (-1, 1)]
    elif closed:
        posts.append(box(hx - ox, hy + iy, CAP_BOTTOM, hx + ox, hy + oy, PLATE_Z[0] + 0.01))
    else:
        end = hy + oy
        posts += [box(hx + s * ix, end - 0.01, HORN_Z[0], hx + s * ox, end + HORN_L, HORN_Z[1]) -
                  box(hx + s * (ox - NOTCH_DEPTH), end, NOTCH_Z[0], hx + s * (ox + 1), end + HORN_L + 1, NOTCH_Z[1])
                  for s in (-1, 1)]
    ties = [box(x - TIE_SLOT[0] / 2, y - TIE_SLOT[1] / 2, PLATE_Z[0] - 1, x + TIE_SLOT[0] / 2, y + TIE_SLOT[1] / 2, PLATE_Z[1] + 1)
            for x, y in TIE_SLOTS] if not duct else []   # the wires are inside, nothing to tie down
    rails_lips = [r + l for r, l in zip(rails, lips)]
    # Clearance pockets stop at the wall face so the ledge keeps its full bearing on the wall top.
    pcb_top = SUPPORT_TOP + PCB_T
    pockets = [Manifold.cylinder(h + CAP_MARGIN, d / 2 + CAP_MARGIN, circular_segments=SEG).translate((x, y, pcb_top))
               for x, y, d, h in (BULK_CAP, SMALL_CAP)]
    inside = box(X0 + WALL, Y0, 0, X1 - WALL, Y1, PLATE_Z[1])
    # Wires rise straight out of the housing through a slit between the lips. Its ends are round
    # (no crack-starting corners) and reach 0.6 mm past the cavity so the end wires stay clear.
    # Open version: the slit runs out of the +y end; slide the bridge onto the plugged-in wires.
    sw = HOUSING_W / 2 - CAP_LIP
    ends = (hy - iy + sw - 0.6, hy + iy - sw + 0.6 if closed else hy + oy + sw + 1)
    slit_top = lip_top + 0.3 if duct else PLATE_Z[1] + 1   # the duct keeps its roof closed
    slit = Manifold.batch_hull([Manifold.cylinder(slit_top - top - CAP_CLEAR, sw, circular_segments=SEG)
                                .translate((hx, y, top + CAP_CLEAR)) for y in ends])
    # The tunnel roof is solid, so the logo goes in the middle of the bridge; elsewhere the slit is in the way.
    logo_c = (BRIDGE_AXIS, (BRIDGE_START_Y + hy + oy) / 2) if duct else LOGO_C
    px0, px1, py0, py1 = P4_PLUG
    # P4 cover: a block over the plug from just above it up to the plate, with a slot over each wired pin. A flush
    # plate is lower than the plug, so the room under it is cut out first.
    p4_lips = box(px0 - P4_LIP_OUT, py0 - P4_LIP_OUT, top + P4_GAP, px1 + P4_LIP_OUT, py1, PLATE_Z[0] + 0.01)
    p4_open = [box(P4_PIN1_X - (n - 1) * P4_PITCH - P4_SLOT_HALF, py0 + P4_LIP, 0, P4_PIN1_X - (n - 1) * P4_PITCH + P4_SLOT_HALF,
                   hy + oy + 1, PLATE_Z[1] + 1) for n in P4_WIRES]
    p4_room = box(px0 - CAP_CLEAR, py0 - CAP_CLEAR, 0, px1 + CAP_CLEAR, hy + oy + 1, top + P4_GAP)
    cuts = ties + p4_open + [p4_room, slit, slab(brand_mark(logo_c), PLATE_Z[1] - LOGO_DEPTH, PLATE_Z[1] + 1)]
    # The bulk capacitor sits 0.4-0.7 mm from the case wall, right where the left leg goes. The leg and its snap
    # bump are cut away from the capacitor to the end of the bridge, so the leg just stops: a pocket round the
    # capacitor alone would leave a sliver of leg hanging past it, in the air when printed. The ledge on the
    # wall top (x < -75, z >= 18.1) stays whole.
    cap_x, cap_y, cap_d, cap_h = BULK_CAP
    notch_y0, notch_top = cap_y - cap_d / 2 - CAP_MARGIN, pcb_top + cap_h + CAP_MARGIN
    notch = [box(LEG_X[0], notch_y0, 14.0, notch_top - 93.1, 0.0, notch_top),   # leg and the strut corner over the capacitor
             box(LEG_X[0] - 1.5, notch_y0, 14.0, LEG_X[0] + 0.5, 0.0, 17.5)]      # snap bump, below the ledge; overlaps the leg cut
    return union([frame, p4_lips] + posts + rails_lips) - union(cuts + notch) - (union(pockets) ^ inside)


def clip(variant=DEFAULT_VARIANT, clear=CLIP_CLEAR):
    """Bar with a through hole for each horn, built in place; prints lying flat. Symmetric about the notch."""
    HORN_Z = horn_z(variant)
    hx, hy = HOUSING_C
    ix, ox = HOUSING_W / 2 + CAP_CLEAR, HOUSING_W / 2 + CAP_CLEAR + CAP_WALL
    c = clear
    end = hy + HOUSING_L / 2 + CAP_CLEAR + CAP_WALL   # open end of the bridge
    y0, y1 = end + 0.05, end + HORN_L               # from the bridge end to the horn tips
    block = xz_prism(rrect(hx - ox - c - CLIP_WALL, HORN_Z[0] - c - CLIP_T, hx + ox + c + CLIP_WALL, HORN_Z[1] + c + CLIP_T, 0.4), y0, y1)
    holes = []
    for s in (-1, 1):
        hole = rrect(min(s * (ix - c), s * (ox + c)), HORN_Z[0] - c, max(s * (ix - c), s * (ox + c)), HORN_Z[1] + c)
        ridge = box2(s * (ox - NOTCH_DEPTH + c), NOTCH_Z[0] + min(c, 0.2), s * (ox + c + 0.01), NOTCH_Z[1] - min(c, 0.2))   # rides in the notch
        holes.append(xz_prism((hole - ridge).translate((hx, 0)), y0 - 0.01, y1 + 0.01))
    return block - union(holes)


def box2(xa, za, xb, zb):
    return rrect(min(xa, xb), min(za, zb), max(xa, xb), max(za, zb))


def brand_mark(centre=LOGO_C):
    """The brand-mark drop minus its mask cuts, from the 64-unit SVG, scaled to LOGO_H and y flipped."""
    def cubic(p0, p1, p2, p3, n=32):
        t = np.linspace(0, 1, n)[:, None]
        return (1 - t) ** 3 * p0 + 3 * (1 - t) ** 2 * t * p1 + 3 * (1 - t) * t ** 2 * p2 + t ** 3 * p3
    P = lambda x, y: np.array((x, y), float)
    arc = np.array([(32 + 20 * np.cos(a), 39 + 20 * np.sin(a)) for a in np.linspace(0, np.pi, 48)])
    drop = np.vstack([cubic(P(32, 5), P(32, 5), P(52, 21), P(52, 39)), arc, cubic(P(12, 39), P(12, 21), P(32, 5), P(32, 5))])
    circle = lambda x, y, r: CrossSection.circle(r, SEG).translate((x, y))
    cuts = [rrect(28.435, -1, 35.565, 27.55), rrect(28.435, 48.45, 35.565, 65),
            CrossSection.batch_hull([circle(32, 48.45, 3.8), circle(21.62, 36.08, 3.8)]),
            circle(32, 27.55, 6.27), circle(31.34, 48.45, 6.27)]
    mark = CrossSection([drop], m3d.FillRule.EvenOdd) - CrossSection.batch_boolean(cuts, m3d.OpType.Add)
    k = LOGO_H / 54.0
    return mark.translate((-32, -32)).mirror((0, 1)).scale((k, k)).translate(centre)


def to_trimesh(m):
    mesh = m.to_mesh()
    return trimesh.Trimesh(np.asarray(mesh.vert_properties)[:, :3], np.asarray(mesh.tri_verts), process=False)


if __name__ == "__main__":
    out = Path(__file__).resolve().parent.parent / "print"
    out.mkdir(exist_ok=True)
    parts = {"case": to_trimesh(case()), "case-minimal": to_trimesh(case(minimal=True, towers=False)),
             "case-minimal-bridge": to_trimesh(case(minimal=True))}
    for v, cfg in VARIANTS.items():
        if cfg.get("duct"):  # the roof joins the two halves: no clip, no closed version
            parts[f"bridge-{v}"] = to_trimesh(bridge(variant=v))
            continue
        parts[f"bridge-{v}"] = to_trimesh(bridge(variant=v))
        if cfg.get("flush"):  # minimal: open version only
            continue
        if v != "original":  # the closed original adds nothing over the closed low profile
            parts[f"bridge-{v}-closed"] = to_trimesh(bridge(closed=True, variant=v))
    parts["clip"] = to_trimesh(clip())   # the same clip for every bridge
    sets = {  # one folder per complete kit: the case plus the bridge pieces that go with it
        "1-original": ["case", "bridge-original", "clip"],
        "2-lowprofile": ["case", "bridge-lowprofile", "bridge-lowprofile-closed", "clip"],
        "3-lowprofile-tunnel": ["case", "bridge-lowprofile-tunnel"],
        "4-minimal-case-and-bridge": ["case-minimal-bridge", "bridge-minimal", "clip"],
        "5-minimal-case-only": ["case-minimal"],
    }
    assert {n for names in sets.values() for n in names} == set(parts)
    for name, tm in parts.items():
        if not name.startswith("case"):  # bridges stand on the closed cap end, the clip lies on its profile
            tm.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, (1, 0, 0)))
        tm.apply_translation(-tm.bounds[0])
        print(name, "watertight", tm.is_watertight, "size", np.round(tm.extents, 2), "volume", round(tm.volume, 1))
    for folder, names in sets.items():
        (out / folder).mkdir(exist_ok=True)
        for name in names:
            for ext in ("stl", "3mf", "obj"):
                parts[name].export(f"{out}/{folder}/openbrewbyweight-{name}.{ext}")
