#!/usr/bin/env python3
"""
ADLC static site generator.

Content lives in content/*.json. Every page is generated for both
languages from the same records — the Arabic site is the same site with
dir="rtl", not a separate build. The timetable is data: class names are
real text in the HTML, so they are searchable, translatable and
readable by a screen reader. That is the whole point of it.

Usage:  python3 build.py            # build into dist/
        python3 build.py --serve    # build, then serve on :8080
"""
import json, os, shutil, sys, html, hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CONTENT, STATIC, DIST = ROOT / "content", ROOT / "static", ROOT / "dist"
LANGS = ("en", "ar")

def load(name):
    with open(CONTENT / name, encoding="utf-8") as f:
        return json.load(f)

SITE, CLASSES, PAGES = load("site.json"), load("classes.json"), load("pages.json")
EVENTS, HIRE = load("events.json"), load("hire.json")
TENANTS, ACADEMY = load("tenants.json"), load("academy.json")
APP, CONSOLE = load("app.json"), load("console.json")
E = lambda s: html.escape(str(s), quote=True)

# The kit's bilingual rule: never mix numeral systems in one view. Hand-authored
# Arabic content uses Arabic-Indic digits, so any number this generator emits on
# an Arabic page has to match. Everything that prints a digit goes through num().
_AR_DIGITS = str.maketrans("0123456789", "\u0660\u0661\u0662\u0663\u0664\u0665\u0666\u0667\u0668\u0669")
def num(v, lang):
    s = str(v)
    return s.translate(_AR_DIGITS) if lang == "ar" else s



def asset(rel):
    """Static URL with a short content hash, so a changed file is a new URL."""
    f = STATIC / rel
    h = hashlib.sha1(f.read_bytes()).hexdigest()[:8] if f.exists() else "0"
    return f"/static/{rel}?v={h}"

def t(node, lang, suffix=""):
    """Pull a localised string: t(obj,'ar') -> obj['ar']; suffix for v_en/v_ar."""
    key = (suffix + lang) if suffix else lang
    return node.get(key, node.get(suffix + "en" if suffix else "en", ""))

# The mark comes from brand/make_marks.py so the site and the exported assets
# can never drift apart. It is a reconstruction traced from the club's badge —
# see that file's note — and the club's vector supersedes it.
sys.path.insert(0, str(ROOT / "brand"))
from make_marks import bloom as _bloom, stem as _stem, PLUM as _MARK_PLUM  # noqa: E402
MARK = ('<svg viewBox="0 0 100 100" aria-hidden="true">' + _bloom(sw=2.4) + _stem() + '</svg>')

# Root-absolute: a relative url() inside a custom property resolves against the
# stylesheet that *uses* it, not the page that declares it, which silently
# doubles the path. Root-absolute avoids that entirely.
HERO_IMG = "/static/img/hero.jpg"

def head(title, lang, desc, extra_css=""):
    rtl = lang == "ar"
    return f"""<!doctype html>
<html lang="{lang}" dir="{'rtl' if rtl else 'ltr'}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{E(title)}</title>
<meta name="description" content="{E(desc)}">
<link rel="alternate" hreflang="{'en' if rtl else 'ar'}" href="../{'en' if rtl else 'ar'}/">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Almarai:wght@400;700;800&amp;family=Bodoni+Moda:opsz,wght@6..96,400;6..96,500&amp;family=IBM+Plex+Mono:wght@400;500&amp;family=IBM+Plex+Sans+Arabic:wght@400;500;600;700&amp;family=IBM+Plex+Sans:wght@400;500;600&amp;display=swap">
<link rel="icon" href="/static/brand/favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="/static/brand/app-icon.svg">
<link rel="stylesheet" href="{asset('css/adlc.css')}">
{extra_css}
</head>
<body>
<a class="skip" href="#main">{'تخطي إلى المحتوى' if rtl else 'Skip to content'}</a>
"""

def header(lang, current):
    other = "ar" if lang == "en" else "en"
    nav = "".join(
        '<li><a href="{href}"{cur}>{label}</a></li>'.format(
            href=("index.html" if n["slug"] == "index" else n["slug"] + ".html"),
            cur=' aria-current="page"' if n["slug"] == current else "",
            label=E(t(n, lang)))
        for n in SITE["nav"])
    brand_main = E(SITE["brand"]["ar"] if lang == "ar" else SITE["brand"]["en"])
    brand_sub  = E(SITE["brand"]["latin"] if lang == "ar" else SITE["brand"]["ar"])
    return f"""<header class="site-head">
<div class="wrap head-in">
  <a class="lockup" href="index.html">{MARK}<span class="nm"><b>{brand_main}</b><em>{brand_sub}</em></span></a>
  <nav aria-label="{'التنقل الرئيسي' if lang=='ar' else 'Main'}"><ul class="site-nav">{nav}</ul></nav>
  <div class="head-cta">
    <a class="lang" href="../{other}/{'index.html' if current=='index' else current+'.html'}" lang="{other}">{'EN' if lang=='ar' else 'ع'}</a>
    <a class="btn btn-secondary" href="app-home.html">{E(t(SITE['cta']['signin'], lang))}</a>
    <a class="btn btn-primary" href="join.html">{E(t(SITE['cta']['join'], lang))}</a>
  </div>
</div>
</header>
<main id="main">"""

def footer(lang):
    s = SITE
    labels = {"en": ("Find us", "Opening hours", "Telephone"), "ar": ("العنوان", "المواعيد", "الهاتف")}
    a, b, c = labels[lang]
    return f"""</main>
<footer class="site-foot"><div class="wrap">
<div class="foot-in">
  <div class="col"><h4>{E(a)}</h4><p>{E(t(s['address'], lang))}</p></div>
  <div class="col"><h4>{E(b)}</h4><p>{E(t(s['hours'], lang))}</p></div>
  <div class="col"><h4>{E(c)}</h4><a href="tel:{E(s['phone'].replace(' ',''))}">{E(s['phone'])}</a></div>
</div>
<p class="foot-note">{E(t(s['footer']['note'], lang))}</p>
</div></footer>
</body></html>"""

# ---------- pages ----------
def page_home(lang):
    h, rtl = SITE["home"], lang == "ar"
    stats = "".join("<div><b>%s</b><span>%s</span></div>" %
                    (E(num(x["n"], lang)), E(t(x, lang))) for x in h["stats"])

    # facilities trio — the club's own rooms, photographed
    fac = [("lagoon.html",     "hero",   PAGES["lagoon"]["title"],  PAGES["lagoon"]["headline"]),
           ("directory.html",  "atrium", {"en": "At the club", "ar": "في النادي"},
                                         {"en": "Salon, nursery, music school and the shops",
                                          "ar": "صالون وحضانة ومدرسة موسيقى ومتاجر"}),
           ("hire.html",       "dining", PAGES["hire"]["title"],
                                         {"en": "Hire a room, or the whole beach",
                                          "ar": "استأجري قاعة، أو الشاطئ كاملاً"})]
    fac_cards = "".join(
        '<a class="tenant" href="{href}"><span class="im" style="--img:url({img})">'
        '<span class="cat">{k}</span></span><span class="tx"><h3>{ttl}</h3><p>{d}</p></span></a>'.format(
            href=href, img=IMGS[img], k=E(t(ttl, lang)), ttl=E(t(ttl, lang)), d=E(t(sub, lang)))
        for href, img, ttl, sub in fac)

    # membership — the conversion surface, on the homepage rather than one click away
    m = PAGES["membership"]
    tiers = "".join(
        '<div class="tier{f}">{badge}<h3>{n}</h3><span class="price">{p}<small>{per}</small></span>'
        '<ul>{inc}</ul><a class="btn {b}" href="join.html?tier={id}">{cta}</a></div>'.format(
            f=" feat" if x["feat"] else "",
            badge='<span class="badge">%s</span>' % E("الأكثر اختياراً" if rtl else "Most chosen") if x["feat"] else "",
            n=E(t(x, lang)),
            p=E("AED —" if x["price"].get("annual") is None else "AED {:,}".format(x["price"]["annual"])),
            per=E(" / سنة" if rtl else " / year"),
            inc="".join("<li>%s</li>" % E(i) for i in (x["inc_ar"] if rtl else x["inc_en"])),
            b="btn-primary" if x["feat"] else "btn-secondary", id=x["id"],
            cta=E("اختاري" if rtl else "Choose"))
        for x in m["tiers"])

    # what's on — three soonest events, seasonal colour on the artwork only
    kinds = {k["id"]: k for k in EVENTS["kinds"]}
    evs = "".join(
        '<a class="ev" href="event-{id}.html" style="--k1:{c1};--k2:{c2}">'
        '<span class="art">{rose}<span class="kind">{kn}</span></span>'
        '<span class="tx"><span class="when">{w}</span><h3>{n}</h3>'
        '<span class="foot"><span class="state {sc}">{sl}</span>'
        '<span class="go">{more}</span></span></span></a>'.format(
            id=x["id"], c1=kinds[x["kind"]]["color"], c2=kinds[x["kind"]]["color2"],
            rose=ROSETTE_WHITE, kn=E(t(kinds[x["kind"]], lang)),
            w=E(x["when_ar"] if rtl else x["when_en"]), n=E(t(x, lang)),
            sc=_state_label(x, lang)[0], sl=E(_state_label(x, lang)[1]),
            more=E("التفاصيل ←" if rtl else "Details →"))
        for x in EVENTS["events"][:3])

    return (head(f"{t(SITE['brand'],lang)}", lang, t(h['lede'], lang),
                 f'<style>.hero{{--hero-img:url("{HERO_IMG}")}}'
                 f'.closer{{--hero-img:url("{IMGS["atrium"]}")}}</style>')
        + header(lang, "index")
        + f"""<section class="hero"><span class="art"></span><div class="wrap">
  <p class="kicker">{E(t(h['kicker'], lang))}</p>
  <h1>{E(t(h['title'], lang))}</h1>
  <p class="lede">{E(t(h['lede'], lang))}</p>
  <div class="actions">
    <a class="btn btn-primary" href="membership.html">{E(t(SITE['cta']['seeall'], lang))}</a>
    <a class="btn btn-quiet" href="visit.html">{E(t(SITE['cta']['book'], lang))}</a>
  </div>
</div></section>
<div class="stats">{stats}</div>

<div class="wrap">
  <section class="block">
    <h2 class="sec">{E("المرافق" if rtl else "The club")}</h2>
    <div class="tenants">{fac_cards}</div>
  </section>

  <section class="block">
    <h2 class="sec">{E(t(m['title'], lang))}</h2>
    <p class="lede">{E(t(m['lede'], lang))}</p>
    <div class="tiers">{tiers}</div>
  </section>

  <section class="block">
    <h2 class="sec">{E(t(PAGES['events']['title'], lang))}</h2>
    <div class="ev-grid">{evs}</div>
    <p style="margin-block-start:1rem"><a class="btn btn-secondary" href="events.html">{E(t(PAGES['events']['title'], lang))} →</a></p>
  </section>
</div>

<section class="closer"><div class="wrap">
  <p class="kicker">{E(t(PAGES['timetable']['title'], lang))}</p>
  <h2>{E("جدول الحصص بيانات، لا صورة" if rtl else "The timetable is data, not a picture")}</h2>
  <p>{E(t(PAGES['timetable']['lede'], lang))}</p>
  <a class="btn btn-primary" href="timetable.html">{E(t(PAGES['timetable']['title'], lang))} →</a>
</div></section>"""
        + footer(lang))

def spots_label(sess, lang):
    free = sess["cap"] - sess["booked"]
    st = PAGES["timetable"]["states"]
    if free <= 0:  return "full", t(st, lang, "full_")
    if free <= 3:  return "few",  t(st, lang, "few_").replace("{n}", num(free, lang))
    return "open", t(st, lang, "open_").replace("{n}", num(free, lang))

def page_timetable(lang):
    tt, cats = PAGES["timetable"], {c["id"]: c for c in CLASSES["categories"]}
    studios = {s["id"]: s for s in CLASSES["studios"]}
    f = tt["filters"]
    daychips = ['<button class="chip" data-facet="day" data-value="all" aria-pressed="true">%s</button>'
                % E(f["all_ar"] if lang == "ar" else f["all_en"])]
    for d in CLASSES["days"]:
        daychips.append('<button class="chip" data-facet="day" data-value="%s" aria-pressed="false">%s</button>'
                        % (d["id"], E(t(d, lang))))
    catchips = ['<button class="chip" data-facet="cat" data-value="all" aria-pressed="true">%s</button>'
                % E(f["all_ar"] if lang == "ar" else f["all_en"])]
    for c in CLASSES["categories"]:
        catchips.append('<button class="chip" data-facet="cat" data-value="%s" aria-pressed="false">'
                        '<span class="dot" style="background:%s"></span>%s</button>'
                        % (c["id"], c["color"], E(t(c, lang))))

    groups = []
    for d in CLASSES["days"]:
        rows = [s for s in CLASSES["sessions"] if s["day"] == d["id"]]
        if not rows: continue
        cards = []
        for s in sorted(rows, key=lambda r: r["time"]):
            cls, label = spots_label(s, lang)
            cards.append(
                '<article class="cls" data-item data-day="{d}" data-cat="{c}" style="--cat:{col}">'
                '<span class="stripe"></span>'
                '<span class="time">{time}<small>{mins}</small></span>'
                '<span class="nm">{name}<span>{coach} · {studio}</span></span>'
                '<span class="spots {scls}">{slabel}</span></article>'.format(
                    d=s["day"], c=s["cat"], col=cats[s["cat"]]["color"],
                    time=E(num(s["time"], lang)),
                    mins=E(("%s د" % num(s["mins"], lang)) if lang == "ar" else ("%d min" % s["mins"])),
                    name=E(t(s, lang)),
                    coach=E(s["coach_ar"] if lang == "ar" else s["coach_en"]),
                    studio=E(t(studios[s["studio"]], lang)),
                    scls=cls, slabel=E(label)))
        groups.append('<section class="daygroup" data-group><h3>%s</h3><div class="classes">%s</div></section>'
                      % (E(t(d, lang)), "".join(cards)))

    return (head(f"{t(tt['title'],lang)} · {t(SITE['brand'],lang)}", lang, t(tt['lede'], lang))
        + header(lang, "timetable")
        + f"""<div class="wrap">
<div class="page-head"><h1>{E(t(tt['title'], lang))}</h1><p>{E(t(tt['lede'], lang))}</p></div>
<div data-filterable>
  <div class="filters">
    <div class="filter-row"><span class="lab">{E(f['day_ar'] if lang=='ar' else f['day_en'])}</span>{"".join(daychips)}</div>
    <div class="filter-row"><span class="lab">{E(f['type_ar'] if lang=='ar' else f['type_en'])}</span>{"".join(catchips)}</div>
  </div>
  {"".join(groups)}
  <p class="empty" data-empty hidden>{E(t(tt['empty'], lang))}</p>
</div>
</div>
<script src="{asset('js/filter.js')}" defer></script>"""
        + footer(lang))

def page_membership(lang):
    m = PAGES["membership"]
    cards = []
    for tier in m["tiers"]:
        inc = "".join("<li>%s</li>" % E(x) for x in (tier["inc_ar"] if lang == "ar" else tier["inc_en"]))
        pa = tier["price"].get("annual")
        price = "AED —" if pa is None else "AED {:,}".format(pa)
        badge = ('<span class="badge">%s</span>' % E("الأكثر اختياراً" if lang == "ar" else "Most chosen")) if tier["feat"] else ""
        cards.append(
            '<div class="tier{feat}">{badge}<h3>{name}</h3>'
            '<span class="price">{price}<small>{per}</small></span><ul>{inc}</ul>'
            '<a class="btn {btn}" href="join.html?tier={tid}">{cta}</a></div>'.format(
                feat=" feat" if tier["feat"] else "", badge=badge,
                name=E(t(tier, lang)), price=E(price),
                per=E(" / سنة" if lang == "ar" else " / year"), inc=inc,
                btn="btn-primary" if tier["feat"] else "btn-secondary", tid=tier["id"],
                cta=E("اختاري" if lang == "ar" else "Choose")))
    return (head(f"{t(m['title'],lang)} · {t(SITE['brand'],lang)}", lang, t(m['lede'], lang))
        + header(lang, "membership")
        + f"""<div class="wrap">
<div class="page-head"><h1>{E(t(m['title'], lang))}</h1><p>{E(t(m['lede'], lang))}</p></div>
<section class="block"><div class="tiers">{"".join(cards)}</div>
<p class="note">{E(t(m['note'], lang))}</p></section>
</div>"""
        + footer(lang))

def page_lagoon(lang):
    g = PAGES["lagoon"]
    body = "".join("<p>%s</p>" % E(p) for p in (g["body"]["ar"] if lang == "ar" else g["body"]["en"]))
    facts = "".join(
        '<li><span class="k">{k}</span><span class="v{w}">{v}</span></li>'.format(
            k=E(t(f, lang)), v=E(t(f, lang, "v_")), w=" warn" if f.get("warn") else "")
        for f in g["facts"])
    return (head(f"{t(g['title'],lang)} · {t(SITE['brand'],lang)}", lang, t(g['headline'], lang),
                 f'<style>.fac-hero{{--hero-img:url("{HERO_IMG}")}}</style>')
        + header(lang, "lagoon")
        + f"""<section class="fac-hero"><div class="wrap">
  <p class="kicker">{E(t(g['kicker'], lang))} · {E(t(g['title'], lang))}</p>
  <h1>{E(t(g['headline'], lang))}</h1>
</div></section>
<div class="wrap"><div class="fac-grid">
  <div class="body">{body}</div>
  <aside class="aside"><ul class="facts">{facts}</ul>
    <a class="btn btn-primary" href="membership.html">{E(t(SITE['cta']['seeall'], lang))}</a></aside>
</div></div>"""
        + footer(lang))

def page_visit(lang):
    v = PAGES["visit"]
    rows = "".join(
        '<li><span class="k">{k}</span><span class="v"{fl}>{val}</span></li>'.format(
            k=E(t(r, lang)), val=E(t(r, lang, "v_")),
            fl=' lang="en" dir="ltr" data-foreign' if r["en"] == "Telephone" else "")
        for r in v["rows"])
    return (head(f"{t(v['title'],lang)} · {t(SITE['brand'],lang)}", lang, t(v['lede'], lang))
        + header(lang, "visit")
        + f"""<div class="wrap">
<div class="page-head"><h1>{E(t(v['title'], lang))}</h1><p>{E(t(v['lede'], lang))}</p></div>
<section class="block"><ul class="kv">{rows}</ul></section>
</div>"""
        + footer(lang))


def page_join(lang):
    j, m = PAGES["join"], PAGES["membership"]
    rtl = lang == "ar"
    req = E(t(j["fields"]["required"], lang))

    # --- step 1: tier + billing ---
    bill = j["billing"]
    switch = "".join(
        '<label><input type="radio" name="billing" value="{v}"{chk}><span>{lab}</span></label>'.format(
            v=v, chk=" checked" if v == "annual" else "", lab=E(t(bill[v], lang)))
        for v in ("annual", "monthly"))
    tiers = []
    for tier in m["tiers"]:
        inc = "".join("<li>%s</li>" % E(x) for x in (tier["inc_ar"] if rtl else tier["inc_en"]))
        flag = ('<span class="flag">%s</span>' % E("الأكثر اختياراً" if rtl else "Most chosen")) if tier["feat"] else ""
        pa = tier["price"].get("annual")
        pm = tier["price"].get("monthly")
        tiers.append(
            '<label class="tier-opt">'
            '<input type="radio" name="tier" value="{id}" data-name="{nm}" '
            'data-price-annual="{pa}" data-price-monthly="{pm}"{chk} required>'
            '<span class="card">{flag}<span class="radio"></span>'
            '<span class="tname">{nm}</span>'
            '<span class="tprice">{plabel}<small>{per}</small></span>'
            '<ul>{inc}</ul></span></label>'.format(
                id=tier["id"], nm=E(t(tier, lang)),
                pa="" if pa is None else pa, pm="" if pm is None else pm,
                chk=" checked" if tier["feat"] else "",
                flag=flag, plabel=E("AED —" if pa is None else "AED {:,}".format(pa)),
                per=E(" / سنة" if rtl else " / year"), inc=inc))

    # --- step 2: details ---
    f = j["fields"]
    def field(fid, ftype, required=True, hint=""):
        return (
            '<div class="field"><label for="{id}">{lab}{star}</label>'
            '<input id="{id}" name="{id}" type="{ty}"{req} autocomplete="{ac}">'
            '{hint}</div>').format(
            id=fid, lab=E(t(f[fid], lang)),
            star=' <span class="req" title="%s">*</span>' % req if required else "",
            ty=ftype, req=" required" if required else "",
            ac={"name": "name", "mobile": "tel", "email": "email",
                "dob": "bday", "eid": "off"}.get(fid, "off"),
            hint='<span class="hint">%s</span>' % E(hint) if hint else "")

    consents = "".join(
        '<label class="consent"><input type="checkbox" name="{id}"{req}>'
        '<span><b>{t}</b>{d}</span></label>'.format(
            id=c["id"], req=" required" if c["req"] else "",
            t=E(t(c, lang)), d=E(c["d_ar"] if rtl else c["d_en"]))
        for c in j["consents"])

    # --- step 3: summary + gateway hand-off ---
    sm = j["summary"]
    def row(key, val_attr, cls=""):
        return ('<div class="row {cls}"><dt>{k}</dt><dd data-sum="{a}">—</dd></div>'
                ).format(cls=cls, k=E(t(sm[key], lang)), a=val_attr)
    summary = (
        '<div class="summary"><h3>{title}</h3><dl>'
        '{tier}{billing}'
        '<div class="row"><dt>{joining}</dt><dd>{included}</dd></div>'
        '<div class="row"><dt>{starts}</dt><dd>{today}</dd></div>'
        '{net}{vat}{total}'
        '</dl></div>').format(
        title=E(t(sm["title"], lang)),
        tier=row("tier", "tier"), billing=row("billing", "billing"),
        joining=E(t(sm["joining"], lang)), included=E(t(sm["included"], lang)),
        starts=E(t(sm["starts"], lang)), today=E(t(sm["today"], lang)),
        net='<div class="row"><dt>%s</dt><dd data-sum="net">—</dd></div>' % E(t(sm["tier"], lang)),
        vat='<div class="row"><dt>%s</dt><dd data-sum="vat">—</dd></div>' % E(t(sm["vat"], lang)),
        total='<div class="row total"><dt>%s</dt><dd data-sum="total">—</dd></div>' % E(t(sm["total"], lang)))

    pay = j["pay"]
    # --- step 4: done ---
    dn = j["done"]
    qr = "".join('<i%s></i>' % ("" if k in (0,1,3,4,5,7,9,11,12,13,15,17,19,20,21,23,24) else ' class="off"')
                 for k in range(25))
    links = "".join(
        '<a href="{h}">{l}<span aria-hidden="true">{arrow}</span></a>'.format(
            h=l["href"], l=E(t(l, lang)), arrow="←" if rtl else "→")
        for l in dn["links"])

    i18n = json.dumps({
        "annual": t(bill["annual"], lang), "monthly": t(bill["monthly"], lang),
        "gateway": t(pay["gateway"], lang), "dash": "AED —",
        "stepWord": "الخطوة" if rtl else "Step", "of": "من" if rtl else "of",
        "fixErrors": "يرجى إكمال الحقول المحددة." if rtl else "Please complete the highlighted fields.",
    }, ensure_ascii=False)

    step_labels = [t(x, lang) for x in j["steps"]]
    prog = "".join(
        '<li data-state="{st}"><span class="rail"></span><span class="lbl">{l}</span></li>'.format(
            st="now" if k == 0 else "todo", l=E(lab))
        for k, lab in enumerate(step_labels))

    return (head(f"{t(j['title'],lang)} · {t(SITE['brand'],lang)}", lang, t(j['lede'], lang))
        + header(lang, "membership")
        + f"""<div class="wrap join">
<div class="page-head" style="border-block-end:0;padding-block-end:.6rem">
  <h1>{E(t(j['title'], lang))}</h1><p>{E(t(j['lede'], lang))}</p>
</div>
<p class="demo-note">{E(t(j['demo'], lang))}</p>

<form data-join novalidate data-i18n='{i18n}'>
  <ol class="progress">{prog}</ol>
  <p class="step-count"></p>
  <p class="form-error" hidden role="alert"></p>

  <fieldset class="step" data-label="{E(step_labels[0])}">
    <legend>{E(step_labels[0])}</legend>
    <div class="switch">{switch}</div>
    <p class="switch-note">{E(t(bill['save'], lang))}</p>
    <div class="tier-list">{"".join(tiers)}</div>
    <div class="step-nav"><span class="spacer"></span>
      <button type="button" class="btn btn-primary" data-next>{E(t(j['nav']['next'], lang))}</button></div>
  </fieldset>

  <fieldset class="step" data-label="{E(step_labels[1])}" hidden>
    <legend>{E(step_labels[1])}</legend>
    <p class="notice">{E(t(j['eligibility'], lang))}</p>
    {field("name","text")}
    <div class="grid2">{field("mobile","tel")}{field("dob","date")}</div>
    {field("email","email")}
    {field("eid","text",True,t(f['eid_hint'], lang))}
    {consents}
    <div class="step-nav">
      <button type="button" class="btn btn-quiet" data-back>{E(t(j['nav']['back'], lang))}</button>
      <span class="spacer"></span>
      <button type="button" class="btn btn-primary" data-next>{E(t(j['nav']['next'], lang))}</button></div>
  </fieldset>

  <fieldset class="step" data-label="{E(step_labels[2])}" hidden>
    <legend>{E(step_labels[2])}</legend>
    {summary}
    <label class="consent"><input type="checkbox" name="renew" checked>
      <span><b>{E(t(pay['renew'], lang))}</b>{E(pay['renew']['d_ar'] if rtl else pay['renew']['d_en'])}</span></label>
    <div class="step-nav">
      <button type="button" class="btn btn-quiet" data-back>{E(t(j['nav']['back'], lang))}</button>
      <span class="spacer"></span>
      <button type="button" class="btn btn-primary" data-next data-paylabel>{E(t(pay['gateway'], lang))}</button></div>
    <p class="pay-explain">{E(t(pay['explain'], lang))}</p>
  </fieldset>

  <fieldset class="step" data-label="{E(step_labels[3])}" hidden>
    <legend>{E(step_labels[3])}</legend>
    <div class="done-card">
      <span class="tick" aria-hidden="true">✓</span>
      <h3>{E(t(dn['title'], lang))}</h3>
      <p>{E(t(dn['lede'], lang))}</p>
    </div>
    <div class="mcard">
      <div><span class="lbl">{E('عضوة · ذهبية' if rtl else 'Member · Gold')}</span>
        <div class="who">{E('فاطمة الحوسني' if rtl else 'Fatima Al Hosani')}</div>
        <span class="lbl" style="color:#E3C9D4">{E('٤٤٧١ ٠٩٢٨' if rtl else '4471 0928')}</span></div>
      <div class="qr" aria-hidden="true">{qr}</div>
    </div>
    <h4 style="font-family:var(--f-mono);font-size:.63rem;letter-spacing:.11em;text-transform:uppercase;color:var(--muted);margin:0 0 .5rem;font-weight:400">{E(t(dn['next'], lang))}</h4>
    <div class="next-links">{links}</div>
  </fieldset>
</form>
</div>
<script src="{asset('js/join.js')}" defer></script>"""
        + footer(lang))


ROSETTE_WHITE = ('<svg class="rosette" viewBox="0 0 100 100" aria-hidden="true">'
    '<g fill="none" stroke="#fff" stroke-width="3">'
    + "".join('<ellipse cx="50" cy="34" rx="9" ry="24"%s/>' %
              ("" if a == 0 else ' transform="rotate(%d 50 50)"' % a)
              for a in range(0, 360, 45)) + "</g></svg>")

def _state_label(ev, lang):
    st = ev["state"]
    words = {
        "open":  ("Registration open", "التسجيل مفتوح"),
        "few":   ("{n} places left",   "بقي {n} أماكن"),
        "full":  ("Spectator list full","القائمة مكتملة"),
        "free":  ("Free · members",    "مجاني · للعضوات"),
        "live":  ("Live",              "جارٍ الآن"),
    }[st]
    txt = words[1] if lang == "ar" else words[0]
    return st, txt.replace("{n}", num(ev.get("left", ""), lang))

def page_events(lang):
    e = PAGES["events"]
    kinds = {k["id"]: k for k in EVENTS["kinds"]}
    chips = ['<button class="chip" data-facet="kind" data-value="all" aria-pressed="true">%s</button>'
             % E("الكل" if lang == "ar" else "All")]
    for k in EVENTS["kinds"]:
        chips.append('<button class="chip" data-facet="kind" data-value="%s" aria-pressed="false">'
                     '<span class="dot" style="background:%s"></span>%s</button>'
                     % (k["id"], k["color"], E(t(k, lang))))
    groups = []
    for mo in EVENTS["months"]:
        evs = [x for x in EVENTS["events"] if x["month"] == mo["id"]]
        if not evs: continue
        cards = []
        for ev in evs:
            k = kinds[ev["kind"]]
            scls, slabel = _state_label(ev, lang)
            cards.append(
                '<a class="ev" data-item data-kind="{kid}" href="event-{id}.html" '
                'style="--k1:{c1};--k2:{c2}">'
                '<span class="art">{rose}<span class="kind">{kname}</span></span>'
                '<span class="tx"><span class="when">{when}</span><h3>{name}</h3><p>{d}</p>'
                '<span class="foot"><span class="state {scls}">{slabel}</span>'
                '<span class="go">{more}</span></span></span></a>'.format(
                    kid=ev["kind"], id=ev["id"], c1=k["color"], c2=k["color2"],
                    rose=ROSETTE_WHITE, kname=E(t(k, lang)),
                    when=E(ev["when_ar"] if lang == "ar" else ev["when_en"]),
                    name=E(t(ev, lang)),
                    d=E(ev["d_ar"] if lang == "ar" else ev["d_en"]),
                    scls=scls, slabel=E(slabel),
                    more=E("التفاصيل ←" if lang == "ar" else "Details →")))
        groups.append(
            '<section class="month-group" data-group><h2>{m}<span>{y}</span></h2>'
            '<div class="ev-grid">{c}</div></section>'.format(
                m=E(t(mo, lang)), y=E(num(mo["year"], lang)), c="".join(cards)))

    return (head(f"{t(e['title'],lang)} · {t(SITE['brand'],lang)}", lang, t(e['lede'], lang))
        + header(lang, "events")
        + f"""<div class="wrap">
<div class="page-head"><h1>{E(t(e['title'], lang))}</h1><p>{E(t(e['lede'], lang))}</p></div>
<div data-filterable>
  <div class="filters"><div class="filter-row">
    <span class="lab">{E(t(e['filter'], lang))}</span>{"".join(chips)}
  </div></div>
  {"".join(groups)}
  <p class="empty" data-empty hidden>{E(t(e['empty'], lang))}</p>
</div>
<p class="tt-note">{E(t(e['hire_link'], lang))} <a href="hire.html">{E(t(PAGES['hire']['title'], lang))}</a>.</p>
</div>
<script src="{asset('js/filter.js')}" defer></script>"""
        + footer(lang))

def page_event(ev, lang):
    e = PAGES["events"]
    k = {x["id"]: x for x in EVENTS["kinds"]}[ev["kind"]]
    scls, slabel = _state_label(ev, lang)
    partners = ""
    if ev["partners"]:
        marks = ('<span class="rule-gold"></span>'.join(
            '<span class="pmark">%s</span>' % E(p) for p in ev["partners"]))
        partners = ('<div class="wrap partners"><span class="lbl">{l}</span>{m}'
                    '<span class="lbl" style="margin-inline-start:auto">{n}</span></div>').format(
            l=E("بالتعاون مع" if lang == "ar" else "Presented with"), m=marks,
            n=E("تظهر شعارات الشركاء هنا فقط" if lang == "ar"
                else "Partner marks appear in this band only"))
    return (head(f"{t(ev,lang)} · {t(SITE['brand'],lang)}", lang,
                 ev["d_ar"] if lang == "ar" else ev["d_en"])
        + header(lang, "events")
        + f"""<section class="ev-hero" style="--k1:{k['color']};--k2:{k['color2']}">
{ROSETTE_WHITE}
<div class="wrap"><p class="kind">{E(t(k, lang))} · {E(ev['when_ar'] if lang=='ar' else ev['when_en'])}</p>
<h1>{E(t(ev, lang))}</h1></div></section>
{partners}
<div class="wrap">
<section class="block">
  <p style="font-size:1rem;color:var(--ink-2);max-width:60ch">{E(ev['d_ar'] if lang=='ar' else ev['d_en'])}</p>
  <div class="changes">
    <h3>{E(t(e['changes'], lang))}</h3>
    <p>{E(ev['changes_ar'] if lang=='ar' else ev['changes_en'])}</p>
  </div>
  <p><span class="state {scls}">{E(slabel)}</span></p>
  <p style="margin-block-start:1.2rem"><a class="btn btn-secondary" href="events.html">{E(t(e['back'], lang))}</a></p>
</section>
</div>"""
        + footer(lang))

def page_hire(lang):
    h, rtl = PAGES["hire"], lang == "ar"
    imgs = IMGS
    spaces = "".join(
        '<article class="space"><span class="im" style="--img:url({img})"></span>'
        '<span class="tx"><h3>{n}</h3><p>{d}</p>'
        '<dl><div><dt>{seat}</dt><dd>{sv}</dd></div>'
        '<div><dt>{stand}</dt><dd>{tv}</dd></div>'
        '<div><dt>{from_}</dt><dd>AED —</dd></div></dl></span></article>'.format(
            img=imgs.get(sp["img"], imgs["hero"]), n=E(t(sp, lang)),
            d=E(sp["d_ar"] if rtl else sp["d_en"]),
            seat=E("جلوس" if rtl else "Seated"), sv=E(num(sp["seated"], lang)),
            stand=E("وقوف" if rtl else "Standing"), tv=E(num(sp["standing"], lang)),
            from_=E("ابتداءً من" if rtl else "From"))
        for sp in HIRE["spaces"])

    marks = {"yes": ("Yes", "نعم"), "no": ("No", "لا"), "ask": ("Ask", "بالتنسيق")}
    rules = "".join(
        '<li><span class="m {m}">{ml}</span><span><b>{t}</b>{d}</span></li>'.format(
            m=r["m"], ml=E(marks[r["m"]][1] if rtl else marks[r["m"]][0]),
            t=E(t(r, lang)), d=E(r["d_ar"] if rtl else r["d_en"]))
        for r in HIRE["rules"])

    f = HIRE["fields"]
    occ = "".join(
        '<label><input type="radio" name="occasion" value="{id}"{c}><span>{l}</span></label>'.format(
            id=o["id"], c=" checked" if i == 0 else "", l=E(t(o, lang)))
        for i, o in enumerate(HIRE["occasions"]))
    spopts = "".join('<option value="%s">%s</option>' % (sp["id"], E(t(sp, lang)))
                     for sp in HIRE["spaces"])

    return (head(f"{t(h['title'],lang)} · {t(SITE['brand'],lang)}", lang, t(h['lede'], lang))
        + header(lang, "hire")
        + f"""<div class="wrap">
<div class="page-head"><h1>{E(t(h['title'], lang))}</h1><p>{E(t(h['lede'], lang))}</p></div>
<section class="block"><div class="spaces">{spaces}</div>

<div class="hire-grid">
  <div>
    <h2 class="sec">{E(t(h['rules_title'], lang))}</h2>
    <p style="font-size:.9rem;color:var(--ink-2);max-width:54ch">{E(t(h['rules_lede'], lang))}</p>
    <ul class="rules">{rules}</ul>
  </div>
  <form class="enquiry" novalidate>
    <h2>{E(t(h['enquire'], lang))}</h2>
    <div class="field"><label>{E(t(f['occasion'], lang))}</label>
      <div class="chips-field">{occ}</div></div>
    <div class="field"><label for="space">{E(t(f['space'], lang))}</label>
      <select id="space" name="space">{spopts}</select></div>
    <div class="grid2">
      <div class="field"><label for="date">{E(t(f['date'], lang))}</label>
        <input id="date" name="date" type="date"></div>
      <div class="field"><label for="guests">{E(t(f['guests'], lang))}</label>
        <input id="guests" name="guests" type="number" min="1" inputmode="numeric"></div>
    </div>
    <div class="field"><label for="hname">{E(t(f['name'], lang))}</label>
      <input id="hname" name="hname" type="text" autocomplete="name"></div>
    <div class="field"><label for="hmobile">{E(t(f['mobile'], lang))}</label>
      <input id="hmobile" name="hmobile" type="tel" autocomplete="tel"></div>
    <div class="field"><label for="notes">{E(t(f['notes'], lang))}</label>
      <textarea id="notes" name="notes"></textarea></div>
    <button class="btn btn-primary" type="button">{E(t(h['send'], lang))}</button>
    <p class="sla-note">{E(t(HIRE['sla'], lang))}</p>
    <p class="sla-note">{E(t(PAGES['join']['demo'], lang))}</p>
  </form>
</div>
</section>
</div>"""
        + footer(lang))


IMGS = {"hero": "/static/img/hero.jpg", "atrium": "/static/img/atrium.jpg",
        "dining": "/static/img/dining.jpg", "lounge": "/static/img/lounge.jpg"}

def page_directory(lang):
    d = PAGES["tenants"]
    cats = {c["id"]: c for c in TENANTS["categories"]}
    chips = ['<button class="chip" data-facet="cat" data-value="all" aria-pressed="true">%s</button>'
             % E("الكل" if lang == "ar" else "All")]
    for c in TENANTS["categories"]:
        chips.append('<button class="chip" data-facet="cat" data-value="%s" aria-pressed="false">%s</button>'
                     % (c["id"], E(t(c, lang))))
    cards = "".join(
        '<a class="tenant" data-item data-cat="{cid}" href="tenant-{id}.html">'
        '<span class="im" style="--img:url({img})"><span class="cat">{cat}</span></span>'
        '<span class="tx"><h3>{n}</h3><span class="op">{hrs}</span><p>{d}</p>'
        '<span class="foot"><span class="state {st}">{stl}</span>'
        '<span class="go">{more}</span></span></span></a>'.format(
            cid=x["cat"], id=x["id"], img=IMGS.get(x["img"], IMGS["atrium"]),
            cat=E(t(cats[x["cat"]], lang)), n=E(t(x, lang)),
            hrs=E(x["hours_ar"] if lang == "ar" else x["hours_en"]),
            d=E(x["d_ar"] if lang == "ar" else x["d_en"]),
            st=x["state"], stl=E(x["state_ar"] if lang == "ar" else x["state_en"]),
            more=E("التفاصيل ←" if lang == "ar" else "Details →"))
        for x in TENANTS["tenants"])

    return (head(f"{t(d['title'],lang)} · {t(SITE['brand'],lang)}", lang, t(d['lede'], lang))
        + header(lang, "directory")
        + f"""<div class="wrap">
<div class="page-head"><h1>{E(t(d['title'], lang))}</h1><p>{E(t(d['lede'], lang))}</p></div>
<div data-filterable>
  <div class="filters"><div class="filter-row">
    <span class="lab">{E(t(d['filter'], lang))}</span>{"".join(chips)}
  </div></div>
  <section class="block" data-group><div class="tenants">{cards}</div></section>
  <p class="empty" data-empty hidden>{E(t(d['empty'], lang))}</p>
</div>
<div class="own-rule"><b>{E(t(d['rule_k'], lang))}</b>{E(t(d['rule'], lang))}</div>
</div>
<script src="{asset('js/filter.js')}" defer></script>"""
        + footer(lang))

def page_tenant(x, lang):
    d, rtl = PAGES["tenants"], lang == "ar"
    cats = {c["id"]: c for c in TENANTS["categories"]}
    body = "".join("<p>%s</p>" % E(par) for par in (x["body_ar"] if rtl else x["body_en"]))
    facts = "".join(
        '<li><span class="k">{k}</span><span class="v{w}">{v}</span></li>'.format(
            k=E(t(fx, lang)), v=E(t(fx, lang, "v_")), w=" warn" if fx.get("warn") else "")
        for fx in x["facts"])
    services = ""
    if x["services"]:
        rows = "".join(
            '<tr><td class="sname">{n}<span>{d}</span></td>'
            '<td class="n">{m}</td><td class="n">AED —</td><td class="n">AED —</td></tr>'.format(
                n=E(t(sv, lang)), d=E(sv["d_ar"] if rtl else sv["d_en"]),
                m=E(("%s د" % num(sv["mins"], lang)) if rtl else ("%d min" % sv["mins"])))
            for sv in x["services"])
        services = (
            '<h2 class="sec" style="margin-block-start:1.6rem">{t}</h2><div class="tw"><table class="services">'
            '<thead><tr><th>{c1}</th><th style="text-align:end">{c2}</th>'
            '<th style="text-align:end">{c3}</th><th style="text-align:end">{c4}</th></tr></thead>'
            '<tbody>{rows}</tbody></table></div>').format(
            t=E(t(d["services_title"], lang)), c1=E(t(d["svc_col"], lang)),
            c2=E(t(d["dur_col"], lang)), c3=E(t(d["member_col"], lang)),
            c4=E(t(d["guest_col"], lang)), rows=rows)

    cta = t(d["book"], lang) if x["services"] else t(d["enquire"], lang)
    return (head(f"{t(x,lang)} · {t(SITE['brand'],lang)}", lang,
                 x["d_ar"] if rtl else x["d_en"],
                 f'<style>.fac-hero{{--hero-img:url("{IMGS.get(x["img"], IMGS["atrium"])}")}}</style>')
        + header(lang, "directory")
        + f"""<section class="fac-hero"><div class="wrap">
  <p class="kicker">{E(t(d['title'], lang))} · {E(t(cats[x['cat']], lang))}</p>
  <h1>{E(t(x, lang))}</h1>
</div></section>
<div class="wrap"><div class="fac-grid">
  <div class="body">
    <p style="font-family:var(--f-mono);font-size:.72rem;letter-spacing:.08em;color:var(--muted)">{E(x['hours_ar'] if rtl else x['hours_en'])}</p>
    {body}{services}
    <p class="licence">{E(t(TENANTS['licence'], lang))}</p>
  </div>
  <aside class="aside">
    <ul class="facts">{facts}</ul>
    <a class="btn btn-primary" href="visit.html">{E(cta)}</a>
    <p style="margin-block-start:.8rem"><a href="directory.html">{E(t(d['back'], lang))}</a></p>
  </aside>
</div></div>"""
        + footer(lang))


def _partner_band(lang):
    pr = ACADEMY["partner"]
    return f"""<div class="partner-band"><div class="wrap">
  <span class="who"><b>{E(pr['name_ar'] if lang=='ar' else pr['name_en'])}</b>
    <em>{E(pr['since_ar'] if lang=='ar' else pr['since_en'])}</em></span>
  <span class="rule-gold"></span>
  <span class="short">{E(pr['short'])}</span>
  <span class="prule">{E(pr['rule_ar'] if lang=='ar' else pr['rule_en'])}</span>
</div></div>"""

def page_academy(lang):
    a, rtl = PAGES["academy"], lang == "ar"
    groups = {g["id"]: g for g in ACADEMY["groups"]}
    blocks = []
    for g in ACADEMY["groups"]:
        sports = [x for x in ACADEMY["sports"] if x["group"] == g["id"]]
        if not sports: continue
        cards = "".join(
            '<a class="sport" href="sport-{id}.html" style="--sport:{col}">'
            '<h3>{n}</h3><span class="ages">{ages}</span><p>{d}</p>'
            '<span class="levels" role="img" aria-label="{lv} {r}/{tot}">{pips}</span>'
            '<span class="foot"><span class="state {st}">{stl}</span>'
            '<span class="go">{more}</span></span></a>'.format(
                id=x["id"], col=x["color"], n=E(t(x, lang)),
                ages=E(x["ages_ar"] if rtl else x["ages_en"]),
                d=E(x["d_ar"] if rtl else x["d_en"]),
                lv=E(t(a["levels"], lang)), r=x["reached"], tot=x["levels"],
                pips="".join('<i class="on"></i>' if k < x["reached"] else '<i></i>'
                             for k in range(x["levels"])),
                st=x["state"], stl=E(x["state_ar"] if rtl else x["state_en"]),
                more=E("التفاصيل ←" if rtl else "Details →"))
            for x in sports)
        blocks.append('<section class="sport-group"><h2>%s</h2><div class="sports">%s</div></section>'
                      % (E(t(g, lang)), cards))

    rows = "".join(
        '<tr><td>{n}</td><td class="n">{dates}</td><td class="n">{sess}</td>'
        '<td class="n">AED —</td><td class="n">AED —</td></tr>'.format(
            n=E(t(tm, lang)), dates=E(tm["dates_ar"] if rtl else tm["dates_en"]),
            sess=E(t(a["weekly"], lang) if tm.get("weekly") else num(tm["sessions"], lang)))
        for tm in ACADEMY["terms"])

    return (head(f"{t(a['title'],lang)} · {t(SITE['brand'],lang)}", lang, t(a['lede'], lang))
        + header(lang, "academy")
        + _partner_band(lang)
        + f"""<div class="wrap">
<div class="page-head"><h1>{E(t(a['title'], lang))}</h1><p>{E(t(a['lede'], lang))}</p></div>
{"".join(blocks)}
<section class="block">
  <h2 class="sec">{E(t(a['terms_title'], lang))}</h2>
  <div class="tw"><table class="terms-table">
    <thead><tr><th>{E(t(a['col_term'], lang))}</th><th>{E(t(a['col_dates'], lang))}</th>
      <th>{E(t(a['col_sessions'], lang))}</th><th>{E(t(a['col_member'], lang))}</th>
      <th>{E(t(a['col_guest'], lang))}</th></tr></thead>
    <tbody>{rows}</tbody>
  </table></div>
  <p class="terms-note">{E(t(a['terms_note'], lang))}</p>
  <div class="consent-note"><b>{E(t(a['consent_title'], lang))}</b>{E(t(ACADEMY['consent'], lang))}</div>
</section>
</div>"""
        + footer(lang))

def page_sport(x, lang):
    a, rtl = PAGES["academy"], lang == "ar"
    groups = {g["id"]: g for g in ACADEMY["groups"]}
    facts = [
        (t(a["ages"], lang),  x["ages_ar"] if rtl else x["ages_en"]),
        (t(a["when"], lang),  x["days_ar"] if rtl else x["days_en"]),
        (t(a["where"], lang), x["where_ar"] if rtl else x["where_en"]),
        (t(a["coach"], lang), x["coach_ar"] if rtl else x["coach_en"]),
        (t(a["levels"], lang), "%s / %s" % (num(x["reached"], lang), num(x["levels"], lang))),
        (t(a["places"], lang), x["state_ar"] if rtl else x["state_en"]),
    ]
    facts_html = "".join(
        '<li><span class="k">%s</span><span class="v">%s</span></li>' % (E(k), E(v))
        for k, v in facts)
    return (head(f"{t(x,lang)} · {t(a['title'],lang)} · {t(SITE['brand'],lang)}", lang,
                 x["d_ar"] if rtl else x["d_en"])
        + header(lang, "academy")
        + _partner_band(lang)
        + f"""<div class="wrap">
<div class="page-head" style="border-block-start:3px solid {x['color']};padding-block-start:1.2rem">
  <p class="kicker" style="color:{x['color']}">{E(t(groups[x['group']], lang))}</p>
  <h1>{E(t(x, lang))}</h1><p>{E(x['d_ar'] if rtl else x['d_en'])}</p>
</div>
<div class="fac-grid">
  <div class="body">
    <h2 class="sec">{E(t(a['levels'], lang))}</h2>
    <p style="font-size:.9rem;color:var(--ink-2);max-width:58ch">{E(
      'يتقدّم كل مستوى بامتحان في نهاية الفصل. تُوضع المشتركات الجدد بعد جلسة تقييم واحدة.'
      if rtl else
      'Each level is passed by assessment at the end of a term. New joiners are placed after a single trial session.')}</p>
    <span class="levels" style="--sport:{x['color']};max-width:18rem;margin-block-start:.6rem">{
      "".join('<i class="on"></i>' if k < x["reached"] else '<i></i>' for k in range(x["levels"]))}</span>
    <div class="consent-note"><b>{E(t(a['consent_title'], lang))}</b>{E(t(ACADEMY['consent'], lang))}</div>
  </div>
  <aside class="aside">
    <ul class="facts">{facts_html}</ul>
    <a class="btn btn-primary" href="visit.html">{E(t(a['enrol'], lang))}</a>
    <p style="margin-block-start:.8rem"><a href="academy.html">{E(t(a['back'], lang))}</a></p>
  </aside>
</div>
</div>"""
        + footer(lang))


# ---------------------------------------------------------------- member app
QR = "".join('<i%s></i>' % ("" if k in (0,1,3,4,5,7,9,11,12,13,15,17,19,20,21,23,24) else ' class="off"')
             for k in range(25))

def _app_shell(lang, page_id, title, body, back=None, script=False, sheet=""):
    rtl = lang == "ar"
    tabs = "".join(
        '<a href="{p}.html"{cur}><span class="g"></span>{l}</a>'.format(
            p=tb["page"], cur=' aria-current="page"' if tb["id"] == page_id else "",
            l=E(t(tb, lang)))
        for tb in APP["tabs"])
    other = "ar" if lang == "en" else "en"
    backlink = ('<a class="back" href="%s.html" aria-label="%s">%s</a>'
                % (back, E("رجوع" if rtl else "Back"), "→" if rtl else "←")) if back else ""
    i18n = json.dumps({k: APP["book"][k + ("_ar" if rtl else "_en")]
                       for k in ("book", "booked", "wait", "waiting")}, ensure_ascii=False)
    return (head(f"{title} · {t(SITE['brand'],lang)}", lang, t(APP['demo'], lang))
        .replace("<body>", '<body class="app">')
        + f"""<div class="app-shell" data-app data-i18n='{i18n}'>
<header class="app-top">{backlink}<h1>{E(title)}</h1><span class="sp"></span>
  <a class="lang" href="../{other}/{page_id and ('app-'+page_id) or 'app-home'}.html" lang="{other}">{'EN' if rtl else 'ع'}</a>
</header>
<div class="app-body">
  <p class="app-demo">{E(t(APP['demo'], lang))}</p>
  {body}
</div>
<nav class="app-tabs" aria-label="{'التنقل' if rtl else 'App'}">{tabs}</nav>
</div>{sheet}"""
        + (f'<script src="{asset("js/app.js")}" defer></script>' if script else "")
        + "</body></html>")

def _cat_colors():
    return {c["id"]: c["color"] for c in CLASSES["categories"]}

def page_app_home(lang):
    rtl, m, h = lang == "ar", APP["member"], APP["home"]
    st = APP["streak"]
    streak_days = "".join(
        '<span class="d{on}{td}"><i></i><em>{l}</em></span>'.format(
            on=" on" if st["done"][k] else "", td=" today" if k == st["today"] else "",
            l=E(lab))
        for k, lab in enumerate(st["days_ar"] if rtl else st["days_en"]))
    cols, studios = _cat_colors(), {x["id"]: x for x in CLASSES["studios"]}
    alerts = "".join(
        '<div class="app-alert {k}"><b>{t}</b>{d}</div>'.format(
            k=a["kind"], t=E(t(a, lang)), d=E(a["d_ar"] if rtl else a["d_en"]))
        for a in APP["alerts"])
    today = [x for x in CLASSES["sessions"] if x["day"] == "sun"][:4]
    rows = "".join(
        '<div class="app-cls" style="--cat:{c}"><span class="stripe"></span>'
        '<span class="t">{tm}<small>{mn}</small></span>'
        '<span class="n">{n}<span>{w}</span></span>'
        '<span class="act"><span class="spots">{sp}</span></span></div>'.format(
            c=cols[x["cat"]], tm=E(num(x["time"], lang)),
            mn=E(("%s د" % num(x["mins"], lang)) if rtl else ("%d min" % x["mins"])),
            n=E(t(x, lang)),
            w=E((x["coach_ar"] if rtl else x["coach_en"]) + " · " + t(studios[x["studio"]], lang)),
            sp=E(_state_words(x, lang)))
        for x in today)
    return _app_shell(lang, "home", h["greeting_ar"] if rtl else h["greeting_en"], f"""
<div class="app-card">
  <svg class="rz" viewBox="0 0 100 100" aria-hidden="true"><g fill="none" stroke="#D9B66A" stroke-width="4">{"".join('<ellipse cx="50" cy="34" rx="9" ry="24"%s/>' % ("" if a==0 else ' transform="rotate(%d 50 50)"' % a) for a in range(0,360,45))}</g></svg>
  <div class="top">
    <div><span class="lbl">{E(('عضوة · ' + m['tier_ar']) if rtl else ('Member · ' + m['tier_en']))}</span>
      <div class="who">{E(m['name_ar'] if rtl else m['name_en'])}</div>
      <span class="lbl" style="color:#E3C9D4">{E(m['valid_ar'] if rtl else m['valid_en'])}</span></div>
    <div class="qr" aria-hidden="true">{QR}</div>
  </div>
  <span class="scan">{E(h['scan_ar'] if rtl else h['scan_en'])} · {E(m['no_ar'] if rtl else m['no'])}</span>
</div>
<div class="streak">
  <div class="hd"><b>{E(st['title_ar'] if rtl else st['title_en'])}</b>
    <span>{E((st['count_ar'] if rtl else st['count_en']).replace('{n}', num(3, lang)))}</span></div>
  <div class="week">{streak_days}</div>
  <p class="note">{E(st['note_ar'] if rtl else st['note_en'])}</p>
</div>
<p class="app-lab">{E(h['next_ar'] if rtl else h['next_en'])}</p>
<div class="app-next" style="--cat:{cols['yoga']}">
  <span class="t">{E(num('09:00', lang))}<small>{E('اليوم' if rtl else 'TODAY')}</small></span>
  <span class="n">{E('بيلاتس ريفورمر' if rtl else 'Reformer Pilates')}<span>{E('نسرين · قاعة اليوغا' if rtl else 'Nesrine · Yoga Studio')}</span></span>
  <span class="go">{E(h['checkin_ar'] if rtl else h['checkin_en'])} ›</span>
</div>
{alerts}
<p class="app-lab">{E(h['today_ar'] if rtl else h['today_en'])}
  <a href="app-timetable.html">{E(h['all_ar'] if rtl else h['all_en'])} ›</a></p>
<div class="app-rows">{rows}</div>
""")

def _state_words(x, lang):
    free = x["cap"] - x["booked"]
    st = PAGES["timetable"]["states"]
    if free <= 0: return t(st, lang, "full_")
    if free <= 3: return t(st, lang, "few_").replace("{n}", num(free, lang))
    return t(st, lang, "open_").replace("{n}", num(free, lang))

def page_app_timetable(lang):
    rtl = lang == "ar"
    cols, studios = _cat_colors(), {x["id"]: x for x in CLASSES["studios"]}
    bk, sh = APP["book"], APP["sheet"]
    days = CLASSES["days"][:3]
    dates = ["07", "08", "09"]

    strip = "".join(
        '<a href="#{id}"{cur}><em>{l}</em><b>{n}</b><span class="dotmark"></span></a>'.format(
            id=d["id"], cur=' aria-current="true"' if k == 0 else "",
            l=E(t(d, lang, "short_")), n=E(num(dates[k], lang)))
        for k, d in enumerate(days))

    out = []
    for k, d in enumerate(days):
        rows = sorted([x for x in CLASSES["sessions"] if x["day"] == d["id"]], key=lambda r: r["time"])
        cards = []
        for x in rows:
            free = x["cap"] - x["booked"]
            full = free <= 0
            st = "wait" if full else "free"
            tmpl = PAGES["timetable"]["states"][("full_" if full else ("few_" if free <= 3 else "open_")) + ("ar" if rtl else "en")]
            when = "%s · %s" % (t(d, lang), num(x["time"], lang))
            who = (x["coach_ar"] if rtl else x["coach_en"]) + " · " + t(studios[x["studio"]], lang)
            cd = ("اليوم" if k == 0 else ("غداً" if k == 1 else "بعد يومين")) if rtl \
                 else ("Today" if k == 0 else ("Tomorrow" if k == 1 else "In 2 days"))
            cards.append(
                '<div class="app-cls" style="--cat:{c}" data-name="{nm}" data-when="{wh}" '
                'data-who="{wo}" data-countdown="{cd}"><span class="stripe"></span>'
                '<span class="t">{tm}<small>{mn}</small></span>'
                '<span class="n">{nm}<span>{wo}</span></span>'
                '<span class="act"><span class="spots" data-template="{tp}">{sp}</span>'
                '<button class="check" type="button" data-state="{st}" data-free="{fr}" '
                'aria-pressed="false" aria-label="{lbl}"></button></span></div>'.format(
                    c=cols[x["cat"]], nm=E(t(x, lang)), wh=E(when), wo=E(who), cd=E(cd),
                    tm=E(num(x["time"], lang)),
                    mn=E(("%s د" % num(x["mins"], lang)) if rtl else ("%d min" % x["mins"])),
                    tp=E(tmpl), sp=E(_state_words(x, lang)), st=st, fr=free,
                    lbl=E((bk["wait_ar"] if rtl else bk["wait_en"]) if full
                          else (bk["book_ar"] if rtl else bk["book_en"]))))
        out.append('<p class="app-lab" id="%s">%s</p><div class="app-rows">%s</div>'
                   % (d["id"], E(t(d, lang)), "".join(cards)))

    sheet = """<div class="sheet" data-sheet hidden role="dialog" aria-modal="true">
  <div class="sh-top"><button class="sh-close" type="button" data-sheet-close
    aria-label="{close}">&times;</button></div>
  <div class="sh-body">
    <span class="tick" aria-hidden="true">✓</span>
    <p class="when" data-sh="when"></p>
    <p class="what" data-sh="what"></p>
    <p class="who" data-sh="who"></p>
    <p class="counted">{counted}</p>
    <p class="countdown" data-sh="countdown"></p>
  </div>
  <div class="sh-actions">
    <button class="btn btn-primary" type="button">{cal}</button>
    <a class="btn btn-quiet" href="app-bookings.html">{mine}</a>
  </div>
</div>""".format(close=E(sh["close_ar"] if rtl else sh["close_en"]),
                 counted=E(sh["counted_ar"] if rtl else sh["counted_en"]),
                 cal=E(sh["cal_ar"] if rtl else sh["cal_en"]),
                 mine=E(sh["mine_ar"] if rtl else sh["mine_en"]))

    body = '<div class="daystrip">%s</div>%s' % (strip, "".join(out))
    return _app_shell(lang, "timetable",
                      APP["tabs"][1]["ar"] if rtl else APP["tabs"][1]["en"],
                      body, script=True, sheet=sheet)

def page_app_bookings(lang):
    rtl, b = lang == "ar", APP["bookings"]
    cols = _cat_colors()
    def block(rows):
        return "".join(
            '<div class="app-row" style="--cat:{c}"><span class="dot" style="background:{c}"></span>'
            '<span class="nm">{n}<span>{w}</span></span>'
            '<span class="end"><span class="v" style="font-family:var(--f-mono);font-size:.7rem;color:var(--muted)">{wh}</span>'
            '<span class="tagpill {tg}">{tl}</span></span></div>'.format(
                c=cols.get(r["cat"], "#8B7079"), n=E(t(r, lang)),
                w=E(r["who_ar"] if rtl else r["who_en"]),
                wh=E(r["when_ar"] if rtl else r["when_en"]),
                tg=r["tag"], tl=E(r["tag_ar"] if rtl else r["tag_en"]))
            for r in rows)
    up = [r for r in b["rows"] if r.get("upcoming")]
    hist = [r for r in b["rows"] if not r.get("upcoming")]
    rest = "".join(
        '<div class="emptyday"><span>%s</span><span>%s</span></div>'
        % (E(dn), E(b["noclass_ar"] if rtl else b["noclass_en"]))
        for dn in (b["restdays_ar"] if rtl else b["restdays_en"]))
    return _app_shell(lang, "account", b["title_ar"] if rtl else b["title_en"], f"""
<p class="app-lab">{E(b['upcoming_ar'] if rtl else b['upcoming_en'])}</p>
<div class="app-rows">{block(up)}</div>
<p class="app-lab">{E(b['week_ar'] if rtl else b['week_en'])}</p>
<div class="app-rows">{rest}</div>
<p class="app-lab">{E(b['history_ar'] if rtl else b['history_en'])}</p>
<div class="app-rows">{block(hist)}</div>
""", back="app-account")

def page_app_facilities(lang):
    rtl, f = lang == "ar", APP["facilities"]
    rows = "".join(
        '<div class="app-row"><span class="dot {st}"></span>'
        '<span class="nm">{n}<span>{v}</span></span>'
        '<span class="end">{btn}</span></div>'.format(
            st=r["st"], n=E(t(r, lang)), v=E(r["v_ar"] if rtl else r["v_en"]),
            btn=('<button class="bookbtn" type="button" data-state="free">%s</button>'
                 % E(f["reserve_ar"] if rtl else f["reserve_en"])) if r["book"] else "")
        for r in f["rows"])
    return _app_shell(lang, "facilities", f["title_ar"] if rtl else f["title_en"], f"""
<p class="app-lab">{E(f['lede_ar'] if rtl else f['lede_en'])}</p>
<div class="app-rows">{rows}</div>
""")

def page_app_academy(lang):
    rtl, a = lang == "ar", APP["academy"]
    pairs = [("next", None), ("term", None), ("attend", None), ("coach", None), ("consent", "warn")]
    items = "".join(
        '<li><span class="k">{k}</span><span class="v{w}">{v}</span></li>'.format(
            k=E(a[p + ("_ar" if rtl else "_en")]),
            v=E(a[p + ("_v_ar" if rtl else "_v_en")]),
            w=" warn" if flag else "")
        for p, flag in pairs)
    return _app_shell(lang, "academy", a["title_ar"] if rtl else a["title_en"], f"""
<div class="app-tile">
  <div class="row1"><span class="app-tier">{E(APP['member']['child_ar'] if rtl else APP['member']['child_en'])}</span></div>
  <span class="no">{E(a['child_line_ar'] if rtl else a['child_line_en'])}</span>
</div>
<ul class="kv-list">{items}</ul>
<p class="app-demo" style="border-inline-start-color:var(--action);background:var(--plum-100)">
  {E(a['consent_note_ar'] if rtl else a['consent_note_en'])}</p>
""")

def page_app_account(lang):
    rtl, ac, m = lang == "ar", APP["account"], APP["member"]
    stats = "".join(
        '<div class="meter-lab"><span>{k}</span><span>{v}</span></div>'.format(
            k=E(t(x, lang)),
            v=E(num(x["v"], lang) + (" / " + num(x["of"], lang) if x.get("of") else "")))
        for x in ac["stats"])
    menu = "".join(
        ('<a href="{h}.html">{l}<span class="v">{v} ›</span></a>' if x["href"] else
         '<span class="item">{l}<span class="v">{v}</span></span>').format(
            h=x["href"], l=E(t(x, lang)),
            v=E(x.get("v_ar" if rtl else "v_en", "")))
        for x in ac["menu"])
    days = ac["days_ar" if rtl else "days_en"].replace("{n}", num(m["renews_days"], lang))
    return _app_shell(lang, "account", ac["title_ar"] if rtl else ac["title_en"], f"""
<div class="app-tile">
  <div class="row1"><span class="app-tier">{E(m['tier_ar'] if rtl else m['tier_en'])}</span>
    <span class="no">{E(m['no_ar'] if rtl else m['no'])}</span></div>
  <div class="meter"><i style="width:{m['renews_pct']}%"></i></div>
  <div class="meter-lab"><span>{E(ac['renews_ar'] if rtl else ac['renews_en'])}</span><span>{E(days)}</span></div>
  <div style="display:flex;gap:.4rem;margin-block-start:.2rem">
    <button class="btn btn-primary" style="flex:1" type="button">{E(ac['renew_ar'] if rtl else ac['renew_en'])}</button>
    <button class="btn btn-quiet" style="flex:1" type="button">{E(ac['freeze_ar'] if rtl else ac['freeze_en'])}</button>
  </div>
</div>
<p class="app-lab">{E(ac['month_ar'] if rtl else ac['month_en'])}</p>
<div class="app-tile">{stats}</div>
<div class="app-menu">{menu}
  <span class="item danger">{E(ac['signout_ar'] if rtl else ac['signout_en'])}</span></div>
""")

APP_FNS = {"app-home": page_app_home, "app-timetable": page_app_timetable,
           "app-bookings": page_app_bookings, "app-facilities": page_app_facilities,
           "app-academy": page_app_academy, "app-account": page_app_account}


# ------------------------------------------------------------- admin console
def _cs_shell(lang, page_id, title, when, body, actions="", script=None):
    rtl = lang == "ar"
    C = CONSOLE
    links, seen = [], set()
    for item in C["nav"]:
        g = item.get("group")
        if g and g not in seen:
            seen.add(g)
            links.append('<span class="cs-grp">%s</span>' % E(t(C["groups"][g], lang)))
        links.append(
            '<a href="{p}.html"{cur}><span class="ic"></span>{l}{b}</a>'.format(
                p=item["page"], cur=' aria-current="page"' if item["id"] == page_id else "",
                l=E(t(item, lang)),
                b='<span class="badge">%s</span>' % E(num(item["badge"], lang)) if item.get("badge") else ""))
    other = "ar" if lang == "en" else "en"
    st = C["staff"]
    return (head(f"{title} · {t(SITE['brand'],lang)}", lang, t(C['demo'], lang))
        .replace("<body>", '<body class="console">')
        + f"""<div class="cs">
<nav class="cs-side" aria-label="{'وحدة التحكم' if rtl else 'Console'}">
  <span class="cs-brand">{MARK.replace(_MARK_PLUM, '#D9B66A')}
    <span><b>{E(t(SITE['brand'], lang))}</b><em>{E('وحدة التحكم' if rtl else 'Console')}</em></span></span>
  {"".join(links)}
</nav>
<div class="cs-main">
  <header class="cs-top"><h1>{E(title)}</h1><span class="when">{E(when)}</span>
    <span class="r">{actions}
      <a class="lang" href="../{other}/console-{page_id}.html" lang="{other}">{'EN' if rtl else 'ع'}</a>
      <span class="who"><i>{E(st['initials'])}</i>{E(t(st, lang, 'name_') if False else (st['name_ar'] if rtl else st['name_en']))}</span>
    </span></header>
  <div class="cs-body">
    <p class="cs-demo">{E(t(C['demo'], lang))}</p>
    {body}
  </div>
</div>
</div>"""
        + ((lambda u: f'<script src="{u}" defer></script>')(asset("js/" + script)) if script else "")
        + "</body></html>")

def page_console_today(lang):
    rtl, T = lang == "ar", CONSOLE["today"]
    cols, studios = _cat_colors(), {x["id"]: x for x in CLASSES["studios"]}
    tiles = ""
    for x in T["tiles"]:
        spark = ""
        if x.get("spark"):
            spark = '<span class="spark">%s</span>' % "".join(
                '<i%s style="height:%d%%"></i>' % (' class="last"' if k == len(x["spark"]) - 1 else "", v)
                for k, v in enumerate(x["spark"]))
        tiles += ('<div class="cs-tile {tone}"><span class="k">{k}</span><b>{v}</b>'
                  '<span class="sub">{s}</span>{sp}</div>').format(
            tone="" if x["tone"] == "plain" else x["tone"], k=E(t(x, lang)),
            v=E(num(x["v"], lang)), s=E(x["sub_ar"] if rtl else x["sub_en"]), sp=spark)

    today = [x for x in CLASSES["sessions"] if x["day"] == "sun"]
    rows = ""
    for x in today:
        free = x["cap"] - x["booked"]
        pct = int(round(x["booked"] / x["cap"] * 100))
        if x["time"] == "11:00":
            right = ('<span class="state full">%s</span>'
                     '<button class="btn btn-primary sm" type="button" style="font-size:.68rem;padding:.28rem .55rem">%s</button>'
                     % (E("المدربة غائبة" if rtl else "Instructor absent"),
                        E("إلغاء وإبلاغ" if rtl else "Cancel & notify")))
        else:
            cls = "full" if free <= 0 else ("few" if free <= 3 else "open")
            right = ('<span class="bar-mini"><i style="width:%d%%"></i></span>'
                     '<span class="state %s">%s</span>' % (pct, cls, E(_state_words(x, lang))))
        rows += ('<div class="lrow"><span class="stripe" style="background:{c}"></span>'
                 '<span class="t">{tm}</span><span class="nm">{n}<span>{w}</span></span>'
                 '<span class="rr">{r}</span></div>').format(
            c=cols[x["cat"]], tm=E(num(x["time"], lang)), n=E(t(x, lang)),
            w=E((x["coach_ar"] if rtl else x["coach_en"]) + " · " + t(studios[x["studio"]], lang)),
            r=right)

    sev = {"now": "var(--danger)", "warn": "var(--warning)", "info": "var(--info)"}
    pill = {"now": "full", "warn": "few", "info": "open"}
    needs = "".join(
        '<div class="lrow"><span class="stripe" style="background:{c}"></span>'
        '<span class="nm">{n}<span>{d}</span></span>'
        '<span class="rr"><span class="state {p}">{tg}</span></span></div>'.format(
            c=sev[x["sev"]], p=pill[x["sev"]], n=E(t(x, lang)),
            d=E(x["d_ar"] if rtl else x["d_en"]), tg=E(x["tag_ar"] if rtl else x["tag_en"]))
        for x in T["needs"])

    return _cs_shell(lang, "today", T["title_ar"] if rtl else T["title_en"],
        T["when_ar"] if rtl else T["when_en"], f"""
<div class="cs-tiles">{tiles}</div>
<div class="cols2">
  <div class="panel"><div class="ph"><b>{E(T['classes_ar'] if rtl else T['classes_en'])}</b>
    <span class="r"><a class="btn btn-quiet" style="font-size:.7rem;padding:.3rem .6rem" href="console-timetable.html">{E(CONSOLE['cms']['title_ar'].split(' · ')[0] if rtl else 'Open timetable')}</a></span></div>
    <div class="pb">{rows}</div></div>
  <div class="panel"><div class="ph"><b>{E(T['needs_ar'] if rtl else T['needs_en'])}</b></div>
    <div class="pb">{needs}</div></div>
</div>
""", actions='<a class="btn btn-secondary" href="console-broadcast.html" style="font-size:.72rem;padding:.34rem .65rem">%s</a>'
     % E("رسالة جديدة" if rtl else "New broadcast"))

def page_console_timetable(lang):
    rtl, M = lang == "ar", CONSOLE["cms"]
    cols = _cat_colors()
    hall = [x for x in CLASSES["sessions"] if x["studio"] == "hall"]
    times = ["08:00", "10:00", "18:00", "19:00"]
    days = CLASSES["days"][:6]
    cells = ['<span></span>'] + ['<span class="hd">%s</span>' % E(t(d, lang)) for d in days]
    for tm in times:
        cells.append('<span class="rl">%s</span>' % E(num(tm, lang)))
        for d in days:
            hit = next((x for x in hall if x["day"] == d["id"] and x["time"] == tm), None)
            if hit:
                sel = " sel" if (hit["time"] == "18:00" and hit["day"] == "sun") else ""
                cells.append('<span class="bk{s}" style="background:{c}"><b>{n}</b><span>{w}</span></span>'.format(
                    s=sel, c=cols[hit["cat"]], n=E(t(hit, lang)),
                    w=E(hit["coach_ar"] if rtl else hit["coach_en"])))
            else:
                cells.append('<span class="sl">+</span>')

    f, v = M["fields"], M["values"]
    def fld(key, val):
        return ('<div class="field"><label>{l}</label><div class="inp">{v}</div></div>'
                ).format(l=E(f[key + ("_ar" if rtl else "_en")]), v=E(val))
    targets = "".join(
        '<label class="chk"><input type="checkbox"{c}>{l}</label>'.format(
            c=" checked" if x["on"] else "", l=E(t(x, lang)))
        for x in M["targets"])

    poster_rows = "".join(
        '<span class="pr"><span>{d}</span><b>{n}</b><i style="background:{c}"></i></span>'
        '<span class="pr"><span>{tm}</span><b>{w}</b><span>{mn}</span></span>'.format(
            d=E((t({"en": x["day"][:3].upper(), "ar": x["day"]}, lang))),
            n=E(t(x, lang)), c=cols[x["cat"]], tm=E(num(x["time"], lang)),
            w=E(x["coach_ar"] if rtl else x["coach_en"]),
            mn=E(("%s د" % num(x["mins"], lang)) if rtl else ("%dm" % x["mins"])))
        for x in hall[:3])
    why = "".join('<p style="font-size:.78rem;color:var(--ink-2);margin:0 0 .6rem;line-height:1.55">%s</p>'
                  % E(x["ar"] if rtl else x["en"]) for x in M["why"])

    return _cs_shell(lang, "timetable", M["title_ar"] if rtl else M["title_en"],
        M["draft_ar"] if rtl else M["draft_en"], f"""
<div class="editor">
  <div class="panel"><div class="ph"><b>{E(M['studio_ar'] if rtl else M['studio_en'])}</b>
    <span class="r"><span class="when">{E(M['hint_ar'] if rtl else M['hint_en'])}</span></span></div>
    <div class="pb" style="overflow-x:auto"><div class="tt-grid">{"".join(cells)}</div></div></div>
  <div class="panel"><div class="ph"><b>{E(M['editing_ar'] if rtl else M['editing_en'])}</b></div>
    <div class="pb">
      {fld("name", v["name"])}
      {fld("namear", v["namear"])}
      <div class="grid2">{fld("start", num(v["start"], lang))}{fld("mins", num(v["mins"], lang))}</div>
      <div class="grid2">{fld("cap", num(v["cap"], lang))}{fld("cat", v["cat_ar"] if rtl else v["cat_en"])}</div>
      {fld("coach", v["coach_ar"] if rtl else v["coach_en"])}
      {fld("repeat", v["repeat_ar"] if rtl else v["repeat_en"])}
      <div class="pub"><span class="app-lab">{E(M['targets_ar'] if rtl else M['targets_en'])}</span>{targets}</div>
    </div></div>
</div>
<div class="panel"><div class="ph"><b>{E(M['poster_ar'] if rtl else M['poster_en'])}</b>
  <span class="r"><span class="when">{E(M['poster_sub_ar'] if rtl else M['poster_sub_en'])}</span></span></div>
  <div class="pb" style="display:grid;grid-template-columns:210px 1fr;gap:1rem;align-items:start">
    <div class="poster">
      <svg class="rz" viewBox="0 0 100 100" aria-hidden="true"><g fill="none" stroke="#D9B66A" stroke-width="3">{"".join('<ellipse cx="50" cy="34" rx="9" ry="24"%s/>' % ("" if a==0 else ' transform="rotate(%d 50 50)"' % a) for a in range(0,360,45))}</g></svg>
      <span class="ttl">{E(M['poster_title_ar'] if rtl else M['poster_title_en'])}</span>
      <span class="rows">{poster_rows}</span>
      <span class="pf">{E(M['poster_foot_ar'] if rtl else M['poster_foot_en'])}</span>
    </div>
    <div>{why}</div>
  </div></div>
""", actions=('<button class="btn btn-quiet" type="button" style="font-size:.72rem;padding:.34rem .65rem">%s</button>'
              '<button class="btn btn-primary" type="button" style="font-size:.72rem;padding:.34rem .65rem">%s</button>')
     % (E(M["dup_ar"] if rtl else M["dup_en"]), E(M["publish_ar"] if rtl else M["publish_en"])))

def page_console_inbox(lang):
    rtl, I = lang == "ar", CONSOLE["inbox"]
    srcs = {x["id"]: x for x in I["sources"]}
    threads = ""
    for th in I["threads"]:
        sc = srcs[th["src"]]
        sla_cls = "hot" if th.get("hot") else ("warm" if th.get("warm") else "cool")
        threads += ('<div class="ith{on}"><span class="av" style="background:{c}">{ab}</span>'
                    '<span class="tx"><b lang="en" dir="ltr" data-foreign>{who}</b>'
                    '<p{ard}{fl}>{msg}</p></span>'
                    '<span class="sla {s}">{sl}</span></div>').format(
            on=" on" if th.get("sel") else "", c=sc["color"], ab=E(sc["abbr"]),
            ard=' class="ar"' if th.get("ar_msg") else "",
            fl="" if th.get("ar_msg") else ' lang="en" dir="ltr" data-foreign',
            who=E(th["who"]),
            msg=E(th["msg"]), s=sla_cls, sl=E(th["sla_ar"] if rtl else th["sla_en"]))
    first = I["threads"][0]
    saved = "".join("<span>%s</span>" % E(t(x, lang)) for x in I["saved"])
    return _cs_shell(lang, "inbox", I["title_ar"] if rtl else I["title_en"],
        I["sub_ar"] if rtl else I["sub_en"], f"""
<div class="panel"><div class="inbox">
  <div class="ilist">{threads}</div>
  <div class="ipane">
    <div class="ihead"><span class="av" style="background:{srcs['ig']['color']};inline-size:21px;block-size:21px;border-radius:3px;display:grid;place-items:center;color:#fff;font-family:var(--f-mono);font-size:.5rem;font-weight:600">IG</span>
      <b class="ar">{E(first['who'])}</b>
      <span class="state full" style="background:var(--danger-bg);color:var(--danger)">{E(I['breach_ar'] if rtl else I['breach_en'])}</span>
      <span class="r" style="margin-inline-start:auto;display:flex;gap:.4rem">
        <button class="btn btn-quiet" type="button" style="font-size:.68rem;padding:.28rem .55rem">{E(I['assign_ar'] if rtl else I['assign_en'])}</button>
      </span></div>
    <div class="ithread">
      <span class="msg them ar">{E(first['msg'])}<span class="mt ar">{E(first['ctx_ar'] if rtl else first['ctx_en'])}</span></span>
      <span class="msg us ar">{E(I['reply_draft'])}<span class="mt ar">{E(I['draft_note_ar'] if rtl else I['draft_note_en'])}</span></span>
    </div>
    <div class="replies">
      <span class="app-lab">{E(I['saved_ar'] if rtl else I['saved_en'])}</span>
      <div class="saved">{saved}</div>
      <div style="display:flex;gap:.4rem;align-items:center;margin-block-start:.2rem">
        <button class="btn btn-primary" type="button" style="margin-inline-start:auto;font-size:.72rem;padding:.34rem .7rem">{E(I['public_ar'] if rtl else I['public_en'])}</button>
      </div>
    </div>
  </div>
</div></div>
<p class="chart-note">{E(I['note_ar'] if rtl else I['note_en'])}</p>
""")

def page_console_reports(lang):
    rtl, R = lang == "ar", CONSOLE["reports"]
    days = CLASSES["days"]
    def band(v):
        return "o1" if v <= 35 else "o2" if v <= 50 else "o3" if v <= 70 else "o4" if v <= 85 else "o5"
    cells = ['<span></span>'] + ['<span class="hd">%s</span>' % E(t(d, lang)) for d in days]
    for r, slot in enumerate(R["slots"]):
        cells.append('<span class="rl">%s</span>' % E(num(slot, lang)))
        for c in range(7):
            v = R["grid"][r][c]
            if v is None:
                cells.append('<span class="c none" title="%s">—</span>' % E(R["noclass_ar"] if rtl else R["noclass_en"]))
            else:
                cells.append('<span class="c %s" title="%s %s — %s%%">%s</span>' % (
                    band(v), E(t(days[c], lang)), E(num(slot, lang)), E(num(v, lang)), E(num(v, lang))))
    legend = "".join('<span class="sc"><i style="background:var(--o%d)"></i></span><span>%s</span>'
                     % (k + 1, E(num(b, lang).replace("%", "٪") if rtl else b))
                     for k, b in enumerate(R["bands"]))
    bars = "".join(
        '<div class="brow"><span class="lab">{l}</span><span class="track">'
        '<span class="fill{low}" style="width:{v}%"></span></span><span class="val">{vv}%</span></div>'.format(
            l=E(t(x, lang)), low=" low" if x["v"] < 50 else "", v=x["v"], vv=E(num(x["v"], lang)))
        for x in R["instructors"])
    srcs = {x["id"]: x for x in CONSOLE["inbox"]["sources"]}
    mx = max(x["n"] for x in R["leads"])
    sbars = "".join(
        '<div class="src"><span class="lab"><i style="background:var(--c-{s})"></i>{l}</span>'
        '<span class="track"><span class="fill" style="width:{w}%;background:var(--c-{s})"></span></span>'
        '<span class="val">{n}</span></div>'.format(
            s=x["src"], l=E(t(srcs[x["src"]], lang)), w=int(x["n"] / mx * 100), n=E(num(x["n"], lang)))
        for x in R["leads"])
    trows = "".join(
        '<tr><td>{l}</td><td class="n">{n}</td><td class="n">{m}</td><td class="n">{c}</td></tr>'.format(
            l=E(t(srcs[x["src"]], lang)), n=E(num(x["n"], lang)),
            m=E(x["median_ar"] if rtl else x["median_en"]), c=E(num(x["conv"], lang)))
        for x in R["leads"])
    return _cs_shell(lang, "reports", R["title_ar"] if rtl else R["title_en"],
        R["period_ar"] if rtl else R["period_en"], f"""
<div class="panel"><div class="ph"><b>{E(R['occ_ar'] if rtl else R['occ_en'])}</b>
  <span class="r"><span class="when">{E(R['occ_sub_ar'] if rtl else R['occ_sub_en'])}</span></span></div>
  <div class="pb"><div style="overflow-x:auto"><div class="hm" role="img" aria-label="{E(R['reading_ar'] if rtl else R['reading_en'])}">{"".join(cells)}</div></div>
    <div class="legend"><span>{E(R['legend_ar'] if rtl else R['legend_en'])}</span>{legend}
      <span class="sc none" style="margin-inline-start:.5rem"><i></i></span><span>{E(R['noclass_ar'] if rtl else R['noclass_en'])}</span></div>
    <p class="chart-note"><strong>{E('ما تقوله' if rtl else 'What it says.')}</strong> {E(R['reading_ar'] if rtl else R['reading_en'])}</p>
  </div></div>
<div class="cols2">
  <div class="panel"><div class="ph"><b>{E(R['instructors_ar'] if rtl else R['instructors_en'])}</b></div>
    <div class="pb"><div class="bars">{bars}</div>
      <div class="axis"><span></span><span class="tk"><span>{E(num(0, lang))}</span><span>{E(num(50, lang))}%</span><span>{E(num(100, lang))}%</span></span><span></span></div>
      <p class="chart-note">{E(R['inst_note_ar'] if rtl else R['inst_note_en'])}</p></div></div>
  <div class="panel"><div class="ph"><b>{E(R['leads_ar'] if rtl else R['leads_en'])}</b>
    <span class="r"><span class="when">{E(R['leads_sub_ar'] if rtl else R['leads_sub_en'])}</span></span></div>
    <div class="pb"><div class="bars">{sbars}</div>
      <div class="tw" style="margin-block-start:.7rem"><table class="services">
        <thead><tr><th>{E(R['col_source_ar'] if rtl else R['col_source_en'])}</th>
          <th style="text-align:end">{E(R['col_enq_ar'] if rtl else R['col_enq_en'])}</th>
          <th style="text-align:end">{E(R['col_reply_ar'] if rtl else R['col_reply_en'])}</th>
          <th style="text-align:end">{E(R['col_conv_ar'] if rtl else R['col_conv_en'])}</th></tr></thead>
        <tbody>{trows}</tbody></table></div>
      <p class="chart-note">{E(R['leads_note_ar'] if rtl else R['leads_note_en'])}</p></div></div>
</div>
""")

def page_console_broadcast(lang):
    rtl, B = lang == "ar", CONSOLE["broadcast"]
    auds = "".join(
        '<label><input type="radio" name="audience" value="{id}" data-reach="{r}" data-push="{p}" data-wa="{w}"{c}>'
        '<span>{l}</span></label>'.format(
            id=x["id"], r=x["reach"], p=x["push"], w=x["wa"],
            c=" checked" if x.get("sel") else "", l=E(t(x, lang)))
        for x in B["audiences"])
    chans = "".join(
        '<label><input type="checkbox"{c}><span>{l}</span></label>'.format(
            c=" checked" if x["on"] else "", l=E(t(x, lang)))
        for x in B["channels"])
    i18n = json.dumps({"compare": B["compare_ar"] if rtl else B["compare_en"]}, ensure_ascii=False)
    return _cs_shell(lang, "broadcast", B["title_ar"] if rtl else B["title_en"],
        E("مسودة" if rtl else "Draft"), f"""
<form class="bcast" data-broadcast novalidate data-i18n='{i18n}'>
  <div class="panel"><div class="ph"><b>{E('الرسالة' if rtl else 'Message')}</b></div>
    <div class="pb">
      <div class="field"><label>{E(B['audience_ar'] if rtl else B['audience_en'])}</label>
        <div class="seg">{auds}</div></div>
      <div class="field"><label>{E('المتأثرات' if rtl else 'Affected')}</label>
        <div class="inp">{E(B['affected_ar'] if rtl else B['affected_en'])}</div></div>
      <div class="field"><label>{E(B['en_label'])}</label>
        <div class="ta" lang="en" dir="ltr" data-foreign><b>{E(B['msg_en_title'])}</b>{E(B['msg_en_body'])}</div></div>
      <div class="field"><label>{E(B['ar_label'])}</label>
        <div class="ta ar"><b>{E(B['msg_ar_title'])}</b>{E(B['msg_ar_body'])}</div></div>
      <div class="field"><label>{E(B['channels_ar'] if rtl else B['channels_en'])}</label>
        <div class="seg">{chans}</div></div>
    </div></div>
  <div class="prev">
    <span class="app-lab">{E(B['preview_ar'] if rtl else B['preview_en'])}</span>
    <div class="push"><span class="ap"></span><span class="pt" lang="en" dir="ltr" data-foreign><b>{E(t(SITE['brand'], 'en'))}</b>
      <p>{E(B['msg_en_title'])}</p></span></div>
    <div class="push"><span class="ap"></span><span class="pt ar"><b>{E(SITE['brand']['ar'])}</b>
      <p>{E(B['msg_ar_title'])}</p></span></div>
    <span class="app-lab" style="margin-block-start:.3rem">{E(B['reach_ar'] if rtl else B['reach_en'])}</span>
    <span class="reach"><span>{E(B['r_audience_ar'] if rtl else B['r_audience_en'])}</span><span data-metric="audience">—</span></span>
    <span class="reach"><span>{E(B['r_push_ar'] if rtl else B['r_push_en'])}</span><span data-metric="push">—</span></span>
    <span class="reach"><span>{E(B['r_wa_ar'] if rtl else B['r_wa_en'])}</span><span data-metric="wa">—</span></span>
    <span class="reach total"><span>{E(B['r_total_ar'] if rtl else B['r_total_en'])}</span><span data-metric="total">—</span></span>
    <p style="font-size:.7rem;color:var(--muted);margin:.3rem 0 0;line-height:1.45" data-compare></p>
    <button class="btn btn-primary" type="button">{E(B['send_ar'] if rtl else B['send_en'])}</button>
  </div>
</form>
<p class="chart-note">{E(B['note_ar'] if rtl else B['note_en'])}</p>
""", script="console.js")

CONSOLE_FNS = {"console-today": page_console_today, "console-timetable": page_console_timetable,
               "console-inbox": page_console_inbox, "console-reports": page_console_reports,
               "console-broadcast": page_console_broadcast}

PAGE_FNS = {"index": page_home, "timetable": page_timetable,
            "membership": page_membership, "lagoon": page_lagoon, "visit": page_visit, "join": page_join,
            "events": page_events, "hire": page_hire,
            "directory": page_directory,
            "academy": page_academy}

def build():
    if DIST.exists(): shutil.rmtree(DIST)
    DIST.mkdir(parents=True)
    shutil.copytree(STATIC, DIST / "static")
    written = 0
    for lang in LANGS:
        out = DIST / lang
        out.mkdir(parents=True, exist_ok=True)
        for slug, fn in PAGE_FNS.items():
            (out / f"{slug}.html").write_text(fn(lang), encoding="utf-8")
            written += 1
        for ev in EVENTS["events"]:
            (out / f"event-{ev['id']}.html").write_text(page_event(ev, lang), encoding="utf-8")
            written += 1
        for tn in TENANTS["tenants"]:
            (out / f"tenant-{tn['id']}.html").write_text(page_tenant(tn, lang), encoding="utf-8")
            written += 1
        for sp in ACADEMY["sports"]:
            (out / f"sport-{sp['id']}.html").write_text(page_sport(sp, lang), encoding="utf-8")
            written += 1
        for slug, fn in APP_FNS.items():
            (out / f"{slug}.html").write_text(fn(lang), encoding="utf-8")
            written += 1
        for slug, fn in CONSOLE_FNS.items():
            (out / f"{slug}.html").write_text(fn(lang), encoding="utf-8")
            written += 1
    (DIST / "index.html").write_text(
        '<!doctype html><meta charset="utf-8">'
        '<meta http-equiv="refresh" content="0; url=en/index.html">'
        '<link rel="canonical" href="en/index.html">'
        '<p>Redirecting to <a href="en/index.html">Abu Dhabi Ladies Club</a>.</p>',
        encoding="utf-8")
    # --- deploy artefacts -------------------------------------------------
    # This is unreleased client work: a reconstructed mark, photography on an
    # assumed licence, and invented prices. It is shared by link, not indexed.
    (DIST / "robots.txt").write_text(
        "# Unreleased client preview — not for indexing.\n"
        "User-agent: *\nDisallow: /\n", encoding="utf-8")
    (DIST / "_headers").write_text(
        "/*\n"
        "  X-Robots-Tag: noindex, nofollow, noarchive, noimageindex\n"
        "  X-Content-Type-Options: nosniff\n"
        "  Referrer-Policy: no-referrer\n"
        "  X-Frame-Options: SAMEORIGIN\n", encoding="utf-8")
    (DIST / "_redirects").write_text(
        "/            /en/index.html   302\n"
        "/en          /en/index.html   302\n"
        "/ar          /ar/index.html   302\n", encoding="utf-8")

    print(f"built {written} pages -> {DIST}")
    print(f"  sessions in timetable: {len(CLASSES['sessions'])}")

if __name__ == "__main__":
    build()
    if "--serve" in sys.argv:
        import http.server, socketserver, functools
        os.chdir(DIST)
        port = int(os.environ.get("PORT", "8080"))
        h = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(DIST))
        socketserver.TCPServer.allow_reuse_address = True
        with socketserver.TCPServer(("0.0.0.0", port), h) as httpd:
            print(f"serving on 0.0.0.0:{port}")
            httpd.serve_forever()
