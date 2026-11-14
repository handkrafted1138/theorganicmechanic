# the Organic Mechanic

Static website for [theorganicmechanic.shop](https://theorganicmechanic.shop/), the artist shop of William Bowers.

This is a plain HTML/CSS/JS site generated for **GitHub Pages**. Checkout stays on Big Cartel: buy buttons go to `https://theorganicmechanic.bigcartel.com/product/...` (not the custom domain, which will point here).

## Publish

1. Create a GitHub repository (for example `theorganicmechanic` or `theorganicmechanic.github.io`).
2. Upload the contents of this folder — the files next to this README, including `CNAME`, `index.html`, and `assets/` — to the repository root.
3. In the repo Settings → Pages, set the source to the `main` branch (root).
4. Point the IONOS DNS for `theorganicmechanic.shop` at GitHub Pages once the site is live, and keep `www` in mind if you still want it. The `CNAME` file already contains `theorganicmechanic.shop`.
5. Leave the Big Cartel store running so checkout, cart, and payments keep working.

Do not put full-resolution scrape files in this repo; images here are already resized (max 2000px) as AVIF, WebP, and JPEG.

Rebuild from the parent project with:

```bash
.venv/bin/python build/build.py
```
