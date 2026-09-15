// SG Eco Loop 2.0 — the two prototypes
// Raghav, solo team. Units: mm. Both run a Raspberry Pi 4 Model B.
//
//   SHOW = 1   CHOPE        — live meal headcount + kitchen board   (SBAB)
//   SHOW = 2   STOCK CLOCK  — 4-slot ingredient rack                (SUTD cai png stall)
//   SHOW = 0   both
//
//   EXPLODE = 1   pull the parts apart
//
// F5 preview · File > Export > Export as Image
// Slide renders live in models/renders/
// ponytail: no fasteners, threads or draft angles — a showcase visual
// and build reference, not a manufacturing drawing.

SHOW    = 0;
EXPLODE = 0;

$fn = 40;
E = EXPLODE;

C_SHELL   = [0.93, 0.93, 0.91];   // wipe-clean white shell
C_DARK    = [0.16, 0.18, 0.19];
C_SCREEN  = [0.10, 0.13, 0.14];
C_METAL   = [0.72, 0.73, 0.75];
C_KEY     = [0.30, 0.32, 0.33];
C_INK     = [0.93, 0.95, 0.93];   // text on a dark screen
C_MUTED   = [0.56, 0.60, 0.58];
C_OK      = [0.22, 0.74, 0.38];   // green — fresh / eating
C_WARN    = [0.96, 0.62, 0.12];   // amber — day 2 / unconfirmed
C_BAD     = [0.86, 0.20, 0.16];   // red — day 3+
C_TG      = [0.16, 0.53, 0.80];   // Telegram blue
C_CHAT    = [0.80, 0.86, 0.80];
C_PAPER   = [0.98, 0.98, 0.96];
C_PLY     = [0.80, 0.67, 0.49];
C_ACRYLIC = [0.78, 0.88, 0.93, 0.5];
C_PLASTIC = [0.90, 0.93, 0.95];
C_HX      = [0.10, 0.35, 0.55];
C_WIRE    = [0.40, 0.42, 0.43];
C_GOLD    = [0.85, 0.72, 0.28];
WIRES     = [[0.85, 0.20, 0.15], [0.95, 0.60, 0.10], [0.20, 0.60, 0.30], [0.20, 0.40, 0.80]];

FONT   = "Liberation Sans";
FONT_B = "Liberation Sans:style=Bold";
MONO   = "Liberation Mono";
MONO_B = "Liberation Mono:style=Bold";

module rbox(w, d, h, r = 4) {
    hull() for (x = [r, w - r], y = [r, d - r])
        translate([x, y, 0]) cylinder(r = r, h = h);
}

// text lying flat, read from above
module flat_text(s, size, halign = "left", font = FONT_B, valign = "baseline")
    linear_extrude(0.8) text(s, size = size, font = font, halign = halign, valign = valign);

// text standing on a face that looks toward -y, read from the front
module face_text(s, size, halign = "left", font = FONT_B)
    rotate([90, 0, 0]) flat_text(s, size, halign, font);

module cable(pts, d = 4, c = C_WIRE)
    color(c) for (i = [0 : len(pts) - 2])
        hull() {
            translate(pts[i])     sphere(d = d, $fn = 12);
            translate(pts[i + 1]) sphere(d = d, $fn = 12);
        }

// ══════════════════════════════════════════════════════════════
//  RASPBERRY PI 4 MODEL B
//  85 x 56 board. Mounting holes 58 x 49 apart, 3.5 in from the
//  edges. The port block overhangs two edges by ~3mm.
// ══════════════════════════════════════════════════════════════

module pi4(heatsink = true) {
    // board
    color([0.04, 0.34, 0.20]) difference() {
        cube([85, 56, 1.4]);
        for (x = [3.5, 61.5], y = [3.5, 52.5])
            translate([x, y, -1]) cylinder(d = 2.7, h = 4);
    }
    // 40-pin GPIO header, long edge
    color(C_DARK) translate([7.1, 49.5, 1.4]) cube([50.8, 5, 8.5]);
    color(C_GOLD)
        for (i = [0:19], j = [0:1])
            translate([8.4 + i * 2.54, 50.8 + j * 2.54, 1.4]) cylinder(d = 0.8, h = 11.5);

    // port block — short edge, overhangs by 3
    color(C_METAL) translate([66.7, 2,  1.4]) cube([21.3, 16,   13.5]);  // Ethernet
    color([0.15, 0.30, 0.62]) translate([70.7, 21, 1.4]) cube([17.3, 13.1, 15.6]);  // USB 3.0
    color(C_METAL)            translate([70.7, 38, 1.4]) cube([17.3, 13.1, 15.6]);  // USB 2.0

    // power / video edge
    color(C_METAL) translate([ 7.7, -1.5, 1.4]) cube([9,   7.5, 3.2]);   // USB-C
    color(C_METAL) translate([21.5, -1.5, 1.4]) cube([7.5, 8,   3.5]);   // micro-HDMI 0
    color(C_METAL) translate([35.0, -1.5, 1.4]) cube([7.5, 8,   3.5]);   // micro-HDMI 1
    color(C_DARK)  translate([52.8,  2.5, 4.4]) rotate([90,0,0]) cylinder(d = 6.5, h = 6);

    // silicon
    if (heatsink)
        color([0.55, 0.56, 0.58]) translate([26, 19, 1.4])
            for (i = [0:6]) translate([i * 2.1, 0, 0]) cube([1.2, 14, 9]);
    else
        color(C_DARK) translate([26, 19, 1.4]) cube([15, 15, 2.5]);
    color(C_DARK) translate([46, 20, 1.4]) cube([10, 12, 1.1]);          // RAM
    color(C_DARK) translate([60, 33, 1.4]) cube([10, 10, 1.1]);          // USB controller
    color(C_METAL) translate([18, 20, -2])  cube([12, 15, 2]);           // microSD, underside
}

module pi4_standoffs(h = 6) {
    color(C_DARK) for (x = [3.5, 61.5], y = [3.5, 52.5])
        translate([x, y, -h]) cylinder(d = 6, h = h);
}

module ds3231() {
    color([0.55, 0.12, 0.12]) cube([38, 22, 1.6]);
    color(C_METAL) translate([12, 6, 1.6]) cylinder(d = 20, h = 3.2);   // CR2032
}

// ══════════════════════════════════════════════════════════════
//  1 · CHOPE — the kitchen board
//
//  NSFs tap Eating / Not eating on a card the bot pins in the
//  unit's existing Telegram group. The Pi 4 runs that bot and this
//  board. At cutoff the board locks the number to cook:
//
//      COOK = C + r x U      41 confirmed + 0.63 x 27 unconfirmed = 58
//
//  After service the kitchen keys in portions left, which scores the
//  forecast and updates r (P90 of past meals in the same slot).
//
//  Why it looks like this:
//   · the Pi 4 sits in the open beside the screen — it runs warm,
//     and judges can see what drives the board.
//   · a USB keypad, not a touchscreen or an app: caterer staff key
//     one number and never have to join the unit's chat.
//   · the phone shows where the numbers come from. Board and card
//     only ever show counts, never names.
// ══════════════════════════════════════════════════════════════

TILT = 15;   // screen leans back

module screen_panel() {
    // frame: x across, y = thickness (front face at y 0), z up
    color(C_DARK)   cube([245, 12, 155]);
    color(C_SCREEN) translate([8, -0.4, 10]) cube([229, 0.5, 135]);
    translate([0, -0.4, 0]) {
        color(C_INK)   translate([18, 0, 126]) face_text("LUNCH · TUE", 8);
        color(C_WARN)  translate([227, 0, 126]) face_text("closes 08:30", 7, "right", FONT);
        color(C_MUTED) translate([18, -0.8, 119]) cube([209, 0.8, 0.8]);
        color(C_MUTED) translate([18, 0, 104]) face_text("COOK", 9);
        color(C_INK)   translate([16, 0, 56])  face_text("58", 42);
        color(C_OK)    translate([118, 0, 94]) face_text("41 confirmed", 7);
        color(C_WARN)  translate([118, 0, 81]) face_text("+17 of 27 unconfirmed", 7);
        color(C_MUTED) translate([118, 0, 68]) face_text("rate 0.63 · P90, last 8 Tue", 5.2, font = FONT);
        // turnout bar, 80 people: 41 eating · 12 not · 27 no answer
        translate([18, -0.8, 30]) {
            color(C_OK)                            cube([107, 0.8, 9]);
            color(C_MUTED) translate([107, 0, 0]) cube([32, 0.8, 9]);
            color(C_WARN)  translate([139, 0, 0]) cube([70, 0.8, 9]);
        }
        color(C_INK) translate([18, 0, 17])  face_text("EATING 41", 5);
        color(C_INK) translate([125, 0, 17]) face_text("NOT 12", 5);
        color(C_INK) translate([227, 0, 17]) face_text("NO ANSWER 27", 5, "right");
    }
}

module chope_board() {
    color(C_SHELL) rbox(360, 150, 12, 6);
    color(C_DARK)  translate([16, -0.01, 3]) face_text("CHOPE", 7);
    translate([10, 40, 12]) rotate([-TILT, 0, 0]) screen_panel();
    color(C_SHELL) for (bx = [40, 205])
        hull() {
            translate([bx, 62, 12]) cube([10, 80, 3]);
            translate([10, 40, 12]) rotate([-TILT, 0, 0]) translate([bx - 10, 12, 40]) cube([10, 3, 70]);
        }
}

// ports face the back, power and video face the right edge
module chope_pi() {
    translate([336, 40, 20 + E * 70]) rotate([0, 0, 90]) { pi4(); pi4_standoffs(8); }
}

module chope_cables() {
    cable([[338, 65, 23], [354, 65, 18], [354, 146, 15], [170, 146, 15], [170, 66, 55]], 5, C_DARK);  // micro-HDMI → screen
    cable([[338, 52, 22], [362, 52, 10], [362, 20, 2], [430, 20, 2]], 4, C_DARK);                     // USB-C power
    cable([[300, 130, 27], [300, 162, 10], [372, 162, 2], [372, -52, 2], [115, -44, 2], [115, -28, 10]], 3.5, C_DARK); // keypad
}

module keypad() {
    keys = [   // col, row, w, h, label — row 0 nearest the user
        [0,4,1,1,"NUM"], [1,4,1,1,"/"], [2,4,1,1,"*"], [3,4,1,1,"-"],
        [0,3,1,1,"7"],   [1,3,1,1,"8"], [2,3,1,1,"9"], [3,2,1,2,"+"],
        [0,2,1,1,"4"],   [1,2,1,1,"5"], [2,2,1,1,"6"],
        [0,1,1,1,"1"],   [1,1,1,1,"2"], [2,1,1,1,"3"], [3,0,1,2,"OK"],
        [0,0,2,1,"0"],   [2,0,1,1,"."]
    ];
    color(C_DARK) rbox(90, 150, 14, 6);
    for (k = keys) {
        w = k[2] * 20 - 3;
        d = k[3] * 20 - 3;
        translate([6 + k[0] * 20, 8 + k[1] * 20, 14]) {
            color(C_KEY) rbox(w, d, 5, 2);
            color(C_INK) translate([w / 2, d / 2, 5])
                flat_text(k[4], len(k[4]) > 1 ? 4 : 7, "center", valign = "center");
        }
    }
    color(C_INK) translate([45, 128, 14]) flat_text("PORTIONS LEFT", 5.5, "center");
}

module phone() {
    // frame: x across, y = thickness (screen at y 0), z up
    color(C_DARK) cube([78, 9, 162]);
    translate([3, -0.01, 6]) {
        color(C_CHAT)  cube([72, 0.4, 150]);
        color(C_TG)    translate([0, -0.3, 136]) cube([72, 0.3, 14]);
        color(C_PAPER) translate([0, -0.3, 125]) cube([72, 0.3, 10]);
        color(C_PAPER) translate([5, -0.3, 50])  cube([62, 0.3, 70]);
        translate([0, -0.3, 0]) {
            color(C_INK)   translate([6, 0, 140.5]) face_text("4 SQN · MAKAN", 5);
            color(C_MUTED) translate([6, 0, 128.5]) face_text("PINNED · Lunch Tue", 3.6, font = FONT);
            color(C_TG)    translate([9, 0, 112])   face_text("CHOPE bot", 3.8);
            color(C_DARK)  translate([9, 0, 101])   face_text("LUNCH · TUE", 6);
            for (r = [["Eating", "41", 91], ["Not eating", "12", 83], ["No answer", "27", 75]]) {
                color(C_DARK) translate([9, 0, r[2]])  face_text(r[0], 4.4, font = FONT);
                color(C_DARK) translate([63, 0, r[2]]) face_text(r[1], 4.4, "right");
            }
            color(C_MUTED) translate([9, 0, 64]) face_text("closes 08:30", 3.6, font = FONT);
            color(C_MUTED) translate([9, 0, 56]) face_text("counts only, no names", 3.2, font = FONT);
        }
        for (b = [["EATING", C_OK, 36], ["NOT EATING", C_MUTED, 23], ["SAME AS LAST WEEK", C_TG, 10]]) {
            color(b[1])  translate([5, -0.3, b[2]]) cube([62, 0.3, 11]);
            color(C_INK) translate([36, -0.3, b[2] + 3.5]) face_text(b[0], 4, "center");
        }
    }
}

module phone_on_stand() {
    color(C_SHELL) {
        translate([-6, -12, 0]) cube([90, 62, 5]);
        translate([-6, -12, 5]) cube([90, 6, 9]);
        hull() {
            translate([10, 38, 5]) cube([58, 10, 2]);
            translate([0, 0, 5]) rotate([-20, 0, 0]) translate([10, 9, 60]) cube([58, 3, 20]);
        }
    }
    translate([0, 0, 5]) rotate([-20, 0, 0]) phone();
}

module chope() {
    chope_board();
    chope_pi();
    if (E == 0) chope_cables();
    translate([70, -175 - E * 70, 0]) keypad();
    translate([230, -120, 0]) rotate([0, 0, -12]) phone_on_stand();
}

// ══════════════════════════════════════════════════════════════
//  2 · STOCK CLOCK — the ingredient rack
//
//  Four slots for the stall's most-binned perishables. Each slot
//  stands on its own load cell, so the Pi 4 sees stock go in (weight
//  jumps up) and come out (weight drops) without anyone typing.
//
//   · each slot's light is the age of its oldest stock:
//     green day 1 · amber day 2, cook today · red day 3+, cook now
//   · at close the printer gives one slip for the market:
//     have · usage · BUY · PREP     (buy = expected use - stock on hand)
//
//  Why it looks like this:
//   · single-point load cells, bolted at one end and loaded at the
//     other, so a basin anywhere on the plate reads the same.
//   · clear top plates — the cell under each basin stays visible.
//   · paper, not a screen: the slip goes to the market at dawn.
//   · DS3231 clock: the stall has no Wi-Fi, and stock age is the
//     whole product — a Pi 4 that wakes up in 1970 gets every light
//     wrong.
//   · open-top electronics box, kept clear of the wet basins.
// ══════════════════════════════════════════════════════════════

PITCH   = 190;
PLATE_Z = 40.7;   // underside of the top plates

SLOTS = [   // name, fill colour, fill height, light, age, texture
    ["KANGKONG", [0.22, 0.45, 0.18], 68, C_WARN, "DAY 2", "leaf"],
    ["TAUGE",    [0.93, 0.91, 0.78], 48, C_OK,   "DAY 1", "sprout"],
    ["TOFU",     [0.96, 0.92, 0.74], 30, C_OK,   "DAY 1", "tofu"],
    ["CABBAGE",  [0.68, 0.82, 0.52], 60, C_BAD,  "DAY 3", "leaf"]
];

// 5 kg single-point cell, 80 x 12.7 x 12.7, long axis along y
module load_cell_5kg() {
    color(C_METAL) difference() {
        cube([12.7, 80, 12.7]);
        hull() for (y = [32, 48]) translate([-1, y, 6.35]) rotate([0, 90, 0]) cylinder(d = 10, h = 15);
        for (y = [6, 14, 66, 74]) translate([6.35, y, -1]) cylinder(d = 4.2, h = 15);
    }
    color(C_PAPER) translate([2.35, 36, 12.7]) cube([8, 8, 0.3]);          // strain gauge
    color(C_DARK) translate([12.7, 40, 6.35]) rotate([0, 90, 0])            // load arrow, points down
        linear_extrude(0.4) polygon([[-5, -1.5], [2, -1.5], [2, -4], [6, 0], [2, 4], [2, 1.5], [-5, 1.5]]);
}

module basin(fill_c, fill_h, kind) {
    color(C_PLASTIC) difference() {
        rbox(170, 250, 90, 10);
        translate([3, 3, 3]) rbox(164, 244, 90, 8);
    }
    color(fill_c) translate([4, 4, 3]) rbox(162, 242, fill_h - 3, 7);
    if (kind == "tofu")
        color(fill_c) for (i = [0:3], j = [0:5])
            translate([12 + i * 38, 12 + j * 38, fill_h]) cube([30, 30, 24]);
    else
        color(fill_c * 0.85) for (i = [0:4], j = [0:8])
            translate([18 + i * 27 + (j % 2) * 12, 18 + j * 26, fill_h])
                scale([1, 1, 0.45]) sphere(r = kind == "sprout" ? 9 : 15, $fn = 16);
}

module slot(i) {
    s = SLOTS[i];
    ox = 10 + i * PITCH;
    cx = ox + 90;
    oy = 15;
    lift = E * 70;
    color(C_DARK) translate([cx - 10, oy + 165, 8]) cube([20, 20, 10]);           // fixed-end spacer
    translate([cx - 6.35, oy + 105, 18]) load_cell_5kg();
    color(C_DARK) translate([cx - 10, oy + 105, 30.7 + lift]) cube([20, 20, 10]); // load-end spacer
    color(C_ACRYLIC) translate([ox, oy, PLATE_Z + lift]) cube([180, 260, 5]);
    translate([ox + 5, oy + 5, PLATE_Z + 5 + lift + E * 100]) basin(s[1], s[2], s[5]);
    if (E == 0) cable([[cx, oy + 186, 24], [cx, 268, 22], [cx + 24, 284, 18]], 4);
    translate([cx, 0, 0]) {
        color(C_DARK) translate([0, -0.2, 42]) rotate([90, 0, 0]) cylinder(d = 26, h = 1);
        color(s[3])   translate([0, -1.2, 42]) rotate([90, 0, 0]) cylinder(d = 18, h = 2);
        color(C_DARK) translate([0, -0.01, 16]) face_text(s[0], 8, "center");
        color(s[3])   translate([18, -0.01, 39]) face_text(s[4], 6);
    }
}

module hx711() {
    color(C_HX)   cube([34, 21, 1.6]);
    color(C_DARK) translate([14, 5.5, 1.6]) cube([8, 10, 1.6]);
    color(C_GOLD) for (j = [0:4]) translate([2, 3 + j * 3.8, 1.6]) cube([0.8, 0.8, 7]);
    color([0.20, 0.50, 0.25]) translate([28, 2, 1.6]) cube([5, 17, 6]);   // load-cell terminal
}

module stock_box() {
    color(C_SHELL) difference() {
        rbox(170, 170, 75, 6);
        translate([3, 3, 3]) rbox(164, 164, 80, 4);
    }
    translate([145, 0, 40]) rotate([90, 0, 0]) {
        color(C_DARK) cylinder(d = 34, h = 3);
        color(C_BAD)  translate([0, 0, 3]) cylinder(d = 24, h = 7);
    }
    color(C_DARK) translate([145, -0.01, 62]) face_text("PRINT", 6, "center");
}

module stock_guts() {
    translate([0, 0, E * 60]) {
        translate([800, 205, 9]) { pi4(); pi4_standoffs(6); }
        translate([800, 164, 3]) ds3231();
        for (k = [0:3]) translate([797 + k * 39, 127, 3]) hx711();
        for (k = [0:3])   // HX711 DT/SCK → Pi GPIO
            cable([[800 + k * 39, 136, 11], [800 + k * 39, 136, 32],
                   [812 + k * 12, 257, 32], [812 + k * 12, 257, 22]], 1.6, WIRES[k]);
    }
    if (E == 0) cable([[766, 284, 19], [806, 272, 10], [806, 152, 8]], 5);   // load-cell bundle
}

module printer() {
    color(C_DARK) rbox(110, 115, 58, 8);
    color(C_KEY)  translate([4, 31, 58]) rbox(102, 80, 3, 6);
    color(C_OK)   translate([95, 14, 58]) cylinder(d = 5, h = 1.5);
    // the slip: rises out of the slot, curls forward at the top
    translate([26, 28, 58]) {
        color(C_PAPER) cube([58, 0.6, 105]);
        color(C_PAPER) translate([0, -12, 105]) rotate([0, 90, 0]) intersection() {
            difference() {
                cylinder(r = 12.3, h = 58);
                translate([0, 0, -1]) cylinder(r = 11.7, h = 60);
            }
            translate([-13, -13, -1]) cube([13, 26, 60]);
        }
        lines = [   // text, size, font, height on the slip
            ["STOCK CLOCK · WED",  4.0, MONO_B, 94],
            ["KANGKONG",           5.0, MONO_B, 78],
            ["have 0.8kg  day 2",  3.6, MONO,   70],
            ["uses 2.6kg/day",     3.6, MONO,   63],
            ["BUY  2 kg",          5.5, MONO_B, 53],
            ["PREP 2.6 kg",        4.2, MONO_B, 45],
            ["TAUGE",              5.0, MONO_B, 34],
            ["have 1.5kg  day 1",  3.6, MONO,   26],
            ["BUY  nothing",       4.5, MONO_B, 16],
            ["+ 2 more",           3.2, MONO,    6]
        ];
        color(C_DARK) {
            for (l = lines) translate([3, 0, l[3]]) face_text(l[0], l[1], font = l[2]);
            translate([3, -0.8, 88]) cube([52, 0.8, 0.8]);
        }
    }
}

module stock_clock() {
    color(C_PLY)   rbox(770, 290, 8, 6);
    color(C_SHELL) translate([0, 0, 8]) cube([770, 12, 52]);                  // front rail
    color(C_DARK)  translate([0, 278, 8]) difference() {                     // rear cable duct
        cube([770, 12, 22]);
        translate([-1, 2, 2]) cube([772, 8, 22]);
    }
    for (i = [0:3]) slot(i);
    translate([790, 120, 0]) stock_box();
    stock_guts();
    translate([800, -E * 50, 0]) printer();
}

if (SHOW == 1) chope();
if (SHOW == 2) stock_clock();
if (SHOW == 0) { stock_clock(); translate([150, 560, 0]) chope(); }
