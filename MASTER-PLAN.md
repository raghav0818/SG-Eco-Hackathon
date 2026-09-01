# SG Eco Loop 2.0 — Master Plan

> **Purpose of this file.** Single source of truth for the project, written to be loaded as context by AI agents. It is heavy on **problem definition and constraints** because those are settled. **Solutions are deliberately left open** — the human is still deciding. Do not collapse the options section into a single recommendation unless asked.
>
> **Rules for any agent reading this:**
> 1. Sections 1–6 are **settled**. Do not relitigate them. In particular, do not re-propose anything in §6 (Ruled Out) — each was killed for a stated reason.
> 2. Section 7 (Solution Candidates) is **open**. Treat entries as options, not decisions.
> 3. Section 10 lists **open questions**. If an answer is needed and not present, say so — do not invent one.
> 4. Facts here are sourced. If you add a claim, cite it or mark it `[UNVERIFIED]`.

**Last updated:** 1 Sep 2026
**Participant:** Raghav (SUTD), competing as an individual
**Programme contact:** Jamie Heng, Programme Manager, SDTA — +65 9019 5694

---

## 1. Programme facts

**SG Eco Loop 2.0** — run by Singapore Deep-Tech Alliance (SDTA). Build a prototype that diverts food or plastic waste from landfill.

### Prizes — 2 × S$1,000

| Prize | Awarded on |
|---|---|
| **Biggest Impact** | Most waste diverted over the programme, in kg. Need not come directly from the prototype. |
| **Best Innovation** | Most innovative prototype, selected by a panel of industry mentors. |

### Judging — 5 criteria, **equally weighted**

1. Problem understanding
2. Originality
3. Feasibility
4. Potential impact
5. Pitch & clarity

> Jamie's explicit warning at kickoff: a team that scores high on one criterion and poorly on the rest loses to a team that is solid on all five. **Do not optimise a single axis.**

### Budget

- **S$200 per prototype.**
- A **second, distinct concept** unlocks another S$200 (total S$400). Distinctness must be agreed with the programme team **in advance** — Jamie asked to be told.

### Dates

| Date | Event |
|---|---|
| 26 Aug 2026 | Online kickoff (done) |
| **5 Sep 2026** | **Hackathon Day 1** — report 08:45, runs 09:00–13:00. Lorong AI @ One-North, 69 Ayer Rajah Cres, Level 3 Vidacity, S139961 |
| 6 Sep 2026 | Hackathon Day 2, 09:00–13:00 |
| Sep 2026 | 2 × mentor check-ins (online or in-person) |
| **1 Oct 2026** | **All deliverables due** |
| **2 Oct 2026** | **Public Showcase**, Temasek Shophouse, 3 hours |

### Deliverables (due 1 Oct)

1. **Prototype** — tested with target users, brought to the showcase.
2. **Scale-Up Plan** — slides, submitted as PDF. Required sections:
   - Problem You Tackled
   - Prototype You Built & Tested
   - Reflections
   - Scaling Up — execution plan, 6-month timeline, stakeholders, budget breakdown
   - *Tips in the brief:* include **photos of the design / build / test process with captions**; the brief states a bias **against obviously AI-generated output**.
3. **Waste Diary** — log every kg diverted, weekly, with a weigh-in **and photo**. Target 20 kg+ per team.
4. **Reimbursement & People Log** — budget claims + everyone engaged. Team-specific Google Sheet.

### Homework due 5 Sep

- A clear **problem statement**: what, how big, who the target user is, who else is involved, why you picked it.
- **2–3 prioritised ideas**, with a rough sense of what each looks like as a working solution.

### Not taken

Industry partner challenge statements from **SUSS**, **Vidacity**, **Kidztropic** were offered as alternatives. **Declined** — pursuing a self-identified problem. (SUSS also offered an optional composting site tour.)

---

## 2. Decisions already made — LOCKED

| Decision | Status |
|---|---|
| **Domain: food waste in SAF cookhouses (army camps)** | Final and non-negotiable. Do not propose alternative domains. |
| **Track: Best Innovation only** | Impact/kg not contested. Waste Diary still filed honestly as a compulsory deliverable — do **not** design around maximising it. |
| **Hardware: Raspberry Pi** | Chosen partly so it is reusable in later personal projects. |
| **Intervention side: consumer, not company** | The user explicitly does not want a kitchen-side / catering-contractor-facing solution. |
| **No camera, no ML vision** | See §4.3 — this is an argument, not a shortcut. |
| **No identity, no accounts, no app, no personal data** | Hard constraint. |
| **Test site: SUTD canteen as proxy servery** | Camp deployment is impossible during the programme (§4.2). Frame honestly as a proxy. |
| **Evidence base: structured interviews, not photographs** | Forced by §4.2. |

---

## 3. THE PROBLEM

### 3.1 Setting

SAF cookhouses feed servicemen across roughly **60 sites** nationwide. Catering is outsourced. Meals are drawn against an **electronic meal accounting system** that records entitlement and turnout.

### 3.2 The two servery models — this distinction is the core of the whole analysis

SAF cookhouses run in **two distinct configurations**, and they fail for **opposite reasons**. Getting this split right is what separates this entry from a generic canteen project. (Source: the participant's own first-hand experience.)

#### **Type 1 — pre-plated heated display**

Kitchen staff portion food onto plates **in advance**. Plates sit under heat lamps in a display cabinet. The diner walks up, takes a plate, and goes.

- **The diner has no input mechanism whatsoever.** You cannot ask a heated cabinet for less rice.
- **The portion is decided before the diner arrives.**

#### **Type 2 — served to order**

The diner queues holding a tray. Kitchen staff serve onto it. The diner can say "less rice."

- **A mechanism already exists, is free, and costs one word.**

### 3.3 Why Type 2 is NOT the target

This was tested and rejected. The reasoning must survive in the pitch, because *showing why you rejected the obvious target is a problem-understanding point.*

The initial hypothesis was that **friction** stops people asking for less, and that a device (a button at the door, a clip on the tray, an app) would lower that friction.

**That hypothesis is wrong**, for two independent reasons:

1. **Any device is strictly worse than speech.** Speaking costs one word and zero setup. A button adds a step. Nothing beats talking.
2. **State-tracking is unsolvable.** If a diner presses a button at the entrance, the server at the counter has no way to know *which person in the moving queue* pressed *what*. There is no identity system, and adding one violates a locked constraint (§2).

**Therefore:** the barrier in Type 2 is not friction. It is **salience** and **the server's default scoop size**. That makes the honest lever in Type 2 the **ladle** — a company-side intervention, which is ruled out.

> **Type 2 is a weak consumer-side target precisely because the consumer-side solution already exists and works.**

### 3.4 The target: Type 1, and the two structural problems inside it

Type 1 is the target because **no mechanism exists at all**. Two distinct waste sources follow structurally, not incidentally.

---

#### **PROBLEM A — One portion size for a population with a ~2× appetite range**

A pre-plated cookhouse serves one portion. Its consumers range from a small-framed clerk to a large infantryman post-exercise. Their genuine appetites differ by roughly a factor of two.

- Everyone who wanted less **wastes the difference — every meal, by design.**
- This waste is **guaranteed by the system architecture**, not by carelessness or bad attitude.
- It is **invisible in aggregate**: it never shows up as over-catering, because the food was correctly issued against entitlement. It only appears at the bin, where nobody measures it.
- The diner has **no available action** other than eating too much or scraping the plate. There is no third option.

**Who is harmed:** the diner (forced choice), the contractor (pays for food that is binned), the SAF (waste handling cost and sustainability targets).

**Why nobody has fixed it:** because it looks like a catering problem, and catering-side metrics say the system is already efficient (§3.6).

---

#### **PROBLEM B — Plating is done blind, and plated food cannot be recovered**

Staff plate to the **indent** (the forecast headcount) before actual turnout is known.

- Turnout varies with duty schedules, outfield activity, bookouts, weather. The indent is a forecast, and forecasts are wrong.
- Plates unclaimed past **hot-hold time** are a **100% loss**. They cannot be re-served, cannot be chilled and reissued, cannot be donated once they have sat under heat.
- The loss is **irreversible at the moment of plating** — every plate made is either eaten or binned, decided hours earlier by someone guessing.

**Corroborating evidence:** Fort Jackson (US Army, EPA study 2019) instrumented two Army dining facilities and found **83% of food waste came from overproduction**, not from plate scrapings. This is the single most important number in the research: **the waste is upstream of the diner's fork.**

**Compounding risk if Problem A is solved naively:** if you offer two plate sizes without a demand signal, staff must now guess **the mix as well as the volume**. Guess wrong, and the leftover plates of the unpopular size are pure waste. **Solving A without B relocates the waste rather than removing it.** Every proposed solution must be checked against this.

---

### 3.5 Secondary problem — nobody in the loop ever sees the outcome

The cook, the server, and the CSM do not routinely learn how much food came back. Neither does the diner. There is **no feedback channel at any resolution** between waste and the decisions that cause it.

This matters because the strongest result in the behavioural literature is about **feedback resolution**, not about awareness (§5.6).

### 3.6 THE PUBLIC-RECORD TRAP — read before writing any pitch

**MINDEF has publicly stated that SAF food waste is ~1% of meals catered**, measured through the electronic meal accounting system ([MINDEF PQ, 3 Feb 2020](https://www.mindef.gov.sg/news-and-events/latest-releases/03feb20_pq/)). Waste goes to biogas treatment at Ulu Pandan / Tuas Nexus.

**Any judge can find this in 30 seconds.** If it is raised from the floor and the pitch has not addressed it, the problem-understanding score is gone.

**Required handling — lead with the figure, then locate the gap:**

- 1% is a **catering-side** number. It is generated by meal accounting: meals *issued* versus meals *drawn*. It measures over-catering.
- It says **nothing about the portion decision** and **nothing about post-consumer waste** — food that was correctly issued, correctly drawn, and then left on the plate.
- Problem A produces waste that is **invisible to that metric by construction**, because the meal was correctly issued and correctly drawn.
- **The 1% figure is evidence that the catering side is already well optimised — which is exactly why the remaining waste sits at the portion decision.**

> Using the 1% figure to *set up* the gap is what demonstrates you did the work. Being ambushed by it is how you lose.

Also relevant: newer cookhouses are moving to **self-serve hawker-style** formats ([PIONEER, Sep 2024](https://defencepioneer.sg/pioneer-articles/13sep24_news1)). Worth knowing — it changes the portion mechanism again, and should be acknowledged rather than hidden.

---

## 4. Hard environmental constraints

### 4.1 No company-side solutions

User-imposed. Interventions must act on the diner or on the diner's available choices, not on the contractor's process.

*Note the tension:* Problem B is structurally kitchen-side. Any solution touching B must be framed as **a signal the servery generates for itself**, not as a management tool imposed on staff.

### 4.2 SAF cookhouses are Green Zone — NO PHOTOGRAPHY

Camera phones may be carried in, but **unauthorised photography is prohibited and is an offence** ([MINDEF PQ, 2 Oct 2017](https://www.mindef.gov.sg/news-and-events/latest-releases/02oct17_pq2/)).

**Consequences, all binding:**

- **No one may photograph food waste inside camp.** Not the participant, not a friend. This was considered and correctly abandoned.
- **The camp cannot supply Waste Diary photo evidence.** The Waste Diary requires a weekly weigh-in *and photo* — so those kg must come from a photographable site.
- **Evidence base is structured interviews** (§8). Legal, and directly rewarded: the Scale-Up Plan asks "how you tested it, with whom", and the People Log exists to record exactly this.
- **The rig cannot be deployed in a cookhouse during the programme.** It runs at the **SUTD canteen as a proxy servery** — photographable, baseline-able, iterable daily.

> Frame the proxy honestly: *"tested in a proxy setting; target deployment is a cookhouse; here is what interviews say about the differences."* Judges reward that over an inflated claim.

### 4.3 A camera is a security problem before it is a technical one

This is why the no-vision constraint is an **argument**, not a shortcut. A camera-based system — the obvious modern approach, and what most competing teams will reach for — is close to **undeployable** in a Green Zone. Weight sensing answers every question a camera would, with no security review, no privacy question, and no personal data.

**State this in the pitch as a design consequence of the environment.** It converts a limitation into evidence of problem understanding.

### 4.4 Statistical honesty

Two weeks at n≈100 diners will **not** produce a statistically significant reduction. Do not claim one.

Design instead for **uptake measurement + a clean baseline + a comparison against a known alternative**, and say so explicitly. The brief asks for "findings and insights." **A straight negative result beats an inflated positive.**

---

## 5. Prior art — know this cold

A mentor will ask "how is this different from Winnow?" The answer must come in one breath.

### 5.1 Kitchen-side incumbents (the commercial mainstream)

**Winnow** (Throw & Go — up to 50% cut in repeat waste), **Leanpath**, **Orbisk**, **Kitro**. All: camera + scale over the **kitchen bin**. Category effectiveness 25–70% hotels, 54% restaurants, 41–50% workplace caterers ([ScienceDirect, 2025](https://www.sciencedirect.com/science/article/pii/S0956053X25001072)).

**All are pre-consumer, chef-facing, and subscription-priced.** None address the portion decision.

### 5.2 Military-specific — already done, publicly

- **Fort Jackson (EPA, 2019)** — Leanpath in two Army dining facilities. ~6,000 lbs/month wasted; **83% from overproduction**; 27,000 lbs weighed over 3 months; 8,000 lbs salvaged for donation. ([EPA](https://cfpub.epa.gov/si/si_public_record_report.cfm?dirEntryId=346767&Lab=NRMRL))
- Food waste is **>50% of total waste output** at some US Army installations.
- **Journal of Forecasting, 2026** — ML model predicting plate waste in military dining facilities ([Wiley](https://onlinelibrary.wiley.com/doi/10.1002/for.70128?af=R)). Cite as proof the problem is live and researched.

### 5.3 Closest competitor — post-consumer, diner-facing

**Raccoon Eyes** — Georgia Tech capstone that became a startup. Camera at the plate-return point shows students *their own* wasted food. 500,000+ plates processed; deployed at Georgia Tech, UGA, Georgia State ([Hypepotamus](https://hypepotamus.com/startup-news/raccoon-eyes-tackles-food-waste/)).

**Name this in the pitch.** The differentiator: Raccoon Eyes intervenes **at the bin, after the portion is already fixed**. Any solution here must intervene **where the portion is set**.

### 5.4 Occupied lane — upstream demand forecasting

AI Singapore's AIAP Batch 11 team "Ape-prentice" won a Smart City Ideation Challenge with **federated learning for restaurant demand prediction** ([AI Singapore](https://aisingapore.org/the-case-for-ai-in-food-waste/)).

**Correction of an earlier misreading:** this was **not** an ML tray scanner, and **nothing was built** — it was an ideation competition, business-side. So the *tray* space is open; the *demand-forecasting* lane is the crowded one. Stay out of forecasting.

### 5.5 Pricing / accountability — works, but not available here

South Korea's RFID pay-as-you-throw scheme (~130 won/kg): Seoul daily food waste **−23.9%** over a decade, **~51%** in some apartment blocks ([WEF](https://www.weforum.org/stories/2019/04/south-korea-recycling-food-waste/)).

Proves weight-based accountability works. **Requires a billing relationship that will never exist with a serviceman.** Cite as evidence, do not copy.

### 5.6 What the behavioural literature actually says

| Intervention | Result | Verdict |
|---|---|---|
| **Trayless dining** | **20–32% reduction**; Aramark measured **25–30%** across 186,000 meals at 25 campuses ([Sustainable America](https://sustainableamerica.org/blog/doing-away-with-the-tray/)) | **Best known per dollar — zero technology.** Use as the control arm. |
| **Real-time collective feedback** | Petersen et al. 2007, dorm-vs-dorm competition: **55% reduction with real-time feedback vs. 31% with weekly** ([Frontiers 2025 review](https://www.frontiersin.org/journals/psychology/articles/10.3389/fpsyg.2025.1561467/full)) | **The mechanism that works.** Feedback must be **collective** and **high-resolution**. |
| **Clean Plate campaigns** | ~15% (Univ. of Lisbon) | Weak |
| **China national anti-waste campaign** | Waste probability 76.1% → 72.9% | Very weak |
| **FoodWise (HKUST, ACM COMPASS 2023)** | Reported **engagement**, not reduction | Measured the wrong thing |

> **Gamification is the losing category.** Do not pitch "a gamified app." NEA's "Love Your Food @ Schools" lists smart bins and gamification as a *future direction* and has not filled it — that is a gap in a programme, not evidence the approach works.

### 5.7 Testing against trayless is a scoring move

Running **trayless as a free control arm** costs $0 and is the single most credible thing you can put before industry mentors: it shows the idea was tested against the best known alternative rather than against nothing.

*Caveat:* trayless applies to Type 2, where a tray exists. In Type 1 there is no tray. Run it at the SUTD canteen as a comparison arm, not as a camp intervention.

### 5.8 Past SG Eco Loop winners

**No public record of SG Eco Loop cohort 1.0 winners exists.** Searched, not found. What is known from the kickoff: cohort 1.0 was a pilot with ~100 ITE College Central students; the top 5 teams presented to ~300 people. **Do not fabricate winner examples.**

### 5.9 The gap, in one sentence

> **Every system built so far measures food waste after the portion is already decided — in the kitchen, or at the bin. In a pre-plated cookhouse the diner has no way to influence that portion at all, and the kitchen decides it blind.**

---

## 6. RULED OUT — do not re-propose

| Idea | Why it was killed |
|---|---|
| **Gamified app / leaderboard / points** | The losing category (§5.6). Every cited result is weak or measures engagement instead of reduction. |
| **ML tray scanner / camera vision** | Raccoon Eyes already did it at 500k+ plates (§5.3). And a camera is a security problem in a Green Zone (§4.3). |
| **Demand forecasting model** | AISG's team occupies that narrative (§5.4). Also business-side, violating §4.1. |
| **Pre-commitment button kiosk** ("press for less rice" at the servery entrance) | The server cannot tell which person in the queue pressed what. Needs an identity system, which is locked out. **And speech is already faster.** |
| **Tray-mounted clip / token / RFID signal** | Same state-tracking failure, plus it adds a step to something that currently costs one word. |
| **Type 2 servery as the primary target** | A free, working consumer-side mechanism already exists there (§3.3). The real lever is the ladle, which is company-side. |
| **Photographing food waste in camp** | Offence under Green Zone rules (§4.2). Considered, correctly abandoned. |
| **Any solution requiring a billing / charging relationship** | No such relationship exists with a serviceman (§5.5). |
| **Optimising for the Impact/kg prize** | User decision — Innovation track only (§2). |

---

## 7. Solution candidates — OPEN, NOT DECIDED

> **Status: the human is still deciding.** These are options with stated risks. Do not narrow to one unless asked. The ordering is not a ranking of intent.

### Design targets any candidate must meet

- Acts on **Problem A**, **Problem B**, or both — and if it acts on A alone, it must explain why it does not simply **relocate** waste (§3.4).
- Zero or near-zero added queue time.
- No training required for diner or server.
- No camera, no identity, no personal data.
- Survives steam, grease, thousands of users.
- Buildable for ≤ S$200 on a Raspberry Pi.
- **Its novelty must not be something a mentor already knows.** "Smaller plates reduce intake" is well established — claiming that as the innovation loses the originality criterion.

### 7.1 Candidates addressing PROBLEM A (fixed portion)

| # | Candidate | Mechanism | Main risk |
|---|---|---|---|
| **A1** | **Two plate sizes in the display + load cell under each shelf** | The diner picks the plate they want. The **choice is the action** — nothing to press, say, or learn. Shelf weight ÷ average plate weight = plates left; rate of change = take rate. | The plate itself is not novel. Must be pitched as the closed loop (see B1), not as "small plates." Does nothing about Problem B on its own. |
| **A2** | **Seconds-availability display** (diner-facing) | Targets **scarcity anxiety** — the reason people take the large portion may not be appetite but that choosing small and still being hungry leaves no recourse. A display reading `SMALL — 7 left · seconds until 13:30` removes the downside. | Unverified hypothesis. Depends on Q4 (are seconds actually permitted?). Shares hardware with A1 at no extra cost. |
| **A3** | **Dish-level waste feedback at the dish** — *"6.2 kg of this came back yesterday"* | Dish-specific, location-specific, delivered **at the moment of choosing** — not on a poster by the door. Data from a one-off bin weigh entered daily; no live bin sensor needed. | Information is the weakest lever in §5.6. Habituation within ~1 week is likely. Strong as a *second* prototype, weak as the only one. |
| **A4** | **Trayless (Type 2 only)** | 20–32% established (§5.6). | Not applicable to Type 1 (no tray). Use as a **$0 control arm at SUTD**, not as the entry. |

### 7.2 Candidates addressing PROBLEM B (blind plating)

| # | Candidate | Mechanism | Main risk |
|---|---|---|---|
| **B1** | **Take-rate → plate-next signal** (kitchen-facing display) | Shelf sensors derive plates-left and take rate per size; the display tells staff what mix to plate next. Self-correcting — the servery measures its own demand. Example: `REGULAR 18 left 6.0/min · SMALL 7 left 4.2/min · -> plate 10 SMALL next · window closes 13:30` | **Shares the rig with A1**, so may not count as a *distinct concept* for the second S$200 (Q1). Sits closest to the §4.1 company-side line — must be framed as a signal the servery generates, not a management tool. |
| **B2** | **Last-call rescue** — broadcast `12 plates left, 10 min to close` to a company Telegram group | Converts a **guaranteed 100% loss into eaten food**. The only candidate that produces real Waste Diary kg as a side effect. Demos live at the showcase. | Meal windows track duty schedules; if everyone is back at work, nobody comes. **Test and report honestly.** Also shares the A1/B1 rig. |
| **B3** | **Hot-hold expiry tracking** | Plates logged in with a timer; alert before the discard threshold. | Weakest. Measures a loss without providing an action, and requires staff to log things. Only revisit if interviews say hot-hold discard is larger than expected. |

### 7.3 Framing note — applies to whichever combination is chosen

Whatever is built, the **claimed innovation** must be the thing a mentor does not already know. Strongest available framing at present:

> *Offering portion choice in a system that structurally has none, plus a self-correcting demand signal so the kitchen plates the right mix without guessing — with no camera, no personal data, and no added queue time, in an environment where a camera is not deployable.*

### 7.4 Indicative build cost (for an A1/B1-shaped build)

| Part | Note | ~Cost |
|---|---|---|
| Raspberry Pi 4 / Zero 2 W | reusable afterwards | own / ~$60 |
| 2 × HX711 + 20 kg load cells | one per shelf | ~$25 |
| HDMI display | kitchen- or diner-facing | ~$40 |
| Shelf platform (plywood / acrylic) | SUTD fab lab | $0 |

**Engineering notes for whoever builds it:**

- **Expose calibration, do not infer it.** Average plate weight per size and empty-shelf tare are stored constants set by a physical routine (place empty → press → save). Load cells drift; plates and shelves differ per camp. Leave the knob.
- **Verification:** one `demo()` / `__main__` self-check asserting the pipeline end to end — known mass on the shelf → tare applied → correct derived plate count and take rate. No test framework, no fixtures.
- **Physical check:** 20 timed placements of a known mass, ±5%, no drift across a 30-minute warm-up.

---

## 8. Evidence plan — interviews

Forced by §4.2. Target **n = 5–8** across camps. Requests must go out **immediately** so findings, not intentions, arrive on 5 Sep.

The Type 1 / Type 2 split is already established from first-hand knowledge. These are the **open** questions:

1. Which type is your camp, and does it vary by meal?
2. **(Type 1)** Are the plates identical, or is there already any size variation? Are plates ever left in the display at window close, and what happens to them?
3. Have you ever wanted less than the plated portion? What did you do — eat it, bin it, give it away?
4. Can you go back for seconds? Does anyone? What stops them?
5. Roughly what fraction of plates come back with food left? (impression, not a count)
6. Does anyone — cook, server, CSM — ever hear how much came back?

**Log every interviewee in the People Log.** The Scale-Up Plan explicitly asks who you tested with; this is scored, not admin.

---

## 9. Scale-up argument

SAF's ~60 cookhouses are run by **two catering contractors — SATS Defence Catering and Foodfare** ([SATS](https://www.sats.com.sg/media/careers-our-people/home-team-academy-cookhouse-food-services), [MINDEF archives](https://www.nas.gov.sg/archivesonline/data/pdfdoc/MINDEF_19980211001.pdf)).

**You do not have to convince the SAF unit by unit. You have to convince two companies** — and food waste is already a direct cost against their contract margin, so the commercial incentive is aligned without appealing to sustainability.

**Policy channel:** the **SAF Sustainability Office**, established 2020 ([PIONEER](https://defencepioneer.sg/pioneer-articles/saf-goes-greener--sets-up-new-saf-sustainability-office)).

**Position in the waste hierarchy:** SAF food waste already goes to **biogas treatment** (Ulu Pandan / Tuas Nexus). Reduction sits *above* treatment in the hierarchy — this is prevention, not better disposal. Say so; it is a potential-impact point.

---

## 10. OPEN QUESTIONS — do not invent answers

| # | Question | Blocks | How it gets answered |
|---|---|---|---|
| **Q1** | Are the two chosen concepts distinct enough to unlock the second S$200? | Budget, prototype 2 scope | **Email Jamie.** She asked to be told in advance. |
| **Q2** | Are Type 1 cookhouse plates genuinely identical today, with no size variation already offered? | **Everything in §7.1.** If size variation already exists, A1 collapses. | Interview Q2 |
| **Q3** | Are plates routinely left unclaimed at window close, and what happens to them? | Whether B2 is worth building | Interview Q2 |
| **Q4** | Are seconds actually permitted and practically available? | A2 entirely | Interview Q4 |
| **Q5** | Which servery type dominates, by meal and by camp? | Generality of the whole entry | Interview Q1 |
| **Q6** | Can the SUTD canteen host a rig, and on what terms? | Test plan | Ask SUTD facilities |

---

## 11. Timeline

| When | What |
|---|---|
| **Now → 4 Sep** | Send interview requests. Email Jamie re: second S$200 (Q1). Write problem statement + 2–3 prioritised ideas. Order load cells + HX711 if a weight-based candidate is chosen. |
| **5 Sep** — Day 1 | Arrive with problem statement + early interview findings. |
| **6 Sep** — Day 2 | Confirm Type 1 focus against interviews. Lock the solution. Start build. |
| **Wk 8 Sep** | Core sensing working, self-check passing. |
| **Wk 15 Sep** | Display + derived metrics. Baseline week at SUTD canteen. Mentor check-in. |
| **Wk 22 Sep** | Intervention week + trayless control arm. |
| **29 Sep – 1 Oct** | Scale-Up Plan slides → PDF. **All deliverables due 1 Oct.** |
| **2 Oct** | Public Showcase, Temasek Shophouse. |

> **Photograph the build process continuously and caption it, starting now.** The Scale-Up Plan brief calls this out under Tips. These are free marks that can only be earned by starting early — they cannot be reconstructed at the end.

---

## 12. Criteria map — how the entry scores on all five

| Criterion | Coverage |
|---|---|
| **Problem understanding** | MINDEF's 1% figure → the gap it structurally cannot cover (§3.6). Fort Jackson's 83% locates the waste upstream (§5.2). The Type 1 / Type 2 split — **including why Type 2 was rejected** — demonstrates first-hand knowledge no competing team has. |
| **Originality** | Intervenes where the portion is **set**, not where waste is **measured**. Camera-free by necessity, for a security-constrained environment. Positioned explicitly against Winnow, Leanpath, Raccoon Eyes, AISG, and Korea's RFID scheme. |
| **Feasibility** | ~S$100–125, one Pi, no ML, no accounts, no personal data, zero added queue time, zero training. Scale-up needs two companies convinced, not an army. |
| **Potential impact** | ~60 cookhouses. Reduction sits **above** the biogas treatment already in place — top of the waste hierarchy, not the bottom. |
| **Pitch & clarity** | Live physical demo — lift a plate, watch the count fall and the signal fire. Works in a loud hall with no network. |

---

## Appendix — source list

| Claim | Source |
|---|---|
| SAF food waste ~1% of meals catered; biogas treatment | [MINDEF PQ, 3 Feb 2020](https://www.mindef.gov.sg/news-and-events/latest-releases/03feb20_pq/) |
| Green Zone photography prohibited, is an offence | [MINDEF PQ, 2 Oct 2017](https://www.mindef.gov.sg/news-and-events/latest-releases/02oct17_pq2/) |
| Newer cookhouses self-serve hawker-style | [PIONEER, Sep 2024](https://defencepioneer.sg/pioneer-articles/13sep24_news1) |
| SAF Sustainability Office established 2020 | [PIONEER](https://defencepioneer.sg/pioneer-articles/saf-goes-greener--sets-up-new-saf-sustainability-office) |
| Cookhouse catering contractors | [SATS](https://www.sats.com.sg/media/careers-our-people/home-team-academy-cookhouse-food-services), [MINDEF archives](https://www.nas.gov.sg/archivesonline/data/pdfdoc/MINDEF_19980211001.pdf) |
| Fort Jackson — 83% overproduction | [EPA, 2019](https://cfpub.epa.gov/si/si_public_record_report.cfm?dirEntryId=346767&Lab=NRMRL) |
| ML plate-waste prediction, military dining | [Journal of Forecasting, 2026](https://onlinelibrary.wiley.com/doi/10.1002/for.70128?af=R) |
| Commercial food-waste tech effectiveness | [ScienceDirect, 2025](https://www.sciencedirect.com/science/article/pii/S0956053X25001072) |
| Raccoon Eyes | [Hypepotamus](https://hypepotamus.com/startup-news/raccoon-eyes-tackles-food-waste/) |
| AISG federated demand forecasting | [AI Singapore](https://aisingapore.org/the-case-for-ai-in-food-waste/) |
| South Korea RFID pay-as-you-throw | [WEF, 2019](https://www.weforum.org/stories/2019/04/south-korea-recycling-food-waste/) |
| Trayless dining 20–32% | [Sustainable America](https://sustainableamerica.org/blog/doing-away-with-the-tray/) |
| Real-time vs. weekly feedback (55% vs 31%) | [Frontiers in Psychology, 2025](https://www.frontiersin.org/journals/psychology/articles/10.3389/fpsyg.2025.1561467/full) |
