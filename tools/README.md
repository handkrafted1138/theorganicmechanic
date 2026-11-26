# Site generator

Source for the Organic Mechanic GitHub Pages site (the parent of this folder).

This used to live in `/workspace/organic-mechanic/build/`, which a box reset
wipes (the reserved name `build`, and also dot-directories like `.venv`). It
now lives *inside the repo* so a reset cannot delete the generator.

## Command (daily Big Cartel sync)

```bash
/workspace/organic-mechanic/venv-site/bin/python /workspace/organic-mechanic/site/tools/build.py
```

That fetches `https://theorganicmechanic.bigcartel.com/products.json`, rebuilds
new or changed product pages and shop listings, then re-applies the homepage
hero last so a catalog rebuild cannot wipe it.

Hero-only:

```bash
/workspace/organic-mechanic/venv-site/bin/python /workspace/organic-mechanic/site/tools/build.py --hero-only
```

The slideshow is defined in `hero_config.py`. Product display-title overrides
are in `display_titles.json`. Scrape cache and full-resolution downloads live
outside the repo at `/workspace/organic-mechanic/scrape/`. Print masters used
by the hero live under `/workspace/prints2/masters/` (and a few other local
paths named in `hero_config.py`).

The Python environment is `/workspace/organic-mechanic/venv-site` (not `.venv`,
which is also wiped on reset). Recreate it with:

```bash
python3 -m venv /workspace/organic-mechanic/venv-site
/workspace/organic-mechanic/venv-site/bin/pip install jinja2 pillow pillow-avif-plugin
```

## Past Works Archives

Retired products are listed in `retired_slugs.json`. The daily sync excludes
them from shop listings, category pages, counts, and the sitemap, and writes
redirects from `/product/<slug>/` to `/archive/`. The archive page is generated
from `../data/archive.json` (names, descriptions, prices, categories) and
full-resolution photographs in `../assets/images/archive/<slug>/`.

Do not remove a slug from `retired_slugs.json` without also deciding whether
it should return to the live shop.
