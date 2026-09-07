# ADLC — bilingual front end

A static, bilingual (EN/AR) site for Abu Dhabi Ladies Club, generated from JSON
content by a single Python script. No Node, no framework, no build chain.

```bash
python3 build.py            # build into dist/
python3 build.py --serve    # build, then serve on http://localhost:8080
```

## Why it is built this way

**The timetable is data, not a picture.** Every class is a record in
`content/classes.json` and is rendered into the HTML as real text. It is
searchable, translatable, readable by a screen reader, and it can feed a booking
engine later. Replacing four hand-built JPEGs a month with this was the audit's
most expensive open finding.

**Arabic is not a translation layer.** Both languages are generated from the same
records and the same templates. The Arabic site is the same site with
`dir="rtl"` — there is no second layout and no second codebase.

**No physical directions in the CSS.** `adlc.css` contains no `left` or `right`
properties, only logical ones (`margin-inline-start`, `inset-inline-end`,
`padding-block`). That is what makes RTL an attribute rather than a rebuild.
There is a guard for it:

```bash
grep -nE '(^|[^-a-z])(left|right)[[:space:]]*:' static/css/adlc.css && echo FAIL || echo OK
```

## Layout

```
content/       site.json      brand, nav, home copy, footer  (bilingual)
               classes.json   categories, studios, days, 25 sessions
               events.json    event kinds (seasonal colours) and events
               hire.json      spaces, hire rules, enquiry fields
               tenants.json   on-site businesses, services, licence line
               academy.json   FBMA partner, 8 sports, terms, consent wording
               app.json       demo member, tabs, app screen copy
               console.json   staff, leads, occupancy grid, broadcast, CMS copy
               pages.json     membership, lagoon, visit, timetable strings
static/css/    adlc.css       design kit v0.1 tokens + components
static/js/     filter.js      generic faceted filtering (timetable + events)
               app.js         member-app booking buttons (in-memory only)
               console.js     broadcast reach recalculation
               join.js        join flow steps, validation, order summary
static/img/    hero.jpg       club photography (see Credits)
build.py       generator      one function per page type
dist/          output         en/ ar/ static/ + a root redirect to /en/
```

## Pages

**Public site:** `index` · `membership` · `timetable` · `academy` · `lagoon` ·
`directory` · `events` · `hire` · `visit` · `join`, plus a generated detail page
per event, per tenant and per sport.

**Member app:** `app-home` · `app-timetable` · `app-facilities` · `app-academy` ·
`app-account` · `app-bookings`.

**Staff console:** `console-today` · `console-timetable` · `console-inbox` ·
`console-reports` · `console-broadcast`.

Each in both languages — **82 pages** total. Adding a page is a function in `build.py` plus an
entry in `PAGE_FNS` and `site.json`'s `nav`.

## Conventions worth keeping

- **Plum acts, gold decorates.** `--action` is plum. Gold is never interactive —
  it fails contrast at button size on ivory.
- **Arabic gets more leading at the same size** (`--lh-ar: 1.75`), baked into the
  token rather than fixed per component.
- **Asset URLs are root-absolute.** A relative `url()` inside a custom property
  resolves against the stylesheet that *uses* it, not the page that declares it,
  which silently doubles the path. This bit us once; `/static/...` avoids it.
- **The filter script only hides rows.** With JavaScript off the page still shows
  every class.

## The join flow

`join.html` in both languages. Four steps in one form: membership, your details,
payment, done. Reached from the header **Join** button, and from a membership
card via `join.html?tier=gold`, which preselects that tier.

**No card fields exist anywhere on this site, by design.** The payment step shows
the order summary and hands control to the gateway's own hosted checkout. Card
data therefore never touches a page the club serves, which keeps the club in PCI
SAQ A and means this prototype cannot collect a card number even by mistake. The
form has no `action` and no `method`; nothing is submitted, stored or sent.

Other decisions worth keeping:

- **Prices are per billing period.** Each tier holds
  `price: {annual, monthly}`. An earlier version had one number per tier, which
  looked fine while prices were unset and would have billed the annual figure to
  monthly members the moment they were filled in. VAT (5%) and the total are
  computed from the period actually selected.
- **Marketing consent is separate, optional and unticked.** Health declaration
  and club rules are required; the notice says operational messages about your
  own bookings are sent either way.
- **Emirates ID is collected, not uploaded.** It is checked at the desk on the
  first visit. Asking for a photograph of an ID document is a liability the club
  does not need in order to sell a membership.
- **Without JavaScript** every step is visible as one long form and still reads
  correctly. The script only hides steps, validates, and keeps the summary in
  sync.

### Verified

Walked end to end in the browser: tier preselect from the query string; step 2
blocked while empty (7 fields flagged) and blocked again on a malformed email;
summary populating tier, period, VAT and total; monthly and annual producing
different amounts (21,000 → VAT 1,050 → 22,050 annual; 2,100 → 105 → 2,205
monthly); step 4 issuing the card. Zero card inputs and no form action present in
the DOM.

## Events and venue hire

`events.html` lists everything by month, filterable by kind, with one generated
detail page per event (`event-<id>.html`) in both languages. `hire.html` covers
the three hireable spaces, the rules, and an enquiry form.

- **Seasonal colour lives on event artwork and nowhere else.** Each kind in
  `events.json` carries its own `color`/`color2`; the nav, buttons and chips stay
  plum and ivory on every page. That boundary is the reason six hues can share
  one page without it losing its owner.
- **"What changes for members" is a required field on every event.** A tournament
  that closes a court is an operational message, and operational messages are
  what the club currently broadcasts as posters.
- **Partner marks appear in one band, never in the header.** The band states that
  rule in the interface, so nobody has to remember it.
- **The hire rules come before the form.** Male guests, male contractors, female
  photographers, halal catering, lagoon lifeguard cover, guest naming. These are
  the questions the front desk answers on every enquiry, and answering them first
  is what turns an enquiry into a booking. Every line needs the club's
  confirmation — getting these wrong is a cultural error, not a design one.
- The enquiry form, like the join form, has **no action and no method**. Nothing
  is submitted or stored.

### One filter implementation, two lists

Adding events meant a second faceted list, so `timetable.js` was replaced by a
generic `filter.js` that both pages use. The markup contract is
`[data-filterable]` around `[data-facet]` buttons and `[data-item]` elements
carrying one attribute per facet, with optional `[data-group]` wrappers and a
`[data-empty]` message. Items are server-rendered; the script only hides them.

## Tenant directory

`directory.html` ("At the club") lists the on-site businesses, filterable by
category, with a generated detail page per tenant (`tenant-<id>.html`).

- **Tenants appear in club chrome, with their names as content rather than as
  competing logos.** There is one phone number on the site and it is the club's;
  a tenant enquiry is routed, not handed off. The rule is printed on the
  directory page so nobody has to remember it, and each detail page closes with
  "Operated under licence at Abu Dhabi Ladies Club."
- **Pop-ups carry an end date and a countdown state.** The specific fix for
  offers that stayed pinned for six years — nothing here outlives its own dates.
- **The salon is framed as a front door, not an amenity.** A salon appointment is
  one of the few ways a non-member can legitimately get inside the building, so
  its page says non-members are welcome by appointment.

### A header regression this caught

The directory made a seventh nav item, and at tablet width the sticky header
wrapped to three rows — 162px of every viewport, permanently. Below 900px the nav
is now a horizontally scrolling strip on its own line, so the header is two rows
(97px at 820px, 138px on a phone) and the page body still never scrolls
sideways. Measured, not eyeballed.

## Academy

`academy.html` groups eight programmes by discipline, each with its own sport
colour, level pips and capacity state, plus terms and fees. A detail page is
generated per sport (`sport-<id>.html`).

- **This is the only section where a second mark appears.** The FBMA band sits
  beneath the club's own header, separated by the one gold rule in the system
  that divides two names, and the band says so in the interface. Every other page
  on the site carries the club's mark alone.
- **Sport colours are the seven already in the academy's own training poster**,
  extended to swim school — the same hues that code the class timetable, so a
  parent who has learned one has learned the other.
- **Photography consent is stated on the academy page and on every sport page**:
  asked separately per programme, optional, and revocable, with what withdrawal
  actually does.

### A numerals bug this caught

The Arabic sport page read `المستويات: 4 / 4` — Western digits beside
Arabic-Indic ones, which the kit's bilingual rules explicitly forbid ("never mix
the two in one view"). Hand-authored Arabic content used Arabic-Indic digits
while every number the generator printed came out Western: class times and
durations, capacity counts, hire capacities, term session counts, level counts,
and the home page stats.

All generated digits now pass through `num(value, lang)`, and `check_numerals.py`
enforces it:

```bash
python3 check_numerals.py dist     # exits 1 on any Western digit
```

Two categories are deliberately exempt, marked `data-foreign` (which also gives
them a correct `lang` and `dir`, so a screen reader announces them properly):

- **Content in another language on purpose** — the broadcast composer's English
  message field, and a member's verbatim message in the lead inbox. Rewriting a
  customer's own words into different numerals would be wrong.
- **Identifiers** — phone numbers and social handles. A number you dial is
  written one way; the club's footer, the Visit page and the inbox now all show
  `+971 50 260 6784` in Western digits, as UAE convention has it.

## Member app

The app is a different product from the public site and is built with its own
chrome: no site header, no site footer, a sticky title bar and a five-tab bar,
constrained to 460px and centred. `body.app` switches the ground colour so the
shell reads as a device surface on desktop. The site's **Sign in** button opens
`app-home.html`.

It reuses the site's content: the timetable comes from the same
`classes.json` records the public page renders, so the two can never disagree.

- **Booking is interactive but honest.** Tapping Book flips the button to Booked
  and decrements the spots count; a full class offers the waitlist instead. State
  is in memory only — no network, no storage — and the banner on every screen
  says so. In a real build `toggle()` becomes a call to the booking engine.
- **The prototype cannot pretend to be signed in.** There is no auth, one demo
  member, and no data leaves the page.
- Arabic numerals are handled in the client too: the JS re-renders the spots
  count in Arabic-Indic digits on Arabic pages, so a booking never introduces the
  mixed-numeral bug the build guard catches server-side.

### Two CSS collisions this batch found

Adding the app to a single growing stylesheet surfaced the same failure twice:
a global single-class rule silently restyling new markup that reused the name.
`.note` (the partner band picking up the membership page's callout box) and
`.tier` (the app's account card picking up the membership tier card). Both are
now scoped — `.prule` and `.app-tier`. There is an audit for it:

```bash
python3 - <<'EOF'
import re, pathlib
css = pathlib.Path("static/css/adlc.css").read_text()
globals_ = set(re.findall(r"(?m)^\.([a-z][a-z0-9-]*)\s*\{", css))
used = set()
for f in pathlib.Path("dist/en").glob("app-*.html"):
    shell = f.read_text().split('class="app-shell"', 1)[-1]
    for m in re.findall(r'class="([^"]+)"', shell):
        used.update(m.split())
print("shared with a global rule:", sorted(globals_ & used))
EOF
```

Anything in that list that is not deliberately shared (`.btn`, `.lang`) or
app-owned (`.app-*`) is a collision waiting to happen.

## Staff console

Three products now share one stylesheet and one content model: the public site,
the member app, and the console. The console has its own chrome again — a plum
sidebar and a topbar — and collapses the sidebar to a horizontal strip below
820px.

- **Timetable CMS.** Editing a class shows a publish checklist: website, member
  app, and an auto-rendered Instagram poster, all from the same records. The push
  notification is deliberately **not** ticked — a routine schedule edit should not
  buzz four thousand phones, and defaults are a design decision.
- **Lead inbox.** Instagram, WhatsApp and web form in one queue with one SLA
  clock. The four threads at the top are the real unanswered comments from the
  club's 20 August post. "Send public reply" is the primary action, not a DM.
- **Reports.** Occupancy heatmap, instructor fill rate, lead source.
- **Broadcast.** Audience defaults to members affected, not everyone; both
  languages are required; the reach panel recomputes on audience change.

### Chart colour is computed, not chosen

The occupancy ramp and the lead-source trio were validated before use — OKLCH
lightness band, chroma floor, protan/deutan separation in OKLab ΔE, a
normal-vision floor, and WCAG contrast against the chart surface, in **both**
light and dark modes with separately re-stepped dark values.

The obvious choice — reusing the programme colours as chart series — was tested
and **rejected**: yoga purple against strength blue measured ΔE 2.3 under
deuteranopia where 8 is the target, and 13 against a normal-vision floor of 15.
So occupancy uses a single hue light-to-dark, because occupancy is magnitude and
not identity; lead source uses a validated three-hue set. Programme colours keep
coding class categories, where they are never read against each other.

Every heatmap cell carries its number as well as its shade, "no class scheduled"
is a dashed empty cell so absence never reads as low attendance, and every chart
has a table.

### A bar-chart bug worth remembering

Both bar charts rendered as empty tracks. The fills were `<span>` elements with
an inline `width:NN%` — but a span is `display:inline` by default, so percentage
width does nothing and the measured width was 0. Grid and flex children get
blockified automatically, which is why the heatmap and the sparkline were fine
and only the bars broke. Any `%`-width fill needs an explicit `display:block`.

## Deploying

`dist/` is a plain static directory — Netlify, Cloudflare Pages, S3, anything.
Build command `python3 build.py`, publish directory `dist`. If you deploy under a
sub-path rather than a domain root, change `HERO_IMG` and the `/static/` links to
match, or set a `<base>`.

## Porting to Next.js

The content JSON and `adlc.css` transfer unchanged. Each `page_*` function maps
to a route component, `LANGS` becomes the `[lang]` segment, and `classes.json`
becomes the data source the booking API later replaces. The reason this is Python
is that the machine it was built on has no Node installed — the architecture was
chosen to survive the port, not to avoid it.

## Status and credits

Class names, coaches, capacities and booking counts are **sample data** for
exercising the design. Verified facts (address, opening year, facilities) come
from the club's Google Business Profile and the architects' published project
record. Prices are deliberately unset — the tier cards render `AED —` until the
club publishes them.

Photography: UPA Italia by Paolo Lettieri Architects, placed on the client's
confirmation of licence. **The floral mark in the header is a reconstruction and
must not ship** — it is drawn inline in `build.py` (`MARK`) so replacing it is a
one-line change once the vector files arrive.
