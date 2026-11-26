"""Render product pages, shop listings, and the sitemap from the scrape catalog."""

from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

import catalog as cat

ROOT = Path(__file__).resolve().parent
SITE = cat.SITE
TODAY = date.today().isoformat()


def env() -> Environment:
    return Environment(
        loader=FileSystemLoader(str(ROOT / "templates")),
        autoescape=select_autoescape(["html"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )


def meta_from_prose(item: dict, title: str) -> str:
    return cat.meta_desc(item, title)


def pictures_for(item: dict, images: list[dict], title: str, section_name: str) -> list[dict]:
    out = []
    sizes = "(max-width: 900px) 100vw, 52vw"
    for i, info in enumerate(images):
        alt = f"{title} — {section_name} by William Bowers" + ("" if i == 0 else f", view {i+1}")
        webp, avif = cat.srcset(info["stem"], ".webp", info), cat.srcset(info["stem"], ".avif", info)
        out.append({
            "html": cat.picture_html(info["stem"], info, alt, sizes, eager=(i == 0), prefer=1200 if i == 0 else 2000),
            "full": cat.largest_webp(info["stem"], info),
            "webp_srcset": webp,
            "avif_srcset": avif,
            "alt": alt,
            "thumb": cat.thumb_url(info["stem"], info),
        })
    return out


def og_image_url(images: list[dict]) -> str:
    if not images:
        return f"{cat.SITE_ORIGIN}/assets/images/brand/og-default.jpg"
    return f"{cat.SITE_ORIGIN}{cat.largest_webp(images[0]['stem'], images[0])}"


def render_product(jinja, item, images, titles, all_items, all_images):
    slug = item["permalink"]
    title = cat.display_title(slug, item["name"], titles)
    section_slug = cat.primary_section(item)
    section = cat.SECTIONS[section_slug]
    sold = item.get("status") == "sold-out"
    pics = pictures_for(item, images, title, section["crumb"])
    desc = meta_from_prose(item, title)
    related_items = [
        p for p in all_items
        if p["permalink"] != slug and cat.in_section(p, section_slug)
    ][:3]
    related = [
        cat.card_html(p, all_images.get(p["permalink"], []), titles, "(max-width: 700px) 50vw, 30vw", section_slug)
        for p in related_items
    ]
    product = {
        "title": title,
        "eyebrow": section["crumb"],
        "on_sale": bool(item.get("on_sale")) and not sold,
        "one_of_one": section_slug == "original-paintings",
        "sold_out": sold,
        "price_label": cat.price_label(item),
        "prose": cat.prose_html(item),
        "specs": cat.specs_for(item, section_slug),
        "buy_url": f"{cat.BUY}/{slug}",
        "buy_label": cat.buy_label(item, section_slug),
        "options_note": cat.options_note(item),
        "pictures": pics,
    }
    ld = {
        "@context": "https://schema.org",
        "@type": "Product",
        "name": title,
        "description": desc,
        "image": [og_image_url([im]) for im in images] or [og_image_url([])],
        "sku": f"om-{slug}",
        "brand": {"@type": "Brand", "name": "the Organic Mechanic"},
        "url": f"{cat.SITE_ORIGIN}/product/{slug}/",
        "category": section["crumb"],
        "offers": {
            "@type": "Offer",
            "url": f"{cat.BUY}/{slug}",
            "priceCurrency": "USD",
            "price": f"{float(item.get('price') or 0):.2f}",
            "availability": "https://schema.org/SoldOut" if sold else (
                "https://schema.org/LimitedAvailability" if section_slug == "original-paintings" else "https://schema.org/InStock"
            ),
            "itemCondition": "https://schema.org/NewCondition",
            "seller": {"@type": "Organization", "name": "the Organic Mechanic"},
        },
        "creator": {"@type": "Person", "name": "William Bowers"},
    }
    crumbs = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": f"{cat.SITE_ORIGIN}/"},
            {"@type": "ListItem", "position": 2, "name": "Shop", "item": f"{cat.SITE_ORIGIN}/shop/"},
            {"@type": "ListItem", "position": 3, "name": section["crumb"], "item": f"{cat.SITE_ORIGIN}{section['path']}"},
            {"@type": "ListItem", "position": 4, "name": title, "item": f"{cat.SITE_ORIGIN}/product/{slug}/"},
        ],
    }
    html = jinja.get_template("product.html").render(
        title=f"{title} | O.M.",
        description=desc,
        canonical=f"{cat.SITE_ORIGIN}/product/{slug}/",
        og_type="product",
        og_title=title,
        og_image=og_image_url(images),
        og_image_alt=f"{title} — {section['crumb']} by William Bowers",
        body_class="page-product",
        nav="shop",
        json_ld=[json.dumps(ld, separators=(",", ":")), json.dumps(crumbs, separators=(",", ":"))],
        product=product,
        section=section,
        related=related,
    )
    dest = SITE / "product" / slug / "index.html"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(html, encoding="utf-8")
    return dest


def render_shop(jinja, section_slug: str | None, items, images, titles):
    if section_slug:
        section = cat.SECTIONS[section_slug]
        filtered = [p for p in items if cat.in_section(p, section_slug)]
        path = SITE / "shop" / section_slug / "index.html"
        url = f"{cat.SITE_ORIGIN}{section['path']}"
        heading, eyebrow, blurb = section["heading"], section["eyebrow"], section["blurb"]
        title, desc = section["meta_title"], section["meta_desc"]
        grid = section["grid"]
        sizes = "(max-width: 700px) 100vw, 46vw" if grid == "grid-2" else "(max-width: 700px) 50vw, 30vw"
    else:
        filtered = list(items)
        path = SITE / "shop" / "index.html"
        url = f"{cat.SITE_ORIGIN}/shop/"
        heading, eyebrow, blurb = "All works.", "The shop", "Originals, handmade jewelry, resin objects, apparel, bags, and home — everything in the studio, in one place."
        title = "Shop Art, Jewelry & Apparel | the Organic Mechanic"
        desc = "Shop original psychedelic paintings, handmade pressed flower resin jewelry, and wearable art by William Bowers."
        grid = "grid"
        sizes = "(max-width: 700px) 50vw, 30vw"
        section = None

    n = len(filtered)
    noun = "piece" if n == 1 else "pieces"
    cards = [
        cat.card_html(p, images.get(p["permalink"], []), titles, sizes, section_slug or cat.primary_section(p))
        for p in filtered
    ]
    html = jinja.get_template("shop.html").render(
        title=title,
        description=desc,
        canonical=url,
        og_type="website",
        og_title=title,
        og_image=f"{cat.SITE_ORIGIN}/assets/images/brand/og-default.jpg",
        og_image_alt="The Organic Mechanic — gold gear and Om seal, Hand Krafted Art",
        body_class="page-shop",
        nav="shop",
        json_ld=[],
        eyebrow=eyebrow,
        heading=heading,
        blurb=blurb,
        count_label=f"{n} {noun}",
        section_slug=section_slug or "",
        grid_class=grid,
        cards=cards,
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(html, encoding="utf-8")
    return path


def write_sitemap(items):
    urls = [
        ("/", "1.0"),
        ("/shop/", "0.8"),
    ]
    for slug in cat.SECTION_ORDER:
        urls.append((cat.SECTIONS[slug]["path"], "0.8"))
    for item in items:
        urls.append((f"/product/{item['permalink']}/", "0.8"))
    static = [
        "/about/", "/commissions/", "/faq/", "/contact/",
        "/policies/", "/policies/shipping/", "/policies/returns/",
        "/custom-pet-pillow/",
    ]
    for u in static:
        urls.append((u, "0.6"))
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]
    for path, pri in urls:
        lines.append(
            f"  <url><loc>{cat.SITE_ORIGIN}{path}</loc><lastmod>{TODAY}</lastmod><priority>{pri}</priority></url>"
        )
    lines.append("</urlset>")
    dest = SITE / "sitemap.xml"
    dest.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return dest


def generate_catalog(
    force_images: bool = False,
    overwrite_pages: bool = False,
    changed_slugs: set[str] | None = None,
    site_dir: Path | None = None,
    scrape_dir: Path | None = None,
) -> dict:
    """Optimize product images, render product + shop pages, refresh the sitemap.

    Static pages (about, contact, faq, commissions, policies, custom pet pillow,
    404) and the homepage (index.html / hero) are left in place. The hero is
    applied separately by build.py after this runs.

    By default, existing product pages are kept (so editorial copy is not
    rewritten). New slugs, slugs in changed_slugs, and --rebuild-pages
    overwrite. Shop listings and the sitemap always refresh when any product
    page is written, or when overwrite_pages / changed_slugs is set, so a new
    product always appears in the shop.
    """
    if site_dir is not None:
        global SITE
        SITE = Path(site_dir)
        cat.SITE = SITE
        cat.PRODUCT_IMG_DIR = SITE / "assets" / "images" / "products"
    if scrape_dir is not None:
        cat.SCRAPE = Path(scrape_dir)
        cat.SCRAPE_IMG_DIR = cat.SCRAPE / "images" / "products"

    titles = cat.load_titles()
    items = cat.load_products()
    images: dict[str, list] = {}
    changed_slugs = set(changed_slugs or [])
    for item in items:
        slug = item["permalink"]
        dest = SITE / "product" / slug / "index.html"
        is_new_or_changed = overwrite_pages or (not dest.exists()) or (slug in changed_slugs)
        print(f"  images {slug} ...")
        images[slug] = cat.optimize_item_images(
            item, force=force_images, encode=is_new_or_changed or force_images
        )

    jinja = env()
    written = []
    skipped = []
    live_slugs = {item["permalink"] for item in items}
    for item in items:
        slug = item["permalink"]
        dest = SITE / "product" / slug / "index.html"
        should = overwrite_pages or (not dest.exists()) or (slug in changed_slugs)
        if not should:
            skipped.append(slug)
            continue
        written.append(render_product(jinja, item, images[item["permalink"]], titles, items, images))
        print(f"  product {slug}")

    refresh_listings = overwrite_pages or bool(changed_slugs) or bool(written)
    if refresh_listings:
        written.append(render_shop(jinja, None, items, images, titles))
        for slug in cat.SECTION_ORDER:
            written.append(render_shop(jinja, slug, items, images, titles))
            print(f"  shop {slug}")
        written.append(write_sitemap(items))
        print("  sitemap")
    return {
        "products": len(items),
        "written": [str(p) for p in written],
        "skipped_existing": skipped,
        "listings_refreshed": refresh_listings,
        "slugs": sorted(live_slugs),
    }
