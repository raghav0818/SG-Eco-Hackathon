# Design research: award-site craft, AI-slop tells, and the Figma→code pipeline

**Compiled:** 2026-09-22
**Method:** primary sources only — official docs, specs, npm registry metadata, MDN browser-compat-data, the Web Platform Status API, and **direct inspection of the live production bundles** of the sites under study (fetched with `curl` on 2026-09-22 and grepped).
**Verification legend:** ✅ verified against a primary source · ⚠️ verified only against a secondary source · ❌ could not verify (flagged, not guessed).

---

# Part 1 — Award-winning "hand-crafted premium" web technique

## 1.1 Site teardowns

All four sites were fetched directly and their JS/CSS bundles scanned. Findings below are **measured**, not inferred from marketing copy.

---

### 1.1.1 L.I.S.A. — https://lisa.locomotive.ca/en (Locomotive)

**Award record** ✅ — Awwwards *Site of the Day*, **16 September 2026**. Agency: **Locomotive (PRO)** + **60fps (PRO)**. Score **7.48** (Design 7.45 / Usability 7.22 / Creativity 7.89 / Content 7.61). Awwwards tag list, verbatim: *"Design Agencies, Technology, Experimental, Animation, 3D, Content architecture, WebGL, GSAP, Blender"*.
Source: https://www.awwwards.com/sites/l-i-s-a

**Delivery shape** ✅ — Not a JS framework app. Plain server-rendered HTML + exactly three assets:

```
https://lisa.locomotive.ca/assets/styles/main.css?v=1773158732955     ~200 KB
https://lisa.locomotive.ca/assets/scripts/vendors.js?v=1773158732955    5.5 KB
https://lisa.locomotive.ca/assets/scripts/app.js?v=1773158732955       2.5 MB  ← everything
```

No `__NEXT_DATA__`, no Nuxt, no Svelte. Behaviour is wired with `data-module-*` attributes in the HTML (`data-module-lisa`, `data-module-lisa-visualizer`, `data-module-header`, `data-module-video-modal`, `data-module-hovers`, `data-module-load`, `data-module-cookie-consent`) — Locomotive's long-standing home-grown module-bootstrap pattern. Content is injected via `data-lisa-content` / `data-lisa-translations` / `data-lisa-locale` attributes.

**Libraries actually present in `app.js`** ✅ (occurrence counts from grep):

| Library | Evidence |
|---|---|
| **three.js** | `THREE.` ×173, `WebGLRenderer` ×35, `ShaderMaterial` ×20, `PerspectiveCamera` ×8 |
| **Custom GLSL** | `gl_FragColor` ×73, `uniform float` ×95, `uniform sampler2D` ×66, `varying vec2` ×83 — this is hand-written shader work, not a shader library |
| **Lenis** | `window.lenisVersion="1.1.9"`; class names `lenis`, `lenis-stopped`, `lenis-smooth`, `lenis-scrolling`; opt-out attributes `data-lenis-prevent`, `data-lenis-prevent-wheel` |
| **GSAP** | `version:"3.14.2", name:"scrambleText"` → GSAP **3.14.2** with **ScrambleTextPlugin**; also `SplitText`, `ScrollTrigger`, `Flip` |
| **Barba.js** | `prefix:"data-barba"`, `x-barba` request header, `namespace`/`wrapper` config — page transitions |
| **Swiper** | carousels |
| **mustache.js 4.2.0** | `{{ }}` client-side templating |
| **Tweakpane** | a debug GUI **shipped to production** — a nice tell that this is a hand-tuned art-directed build |

**Easing vocabulary** ✅ — from `main.css`, the two curves that carry the whole site:

```css
cubic-bezier(0.215, 0.61, 0.355, 1)   /* easeOutCubic (Penner) — 43 uses */
cubic-bezier(0.23, 1, 0.32, 1)        /* easeOutQuint (Penner)  —  9 uses */
```

Both are pure ease-*out* curves. There is no overshoot/elastic easing anywhere. This matches the animation consensus (§1.9).

**Accessibility finding** ⚠️ — `prefers-reduced-motion` appears **5 times in `main.css` and zero times in `app.js`**. Lenis **1.1.9** predates the `respectReducedMotion` option (see §1.2), so on this build the CSS transitions are suppressed under reduced motion but the **inertia scroll itself is not**. Worth copying the CSS discipline; worth *not* copying the scroll gap.

---

### 1.1.2 Solarin (Sirin Labs) — https://www.awwwards.com/sites/solarin

**Award record** ✅ — Awwwards *Site of the Day*, **12 July 2016**. Agency **Monks (PRO)**. Overall **8.17/10**.
Technologies, verbatim from the Awwwards listing: *"Promotional, Technology, Web & Interactive, Big Background Images, Clean, Unusual Navigation, WebGL, GSAP, RequireJS, Modernizr, Knockout"*.
Source: https://www.awwwards.com/sites/solarin

**Liveness** ✅ — the site is **dead**. `solarin.com` now redirects to a domain-parking page (`domains.atom.com`, HTTP 403); `sirinlabs.com` returns HTTP 526. Only an archive copy survives:
http://web.archive.org/web/20161031202724/https://www.solarin.com/ (checked via the Wayback availability API).

**Decision-relevant read:** of that 2016 stack, **RequireJS, Knockout and Modernizr are all obsolete**. The only two things that survived ten years are **WebGL** and **GSAP**. That is the single most useful datapoint in this whole section: the durable half of the "premium" toolkit is small.

---

### 1.1.3 UNITED24 Rebuild Map — https://u24.gov.ua/rebuild/map

**Stack** ✅ — measured from the live page:

```html
<script src="runtime-es2015.75a0093ffb6a6c7e55c3.js">
<script src="runtime-es5.75a0093ffb6a6c7e55c3.js">
<script src="polyfills-es5.fda8bcb158e682e5e9ed.js">
<script src="polyfills-es2015.ebb5508bbd7ead092ddf.js">
<script src="scripts.26d03bd3d89e957cb685.js">
<script src="main-es2015.7ebbacf204898af41d07.js">   ← 1.6 MB
<script src="main-es5.7ebbacf204898af41d07.js">
```

That `es2015`/`es5` pair is Angular CLI **differential loading** (Angular 8–12 era output). Grepping `main-es2015.js`: **`mapbox` ×264**, `Angular` ×39. **Zero** hits for three.js, GSAP, Lenis, D3, Leaflet, deck.gl. `styles.css` (305 KB) has 10 `backdrop-filter` and **no** `animation-timeline` / `scroll-timeline`.

**Decision-relevant read:** a site of this profile and reputation is an **Angular + Mapbox GL** app with essentially no animation library. Its impact is content, cartography and data density — not scroll choreography. Do not assume "award-adjacent" implies a WebGL hero.

---

### 1.1.4 LinusBio — https://www.linusbio.com/

**Award record** ⚠️ — listed on Awwwards as a **Nominee** (https://www.awwwards.com/sites/linusbio). ❌ Could not confirm a Site-of-the-Day win.

**Stack** ✅:
- CMS/hosting: **Craft CMS on Servd** — assets on `servd-linusbio-cs.b-cdn.net` (bunny.net CDN).
- One CSS (74 KB) + one JS (335 KB): `main-corporate.min.css` / `main-corporate.min.js`.
- `main-corporate.min.js` contains: **Swiper** (×410), **GSAP + ScrollTrigger**, **ScrollToPlugin `version:"3.12.1"`** → GSAP **3.12.1**, and **Alpine.js `version:"3.13.10"`**.
  - ⚠️ Caveat: the `ScrollSmoother` and `Flip` strings in the bundle are ScrollTrigger's **internal interop checks** (`e.vars.id !== "ScrollSmoother"`), not proof those plugins are loaded. Do not read them as "they use ScrollSmoother".
- **No Lenis.** No three.js.
- CSS: 15 × `backdrop-filter`, 5 × `text-wrap`, and the dominant easing is `cubic-bezier(.4,0,.2,1)` (×14) — that is **Tailwind's default `ease-in-out`**, so this is a Tailwind build.

**The actual "premium" technique here** ✅ — the hero motion is not WebGL at all. It is **pre-rendered, compressed, CDN-hosted MP4**:

```
servd-linusbio-cs.b-cdn.net/production/videos/Hair-Slicing-hero-compressed.mp4
servd-linusbio-cs.b-cdn.net/production/videos/Ablation-Section-Compressed_2025-02-12-171852_vxrb.mp4
servd-linusbio-cs.b-cdn.net/production/videos/Spectrometry-Hero-Compressed_2025-02-12-171650_ayhy.mp4
```

**Decision-relevant read:** the cinematic feel is bought with *video + Tailwind + Alpine + GSAP scroll triggers*, which is roughly a weekend of work, not a shader pipeline.

---

### 1.1.5 Cross-site summary

| | Lisa (Locomotive) | Solarin (2016) | U24 Rebuild Map | LinusBio |
|---|---|---|---|---|
| Framework | none (vanilla modules) | RequireJS/Knockout | Angular CLI | Craft CMS + Alpine |
| Smooth scroll | **Lenis 1.1.9** | — | — | — |
| Animation | **GSAP 3.14.2** (+ScrambleText, SplitText, ScrollTrigger, Flip) | GSAP | — | GSAP 3.12.1 + ScrollTrigger |
| 3D | **three.js + custom GLSL** | WebGL | — | — (MP4 instead) |
| Page transitions | **Barba.js** | — | Angular router | — |
| Payload | 2.5 MB JS | n/a | 1.6 MB JS | **335 KB JS** |

The only library that appears on more than one modern site is **GSAP**. That is the toolkit's actual centre of gravity.

---

## 1.2 Lenis (smooth / inertia scroll)

**Owner:** darkroom.engineering (formerly Studio Freight). Repo https://github.com/darkroomengineering/lenis · site https://lenis.dev (the old `lenis.darkroom.engineering` 301s there).

**Current release** ✅ — **`lenis@1.3.26`, MIT** (npm registry, checked 2026-09-22).

```bash
npm i lenis
```
```html
<script src="https://unpkg.com/lenis@1.3.26/dist/lenis.min.js"></script>
```

**Core API** ✅ (from the repo README):

| Option | Default | Meaning |
|---|---|---|
| `duration` | `1.2` | scroll animation length (s) |
| `easing` | exponential | curve function |
| `lerp` | `0.1` | linear-interpolation intensity 0–1 |
| `orientation` | `"vertical"` | or `"horizontal"` |
| `smoothWheel` | `true` | smooth the mouse wheel |
| `syncTouch` | `false` | mimic touch scroll |
| `autoRaf` | `false` | run its own rAF loop |
| `wheelMultiplier` / `touchMultiplier` | `1` | input gain |
| `respectReducedMotion` | `true` | see below |

Two ways to drive it:

```js
// self-driven
const lenis = new Lenis({ autoRaf: true })
lenis.on('scroll', (e) => console.log(e))

// manual rAF
const lenis = new Lenis()
function raf(time) { lenis.raf(time); requestAnimationFrame(raf) }
requestAnimationFrame(raf)
```

**GSAP ScrollTrigger integration — the canonical snippet** ✅:

```js
const lenis = new Lenis()
lenis.on('scroll', ScrollTrigger.update)
gsap.ticker.add((time) => { lenis.raf(time * 1000) })
gsap.ticker.lagSmoothing(0)
```

This is the whole trick: Lenis owns the scroll position, GSAP's ticker owns the clock, and ScrollTrigger recalculates off Lenis's emitted scroll rather than the native one.

**Framework bindings** ✅: `lenis/react`, `lenis/vue`, `lenis/framer`, plus a `lenis/snap` sub-package.

**Accessibility / reduced motion** ✅ — verified in source, `packages/core/src/lenis.ts`:

```ts
// `.matches` is read at scroll time so preference changes apply live, no listener needed
private readonly reducedMotionMediaQuery = window.matchMedia(
  '(prefers-reduced-motion: reduce)'
)
...
respectReducedMotion = true,     // constructor default
...
scrollTo(...) { if (this.prefersReducedMotion) { /* jump, don't animate */ } }
```

So on current Lenis: smoothing is disabled and programmatic scrolls jump instantly when the user asks for reduced motion, and the preference is re-read live rather than latched at construction. `lenis.prefersReducedMotion` is readable at runtime. Opt out with `new Lenis({ respectReducedMotion: false })` — don't.
**Note the version gap:** Lisa ships **1.1.9**, which does not contain this option. If you copy Lisa, copy it from current Lenis, not from Lisa.

**Honest cost:** Lenis hijacks native scroll. That means it fights the OS scroll physics, breaks native scroll-anchoring behaviours in some cases, and adds a rAF loop for the page's lifetime. `lenis.dev` claims "under 5kb" and "no accessibility trade-offs" — the first is verifiable, the second is marketing. For a single-page portfolio, **native scroll + `scroll-behavior: smooth` for anchors** clears the bar without any of this.

---

## 1.3 GSAP + ScrollTrigger, and the 2025 licence change

### Licensing — the important nuance ✅

- **GSAP 3.13 shipped 29 April 2025**, and with it *all* formerly Club-only plugins became free: **SplitText, MorphSVG, DrawSVG, ScrollSmoother, ScrambleText, Inertia, Physics2D, GSDevTools, MotionPath, Flip, Draggable, Observer**. Source: https://gsap.com/blog/3-13/ and https://gsap.com/pricing/ ("GSAP is now 100% free for all users, thanks to Webflow's support"; footer: "A Webflow Product").
- **GSAP is free but it is NOT open source.** npm metadata for `gsap@3.15.0` reads:

  ```
  "license": "Standard 'no charge' license: https://gsap.com/standard-license."
  ```

  The licence (https://gsap.com/standard-license, effective **30 April 2025**, last modified **30 May 2025**, © 2025 Webflow) permits *"implementation and/or use of GSAP Products on any website, web application, or digital interface by any person or entity"*, including commercial use, but **prohibits** using GSAP inside *"tools that allow users to build visual animations without code that … competes with Webflow's visual animation building capabilities"*, prohibits reverse-engineering toward such a tool, and requires that you *"not remove or alter any proprietary notices or branding"*.
- **Current version** ✅: **`gsap@3.15.0`**, published **2026-04-13** (npm registry, checked 2026-09-22). Lisa ships 3.14.2.

For a personal portfolio this licence is a non-issue. Flagging it because "GSAP is free now" is routinely mis-stated as "GSAP is MIT now". It is not.

### ScrollTrigger ✅

Config surface (https://gsap.com/docs/v3/Plugins/ScrollTrigger/):

| Prop | What it does |
|---|---|
| `trigger` | element whose document position drives the trigger |
| `start` / `end` | `"top bottom"`, `"bottom top"`, `"+=500"` |
| `scrub` | `true` = bind progress to scrollbar; `1` = 1 s of smoothing lag |
| `pin` | lock an element for the active range (auto-adds padding) |
| `pinSpacing` | `false` to suppress that padding |
| `snap` | `0.1`, `"labels"`, or a function |
| `toggleActions` | 4 verbs for enter/leave/enterBack/leaveBack, e.g. `"play pause resume reset"` |
| `markers` | dev-only visualiser |
| `anticipatePin` | avoids the flash when pinning at high scroll velocity |
| `invalidateOnRefresh` | drop cached values and recompute from current state |
| `containerAnimation` | trigger inside a horizontally-scrolling (tweened) container |
| `onEnter` / `onLeave` / `onEnterBack` / `onLeaveBack` | callbacks receiving the instance (`progress`, `direction`) |

Canonical form:

```js
gsap.to(".box", {
  scrollTrigger: {
    trigger: ".box",
    start: "top center",
    end: "bottom center",
    scrub: 1,
    pin: true,
    onEnter: () => console.log("entered")
  },
  x: 500,
  duration: 2
});
```

**Performance model** ✅ — the docs state ScrollTrigger computes start/end positions **up front** rather than polling element positions, debounces scroll events, syncs updates to the refresh rate, and throttles resize recalculation. `ScrollTrigger.refresh()` re-measures after DOM/viewport changes and is normally automatic.

### `gsap.quickTo()` ✅ — the cursor/magnetic primitive

https://gsap.com/docs/v3/GSAP/gsap.quickTo()

```js
let xTo = gsap.quickTo("#id", "x", { duration: 0.4, ease: "power3" });
let yTo = gsap.quickTo("#id", "y", { duration: 0.4, ease: "power3" });
document.querySelector("#container").addEventListener("mousemove", (e) => {
  xTo(e.pageX);
  yTo(e.pageY);
});
```

Docs: *"if you find yourself calling `gsap.to()` many times on the same numeric property of the same target, like in a 'mousemove' event, you can **boost performance** by creating a quickTo() function instead."* It skips unit conversion, relative values, function-based values, plugin parsing and alias resolution, and pipes raw numbers straight at the property.

---

## 1.4 Native CSS scroll-driven animations — and when they replace JS

Spec: https://drafts.csswg.org/scroll-animations-1/ · MDN: https://developer.mozilla.org/en-US/docs/Web/CSS/CSS_scroll-driven_animations

**Syntax** ✅:

```css
/* anonymous scroll-progress timeline */
div { animation: bg linear; animation-timeline: scroll(nearest inline); }

/* anonymous view-progress timeline (element's visibility in its scrollport) */
.card { animation: reveal linear both; animation-timeline: view(); 
        animation-range: entry 0% cover 40%; }

/* named timelines */
main      { scroll-timeline: --main-timeline; }
div::after{ animation: shape linear; animation-timeline: --main-timeline; }
```

Supporting properties: `scroll-timeline-name` / `-axis`, `view-timeline-name` / `-axis` / `-inset`, `timeline-scope` (hoist a named timeline so non-descendants can use it), `animation-range` / `-start` / `-end` with the named ranges `cover`, `contain`, `entry`, `exit`.

Feature-detect:

```css
@supports not (scroll-timeline: --main-timeline) { /* fallback */ }
```

**Browser support, 2026** ✅ (Web Platform Status API `scroll-driven-animations`, and MDN browser-compat-data for `animation-timeline`, both checked 2026-09-22):

| Browser | Status |
|---|---|
| Chrome / Edge | **115** (2023-07-18) |
| Chrome Android | **115** |
| Safari / iOS Safari | **26** (2025-09-15) |
| **Firefox** | **`"version_added": "preview"`** — Nightly/flag only, NOT shipped |

Baseline: **`limited`**. Web-platform-tests stable scores: Chrome 0.845, Safari 0.839, **Firefox 0.098**. Mozilla's standards position is `positive`, Apple's is `support`, but as of today Firefox has not shipped it.

**When it replaces JS — honest rule:**
- ✅ **Replace GSAP with native CSS** for *progressive-enhancement decoration*: scroll progress bars, parallax on a decorative layer, reveal-on-enter, sticky-header shrink. These degrade to "no animation" in Firefox and nobody notices.
- ❌ **Don't replace GSAP** where the animation *is* the layout — pinned sections, horizontal scroll sections, anything where the fallback is a broken page. `position: sticky` + `animation-timeline` can emulate pinning, but the Firefox fallback is a page that reads wrong, not a page that reads plain.
- 🟡 CSS scroll-driven animations run **off the main thread** when animating compositor-friendly properties, which is their real advantage over any JS approach for INP (§1.10).

---

## 1.5 Three.js / R3F / WebGL — and the case for a 2D canvas instead

**Versions** ✅ (npm, 2026-09-22): `three@0.186.0` (MIT) · `@react-three/fiber@9.7.0` (MIT).
**WebGL2** is Baseline **widely available** (Chrome 56 / Firefox 51 / Safari 15). **WebGPU** is Baseline **limited** — Chrome 144 desktop (2026-01-13), Chrome Android 121, Safari 26, **no Firefox**. Don't build a portfolio on WebGPU yet.

**R3F performance guidance** ✅ (https://r3f.docs.pmnd.rs/advanced/scaling-performance):
- `frameloop="demand"` — render only when props change; the single biggest battery/fan win for a static-ish hero.
- `invalidate()` — request a frame after out-of-band mutations. *"Calling invalidate() will not render immediately, it merely requests a new"* frame.
- Share geometries/materials across meshes; `useLoader` is cached automatically across the tree.
- `InstancedMesh` — hundreds of thousands of objects in one draw call instead of thousands of meshes.
- `<PerformanceMonitor>` (drei) — watches average fps, fires `onIncline`/`onDecline` so you can scale DPR or drop effects.
- `regress()` — drop `performance.current` below 1 during interaction, scale resolution/effects down, restore when idle.
- `startTransition` for expensive work so heavy loads don't stall the frame.
- Never `setState` inside `useFrame`.

**Postprocessing** ⚠️ — an `EffectComposer` chain means at minimum one extra full-screen render target pass per effect, at device resolution. Bloom, DOF and SSAO are each an extra full-screen pass (bloom is several, because of the downsample/upsample pyramid). On a portfolio hero this is where the mobile frame budget dies. ❌ I did not find a first-party three.js page stating per-effect costs numerically; treat this as engineering judgement, not a cited number.

**When a 2D `<canvas>` generative background is the smarter lazy choice** — the reasoning, with the parts I can and cannot source:

- ✅ **A CSS gradient costs effectively nothing.** No render loop, no JS, composited.
- ⚠️ A canvas/SVG animation costs a slice of the main thread every frame; a WebGL fragment shader runs once per pixel per frame **for as long as the page is open**, which is a continuous mobile battery draw.
- ⚠️ Practical levers that apply to *both* canvas 2D and WebGL: render at half resolution and let CSS upscale (~3× saving); cap the loop at 30 fps (most background effects are indistinguishable, and it halves GPU work); a small canvas costs a fraction of a full-bleed one.
- ✅ The decisive structural argument: **three.js at `0.186.0` is ~600 KB+ before your scene code**, versus a 2D canvas generative background that is typically 30–80 lines with **zero dependencies**. For a single-page portfolio, a 2D canvas (or an MP4, per LinusBio in §1.1.4) buys ~90 % of the perceived production value for ~2 % of the payload and none of the WebGL context-loss, colour-management or mobile-GPU variance problems.
- ✅ **Pause it.** Use `IntersectionObserver` (Baseline widely available since 2019) to stop the loop when the canvas scrolls out, and `document.visibilityState` to stop it on tab blur. Neither is optional.

**Recommended ladder for a hero:** static image or CSS gradient → grain/noise overlay → 2D canvas generative → MP4 (`autoplay muted loop playsinline` + `poster`) → three.js. Stop at the first rung that carries the brief.

---

## 1.6 Text reveal techniques

### GSAP SplitText (free since 3.13) ✅

https://gsap.com/docs/v3/Plugins/SplitText/

```js
let split = SplitText.create(".split", { type: "words, chars" });
```

| Option | Behaviour |
|---|---|
| `type` | `"chars"`, `"words"`, `"lines"`, comma-separated. Default `"chars,words,lines"` |
| `mask` | `"lines"` / `"words"` / `"chars"` — wraps each in a clipping element, which is the whole "text slides up out of a mask" effect in one word |
| `aria` | `"auto"` (default): `aria-label` on the parent, `aria-hidden` on every split child. Also `"hidden"`, `"none"` |
| `autoSplit` | re-splits when fonts finish loading, or when width changes **and** `"lines"` is in `type` |
| `onSplit()` / `onRevert()` | callbacks; returning an animation from `onSplit` gets it auto-cleaned on re-split |
| `deepSlice` | default `true` — correctly subdivides a nested `<strong>`/`<a>` that wraps across lines |
| `smartWrap` | prevents mid-word breaks when splitting chars only |
| `linesClass` / `wordsClass` / `charsClass` | `"word++"` auto-increments (`word1`, `word2`, …) |
| `propIndex` | adds a CSS var per element, e.g. `--word: 1` — lets you do the stagger in pure CSS |
| `.revert()` | restores the original `innerHTML` |

**Font-loading caveat** ✅, quoted: *"If you split before your web fonts are ready, the layout may shift or misalign."* Fix: await `document.fonts.ready`, or set `autoSplit: true`.

**Accessibility** ✅ — SplitText's default `aria: "auto"` is the reason it beats hand-rolled char-splitting: hand-rolled splitting makes a screen reader read a headline one letter at a time.

**3.13 (2025-04-29) additions** ✅: `aria` handling, `mask`, `deepSlice`, `autoSplit`, `onSplit`/`onRevert`, better emoji/non-Latin handling, standalone mode, and a **~50 % smaller file**.

### CSS-only alternatives

- **Mask reveal without JS:** wrap each line in an `overflow: hidden` (or `clip`) parent and translate the inner span. Combined with `animation-timeline: view()` (§1.4) this is a zero-JS line reveal — with the Firefox caveat.
- **`::before`/`::after` wipe masks:** an absolutely-positioned pseudo-element over the text, transitioned on `transform: scaleX()` with `transform-origin` flipping between enter and exit. Cheap, compositor-only.
- **Variable fonts:** animating `font-variation-settings` (weight/width/optical size) on hover or scroll gives a reveal that no template ships, at the cost of one font file. ⚠️ Animating variation settings is *not* compositor-friendly (it triggers layout); keep it to small, discrete, user-triggered moments.

### `text-wrap` ✅ (Web Platform Status API, 2026-09-22)

| Value | Baseline | Support |
|---|---|---|
| `text-wrap: balance` | **newly available** since 2024-05-13 | Chrome 114 · Firefox 121 · Safari 17.5 |
| `text-wrap: pretty` | **limited** | Chrome 117 · Safari 26 (2025-09-15) · **no Firefox** (WPT score 0) |

Practical rule: **`balance` on headings** (it's everywhere now, and it's the single cheapest thing that makes type look art-directed); **`pretty` on body copy** as pure progressive enhancement (it only kills orphans — nothing breaks in Firefox). `balance` is spec'd to bail out above a small line count, so don't put it on paragraphs.

---

## 1.7 View Transitions API

Spec: https://drafts.csswg.org/css-view-transitions-1/ and `-2/` · MDN: https://developer.mozilla.org/en-US/docs/Web/API/View_Transition_API

**Same-document (SPA):**

```js
const viewTransition = document.startViewTransition(() => { updateDOM(); });
viewTransition.ready.then(() => { /* animation about to run */ });
viewTransition.finished.then(() => { /* done */ });
viewTransition.skipTransition();
```

**Cross-document (MPA)** — both pages must opt in:

```css
@view-transition { navigation: auto; }
```

Name the participants:

```css
.hero-image { view-transition-name: hero; }
.caption    { view-transition-name: caption; }
```

Pseudo-element tree you animate against:

```
::view-transition
└─ ::view-transition-group(name)
   └─ ::view-transition-image-pair(name)
      ├─ ::view-transition-old(name)
      └─ ::view-transition-new(name)
```

**Chrome specifics** ✅ (https://developer.chrome.com/docs/web-platform/view-transitions/cross-document):
- `navigation: auto` covers `traverse`, `push`, `replace` — **not** reloads or address-bar navigations.
- **Same-origin only** (scheme + host + port), and **no intermediate cross-origin redirect**.
- `pageswap` (fires before the old page's last frame) and `pagereveal` (fires after the new page initialises, before first render) — Chrome 124+. Both expose `e.viewTransition`, and *"you can decide to skip the transition in both events."*
- `navigation.activation` (Chrome 123+) exposes old/new history entries so you can style by direction.
- **Types**: `@view-transition { types: slide, forwards; }` or `e.viewTransition.types.add(t)` in `pagereveal`, then select with `:active-view-transition-type()`.
- Render-blocking to avoid a flash of half-built page: `<link rel="expect" blocking="render" href="#section1">` — Chrome's own doc warns this *"blocks fundamental incremental rendering; measure Core Web Vitals impact before use."*
- Pair with the **Speculation Rules API** for prerender so the new document is ready.

**Browser support, 2026** ✅ (Web Platform Status API):

| Feature | Baseline | Chrome | Safari | Firefox |
|---|---|---|---|---|
| **View transitions (same-doc)** | **newly available, 2025-10-14** | 111 (2023-03-07) | 18 (2024-09-16) | **144 (2025-10-14)** |
| **Cross-document view transitions** | **limited** | 126 (2024-06-11) | 18.2 (2024-12-11) | **not shipped** (WPT 0.05) |
| **Speculation Rules** | **limited** | 109 | **not shipped** | **not shipped** |

Same-document view transitions crossed into Baseline "newly available" in **October 2025** — they are now a reasonable default for a single-page portfolio's section/route changes. Cross-document is Chrome+Safari only, so treat MPA transitions as pure enhancement.

**Always gate it:**

```js
if (!document.startViewTransition) { updateDOM(); return; }
document.startViewTransition(() => updateDOM());
```
```css
@media (prefers-reduced-motion: reduce) {
  ::view-transition-group(*),
  ::view-transition-old(*),
  ::view-transition-new(*) { animation: none !important; }
}
```

---

## 1.8 Custom cursors, magnetic buttons, easing

### Custom cursors ✅

Canonical technique (Codrops, https://tympanus.net/codrops/2019/01/31/custom-cursor-effects/):
1. `position: fixed` element, offset by half its size (`left: -2.5px; top: -2.5px` for a 5 px dot).
2. Hide the native cursor: `.page, .page a { cursor: none; }`
3. A `requestAnimationFrame` loop lerping toward the real pointer:
   ```js
   lastX = lerp(lastX, clientX, 0.2);
   lastY = lerp(lastY, clientY, 0.2);
   ```
   0.2 = move 20 % of the remaining distance per frame → the trailing/lag feel.
4. "Sticky" hover: when over an interactive element, lerp toward the element's **centre** (`stuckX`, `stuckY`) rather than toward the pointer. That is the same maths as a magnetic button, applied to the cursor instead of the button.

The modern replacement for the hand-written lerp loop is `gsap.quickTo()` (§1.3) — `duration: 0.2–0.4, ease: "power3"` is the conventional feel.

**Caveats the tutorial does not mention** (and which matter more than the effect):
- `cursor: none` removes the OS cursor for **everyone**, including users who rely on cursor size/contrast accessibility settings. Gate it: `@media (hover: hover) and (pointer: fine)`.
- Gate it again on `prefers-reduced-motion: reduce` — a lagging cursor is motion.
- Touch devices must never see it.
- It is also, per §2, a *recognised AI-slop tell* when it's a purposeless floating dot (see "Cursor follower dots" and slop-gate 45). A custom cursor earns its place only when it carries information (a "drag" affordance, a "view project" label, a magnifier).

### Magnetic buttons ⚠️

The standard implementation: on `mousemove` within the button's bounds, translate the button (and usually its label at a lower factor, for parallax) by a fraction of the pointer's offset from the button centre; on `mouseleave`, tween back to 0. `gsap.quickTo` on `x`/`y` per element is the performant form. ❌ No single authoritative first-party spec for this — it's folklore codified in tutorials. The only load-bearing rules: animate `transform` only, cap the displacement (~10–25 % of half-width), and disable under `(pointer: coarse)` and reduced motion.

### Easing ✅

- **`linear()` easing function** — Baseline **widely available** since 2026-06-11; shipped Chrome 113 (2023-05-02), Firefox 112 (2023-04-11), Safari 17.2 (2023-12-11). This means you can now express **spring and bounce curves in pure CSS** by approximating them as a many-stop `linear()` — no JS spring library needed:
  ```css
  --ease-spring: linear(0, 0.006, 0.025 2.8%, 0.101 6.1%, 0.539 18.9%, 0.721 25.3%, 0.849, 0.937 34.6%, 1.007 41.6%, 1.033, 1.036, 1.02, 1.001, 0.991 63.5%, 0.998 79%, 1);
  ```
- **cubic-bezier conventions worth stealing** — measured off Lisa's production CSS:
  - `cubic-bezier(0.215, 0.61, 0.355, 1)` — easeOutCubic, the workhorse (43 uses)
  - `cubic-bezier(0.23, 1, 0.32, 1)` — easeOutQuint, for larger/slower moves (9 uses)
  - and off LinusBio: `cubic-bezier(.4, 0, .2, 1)` — Tailwind's default `ease-in-out`
- **Consensus on curve choice** ✅ (https://emilkowal.ski/ui/great-animations): prefer **`ease-out`** — *"starts fast and slows down at the end, which gives the impression of a quick response."* Durations *"usually shorter than 300ms"*. Animations must be **interruptible**. *"Never animate keyboard initiated actions."* Animate **`transform` and `opacity` only**.
- Rauno Freiberg's Web Interface Guidelines (https://interfaces.rauno.me/) is tighter still: *"Animation duration should not be more than 200ms for interactions to feel immediate."* Scale subtly (0.8→1 for dialogs, 1→0.96 for buttons), not 0→1.

**Vercel Labs' Web Interface Guidelines** ✅ (https://github.com/vercel-labs/web-interface-guidelines, `AGENTS.md`), Animation section, verbatim:

```
- MUST: Honor `prefers-reduced-motion` (provide reduced variant or disable)
- SHOULD: Prefer CSS > Web Animations API > JS libraries
- MUST: Animate compositor-friendly props (`transform`, `opacity`) only
- NEVER: Animate layout props (`top`, `left`, `width`, `height`)
- SHOULD: Animate only to clarify cause/effect or add deliberate delight
- SHOULD: Choose easing to match the change (size/distance/trigger)
- MUST: Animations interruptible and input-driven; autoplay only for muted, non-essential loops
- MUST: Autoplay motion >5s alongside other content has pause, stop, or hide controls
- MUST: Correct `transform-origin` (motion starts where it "physically" should)
- MUST: SVG transforms on `<g>` wrapper with `transform-box: fill-box`
```

Install: `npx skills add https://github.com/vercel-labs/agent-skills --skill web-design-guidelines`.

---

## 1.9 Other platform features worth knowing (2026 support) ✅

| Feature | Baseline | First shipped |
|---|---|---|
| `prefers-reduced-motion` | **widely** since 2022-07-15 | Safari 10.1 (2017-03-27) |
| `backdrop-filter` | **newly** since 2024-09-16 | Chrome 76; **Safari only 18** |
| `content-visibility` | **newly** since 2025-09-15 | Chrome 108, FF 130, Safari 26 |
| IntersectionObserver | **widely** since 2021 | Chrome 58 |
| WebGL2 | **widely** since 2024-03-20 | Safari 15 |
| WebGPU | **limited** | Chrome 144 desktop, Safari 26, **no Firefox** |

Note `backdrop-filter` only reached Safari in **September 2024** — which is part of why glassmorphism suddenly became ubiquitous, and part of why it now reads as dated (§2).

---

## 1.10 Performance: what these effects actually cost

### The metrics ✅

- **LCP** (https://web.dev/articles/lcp): *"Good LCP values are 2.5 seconds or less"* at the **75th percentile** across mobile and desktop; **> 4.0 s is poor**. LCP includes previous-page unload, connection setup, redirects and other TTFB delays.
- **INP** (https://web.dev/articles/inp): **≤ 200 ms good**, **200–500 ms needs improvement**, **> 500 ms poor**, at the **75th percentile**. Three phases: **input delay** (blocking work before handlers run) → **processing duration** (handler execution) → **presentation delay** (until the next frame paints). Main causes: long tasks, large/complex layouts, layout thrashing, expensive style recalculation, oversized DOM, client-side-rendering delays.

### How each technique hits those metrics

| Technique | LCP | INP | Mitigation |
|---|---|---|---|
| **2.5 MB JS bundle** (Lisa) | severe — parse/compile blocks the main thread | severe input delay | code-split, defer everything non-hero, `type="module"` |
| **Lenis** | none | adds a permanent rAF loop; scroll handlers become main-thread work | `autoRaf: false` and drive off GSAP's ticker (one loop, not two) |
| **ScrollTrigger** | none | pre-computed positions + debounced scroll keeps it cheap; `ScrollTrigger.refresh()` on resize is the expensive moment | batch refreshes, `invalidateOnRefresh` only where needed |
| **three.js hero** | large — ~600 KB+ before your scene | GPU work competes with input handling; shader compile is a long task | `frameloop="demand"`, instancing, `PerformanceMonitor` + DPR scaling, lazy-init after LCP |
| **Postprocessing** | none | one+ full-screen pass per effect per frame | drop effects on `onDecline`; skip entirely on `(pointer: coarse)` |
| **SplitText on the H1** | can cause CLS if fonts load late | negligible | `await document.fonts.ready` or `autoSplit: true` |
| **`backdrop-filter`** | none | forces a backdrop re-render of everything behind it each frame; expensive when animated or stacked | never animate it; never stack it; prefer a translucent solid |
| **CSS scroll-driven animation** | none | **runs off the main thread** for compositor props | the reason to prefer it where support allows |
| **Custom cursor rAF loop** | none | a per-frame main-thread write; harmless alone, compounding with others | `gsap.quickTo`, gate on `(hover: hover)` |

### The mitigations award sites actually use ✅

1. **Never lazy-load the LCP element.** Hallmark's anti-pattern file cites: lazy-loaded LCP images show **p75 720 ms vs 364 ms** for preloaded — 2× slower, 4× more "poor" experiences. Use `fetchpriority="high"`; reserve `loading="lazy"` for below-the-fold media. ⚠️ I could not reach Google's own page for that statistic (the Lighthouse URL 404s), so treat the exact figures as secondary.
2. **Hero video, not hero shader** (LinusBio) — `<video autoplay muted loop playsinline poster>` with a CDN-compressed MP4 is decoded off the main thread and costs nothing in JS.
3. **Pause everything offscreen** — IntersectionObserver + `visibilitychange`.
4. **Render at half DPR and let CSS upscale.**
5. **`content-visibility: auto`** on long below-the-fold sections (Baseline newly available since 2025-09-15).
6. **Preconnect/preload the display font**, and split text only after `document.fonts.ready`, or you trade a nice reveal for CLS.

---

# Part 2 — The concrete tells of "AI-generated slop" frontend, and countermeasures

## 2.1 The origin story, sourced ✅

**Adam Wathan** (creator of Tailwind CSS), on X, **August 2025** (post id 1953510802159219096, ~1 M views):

> *"I'd like to formally apologize for making every button in Tailwind UI `bg-indigo-500` five years ago, leading to every AI generated UI on earth also being indigo."*

https://x.com/adamwathan/status/1953510802159219096

The mechanism is a training feedback loop: Tailwind UI shipped indigo as its neutral placeholder accent → thousands of tutorials, starters and open-source projects copied it → models trained on that corpus → model outputs got republished → the next training round contained even more indigo.

## 2.2 Empirical measurement — how widespread it actually is ✅

**Adrian Krebs, "Scoring 500 Show HN pages for AI design slop"** (https://www.adriankrebs.ch/blog/design-slop/) — the only quantitative study I found, and it's deterministic rather than vibes:

- **Method:** Playwright headless browser loads each site; an in-page script reads the DOM and **computed styles**. Explicitly *not* screenshots or LLM image judgement. Manual QA put false positives at ~5–10 %.
- **Corpus:** **1,590 Show HN submissions.**
- **16 detection patterns** across four categories:
  - *Fonts:* Inter; Space Grotesk / Instrument Serif pairings; serif-italic accents
  - *Colors:* purple tones; dark mode with grey text; low-contrast body text; gradients; coloured glows/shadows
  - *Layout:* centred heroes; badges above headlines; coloured card borders; icon-topped feature grids; numbered step sequences; stat banners; emoji navigation; all-caps labels
  - *CSS:* shadcn/ui components; glassmorphism
- **Results, verbatim:** *"High (4+ patterns): 22% (347 sites); Medium (2-3 patterns): 32% (508 sites); Low (0-1 patterns): 46% (735 sites)"* — **54 % of Show HN pages trigger 2 or more tells.**

The companion tool codifies **14 named patterns** (https://github.com/AdrianKrebs/ai-design-checker): templated display fonts (Space Grotesk, Instrument Serif, Geist, Syne, Fraunces) · hero font mix · "vibe purple" (indigo/violet accent) · gradients · accent stripe · glassmorphism (`backdrop-blur`) · coloured glow box-shadow · emoji nav · centred + Inter · perma-dark · numbered steps · stat banner · headline badge · FAQ accordion. Per-pattern rules live in `src/patterns/<id>.js`.

## 2.3 The full tell catalogue

The most complete public catalogue is **https://github.com/febbhav/signs-of-ai-design**. Quoted descriptions below are from it unless noted; ⚠️ it is a community artifact, not a vendor doc, but it is specific, falsifiable, and matches what the two independent codified sources (Anthropic's `frontend-design` skill and Nutlope's `hallmark`) say.

### Colour
| Tell | Description |
|---|---|
| **Purple→indigo gradient** | *"Indigo-to-violet hero washes and gradient buttons, typically built from Tailwind's `indigo-500`"* |
| **Gradient text headings** | *"Gradient fill clipped to headings and to big metric numbers, carrying no meaning"* — `background-clip: text`. Hallmark: *"Signals 'AI generated' faster than almost anything else."* |
| **Neon-on-dark with glow** | *"Cyan, violet, or pink accents on near-black backgrounds, with colored box shadows"* |
| **The emerald fallback** | *"When a prompt bans purple, models cascade to emerald (#10B981)"* — i.e. banning one colour doesn't fix the problem |
| **Cream + terracotta "tasteful"** | Anthropic's own skill flags this as a tell *about Claude specifically*: a cream background near **`#F4F1EA`** with a high-contrast serif display and a **`#D97757`** clay accent — *"Anthropic's own Claude-interaction accent, so on a user's brief it reads as a tell"* |
| **Timid evenly-weighted palettes** | *"Several muted colors at equal visual weight, with no single dominant color"* |
| **Pure `#000` / `#fff`** | Hallmark: *"Both read as flat and synthetic."* |

### Typography
| Tell | Description |
|---|---|
| **Inter everywhere** | *"Inter (or a system sans) as the only typeface on the page."* Hallmark: *"A one-font page is a template page."* |
| **Geist / Space Grotesk / Instrument Serif** | *"Geist has been called the new Inter"*; *"Instrument Serif is the newest reflex"* |
| **Oversized italic serif display** | *"A huge italic serif hero headline, or a single serif-italic accent word."* Hallmark makes this an auto-fail (gate 38a): *"Italic headers — above all the single italicised emphasis-word inside an upright headline — are a top AI tell."* |
| **Single family, single weight** | Flat hierarchy across the whole page |
| **Monospace as decoration** | *"Body copy or ordinary labels set in a code font for hacker atmosphere"* |
| **All-caps eyebrow labels** | Anthropic's skill: *"a tracked-out ALL-CAPS eyebrow label above every heading"* |
| **Title Case Everything** | Every heading, button, label and chart title |
| **Accenting one word in a headline** | Anthropic's skill lists this first among *"the commonest tells of a generated page"* |

### Layout & structure
| Tell | Description |
|---|---|
| **The full hero formula** | *"Centered stack: badge, a full sentence set at 64 pixels or larger, one-line subhead"* + `min-height: 100vh` |
| **The three-card feature row** | *"Exactly three equal cards below the hero, each with an icon on top"* |
| **Cookie-cutter page order** | *"Hero, logo wall, three-card features, testimonial carousel, stats row, pricing table"* |
| **The AI nav** | Hallmark: wordmark-left + 4–5 inline links + CTA-right + full-width + sticky + white + 1 px hairline border-bottom. *"When the nav can't tell you what kind of site you're on, the page is templated."* |
| **The AI footer** | 4 link columns (Product/Company/Resources/Legal) + social row + tiny copyright + hairline top border |
| **Eyebrow chip / headline badge** | *"A tiny uppercase tracked label, or a pill badge ('New', 'v2.0 is here')"* |
| **Numbered markers 01/02/03** | Anthropic's skill: *"that's only appropriate if the content actually is a sequence"* |
| **Bento grid** | *"An asymmetric boxed grid, often dark with accent-colored tiles"* |
| **Gradient orbs / aurora blobs** | *"Abstract purple or violet gradient blobs floating behind the hero"* |
| **Monotonous spacing** | *"One spacing value everywhere, identical section padding top to bottom"* |
| **Cards inside cards** | *"Every content block boxed, then boxes nested inside boxes"* |

### Components
| Tell | Description |
|---|---|
| **`rounded-2xl` everything** | *"One large border radius (16 to 24 pixels) applied to every card, input, button"* |
| **The untouched shadcn card** | *"`rounded-2xl shadow-lg p-6`, the default muted primary color"* |
| **The ghost card** | *"A hairline border paired with a wide diffuse shadow on the same card"* — two edge treatments at once |
| **Coloured left-border strip** | *"A three or four pixel colored border on one side of an ordinary card"* |
| **Reflexive glassmorphism** | *"Frosted-glass blur on cards, modals, and navs where there is no layering problem"* |
| **Icon tile above heading** | *"A small rounded-square icon container above a heading"* |
| **Re-drawn UI chrome** | Hallmark gate 47: hand-built fake browser bars (URL pill + traffic-light dots), fake phone frames, fake terminal/IDE chrome. *"The model invented a UI that already exists in the user's environment."* |

### Icons
| Tell | Description |
|---|---|
| **"The Lucide five"** | *"Sparkles for AI, Zap for fast, Shield for secure, Check for benefits"* — plus `Brain`, `ArrowRight` |
| **The sparkle glyph** | *"The four-point sparkle as a universal AI badge on features"* |
| **Emoji as feature icons** | *"A rocket, gear, sparkle, or check emoji standing in for designed icons"* |
| **Mixed icon libraries** | Hallmark gate 30: Material + Heroicons + Lucide on one page |

### Fake / dead content
| Tell | Description |
|---|---|
| **Animated stat counters & implausible numbers** | *"A horizontal stat banner with numbers counting up on scroll"* |
| **Invented metrics** | Hallmark gate 46: *"'10× faster', 'saves 5 hours per week', 'trusted by 50,000+ teams', '99.9 % uptime', '+47 % conversion'"* fabricated to fill a proof slot |
| **Logo soup** | *"A grayscale wall of client or partner logos mid-page"* |
| **Fake testimonials** | *"A grid of one-sentence broad praise from first-name-only or generated people"* |
| **Fabricated trust chrome** | *"Compliance badges for audits that never happened, invented user counts"* |
| **Three-tier pricing, highlighted middle** | *"Most Popular" badge on the middle tier* |
| **Footer fingerprints** | *"a generator attribution like 'Built with v0'"* |
| **Dead buttons** | Hallmark enforces the inverse: every interactive element must ship **all 8 states** — default · hover · `:focus-visible` · `:active` · disabled · loading · error · success |

### Motion
| Tell | Description |
|---|---|
| **The same fade-in on everything** | *"An identical fade-up entrance on every section, scroll-triggered."* Anthropic's skill: *"fade-and-slide-up entrances on each section and hover transitions on every card are the generic default and read as AI-generated."* |
| **Bounce / elastic easing on UI** | Hallmark gate 12 flags `cubic-bezier(0.34, 1.56, …)` on buttons, modals, tooltips |
| **`transition-all`** | gate 10 — name the properties |
| **Universal `hover:scale-105`** | gate 11 |
| **Multiple simultaneous hover effects** | gate 13 — translate + scale + shadow + colour + rotate on one element |
| **Animating layout props** | gate 14 — `width`, `height`, `top`, `left`, `margin`, `padding` |
| **Focus rings that fade in** | gate 15 — keyboard users need it instantly |
| **Cursor follower dots** | listed as a microinteraction tell in its own right |
| **Motion incoherence** | *"buttons that snap next to cards that animate"* |

### Copy
| Tell | Description |
|---|---|
| **The weightless headline** | *"'Build faster. Ship smarter.' Grammatically perfect, could describe any product"* |
| **The buzzword layer** | *"'streamline', 'supercharge', 'empower'"*; hallmark adds *"Elevate / Seamless / Powerful"* |
| **Em-dash density** | *"Em dash frequency several times the human baseline"* |
| **Arrow glyph welded to buttons** | Anthropic's skill: *"a '→' appended to link and button text"* |
| **Middle-dot meta strings** | *"meta strings joined with middle dots ('A · B · C')"* |
| **Placeholder names / startup clichés** | Hallmark gate 19: "Jane Doe / John Smith", "Acme, Nexus, Seamless, Unleash" |
| **Tinted near-black standing in for black** | `#0B0B0B`, `#111` |

## 2.4 What the vendors themselves say

- **Anthropic** ships this as a first-party skill (`frontend-design`, in `claude-plugins-official`). Its calibration list of *"AI-generated design right now clusters around"* five traits is quoted throughout above. Its structural point is the sharpest thing I found on the subject:

  > *"All traits are legitimate for some briefs, but they are defaults rather than choices, and they appear regardless of subject."*

- **Vercel Labs** ships `web-interface-guidelines` (129 README bullets / 107 `AGENTS.md` MUST-SHOULD-NEVER rules / 103 command rules) and a `web-design-guidelines` skill, plus Vercel Agent code review reading `AGENTS.md` / `CLAUDE.md` / `.cursorrules`. https://vercel.com/changelog/web-interface-guidelines-now-available-as-an-agent-command
- ❌ I could **not** find a first-person statement from shadcn (the shadcn/ui maintainer) on AI slop specifically. The commonly repeated framing — "shadcn defaults left untouched" — is community observation, and the codified rule sets (hallmark, signs-of-ai-design, ai-design-checker) all encode it, but no maintainer quote. Flagged rather than fabricated.
- ❌ The claimed *New Yorker* piece naming companies with a *"Claudian sameness"* surfaced only in a search summary; I could not fetch the article. Do not cite it.

## 2.5 Countermeasures — what the codified sources actually prescribe

These are the fixes as stated by the primary sources, not general advice.

### Commit to one point of view
> *"Spend your boldness in one place. Let one element be the memorable thing, keep everything around it quiet and disciplined, and cut any decoration that does not serve the brief."*
> — Anthropic `frontend-design` skill

And the closing test, quoting Chanel: *"before leaving the house, take a look in the mirror and remove one accessory."*

### Ground the design in the subject matter, not in "modern web design"
> *"The subject's industry, subject matter, materials, and vernacular are where distinctive visual choices come from — a design for a toy for girls aged 8–11 will be very aesthetically different from a dashboard for financial analysts."*

### Two-pass process with an explicit uniqueness check
Anthropic's prescribed loop: (1) brainstorm a compact token plan — 4–6 named hex values, typeface roles, an ASCII-wireframe layout concept, and a principles list; (2) **review that plan against the brief before writing code**, and *"work through a similar prompt to see if you arrive somewhere similar"* — if you do, revise and say what changed and why. Only then write code.

### Restrained palette, one accent, tinted neutrals
Hallmark's gates make this checkable:
- **gate 22** — no zero-chroma neutrals: *"Pure greys read as flat. Tint every neutral toward the anchor hue — minimum 0.005 chroma."*
- **gate 23** — *"Does the accent colour cover more than ~5 % of any single viewport?"* If yes, retreat. *"Accent is for emphasis, not for filling."*
- **gate 2** — no purple→blue gradient anywhere, *"including a `background-clip: text` gradient headline"*. **No genre allows gradient text.**

### Break the symmetry deliberately
- **gate 6** — *"Pick at most two centred elements and break alignment for the rest; the eyebrow or CTA should sit off-axis."*
- **gate 3 fix** — *"Break the grid. Vary column widths. Mix card heights. Remove one card and use negative space. Move the icons inline, not above. Or drop the cards entirely and use typographic rhythm."*
- **gate 9** — sections must not be separated only by equal whitespace; earn a rule, an ornament, or a colour shift.
- **gate 24** — every spacing value on a named scale; *"Arbitrary `padding: 17px` is a tell"* (note: the tell is *arbitrariness*, not asymmetry — deliberate asymmetry comes from the scale, not from noise).

### Real texture over synthetic gloss
- Aurora-blob fix: *"Solid surface. Or a subtle two-stop CSS gradient + SVG `<feTurbulence>` grain at < 0.1 opacity."*
- Anti-pattern *"Plastic illustrations and generated headshots"* → *"Commission illustration or use authentic photography aligned with brand."*
- ⚠️ Community consensus (weaker sourcing) adds: use **real scanned** paper/film grain rather than a generated noise filter, because real surfaces have irregular structure that generators don't reproduce; keep texture as an accent layer, not a foundation.

### Unusual type pairings, and a hard cap
- **gate 37** — at most **three** `font-family` families: `--font-display`, `--font-body`, and at most one outlier. A fourth is slop. Mono counts as a family if used for anything non-code.
- **gate 38** — the outlier face may appear in **at most two slots** (wordmark + hero stat, or wordmark + masthead, or hero stat + pull quote). Three slots means it has become a third body font.
- **gate 38a** — headings and display type are **roman**. Emphasis comes from weight, accent colour, or a drawn underline.
- Anthropic: one family or two, *"and if two, make them clearly distinct."* Line length **< 80 characters** by default; serif body copy gets slightly more line-height than sans.

### Real data over fake
- **gate 46** — any fabricated quantitative claim is an auto-fail. The permitted fixes are: replace the number with `—` plus a labelled grey block, ask the user for the real metric, or **rebuild the section without the proof slot**. Also: *"A stat is never the hero's sole headline."*
- Hallmark's SKILL.md states it as a standing discipline: *"Honest copy — no fabricated content. If the user did not supply a metric, do not invent one."*

### Working interactions, not decorative ones
- **8 states mandatory** for every interactive component: default · hover · `:focus-visible` · `:active` · disabled · loading · error · success.
- **gate 26** — a component with only default + hover fails.
- **gate 27** — *"Is there any `transform` / `animation` keyframe that is NOT covered by a `@media (prefers-reduced-motion: reduce)` fallback?"*
- **gate 17** — tooltip hover delay 800–1000 ms; **focus delay 0 ms**. Not the same number.
- **gate 18** — auto-rotating content must pause on hover **and** focus (WCAG 2.2.2).
- **gate 33** — every decorative `<svg>`, `<canvas>` or CSS-art `<div>` needs `aria-label` **or** `aria-hidden="true"`. *"Skipping this is the new accessibility tell."*
- **gate 40** — contrast: body text (< 24 px regular or < 18 px bold) needs **4.5:1 / APCA Lc ≥ 60**; large text, icons and focus rings need **3:1 / APCA Lc ≥ 45**.
- Rauno: *"Box shadow should be used for focus rings, not outline which won't respect radius."* · *"Inputs should be wrapped with a `<form>` to submit by pressing Enter."* · *"Font size for inputs should not be smaller than 16px to prevent iOS zooming on focus."* · *"Buttons should be disabled after submission to avoid duplicate network requests."*

### Idiosyncratic details that read as human
- **gate 45** — *"Decoration must be motivated: a cursor inside a typed command (signals 'you'd type next'), a numeral that names an issue / year / version / chapter, a gradient that responds to interaction, a stamp that names an authorship or date. Random ornaments … are slop."*
- Anthropic: *"Structural devices like outlines, borders, numbering, eyebrows, dividers, labels, etc., encode useful information about the content rather than decorate it."*
- Motion: *"A single orchestrated moment — one page-load sequence or one reveal — lands better than scattered effects."*
- Typographic micro-craft that models skip (hallmark "Minor" tier): curly quotes not straight, real em dashes not `--`, `…` not `...`, `tabular-nums` on numeric tables, no `z-index: 9999`, no `100vw` widths.

### The structural countermeasure (the strongest single idea)
Hallmark's differentiator is worth stating in full because it goes beyond palette swaps:

> *"Hallmark insists on **structural variety**, not just visual variety. Two pages by Hallmark for two different briefs should not share the same hero → 3-feature → CTA → footer rhythm. They should feel like different sites, not different colour-swaps of the same template."*

It enforces this with a stamp written into the CSS (`/* Hallmark · macrostructure: <name> · … */`) and a project log, so the *next* generation must pick a different macrostructure. Whatever tool you use, the transferable idea is: **the tell is the shape of the page, and a palette change does not fix a shape.**

## 2.6 A 10-minute self-audit for this portfolio

1. Search the CSS for `gradient` — if any hit is on a heading or a hero background, delete it.
2. Search for `indigo`, `violet`, `purple`, `#6366f1`, `#8b5cf6`, `#10b981`, `#D97757`, `#F4F1EA`.
3. Count `font-family` declarations. > 3 → cut.
4. Is any heading italic? → make it roman.
5. Count `border-radius` values. One value everywhere → differentiate by component role.
6. Search `backdrop-filter` / `backdrop-blur` — is there an actual layering problem at each site? No → remove.
7. Is the hero `100vh` + fully centred? → break one axis.
8. Is there a 3-equal-column icon grid? → remove one, or vary widths.
9. Tab through the page. Every focusable thing has a visible ring that appears **instantly**? Any button that does nothing?
10. Is every number on the page real?
11. `@media (prefers-reduced-motion: reduce)` present and actually covering every keyframe?
12. Run https://github.com/AdrianKrebs/ai-design-checker against the deployed URL.

---

# Part 3 — Figma → code pipeline in 2026

## 3.1 Figma MCP server

Primary docs: https://developers.figma.com/docs/figma-mcp-server/ · help centre https://help.figma.com/hc/en-us/articles/32132100833559-Guide-to-the-Figma-MCP-server · official guide repo https://github.com/figma/mcp-server-guide

### Remote vs desktop ✅

| | **Remote (recommended)** | **Desktop (local)** |
|---|---|---|
| Endpoint | `https://mcp.figma.com/mcp` | `http://127.0.0.1:3845/mcp` |
| Requires desktop app | no | yes |
| Availability | *"available on all seats and plans"* | *"a Dev or Full seat"* on *"all paid plans"* |
| Selection-based prompting | ✗ — *"The remote server requires a link to a frame or layer"* | ✓ — *"Selection-based prompting only works with the desktop MCP server"* |
| Write-to-canvas | ✓ (remote-only) | ✗ |
| Required for | — | Figma for Government |

Figma's own guidance: *"Only clients listed in the Figma MCP Catalog can connect to the Figma MCP Server"* (there is a waitlist for others), and the remote server *"provides the broadest set of features."*

### Exact setup ✅

**Claude Code** — plugin route (preferred):
```
claude plugin install figma@claude-plugins-official
```
Manual:
```
claude mcp add --transport http figma https://mcp.figma.com/mcp
```
Add `--scope user` to make it global:
```
claude mcp add --scope user --transport http figma https://mcp.figma.com/mcp
```
Then `/mcp` → select `figma` → **Authenticate** (OAuth).

**VS Code** — `mcp.json` (⌘⇧P → "MCP: Open User Configuration" or "MCP: Open Workspace Folder MCP Configuration"):
```json
{
  "inputs": [],
  "servers": {
    "figma": {
      "url": "https://mcp.figma.com/mcp",
      "type": "http"
    }
  }
}
```

**Generic `.mcp.json`** (from Figma's own `figma/mcp-server-guide` repo):
```json
{
  "mcpServers": {
    "figma": {
      "url": "https://mcp.figma.com/mcp"
    }
  }
}
```

**Cursor** — `/add-plugin figma`, or deep link `cursor://anysphere.cursor-deeplink/plugin/add?id=657`.
**Codex** — `codex mcp add figma --url https://mcp.figma.com/mcp`.
**Xcode** (27 beta+) — `xcode://agent-plugin-clone?repo=https%3A%2F%2Fgithub.com%2Ffigma%2Fmcp-server-guide`.
❌ The remote-installation page carries **no** Windsurf or Zed instructions, despite the help-centre page listing them as compatible editors.

### Tools exposed ✅

https://developers.figma.com/docs/figma-mcp-server/tools-and-prompts/

**Read (design → code):**

| Tool | Returns | Availability |
|---|---|---|
| `get_design_context` | React + Tailwind representation of the selection, steerable to other frameworks | desktop + remote (selection-based on desktop only) |
| `get_metadata` | *"Sparse XML representation of your selection containing just basic properties such as the layer IDs, names, types, position and sizes"*; param `nodeId` | desktop + remote |
| `get_screenshot` | PNG (base64 or URL) | desktop + remote |
| `get_variable_defs` | *"Variables and styles used in your Figma selection, such as colors, spacing, and typography"* | desktop + remote |
| `get_code_connect_map` | *"Object where each key is a Figma node ID … value contains metadata about the connected component: componentName, source, snippet"*; params `clientFrameworks`, `clientLanguages` | desktop + remote |
| `get_motion_context` | *"Keyframe animation data … an inventory of animated nodes, keyframe tracks with easing curves, pre-computed CSS @keyframes"*; params `nodeId`, `recursive` | desktop + remote |
| `get_figjam` | FigJam metadata in XML | desktop + remote |
| `download_assets` | *"Temporary URLs that must be fetched"*; PNG/JPG/SVG/PDF; **up to 20 nodes** | **remote-only** |

**Write (code → design), all remote-only:** `use_figma`, `generate_figma_design`, `create_new_file`, `upload_assets` (PNG/JPG/GIF/WebP, **max 10 MB**), `generate_diagram`.
**Design system:** `get_libraries`, `search_design_system` (remote-only); `add_code_connect_map`.
**Account:** `whoami` — returns the user's email, their plans, and *"the seat type the user has on each plan"* (remote-only).
**Prompt:** `create_design_system_rules` — emits a rules file that *"Provides agents with the right context to translate designs into high-quality, codebase-aware frontend code."*
Also present: generative-plugin and shader tool families, and a "Weave" tool-run family.

### Access tiers and rate limits ✅

https://developers.figma.com/docs/figma-mcp-server/rate-limits-access/

| Seat | Starter | Professional | Organization | Enterprise |
|---|---|---|---|---|
| **View, Collab** | up to **20/month** | up to **6/month** | up to **6/month** | up to **6/month** |
| **Dev, Full** | — | up to **200/day, 10/min** | up to **200/day, 15/min** | up to **600/day, 20/min** |

Education plans follow Professional. `create_new_file` and `whoami` are exempt from rate limits. Figma *"reserves the right to change rate limits."*
⚠️ The exact Dev/Full column-to-plan mapping came back slightly inconsistently across two fetches of the same page; treat the *shape* (View/Collab ≈ 6–20 per **month**; Dev/Full = hundreds per **day**) as solid and re-read the page before relying on an exact number.

**Answer to "does it need Dev Mode / a particular plan?":** the **remote** server works *on all seats and plans* — but a **View or Collab seat gets ~6 calls a month**, which is not a workflow. In practice you need a **Dev or Full seat on a paid plan**. The **desktop** server strictly requires a Dev or Full seat on a paid plan.

### Known limits ✅/⚠️
- **Token blowups on large selections.** ⚠️ Selections around **~170,000 tokens** trigger a warning; large selections time out or return incomplete. Figma's own guide: *"Break screens into smaller parts (like components or logical chunks) for faster, more reliable results."*
- **Claude Code specifically** ⚠️ can error when `get_design_context` exceeds the 25,000-token MCP output cap; the workaround is the `MAX_MCP_OUTPUT_TOKENS` env var.
- **Recommended order** ✅ (Figma's guide): `get_metadata` first (sparse outline, sidesteps the token warning) → `get_screenshot` for visual reference → `get_design_context` on just the sections you're building → `download_assets` last.
- **Write-to-canvas pricing** ✅: *"currently available for free during the beta period"* but *"will eventually be a usage-based paid feature."*
- Cursor users report MCP failures from expired/corrupted auth tokens ⚠️.
- File hygiene matters more than prompt quality: use components for reused elements, Code Connect links, **variables for design tokens**, and semantic layer names.

---

## 3.2 Figma Variables → design tokens

### The REST API — the blocker ✅

https://developers.figma.com/docs/rest-api/variables/

> **"To use this API, you must have a Full seat in an Enterprise org; guests cannot use the API."**

Endpoints:
```
GET  /v1/files/:file_key/variables/local        scope: file_variables:read
GET  /v1/files/:file_key/variables/published    scope: file_variables:read
POST /v1/files/:file_key/variables              scope: file_variables:write
```
POST additionally requires **Full seat or admin**, **Enterprise**, and **Edit access** to the file. Reads require View access and any org-member account type.

**This is the single most important fact in Part 3 for a solo developer: the Variables REST API is Enterprise-only.** A one-person portfolio on a free or Professional plan **cannot** pull tokens via REST. The available routes are:
1. **`get_variable_defs`** via the MCP server (works on the far cheaper seat tiers — this is the practical path), or
2. **Tokens Studio** plugin → Git sync (below), or
3. skip Figma variables entirely and keep tokens in CSS custom properties.

### W3C Design Tokens Community Group format ✅

https://www.designtokens.org/TR/drafts/format/ (the old `tr.designtokens.org` 301s here)

Status: **Design Tokens Format Module 2025.10**, a *preview draft* of a Draft Community Group Report, published **8 September 2026**. The spec itself says: *"Do not attempt to implement this version of the specification."* — i.e. **still not stable in late 2026**.

Reserved `$`-prefixed keys: `$value` (required), `$type`, `$description`, `$extensions` (reverse-domain vendor namespacing), `$deprecated` (`true` / `false` / an explanatory string).
Groups are plain nesting without `$value`; they support `$type` inheritance, `$extends`, and a reserved `$root` token name. The spec warns *"groups are arbitrary and tools SHOULD NOT use them to infer the type or purpose of design tokens."*
Aliases: `{group.token}` for a whole value, or JSON Pointer `#/path/to/target` via `$ref` for property-level reference.
Types: color, dimension, fontFamily, fontWeight, duration, cubicBezier, number, strokeStyle, border, transition, shadow, gradient.

```json
{
  "color": {
    "primary": {
      "$type": "color",
      "$value": { "colorSpace": "srgb", "components": [0, 0.4, 0.8], "hex": "#0066cc" }
    }
  },
  "shadow": {
    "medium": {
      "$type": "shadow",
      "$value": {
        "color": "{color.primary}",
        "offsetX": { "value": 0.5, "unit": "rem" },
        "offsetY": { "value": 0.5, "unit": "rem" },
        "blur":    { "value": 1.5, "unit": "rem" },
        "spread":  { "value": 0,   "unit": "rem" }
      }
    }
  }
}
```

Note the colour shape changed from a plain hex string to a structured `{colorSpace, components, hex}` object — a real migration cost for anyone who adopted an earlier draft.

### Style Dictionary ✅

https://styledictionary.com · **`style-dictionary@5.5.5`, Apache-2.0** (npm, 2026-09-22).

```bash
npm install -D style-dictionary
```
```json
{
  "source": ["tokens/**/*.json"],
  "platforms": {
    "css": {
      "transformGroup": "css",
      "buildPath": "build/",
      "files": [{ "destination": "variables.css", "format": "css/variables" }]
    }
  }
}
```
```bash
style-dictionary build
```
Described as *"forward-compatible with Design Token Community Group spec"*, with DTCG utilities in the reference docs.

### Tokens Studio ⚠️

https://docs.tokens.studio · repo https://github.com/tokens-studio/figma-plugin
- Syncs tokens between Figma and **GitHub, GitLab, Azure DevOps, Bitbucket, JSONBin, read-only URLs, Supernova**.
- Supports the DTCG `$value` / `$type` shape.
- **Pro gate:** multi-file/folder token storage is a Pro feature; and *"If other team members are working with your tokens and do not have a Pro Licence for Tokens Studio, your tokens will be read-only for them."*
- For a solo dev this is the realistic way to get Figma variables into Git **without** an Enterprise plan.

### Realistic token pipelines

| Path | Requires | Verdict for a solo portfolio |
|---|---|---|
| Figma Variables REST → Style Dictionary → CSS | **Enterprise + Full seat** | ❌ out of reach |
| Tokens Studio → Git → Style Dictionary → CSS | Figma free + Tokens Studio (free tier for single-file) | 🟡 works, but it's a whole subsystem |
| MCP `get_variable_defs` → agent writes `:root` vars | Dev/Full seat on a paid plan | 🟡 fine if you're already in Figma |
| **Hand-written CSS custom properties** | nothing | ✅ **the right answer for one page** |

---

## 3.3 Figma Code Connect ✅

https://developers.figma.com/docs/code-connect/ · **`@figma/code-connect@2.0.1`, MIT** (npm, 2026-09-22).

> *"a bridge between your codebase and Figma's Dev Mode, connecting components in your repositories directly to components in your design files"*

**Supported platforms:** React and React Native · HTML (covers Web Components, Angular, Vue) · SwiftUI · Jetpack Compose.

**File convention:** `<Component>.figma.tsx` (React) / `.figma.ts` (template form).

**React form — full example:**
```tsx
import figma from '@figma/code-connect/react'

figma.connect(Button, 'https://...', {
  props: {
    label: figma.string('Text Content'),
    disabled: figma.boolean('Disabled'),
    type: figma.enum('Type', {
      Primary: 'primary',
      Secondary: 'secondary',
    }),
    icon: figma.instance('Icon'),
    className: figma.className([
      'btn-base',
      figma.enum("Size", { Large: 'btn-large' }),
    ]),
    children: figma.children('Content')
  },
  example: ({ disabled, label, type, icon, className, children }) => (
    <Button disabled={disabled} type={type} className={className}>
      {icon}{label}{children}
    </Button>
  ),
})
```

**Template (`.figma.ts`) form**, from the docs:
```ts
// url=https://www.figma.com/file/your-file-id/Button?node-id=123
import figma from 'figma'
const instance = figma.selectedInstance
export default {
  example: figma.code`
    <Button
      size={${instance.getEnum('Size', { Large: 'large', Medium: 'medium', Small: 'small' })}}
      disabled={${instance.getBoolean('Disabled')}}
    >
      ${instance.getString('Text Content')}
    </Button>
  `,
  imports: ['import { Button } from "components/Button" '],
  id: 'button',
}
```

**CLI:** `figma connect create` · `figma connect publish` · `figma connect unpublish` · `figma connect parse`.
❌ The exact flag list (`--token`, `--node-url`, `--dir`, `--label`, `--skip-validation`) and the full `figma.config.json` shape are referenced by the docs but were **not present in the pages I could fetch** (`/docs/code-connect/cli/` 404s). Run `npx figma connect --help` rather than trusting a remembered flag list.

**Verdict for a one-page portfolio:** Code Connect is infrastructure for a **shared design system with multiple consumers**. With no component library and no designer on the other side of the handoff, it has literally nothing to connect. Skip.

---

## 3.4 Google Stitch

### What it is ✅

https://developers.googleblog.com/stitch-a-new-way-to-design-uis/ — announced **20 May 2025**:

> *"Stitch is a new experiment from Google Labs that allows you to turn simple prompt and image inputs into complex UI designs and frontend code in minutes."*

Powered by Gemini (2.5 Pro at launch; subsequently updated for Gemini 3 per https://blog.google/innovation-and-ai/models-and-research/google-labs/stitch-gemini-3/). Outputs: **HTML/CSS front-end code** plus a **"paste to Figma"** export. There is also an official *Stitch to Figma* Figma community plugin (id `1577379704241183556`).

**Free tier** ⚠️: commonly reported as **350 generations/month in Standard Mode** (Gemini Flash) and **50/month in Experimental Mode** (Gemini Pro). ❌ I could **not** confirm these numbers from a Google-owned page — the launch blog states no limits, and `stitch.withgoogle.com/docs` is a JS-rendered Google app that returns no static text to a fetcher.

### The MCP server ⚠️ — flagged as unverified-primary

`https://stitch.withgoogle.com/docs/mcp/setup` is client-rendered; `curl` returns only the Google app shell (`WIZ_global_data`), and both WebFetch attempts came back with nothing but the page title. **I could not read the official setup page.** Google's own codelab (https://codelabs.developers.google.com/design-to-code-with-antigravity-stitch) confirms the **API-key flow** — profile picture → settings → API key section → *"Create key"* → paste it into the client's Stitch plugin config — and confirms verification by asking the agent *"List my Stitch projects."* — but it does **not** print the server URL, the JSON, or the tool names.

The following therefore comes from a secondary source (https://sotaaz.com/post/stitch-mcp-api-en), which states it matches Google's codelab; **verify before relying on it**:

- **Server URL:** `https://stitch.googleapis.com/mcp`
- **Auth header:** `X-Goog-Api-Key`
- **Claude Code:**
  ```
  claude mcp add stitch --transport http https://stitch.googleapis.com/mcp --header "X-Goog-Api-Key: YOUR-API-KEY" -s user
  ```
- **Generic config:**
  ```json
  {
    "mcpServers": {
      "stitch": {
        "url": "https://stitch.googleapis.com/mcp",
        "headers": { "X-Goog-Api-Key": "YOUR-API-KEY" }
      }
    }
  }
  ```
- **Tools:** `create_project`, `list_projects`, `list_screens`, `get_project`, `get_screen`, `generate_screen_from_text`
- There is also a third-party CLI wrapper, `npx @_davideast/stitch-mcp init` (https://github.com/davideast/stitch-mcp) — **not** a Google product.
- That source itself concedes: *"Free-tier limits, tool names, and model specifications are not officially documented and may change."*

### Where Stitch sits in a pipeline

Stitch **generates** a design from a prompt; Figma MCP **reads** a design that already exists. So the notional chain is:

```
prompt ──▶ Stitch (generate_screen_from_text) ──▶ HTML/CSS  ──▶ code
                         └──▶ paste to Figma ──▶ Figma file ──▶ Figma MCP (get_design_context) ──▶ code
```

**The honest problem with that chain for this project:** Stitch is a *Gemini model generating a UI from a prompt*. Whatever it produces sits at the same statistical centroid described in Part 2 — it is a machine for producing exactly the purple-gradient, Inter, centred-hero, three-card page this portfolio is trying not to be. Pushing that through Figma and back out to code launders it, it does not fix it. If Stitch is used at all, use it for **layout exploration you then throw away**, never as the source of the visual direction.

---

## 3.5 Is a Figma round-trip worth it for a one-person, single-page dev portfolio?

### Evidence FOR ✅
- **Cheap entry on the remote MCP server.** *"available on all seats and plans"* — you can literally start with no paid seat.
- **`get_variable_defs` is the only non-Enterprise machine-readable route to Figma variables**, since the REST Variables API requires *"a Full seat in an Enterprise org"*. If you already keep tokens in Figma, MCP is how you get them out.
- **Visual exploration is genuinely faster on a canvas.** Anthropic's own prescribed process (§2.5) — a token plan, ASCII wireframes, and a *comparison* step before writing code — is exactly the job a design canvas does well. Some artifact must hold that exploration; Figma is a reasonable one.
- **Design becomes reviewable before it becomes expensive.** Changing a hero's structure in Figma is minutes; changing it after the CSS specificity is layered in is not.
- **The strongest structural argument from Part 2 applies here:** the tell is the *shape* of the page. Shape is exactly what you iterate on in a design tool and exactly what you don't iterate on once you're editing CSS.

### Evidence AGAINST ✅
- **The tooling is sized for teams, and the parts that matter are gated.**
  - Variables REST API: **Enterprise + Full seat.**
  - MCP on a View/Collab seat: **~6 tool calls per month.**
  - Tokens Studio multi-file sync and team read/write: **Pro.**
  - Code Connect: **needs a component library and a design/code split that a solo project does not have.**
- **Token blowups.** Large selections time out or return incomplete; the prescribed fix is to decompose the page and run `get_metadata` first. That's real ceremony per section, every time.
- **The mental-model mismatch is real.** ⚠️ A designer's canvas is absolute positioning; the browser is flow, stacking and intrinsic sizing. A Figma frame that looks right is not a layout that resizes right — you re-solve responsiveness in code regardless.
- **The observed inversion.** ⚠️ The most commonly reported reason a developer opens Figma is to screenshot a live page into a frame and redraw it — i.e. the canvas is downstream of the browser, not upstream.
- **The award sites themselves don't show a token pipeline.** None of the four sites studied exposes design tokens, a token build step, or DTCG artifacts. Lisa's craft is in `main.css` — 200 KB of hand-authored CSS with two hand-picked Penner curves. That is a person, in a stylesheet.
- **DTCG isn't stable.** The spec's own current draft (September 2026) says *"Do not attempt to implement this version."* Building a token pipeline on it now buys a migration.
- **The round-trip loses the only thing worth having.** Figma cannot express `animation-timeline: view()`, a GLSL shader, `linear()` easing, `:focus-visible`, `text-wrap: balance`, an 8-state component, or `prefers-reduced-motion`. Every item in §2.5's countermeasure list that separates a human-made page from a generated one lives in code, not in a frame. A round-trip carries the layer that's easy to fake and drops the layer that isn't.

### Verdict

**For a single-page personal developer portfolio built by one person: a full Figma round-trip is ceremony. Don't build it.**

The value of Figma here is the **thinking**, not the **pipeline**. Take the first half and skip the second:

1. **Do the design plan.** Anthropic's two-pass process — 4–6 named hex values, typeface roles, an ASCII-wireframe layout concept, a principles list, then an explicit "would I have produced this for any brief?" review. This is 30 minutes and it is where the whole outcome is decided.
2. **Hold it wherever is fastest** — a Figma frame, a sketch, a `design.md`. The artifact is not the point; committing to a point of view before writing CSS is.
3. **Tokens are ~20 CSS custom properties in `:root`.** No Style Dictionary, no Tokens Studio, no DTCG, no build step. Revisit only if a second surface appears.
4. **Skip entirely:** Code Connect (nothing to connect), the Variables REST API (Enterprise-gated), Style Dictionary (one consumer), Stitch (it generates the aesthetic you're avoiding).
5. **Keep Figma MCP installed anyway** — `claude mcp add --scope user --transport http figma https://mcp.figma.com/mcp` costs nothing, and `get_screenshot` / `get_design_context` are genuinely useful the day someone hands you a frame.

The ranked leverage for *this* project, highest first: **(1)** commit to a specific visual point of view grounded in the subject; **(2)** run the Part 2 self-audit; **(3)** make every interaction actually work (8 states, focus-visible, reduced motion); **(4)** one orchestrated motion moment; **(5)** ship under 200 KB of JS. A Figma round-trip is not on that list.

---

# Appendix — versions and dates verified 2026-09-22

| Thing | Value | Source |
|---|---|---|
| `gsap` | **3.15.0**, published **2026-04-13**, *"Standard 'no charge' license"* (not OSS) | npm registry |
| GSAP free-for-all release | **3.13**, **2025-04-29** | gsap.com/blog/3-13/ |
| GSAP Standard License | effective **2025-04-30**, modified **2025-05-30**, © Webflow | gsap.com/standard-license |
| `lenis` | **1.3.26**, MIT | npm registry |
| Lenis on lisa.locomotive.ca | **1.1.9** (`window.lenisVersion`) | live bundle |
| `three` | **0.186.0**, MIT | npm registry |
| `@react-three/fiber` | **9.7.0**, MIT | npm registry |
| `style-dictionary` | **5.5.5**, Apache-2.0 | npm registry |
| `@figma/code-connect` | **2.0.1**, MIT | npm registry |
| DTCG format | **Design Tokens Format Module 2025.10**, preview draft, **2026-09-08** | designtokens.org |
| Scroll-driven animations | Baseline **limited** · Chrome 115 (2023-07-18) · Safari 26 (2025-09-15) · **Firefox: preview only** | webstatus.dev + MDN BCD |
| View transitions (same-doc) | Baseline **newly**, **2025-10-14** · Chrome 111 · Safari 18 · Firefox 144 | webstatus.dev |
| Cross-document view transitions | Baseline **limited** · Chrome 126 · Safari 18.2 · **no Firefox** | webstatus.dev |
| `linear()` easing | Baseline **widely**, high date **2026-06-11** | webstatus.dev |
| `text-wrap: balance` | Baseline **newly**, **2024-05-13** | webstatus.dev |
| `text-wrap: pretty` | Baseline **limited** · Safari 26 · **no Firefox** | webstatus.dev |
| `backdrop-filter` | Baseline **newly**, **2024-09-16** (Safari 18) | webstatus.dev |
| `content-visibility` | Baseline **newly**, **2025-09-15** | webstatus.dev |
| WebGPU | Baseline **limited** · Chrome 144 (2026-01-13) · Safari 26 · **no Firefox** | webstatus.dev |
| LCP thresholds | ≤ 2.5 s good, > 4.0 s poor, p75 | web.dev/articles/lcp |
| INP thresholds | ≤ 200 ms good, 200–500 needs improvement, > 500 poor, p75 | web.dev/articles/inp |
| Figma remote MCP | `https://mcp.figma.com/mcp`, all seats/plans | developers.figma.com |
| Figma desktop MCP | `http://127.0.0.1:3845/mcp`, Dev/Full seat, paid plans | help.figma.com |
| Figma Variables REST API | **Full seat in an Enterprise org** | developers.figma.com/docs/rest-api/variables/ |
| Stitch launch | **2025-05-20**, Google Labs | developers.googleblog.com |

## Explicitly NOT verified

- ❌ Stitch MCP server URL, config JSON, and tool names — the official `stitch.withgoogle.com/docs/mcp/setup` page is JS-rendered and unreadable to a fetcher; §3.4 values come from a secondary source.
- ❌ Stitch free-tier generation quotas (350 standard / 50 experimental) — no Google-owned page confirms them.
- ❌ LinusBio's exact Awwwards status — it appears as a **Nominee**, not a confirmed Site of the Day.
- ❌ A UNITED24 Awwwards entry — `awwwards.com/sites/united24-rebuild-map` 404s; ❌ no award record located.
- ❌ Any first-person shadcn-maintainer statement on AI design slop.
- ❌ The *New Yorker* "Claudian sameness" article — surfaced in a search summary only; not fetched.
- ❌ Code Connect CLI flag list and `figma.config.json` shape — the CLI docs page 404s. Use `npx figma connect --help`.
- ❌ First-party three.js numbers for postprocessing pass cost.
- ❌ Google's own page for the lazy-loaded-LCP p75 720 ms vs 364 ms statistic (Lighthouse URL 404s); figure is quoted from the `hallmark` repo.
- ⚠️ Figma MCP rate-limit table — the plan↔seat mapping returned inconsistently across two fetches of the same page. Re-read before relying on an exact number.
