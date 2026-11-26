"""Fetch Big Cartel products.json, download new/changed images, update scrape/."""

from __future__ import annotations

import hashlib
import json
import re
import ssl
import time
import urllib.request
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.parse import urlparse, urlunparse

SCRAPE = Path(__file__).resolve().parent.parent.parent / "scrape"
BC_JSON = "https://theorganicmechanic.bigcartel.com/products.json"
UA = "TheOrganicMechanicSiteBot/1.0 (catalog-sync)"

# Prefer a large uncropped asset when Big Cartel serves size-limited URLs.
FULL_QS = "fit=max&w=10000"


class _TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self._chunks: list[str] = []

    def handle_data(self, data: str) -> None:
        self._chunks.append(data)

    def text(self) -> str:
        return re.sub(r"\s+", " ", "".join(self._chunks)).strip()


def html_to_text(html: str) -> str:
    if not html:
        return ""
    parser = _TextExtractor()
    try:
        parser.feed(html)
        return parser.text()
    except Exception:
        return re.sub(r"<[^>]+>", " ", html)


def _ctx():
    return ssl.create_default_context()


def _get(url: str, timeout: int = 30) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json,image/*,*/*"})
    with urllib.request.urlopen(req, context=_ctx(), timeout=timeout) as resp:
        return resp.read()


def full_res_url(url: str) -> str:
    if not url:
        return url
    parts = urlparse(url)
    return urlunparse((parts.scheme, parts.netloc, parts.path, parts.params, FULL_QS, ""))


def image_key(url: str) -> str:
    path = urlparse(url).path
    return path.rsplit("/", 1)[-1] or path


def filename_for(slug: str, index: int, url: str) -> str:
    name = image_key(url)
    name = re.sub(r"[^A-Za-z0-9._-]+", "-", name)
    if not name.lower().endswith((".jpg", ".jpeg", ".png", ".webp", ".gif")):
        name += ".jpg"
    return f"{slug}__{index:02d}__{name}"


def fetch_store_products() -> list[dict]:
    """Paginate the public Big Cartel products.json feed."""
    items: list[dict] = []
    seen: set[int] = set()
    page = 1
    while page <= 20:
        url = BC_JSON if page == 1 else f"{BC_JSON}?page={page}"
        raw = _get(url)
        data = json.loads(raw.decode("utf-8"))
        batch = data if isinstance(data, list) else data.get("products") or []
        if not batch:
            break
        new = 0
        for item in batch:
            pid = item.get("id")
            if pid in seen:
                continue
            seen.add(pid)
            items.append(item)
            new += 1
        if new == 0 or len(batch) < 100:
            # Storefront JSON is typically the full catalog in one payload
            # once a short page (or a repeat) appears, stop.
            if page > 1 and new == 0:
                break
            if len(batch) < 100:
                break
        page += 1
        time.sleep(0.2)
    items.sort(key=lambda p: (p.get("position") is None, p.get("position") or 0, p.get("name") or ""))
    return items


def _options(raw: dict) -> list[dict]:
    out = []
    for opt in raw.get("options") or []:
        out.append({
            "id": opt.get("id"),
            "name": opt.get("name"),
            "price": opt.get("price"),
            "sold_out": opt.get("sold_out"),
            "is_low_inventory": opt.get("is_low_inventory"),
            "is_almost_sold_out": opt.get("is_almost_sold_out"),
        })
    return out


def prices(raw: dict) -> tuple[float | None, float | None, float | None]:
    opts = [o.get("price") for o in (raw.get("options") or []) if o.get("price") is not None]
    base = raw.get("price")
    nums = [float(x) for x in opts + ([base] if base is not None else [])]
    if not nums:
        return base, base, base
    return (float(base) if base is not None else min(nums)), min(nums), max(nums)


def enrich(raw: dict, previous: dict | None, img_dir: Path) -> dict:
    """Build a scrape-style product record from a Big Cartel API item."""
    slug = raw["permalink"]
    desc_html = raw.get("description") or ""
    price, pmin, pmax = prices(raw)
    prev_list = list((previous or {}).get("images") or [])
    prev_imgs = {image_key(i.get("source_url") or i.get("full_res_url") or ""): i for i in prev_list}
    incoming = []
    seen_keys = set()
    for img in raw.get("images") or []:
        src = img.get("url") or img.get("source_url") or ""
        key = image_key(src)
        if not key or key in seen_keys:
            continue
        seen_keys.add(key)
        incoming.append((key, src, img))
    prev_keys = [image_key(i.get("source_url") or i.get("full_res_url") or "") for i in prev_list]
    keep_prev = bool(prev_keys) and set(seen_keys) <= set(prev_keys) and len(seen_keys) < len([k for k in prev_keys if k])
    images = []
    if keep_prev:
        for idx, rec in enumerate(prev_list, start=1):
            kept = dict(rec)
            kept["index"] = idx
            images.append(kept)
    else:
        for idx, (key, src, img) in enumerate(incoming, start=1):
            prev = prev_imgs.get(key)
            full = full_res_url(src)
            filename = (prev or {}).get("filename") or filename_for(slug, idx, src)
            local = Path((prev or {}).get("local_path") or (img_dir / filename))
            # Prefer the canonical scrape path when we already have the file.
            canon = img_dir / filename
            if canon.exists() or not local.exists():
                local = canon
            record = {
                "index": idx,
                "source_url": src,
                "full_res_url": full,
                "local_path": str(local),
                "filename": filename,
                "reported_width": img.get("width") or (prev or {}).get("reported_width"),
                "reported_height": img.get("height") or (prev or {}).get("reported_height"),
                "actual_width": (prev or {}).get("actual_width"),
                "actual_height": (prev or {}).get("actual_height"),
                "bytes": (prev or {}).get("bytes"),
                "format": (prev or {}).get("format"),
                "download_ok": bool(local.exists() or (prev and Path((prev or {}).get("local_path") or local).exists())),
            }
            images.append(record)
    urls = {
        "store": raw.get("url") or f"https://theorganicmechanic.bigcartel.com/product/{slug}",
        "buy": f"https://theorganicmechanic.bigcartel.com/product/{slug}",
        "site": f"https://theorganicmechanic.shop/product/{slug}/",
    }
    return {
        "id": raw.get("id"),
        "name": raw.get("name"),
        "permalink": slug,
        "position": raw.get("position"),
        "status": raw.get("status"),
        "created_at": raw.get("created_at"),
        "currency": raw.get("currency") or "USD",
        "has_option_groups": bool(raw.get("has_option_groups")),
        "on_sale": bool(raw.get("on_sale")),
        "tax": raw.get("tax"),
        "price": price,
        "default_price": raw.get("default_price") or price,
        "price_min": pmin,
        "price_max": pmax,
        "description_html": desc_html,
        "description_text": html_to_text(desc_html),
        "artists": raw.get("artists") or [],
        "categories": raw.get("categories") or [],
        "option_groups": raw.get("option_groups") or [],
        "options": _options(raw),
        "image_count": len(images),
        "images": images,
        "urls": (previous or {}).get("urls") or urls,
    }


def download_image(record: dict, force: bool = False) -> bool:
    dest = Path(record["local_path"])
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_size > 0 and not force:
        record["download_ok"] = True
        if not record.get("bytes"):
            record["bytes"] = dest.stat().st_size
        return False
    url = record.get("full_res_url") or record.get("source_url")
    data = _get(url, timeout=60)
    tmp = dest.with_suffix(dest.suffix + ".tmp")
    tmp.write_bytes(data)
    tmp.replace(dest)
    record["bytes"] = len(data)
    record["download_ok"] = True
    try:
        from PIL import Image
        Image.MAX_IMAGE_PIXELS = None
        with Image.open(dest) as im:
            record["actual_width"], record["actual_height"] = im.size
            record["format"] = im.format
    except Exception:
        pass
    return True


def fingerprint(item: dict) -> str:
    payload = {
        "id": item.get("id"),
        "name": item.get("name"),
        "status": item.get("status"),
        "price": item.get("price"),
        "price_min": item.get("price_min"),
        "price_max": item.get("price_max"),
        "on_sale": item.get("on_sale"),
        "has_option_groups": item.get("has_option_groups"),
        "description_html": item.get("description_html") or item.get("description"),
        "categories": [(c.get("permalink") or c.get("name")) for c in item.get("categories") or []],
        "options": [(o.get("name"), o.get("price"), o.get("sold_out")) for o in item.get("options") or []],
        "images": [image_key(i.get("source_url") or i.get("url") or i.get("full_res_url") or "") for i in item.get("images") or []],
    }
    blob = json.dumps(payload, sort_keys=True, ensure_ascii=False).encode()
    return hashlib.sha256(blob).hexdigest()[:16]


def load_scrape(path: Path | None = None) -> dict:
    path = path or (SCRAPE / "products.json")
    if not path.exists():
        return {"products": []}
    data = json.loads(path.read_text())
    if isinstance(data, list):
        return {"products": data}
    return data


def sync(scrape_dir: Path | None = None, force_images: bool = False) -> dict:
    """Compare live Big Cartel products with scrape/, download new images, write JSON.

    Returns a change report: added/updated/removed permalinks, whether anything
    changed, and counts.
    """
    scrape_dir = scrape_dir or SCRAPE
    img_dir = scrape_dir / "images" / "products"
    img_dir.mkdir(parents=True, exist_ok=True)
    current = load_scrape(scrape_dir / "products.json")
    prev_items = {p["permalink"]: p for p in current.get("products") or []}
    raw_items = fetch_store_products()

    enriched = []
    added, updated, unchanged = [], [], []
    downloaded = 0
    for raw in raw_items:
        slug = raw["permalink"]
        prev = prev_items.get(slug)
        item = enrich(raw, prev, img_dir)
        for rec in item["images"]:
            # Redownload if the source asset changed or the file is missing.
            need = force_images or not Path(rec["local_path"]).exists() or (
                prev and image_key(rec.get("source_url") or "") not in {
                    image_key(i.get("source_url") or "") for i in prev.get("images") or []
                }
            )
            if need or not rec.get("download_ok"):
                try:
                    if download_image(rec, force=force_images or need):
                        downloaded += 1
                except Exception as exc:
                    rec["download_ok"] = False
                    rec["download_error"] = str(exc)
                    print(f"  ! image failed {slug} {rec.get('filename')}: {exc}")
        enriched.append(item)
        if prev is None:
            added.append(slug)
        elif fingerprint(prev) != fingerprint(item):
            updated.append(slug)
        else:
            unchanged.append(slug)

    removed = [slug for slug in prev_items if slug not in {p["permalink"] for p in enriched}]
    changed = bool(added or updated or removed or downloaded)
    if changed:
        (scrape_dir / "products-raw.json").write_text(
            json.dumps(raw_items, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        products_path = scrape_dir / "products.json"
        out = dict(current)
        out["scraped_at"] = datetime.now(timezone.utc).isoformat()
        out["products"] = enriched
        counts = out.get("counts") or {}
        counts.update({
            "products": len(enriched),
            "active": sum(1 for p in enriched if p.get("status") == "active"),
            "sold_out": sum(1 for p in enriched if p.get("status") == "sold-out"),
            "on_sale": sum(1 for p in enriched if p.get("on_sale")),
        })
        out["counts"] = counts
        products_path.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    report = {
        "changed": changed,
        "added": added,
        "updated": updated,
        "removed": removed,
        "unchanged": len(unchanged),
        "downloaded_images": downloaded,
        "total": len(enriched),
    }
    print(
        f"Big Cartel sync: {len(enriched)} products "
        f"(+{len(added)} ~{len(updated)} -{len(removed)}, {downloaded} new images)"
    )
    if added:
        print("  added:", ", ".join(added))
    if updated:
        print("  updated:", ", ".join(updated))
    if removed:
        print("  removed:", ", ".join(removed))
    return report


if __name__ == "__main__":
    sync()
