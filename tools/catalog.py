"""Catalog helpers: sections, titles, product cards, image variants, and copy."""

from __future__ import annotations

import html
import json
import re
from html.parser import HTMLParser
from pathlib import Path

from PIL import Image

Image.MAX_IMAGE_PIXELS = None

ROOT = Path(__file__).resolve().parent
SITE = ROOT.parent
SCRAPE = SITE.parent / "scrape"
PRODUCT_IMG_DIR = SITE / "assets" / "images" / "products"
SCRAPE_IMG_DIR = SCRAPE / "images" / "products"
TITLES_PATH = ROOT / "display_titles.json"
RETIRED_PATH = ROOT / "retired_slugs.json"
SITE_ORIGIN = "https://theorganicmechanic.shop"
BUY = "https://theorganicmechanic.bigcartel.com/product"

# AVIF/WebP steps; JPEG is written at JPEG_PREFER (or native if smaller).
IMG_WIDTHS = (400, 800, 1600, 2000)
JPEG_PREFER = 1200

# Big Cartel category permalink -> site section. Bags win over apparel when both.
CATEGORY_SECTION = {
    "original-paintings": "original-paintings",
    "pressed-flower-jewelry": "jewelry",
    "pendants-jewelry": "jewelry",
    "resin-art": "resin-art",
    "keepsake-stash-boxes": "resin-art",
    "art-backpacks-bags": "bags",
    "om-apparel-art-clothing": "apparel",
    "art-home-decor": "home",
}

# Products whose Big Cartel category does not match the shop section.
SECTION_OVERRIDE = {
    "flag": "home",
    "i-bees-in-the-trap-tough-case-for-iphone": "home",
    "custom-shaped-pillow": "home",
    "the-pondering-astronaut-framed-poster": "wall-art",
    "the-lion-and-the-hare-framed-poster": "wall-art",
    "sailings-the-side-of-the-erph-framed-poster": "wall-art",
    "og-octopus-s2x-box-framed-poster": "wall-art",
    "nor-graffiti-framed-poster": "wall-art",
    "paul-wall-russ-framed-poster": "wall-art",
    "prime-sloth-framed-poster": "wall-art",
    "jags-framed-poster": "wall-art",
    "the-pondering-astronaut-indoor-wall-tapestry": "wall-art",
}

SECTION_ORDER = [
    "original-paintings",
    "wall-art",
    "jewelry",
    "resin-art",
    "apparel",
    "bags",
    "home",
]

SECTIONS = {
    "original-paintings": {
        "path": "/shop/original-paintings/",
        "crumb": "Original paintings",
        "heading": "Original paintings & sculpture.",
        "eyebrow": "One of one",
        "blurb": "One-of-a-kind acrylic, mixed-media, and pyrography works by William Bowers. When a piece is sold, it leaves the studio for good.",
        "meta_title": "Original Psychedelic Paintings by William Bowers",
        "meta_desc": "One-of-a-kind acrylic and mixed-media works — mandalas, visionary figures, and cosmic animal paintings. Signed originals, insured U.S. shipping.",
        "grid": "grid-2",
    },
    "wall-art": {
        "path": "/shop/wall-art/",
        "crumb": "Wall art & prints",
        "heading": "Wall art & prints.",
        "eyebrow": "Prints",
        "blurb": "Framed posters and tapestries of original paintings by William Bowers, printed to order.",
        "meta_title": "Wall Art & Prints | Framed Posters and Tapestries",
        "meta_desc": "Framed posters and indoor wall tapestries of original paintings by William Bowers. Printed to order and shipped from the U.S.",
        "grid": "grid",
    },
    "jewelry": {
        "path": "/shop/jewelry/",
        "crumb": "Pressed flower jewelry",
        "heading": "Pressed flower resin jewelry.",
        "eyebrow": "Handmade, limited",
        "blurb": "Real wildflowers, wings, and botanicals set in resin. Small-batch pendants and earrings, often one of a kind.",
        "meta_title": "Pressed Flower Resin Jewelry | Handmade Pendants & Earrings",
        "meta_desc": "Real pressed wildflowers, cicada wings, and botanicals set in resin. Handmade, small-batch pendants and earrings from the Organic Mechanic.",
        "grid": "grid",
    },
    "resin-art": {
        "path": "/shop/resin-art/",
        "crumb": "Resin art & boxes",
        "heading": "Resin art, trays & keepsake boxes.",
        "eyebrow": "Functional art",
        "blurb": "Hand-painted trays and carved, resin-finished keepsake boxes — objects meant to be used and kept.",
        "meta_title": "Resin Art, Trays & Keepsake Boxes | the Organic Mechanic",
        "meta_desc": "Hand-painted resin trays and one-of-a-kind keepsake and stash boxes by William Bowers. Handmade functional art from the Organic Mechanic.",
        "grid": "grid",
    },
    "apparel": {
        "path": "/shop/apparel/",
        "crumb": "Apparel",
        "heading": "O.M. apparel — art you can wear.",
        "eyebrow": "Wearable art",
        "blurb": "Festival-ready hoodies, bombers, tees, shoes, and more, printed to order with original art by William Bowers.",
        "meta_title": "O.M. Apparel — Psychedelic All-Over Print Clothing",
        "meta_desc": "Festival-ready hoodies, bombers, tees, and shoes printed with original art by William Bowers. Printed to order in the U.S.",
        "grid": "grid",
    },
    "bags": {
        "path": "/shop/bags/",
        "crumb": "Bags",
        "heading": "Art backpacks, slings & duffles.",
        "eyebrow": "Carry the work",
        "blurb": "Everyday bags printed with original paintings — backpacks, slings, and a duffle for life on the go.",
        "meta_title": "Art Backpacks & Bags | the Organic Mechanic",
        "meta_desc": "Backpacks, sling bags, and a duffle printed with original psychedelic art by William Bowers. Everyday carry, printed to order.",
        "grid": "grid",
    },
    "home": {
        "path": "/shop/home/",
        "crumb": "Home",
        "heading": "Art for the house.",
        "eyebrow": "Live with the work",
        "blurb": "Pillows, a wall flag, and a phone case — plus custom-shaped pet pillows from your photograph.",
        "meta_title": "Art Home Decor | the Organic Mechanic",
        "meta_desc": "Art pillows, a wall flag, and a phone case printed with original work by William Bowers, plus custom pet pillows.",
        "grid": "grid",
    },
}


def load_titles() -> dict[str, str]:
    if TITLES_PATH.exists():
        return json.loads(TITLES_PATH.read_text(encoding="utf-8"))
    return {}


def load_retired_slugs() -> set[str]:
    """Slugs hidden from shop listings, counts, and the sitemap."""
    if not RETIRED_PATH.exists():
        return set()
    data = json.loads(RETIRED_PATH.read_text(encoding="utf-8"))
    if isinstance(data, dict):
        return set(data.get("slugs") or [])
    if isinstance(data, list):
        return set(data)
    return set()


def load_products() -> list[dict]:
    data = json.loads((SCRAPE / "products.json").read_text(encoding="utf-8"))
    return list(data.get("products") or [])


def load_shop_products() -> list[dict]:
    retired = load_retired_slugs()
    return [p for p in load_products() if p.get("permalink") not in retired]


def display_title(slug: str, name: str, titles: dict | None = None) -> str:
    titles = titles if titles is not None else load_titles()
    return titles.get(slug, (name or "").strip())


def _cat_permalinks(item: dict) -> list[str]:
    return [c.get("permalink") or "" for c in (item.get("categories") or [])]


def primary_section(item: dict) -> str:
    slug = item.get("permalink") or ""
    if slug in SECTION_OVERRIDE:
        return SECTION_OVERRIDE[slug]
    cats = _cat_permalinks(item)
    # Prefer bags over apparel when a product is in both.
    ranked = [
        "original-paintings",
        "pressed-flower-jewelry",
        "pendants-jewelry",
        "resin-art",
        "keepsake-stash-boxes",
        "art-backpacks-bags",
        "om-apparel-art-clothing",
        "art-home-decor",
    ]
    for key in ranked:
        if key in cats:
            return CATEGORY_SECTION[key]
    return "home"


def in_section(item: dict, section_slug: str) -> bool:
    return primary_section(item) == section_slug


def fmt_price(value: float | int | None) -> str:
    if value is None:
        return ""
    n = float(value)
    if n == int(n):
        return f"${int(n)}"
    return f"${n:.2f}"


def price_label(item: dict) -> str:
    if item.get("status") == "sold-out":
        return "Sold"
    lo = item.get("price_min")
    hi = item.get("price_max")
    if lo is None:
        lo = item.get("price") or 0
    if hi is None:
        hi = lo
    if float(lo) != float(hi):
        return f"{fmt_price(lo)} – {fmt_price(hi)}"
    return fmt_price(lo)


def buy_label(item: dict, section_slug: str) -> str:
    if item.get("status") == "sold-out":
        return "Sold"
    options = item.get("options") or []
    groups = item.get("option_groups") or []
    if section_slug == "original-paintings":
        return "Buy this original"
    if len(options) > 1 or groups or (section_slug in {"apparel", "bags", "home"} and len(options) > 1):
        return "Select options & buy"
    if section_slug in {"apparel", "bags"} and any(
        re.search(r"\b(xs|s|m|l|xl|size)\b", (o.get("name") or ""), re.I) for o in options
    ):
        return "Select options & buy"
    if len(options) > 1:
        return "Select options & buy"
    # Printed merch with a single default option still uses "Select options" when sizes exist in the name set
    if section_slug in {"apparel", "bags", "home"} and _looks_sized(item):
        return "Select options & buy"
    if section_slug in {"jewelry", "resin-art"}:
        return "Buy this piece"
    if section_slug == "home" and not _looks_sized(item):
        return "Buy this piece"
    return "Buy this piece"


def _looks_sized(item: dict) -> bool:
    names = " ".join(o.get("name") or "" for o in (item.get("options") or []))
    if item.get("option_groups"):
        return True
    return bool(re.search(r"\b(xs|xxl|3xl|size)\b", names, re.I) or "×" in names or "x" in names.lower())


def options_note(item: dict) -> str:
    groups = item.get("option_groups") or []
    options = item.get("options") or []
    if groups:
        parts = []
        for g in groups:
            name = (g.get("name") or "Options").strip()
            vals = g.get("values") or g.get("options") or []
            if vals and isinstance(vals[0], dict):
                labels = [str(v.get("name") or v.get("value") or "") for v in vals]
            else:
                labels = [str(v) for v in vals]
            labels = [x for x in labels if x]
            if labels:
                parts.append(f"{name}: " + ", ".join(labels) if name.lower() != "size" and name.lower() != "sizes"
                             else _size_phrase(name, labels))
        if parts:
            return " ".join(parts)
    if len(options) > 1:
        names = [str(o.get("name") or "").strip() for o in options]
        names = [n for n in names if n]
        if _are_sizes(names):
            return _size_range_phrase(names)
        return ", ".join(names)
    return ""


def _are_sizes(names: list[str]) -> bool:
    blob = " ".join(names).lower()
    return bool(re.search(r"\b(xs|s|m|l|xl|xxl|3xl)\b", blob)) or any("×" in n or "x" in n.lower() for n in names)


def _size_phrase(name: str, labels: list[str]) -> str:
    if name.lower() in {"size", "sizes"}:
        return "Size: " + ", ".join(labels) if any("×" in x or "″" in x or '"' in x for x in labels) else _size_range_phrase(labels)
    return f"{name}: " + ", ".join(labels)


def _size_range_phrase(names: list[str]) -> str:
    # "Sizes XS–3XL"
    order = ["XS", "S", "M", "L", "XL", "2XL", "XXL", "3XL", "4XL"]
    upper = [n.strip().upper().replace("XXL", "2XL") for n in names]
    present = [s for s in order if s in upper or s.replace("2XL", "XXL") in [n.strip().upper() for n in names]]
    if len(present) >= 2:
        a, b = present[0], present[-1]
        a = "XS" if a == "XS" else a
        b = "3XL" if b in {"3XL"} else ("2XL" if b == "2XL" else b)
        # Prefer the common merch phrasing
        last = names[-1].strip()
        first = names[0].strip()
        # keep original last token if it's 3XL
        return f"Sizes {first}–{last}"
    return "Sizes " + ", ".join(names)


class _TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self._chunks: list[str] = []

    def handle_data(self, data: str) -> None:
        self._chunks.append(data)

    def text(self) -> str:
        return re.sub(r"\s+", " ", "".join(self._chunks)).strip()


def _html_to_text(raw: str) -> str:
    if not raw:
        return ""
    p = _TextExtractor()
    try:
        p.feed(raw)
        return p.text()
    except Exception:
        return re.sub(r"<[^>]+>", " ", raw)


def prose_html(item: dict) -> str:
    raw_html = (item.get("description_html") or "").strip()
    if raw_html and ("<p" in raw_html.lower() or "<br" in raw_html.lower()):
        # Keep paragraph structure; strip wrapping body if present.
        parts = re.split(r"</p>\s*", raw_html, flags=re.I)
        out = []
        for part in parts:
            part = re.sub(r"^<p[^>]*>", "", part, flags=re.I).strip()
            if not part:
                continue
            # If this chunk has no tags, escape
            if "<" not in part:
                out.append(f"          <p>{html.escape(part)}</p>")
            else:
                # allow simple breaks inside
                out.append(f"          <p>{part}</p>")
        if out:
            return "\n        \n".join(out) + "\n        \n        "
    text = (item.get("description_text") or _html_to_text(raw_html) or "").strip()
    if not text:
        return ""
    # Split on blank lines; keep single newlines inside a paragraph.
    chunks = re.split(r"\n\s*\n", text)
    if len(chunks) == 1 and "\n" in text and "•" in text:
        # Intro paragraph + bullet block
        idx = text.find("•")
        if idx > 0:
            intro = text[:idx].strip()
            rest = text[idx:].strip()
            chunks = [intro, rest] if intro else [rest]
    out = []
    for chunk in chunks:
        chunk = chunk.strip()
        if chunk:
            out.append(f"          <p>{html.escape(chunk)}</p>")
    return "\n        \n".join(out) + "\n        \n        "


def meta_desc(item: dict, title: str) -> str:
    text = (item.get("description_text") or _html_to_text(item.get("description_html") or "") or "").strip()
    text = re.sub(r"\s+", " ", text)
    if not text:
        return f"{title} by William Bowers, from the Organic Mechanic."
    if len(text) <= 160:
        return text
    cut = text[:157].rsplit(" ", 1)[0]
    return cut + "…"


def specs_for(item: dict, section_slug: str) -> list[dict]:
    specs: list[dict] = []
    if section_slug == "original-paintings":
        specs.append({"k": "Type", "v": "One-of-a-kind original"})
    elif section_slug in {"jewelry", "resin-art"}:
        specs.append({"k": "Type", "v": "Handmade, limited"})
    else:
        specs.append({"k": "Type", "v": "Printed to order"})
    specs.append({"k": "Artist", "v": "William Bowers"})
    if section_slug == "jewelry":
        specs.append({"k": "Materials", "v": "Pressed botanicals in UV / polymer resin"})
    # Medium / size are editorial and live on existing pages; new pages get section defaults only.
    if section_slug == "original-paintings":
        specs.append({"k": "Shipping", "v": "$30 (packed with extra care and insured)"})
        specs.append({"k": "Production", "v": "In-stock items ship in 2–4 business days (delivery about 3–5 days)."})
        if item.get("on_sale") or item.get("status") == "sold-out":
            specs.append({"k": "Returns", "v": "Sale items are final sale." if item.get("on_sale") and item.get("status") != "sold-out" else "Final sale (originals, stash boxes, and custom work)."})
        else:
            specs.append({"k": "Returns", "v": "Final sale (originals, stash boxes, and custom work)."})
    elif section_slug == "jewelry":
        specs.append({"k": "Shipping", "v": "$6.95 within the U.S., plus $3 each additional item"})
        specs.append({"k": "Production", "v": "In-stock items ship in 2–4 business days (delivery about 3–5 days)."})
        specs.append({"k": "Returns", "v": "30-day return in original condition; customer pays return shipping."})
    elif section_slug == "resin-art":
        specs.append({"k": "Shipping", "v": "$9.95 within the U.S., plus $3 each additional item"})
        specs.append({"k": "Production", "v": "In-stock items ship in 2–4 business days (delivery about 3–5 days)."})
        specs.append({"k": "Returns", "v": "Final sale (originals, stash boxes, and custom work)."})
    else:
        specs.append({"k": "Shipping", "v": "$9.95 within the U.S., plus $3 each additional item"})
        specs.append({"k": "Production", "v": "Printed to order; allow 5–10 business days to produce before shipping."})
        specs.append({"k": "Returns", "v": "Unworn clothing and most home goods: 30-day return in original condition; customer pays return shipping. Sale items and custom work are final sale."})
    return specs


def _open_rgb(path: Path) -> Image.Image:
    im = Image.open(path)
    if im.mode not in ("RGB", "L"):
        im = im.convert("RGB")
    elif im.mode == "L":
        im = im.convert("RGB")
    return im


def _fit_width(im: Image.Image, width: int) -> Image.Image:
    if im.width <= width:
        return im.copy()
    height = max(1, int(round(im.height * (width / im.width))))
    return im.resize((width, height), Image.Resampling.LANCZOS)


def optimize_item_images(item: dict, force: bool = False, encode: bool = True) -> list[dict]:
    PRODUCT_IMG_DIR.mkdir(parents=True, exist_ok=True)
    out: list[dict] = []
    slug = item["permalink"]
    for rec in item.get("images") or []:
        index = rec.get("index") or rec.get("position") or (len(out) + 1)
        src = Path(rec.get("local_path") or rec.get("path") or "")
        if not src.exists():
            name = rec.get("filename") or src.name
            alt = SCRAPE_IMG_DIR / name
            src = alt if alt.exists() else src
        if not src.exists():
            # last resort: already-exported stems
            stem = f"{slug}__{int(index):02d}"
            existing = list(PRODUCT_IMG_DIR.glob(f"{stem}--*"))
            if existing:
                info = _info_from_existing(stem, existing)
                if info:
                    out.append(info)
                    continue
            print(f"  missing source image for {slug} #{index}: {src}")
            continue
        stem = f"{slug}__{int(index):02d}"
        info = _encode_one(src, stem, force=force, encode=encode)
        out.append(info)
    return out


def _info_from_existing(stem: str, files: list[Path]) -> dict | None:
    variants: dict[int, dict] = {}
    native = None
    for p in files:
        m = re.search(r"--(\d+)\.(jpg|jpeg|webp|avif)$", p.name, re.I)
        if not m:
            continue
        w = int(m.group(1))
        ext = "." + m.group(2).lower().replace("jpeg", "jpg")
        variants.setdefault(w, {})[ext] = p.name
        if ext == ".jpg":
            try:
                with Image.open(p) as im:
                    # infer native from? we don't have it; leave and fix below
                    pass
            except Exception:
                pass
    if not variants:
        return None
    # Prefer a jpg or the largest webp to guess aspect; native width unknown.
    # Read the largest file's pixel size and scale to the max width key if needed.
    largest_w = max(variants)
    # try to get actual native from a scan of scrape? skip — use largest encoded
    pick = None
    for ext in (".jpg", ".webp", ".avif"):
        if ext in variants[largest_w]:
            pick = PRODUCT_IMG_DIR / variants[largest_w][ext]
            break
    native_w, native_h = largest_w, largest_w
    if pick and pick.exists():
        with Image.open(pick) as im:
            native_w, native_h = im.size
            if native_w != largest_w and native_w:
                native_h = int(round(im.height * (largest_w / im.width))) if False else im.height
                # If this variant was resized, native is at least largest_w if we didn't upscale
                # We cannot know true native; store the largest variant size.
                native_w, native_h = im.size
                # If width==largest_w this IS the variant size, not necessarily native.
    return {"stem": stem, "native": [native_w, native_h], "variants": {str(k): v for k, v in variants.items()}}


def _encode_one(src: Path, stem: str, force: bool = False, encode: bool = True) -> dict:
    with _open_rgb(src) as original:
        native_w, native_h = original.size
        variants: dict[int, dict] = {}
        # Decide target widths (never upscale)
        targets = []
        for w in IMG_WIDTHS:
            tw = min(w, native_w)
            if tw not in targets:
                targets.append(tw)
        if native_w not in targets and native_w < max(IMG_WIDTHS):
            targets.append(native_w)
        jpeg_w = min(JPEG_PREFER, native_w)
        if jpeg_w not in targets:
            targets.append(jpeg_w)
        targets = sorted(set(targets))

        if not encode and not force:
            # Read whatever is already on disk
            existing = list(PRODUCT_IMG_DIR.glob(f"{stem}--*"))
            info = _info_from_existing(stem, existing) if existing else None
            if info:
                info["native"] = [native_w, native_h]
                return info

        for tw in targets:
            resized = _fit_width(original, tw)
            is_jpeg_target = tw == jpeg_w
            fmts = []
            if tw in IMG_WIDTHS or tw == native_w:
                fmts.extend([
                    (".webp", dict(format="WEBP", quality=86, method=6)),
                    (".avif", dict(format="AVIF", quality=62)),
                ])
            if is_jpeg_target:
                fmts.append((".jpg", dict(format="JPEG", quality=90, optimize=True, progressive=True, subsampling=0)))
            for ext, kw in fmts:
                dest = PRODUCT_IMG_DIR / f"{stem}--{tw}{ext}"
                if dest.exists() and not force and dest.stat().st_mtime >= src.stat().st_mtime and dest.stat().st_size > 0:
                    variants.setdefault(tw, {})[ext] = dest.name
                    continue
                if not encode and dest.exists():
                    variants.setdefault(tw, {})[ext] = dest.name
                    continue
                tmp = dest.with_suffix(dest.suffix + ".tmp")
                try:
                    resized.save(tmp, **kw)
                    tmp.replace(dest)
                    variants.setdefault(tw, {})[ext] = dest.name
                except Exception as exc:
                    if tmp.exists():
                        tmp.unlink()
                    if ext == ".avif":
                        print(f"  avif skipped for {stem}@{tw}: {exc}")
                    else:
                        raise
            resized.close()
        return {
            "stem": stem,
            "source": str(src),
            "native": [native_w, native_h],
            "variants": {str(k): v for k, v in variants.items()},
        }


def srcset(stem: str, ext: str, info: dict) -> str:
    parts = []
    for w, files in sorted((info.get("variants") or {}).items(), key=lambda kv: int(kv[0])):
        name = files.get(ext)
        if name:
            parts.append(f"/assets/images/products/{name} {w}w")
    return ", ".join(parts)


def largest_webp(stem: str, info: dict) -> str:
    variants = info.get("variants") or {}
    if not variants:
        return ""
    # prefer largest webp, else jpg
    for w, files in sorted(variants.items(), key=lambda kv: int(kv[0]), reverse=True):
        name = files.get(".webp") or files.get(".jpg") or files.get(".avif")
        if name:
            return f"/assets/images/products/{name}"
    return ""


def thumb_url(stem: str, info: dict) -> str:
    variants = info.get("variants") or {}
    # prefer 400 webp
    for want in (400, 800):
        files = variants.get(str(want)) or {}
        name = files.get(".webp") or files.get(".jpg") or files.get(".avif")
        if name:
            return f"/assets/images/products/{name}"
    return largest_webp(stem, info)


def picture_html(stem: str, info: dict, alt: str, sizes: str, eager: bool = False, prefer: int = 1200) -> str:
    native_w, native_h = (info.get("native") or [0, 0])[:2]
    variants = info.get("variants") or {}
    # JPEG fallback at prefer, else closest
    jpg_w = None
    if str(prefer) in variants and ".jpg" in variants[str(prefer)]:
        jpg_w = prefer
    else:
        jpeg_widths = [int(w) for w, f in variants.items() if ".jpg" in f]
        if jpeg_widths:
            jpg_w = min(jpeg_widths, key=lambda w: abs(w - prefer))
        else:
            jpg_w = max((int(w) for w in variants), default=prefer)
    files = variants.get(str(jpg_w), {})
    name = files.get(".jpg") or files.get(".webp") or files.get(".avif")
    src = f"/assets/images/products/{name}" if name else ""
    avif = srcset(stem, ".avif", info)
    webp = srcset(stem, ".webp", info)
    loading = "" if eager else ' loading="lazy"'
    fetch = ' fetchpriority="high"' if eager else ""
    # width/height are native pixels when known
    w, h = native_w or jpg_w, native_h or jpg_w
    img = (
        f'<img src="{src}" alt="{html.escape(alt)}" width="{w}" height="{h}"'
        f'{fetch}{loading} decoding="async" >'
    )
    sources = []
    if avif:
        sources.append(f'  <source type="image/avif" srcset="{avif}" sizes="{sizes}">')
    if webp:
        sources.append(f'  <source type="image/webp" srcset="{webp}" sizes="{sizes}">')
    return "<picture>\n" + "\n".join(sources) + "\n  " + img + "\n</picture>"



SHARE_ICON = (
    '<svg class="share-icon" viewBox="0 0 24 24" aria-hidden="true" focusable="false">'
    '<path d="M12 3.5 7.8 7.7a1 1 0 0 0 1.4 1.4L11 7.3V15a1 1 0 1 0 2 0V7.3l1.8 1.8a1 1 0 1 0 1.4-1.4L12 3.5z"/>'
    '<path d="M6 13.5a1 1 0 0 0-1 1V18a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2v-3.5a1 1 0 1 0-2 0V18H7v-3.5a1 1 0 0 0-1-1z"/>'
    "</svg>"
)


def share_image_url(images: list[dict]) -> str:
    if not images:
        return ""
    rel = largest_webp(images[0]["stem"], images[0]) or thumb_url(images[0]["stem"], images[0])
    if not rel:
        return ""
    return rel if rel.startswith("http") else f"{SITE_ORIGIN}{rel}"


def share_page_url(slug: str) -> str:
    return f"{SITE_ORIGIN}/product/{slug}/"


def share_button_html(title: str, url: str, image: str = "", *, variant: str = "card") -> str:
    """Accessible Share control. variant is 'card' (icon) or 'pdp' (labeled, next to buy)."""
    label = f"Share {title}"
    img_attr = f' data-share-image="{html.escape(image, quote=True)}"' if image else ""
    if variant == "pdp":
        classes = "btn btn-ghost share-btn share-btn--pdp"
        visible = '<span class="share-label">Share</span>'
    else:
        classes = "share-btn share-btn--card"
        visible = ""
    return (
        f'<button type="button" class="{classes}" data-share '
        f'data-share-url="{html.escape(url, quote=True)}" '
        f'data-share-title="{html.escape(title, quote=True)}"{img_attr} '
        f'aria-label="{html.escape(label, quote=True)}" aria-haspopup="menu" aria-expanded="false">'
        f"{SHARE_ICON}{visible}</button>"
    )


def card_html(item: dict, images: list[dict], titles: dict, sizes: str, section_slug: str) -> str:
    slug = item["permalink"]
    title = display_title(slug, item.get("name") or "", titles)
    section = SECTIONS[section_slug]
    sold = item.get("status") == "sold-out"
    on_sale = bool(item.get("on_sale")) and not sold
    one = section_slug == "original-paintings"
    badges = ["", ""]
    badge_bits = ["", ""]
    # Match the somewhat loose whitespace of the original renderer.
    sale = '    <span class="badge badge-sale">On sale</span>\n' if on_sale else ""
    one_b = '    <span class="badge badge-one">One of one</span>\n' if one else ""
    sold_b = '    <span class="badge badge-sold">Sold</span>\n' if sold else ""
    pic = ""
    if images:
        alt = f"{title} — {section['crumb']} by William Bowers"
        pic = picture_html(images[0]["stem"], images[0], alt, sizes, eager=False, prefer=1200)
    share = share_button_html(title, share_page_url(slug), share_image_url(images), variant="card")
    return (
        f'<article class="card">\n'
        f'<a class="card-link" href="/product/{slug}/">\n'
        f'  <div class="card-media">\n'
        f'    <div class="badges">\n'
        f'  \n'
        f'{sold_b}'
        f'  \n'
        f'{sale}'
        f'  \n'
        f'{one_b}'
        f'  \n'
        f'</div>\n'
        f'    \n\n'
        f'{pic}\n\n\n'
        f'  </div>\n'
        f'  <div class="card-body">\n'
        f'    <div class="card-meta">{html.escape(section["crumb"])}</div>\n'
        f'    <h3 class="card-title">{html.escape(title)}</h3>\n'
        f'    <div class="card-price">{price_label(item)}</div>\n'
        f'  </div>\n'
        f'</a>\n'
        f'{share}\n'
        f'</article>'
    )
