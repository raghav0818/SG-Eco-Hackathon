# Chope — gamification research

> **Why this file exists.** Mentor feedback: *"for Chope, do consider to look into 'gamification'
> for the army personnel's as you are targeting the behavioural changes."*
>
> **Written 23 Sep 2026, against primary sources.** Provenance tags: `[cited]` public source (URL
> inline and in §9) · `[T1]` Raghav's own service · `[T2]` senior's interview, 4 Sep · `[T5]` Raghav,
> 20 Sep · `[ASSUMED]` needs fieldwork · `[DERIVED]` follows from the above. Where evidence is weak,
> this file says so.
>
> **What this does not change.** `00-master-plan.md` §6 rules out *"a gamified app / leaderboard /
> points"*, and that still holds. Nothing here is a points system. Everything below is **collective
> feedback plus a group goal**, sent through the poll and message Chope already posts. §5.6 of the
> same file already found that this is the mechanism that works.

---

## 0. TL;DR — the decision

**The behaviour to change is one thing: replying honestly instead of staying silent.** Silence is
counted as eating `[T1]`, and that padding is where the waste starts. Chope should not reward
eating less, finishing the plate, or tapping more often. It rewards the **unit** for giving the
kitchen a true number, and it shows the unit what that number caused.

**Gamify the unit, never the person.** Telegram's servers make the poll anonymous, so no user id
ever reaches the Pi. Every individual mechanic (points, streaks, badges, personal leaderboards)
needs `from.id`, and adding one would turn the privacy claim back into a promise about our code
(§1). Nothing in the evidence justifies that trade.

**One rule decides the design: score what the unit controls, show what it causes.** The unit
controls its reply rate, so that is the goal and the only thing that earns a ✅. The unit does not
control the leftovers (the kitchen buffer and the menu drive them), so leftovers are shown as a
consequence and never scored. This follows feedback-intervention theory, which finds that
feedback works when it points at the task and fails when it points at the self (Kluger & DeNisi 1996).

### Ranked mechanics

| # | Mechanic | Telegram mechanism | Evidence | Failure mode | For 2 Oct? |
|---|---|---|---|---|---|
| **1** | **After-service unit scorecard.** Plates that came back (consequence), the reply-goal result (the score) and a "promises kept" check (honesty) | The existing `sendMessage` after `key N`. Text only | Collective feedback + positive feedback (Petersen 2007; Deci 1999 d=+0.33); **Half B made visible** | Leftovers credited to or blamed on the unit, though the kitchen drives them → **so they are never scored** | **Ship** |
| **2** | **The poll carries yesterday's consequence and today's goal.** The poll's `description` holds one line: *"Yesterday 9 plates came back. Silent = cooked for. Goal: 70 replies by 10:30."* | `sendPoll(description=…)`, 0–1024 chars `[cited]`. The only text the **silent** see before cutoff | Specific group goals d=0.56–0.80 (Kleingeld 2011); descriptive norms (Schultz 2007; Nolan 2008) | Stated as "only 31 replied" it becomes a destructive norm (Cialdini 2003) → **print the count who replied, never the count who stayed silent** | **Ship** |
| **3** | **A rolling week record, not a streak.** "4 of 5 lunches hit the goal", plus a Friday recap: portions *not* cooked compared with the everyone-counted rule | `sendMessage` from Friday's `key N` | Intact streaks raise engagement, and a broken streak costs more than a rolling count (Silverman & Barasch 2023) | Weekly recaps fade (novelty, Koivisto & Hamari 2014) → one message a week, no badges | **Ship** |
| **4** | **Friday anonymous quiz.** *"How many plates came back this week?"* Four ranges, confetti on the right answer | `sendPoll(type="quiz", is_anonymous=True, correct_option_ids=[k], explanation=…)` `[cited]` | Makes Half B salient in a playful form. **Weakest evidence here**: nothing measures quiz-poll effects on behaviour | Clutter in a unit chat, and it decays fast → **weekly at most. Drop it if the survey says mute** | Optional |
| **5** | **Platoon vs platoon** on how often each hits its reply goal. One anonymous poll per platoon group, summed for the kitchen | N × `sendPoll`. Code change | Intergroup competition removed a 30% free-rider loss (Erev 1993) and raised intrinsic motivation (Tauer & Harackiewicz 2004) | Gives the chain of command a ranking, which Campbell's law predicts will turn into pressure to fake-tap → **same-company only, rolling weeks, never passed upward** | **Scale-up slide only** |

Cost of 1–3: text changes to two `sendMessage` strings plus one `sendPoll` kwarg. There is no new
state beyond counts Chope already logs in `meals.csv`, **and no identifier anywhere.**

---

## 1. The anonymity constraint, and why individual gamification is rejected

### 1.1 What Telegram actually exposes (Bot API 10.3, 24 Aug 2026 — [core.telegram.org/bots/api](https://core.telegram.org/bots/api)) `[cited]`

| Surface | What the bot receives | Individual state possible? |
|---|---|---|
| `sendPoll`, `is_anonymous` | *"True, if the poll needs to be anonymous, defaults to True"* | — |
| `poll_answer` update / `PollAnswer` | *"A user changed their answer in a **non-anonymous** poll"* — never fired for anonymous polls | **No** (anonymous) |
| `stopPoll` | *"On success, the stopped Poll is returned"*: `total_voter_count` plus `voter_count` per option | **No.** Counts only |
| MTProto `messages.getPollVotes` | *"can be used to get poll results for **non-anonymous** polls"* ([core.telegram.org/api/poll](https://core.telegram.org/api/poll)) | **No** (anonymous) |
| Inline keyboard → `callback_query` | Every tap carries `from: User` | Yes. **This is why the keyboard version was cut** (`08-chope-prd.md`) |
| Games (`sendGame`, `setGameScore`) | The Play button yields a `CallbackQuery`. `setGameScore` **requires `user_id`**: *"set the score of the specified user"* | Yes, and **only** per user. **Unusable** |
| Reactions (`message_reaction`) | `MessageReactionUpdated.user`: *"The user that changed the reaction"*. The bot must be **admin** | Yes. **Unusable** as an input |
| `message_reaction_count` | Anonymous counts, but *"only for messages with anonymous reactions"*, bot must be admin, and it needs an update loop Chope does not have | Moot |
| `sendMessage`, `sendPhoto`, `sendPoll(type="quiz")` | Outbound only | **Safe.** Everything recommended here uses these |

**So every mechanic in the TL;DR is outbound-only and aggregate.** The Pi never receives anything
it does not already receive today, which is three integers from `stopPoll`.

### 1.2 Why breaking anonymity is not worth it

**What it would buy:** personal streaks, badges and nudges for non-repliers. All of that is Half A,
the indent-easing half that the senior's critique already dismisses `[T2]`, and `08-chope-prd.md`
already accepted losing *"Same as last week"* for the same reason.

**What it would cost, with evidence:**

1. **Honest "Not eating" is the signal, and anonymity is what produces honesty.** Units are told to
   scan whether or not they eat `[T1]`, so the local norm treats declining as a deviation. When
   answers are anonymous rather than merely confidential, people report sensitive behaviour far
   more truthfully: 74% vs 25% of known cheaters admitted it (Ong & Weiss 2000, [Wiley](https://onlinelibrary.wiley.com/doi/abs/10.1111/j.1559-1816.2000.tb02462.x)) `[cited]`. A "Not
   eating" linked to a name is a tap a sergeant can see, and the silence that pads the number
   comes back `[DERIVED]`.
2. **Monitoring does not raise performance, and it does raise stress.** 94 samples, N=23,461: *"no
   evidence that EPM improves worker performance … associated with increased worker stress,
   regardless of the characteristics of monitoring"* (Ravid et al. 2023, [Personnel Psychology](https://onlinelibrary.wiley.com/doi/abs/10.1111/peps.12514)) `[cited]`.
   A second meta-analysis (70 samples) found performance r=−0.01, satisfaction r=−0.10, stress
   r=+0.11 and counterproductive behaviour r=+0.09 (Siegel, König & Lazar 2022, [CHB Reports](https://www.sciencedirect.com/science/article/pii/S2451958822000616)) `[cited]`.
   These are workplace samples, not conscripts. Treating them as transferable is `[ASSUMED]`, but
   nothing suggests conscripts would react *better* to being watched.
3. **Individual leaderboards and badges can lower motivation.** In a 16-week classroom study, the
   gamified section with a leaderboard and badges ended with *less* intrinsic motivation,
   satisfaction and empowerment, and lower exam scores (Hanus & Fox 2015, [C&E](https://dl.acm.org/doi/10.1016/j.compedu.2014.08.019)) `[cited]`.
4. **Per-person state would be personal data.** Today's claim is: *"No personal data is collected at all,
   so neither the PSGA framework nor IM8's personal-data provisions have anything to bite on"*
   (`08-chope-prd.md`). A salted hash does not rescue it, because 90 ids can be enumerated in a
   second (PDPC *Guide to Basic Anonymisation*, already cited in the PRD).
5. **The chain-of-command risk.** Anything that names people can be used to punish them. The
   existing tally rule already reports units that fall short `[T1]`, and proxy scanning is the
   rational workaround `[T2]`. A per-person Chope record would become a second tally, and Campbell's
   law predicts what happens next: *"the more any quantitative social indicator is used for social
   decision-making, the more subject it will be to corruption pressures"* (Campbell 1979, [EPP](https://doi.org/10.1016/0149-7189(79)90048-X)) `[cited]`.

**Verdict: rejected.** Individual gamification would buy a small and unstable behavioural effect
(§2.1: g=0.25 for behaviour, *"less stable"* under rigorous designs). It would cost the honesty of
the only input the forecast runs on.

---

## 2. Evidence review

### 2.1 Q1 — Does gamification work? What are the failure modes?

| Claim | Source | Tag |
|---|---|---|
| A review of 24 empirical studies found positive effects that are *"greatly dependent on the context … as well as on the users"* | Hamari, Koivisto & Sarsa 2014, [HICSS](https://dl.acm.org/doi/10.1109/HICSS.2014.377) | `[cited]` |
| A review of 819 studies found results *"lean towards positive"*, but *"the amount of mixed results is remarkable"*. Points, badges and leaderboards dominate | Koivisto & Hamari 2019, [IJIM](https://www.sciencedirect.com/science/article/pii/S0268401217305169) | `[cited]` |
| Meta-analysis: cognitive g=0.49, motivational g=0.36, **behavioural g=0.25 (k=9)**. Motivational and behavioural effects were *"less stable"* in rigorous studies. **Competition combined with collaboration** was a significant positive moderator for behaviour | Sailer & Homner 2020, [Educ Psychol Rev](https://link.springer.com/article/10.1007/s10648-019-09498-w) | `[cited]` |
| Overjustification: tangible and expected rewards undermine intrinsic motivation (d=−0.28 to −0.40). **Positive feedback enhances it (d=+0.33 free-choice, +0.31 interest)** | Deci, Koestner & Ryan 1999, [Psych Bull](https://doi.org/10.1037/0033-2909.125.6.627) | `[cited]` |
| Novelty: perceived enjoyment and usefulness of gamification **decline with use** | Koivisto & Hamari 2014, [CHB](http://www.creativegames.org.uk/modules/Gamification/Koivisto_et_Hamari-Demographic_differences_in_perceived%20benefits_from_gamification-2014.pdf) | `[cited]` |
| Leaderboards act like difficult goals. They work when people are committed to the goal | Landers, Bauer & Callan 2017, [CHB](https://www.sciencedirect.com/science/article/abs/pii/S0747563215300868) | `[cited]` |
| Feedback improves performance on average (d=0.41), but **more than a third of interventions made performance worse**. Effectiveness falls as attention moves from the task toward the self | Kluger & DeNisi 1996, [Psych Bull](https://doi.org/10.1037/0033-2909.119.2.254) | `[cited]` |

**What this means for Chope:** do not add rewards. The Deci result is the one to design on:
**informational positive feedback raises motivation, and expected tangible rewards lower it.**
The scorecard is informational feedback. A free drink for the best platoon would be an expected
tangible reward. Expect decay (Koivisto & Hamari 2014), so the scale-up claim cannot be "this lasts".

### 2.2 Q2 — Collective feedback, social norms, group goals, intergroup competition

| Claim | Source | Tag |
|---|---|---|
| Showing households the neighbourhood average made high users cut consumption, but **low users increased it (the boomerang effect)**. Adding an injunctive ☺/☹ removed the boomerang | Schultz et al. 2007, [Psych Sci](https://journals.sagepub.com/doi/10.1111/j.1467-9280.2007.01917.x) | `[cited]` |
| Descriptive norms changed behaviour the most of all message types, although **people rated them the least motivating**. Self-report will therefore understate the effect | Nolan et al. 2008, [PSPB](https://journals.sagepub.com/doi/10.1177/0146167208316691) | `[cited]` |
| A descriptive norm about an *undesired* behaviour ("many visitors take wood") **increased** theft to 7.92%. The injunctive sign held it at 1.67% | Cialdini 2003, [CDPS](https://journals.sagepub.com/doi/10.1111/1467-8721.01242) | `[cited]` |
| Opower, 600,000 households: **−2.0% on average**, equivalent to an 11–20% price rise. The top decile cut 6.3% and the bottom decile 0.3%. **The injunctive ☺ categories "played an insignificant role"** | Allcott 2011, [JPubE](https://eml.berkeley.edu/~saez/course131/allcott2011.pdf) | `[cited]` |
| Repeated reports produce *"action and backsliding"* that attenuates over time. Effects decay 10–20% a year once reports stop, and people keep responding after two years | Allcott & Rogers 2014, [AER](https://www.aeaweb.org/articles?id=10.1257%2Faer.104.10.3003) | `[cited]` |
| Group goals: overall d=0.56. **Specific, difficult group goals d=0.80** against nonspecific ones. 49 effect sizes, 739 groups | Kleingeld, van Mierlo & Arends 2011, [JAP](https://pubmed.ncbi.nlm.nih.gov/21744940/) | `[cited]` |
| Dorm competition over two weeks: real-time feedback **−55%**, weekly feedback −31%, −32% overall in electricity. Short, and paired with incentives | Petersen et al. 2007, [IJSHE](https://www.emerald.com/insight/content/doi/10.1108/14676370710717562/full/html) | `[cited]` |
| Field experiment: a collective reward cost **30%** of output through free-riding. **Intergroup competition eliminated the loss**, and it worked better the more similar the teams were | Erev, Bornstein & Galili 1993, [JESP](https://www.sciencedirect.com/science/article/abs/pii/S0022103183710218) | `[cited]` |
| Competition between groups (cooperation inside the group, competition between groups) raised intrinsic motivation more than pure competition or pure cooperation did | Tauer & Harackiewicz 2004, [JPSP](https://pubmed.ncbi.nlm.nih.gov/15149259/) | `[cited]` |

**What this means for Chope:**
- The reply goal must be **specific and slightly hard**: *"70 of 90 by 10:30"*, not *"please reply"*
  (Kleingeld). Set it at the unit's recent median plus a little `[ASSUMED]`. The number is a
  judgement call that needs a week of data.
- **Never publish the prevalence of silence.** "Only 31 replied" is the Petrified Forest sign.
  Publish the count who did reply, against the goal (Cialdini 2003).
- **Add the ✅/❌ against the goal, but do not rely on it.** Schultz found the injunctive marker
  fixed the boomerang effect. Allcott found it did not matter at scale. The evidence is mixed. It
  costs one character, so keep it and do not claim it works.
- Expect the effect to be **small and decaying**. Opower's 2% came from 600k households with
  months of data. Chope has ~90 people and a week.

### 2.3 Q3 — Food-waste and military dining evidence

| Claim | Source | Tag |
|---|---|---|
| US Army Fort Jackson DFACs: *"Overproduction was by far the primary reason (83%) for waste."* One cause named: *"a unit is scheduled to have a meal at a DFAC but does not show up due to training requirements."* Recommendation: *"increased communication with training staff regarding the timing of field exercises"* | EPA/600/R-19/095, Sep 2019, [EPA](https://cfpub.epa.gov/si/si_public_record_report.cfm?dirEntryId=346767&Lab=NRMRL) | `[cited]` |
| The same study found staff *cooked extra on food-bank collection days*, because they knew it would be donated. Measurement exposed it and management corrected it. **The kitchen buffer responds to incentives, and making it visible changed it** | same | `[cited]` |
| Buffet sign "you may help yourself more than once": **−20.5%** plate waste. Smaller plates: −19.5% | Kallbekken & Sælen 2013, [Econ Letters](https://www.sciencedirect.com/science/article/abs/pii/S0165176513001286) | `[cited]`. Plate waste, **not** our waste type |
| Informational interventions alone are ineffective against consumer food waste | Stöckli, Niklaus & Dorn 2018, [RCR](https://www.sciencedirect.com/science/article/abs/pii/S0921344918301307) | `[cited]` |
| UK hospitality: 920kt/yr. 45% preparation, 21% spoilage, 34% plate | WRAP 2013, [WRAP](https://www.wrap.ngo/resources/report/overview-waste-hospitality-and-food-service-sector) | `[cited]` |
| Pre-ordering in a university canteen, 946 students over 3 years (adoption and planning behaviour) | Migliavada, Ricci & Torri 2021, [Appetite](https://www.semanticscholar.org/paper/A-three-year-longitudinal-study-on-the-use-of-in-a-Migliavada-Ricci/3236da92a2a59f456b9c7c705fded6ac156b94b7) | `[cited]`, abstract only. **Effect on waste not verified** |
| SAF: weekly forecasts, electronic meal accounting, **~1%** waste | [MINDEF PQ, 3 Feb 2020](https://www.mindef.gov.sg/news-and-events/latest-releases/03feb20_pq/) | `[cited]` |
| SAF Sustainability Office set up in 2021. Smart-meter dashboards let unit commanders *"view consumption patterns in one single picture and identify anomalies"* and compare units, **for water and electricity** | [MINDEF fact sheet, 2 Mar 2022](https://www.mindef.gov.sg/news-and-events/latest-releases/02mar22_fs4/) | `[cited]` |
| NEA *Love Your Food @ Schools* (2017–19): clean-plate photo activity, food-waste digesters | [NEA](https://www.nea.gov.sg/media/news/news/index/nea-launches-love-your-food-@-schools-project-to-encourage-youth-to-cherish-and-not-waste-food) | `[cited]`. No outcome data found |
| **No SAF food-waste gamification campaign found.** Searched MINDEF and PIONEER | — | Searched, not found. **Do not claim one** |

**What this means for Chope:**
- **Fort Jackson is the strongest single citation for Chope, and it is not about gamification.**
  An army dining facility's waste was 83% overproduction, driven partly by units not telling the
  kitchen they would be absent. That is the silent-NSF problem in a different army.
- Stöckli is the reason the scorecard cannot be data alone. It has to carry a **goal**
  (mechanic 2) and a **norm** (mechanics 1 and 3).
- The MINDEF dashboard shows that **unit-vs-unit comparison is already an SAF practice**. It also
  shows the danger: that comparison is built for commanders to find "anomalies". Mechanic 5 must not become that.

### 2.4 Q4 — Military / NS context

| Claim | Source | Tag |
|---|---|---|
| The Best Unit Competition has run since 1969 and **Best NS Unit** since 1993. It recognises *"combat readiness, operational proficiency, and administrative excellence."* **No sustainability or food criterion** | [MINDEF, 28 Jun 2026](https://www.mindef.gov.sg/news-and-events/latest-releases/28jun26-nr/) | `[cited]` |
| Cohesion and performance: a small effect. It is stronger in **small, real** groups and **driven by commitment to the task, not by group pride**. The causal path may run performance → cohesion | Mullen & Copper 1994, [Psych Bull](https://doi.org/10.1037/0033-2909.115.2.210) | `[cited]` |
| Military cohesion = primary (peer and leader) bonding + secondary (institutional) bonding | Siebold 2007, [AF&S](https://journals.sagepub.com/doi/10.1177/0095327X06294173) | `[cited]` |
| Units are reported when the tally does not match. People are told to scan whether or not they eat | Raghav's service | `[T1]` |
| Proxy scanning happens, and out-ration reclassification makes the numbers tally | Senior's interview | `[T2]` |
| NSFs resent extra admin. Anything the chain of command can see gets used for accountability | — | `[ASSUMED]`, consistent with [T1]/[T2]. **Test it (§5)** |

**What this means for Chope:** unit identity and inter-unit competition are native to SAF culture,
so a platoon-level frame will not feel foreign `[ASSUMED]`. Mullen & Copper argue for making the
**task** (feed the kitchen a true number) the object of pride, not the platoon name. The tally rule
`[T1]` is the warning: the SAF's existing count already turned into a compliance game. **Chope's
output must never become an input to that rule.** The scorecard stays inside the unit's own chat.

### 2.5 Q5 — What Telegram permits (Bot API 10.3) `[cited]`

| Feature | Exact behaviour | Use in Chope |
|---|---|---|
| `sendPoll.description` | *"Description of the poll to be sent, 0-1024 characters"* | **Mechanic 2.** One kwarg in `cmd_open()` |
| `sendPoll.type="quiz"` + `correct_option_ids` + `explanation` | *"required for polls in quiz mode"*. Explanation 0–200 chars. Confetti on a correct answer ([Telegram blog](https://telegram.org/blog/polls-2-0-vmq)) | **Mechanic 4** |
| `allows_revoting` | *"defaults to False for quizzes and to True for regular polls"* | People can already change "Eating" to "Not eating" if plans change. **Say so in the description** |
| `hide_results_until_closes` | *"results must be shown only after the poll closes"* | **Leave off.** A replier seeing the running tally is a live descriptive norm |
| `open_period` / `close_date` | **Now 5–2,628,000 s** (~30 days) | **Correction:** `08-chope-prd.md` says 5–600 s, which is stale. Cron `stopPoll` stays anyway: with no update loop, it is the only way the counts reach the Pi. The quiz can use `open_period` because nobody needs its results |
| `pinChatMessage` | Bot must be admin with `can_pin_messages` | **Skip.** It is a permission request for a nice-to-have |
| `setMessageReaction` | Bot can set one reaction per message | A bot 🔥 on a goal-hit day is harmless and adds nothing. Skip |
| `members_only` | *"for channel chats only"* | Not available in groups |
| `sendPhoto` | Can post a generated chart | Skip. Text renders on every phone and needs no image library on the Pi |

### 2.6 Q6 — Reward accuracy, not volume

**The trap:** a goal on reply *count* alone invites anyone near the goal to tap something. A false
**"Eating"** is the dangerous tap, because it raises `confirmed`, and `confirmed ≤ COOK` is a hard
floor. So a fake "Eating" vote buys a portion that will be binned. A false "Not eating" is caught
downstream as a stock-out, and `slack` adapts.

**What already protects the vote** `[cited]`: Telegram allows one vote per account, server-side,
and only group members can vote. So the ceiling on fake volume is **the number of members in the
chat**, which `getChatMemberCount` already reads as strength.

**What the scorecard adds, with no identity:** a **promises-kept check**. `taken = actual − left`
counts plates that actually left the shelf. If `taken < eat`, then **at least `eat − taken`
people who said "Eating" did not eat**. That is a hard lower bound computed from aggregates.
It is weak: silent eaters also take plates and hide no-shows, so it will rarely fire `[DERIVED]`.
It is still the right thing to display, because it makes the scored behaviour an **accurate**
reply and not just a reply. **The goal is framed as "replied", and the check is framed as "said
eating = came to eat".**

---

## 3. Mock-ups — the actual messages

All figures illustrate a 90-strong unit. They are **not** trial data.

### 3.1 Mechanic 2 — the morning poll (`cmd_open`)

```
📊 Lunch today?                                   [anonymous poll]
   ○ Eating
   ○ Not eating

   Yesterday 9 plates came back uneaten.
   Silent = cooked for. Plans change? Tap again before 10:30.
   Unit goal: 70 replies by 10:30  (this week: ✅ ✅ ❌ ✅)
```

### 3.2 Mechanic 1 — after service (replaces the current `cmd_left` text)

```
🍛 LUNCH · Thu 26 Sep
Came back uneaten:   9 plates   (your usual: 14)

Replied by 10:30:    74 / 90    goal 70 ✅
Said eating 58 · plates taken 81 · promises kept ✓

72% of the silent ate today — so every silent tap
is still a plate cooked for you.
```

The line *"72% of the silent ate"* is `r`, already in the current message. It is the norm that
tells a silent person they are being cooked for.

**Change to the current message, recommended:** drop `kitchen cooked %d (+%d%%)` from the **group**
text. Keep it in `meals.csv`. Posting the kitchen's buffer into ninety NSFs' chat points at
the kitchen, which is the one audience `00-master-plan.md` §4.1 says the intervention must not
read as a management tool against. The buffer evidence is for the kitchen and the scale-up slide.

### 3.3 Mechanic 3 — Friday recap (appended to Friday's after-service message)

```
📅 WEEK 39 · your unit
Goal hit: 4 of 5 lunches
Came back uneaten this week: 46 plates
Not cooked vs. "silent counts as eating": 38 portions
Next week's goal: 72 replies by 10:30
```

*"Not cooked vs. silent counts as eating"* is `Σ(strength − board)`. It is the counterfactual of
the current rule, and it assumes today's indent equals strength `[ASSUMED]`. Label it that way on
any slide.

### 3.4 Mechanic 4 — Friday quiz (optional, 30 min after the recap)

```
❓ How many plates came back uneaten this week?     [anonymous quiz]
   ○ Under 20     ○ 20–40     ● 40–60     ○ Over 60
💡 46 — about half a platoon's lunch. Tap Not eating when you're out.
```

### 3.5 Mechanic 5 — platoon vs platoon (scale-up slide, not built)

```
🏁 ALPHA COY · weeks the reply goal was hit (last 4)
   P1 ████ 4    P2 ███░ 3    P3 ███░ 3
```

Rolling, same company, similar-sized platoons (Erev 1993). **Shows goal hits, never leftovers**:
the pan is shared, so leftovers cannot be attributed to a platoon.

---

## 4. What not to do

1. **No individual anything.** No points, streaks, badges, personal leaderboards, "@name didn't
   reply" or DM nudges. Each one needs `from.id` (§1.1).
2. **No non-anonymous polls, inline keyboards, Games or reaction-reading.** They are the four ways
   an identity reaches the bot.
3. **Never show waste to the kitchen as a score.** The board shows today's number only
   (`10-chope-board-ui-prd.md` §0). **Also remove the kitchen-buffer percentage from the group
   message** (§3.2).
4. **Never score leftovers against the unit.** The unit does not control the buffer or the menu.
   Scoring an outcome people cannot move is the self-focused feedback that Kluger & DeNisi found
   harms performance.
5. **No tangible rewards.** Free drinks, off-days or "best platoon gets…" are expected tangible
   rewards (Deci 1999: undermining). They also pay people to tap "Eating" falsely.
6. **Never publish the prevalence of silence** ("only 31 replied", "59 ignored this"). That is a
   destructive descriptive norm (Cialdini 2003).
7. **Nothing forwarded up the chain.** No weekly report to the OC, no cross-company league and no
   link to the tally reconciliation. Campbell's law, and `[T1]`: the tally is already gamed.
8. **No fragile consecutive streak.** Use "4 of 5", not "🔥 12-day streak" (Silverman & Barasch 2023).
9. **No more than one extra message a week.** It is a unit chat, not our channel.
10. **Do not pitch "gamified Chope".** `00-master-plan.md` §6 still stands. Pitch it as **collective
    feedback with a group goal: Half B, delivered to the people making the declaration.**

---

## 5. What to test before 2 Oct (cheap, one week, ~10 people)

**Only the Telegram half can be tested live.** The trial group has no kitchen, so every "came back"
figure there is a replay number and must say `[demo]` in the message itself.

| Test | How | What it yields | Honest ceiling |
|---|---|---|---|
| **T1 · Reply rate, before vs after** | First 3 lunches: plain poll, as now. Next 4: poll `description` + goal line (mechanic 2) + scorecard with `[demo]` leftovers | Reply rate per lunch (`total_voter_count` / strength) and the share of "Not eating", **with n** | ~10 people, 3 vs 4 lunches, no control, novelty confounded. **A direction, never an effect** |
| **T2 · Surveillance check** | 10-min think-aloud with 3 NSFs on the §3 mock-ups: *"Who can see this? What would your sergeant do with it? Would you tap Not eating?"* | Whether the unit-level framing *reads* as anonymous. Test the `[ASSUMED]` rows in §2.4 | Qualitative, n=3 |
| **T3 · Anonymous exit poll** | Friday, three **anonymous Telegram polls** in the trial group: (a) *Did the after-lunch message change whether you replied?* yes / no / didn't read; (b) *Keep / mute / remove the Friday quiz?*; (c) *Could this be used against your unit?* yes / no / unsure | Counts only. The same privacy design as the product | Self-report understates norm effects (Nolan 2008), so read (a) conservatively |

Each person in T2 goes into the People Log. That counts toward the 10+ requirement.

### What can honestly go on a slide

> *We gamified the unit, not the person. Chope's anonymous poll never sends an identity to our code,
> so every mechanic is collective: a specific reply goal for the group, and a message after lunch
> showing what the group's answers caused. That is Half B, delivered to the people declaring the
> number. In a 7-day trial with N servicemen, the reply rate was A% over 3 plain lunches and B%
> over 4 lunches with the goal and scorecard. The sample is small, there is no control group, and
> this is a direction, not an effect. X of Y said the scorecard changed whether they replied, and
> Z of Y thought it could be used against their unit.*

**Do not claim** that gamification reduced waste, that the ✅ markers work, or that the effect lasts
(Allcott & Rogers: it decays). **Do claim** the design constraint, because it is the strongest
point: every surface where Telegram leaks an identity was mapped (§1.1) and avoided.

---

## 6. Sources

| # | Source | URL |
|---|---|---|
| 1 | Telegram Bot API 10.3 (24 Aug 2026): sendPoll, stopPoll, PollAnswer, Poll, sendGame, setGameScore, setMessageReaction, MessageReactionUpdated, pinChatMessage | https://core.telegram.org/bots/api |
| 2 | Telegram MTProto: polls, `messages.getPollVotes` restricted to non-anonymous polls | https://core.telegram.org/api/poll |
| 3 | Telegram blog, Polls 2.0 (visible votes, quiz mode) | https://telegram.org/blog/polls-2-0-vmq |
| 4 | Hamari, Koivisto & Sarsa 2014, HICSS | https://dl.acm.org/doi/10.1109/HICSS.2014.377 |
| 5 | Koivisto & Hamari 2019, IJIM 45:191–210 | https://www.sciencedirect.com/science/article/pii/S0268401217305169 |
| 6 | Sailer & Homner 2020, Educ Psychol Rev 32:77–112 | https://link.springer.com/article/10.1007/s10648-019-09498-w |
| 7 | Deci, Koestner & Ryan 1999, Psych Bull 125:627–668 | https://doi.org/10.1037/0033-2909.125.6.627 |
| 8 | Koivisto & Hamari 2014, CHB 35:179–188 | http://www.creativegames.org.uk/modules/Gamification/Koivisto_et_Hamari-Demographic_differences_in_perceived%20benefits_from_gamification-2014.pdf |
| 9 | Hanus & Fox 2015, Computers & Education 80:152–161 | https://dl.acm.org/doi/10.1016/j.compedu.2014.08.019 |
| 10 | Landers, Bauer & Callan 2017, CHB 71:508–515 | https://www.sciencedirect.com/science/article/abs/pii/S0747563215300868 |
| 11 | Kluger & DeNisi 1996, Psych Bull 119:254–284 | https://doi.org/10.1037/0033-2909.119.2.254 |
| 12 | Schultz et al. 2007, Psych Sci 18:429–434 | https://journals.sagepub.com/doi/10.1111/j.1467-9280.2007.01917.x |
| 13 | Nolan et al. 2008, PSPB 34:913–923 | https://journals.sagepub.com/doi/10.1177/0146167208316691 |
| 14 | Cialdini 2003, Curr Dir Psych Sci 12:105–109 | https://journals.sagepub.com/doi/10.1111/1467-8721.01242 |
| 15 | Allcott 2011, J Public Econ 95:1082–1095 | https://eml.berkeley.edu/~saez/course131/allcott2011.pdf |
| 16 | Allcott & Rogers 2014, AER 104:3003–3037 | https://www.aeaweb.org/articles?id=10.1257%2Faer.104.10.3003 |
| 17 | Kleingeld, van Mierlo & Arends 2011, JAP 96:1289–1304 | https://pubmed.ncbi.nlm.nih.gov/21744940/ |
| 18 | Petersen et al. 2007, IJSHE 8(1):16–33 | https://www.emerald.com/insight/content/doi/10.1108/14676370710717562/full/html |
| 19 | Erev, Bornstein & Galili 1993, JESP 29:463–478 | https://www.sciencedirect.com/science/article/abs/pii/S0022103183710218 |
| 20 | Tauer & Harackiewicz 2004, JPSP 86:849–861 | https://pubmed.ncbi.nlm.nih.gov/15149259/ |
| 21 | Silverman & Barasch 2023, J Consumer Research 49(6):1095–1117 | https://academic.oup.com/jcr/article-abstract/49/6/1095/6623414 |
| 22 | Ong & Weiss 2000, J Appl Soc Psych 30:1691–1708 | https://onlinelibrary.wiley.com/doi/abs/10.1111/j.1559-1816.2000.tb02462.x |
| 23 | Ravid et al. 2023, Personnel Psychology (EPM meta-analysis) | https://onlinelibrary.wiley.com/doi/abs/10.1111/peps.12514 |
| 24 | Siegel, König & Lazar 2022, CHB Reports 8:100227 | https://www.sciencedirect.com/science/article/pii/S2451958822000616 |
| 25 | Campbell 1979, Evaluation and Program Planning 2:67–90 | https://doi.org/10.1016/0149-7189(79)90048-X |
| 26 | EPA 2019, Food Waste Reduction in Military Kitchens (Fort Jackson), EPA/600/R-19/095 | https://cfpub.epa.gov/si/si_public_record_report.cfm?dirEntryId=346767&Lab=NRMRL |
| 27 | Kallbekken & Sælen 2013, Economics Letters 119:325–327 | https://www.sciencedirect.com/science/article/abs/pii/S0165176513001286 |
| 28 | Stöckli, Niklaus & Dorn 2018, Resour Conserv Recycl 136:445–462 | https://www.sciencedirect.com/science/article/abs/pii/S0921344918301307 |
| 29 | WRAP 2013, Overview of waste in UK hospitality and food service | https://www.wrap.ngo/resources/report/overview-waste-hospitality-and-food-service-sector |
| 30 | Migliavada, Ricci & Torri 2021, Appetite 163 (abstract only) | https://www.semanticscholar.org/paper/A-three-year-longitudinal-study-on-the-use-of-in-a-Migliavada-Ricci/3236da92a2a59f456b9c7c705fded6ac156b94b7 |
| 31 | MINDEF PQ, 3 Feb 2020: meal accounting, ~1% | https://www.mindef.gov.sg/news-and-events/latest-releases/03feb20_pq/ |
| 32 | MINDEF fact sheet, 2 Mar 2022: Go Greener SAF, smart-meter dashboards, SAF Sustainability Office | https://www.mindef.gov.sg/news-and-events/latest-releases/02mar22_fs4/ |
| 33 | MINDEF, 28 Jun 2026: SAF Best Unit Competition | https://www.mindef.gov.sg/news-and-events/latest-releases/28jun26-nr/ |
| 34 | NEA, Love Your Food @ Schools | https://www.nea.gov.sg/media/news/news/index/nea-launches-love-your-food-@-schools-project-to-encourage-youth-to-cherish-and-not-waste-food |
| 35 | Mullen & Copper 1994, Psych Bull 115:210–227 | https://doi.org/10.1037/0033-2909.115.2.210 |
| 36 | Siebold 2007, Armed Forces & Society 33:286–295 | https://journals.sagepub.com/doi/10.1177/0095327X06294173 |
