"""Past Works Archives: static data, page render, and product-URL redirects."""

from __future__ import annotations

import json
from html import escape
from pathlib import Path

import catalog as cat

ROOT = Path(__file__).resolve().parent
SITE = cat.SITE
ARCHIVE_DATA = SITE / "data" / "archive.json"
RETIRED_PATH = ROOT / "retired_slugs.json"
ARCHIVE_IMG = SITE / "assets" / "images" / "archive"
BANNER = (
    "If any of these past works speak to you let me know and "
    "I'll pull it out of the archives for you."
)
CONTACT_EMAIL = "theorganicmechanicshop@gmail.com"

SLUG_ORDER = [
    "choose-your-path",
    "ghostwhispers",
    "cant-put-my-thumb-on-it",
    "zeus-the-dog",
    "pendants",
    "in-the-depths-shower-curtian",
    "tapered-stainless-steel-tumbler",
    "higher-horizons-tapered-stainless-steel-tumbler",
    "tellie-ellie-tapered-stainless-steel-tumbler",
]


def load_retired_slugs() -> set[str]:
    if not RETIRED_PATH.exists():
        return set(SLUG_ORDER)
    data = json.loads(RETIRED_PATH.read_text(encoding="utf-8"))
    if isinstance(data, dict):
        return set(data.get("slugs") or SLUG_ORDER)
    if isinstance(data, list):
        return set(data)
    return set(SLUG_ORDER)


def load_archive() -> dict:
    if not ARCHIVE_DATA.exists():
        raise FileNotFoundError(f"archive data missing: {ARCHIVE_DATA}")
    return json.loads(ARCHIVE_DATA.read_text(encoding="utf-8"))


def shop_items(items: list[dict]) -> list[dict]:
    retired = load_retired_slugs()
    return [p for p in items if p.get("permalink") not in retired]


def _picture_html(pic: dict, alt: str, sizes: str, eager: bool = False) -> str:
    avif = pic.get("avif_srcset") or ""
    webp = pic.get("webp_srcset") or ""
    src = pic.get("src") or pic.get("full")
    w, h = pic.get("width") or "", pic.get("height") or ""
    loading = "eager" if eager else "lazy"
    parts = ["<picture>"]
    if avif:
        parts.append(f'  <source type="image/avif" srcset="{avif}" sizes="{sizes}">')
    if webp:
        parts.append(f'  <source type="image/webp" srcset="{webp}" sizes="{sizes}">')
    parts.append(
        f'  <img src="{src}" alt="{escape(alt, quote=True)}" width="{w}" height="{h}" '
        f'loading="{loading}" decoding="async">'
    )
    parts.append("</picture>")
    return "\n".join(parts)


def pictures_for(item: dict) -> list[dict]:
    title = item.get("display_name") or item.get("name") or item["slug"]
    out = []
    images = item.get("images") or []
    sizes = "(max-width: 900px) 100vw, 42vw"
    for i, pic in enumerate(images):
        alt = f"{title}" + ("" if i == 0 else f", view {i + 1}")
        src = pic.get("src") or pic.get("full")
        out.append({
            "html": _picture_html(pic, alt, sizes, eager=(i == 0)),
            "full": pic.get("full") or src,
            "webp_srcset": pic.get("webp_srcset") or "",
            "avif_srcset": pic.get("avif_srcset") or "",
            "alt": alt,
            "thumb": src,
        })
    return out


def render_archive(jinja) -> Path:
    data = load_archive()
    items = []
    for item in data.get("items") or []:
        row = dict(item)
        row["pictures"] = pictures_for(item)
        items.append(row)
    n = len(items)
    noun = "piece" if n == 1 else "pieces"
    email = data.get("email") or CONTACT_EMAIL
    socials = data.get("socials") or []
    crumbs = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": f"{cat.SITE_ORIGIN}/"},
            {"@type": "ListItem", "position": 2, "name": "Past Works Archives", "item": f"{cat.SITE_ORIGIN}/archive/"},
        ],
    }
    html = jinja.get_template("archive.html").render(
        title="Past Works Archives | the Organic Mechanic",
        description=(
            "Past works from The Organic Mechanic — paintings, handmade objects, "
            "and pieces that have left the shop, kept in the studio archives."
        ),
        canonical=f"{cat.SITE_ORIGIN}/archive/",
        og_type="website",
        og_title="Past Works Archives",
        og_image=f"{cat.SITE_ORIGIN}/assets/images/brand/og-default.jpg",
        og_image_alt="The Organic Mechanic — gold gear and Om seal, Hand Krafted Art",
        body_class="page-archive",
        nav="archive",
        json_ld=[json.dumps(crumbs, separators=(",", ":"))],
        email=email,
        socials=socials,
        banner=data.get("banner") or BANNER,
        count_label=f"{n} {noun}",
        items=items,
    )
    dest = cat.SITE / "archive" / "index.html"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(html, encoding="utf-8")
    return dest


def write_product_redirect(jinja, slug: str, title: str | None = None) -> Path:
    dest = cat.SITE / "product" / slug / "index.html"
    dest.parent.mkdir(parents=True, exist_ok=True)
    name = title or slug
    html = jinja.get_template("redirect.html").render(
        title=f"{name} has been archived",
        description=f"{name} has moved to the Past Works Archives.",
        canonical=f"{cat.SITE_ORIGIN}/archive/#{slug}",
        og_type="website",
        og_title=f"{name} — Past Works Archives",
        og_image=f"{cat.SITE_ORIGIN}/assets/images/brand/og-default.jpg",
        og_image_alt="The Organic Mechanic — gold gear and Om seal, Hand Krafted Art",
        body_class="page-archive-redirect",
        nav="archive",
        json_ld=[],
        redirect_to=f"/archive/#{slug}",
    )
    dest.write_text(html, encoding="utf-8")
    return dest


def write_retired_redirects(jinja) -> list[Path]:
    data = load_archive()
    titles = {item["slug"]: item.get("display_name") or item.get("name") for item in data.get("items") or []}
    written = []
    for slug in load_retired_slugs():
        written.append(write_product_redirect(jinja, slug, titles.get(slug)))
    return written
