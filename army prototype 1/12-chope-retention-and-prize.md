# Chope: retention loop and the monthly special lunch

> **Why this file exists.** Raghav's direction, 23 Sep: people have to keep coming back, and
> **there will be a prize**: once a month the cookhouse cooks something it would not normally
> make (a Western lunch, say) for the units that take part best. This file designs around that.
> It does not argue against it. `11-chope-gamification-research.md` concluded "no tangible
> rewards", and **that conclusion is overruled here.** Its Telegram and anonymity facts are
> reused. Where the prize carries a real risk (fake votes, overjustification, sandbagging,
> winner-take-all drop-off), the answer here is a **rule**, not a veto.
>
> **Provenance.** `[cited]` public source, URL inline and in §10 · `[T1]` Raghav's own service ·
> `[T2]` senior's interview, 4 Sep · `[T5]` Raghav, 20 Sep · `[ASSUMED]` needs fieldwork or asking ·
> `[DERIVED]` arithmetic on the above · `[weak]` non-primary source, shown only because nothing
> better exists. Written 23 Sep 2026.

---

## 0. TL;DR: the whole loop

**Think of Chope as a SaaS product whose "account" is the unit.** The poll is anonymous at
Telegram's servers, so the bot never learns who voted
([`is_anonymous`, `PollAnswer`](https://core.telegram.org/bots/api#sendpoll)) `[cited]`.
Retention therefore has to be measured and rewarded **per unit, per lunch**, never per person.
That is not a gap. Everything below works from `stopPoll` counts alone.

**The behaviour we pay for is a reply, and "Not eating" counts exactly the same as "Eating".**
That one rule removes most of the gaming (§4). The cheapest way for a unit to hit its goal is to
answer truthfully.

| Cadence | What happens | Mechanism (evidence) | Telegram call |
|---|---|---|---|
| **Daily 07:00** | Poll posts. Its description carries the unit's month bar and today's goal | External trigger + goal-gradient (Eyal; Kivetz 2006) | `sendPoll(description=…)` |
| **Daily ~09:45** | A nudge, **only if the unit is below its goal**, worded from a rotating pool | Prompt (Fogg B=MAP). Rotation because fresh templates beat stale ones (Yancey & Settles 2020) | one-shot `getUpdates` → `poll` state, then `sendMessage` |
| **Daily at cutoff** | Board locks. "Goal Day ✅" or "not today" | Immediate feedback | `stopPoll`, `sendMessage` |
| **Daily after service** | Scorecard: plates that came back (variable), goal result, bar edited in place | Variable reward (Eyal); Half B made visible | `sendMessage(disable_notification)`, `editMessageText` on the pinned bar |
| **Friday** | Week recap, with every unit's position toward the special | Group goal + intergroup comparison (Kleingeld 2011; Erev 1993) | `sendMessage` |
| **Monday after the 15th** | **Fresh start.** Units that can no longer reach 15 are offered route 2: 9 of the last 10 lunches | Fresh-start effect (Dai, Milkman & Riis 2014); stops trailing units giving up (Casas-Arce 2009) | `sendMessage` |
| **Last lunch of the month** | Results. **Every unit over the threshold qualifies**, with no single winner. Qualifiers vote on which special | Criterion prize, not a tournament (Good Behavior Game 1969; Bandiera 2013). The vote is the Hook's **investment** step | anonymous `sendPoll` to qualifiers |
| **Monthly, ~2nd week** | **The special lunch.** Next month's bar has already started, with 2 days endowed | Endowed progress (Nunes & Drèze 2006); avoids post-reward reset (Kivetz 2006) | — |

**The prize pays for itself, roughly** (§3). A 90-man unit on Chope has about **95 fewer portions
cooked a month** `[DERIVED]`. At an assumed S$1.50–3.00 of ingredients a portion that is
**S$140–285 a month**, about what a special-lunch upgrade for the same 90 men costs `[ASSUMED]`.
So the pitch is *"the food you didn't waste becomes your Western lunch"*, and it only holds if
most of the saving goes back into the special. If Half B later shrinks the kitchen buffer, the
saving more than doubles, and then a slice of it is enough.

**Cheapest version of the prize, to ask about first:** the SAF caterer already runs festive meals
and brand collaborations (Killiney laksa, mee siam)
([PIONEER, 13 Sep 2024](https://defencepioneer.sg/pioneer-articles/13sep24_news1)) `[cited]`. Giving
the qualifying units **the pick of an existing special day's menu** costs the caterer close to
nothing. Ask for this before asking for an extra meal (§9).

---

## 1. Frameworks, and what each one becomes under anonymity

| Framework (primary source) | What it says | What it becomes in Chope, at unit level |
|---|---|---|
| **Hook model**, Eyal ([nirandfar.com](https://www.nirandfar.com/how-to-manufacture-desire/)) `[cited]` | Trigger → action → **variable reward** → **investment**. Investments *"can be leveraged to make the trigger more engaging, the action easier, and the reward more exciting with every pass"* | Trigger = poll + nudge. Action = one tap. Variable reward = today's plates-came-back number and the running race to the special. Investment = the **menu vote**: qualifiers decide what the kitchen cooks, which gives next month's bar something to aim at |
| **Variable rewards: tribe, hunt, self**, Eyal ([nirandfar.com](https://www.nirandfar.com/want-to-hook-your-users-drive-them-crazy/)) `[cited]` | Social, material and mastery rewards | Tribe: *our unit* vs other units. Hunt: the special lunch. Self: "our number was accurate". All three work at unit level |
| **B = MAP**, Fogg ([behaviormodel.org](https://www.behaviormodel.org/)) `[cited]` | *"Behavior happens when Motivation, Ability, and a Prompt come together at the same time … When a behavior does not occur, at least one of those three elements is missing"* | Ability is already at its maximum (two taps in a chat they are in). **The missing piece is the prompt at the right moment and a reason to care.** The nudge is the prompt, the prize is the motivation. Do not add steps |
| **Goal-gradient**, Kivetz, Urminsky & Zheng 2006 ([JMR PDF](https://home.uchicago.edu/ourminsky/Goal-Gradient_Illusionary_Goal_Progress.pdf)) `[cited]` | Café "buy 10 get 1": *"interpurchase times decrease by 20%"* as the free coffee nears. **After redeeming, the next card starts slow again** (post-reward resetting) | Show a **visible bar toward the special** every day. Hold the special lunch *after* next month's bar has started, so the reward day falls inside a live bar and not at a reset |
| **Endowed progress**, Nunes & Drèze 2006 ([JCR](https://academic.oup.com/jcr/article-abstract/32/4/504/1787425)) `[cited]` | A 10-stamp card with 2 pre-stamped beat an 8-stamp card, same effort: **34% vs 19%** completion ([summary](https://loyaltyrewardco.com/loyalty-psychology-series-endowed-progress-effect/)) `[weak]` for the exact figures | The bar is **17 Goal Days with 2 "on the house"**: the same 15 earned days, framed as already started. The same for every unit, and printed in the rules so it is not a trick |
| **Fresh start**, Dai, Milkman & Riis 2014 ([Mgmt Sci PDF](https://faculty.wharton.upenn.edu/wp-content/uploads/2014/06/Dai_Fresh_Start_2014_Mgmt_Sci.pdf)) `[cited]` | Gym visits and goal commitments rise after *"the outset of a new week, month, year, or semester"*. Landmarks *"relegate past imperfections to a previous period"* | Mid-month second route (§4.2), announced on a **Monday**. The monthly reset itself is a landmark |
| **Streaks and loss aversion**, Silverman & Barasch 2023 ([JCR](https://academic.oup.com/jcr/article-abstract/49/6/1095/6623414)) `[cited]` | Intact logged streaks raise engagement compared with broken ones. The effect is **amplified when people blame themselves for the break and attenuated when a streak can be "repaired"** | Primary display is a count ("11 of 14"), which cannot break. A unit streak is shown as a secondary line and **auto-repairs** once a week (§2.6) |
| **Duolingo streak freeze** ([Duolingo blog](https://blog.duolingo.com/how-duolingo-streak-builds-habit)) `[cited]` | Letting learners equip two Freezes *"increased the relative number of active learners on Duolingo every day by +0.38%"*. 7-day streakers are *"3.6 times more likely to complete their course"* | Repair is worth building in, and the gain is small. **First-party numbers from 500M users; do not expect a measurable effect at 90** |
| **Duolingo leagues** ([Duolingo blog](https://blog.duolingo.com/duolingo-leagues-leaderboards/)) `[cited]` | Weekly reset. *"You're matched with people who have similar study habits to you"* | Compare units against **similar-sized** units only, and reset monthly. Erev 1993 found the same thing: competition works best between similar teams |
| **Notification bandit**, Yancey & Settles, KDD 2020 ([PDF](https://research.duolingo.com/papers/yancey.kdd20.pdf)) `[cited]` | Novelty makes new templates beat old ones for a while (*"recovering arm"*). Their algorithm gave *"a 0.5% increase in total daily active users … and a 2% increase in new user retention"* | **Rotate nudge wording** from a pool of 6–8 and never repeat one within a week. A bandit is overkill at n=1 group a day. Plain round-robin captures the novelty part |
| **Strava clubs and group challenges** ([Strava Help](https://support.strava.com/en-us/articles/15401736-group-challenges)) `[cited]` | Group challenges include a **"Group Goal: … no leaderboard, but you can see how you're contributing to the group effort"**. Club leaderboards reset weekly ([Clubs](https://support.strava.com/en-us/articles/15402172-clubs-on-strava)) | The "Group Goal" form is Chope's form: the unit chases a shared bar. The cross-unit board is secondary |
| **Retention curves**, Amplitude docs ([Amplitude](https://amplitude.com/docs/analytics/charts/retention-analysis/retention-analysis-interpret)) `[cited]` | N-day vs unbounded vs bracket retention. Cohort entry = *"the day a user triggers the starting event"* | Cohort = unit, entry = first poll. Bracket = calendar month (§6) |

---

## 2. Each mechanic, with the message it sends

All figures are illustrative for a 90-strong unit. **They are not trial data.** Bars are
10 characters wide, so they fit a phone line and render in any Telegram client.

### 2.1 The morning poll: trigger plus bar (`sendPoll`, `description` 0–1024 chars)

`sendPoll` takes a `description` *"of the poll to be sent, 0-1024 characters"*
([Bot API 10.3](https://core.telegram.org/bots/api#sendpoll)) `[cited]`. It is the only text the
silent see before cutoff, so the bar goes there.

```
📊 Lunch today?                                  [anonymous poll]
   ○ Eating
   ○ Not eating

   SPECIAL LUNCH · September
   ▓▓▓▓▓▓▓░░░  12/17 Goal Days   (2 on the house)
   Today's goal: 72 replies by 10:30. Either answer counts.
   Plans change? Tap again, you can switch until 10:30.
```

`allows_revoting` *"defaults … to True for regular polls"* `[cited]`, so "switch" is true today.

### 2.2 The conditional nudge: a prompt, sent only when needed

**Constraint:** Chope has no update loop, and `08-chope-prd.md` forbids a listening socket. A
**single cron-run `getUpdates` call** is outbound, like every other call. It returns `poll`
updates, which carry live aggregate counts: *"New poll state. Bots receive only updates about
manually stopped polls and polls, which are sent by the bot"*
([Update](https://core.telegram.org/bots/api#update)) `[cited]`. That is still counts only, with
no user id. Whether a privacy-mode group bot receives these in practice is `[ASSUMED]`, so test it
on day 1 of the trial.

Rule: at 09:45, if `replies < goal`, post **one** message. Otherwise post nothing. Ninety people
get pinged only on days the unit is behind, which keeps it from becoming noise in the unit's own
chat.

```
⏰ 45 min to cutoff · 61 of 72 replies so far.
11 more and today is a Goal Day. "Not eating" counts.
```

Rotation pool (round-robin, no repeats within 5 lunches, per Yancey & Settles):

```
• "11 taps from a Goal Day. Out for lunch? That counts too."
• "Kitchen cooks at 10:30. Silent = cooked for."
• "61/72. Your September bar is at 12/17."
• "On MC, course or duty today? Tap Not eating yourself, even from home."
• "3 lunches to the menu vote cut-off. 11 taps today."
```

Never word a nudge so it suggests voting on someone else's behalf (§4.3).

Print the count that **did** reply, never the count that did not. "29 haven't replied" is the
destructive descriptive norm (Cialdini 2003, cited in `11` §2.2).

### 2.3 Cutoff and after-service scorecard: the variable reward

```
🍛 LUNCH · Thu 24 Sep
Replied by 10:30: 76 / 90   goal 72  ✅ GOAL DAY
Came back uneaten: 7 plates   (last 5 lunches: 12, 9, 15, 8, 7)

SPECIAL LUNCH · September
▓▓▓▓▓▓▓▓░░  13/17   4 more · 6 lunches left
```

Send with `disable_notification=True`: *"Users will receive a notification with no sound"*
([sendMessage](https://core.telegram.org/bots/api#sendmessage)) `[cited]`. The "came back" number
is the **variable** part. It moves every day, the unit cannot fully control it, and it is never
scored (`11` §0 rule, kept). The bar is the scored part.

### 2.4 Pinned bar, edited in place (optional, needs admin)

Pin one message at the start of the month and `editMessageText` it after every lunch. The unit
gets a permanent progress bar at the top of its chat with **zero new messages a day**. Cost: the
bot *"must be an administrator with the 'can_pin_messages' right"*
([pinChatMessage](https://core.telegram.org/bots/api#pinchatmessage)) `[cited]`. Pass
`disable_notification=True` to the pin. If the food IC will not grant admin, skip this. §2.1
already carries the bar daily.

```
📌 SEPTEMBER · SPECIAL LUNCH
▓▓▓▓▓▓▓▓░░  13/17 Goal Days
Route 2 (from Mon 21): 5 of last 10 needed 9
Updated after every lunch.
```

### 2.5 Friday recap and the cross-unit board

```
📅 WEEK 39 · Alpha
Goal Days this week: 4 of 5
Month: ▓▓▓▓▓▓▓▓░░ 13/17

SBAB cookhouse, units on track for the special:
  Alpha    ▓▓▓▓▓▓▓▓░░ 13   ✅ on track
  Bravo    ▓▓▓▓▓▓▓░░░ 12   ✅ on track
  Charlie  ▓▓▓▓▓░░░░░  9   route 2 open Mon
Every unit that reaches 17 eats. This is not a race.
```

The **last line is the design**: a threshold, not a tournament (§4.1). Rank is shown because
intergroup comparison removes free-riding (Erev 1993, in `11` §2.2) and Bandiera et al. found a
tournament prize lifted team output by 24%, but **only for teams at the top**, while rank feedback
alone cut the bottom teams' output by 14%
([JEEA 2013](https://academic.oup.com/jeea/article/11/5/1079/2315903)) `[cited]`. So the board
shows position, **the prize never depends on it**, and a unit behind always has a live route
(§4.2).

### 2.6 Streak line, with auto-repair

```
🔥 Goal Day streak: 6   (1 repair left this week)
```

One missed lunch a week is repaired automatically, like Duolingo's Freeze. Silverman & Barasch
found repair attenuates the demotivation of a break `[cited]`. It is a secondary line. The
count in §2.3 is what decides the prize.

### 2.7 Fresh-start Monday (after the 15th)

```
🔄 NEW HALF · Mon 21 Sep
Charlie: 17 is out of reach this month. Route 2 is open:
9 Goal Days in the last 10 lunches also earns the special.
Starts today. Last half doesn't count.
```

Only sent to units that route 1 can no longer reach. Units still on track get nothing extra.

### 2.8 Month end: qualifiers and the menu vote (investment step)

```
🏁 SEPTEMBER RESULTS
Alpha 17 ✅ · Bravo 18 ✅ · Charlie route 2 ✅ · Delta 11
Qualified units eat the special on Wed 14 Oct.
```

Then, **to each qualifying unit only**, an anonymous poll:

```
📊 October special: what should the kitchen cook?      [anonymous poll]
   ○ Western: chicken chop, fries, coleslaw
   ○ Mala xiang guo
   ○ Nasi lemak with fried chicken
   ○ Korean bulgogi rice
   Options are the ones the cookhouse said it can do. Most votes across all qualifying units wins.
```

Options are **pre-approved by the cookhouse** `[ASSUMED]`, because `allow_adding_options` is
*"not supported for anonymous polls"* `[cited]` and the kitchen needs the choice to be feasible
anyway. Sum the `stopPoll` counts across units' polls. This is the **investment**: the unit has now
shaped what it will eat, so next month's bar is chasing a meal it chose.

### 2.9 Telegram surfaces: safe or not

| Surface | Identity reaches the bot? | Use |
|---|---|---|
| `sendPoll(is_anonymous=True)`, `stopPoll`, `poll` update via `getUpdates` | No, counts only | Core |
| `sendMessage`, `editMessageText`, `pinChatMessage`, `sendPhoto` | Outbound only | Yes. `sendPhoto` (≤10 MB) could carry a rendered bar chart for the Friday recap, but text bars render everywhere and need no image library. **Skip** |
| `sendPoll(type="quiz")` | Anonymous if `is_anonymous` | Optional Friday "how many plates came back?" (`11` §3.4) |
| `message_reaction` | **Yes.** `MessageReactionUpdated.user`: *"The user that changed the reaction, if the user isn't anonymous"* ([API](https://core.telegram.org/bots/api#messagereactionupdated)) `[cited]` | **Never read reactions** |
| Inline keyboard, `setGameScore` | Yes, `from.id` / `user_id` | Never |

Rate limit: *"In a group, bots are not be able to send more than 20 messages per minute"*
([Bot FAQ](https://core.telegram.org/bots/faq)) `[cited]`. The loop sends at most 3 a day per group.

---

## 3. The prize pays for itself: arithmetic

Inputs from `CLAUDE.md`: strength ≈ 90. Today silence counts as eating, so the indent ≈ strength
`[T1]` `[ASSUMED]`. The kitchen cooks ~×1.10 of whatever it is given `[T5]`. Chope saves **4.8%**
against the indent in steady state (replay, 20 runs × 60 meals). Lunch only, ~20 weekday lunches
a month `[T5]`.

```
Portions not cooked per lunch   = 90 × 0.048 × 1.10          = 4.75
Per month (20 lunches)          = 4.75 × 20                   ≈ 95 portions / unit
Ingredient cost per portion     = S$1.50 – 3.00              [ASSUMED]
Monthly saving per 90-pax unit  = 95 × 1.50 … 95 × 3.00      ≈ S$143 – 285

Cost of the special, per unit   = premium over a normal lunch × 90
                                = S$1.50 – 3.00 × 90         ≈ S$135 – 270   [ASSUMED]
```

**What that means:** under these assumptions, one unit's monthly saving ≈ one special lunch for
the same unit. **The self-funding claim holds only if most of the saving is returned, not a
slice.** Say so on the slide and do not round it up.

**Where it becomes a slice.** Half B's real prize is the buffer (`CLAUDE.md`). If the evidence
Chope collects lets the kitchen cut its buffer from 10% to 3%:

```
Extra portions not cooked       = 90 × 0.07 × 20              ≈ 126 / month / unit
Extra saving                    = 126 × 1.50 … 3.00           ≈ S$189 – 378
Total                           ≈ S$330 – 660 / month; special costs S$135 – 270 → 20–80% of it
```

**Funding scales with qualifiers.** Every unit that qualifies has, by qualifying, replied enough
to produce its own saving. A threshold prize therefore does not blow the budget when many units
qualify, which is the usual objection to "everyone above X wins".

**Caveats, each load-bearing:**
- **No public source gives SAF per-meal cost.** MINDEF's replies on NSF meals give none
  ([6 May 2026 PQ](https://www.mindef.gov.sg/news-and-events/latest-releases/6may26-pq3/);
  [1 Feb 2018](https://www.mindef.gov.sg/news-and-events/latest-releases/01feb18_fr/)) `[cited]`.
  Forum claims of S$5–6 per contracted meal exist
  ([HardwareZone](https://forums.hardwarezone.com.sg/national-service-knowledge-base-162/does-saf-meal-cost-%246-each-how-come-caterer-like-lee-garden-dont-bid-4974611.html))
  `[weak]`. S$1.50–3.00 of *ingredients* is an assumption. **Ask the cookhouse (§9).**
- **Who keeps the saving depends on §8, still unresolved.** If the caterer is paid per meal
  scanned or indented, an uncooked portion is the **caterer's** saving. Then the caterer funds the
  special, and it is also their sustainability story. If MINDEF pays for what is cooked, the saving
  is MINDEF's and the approval sits with the unit/camp.
- **The 4.8% was measured at the replay's reply rates.** How the saving moves with reply rate is
  **not measured**. A `replay.py` sweep over reply rates would give the curve that ties "more
  replies" to "more saving" (a run, no new code, if the replay exposes reply rate as a parameter
  `[ASSUMED]`).
- The saving is real only if the kitchen cooks to the board. Chope logs `buffer_pct` every lunch,
  so this is checkable.

---

## 4. Prize rules that close off gaming

The rules are short enough to print in the poll's pinned message:

```
SPECIAL LUNCH RULES
1. A Goal Day = your unit's replies reach the goal by cutoff. Eating and Not eating count the same.
2. 15 Goal Days in the month earns the special (bar shows 17 with 2 on the house).
   Or: 9 Goal Days in the last 10 lunches.
3. Every unit that qualifies eats. There is no single winner.
4. Goal = 80% of your unit's strength, same % for every unit. Days you're not in camp don't count.
5. Qualifying units vote on the menu.
```

### 4.1 Threshold, not tournament

| Design | Evidence | Verdict |
|---|---|---|
| Single winner per month | Leaders slack once ahead, and trailers quit when the gap looks too large: *"winning participants decrease their effort as their lead extends"* (Casas-Arce & Martínez-Jerez 2009, [Mgmt Sci](https://pubsonline.informs.org/doi/10.1287/mnsc.1090.1021)) `[cited]`. Tournament gains accrue **only to top teams** (Bandiera et al. 2013) `[cited]` | Rejected |
| **Threshold, every unit can win** | The Good Behavior Game (Barrish, Saunders & Wolf 1969, [JABA](https://onlinelibrary.wiley.com/doi/abs/10.1901/jaba.1969.2-119)) `[cited]`: classroom teams compete against a **fixed criterion**, *"if both teams keep their points below a preset level, then both teams share in the reward"* ([summary](https://en.wikipedia.org/wiki/Good_Behavior_Game)) `[weak]`. Group consequences for individual behaviour, which is exactly Chope's anonymous case | **Adopted** |
| Threshold + rank for a non-material perk | Keeps the "tribe" reward and the intergroup comparison (Erev 1993) with no one excluded from the meal | **Adopted:** rank only breaks ties in the menu vote |

### 4.2 Keep every unit live all month

The mid-month route (9 of the last 10) exists because of Casas-Arce: a unit that is mathematically
out on day 8 stops replying for 12 lunches, and silence is the waste. Route 2 opens on a
**Monday** (fresh start) and gives any unit a real chance until the 11th-last lunch `[DERIVED]`.

### 4.3 Threat model

| Gaming move | Why someone would | What stops it |
|---|---|---|
| **Fake "Eating" to hit the count** | Near the goal, tap anything | Rule 1. "Not eating" counts equally, so there is no reason to pick Eating falsely. A true reply is as cheap as a false one. **Residual cost:** a thoughtless "Eating" floors COOK (`confirmed ≤ COOK`) and adds up to `1 − r` of a portion compared with staying silent. The after-service line *"said eating 58 · plates taken 81"* surfaces it cookhouse-wide: whenever `Σ eat > taken`, at least that many "Eating" votes were false `[DERIVED]`. **Show it, do not punish on it.** It cannot be attributed to a unit when the pan is shared |
| **Outsiders in the chat voting** | Inflate replies | Telegram: one vote per account, members only. **Set `CHOPE_STRENGTH` explicitly** per unit. `chope.py` already warns when `votes > strength` |
| **Sandbagging the goal** | If the goal were "your median + a bit", a unit could reply less in week 1 to get an easy target | Rule 4. The goal is a **fixed % of strength**, the same for all units, never self-referenced. (This replaces `11` §2.2's "recent median plus a little" for the prize goal) |
| **Commander orders "everyone tap Eating"** | The old tally culture `[T1]` `[T2]` | Rule 1 removes the reason. An order to **reply** is aligned with the goal and harmless, and anonymity keeps "Not eating" safe from that commander. Flag in the think-aloud test (§7) |
| **Someone taps for absent mates** | Hit the count | Impossible: one account, one vote. The nudge pool must never suggest it (§2.2) |
| **Coasting after qualifying** | Kivetz: effort resets after a reward; Casas-Arce: leaders slack | Days after qualifying count toward **menu-vote tie-break**. The special is held in the 2nd week of the next month, so a live bar is already running |
| **Unit in the field all week** | Out of camp, cannot "reply properly" | Days out of camp **do not count** (Rule 4). But a whole-unit "Not eating" before an exercise is the single most valuable reply there is: Fort Jackson's waste was driven partly by *"a unit … scheduled to have a meal … but does not show up due to training requirements"* ([EPA 2019](https://cfpub.epa.gov/si/si_public_record_report.cfm?dirEntryId=346767&Lab=NRMRL)) `[cited]`. **That reply earns a Goal Day** |

### 4.4 Overjustification: why the prize is safe here

Deci, Koestner & Ryan's meta-analysis found expected tangible rewards undermine *intrinsic*
motivation (d = −0.28 to −0.40). It also found the effect **is not significant when the task is
uninteresting to begin with**, and that **positive feedback raises motivation** (d = +0.33)
([Psych Bull 1999](https://doi.org/10.1037/0033-2909.125.6.627);
[authors' 2001 summary](https://www.selfdeterminationtheory.org/SDT/documents/2001_DeciKoestnerRyan.pdf))
`[cited]`. Nobody finds replying to a lunch poll intrinsically interesting. There is no intrinsic
motivation to crowd out. The real risk is **what happens if the prize stops**: effects fade once
feedback stops (Allcott & Rogers 2014, in `11` §2.2). The answer is §3: a self-funding prize has
no budget reason to stop. Keep the daily positive feedback (§2.3) running alongside it, since
that is the part the meta-analysis says helps.

---

## 5. Military precedents (official sources)

| Precedent | What it shows | Source |
|---|---|---|
| SAF cookhouses already run **festive meals** (*"Baked Honey Glazed Chicken Set for Chinese New Year"*) and **brand collaborations** (Killiney *laksa*, curry chicken, *mee siam*) | The special lunch is an existing operational capability, not a new ask. The prize can re-use a slot that already exists | [PIONEER, 13 Sep 2024](https://defencepioneer.sg/pioneer-articles/13sep24_news1) `[cited]` |
| SFIM chefs *"plan the meals according to what the majority prefers"* and *"constantly engage servicemen … to fine-tune the menus"* | The menu vote (§2.8) is a formal version of what the caterer says it already does | same `[cited]` |
| Two caterers: SFIM (SATS) and Foodfare | Whoever runs SBAB is the approver for the special `[ASSUMED]` | same `[cited]` |
| SAF diets are planned by *"nutritionists and sports scientists"*. Servicemen give menu feedback *"through their commanders"* | The special must still pass nutrition planning. Ask (§9) | [MINDEF, 1 Feb 2018](https://www.mindef.gov.sg/news-and-events/latest-releases/01feb18_fr/) `[cited]` |
| **SAF Best Unit Competition**, since 1969 | Unit-vs-unit recognition is native to SAF culture. No food or sustainability criterion | [MINDEF, 28 Jun 2026](https://www.mindef.gov.sg/news-and-events/latest-releases/28jun26-nr/) `[cited]` |
| **US Army Philip A. Connelly Award**, since 1968: dining facilities judged on *"food preparation, taste, nutrition, service and sanitation"* | Military food competitions exist, but they reward the **cooks**, not the diners. No precedent found for rewarding *diners* for accurate headcounts | [army.mil](https://www.army.mil/article/103354/best_in_army_food_service_honored) `[cited]` |
| US Army Fort Jackson: overproduction = 83% of waste; unit no-shows named as a cause | The behaviour being rewarded is the documented root cause elsewhere | [EPA 2019](https://cfpub.epa.gov/si/si_public_record_report.cfm?dirEntryId=346767&Lab=NRMRL) `[cited]` |
| **Searched, not found:** any SAF/MINDEF scheme giving units a meal reward for participation | **Do not claim one.** Say "novel, built on existing festive-meal capability" | — |

---

## 6. Measuring retention

Anonymity means **no individual retention is measurable**, by design. Every metric below comes
from `stopPoll` counts plus the two keypad numbers `meals.csv` already logs.

| Metric | Definition | SaaS analogue | Target / read |
|---|---|---|---|
| **Reply rate** `R` | `(eat + notc) / strength`, per unit per lunch | DAU / eligible users | The headline. Compare pre-prize with post-prize weeks |
| **Silent share** | `1 − R` | Churned-today | Must fall. This is what pads the cook number |
| **Not-eating share** | `notc / (eat + notc)` | — | Should **rise** from near zero. Evidence that people now decline honestly instead of going silent `[ASSUMED]` |
| **Goal-Day rate** | Goal Days / lunches held, per unit per month | Weekly-active % | ≥ 75% qualifies |
| **Unit retention (monthly bracket)** | % of units live in month 1 that still have ≥ 15 Goal Days in month *m* | Amplitude bracket retention, cohort = unit's first month | Look for the curve to **flatten** rather than decay to zero |
| **Phantom eaters** | `max(0, Σ eat − taken)`, cookhouse-wide | Fraud rate | Should be ~0. A rise means the prize is buying fake Eatings |
| **Outcome** | portions not cooked vs "silent = eating"; `buffer_pct` | Revenue | What the prize is for |

**On the slide:** one chart. Reply rate by lunch, one line per unit (or the trial group), a
vertical line at "prize announced", and a shaded pre-period. Under it, one line each: silent share
before → after, Not-eating share before → after, phantom eaters. **Label n and the number of
lunches on the chart itself.**

---

## 7. Cheap test before 1 Oct (~10 people, S$0)

Five weekday lunches remain: Thu 24, Fri 25, Mon 28, Tue 29, Wed 30 Sep. That is not a month, so
**compress the month into a week** and test the parts that can be tested.

| # | Test | How | Yields | Honest ceiling |
|---|---|---|---|---|
| **P1** | Reply rate, plain vs prize-framed | Thu–Fri: plain poll. Mon–Wed: poll with bar + goal + nudge + scorecard, "Goal = 8 of 10, **3 Goal Days of 3 earns the group's pick of Friday's lunch spot**" | `R`, silent share, Not-eating share per lunch | 2 vs 3 lunches, one group, novelty confounded. **Direction only** |
| **P2** | Does `getUpdates` return live poll counts? | One call at 09:45 on day 1 | Whether §2.2's conditional nudge is buildable | Binary. Answers the `[ASSUMED]` in §2.2 |
| **P3** | Think-aloud, 3 NSFs, on §2 mock-ups | *"Would you tap Eating falsely to hit the goal? Would your sergeant tell you to? Is 17-with-2-free motivating or silly? Threshold or single winner?"* | Whether Rule 1 and the threshold read the way §4 assumes | n = 3, qualitative |
| **P4** | Anonymous exit polls in the trial group | (a) Threshold vs single-winner, which makes you reply more? (b) Western / mala / other: which special would you work for? (c) Could the board be used against your unit? yes/no/unsure | Counts only. Same privacy design as the product | Self-report |

**The prize in the trial must cost S$0.** Spending is gated: Jamie requires approval *before*
any purchase (`CLAUDE.md`). The group picking where it eats on Friday, each paying their own, is
free and still a real, wanted reward. Every P3 participant goes in the People Log.

**What can go on the slide:** *"In a 5-lunch trial with N people, reply rate was A% on 2 plain
lunches and B% on 3 lunches with the month bar and prize. Silent share fell from X to Y. Phantom
Eatings: Z."* **Do not claim** a retention effect. Five lunches cannot show retention. Claim the
**design**, with its evidence and the self-funding arithmetic, and name the one-month pilot as the
scale-up step.

---

## 8. What changes elsewhere (not edited, noted for Raghav)

- `11-chope-gamification-research.md` §0, §2.1 and §4 item 5 ("no tangible rewards") are
  **superseded by this file**. Its anonymity table (§1.1), its norm evidence (§2.2) and "print who
  replied, never who didn't" all still hold.
- `11` §2.2 sets the goal at "recent median plus a little". For the **prize** goal that invites
  sandbagging, so use a fixed % of strength (§4.3).
- Multi-unit Chope (one poll per unit, summed for the kitchen) is a code change and is not
  written. `chope.py` today is one chat, one pan.

---

## 9. Questions for the cookhouse, before the pitch claims any of this

| # | Question | Blocks |
|---|---|---|
| Q1 | **Who approves an off-menu special lunch:** the caterer's site manager (SFIM/Foodfare), the camp's food/S4 branch, or both? What lead time? | Whether the prize exists |
| Q2 | Can the prize **re-use an existing special slot** (festive meal, brand-collab day), with qualifying units choosing its menu? | The zero-cost version of the prize |
| Q3 | What does a Western set cost over a normal lunch, **in ingredients**, per portion? What does a normal lunch cost? | §3 arithmetic, currently `[ASSUMED]` |
| Q4 | Is the caterer paid per meal **scanned**, **indented** or **cooked**? (`CLAUDE.md` §8) | Who keeps the saving, and so who funds the special |
| Q5 | **How many units** eat at SBAB's cookhouse, how big is each, and do they eat in separate sittings or lines? | The cross-unit board. Whether leftovers could ever be per unit |
| Q6 | Must the special have halal / vegetarian / allergy variants? Does the nutritionist need to sign it off? | Menu-vote options |
| Q7 | Could the kitchen serve the special to *some* units on a day and the normal menu to others? Or must it be cookhouse-wide? | Whether a threshold prize is operable. If it must be cookhouse-wide, the rule becomes "the special happens when ≥ N units qualify" |
| Q8 | Will the unit's food IC make the bot a group admin? | §2.4 pinned bar (optional) |

---

## 10. Sources

| # | Source | URL |
|---|---|---|
| 1 | Telegram Bot API 10.3 (24 Aug 2026): sendPoll (`description`, `allows_revoting`, `allow_adding_options`, `open_period`), Update.poll, stopPoll, pinChatMessage, editMessageText, sendPhoto, sendMessage `disable_notification`, MessageReactionUpdated | https://core.telegram.org/bots/api |
| 2 | Telegram Bot FAQ: group rate limit | https://core.telegram.org/bots/faq |
| 3 | Eyal, Hooked model | https://www.nirandfar.com/how-to-manufacture-desire/ |
| 4 | Eyal, variable rewards (tribe, hunt, self) | https://www.nirandfar.com/want-to-hook-your-users-drive-them-crazy/ |
| 5 | Fogg Behavior Model | https://www.behaviormodel.org/ |
| 6 | Kivetz, Urminsky & Zheng 2006, JMR 43:39–58 | https://home.uchicago.edu/ourminsky/Goal-Gradient_Illusionary_Goal_Progress.pdf |
| 7 | Nunes & Drèze 2006, JCR 32(4):504–512 | https://academic.oup.com/jcr/article-abstract/32/4/504/1787425 |
| 7b | Endowed-progress figures (34% vs 19%), secondary | https://loyaltyrewardco.com/loyalty-psychology-series-endowed-progress-effect/ |
| 8 | Dai, Milkman & Riis 2014, Management Science | https://faculty.wharton.upenn.edu/wp-content/uploads/2014/06/Dai_Fresh_Start_2014_Mgmt_Sci.pdf |
| 9 | Silverman & Barasch 2023, JCR 49(6):1095–1117 | https://academic.oup.com/jcr/article-abstract/49/6/1095/6623414 |
| 10 | Duolingo, how the streak builds habit (Freeze +0.38% DAU; 7-day 3.6×) | https://blog.duolingo.com/how-duolingo-streak-builds-habit |
| 11 | Duolingo, leagues and leaderboards | https://blog.duolingo.com/duolingo-leagues-leaderboards/ |
| 12 | Yancey & Settles 2020, KDD, sleeping recovering bandit | https://research.duolingo.com/papers/yancey.kdd20.pdf |
| 13 | Strava Help, Group Challenges | https://support.strava.com/en-us/articles/15401736-group-challenges |
| 14 | Strava Help, Clubs | https://support.strava.com/en-us/articles/15402172-clubs-on-strava |
| 15 | Amplitude Docs, interpret retention analysis | https://amplitude.com/docs/analytics/charts/retention-analysis/retention-analysis-interpret |
| 16 | Bandiera, Barankay & Rasul 2013, JEEA 11(5):1079 | https://academic.oup.com/jeea/article/11/5/1079/2315903 |
| 17 | Casas-Arce & Martínez-Jerez 2009, Management Science | https://pubsonline.informs.org/doi/10.1287/mnsc.1090.1021 |
| 18 | Barrish, Saunders & Wolf 1969, JABA 2:119–124 | https://onlinelibrary.wiley.com/doi/abs/10.1901/jaba.1969.2-119 |
| 18b | Good Behavior Game, "both teams share", secondary | https://en.wikipedia.org/wiki/Good_Behavior_Game |
| 19 | Deci, Koestner & Ryan 1999, Psych Bull 125:627 | https://doi.org/10.1037/0033-2909.125.6.627 |
| 20 | Deci, Koestner & Ryan 2001, summary incl. uninteresting-task result | https://www.selfdeterminationtheory.org/SDT/documents/2001_DeciKoestnerRyan.pdf |
| 21 | PIONEER, SAF cookhouses, 13 Sep 2024 | https://defencepioneer.sg/pioneer-articles/13sep24_news1 |
| 22 | MINDEF, cookhouse meals carefully planned, 1 Feb 2018 | https://www.mindef.gov.sg/news-and-events/latest-releases/01feb18_fr/ |
| 23 | MINDEF, NSF meal allowances PQ, 6 May 2026 | https://www.mindef.gov.sg/news-and-events/latest-releases/6may26-pq3/ |
| 24 | MINDEF, SAF Best Unit Competition, 28 Jun 2026 | https://www.mindef.gov.sg/news-and-events/latest-releases/28jun26-nr/ |
| 25 | army.mil, Connelly Award | https://www.army.mil/article/103354/best_in_army_food_service_honored |
| 26 | EPA 2019, Fort Jackson, EPA/600/R-19/095 | https://cfpub.epa.gov/si/si_public_record_report.cfm?dirEntryId=346767&Lab=NRMRL |
| 27 | HardwareZone forum, SAF meal cost claims `[weak]` | https://forums.hardwarezone.com.sg/national-service-knowledge-base-162/does-saf-meal-cost-%246-each-how-come-caterer-like-lee-garden-dont-bid-4974611.html |
| — | Erev 1993, Cialdini 2003, Kleingeld 2011, Allcott & Rogers 2014: cited in `11-chope-gamification-research.md` §6 | see that file |
