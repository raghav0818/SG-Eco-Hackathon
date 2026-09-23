# Tray Watch — Scale-Up Plan deck blueprint

Prepared 23 September 2026. This is the **Tray Watch** specialization of the [shared Scale-Up Plan structure](../scale-up-plan-base.md). The required deliverable is a **slide deck submitted as a PDF by 1 October**; the public showcase is **2 October**. Selected slides can support the booth video, photos, and prototype. The [official deliverable page](../hackathon%20documents/SG%20Eco%20Loop%20Hackathon%20Framework%20Reference.pdf) (p. 1), [kickoff slides](../hackathon%20documents/20260826%20SG%20Eco%20Loop%20Kickoff%20Slides.pdf) (pp. 5–6, 31), and [organizer transcript](../hackathon%20documents/20260826%20SG%20Eco%20Loop%20Kickoff.transcript.vtt) (02:26–02:31) govern the content.

## The case to make

> **Tray Watch records display trays during service and turns those observations into a retrospective page for the owner's next preparation and top-up plan. Its first pilot must establish whether the visual readings are reliable, useful, and able to reduce discarded food without causing stock-outs.**

The stall owner is the **user**; a food-court operator is a **possible scale buyer**, still to be validated. Students are customers whose choices affect the tray, not users of the device. The current product is a camera and Pi above the display, an analysis pipeline, and a **later report** for the owner. An in-service alert is a possible future version, not the present result. The [user journey](06-traywatch-user-journey.md) and [PRD](09-traywatch-prd.md) develop that distinction.

The Best Innovation rubric has five **equally weighted** criteria: **problem understanding, originality, feasibility, potential impact, pitch and clarity** ([kickoff slides, p. 5](../hackathon%20documents/20260826%20SG%20Eco%20Loop%20Kickoff%20Slides.pdf); [organizer transcript, 00:11:59](../hackathon%20documents/20260826%20SG%20Eco%20Loop%20Kickoff.transcript.vtt)). Give each criterion visible evidence. The national context is substantial—Singapore generated **790,000 tonnes of food waste in 2025**, with an **18% recycling rate**—but that is *all food waste*, not Tray Watch's addressable market or its measured impact ([NEA](https://www.nea.gov.sg/our-services/waste-management/3r-programmes-and-resources/food-waste-management)).

## Evidence you have, and evidence you still need

| Evidence | What it supports | Limit |
| --- | --- | --- |
| [Photos of the mounted system](../images%20for%20traywatch/), especially photos 5 and 6 | The camera and Pi were physically placed at a real SUTD canteen stall. | Similar still views do not show a refill, a time series, model accuracy, or avoided waste. |
| Owner interview recorded in the [PRD](09-traywatch-prd.md) and [project context](../CLAUDE.md) | The owner's concern about slow-selling vegetables and her permission/preferences informed the concept. | An interview is discovery feedback; it is not a test of the completed report. |
| `capture.py`, `analyse.py`, `report.py` and their self-tests | A working software path exists and can be exercised. | Self-tests and `demo_week.py` use controlled or synthetic inputs; they are not stall findings. |
| A controlled home test with bowls or, preferably, rectangular food containers | Can test frame capture, known visual-level changes, an actual top-up, timestamping, agreement with manual visual labels, and report rendering. | Label it a **home bench test**. A visual label is not a measured tray volume or food mass; the test does not prove performance at the stall or waste reduction. |
| Saved Pi frames/CSV, owner response to a report, and comparable waste weights | Could support field accuracy, usefulness, and eventual kg reduction. | None is present in this checkout as of 23 September. Add only if obtained. |

The organizer explicitly asks for **what was actually built and tested, how/where/with whom, findings, actual impact, reflections, and a six-month plan with stakeholders and budget** ([framework reference, p. 1](../hackathon%20documents/SG%20Eco%20Loop%20Hackathon%20Framework%20Reference.pdf)). The organizer also warns that obvious AI output should not replace user interaction. Use the real stall photos as the deck's visual backbone; mark generated diagrams as illustrations.

## The PDF: 13 core slides plus a short appendix

| Slide | Headline and content | Proof to put on the slide | Main judging criterion |
| --- | --- | --- | --- |
| 1 | **“The decision happens before food reaches the bin.”** One sentence explaining Tray Watch. | Real stall photo, one small label pointing to the camera. | Proposition; pitch and clarity. |
| 2 | **The owner's actual problem and why you chose it.** Summarize what she told you about slow-selling vegetables and the choice to prepare or top up. | An attributed **interview summary** with role/date, unless verbatim words can be verified; a buy → cook → display → leftover path. | Problem, why chosen, what learned; problem understanding. |
| 3 | **Scale, users and unknowns.** NEA's 2025 national figure is context only; eligible users are stalls with cooked food displayed in trays. The stall owner acts on the report; an operator may pay and approve shared-site mounts. Local baseline and buyer demand remain unmeasured. | One sourced national number, one role map, and a “to measure” box. | Problem size, target user, others involved, unknowns. |
| 4 | **The real-world concept.** Observe display trays through service and give one next-day preparation or top-up decision. Compare Winnow's camera-plus-scale at disposal with this earlier observation point ([Winnow](https://www.winnowsolutions.com/product/food-waste-management-software)); claim a different input, not market exclusivity or proved superiority. | Four-step service loop and side-by-side observation point. | Concept and originality. |
| 5 | **What was actually built.** Pi 5, webcam, fixed crop, periodic JPEGs, tray-fill analysis, one-page output. Identify manual dish mapping and all still-planned automation. | Real stall photos 5 and 6 plus a four-box data flow. | Prototype and feasibility. |
| 6 | **Where/how/with whom it was tested.** Separate real SUTD mounting and framing with owner involvement from the controlled home bowl/container test. Give dates, participants, tasks and limitations. A home bench result never becomes a stall performance result. | Two clearly captioned photos, one field and one home; test matrix. | Testing method and feasibility. |
| 7 | **What the tests found.** Report actual frame coverage, visible privacy, agreement with manual **visual** fill labels, known-refill detection and report rendering *only after measured*. State an owner reaction only if obtained. Show a failure and a numerator/denominator. Never call model fill or leftover kg “exact.” | Compact result table with the raw frame/report reference. | Findings and insight; feasibility/clarity. |
| 8 | **Impact: current evidence and potential.** State “avoided kilograms not yet measured” unless an intervention and weighed comparison occurred. Show the audit bridge from tray observation → owner action → weighed discard, and a transparent **illustrative** scenario, not a forecast. | One equation, labelled sensitivity range and missing measurement. | Waste diverted and potential impact. |
| 9 | **Reflection, biggest obstacle, skills.** The owner already knows which dishes sell slowly. The harder question is whether tray quantity and top-up timing change a useful decision. Name the hardest build/test problem and what changed in the design; acknowledge the owner and mentor with permission. | Before/after product decision, backed by interview and tests. | Learning, challenge, response, skills. |
| 10 | **Refine and pilot.** Fix capture reliability, tray identity and output clarity; first weigh comparable baseline waste, then give one reversible recommendation. Set a stop rule for stock-outs and owner burden. | One pilot experiment diagram, baseline → recommendation → comparison. | What comes next and why; feasibility. |
| 11 | **Six-month execution timeline.** Use the month-by-month gates below. Show a one-stall baseline/intervention before multi-stall replication. | Timeline from Oct 2026 to Mar 2027 with decision gates. | Scaling execution and six-month timeline. |
| 12 | **Stakeholders and recruitment.** Owner reads/acts; site or food-court operator grants mounting/network/privacy permission and may buy; students affect demand; researcher audits waste. **Ask** the current owner for an introduction only if willing, then approach the operator and two other stalls; no introduction or commitment is secured yet. | Role map with a proposed introduction/permission path. | Who is involved and how to bring them in. |
| 13 | **An itemized pilot budget and the ask.** Show three-stall, six-month cash spend, fully loaded work, per-stall cost and cell provenance. Ask for one stall and operator approval for a measured pilot; do not ask judges to believe an unmeasured kg claim. | Budget table from the section below; one-sentence pilot ask. | Budget breakdown and potential impact. |

Appendix: one technical architecture slide, test protocol and raw result table, source links, acknowledgements, and the specific assumptions behind the impact and budget. Include **photo captions** (what, where, when, who permitted it). The deck is a PDF, but slides 1, 5, 7 and 11 can also be printed or displayed at the booth.

## Run one defensible home test before writing slide 8

Use the real Pi/webcam and actual `capture.py` → `analyse.py` → `report.py` chain. Rectangular food containers resemble the target trays better than bowls; if only bowls are available, say so. Set 3–4 containers at known visual fill levels, take a manual photo and timestamp at each step, remove some contents, make one **known** refill, then leave one container partly full. Run at least 30–60 minutes so several scheduled captures bracket each change. Keep the original frames and a hand-written truth table. Label the site **home**, not SUTD.

Report: usable frames / expected frames; number of containers correctly counted; mean absolute **disagreement with manually estimated visual fill** in percentage points on a labelled sample; whether the known refill was detected and the timestamp error; whether the printed page matches the source images. This is **model-versus-person agreement**, not error against measured food volume or kilograms. If the model fails on bowls, that is a test result and a reason to pilot with real tray geometry next. `report.py --no-llm` provides an offline fallback. Do not show the `demo_week.py` synthetic page as a field result; it is intentionally marked **SYNTHETIC**.

If you can reach the stall owner, show her the labelled home-test page or a clearly marked example and ask **“Would this change what you prepare or top up tomorrow? What is missing?”** Record the exact answer and whether she was looking at a simulation. That is feedback on usefulness, separate from the bench accuracy test; do not present it as a week of live deployment.

## Six months after the showcase: a gated pilot

| Month | Action and stakeholders | Decision gate |
| --- | --- | --- |
| **Oct 2026** | Fix the field path: reliable mount, crop, clock, tray identity if moved, and report captions. Ask the existing stall owner to inspect an actual output; seek stall and site permission. | **Proposed gate:** written site permission, no identifiable people in retained frames, ≥95% of scheduled frames usable over 3 service days, and one owner interpretation of the page recorded. If not, fix setup before baseline. |
| **Nov** | One-stall **baseline**: plan **10 comparable service days** and manually weigh unsold cooked food at close by dish. Log menu, hours, footfall proxy and whether food is discarded, reused or donated. | **Proposed gate:** at least 8 of 10 days have a complete tray log and matched, dish-level weight/destination record. If not, extend baseline. |
| **Dec** | One-stall intervention: give one reversible recommendation per week over **10 comparable service days**; record whether followed, discarded kg, sell-outs and sales/owner concerns. | **Proposed gate:** at least 8 complete days and one documented owner action. Any concerning stock-out or lost-sales signal pauses expansion, regardless of apparent kg change. |
| **Jan 2027** | **If the one-stall gate passed**, ask the owner for an introduction if willing and seek operator permission to repeat in 2–3 eligible stalls and different lighting/layouts. Owners control menu and replenishment. | **Proposed gate:** two additional consenting stalls with site approval and at least 3 usable service days each. Otherwise stay at one stall. |
| **Feb** | Automate dish identity, audit sampling, report delivery and fault alerts; time installation and support per stall. | **Proposed gate:** report each site's setup minutes, ongoing support minutes/week and report delivery success; obtain staff acceptance rather than assuming the work is affordable. |
| **Mar** | Present measured waste, owner adoption, full pilot cost and buyer interviews; decide to extend, change the product, or stop. | **Proposed gate:** report baseline vs intervention kg with denominator, stock-outs, owner follow-through, cash/full cost per stall, and at least one operator's stated purchase conditions. No buyer response means buyer fit remains open. |

NEA's [food-retail food-waste audit template](https://www.nea.gov.sg/docs/default-source/our-services/waste-management/fwm-guidebook-for-food-retail-establishments-%28resized%29.pdf) separates **over-production** from preparation and plate waste and records kilograms and destination. Use that in the **pilot evaluation**. The everyday Tray Watch interface can still speak in tray levels; a temporary research weigh-in is how you verify an environmental kg claim.

## Impact slide: show the arithmetic, then the missing measurement

`avoided kg/year = eligible stalls × service days/year × measured avoided kg per stall-day × adoption factor`

For a **hypothetical** site with 20 eligible stalls, 250 service days and 0.25 kg avoided per adopting stall-day at full adoption, the arithmetic is **1,250 kg/year**. At 0.10 kg it is 500 kg; at 0.50 kg it is 2,500 kg. These are *sensitivity cases*, not forecasts or results. Replace the 0.25 kg and adoption assumptions with weighed pilot data and owner follow-through before presenting a forecast. Never use Singapore's 790,000-tonne total as though it were Tray Watch's market or savings.

The primary outcome is **kg of unsold cooked food discarded per comparable dish-service**, not percent fill on a photograph. Track stock-outs, sales and discarded/reused/donated destinations alongside it. Without a baseline and a change the owner actually made, the current attributable reduction is **unmeasured**.

## Budget slide: one model, with provenance on every cell

Budget a **three-stall, six-month pilot**, not an imaginary national rollout. Show columns for quantity, unit cost, source, and total:

| Line | Calculation to show | Status |
| --- | --- | --- |
| Pi 5 2 GB | 3 × **S$98 = S$294** as a **historical-price planning case**, before reuse and any new quote | Actual unit price on the [14 Sep 2026 project invoice](../FINANCE%20CLAIMS/Order_548750.pdf); incremental cash can be lower if an existing board is reused. Do not count one physical Pi in both prototype budgets. |
| Webcams | 3 × current supplier quote | Existing camera proves feasibility; fleet purchase price still needs a quote. |
| SD cards, power, safe mounts, spare | Per-stall bill of materials × 3 | Quote; confirm site approval and cleaning/access constraints. |
| Vision calls and storage | Measured cost per observed service day × planned days × 3 | The PRD's ~US$2/week is an estimate, not a bill. Check current [Google API pricing](https://ai.google.dev/gemini-api/docs/pricing) and usage after the home test. |
| Human work | Installation hours + manual dish labels/audits + owner review + support hours, each × a stated hourly rate | State this even if the student prototype used unpaid time. Automation must reduce it. |
| Travel, printing, contingency | Itemised; contingency percentage stated | Estimate and later verify. |

Do not use the prototype's “≤S$20 more hardware” as the per-stall scale cost: it assumes the Pi and webcam were already owned. Show **pilot cash spend**, **fully loaded cost**, and **cost per stall** separately. Before exporting the PDF, obtain dated supplier quotes for cameras, mounts, storage and power; measure API usage in the home run and staff time in setup/audit. Calculate `six-month cash = new hardware + software/usage + paid setup/audit + travel + contingency`, then the fully loaded total including reused gear and unpaid hours. The operator buyer and any rental price remain hypotheses until buyer interviews. **Do not submit a placeholder-only budget slide.**

## Questions judges are likely to ask

| Question | Evidence-based answer now |
| --- | --- |
| “How many kilograms did Tray Watch save?” | “We have not measured an attributable reduction yet. We mounted it at a real stall. A home test of the capture/analysis chain is planned; if completed, I will show its labelled result. The proposed pilot weighs over-production before and after one owner-approved change.” |
| “Doesn't the owner already know which dishes sell slowly?” | “Yes. Her own interview made that clear. The proposed value is the *amount left and timing of a top-up*, tied to one next-day decision; that value still needs user validation.” |
| “Why isn't this Winnow?” | “Winnow measures food discarded at a bin and gives kitchens actionable reports. Tray Watch's distinct proposed input is the display tray *during service*. We have not proved superiority or impact yet.” |
| “Who will pay and who gives permission?” | “The stall owner uses the output. A food-court operator is the hypothesised fleet buyer and would approve shared-site deployment; that buyer case is a Month 4–6 test.” |
| “Is your video or report AI-generated?” | “The stall and hardware photos are real. Any AI animation is labelled as an illustration. The home demonstration and synthetic demo are separately labelled; field results come only from original frames and logs.” |

## Work before the 1 October PDF

| When | Finish this |
| --- | --- |
| **23–25 Sep** | Run the home bench test; retain original images/CSV and a one-page result table. Ask for owner feedback remotely if feasible. Fix code failures that prevent the real chain from running. |
| **26–27 Sep** | Draft all 13 slides with real, captioned stall photos; keep the home demonstration visibly separate. Get supplier quotes and log your time for the budget. |
| **28–29 Sep** | Have one uninvolved reader test the deck against all five judging criteria. Resolve unclear claims; prepare the video and printed example report. |
| **30 Sep** | Export PDF, check it on another device, and submit before the 1 Oct deadline. Test the booth video offline. |
| **2 Oct** | Bring the real camera/Pi, loop the short video silently, and practise the 45-second pitch plus the five questions above. The organizer says judges will speak with you about *what* you built and *why* ([kickoff transcript](../hackathon%20documents/20260826%20SG%20Eco%20Loop%20Kickoff.transcript.vtt), 00:16–00:17). |

The Waste Diary and People Log are separate programme deliverables. Do not turn a bowl demonstration or a visually full tray into kilograms diverted. The [programme email](../hackathon%20documents/email.txt) requires weighed, photographed kg for the diary and stresses integrity; the Scale-Up Plan can explain the **future impact measurement** without claiming those kg today.
