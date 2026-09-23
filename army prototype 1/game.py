"""Chope's game layer: the unit's month in a league, stickers, Singlish banter.

The only inputs are poll COUNTS, so the game is anonymous by construction -- it scores
the unit, never a person.  Rules (13-chope-fun-bot-decisions.md, option B):
    Goal Day = replies >= 80% of strength.  "Not eating" counts exactly like "Eating",
               so a fake reply earns nothing a real one wouldn't.
    One Goal Day = one point.  MOST points at month end wins the cookhouse special.
Rival units are SEEDED demo data -- say so on the slide.
"""
import json, math, os, random, sys, time

HERE  = os.path.dirname(os.path.abspath(__file__))
UNITS = os.environ.get("CHOPE_UNITS", os.path.join(HERE, "units.json"))  # never relative: cron CWD is /
HOME  = os.environ.get("CHOPE_UNIT", "Alpha Coy")
PRIZE = os.environ.get("CHOPE_PRIZE", "🍔 Western lunch")
PACKS = os.environ.get("CHOPE_STICKERS", "UtyaDuck,HotCherry").split(",")
GOAL, LUNCHES = 0.80, 20                 # 80% replied; ~20 weekday lunches a month

# Demo month, 17 lunches in: HOME is tied for first, so the first visitor whose vote
# makes a Goal Day takes the lead.  [pts, portions saved]
SEED = {"Bravo Coy": [14, 96], HOME: [14, 88], "Hangar 3": [12, 81],
        "Charlie Coy": [10, 64], "Signals Det": [7, 40]}

MOODS = {"win": "🏆🥇🎉🥳😎", "hype": "🔥💪👍😁👏", "sad": "😭😢😞💔🥲", "think": "🤔🧐🙄"}
EXCUSES = ["Sergeant say run 2.4 during lunch.", "Guard duty, cannot.",
           "Book out early, eat McDonald's already.", "Canteen got chicken rice, sorry cookhouse.",
           "Stuck in the hangar, aircraft more important than me.",
           "Medical appointment, MO say drink water only.", "Fall in for IPPT briefing, again.",
           "Store IC hiding my mess tin."]
EIGHTBALL = ["Confirm plus chop.", "Steady lah, can.", "Wah, don't think so leh.",
             "Ask your sergeant.", "Maybe. Depends on the curry.", "Sure or not? Tap the poll first.",
             "No lah, dream on.", "Signs point to Western lunch 🍔."]
HELP = [("leaderboard", "Unit ranking this month"), ("progress", "Our points and rank"),
        ("saved", "Portions not wasted this month"), ("today", "Replies so far vs the goal"),
        ("menu", "Vote next month's special"), ("excuse", "NS excuse to skip lunch"),
        ("8ball", "Ask the cookhouse oracle"), ("demo", "Full lunch in 45 s · /demo monthend · /demo reset")]


def seed():
    g = {"pts": {u: p for u, (p, s) in SEED.items()},
         "saved": {u: s for u, (p, s) in SEED.items()}, "played": 17, "last_left": 9,
         "month": time.strftime("%Y-%m"), "champions": []}
    save(g)
    return g


def load():
    try:
        g = json.load(open(UNITS))
    except (OSError, ValueError):
        return seed()
    g.setdefault("month", time.strftime("%Y-%m"))   # units.json from before rollover existed
    g.setdefault("champions", [])
    return g


def save(g):
    json.dump(g, open(UNITS + ".tmp", "w"))
    os.replace(UNITS + ".tmp", UNITS)


def need(n):
    return math.ceil(GOAL * n)


def ranking(g):
    return sorted(g["pts"], key=lambda u: (-g["pts"][u], -g["saved"][u], u))


def rank(g, u=HOME):
    return ranking(g).index(u) + 1


def record(g, replied, n, saved):
    """One lunch, scored at the cutoff: replies are all a Goal Day needs.
    Returns (goal_day, took_the_lead)."""
    was = rank(g)
    goal = replied >= need(n)
    g["pts"][HOME] += goal
    g["saved"][HOME] += max(0, saved)
    g["played"] += 1
    save(g)
    return goal, rank(g) == 1 and was != 1


def month_name(ym):
    return time.strftime("%B", time.strptime(ym, "%Y-%m"))


def next_month(ym):
    y, m = map(int, ym.split("-"))
    return "%04d-%02d" % (y + m // 12, m % 12 + 1)


def table(g):
    medal = ["🥇", "🥈", "🥉"]
    return "\n".join("%s %-12s %2d pts%s" % (medal[i] if i < 3 and g["pts"][u] else "%d." % (i + 1), u,
                                             g["pts"][u], "  👈 us" if u == HOME else "")
                     for i, u in enumerate(ranking(g)))


def rollover(g, new):
    """Month end: crown the leader, zero every unit, start `new` from lunch 0.
    Ties go to portions saved -- the same order the leaderboard showed all month.
    Returns the announcement, or None if the month has not changed."""
    if new <= g["month"]:         # "YYYY-MM" sorts as text; never roll backwards after
        return None               # a /demo monthend fast-forward
    top, old, final = ranking(g), month_name(g["month"]), table(g)
    champ = top[0] if g["pts"][top[0]] else None
    if champ:
        g["champions"].append([g["month"], champ])
        head = "🏆🏆🏆 %s CHAMPION: %s 🏆🏆🏆\n%s is theirs — vote the menu below!" % (
            old.upper(), champ.upper(), PRIZE)
        if champ != HOME:
            head += "\n\n%s finished #%d. Next month our turn lah." % (HOME, top.index(HOME) + 1)
    else:
        head = "%s ends with no Goal Days at all. No winner, no %s. Sian." % (old, PRIZE)
    for u in g["pts"]:
        g["pts"][u] = g["saved"][u] = 0
    g["played"], g["month"] = 0, new
    save(g)
    return ("%s\n\nFinal table, %s:\n%s\n\n🔄 %s starts now. Everybody back to 0 — "
            "fresh start." % (head, old, final, month_name(new)))


def progress(g):
    p = g["pts"][HOME]
    bar = "▓" * min(10, round(10 * p / LUNCHES)) + "░" * (10 - min(10, round(10 * p / LUNCHES)))
    return ("%s %d pts · #%d of %d · %d lunches left\n🏆 Most points at month end eats %s"
            % (bar, p, rank(g), len(g["pts"]), max(0, LUNCHES - g["played"]), PRIZE))


def leaderboard(g):
    last = "\nLast month: 🏆 %s" % g["champions"][-1][1] if g["champions"] else ""
    return "🏆 Chope League — %s\n\n%s\n\nMost points at month end eats %s.%s" % (
        month_name(g["month"]), table(g), PRIZE, last)


def morning(g, n):
    return ("🍛 Lunch poll is up. Tap lah — silent also counted as eating, cook for nothing.\n"
            "Yesterday %d plates came back.\nGoal Day = %d replies.\n\n%s"
            % (g["last_left"], need(n), progress(g)))


def locked(replied, n, cook, goal, lead):
    s = "🔒 Poll closed. %d/%d replied — " % (replied, n)
    s += "GOAL DAY ✅ +1 pt" if goal else "short by %d 😬 no point today" % (need(n) - replied)
    s += "\nKitchen cooking %d. Don't say bojio." % cook
    if lead:
        s += "\n\n🥇 %s TAKES THE LEAD! %s is within reach." % (HOME.upper(), PRIZE)
    return s


def scorecard(g, left, taken):
    prev, g["last_left"] = g["last_left"], left
    save(g)
    verdict = ("Steady lah 👏" if left < prev else "Same same." if left == prev
               else "Wah, more than yesterday. Tap the poll leh 🥲")
    return ("🍽 Lunch done. %d plates came back (yesterday %d). %d eaten.\n%s\n\n%s"
            % (left, prev, taken, verdict, progress(g))), ("hype" if left <= prev else "sad")


def saved(g):
    return ("♻️ %s: %d portions NOT cooked for nobody this month, vs the old "
            "'silent = eating' rule.\nThe food you didn't waste is what pays for %s."
            % (HOME, g["saved"][HOME], PRIZE))


_stickers = []


def sticker(tg, chat, mood):
    """Public packs, looked up by name, cached.  A sticker never breaks a message."""
    global _stickers
    if not _stickers:
        for name in PACKS:
            try:
                _stickers += tg("getStickerSet", name=name.strip())["stickers"]
            except Exception as e:
                print("sticker pack %s skipped: %s" % (name, e), file=sys.stderr)
    pool = [s for s in _stickers if s.get("emoji") and s["emoji"] in MOODS[mood]] or _stickers
    try:
        tg("sendSticker", chat_id=chat, sticker=random.choice(pool)["file_id"])
    except Exception as e:                    # ponytail: includes "no packs loaded"
        print("sticker skipped:", e, file=sys.stderr)
