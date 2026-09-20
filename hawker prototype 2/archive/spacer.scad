// Stock Clock — the only part you need to print.
//
// It is a block with two holes. You need 8 of them: two per slot.
// Both the fixed-end and the load-end spacer are this same part, so there is
// nothing to keep track of.
//
// HOW TO USE THIS FILE — no CAD experience needed:
//   1. Install OpenSCAD (free, openscad.org).
//   2. Open this file.
//   3. Measure your load cell when it arrives. Change the four numbers below.
//      Nothing else in the file needs touching.
//   4. Press F5 to look at it. Press F6 to build it properly.
//   5. File > Export > Export as STL. Slice and print 8.
//
// PRINT SETTINGS: no supports, 4 perimeters, 40% infill. These carry the whole
// weight of a basin of vegetables, so do not print them at 10% infill.

// ── MEASURE YOUR LOAD CELL, THEN CHANGE THESE FOUR NUMBERS ───────────────
CELL_W     = 12.7;  // width of the metal bar (callipers, or the spec sheet)
HOLE_GAP   = 8;     // centre-to-centre between the TWO holes at ONE end
BOLT_D     = 4;     // the bolt you are using: 4 for M4, 5 for M5
GAP_HEIGHT = 10;    // air under the free end so it can bend. 10 is safe.
// ─────────────────────────────────────────────────────────────────────────

// Everything below is worked out from the four numbers above.

BLOCK = CELL_W + 8;        // a bit wider than the cell so it seats flat
HOLE  = BOLT_D + 0.5;      // printed holes come out undersize; this is the slop

module spacer() {
    difference() {
        translate([-BLOCK / 2, -BLOCK / 2, 0])
            cube([BLOCK, BLOCK, GAP_HEIGHT]);

        // two bolt holes, straight through
        for (y = [-HOLE_GAP / 2, HOLE_GAP / 2])
            translate([0, y, -1])
                cylinder(d = HOLE, h = GAP_HEIGHT + 2, $fn = 30);
    }
}

// Laid out as a printable plate of 8. Delete the loop and leave a bare
// spacer() if your slicer would rather arrange them itself.
for (i = [0:3], j = [0:1])
    translate([i * (BLOCK + 5), j * (BLOCK + 5), 0]) spacer();

// ponytail: a plain block, not a bracket that hugs the cell. A hugging bracket
// has to match one exact load cell; this one works with whatever arrives, and
// the bolts do the locating. Print a single one first and check it before
// committing to all 8.
