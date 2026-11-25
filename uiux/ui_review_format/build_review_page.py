#!/usr/bin/env python3
"""Build one static, reviewable HTML page from a JSON review manifest.

Usage: python build_review_page.py manifest.json out.html [--inline]

Manifest contract: manifest_schema.md beside this file (in the LCA playbook,
uiux/ui_review_format/). Why the page looks this way: uiux/ui_review_format.md.
Standard library only; no network. Image paths are relative to the output file's
directory. With --inline every image is embedded as base64 so the single file can be
sent or opened anywhere. A missing image file is an error, never a broken image.
"""
import argparse
import base64
import hashlib
import html
import json
import struct
import sys
from pathlib import Path

OWNER_LABELS = {
    "either": "Either lead can decide",
    "product": "Product / domain lead decides",
    "engineering": "Engineering lead decides",
}
MAX_WIDTH = {"desktop": 560, "phone": 260}
MIME = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png"}
DEFAULT_LEGEND = (
    "<p>Each card is one change or one question. Read the summary and the yellow box: "
    "that is the ask. Open <b>Options</b> to see a screenshot of each choice, at the "
    "device sizes that matter, with the state each image comes from under it; click an "
    "image to enlarge it. <b>Details</b> holds technical background and links and is "
    "optional.</p>"
)


class BuildError(Exception):
    pass


def need(obj, key, where):
    if not isinstance(obj, dict) or key not in obj:
        raise BuildError(f"{where}: missing required key '{key}'")
    return obj[key]


def esc(text):
    return html.escape(str(text), quote=True)


def image_size(data, path):
    """Return (width, height) for a PNG or JPEG, read from its header."""
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return struct.unpack(">II", data[16:24])
    if data[:2] == b"\xff\xd8":
        i = 2
        while i + 9 < len(data):
            if data[i] != 0xFF:
                i += 1
                continue
            marker = data[i + 1]
            if marker == 0xFF or marker == 0x01 or 0xD0 <= marker <= 0xD8:
                i += 2 if marker != 0xFF else 1
                continue
            seglen = struct.unpack(">H", data[i + 2:i + 4])[0]
            if 0xC0 <= marker <= 0xCF and marker not in (0xC4, 0xC8, 0xCC):
                h, w = struct.unpack(">HH", data[i + 5:i + 9])
                return w, h
            i += 2 + seglen
    raise BuildError(f"cannot read image size (not a PNG or JPEG?): {path}")


class Builder:
    def __init__(self, manifest, out_dir, inline):
        self.m = manifest
        self.out_dir = out_dir
        self.inline = inline
        self.items = 0
        self.images = 0
        self.files = set()
        self.missing = []
        self.owner_labels = dict(OWNER_LABELS, **manifest.get("owner_labels", {}))
        self.cache = {}

    def load(self, src, where):
        """Return (data, sha) for an image, or None and record it as missing."""
        if "://" in src or src.startswith(("/", "data:")):
            raise BuildError(f"{where}: image src must be a path relative to the output file: {src}")
        path = (self.out_dir / src).resolve()
        if path.suffix.lower() not in MIME:
            raise BuildError(f"{where}: only .jpg, .jpeg and .png images are supported: {src}")
        if path not in self.cache:
            if not path.is_file():
                self.missing.append(f"{where}: {src} (looked for {path})")
                return None
            data = path.read_bytes()
            self.cache[path] = (data, hashlib.sha256(data).hexdigest(), image_size(data, path))
        self.files.add(path)
        return self.cache[path]

    def figure(self, img, where, same_as):
        src = need(img, "src", where)
        caption = need(img, "caption", where)
        kind = need(img, "kind", where)
        if kind not in MAX_WIDTH:
            raise BuildError(f"{where}: image kind must be 'desktop' or 'phone', got {kind!r}")
        self.images += 1
        loaded = self.load(src, where)
        if loaded is None:
            return "", None
        data, sha, (w, h) = loaded
        shown_w = min(w, MAX_WIDTH[kind])  # never upsample
        shown_h = round(h * shown_w / w)
        if self.inline:
            url = f"data:{MIME[Path(src).suffix.lower()]};base64," + base64.b64encode(data).decode()
        else:
            url = esc(src)
        tag = (f'<img src="{url}" width="{shown_w}" height="{shown_h}" loading="lazy" '
               f'alt="{esc(caption)}">')
        if not self.inline:
            tag = f'<a href="{url}" target="_blank" rel="noopener">{tag}</a>'
        note = ""
        if sha in same_as:
            note = f'<span class="same">no change: same image as {esc(same_as[sha])}</span>'
        return (f'<figure class="{kind}" style="width:{shown_w}px">{tag}'
                f'<figcaption>{esc(caption)} {note}</figcaption></figure>'), sha

    def option(self, opt, where, same_as):
        label = need(opt, "label", where)
        title = need(opt, "title", where)
        figs, shas = [], []
        for n, img in enumerate(opt.get("images", [])):
            fig, sha = self.figure(img, f"{where}, image {n + 1}", same_as)
            figs.append(fig)
            shas.append(sha)
        shots = "".join(figs) or '<p class="muted">No screenshot for this option.</p>'
        note = opt.get("note_html", "")
        return (f'<div class="option"><h4><span class="olabel">{esc(label)}</span>{esc(title)}</h4>'
                f'<div class="shots">{shots}</div>{note}</div>'), [s for s in shas if s]

    def item(self, it, sec_id):
        item_id = need(it, "id", f"section {sec_id}, an item")
        where = f"item {item_id}"
        title = need(it, "title", where)
        owner = it.get("owner")
        summary = need(it, "summary_html", where)
        ask = need(it, "ask", where)
        if owner is not None and owner not in self.owner_labels:
            raise BuildError(f"{where}: unknown owner {owner!r}; expected one of {sorted(self.owner_labels)}")
        self.items += 1
        tags = it.get("tags", [])
        pills = "".join(f'<span class="pill">{esc(t)}</span>' for t in tags)
        status = f'<p class="status">{esc(it["status"])}</p>' if it.get("status") else ""
        ask_box = (f'<div class="ask"><span class="k">The ask</span>{esc(ask)}</div>' if ask else "")
        score = ""
        if it.get("score") is not None:
            note = f' &middot; {esc(it["score_note"])}' if it.get("score_note") else ""
            score = f'<p class="score">Score: <b>{esc(it["score"])}</b>{note}</p>'
        options, same_as = [], {}
        for n, opt in enumerate(it.get("options", [])):
            html_opt, shas = self.option(opt, f"{where}, option {n + 1}", same_as)
            options.append(html_opt)
            for sha in shas:
                same_as.setdefault(sha, opt.get("label", "?"))
        opts = ""
        if options:
            labels = {str(o.get("label", "")).lower() for o in it.get("options", [])}
            noun = ("What it looks like" if len(options) == 1 else "Before and after"
                    if labels == {"before", "after"} else f"Options ({len(options)})")
            opts = (f'<details class="fold"><summary>{noun}: screenshots</summary>'
                    f'<div class="options">{"".join(options)}</div></details>')
        links = "".join(f'<li><a href="{esc(need(l, "href", where + ", a link"))}">'
                        f'{esc(need(l, "text", where + ", a link"))}</a></li>' for l in it.get("links", []))
        more = it.get("details_html", "") + (f"<ul>{links}</ul>" if links else "")
        details = f'<details class="fold more"><summary>Details</summary>{more}</details>' if more else ""
        rev = it.get("lavish_revision")
        rev_attr = f' data-lavish-revision="{esc(rev)}"' if rev else ""
        owner_span = (
            f'<span class="owner o-{esc(owner)}">{esc(self.owner_labels[owner])}</span>'
            if owner is not None else ""
        )
        meta_div = f'<div class="meta">{owner_span}{pills}</div>' if (owner_span or pills) else ""
        return (f'<article class="item" id="item-{esc(item_id)}" data-tags="{esc(json.dumps(tags))}"{rev_attr}>'
                f'<h3><span class="iid">{esc(item_id)}</span> {esc(title)}</h3>{status}'
                f'{meta_div}'
                f'<div class="summary">{summary}</div>{ask_box}{score}{opts}{details}</article>'), item_id, title

    def build(self):
        title = need(self.m, "title", "manifest")
        sections = need(self.m, "sections", "manifest")
        body, toc, seen, all_tags = [], [], set(), []
        for sec in sections:
            sec_id = need(sec, "id", "a section")
            heading = need(sec, "heading", f"section {sec_id}")
            cards, entries = [], []
            for it in need(sec, "items", f"section {sec_id}"):
                card, item_id, item_title = self.item(it, sec_id)
                if item_id in seen:
                    raise BuildError(f"item {item_id}: duplicate item id")
                seen.add(item_id)
                for t in it.get("tags", []):
                    if t not in all_tags:
                        all_tags.append(t)
                cards.append(card)
                entries.append(f'<li><a href="#item-{esc(item_id)}">{esc(item_id)} {esc(item_title)}</a></li>')
            body.append(f'<section class="sec" id="{esc(sec_id)}"><h2>{esc(heading)}</h2>'
                        f'{sec.get("intro_html", "")}{"".join(cards)}</section>')
            toc.append(f'<li><a href="#{esc(sec_id)}">{esc(heading)}</a> <span class="muted">({len(cards)})</span>'
                       f'<ol>{"".join(entries)}</ol></li>')
        src = self.m.get("source") or {}
        meta = [esc(self.m["generated"])] if self.m.get("generated") else []
        if src.get("branch"):
            meta.append(f'branch <code>{esc(src["branch"])}</code>')
        if src.get("commit"):
            meta.append(f'commit <code>{esc(src["commit"])}</code>')
        if src.get("pr"):
            meta.append(f'<a href="{esc(src["pr"])}">pull request</a>')
        chips = "".join(f'<button type="button" class="chip" data-tag="{esc(t)}" aria-pressed="false">{esc(t)}</button>'
                        for t in all_tags)
        revisions = ""
        if self.m.get("lavish_revisions") is not None:
            data = json.dumps(self.m["lavish_revisions"]).replace("</", "<\\/")
            revisions = f'<script type="application/json" data-lavish-revisions>{data}</script>'
        subtitle = f'<p class="sub">{esc(self.m["subtitle"])}</p>' if self.m.get("subtitle") else ""
        return PAGE.format(
            title=esc(title), subtitle=subtitle, meta=" &middot; ".join(meta),
            legend=self.m.get("legend_html") or DEFAULT_LEGEND, toc="".join(toc), chips=chips,
            body="".join(body), css=CSS, js=JS, revisions=revisions)


CSS = """
:root{color-scheme:light dark;--bg:#f5f4f0;--card:#fff;--ink:#1d1f21;--muted:#5f6368;--line:#dad7cf;--accent:#1f55a8;
--ask-bg:#fff4d1;--ask-line:#d49b00;--pill:#ebe8e1;--on:#1f55a8;--on-ink:#fff}
:root[data-theme=light]{color-scheme:light}
@media (prefers-color-scheme:dark){:root:not([data-theme=light]){--bg:#15171a;--card:#1f2226;--ink:#e7e6e2;--muted:#a4a8ae;
--line:#373c43;--accent:#93b6ff;--ask-bg:#3b321c;--ask-line:#c8961a;--pill:#2d3137;--on:#93b6ff;--on-ink:#111}}
:root[data-theme=dark]{color-scheme:dark;--bg:#15171a;--card:#1f2226;--ink:#e7e6e2;--muted:#a4a8ae;
--line:#373c43;--accent:#93b6ff;--ask-bg:#3b321c;--ask-line:#c8961a;--pill:#2d3137;--on:#93b6ff;--on-ink:#111}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.5 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;overflow-wrap:anywhere}
a{color:var(--accent)} code{font-size:.9em} .muted{color:var(--muted)}
header{max-width:1500px;margin:0 auto;padding:24px 16px 0}
h1{margin:0 0 4px;font-size:26px;line-height:1.25} .sub{margin:0 0 6px;color:var(--muted)}
.meta-line{font-size:14px;color:var(--muted);margin:0 0 12px}
.legend{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:4px 16px;font-size:15px}
.bar{display:flex;flex-wrap:wrap;gap:6px;align-items:center;margin:14px 0 0}
button{font:inherit;font-size:13px;color:var(--ink);background:var(--card);border:1px solid var(--line);border-radius:999px;padding:3px 11px;cursor:pointer}
button[aria-pressed=true]{background:var(--on);color:var(--on-ink);border-color:var(--on)}
.wrap{display:grid;grid-template-columns:250px minmax(0,1fr);gap:28px;max-width:1500px;margin:0 auto;padding:20px 16px 48px}
nav.toc{position:sticky;top:12px;align-self:start;max-height:calc(100vh - 24px);overflow:auto;font-size:14px}
nav.toc ol{list-style:none;margin:0;padding:0} nav.toc ol ol{margin:2px 0 10px 10px;font-size:13px}
nav.toc a{text-decoration:none} nav.toc li{margin:2px 0}
h2{font-size:21px;margin:8px 0 12px}
.item{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:18px 20px;margin:0 0 18px}
.item h3{margin:0 0 4px;font-size:19px;line-height:1.3} .iid{color:var(--muted);font-weight:500}
.status{margin:0 0 6px;font-size:14px;color:var(--muted)}
.meta{display:flex;flex-wrap:wrap;gap:6px;align-items:center;margin:0 0 8px}
.owner{font-size:12px;font-weight:700;border:1px solid var(--ink);border-radius:4px;padding:0 7px}
.pill{font-size:12px;background:var(--pill);border-radius:999px;padding:1px 9px}
.summary p{margin:6px 0}
.ask{border-left:5px solid var(--ask-line);background:var(--ask-bg);border-radius:6px;padding:10px 14px;margin:12px 0;font-weight:600}
.ask .k{display:block;font-size:12px;letter-spacing:.05em;text-transform:uppercase;color:var(--muted)}
.score{margin:6px 0;font-size:14px;color:var(--muted)}
details.fold{margin-top:10px;border-top:1px solid var(--line);padding-top:8px}
summary{cursor:pointer;font-weight:600;color:var(--accent)}
.options{display:flex;flex-wrap:wrap;gap:24px;margin-top:12px}
.option{flex:1 1 320px;min-width:0;max-width:100%}
.option h4{margin:0 0 8px;font-size:15px}
.olabel{display:inline-block;min-width:1.7em;text-align:center;background:var(--ink);color:var(--card);border-radius:4px;padding:0 6px;margin-right:8px}
.shots{display:flex;flex-wrap:wrap;gap:12px;align-items:flex-start}
figure{margin:0;flex:0 1 auto;min-width:0;max-width:100%}
figure img{display:block;width:100%;max-width:100%;height:auto;border:1px solid var(--line);border-radius:4px;cursor:zoom-in}
figcaption{font-size:13px;color:var(--muted);margin-top:4px}
.same{display:inline-block;font-size:12px;background:var(--pill);border-radius:4px;padding:0 6px;color:var(--ink)}
.more pre{overflow-x:auto} .more table{display:block;overflow-x:auto}
#lb{position:fixed;inset:0;background:rgba(0,0,0,.85);display:flex;align-items:center;justify-content:center;padding:12px;z-index:10;cursor:zoom-out}
#lb[hidden]{display:none} #lb img{max-width:100%;max-height:100%;background:#fff}
[hidden]{display:none!important}
@media (max-width:900px){.wrap{grid-template-columns:minmax(0,1fr)}
nav.toc{position:static;max-height:none} nav.toc ol ol{display:none}}
@media (max-width:520px){.item{padding:14px 12px} .option{flex-basis:100%} h1{font-size:22px}}
"""

JS = """
(function(){
var active=new Set(), clear=document.getElementById('all-tags');
function apply(){
  document.querySelectorAll('.item').forEach(function(it){
    var tags=JSON.parse(it.getAttribute('data-tags')||'[]');
    it.hidden=active.size>0&&!tags.some(function(t){return active.has(t);});
  });
  document.querySelectorAll('section.sec').forEach(function(s){
    s.hidden=active.size>0&&!s.querySelector('.item:not([hidden])');
  });
  document.querySelectorAll('nav.toc a[href^="#item-"]').forEach(function(a){
    var it=document.getElementById(a.getAttribute('href').slice(1));
    a.parentNode.hidden=!!(it&&it.hidden);
  });
  if(clear)clear.setAttribute('aria-pressed',String(active.size===0));
}
document.querySelectorAll('.chip').forEach(function(b){b.addEventListener('click',function(){
  var t=b.getAttribute('data-tag');
  if(active.has(t))active.delete(t);else active.add(t);
  b.setAttribute('aria-pressed',String(active.has(t)));apply();
});});
if(clear)clear.addEventListener('click',function(){active.clear();
  document.querySelectorAll('.chip').forEach(function(b){b.setAttribute('aria-pressed','false');});apply();});
function fold(open){document.querySelectorAll('details.fold').forEach(function(d){d.open=open;});}
document.getElementById('expand').addEventListener('click',function(){fold(true);});
document.getElementById('collapse').addEventListener('click',function(){fold(false);});
var lb=document.getElementById('lb'), big=lb.querySelector('img');
document.addEventListener('click',function(e){
  var img=e.target.closest&&e.target.closest('figure img'); if(!img)return;
  e.preventDefault(); big.src=img.currentSrc||img.src; big.alt=img.alt; lb.hidden=false;
});
lb.addEventListener('click',function(){lb.hidden=true;big.removeAttribute('src');});
document.addEventListener('keydown',function(e){if(e.key==='Escape'&&!lb.hidden)lb.click();});
})();
"""

PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title><style>{css}</style>{revisions}</head>
<body>
<header><h1>{title}</h1>{subtitle}<p class="meta-line">{meta}</p>
<div class="legend">{legend}</div>
<div class="bar"><button type="button" id="expand">Expand all</button>
<button type="button" id="collapse">Collapse all</button>
<span class="muted" style="margin-left:8px;font-size:13px">Filter:</span>
<button type="button" id="all-tags" aria-pressed="true">all</button>{chips}</div></header>
<div class="wrap"><nav class="toc" aria-label="Contents"><ol>{toc}</ol></nav>
<main>{body}</main></div>
<div id="lb" hidden><img alt=""></div>
<script>{js}</script>
</body></html>
"""


def main(argv=None):
    ap = argparse.ArgumentParser(description="Build a static UI review page from a JSON manifest.")
    ap.add_argument("manifest")
    ap.add_argument("out")
    ap.add_argument("--inline", action="store_true", help="embed every image as base64")
    args = ap.parse_args(argv)
    out = Path(args.out)
    try:
        manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
        builder = Builder(manifest, out.resolve().parent, args.inline)
        page = builder.build()
    except (BuildError, json.JSONDecodeError, OSError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    report = (f"{out}: {builder.items} items, {builder.images} images "
              f"({len(builder.files)} files), {len(builder.missing)} missing")
    if builder.missing:
        for m in builder.missing:
            print(f"error: missing image file: {m}", file=sys.stderr)
        print(report + "; page not written", file=sys.stderr)
        return 1
    try:
        out.write_text(page, encoding="utf-8")
    except OSError as e:
        print(f"error: cannot write {out}: {e}", file=sys.stderr)
        return 2
    size = out.stat().st_size
    print(report + f", {size / 1024:.0f} KB" + (" (images inlined)" if args.inline else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
