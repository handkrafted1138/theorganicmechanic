#!/usr/bin/env python3
"""Build The Organic Mechanic static site.

This package lives inside the GitHub Pages repo (the parent of this folder). It is the source
of truth for both the product catalog (pages + shop listings) and the
homepage hero slideshow (original paintings + canvas-to-wearable pairings).

Default run (what the daily Big Cartel sync should call):
  1. Fetch Big Cartel products.json and update scrape/ (new images too)
  2. Optimize new/changed product images
  3. Write product pages for new or changed items, refresh shop listings
  4. Re-apply the homepage hero last so a catalog rebuild cannot wipe it

Usage:
  /workspace/organic-mechanic/venv-site/bin/python /workspace/organic-mechanic/site/tools/build.py
  /workspace/organic-mechanic/venv-site/bin/python /workspace/organic-mechanic/site/tools/build.py --hero-only
  /workspace/organic-mechanic/venv-site/bin/python /workspace/organic-mechanic/site/tools/build.py --no-fetch
  /workspace/organic-mechanic/venv-site/bin/python /workspace/organic-mechanic/site/tools/build.py --rebuild-pages
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
from html import escape
from pathlib import Path

from PIL import Image

Image.MAX_IMAGE_PIXELS = None

ROOT = Path(__file__).resolve().parent
SITE = ROOT.parent
TEMPLATES = ROOT / "templates"
HERO_DIR = SITE / "assets" / "images" / "hero"
CSS_OUT = SITE / "assets" / "css" / "hero.css"
JS_OUT = SITE / "assets" / "js" / "hero.js"
MANIFEST = ROOT / "hero_manifest.json"

# Ensure we can import sibling config when run as a script.
sys.path.insert(0, str(ROOT))
import hero_config as cfg  # noqa: E402


def _open_source(path: str | Path) -> Image.Image:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(path)
    im = Image.open(path)
    if im.mode not in ("RGB", "L"):
        im = im.convert("RGB")
    elif im.mode == "L":
        im = im.convert("RGB")
    return im


def _fit_width(im: Image.Image, width: int) -> Image.Image:
    if im.width <= width:
        return im.copy()
    ratio = width / im.width
    height = max(1, int(round(im.height * ratio)))
    return im.resize((width, height), Image.Resampling.LANCZOS)


def optimize_one(src: Path, stem: str, widths=cfg.WIDTHS) -> dict:
    """Write JPEG + WebP (+ AVIF) variants. Never upscale."""
    HERO_DIR.mkdir(parents=True, exist_ok=True)
    with _open_source(src) as original:
        native_w, native_h = original.size
        variants = {}
        largest = None
        for w in widths:
            target_w = min(w, native_w)
            # Skip duplicate sizes when the source is smaller than this step.
            if largest is not None and target_w == largest[0]:
                continue
            resized = _fit_width(original, target_w)
            largest = resized.size
            for ext, save_kwargs in (
                (".jpg", dict(format="JPEG", quality=90, optimize=True, progressive=True, subsampling=0)),
                (".webp", dict(format="WEBP", quality=86, method=6)),
                (".avif", dict(format="AVIF", quality=62)),
            ):
                dest = HERO_DIR / f"{stem}--{target_w}{ext}"
                if dest.exists() and dest.stat().st_mtime >= src.stat().st_mtime and dest.stat().st_size > 0:
                    variants.setdefault(target_w, {})[ext] = dest.name
                    continue
                tmp = dest.with_suffix(dest.suffix + ".tmp")
                try:
                    resized.save(tmp, **save_kwargs)
                    tmp.replace(dest)
                    variants.setdefault(target_w, {})[ext] = dest.name
                except Exception as exc:
                    if tmp.exists():
                        tmp.unlink()
                    if ext == ".avif":
                        print(f"  avif skipped for {stem}@{target_w}: {exc}")
                    else:
                        raise
            resized.close()
    return {
        "stem": stem,
        "source": str(src),
        "native": [native_w, native_h],
        "variants": {str(k): v for k, v in variants.items()},
    }


def collect_sources() -> list[tuple[str, Path]]:
    seen = {}
    for slide in cfg.SLIDES:
        if slide["kind"] == "original":
            seen.setdefault(slide["id"], Path(slide["source"]))
        else:
            seen.setdefault(slide["art_id"], Path(slide["art_source"]))
            seen.setdefault(slide["id"] + "-product", Path(slide["product_source"]))
    return list(seen.items())


def optimize_all(force: bool = False) -> dict:
    if force and HERO_DIR.exists():
        for p in HERO_DIR.glob("*"):
            if p.is_file():
                p.unlink()
    results = {}
    for stem, src in collect_sources():
        print(f"Optimizing {stem} from {src} ...")
        results[stem] = optimize_one(src, stem)
        print(f"  native {results[stem]['native'][0]}×{results[stem]['native'][1]}")
    return results


def _srcset(stem: str, ext: str, images: dict) -> str:
    parts = []
    info = images[stem]
    for w, files in sorted(info["variants"].items(), key=lambda kv: int(kv[0])):
        name = files.get(ext)
        if name:
            parts.append(f"/assets/images/hero/{name} {w}w")
    return ", ".join(parts)


def _fallback_src(stem: str, images: dict, prefer_w: int = 1600) -> tuple[str, int, int]:
    info = images[stem]
    native_w, native_h = info["native"]
    widths = sorted(int(w) for w in info["variants"])
    chosen = min(widths, key=lambda w: abs(w - prefer_w))
    # Prefer jpeg fallback for maximum compatibility.
    files = info["variants"][str(chosen)]
    name = files.get(".jpg") or files.get(".webp")
    # Actual pixel size of this variant (width = chosen, height scaled)
    height = max(1, int(round(native_h * (chosen / native_w))))
    return f"/assets/images/hero/{name}", chosen, height


def picture_html(
    stem: str,
    images: dict,
    alt: str,
    *,
    eager: bool = False,
    sizes: str = "100vw",
    object_position: str | None = None,
    extra_img_attrs: str = "",
) -> str:
    src, w, h = _fallback_src(stem, images, prefer_w=1600 if eager else 1600)
    avif = _srcset(stem, ".avif", images)
    webp = _srcset(stem, ".webp", images)
    style = f' style="object-position: {escape(object_position)};"' if object_position else ""
    loading = "" if eager else ' loading="lazy"'
    fetch = ' fetchpriority="high"' if eager else ""
    img = (
        f'<img src="{src}" alt="{escape(alt)}" width="{w}" height="{h}"'
        f'{fetch}{loading} decoding="async"{style} {extra_img_attrs}>'
    )
    sources = []
    if avif:
        sources.append(f'  <source type="image/avif" srcset="{avif}" sizes="{sizes}">')
    if webp:
        sources.append(f'  <source type="image/webp" srcset="{webp}" sizes="{sizes}">')
    return "<picture>\n" + "\n".join(sources) + "\n  " + img + "\n</picture>"


def backdrop_html(stem: str, images: dict, *, eager: bool = False) -> str:
    """Small (800px) copy of the painting for a blurred full-bleed atmosphere layer."""
    info = images[stem]
    widths = sorted(int(w) for w in info["variants"])
    chosen = 800 if 800 in widths else widths[0]
    files = info["variants"][str(chosen)]
    name = files.get(".webp") or files.get(".jpg") or files.get(".avif")
    native_w, native_h = info["native"]
    height = max(1, int(round(native_h * (chosen / native_w))))
    loading = "" if eager else ' loading="lazy"'
    return (
        f'<div class="hero-art-bg" aria-hidden="true">'
        f'<img src="/assets/images/hero/{name}" alt="" width="{chosen}" height="{height}"'
        f'{loading} decoding="async">'
        f"</div>"
    )


def wrap_lazy(inner: str, eager: bool) -> str:
    if eager:
        return inner
    return f"<template>\n{inner}\n</template>"


def render_original_slide(slide: dict, images: dict, eager: bool) -> str:
    pic = picture_html(
        slide["id"],
        images,
        slide["alt"],
        eager=eager,
        sizes="(min-width: 861px) 55vw, 92vw",
    )
    bg = backdrop_html(slide["id"], images, eager=eager)
    cap = (
        f'    <div class="hero-caption">\n'
        f'      <span class="eyebrow">Original painting</span>\n'
        f'      <p class="hero-art-title">{escape(slide["title"])}</p>\n'
        f'    </div>'
    )
    inner = (
        f"{bg}\n"
        f'      <figure class="hero-art-frame">\n'
        f"        {pic}\n"
        f"      </figure>"
    )
    return (
        f'    <div class="hero-slide{" is-active" if eager else ""}" '
        f'data-title="{escape(slide["title"])}">\n'
        f'      {wrap_lazy(inner, eager)}\n'
        f'{cap}\n'
        f'    </div>'
    )


def render_pairing_slide(slide: dict, images: dict, eager: bool) -> str:
    product_stem = slide["id"] + "-product"
    art_stem = slide["art_id"]
    art_pos = slide.get("art_object_position") or "center"
    product_pic = picture_html(
        product_stem,
        images,
        slide["product_alt"],
        eager=eager,
        sizes="(min-width: 861px) 42vw, 100vw",
        object_position="center",
    )
    art_pic = picture_html(
        art_stem,
        images,
        slide["art_alt"],
        eager=eager,
        sizes="(min-width: 861px) 40vw, 92vw",
    )
    art_bg = backdrop_html(art_stem, images, eager=eager)
    # Art is lazy even when this is not the first slide; product may be eager
    # only if this were first (it isn't). Both go in a template when not eager.
    inner = (
        f'      <div class="hero-pair">\n'
        f'        <figure class="hero-pair-art">\n'
        f'          {art_bg}\n'
        f'          {art_pic}\n'
        f'        </figure>\n'
        f'        <figure class="hero-pair-product">\n'
        f'          {product_pic}\n'
        f'        </figure>\n'
        f'      </div>\n'
        f'      <span class="hero-pair-kicker">{escape(slide["pairing_label"])}</span>\n'
        f'      <div class="hero-caption">\n'
        f'        <span class="eyebrow">{escape(slide["pairing_label"])}</span>\n'
        f'        <p class="hero-art-title">{escape(slide["art_title"])}</p>\n'
        f'        <a href="{escape(slide["product_url"], quote=True)}" '
        f'rel="noopener noreferrer">{escape(slide["cta"])} →</a>\n'
        f'      </div>'
    )
    body = inner if eager else f"<template>\n{inner}\n</template>"
    return (
        f'    <div class="hero-slide hero-slide--pair{" is-active" if eager else ""}" '
        f'data-title="{escape(slide["art_title"])}" '
        f'data-product-name="{escape(slide["product_name"])}" '
        f'data-product-url="{escape(slide["product_url"], quote=True)}" '
        f'data-cta="{escape(slide["cta"])}">\n'
        f'{body}\n'
        f'    </div>'
    )


def render_hero(images: dict, variant: str = "hybrid") -> str:
    parts = []
    first = True
    for slide in cfg.SLIDES:
        eager = first and slide["kind"] == "original"
        if slide["kind"] == "original":
            parts.append(render_original_slide(slide, images, eager=eager))
        else:
            parts.append(render_pairing_slide(slide, images, eager=False))
        first = False

    dots = []
    for i, slide in enumerate(cfg.SLIDES):
        if slide["kind"] == "original":
            label = f'Show {slide["title"]}'
        else:
            label = f'Show {slide["pairing_label"]}: {slide["art_title"]} and {slide["product_name"]}'
        current = ' aria-current="true"' if i == 0 else ""
        dots.append(f'    <button type="button" aria-label="{escape(label)}"{current}></button>')

    first_original = next(s for s in cfg.SLIDES if s["kind"] == "original")
    return f'''<section class="hero" aria-label="Original paintings by William Bowers" data-hero-slideshow data-hero-variant="{escape(variant)}" data-slide-ms="{cfg.SLIDE_MS}" data-pair-reveal-ms="{cfg.PAIR_REVEAL_MS}">
  <div class="hero-media">
{chr(10).join(parts)}
  </div>
  <div class="hero-copy">
    <span class="eyebrow">William Bowers · Hand Krafted Art</span>
    <h1>Original visions,<br><em>made to be lived with.</em></h1>
    <p class="hero-lead">Psychedelic and visionary paintings, pressed flower resin jewelry, and wearable art — handmade and printed to order by The Organic Mechanic.</p>
    <div class="hero-actions">
      <a class="btn btn-gold btn-lg" href="/shop/original-paintings/">Shop originals</a>
      <a class="btn btn-ghost btn-lg" href="/shop/jewelry/">Shop jewelry</a>
    </div>
  </div>
  <div class="hero-dots" aria-label="Featured paintings">
{chr(10).join(dots)}
  </div>
</section>
'''


def preload_tags(images: dict) -> str:
    first = next(s for s in cfg.SLIDES if s["kind"] == "original")
    # Preload the most likely LCP candidate: webp at 1600/2400 via imagesrcset.
    webp = _srcset(first["id"], ".webp", images)
    jpg, _, _ = _fallback_src(first["id"], images, prefer_w=1600)
    return (
        f'  <link rel="preload" as="image" href="{jpg}" imagesrcset="{webp}" '
        f'imagesizes="(min-width: 861px) 55vw, 92vw" type="image/webp" fetchpriority="high">\n'
    )


def patch_index(html: str, hero: str, images: dict) -> str:
    # Stylesheet
    html = html.replace('href="/assets/css/hero.css"', 'href="/assets/css/hero.css?v=20261121c"')
    if 'href="/assets/css/hero.css' not in html:
        html = html.replace(
            '<link rel="stylesheet" href="/assets/css/style.css">',
            '<link rel="stylesheet" href="/assets/css/style.css">\n  '
            '<link rel="stylesheet" href="/assets/css/hero.css?v=20261121c">',
            1,
        )
    # Preload (replace previous managed block or insert after existing preloads)
    preload = preload_tags(images)
    html = re.sub(
        r"  <!-- HERO-PRELOAD-START -->.*?<!-- HERO-PRELOAD-END -->\n",
        "",
        html,
        flags=re.S,
    )
    html = html.replace(
        '<link rel="stylesheet" href="/assets/css/fonts.css">',
        '<!-- HERO-PRELOAD-START -->\n' + preload + '  <!-- HERO-PRELOAD-END -->\n'
        '  <link rel="stylesheet" href="/assets/css/fonts.css">',
        1,
    )
    # Hero section — first <section class="hero" ...>...</section>
    html, n = re.subn(
        r'<section class="hero"[\s\S]*?</section>',
        hero.rstrip(),
        html,
        count=1,
    )
    if n != 1:
        raise RuntimeError(f"expected to replace exactly 1 hero section, replaced {n}")
    # Script
    html = html.replace('src="/assets/js/hero.js"', 'src="/assets/js/hero.js?v=20261121c"')
    if 'src="/assets/js/hero.js' not in html:
        html = html.replace(
            '<script src="/assets/js/main.js" defer></script>',
            '<script src="/assets/js/hero.js?v=20261121c" defer></script>\n  '
            '<script src="/assets/js/main.js" defer></script>',
            1,
        )
    return html


def patch_main_js(text: str) -> str:
    needle = '  const hero = document.querySelector(".hero");\n  if (hero) {'
    replacement = (
        '  const hero = document.querySelector(".hero");\n'
        '  // Hero slideshow is owned by /assets/js/hero.js when data-hero-slideshow is present.\n'
        '  if (hero && !hero.hasAttribute("data-hero-slideshow")) {'
    )
    if "data-hero-slideshow" in text:
        return text
    if needle not in text:
        raise RuntimeError("could not find hero block in main.js to guard")
    return text.replace(needle, replacement, 1)


def write_assets(images: dict, variant: str = "hybrid") -> None:
    CSS_OUT.write_text((TEMPLATES / "hero.css").read_text(), encoding="utf-8")
    JS_OUT.write_text((TEMPLATES / "hero.js").read_text(), encoding="utf-8")
    index = SITE / "index.html"
    html = index.read_text(encoding="utf-8")
    hero = render_hero(images, variant=variant)
    index.write_text(patch_index(html, hero, images), encoding="utf-8")
    main_js = SITE / "assets" / "js" / "main.js"
    main_js.write_text(patch_main_js(main_js.read_text(encoding="utf-8")), encoding="utf-8")


def write_manifest(images: dict) -> None:
    payload = {
        "variant": cfg.LIVE_VARIANT,
        "timing": {"slide_ms": cfg.SLIDE_MS, "fade_ms": cfg.FADE_MS, "pair_reveal_ms": cfg.PAIR_REVEAL_MS},
        "images": images,
        "slides": cfg.SLIDES,
        "missing": cfg.MISSING,
    }
    MANIFEST.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Wrote {MANIFEST}")


def apply_hero(force: bool = False, variant: str = cfg.LIVE_VARIANT) -> None:
    images = optimize_all(force=force)
    write_assets(images, variant=variant)
    write_manifest(images)
    print("Hero slideshow applied to", SITE / "index.html")


def main() -> int:
    parser = argparse.ArgumentParser(description="Build The Organic Mechanic site (catalog + hero).")
    parser.add_argument("--hero-only", action="store_true", help="Only rebuild the homepage hero; do not fetch or render the catalog.")
    parser.add_argument("--no-fetch", action="store_true", help="Skip the Big Cartel fetch and rebuild from the current scrape/.")
    parser.add_argument("--rebuild-pages", action="store_true", help="Rewrite every product and shop page from scrape/ (keeps index.html until the hero step).")
    parser.add_argument("--force", action="store_true", help="Re-encode hero images even if they look up to date.")
    parser.add_argument("--force-images", action="store_true", help="Re-encode product (and, with --force, hero) images even if they look up to date.")
    parser.add_argument("--variant", default=cfg.LIVE_VARIANT, choices=("hybrid", "sequential"))
    args = parser.parse_args()

    if not SITE.exists():
        raise SystemExit(f"site directory not found: {SITE}")

    report = None
    if not args.hero_only and not args.no_fetch:
        import fetch_catalog
        report = fetch_catalog.sync(force_images=args.force_images)

    if not args.hero_only:
        import site_gen
        changed = set((report or {}).get("added") or []) | set((report or {}).get("updated") or [])
        # A no-fetch full rebuild still refreshes listings when --rebuild-pages
        # is set; otherwise only missing product pages are written, then the hero.
        result = site_gen.generate_catalog(
            force_images=args.force_images,
            overwrite_pages=args.rebuild_pages,
            changed_slugs=changed,
        )
        print(
            f"Catalog: {result['products']} products, "
            f"{len(result['written'])} files written, "
            f"{len(result['skipped_existing'])} existing product pages kept"
        )

    apply_hero(force=args.force, variant=args.variant)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

