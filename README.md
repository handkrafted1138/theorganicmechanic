# the Organic Mechanic

Static website for [theorganicmechanic.shop](https://theorganicmechanic.shop/), the artist shop of William Bowers.

This is a plain HTML/CSS/JS site generated for **GitHub Pages**. Checkout stays on Big Cartel: buy buttons go to `https://theorganicmechanic.bigcartel.com/product/...` (not the custom domain, which will point here).

## Publish

1. Create a GitHub repository (for example `theorganicmechanic` or `theorganicmechanic.github.io`).
2. Upload the contents of this folder — the files next to this README, including `CNAME`, `index.html`, and `assets/` — to the repository root.
3. In the repo Settings → Pages, set the source to the `main` branch (root).
4. Point the IONOS DNS for `theorganicmechanic.shop` at GitHub Pages once the site is live, and keep `www` in mind if you still want it. The `CNAME` file already contains `theorganicmechanic.shop`.
5. Leave the Big Cartel store running so checkout, cart, and payments keep working.

Do not put full-resolution scrape files in this repo; product images are resized (max 2000px) as AVIF, WebP, and JPEG. Homepage hero stills are resized to 800/1600/2400px.

Rebuild from the parent project with the project venv (this is also the command the daily Big Cartel sync should run):

```bash
/workspace/organic-mechanic/venv-site/bin/python /workspace/organic-mechanic/site/tools/build.py
```

That fetches Big Cartel, rebuilds any new or changed product pages and shop listings, then re-applies the homepage hero last so the catalog rebuild cannot wipe it.

Hero-only:

```bash
/workspace/organic-mechanic/venv-site/bin/python /workspace/organic-mechanic/site/tools/build.py --hero-only
```

The slideshow is defined in `tools/hero_config.py`.

The generator lives in `tools/` (inside this repo). Do not put it in a folder named `build`, `dist`, `out`, or a dot-directory like `.venv` — those are wiped when the box is reset.
