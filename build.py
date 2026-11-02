"""Builds the static steadywren.com site (GitHub Pages serves the repo root).

    python3 build.py

Sources: data/catalog.json (platforms + products), content/*.md (legal and support pages), assets/.
Output: index.html, <platform>/, privacy/, terms/, support/, 404.html, sitemap.xml - committed with the sources.
A new product = one entry in data/catalog.json (+ its image in assets/products/). No dependencies.
"""
import html
import json
import re
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SITE = "https://steadywren.com"
EMAIL = "support@steadywren.com"
# Cloudflare Worker that turns the contact form into an email (worker/). Until it is deployed the form falls back
# to opening the visitor's mail app with the message filled in.
CONTACT_ENDPOINT = "https://api.steadywren.com/contact"
CATALOG = json.loads((ROOT / "data" / "catalog.json").read_text())
PLATFORMS = CATALOG["platforms"]
PRODUCTS = CATALOG["products"]
CUSTOM = "Custom JS solution"

BIO = (
    "Hi, I'm Yurii - a full-stack developer (React, Node.js, Next.js, NestJS, Supabase) and the person behind "
    "Steadywren. I build data tools that run on marketplaces like Apify, MCPize and Atlassian: scrapers with the "
    "analysis built in, MCP servers for AI assistants and apps for teams. And I build custom JavaScript solutions "
    "when an off-the-shelf tool doesn't fit."
)

PRINCIPLES = [
    ("Clean, typed data", "Numbers are numbers, dates are ISO, missing values are empty - ready for a spreadsheet or "
                          "a database."),
    ("No silent failures", "If a site changes or blocks us, the run fails loudly instead of returning an empty "
                           "success. You never pay for garbage."),
    ("Checked every day", "Every product runs a daily health check, so breakages are caught before you notice them."),
    ("Fair pricing", "Pay per result, with a results limit on every product to cap your cost."),
    ("Public data only", "No logins and no personal data of private individuals."),
    ("Maintained, not abandoned", "When a site changes, products are updated - and every question gets a real "
                                  "answer from the person who built it."),
]

PAGES = [  # slug, source, title in the menu
    ("privacy", "privacy-policy.md", "Privacy"),
    ("terms", "eula.md", "Terms"),
    ("support", "support.md", "Support"),
]

e = html.escape


def inline(text):
    text = e(text, quote=False)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"`(.+?)`", r"<code>\1</code>", text)
    text = re.sub(r"(?<![\"/>])(https://[^\s<)]+[^\s<).,;])", r'<a href="\1">\1</a>', text)
    return re.sub(r"(?<![\w.>])([\w.+-]+@[\w-]+\.[\w.]+\w)", r'<a href="mailto:\1">\1</a>', text)


def markdown(source):
    """The small Markdown subset the content uses: headings, paragraphs, '-' lists, bold, code, links."""
    out, para, items = [], [], []

    def flush():
        if para:
            out.append(f"<p>{inline(' '.join(para))}</p>")
            para.clear()
        if items:
            out.append("<ul>" + "".join(f"<li>{inline(i)}</li>" for i in items) + "</ul>")
            items.clear()

    for line in source.splitlines():
        if not line.strip():
            flush()
        elif m := re.match(r"(#{1,3}) (.+)", line):
            flush()
            out.append(f"<h{len(m[1])}>{inline(m[2])}</h{len(m[1])}>")
        elif line.startswith("- "):
            if para:
                flush()
            items.append(line[2:])
        elif items and line.startswith("  "):
            items[-1] += " " + line.strip()
        else:
            para.append(line.strip())
    flush()
    return "\n".join(out)


def contact_modal(depth):
    """One topic per message (radio): the platform's logo badge or a custom JS solution."""
    options = [(p["name"], platform_logo(p, depth)) for p in PLATFORMS]
    options.append((CUSTOM, '<b class="code" aria-hidden="true">{ }</b><span>Custom JS solution</span>'))
    chips = "".join(f'<label class="chip"><input type="radio" name="topic" value="{e(name)}" required>'
                    f"<span>{inner}</span></label>" for name, inner in options)
    return f"""<dialog id="contact" class="modal" aria-labelledby="contact-title">
  <form id="contact-form" method="dialog" data-endpoint="{CONTACT_ENDPOINT}" data-email="{EMAIL}">
    <button class="close" type="button" data-close aria-label="Close">×</button>
    <h2 id="contact-title">Let's build something</h2>
    <p class="muted">Tell me what you need - a scraper, an MCP server, an Atlassian app or a custom JavaScript
    solution - and I will get back to you.</p>
    <fieldset><legend>What is it about?</legend><div class="chips">{chips}</div></fieldset>
    <label class="field">Your idea<textarea name="message" rows="5" required minlength="10"
      placeholder="What should it do, for whom, and by when?"></textarea></label>
    <label class="field">Your email<input name="email" type="email" required autocomplete="email"
      placeholder="you@company.com"></label>
    <label class="hp" aria-hidden="true">Leave empty<input name="website" tabindex="-1" autocomplete="off"></label>
    <button class="button" type="submit">Send</button>
    <p class="status" role="status" aria-live="polite"></p>
  </form>
</dialog>"""


def layout(title, body, depth, description, extra_head=""):
    up = "../" * depth
    nav = (f'<a href="{up}#platforms">Products</a>'
           + "".join(f'<a href="{up}{slug}/">{label}</a>' for slug, _, label in PAGES))
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(description)}">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(description)}">
<meta property="og:image" content="{SITE}/assets/og-image.png">
<link rel="icon" type="image/png" href="{up}assets/favicon-32.png">
<link rel="apple-touch-icon" href="{up}assets/apple-touch-icon.png">
<link rel="stylesheet" href="{up}assets/style.css">
{extra_head}<script src="{up}assets/app.js" defer></script>
</head>
<body>
<header class="bar">
  <a class="lockup" href="{up or './'}"><img src="{up}assets/steadywren-mark.svg" alt="" width="40" height="40"><span>steady<b>wren</b></span></a>
  <nav>{nav}<button class="link" type="button" data-contact>Contact</button></nav>
</header>
<main>
{body}
</main>
<footer class="bar">
  <span>© {date.today().year} Steadywren</span>
  <nav>{"".join(f'<a href="{up}{slug}/">{label}</a>' for slug, _, label in PAGES)}<a href="mailto:{EMAIL}">{EMAIL}</a></nav>
</footer>
{contact_modal(depth)}
</body>
</html>
"""


def platform_chip(p, depth=0):
    count = sum(1 for x in PRODUCTS if x["platform"] == p["id"])
    note = f"{count} product{'s' if count != 1 else ''}" if p["status"] == "live" else "coming soon"
    return (f'<a class="platform" href="{"../" * depth}{p["id"]}/" style="--accent:{p["accent"]}">'
            f'{platform_logo(p, depth)}<small>{note}</small></a>')


def platform_logo(p, depth=0, cls="logo"):
    """The platform's official logo (light/dark variants) or, where its brand rules forbid that, its name."""
    logo = p.get("logo")
    if not logo:
        return f'<i aria-hidden="true"></i><span>{e(p["name"])}</span>'
    base = f'{"../" * depth}assets/platforms/'
    img = (f'<picture class="{cls}{" full" if logo["full"] else ""}">'
           f'<source srcset="{base}{logo["dark"]}" media="(prefers-color-scheme: dark)">'
           f'<img src="{base}{logo["light"]}" alt="{e(p["name"])}"></picture>')
    return img if logo["full"] else img + f'<span>{e(p["name"])}</span>'


def home():
    chips = "".join(platform_chip(p) for p in PLATFORMS)
    # The track holds the chips twice and scrolls by half its width, so the loop has no visible seam.
    marquee = f'<div class="marquee" aria-label="Platforms"><div class="track">{chips * 4}</div></div>'
    principles = "\n".join(f"  <li><h3>{t}</h3><p>{e(p)}</p></li>" for t, p in PRINCIPLES)
    body = f"""<section class="hero">
  <img class="hero-mark" src="assets/steadywren-mark.svg" alt="Steadywren - a small blue wren" width="132" height="132">
  <h1>Small tools. Steady results.</h1>
  <p class="lead">{e(BIO)}</p>
</section>
<section id="platforms">
  <h2>Where my products live</h2>
  <p class="muted">Pick a platform to search everything I have built there.</p>
  {marquee}
</section>
<section class="cta">
  <h2>Have something to build?</h2>
  <p class="muted">Scrapers, MCP servers, Atlassian apps or a custom JavaScript solution - tell me about it.</p>
  <button class="button big" type="button" data-contact>Contact me</button>
</section>
<section>
  <h2>How I work</h2>
  <ul class="principles">
{principles}
  </ul>
</section>"""
    return layout("Steadywren - small tools, steady results", body, 0,
                  "Yurii's data tools on Apify, MCPize and Atlassian, and custom JavaScript solutions. Clean, typed "
                  "data, pay per result.")


def platform_page(p):
    items = [x for x in PRODUCTS if x["platform"] == p["id"]]
    store = (f'<a class="button ghost" href="{e(p["store"])}" target="_blank" rel="noopener">All on {e(p["name"])} →</a>'
             if p["store"] else "")
    if items:
        cards = "\n".join(f"""  <li><a class="card" href="{e(x["url"])}" target="_blank" rel="noopener">
    <img src="../assets/products/{e(x["image"])}" alt="" width="72" height="72" loading="lazy">
    <div><h3>{e(x["title"])}</h3><p>{e(x["description"])}</p><span class="go">Open on {e(p["name"])} →</span></div>
  </a></li>""" for x in items)
        index = json.dumps([{"title": x["title"], "description": x["description"], "keywords": x.get("keywords", "")}
                            for x in items]).replace("</", "<\\/")
        listing = f"""<label class="search"><span class="sr">Search {e(p["name"])} products</span>
  <input id="search" type="search" placeholder="Search products - try “flipa” or “reviews”" autocomplete="off"></label>
<p class="muted small" id="search-count">{len(items)} products</p>
<ul class="cards" id="results">
{cards}
</ul>
<p class="empty" id="no-results" hidden>Nothing found. <button class="link" type="button" data-contact>Ask me to build it →</button></p>
<script type="application/json" id="search-index">{index}</script>"""
    else:
        listing = """<div class="soon"><h3>Coming soon</h3><p class="muted">The first product here is in the works.
  Want to be first to know, or have something specific in mind?</p>
  <button class="button" type="button" data-contact>Contact me</button></div>"""
    body = f"""<section class="page-head" style="--accent:{p["accent"]}">
  <a class="back" href="../#platforms">← All platforms</a>
  <h1>{platform_logo(p, 1, "logo big") if p.get("logo") else '<i aria-hidden="true"></i>' + e(p["name"])}</h1>
  <p class="lead left">{e(p["tagline"])}</p>
  {store}
</section>
<section>
{listing}
</section>"""
    return layout(f"{p['name']} products - Steadywren", body, 1, f"Steadywren products on {p['name']}: {p['tagline']}")


def main():
    (ROOT / "index.html").write_text(home())
    for p in PLATFORMS:
        page = ROOT / p["id"] / "index.html"
        page.parent.mkdir(exist_ok=True)
        page.write_text(platform_page(p))
    for slug, source, label in PAGES:
        text = (ROOT / "content" / source).read_text()
        title = re.match(r"# (.+)", text)[1]
        page = ROOT / slug / "index.html"
        page.parent.mkdir(exist_ok=True)
        page.write_text(layout(f"{title} - Steadywren", f'<article class="doc">\n{markdown(text)}\n</article>', 1,
                               f"Steadywren {label.lower()}."))
    (ROOT / "404.html").write_text(layout("Not found - Steadywren", '<section class="hero"><h1>Page not found.</h1>'
                                          '<p class="lead"><a href="/">Back to the home page</a></p></section>', 0,
                                          "Page not found."))
    urls = [f"{SITE}/"] + [f"{SITE}/{p['id']}/" for p in PLATFORMS] + [f"{SITE}/{s}/" for s, _, _ in PAGES]
    (ROOT / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?>\n'
                                      '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
                                      + "".join(f"  <url><loc>{u}</loc></url>\n" for u in urls) + "</urlset>\n")
    print("built:", ", ".join(["index.html"] + [f"{p['id']}/" for p in PLATFORMS]
                              + [f"{s}/" for s, _, _ in PAGES] + ["404.html", "sitemap.xml"]))


if __name__ == "__main__":
    main()
