"""Homepage hero slideshow — original paintings and canvas-to-wearable pairings.

This is the source of truth. build.py reads it on every site rebuild so a
daily Big Cartel catalog sync cannot silently fall back to the old 3-slide hero.
"""

# Display variants:
#   live / hybrid: originals full-bleed; pairing slides are side-by-side on
#     wide screens, and product-then-painting crossfades on smaller screens.
#   sequential: pairing slides are expanded into two full-bleed slides
#     (product photo, then the original). Used for the comparison screenshot.
LIVE_VARIANT = "hybrid"

# Timing
SLIDE_MS = 6000
FADE_MS = 1800
PAIR_REVEAL_MS = 2800  # on mobile hybrid, when the painting fades in over the product

# Responsive widths written for each still
WIDTHS = (800, 1600, 2400)

SLIDES = [
    {
        "id": "lion-and-the-hare",
        "kind": "original",
        "title": "The Lion and the Hare",
        "alt": "The Lion and the Hare, original painting by William Bowers — a blue hare facing a roaring red lion",
        "source": "/workspace/prints2/masters/lion--the-hair300.jpg",
        "source_note": "Print master 300 DPI (Drive: lion--the-hair300.jpg, uploaded 2026-11-24), 6400×4267",
        "object_position": "center",
        "requested": True,
    },
    {
        "id": "pair-lion-bomber",
        "kind": "pairing",
        "title": "The Lion and the Hare",
        "pairing_label": "From canvas to wearable",
        "product_name": "Unisex Bomber Jacket",
        "product_slug": "unisex-bomber-jacket",
        "product_url": "https://theorganicmechanic.bigcartel.com/product/unisex-bomber-jacket",
        "cta": "Shop the bomber jacket",
        "art_id": "lion-and-the-hare",
        "art_title": "The Lion and the Hare",
        "art_alt": "The Lion and the Hare, original painting by William Bowers",
        "art_source": "/workspace/prints2/masters/lion--the-hair300.jpg",
        "art_source_note": "Print master 300 DPI (Drive: lion--the-hair300.jpg, uploaded 2026-11-24), 6400×4267",
        "art_object_position": "center",
        "product_alt": "Unisex bomber jacket printed with The Lion and the Hare by William Bowers",
        "product_source": "/workspace/organic-mechanic/scrape/images/products/unisex-bomber-jacket__02__all-over-print-unisex-bomber-jacket-white-front-6a80486d0c035.jpg",
        "product_source_note": "Big Cartel merch mockup (front), 2000×2000",
        "product_fallback": "/workspace/organic-mechanic/scrape/images/products/unisex-bomber-jacket__02__all-over-print-unisex-bomber-jacket-white-front-6a80486d0c035.jpg",
    },
    {
        "id": "the-pondering",
        "kind": "original",
        "title": "The Pondering",
        "alt": "The Pondering, original acrylic painting by William Bowers — a surreal contemplative figure in blue, gold, and magenta",
        "source": "/workspace/prints2/masters/The_pondering_astronaut_300dpi.jpg",
        "source_note": "Print master 300 DPI (The_pondering_astronaut_300dpi.jpg), 8403×9477",
        "object_position": "center 28%",
        "requested": True,
    },
    {
        "id": "pair-ponder-tee",
        "kind": "pairing",
        "title": "The Pondering",
        "pairing_label": "From canvas to wearable",
        "product_name": "“Ponder” Youth cotton crew neck t-shirt",
        "product_slug": "youth-cotton-crew-neck-t-shirt",
        "product_url": "https://theorganicmechanic.bigcartel.com/product/youth-cotton-crew-neck-t-shirt",
        "cta": "Shop the Ponder tee",
        "art_id": "the-pondering",
        "art_title": "The Pondering",
        "art_alt": "The Pondering, original acrylic painting by William Bowers",
        "art_source": "/workspace/prints2/masters/The_pondering_astronaut_300dpi.jpg",
        "art_source_note": "Print master 300 DPI, 8403×9477",
        "art_object_position": "center 28%",
        "product_alt": "Ponder all-over-print youth t-shirt featuring The Pondering by William Bowers",
        "product_source": "/workspace/organic-mechanic/scrape/images/products/youth-cotton-crew-neck-t-shirt__01__all-over-print-youth-cotton-crew-neck-t-shirt-white-front-6a7d420f3ca79.jpg",
        "product_source_note": "Big Cartel merch mockup (front), 2000×2000",
    },
    {
        "id": "cepla-producer",
        "kind": "original",
        "title": "Cepla-Producer",
        "alt": "Cepla-Producer (Octopus on Keys), original painting by William Bowers — a cosmic octopus with headphones playing a keyboard",
        "source": "/workspace/printful/octopus-on-keys_24x36.jpg",
        "source_note": "Google Drive / local 24×36 in 300 DPI master (octopus-on-keys_24x36in_landscape_300dpi.jpg), 10800×7200",
        "object_position": "center 42%",
        "requested": True,
    },
    {
        "id": "the-light-conductor",
        "kind": "original",
        "title": "The Light Conductor",
        "alt": "The Light Conductor, original painting by William Bowers — a visored figure conducting beams of light",
        "source": "/workspace/prints2/masters/The_Light_Conductor_300dpi.jpg",
        "source_note": "Print master 300 DPI (Drive: The_Light_Conductor_300dpi.jpg), 8004×10008",
        "object_position": "center 32%",
        "requested": True,
    },
    {
        "id": "pair-conductor-bomber",
        "kind": "pairing",
        "title": "The Light Conductor",
        "pairing_label": "From canvas to wearable",
        "product_name": "Unisex Bomber Jacket",
        "product_slug": "unisex-bomber-jacket",
        "product_url": "https://theorganicmechanic.bigcartel.com/product/unisex-bomber-jacket",
        "cta": "Shop the bomber jacket",
        "pairing_note": "The Light Conductor is printed on the back of the same Lion and the Hare bomber.",
        "art_id": "the-light-conductor",
        "art_title": "The Light Conductor",
        "art_alt": "The Light Conductor, original painting by William Bowers",
        "art_source": "/workspace/prints2/masters/The_Light_Conductor_300dpi.jpg",
        "art_source_note": "Print master 300 DPI, 8004×10008",
        "art_object_position": "center 32%",
        "product_alt": "Back of the unisex bomber jacket printed with The Light Conductor by William Bowers",
        "product_source": "/workspace/organic-mechanic/scrape/images/products/unisex-bomber-jacket__01__all-over-print-unisex-bomber-jacket-white-back-6a80486d0bc2d.jpg",
        "product_source_note": "Big Cartel merch mockup (back), 2000×2000",
    },
    {
        "id": "sacred-samurai",
        "kind": "original",
        "title": "Sacred Samurai",
        "alt": "Sacred Samurai, original painting by William Bowers — a samurai silhouette against a violet and rose field",
        "source": "/workspace/prints2/masters/Symphony_Samurai_300dpi.jpg",
        "source_note": "Print master 300 DPI filed as Symphony_Samurai_300dpi.jpg, 7809×10341",
        "object_position": "center 35%",
        "requested": True,
    },
    {
        "id": "cosmic-owl",
        "kind": "original",
        "title": "Cosmic Owl",
        "alt": "Cosmic Owl, original psychedelic mandala acrylic painting on a round canvas by William Bowers",
        "source": "/workspace/organic-mechanic/scrape/images/products/owl-mandala__02__20260421_084339.jpg",
        "source_note": "Big Cartel original-painting photo, 3000×2854",
        "object_position": "center 45%",
        "shop_path": "/product/owl-mandala/",
    },
    {
        "id": "heady-jellys",
        "kind": "original",
        "title": "Heady Jellys",
        "alt": "Heady Jellys, original painting by William Bowers — two vivid jellyfish in a teal sea",
        "source": "/workspace/prints2/masters/Heady_jellys_300dpi.jpg",
        "source_note": "Print master 300 DPI, 7737×10575",
        "object_position": "center 30%",
    },
    {
        "id": "electric-lady",
        "kind": "original",
        "title": "Electric Lady",
        "alt": "Electric Lady, original mixed-media sculpture on fractal-burned live-edge wood by William Bowers",
        "source": "/workspace/organic-mechanic/scrape/images/products/electric-lady__01__electric+lady.jpg",
        "source_note": "Big Cartel original-art photo, 2880×4271",
        "object_position": "center 35%",
        "shop_path": "/product/electric-lady/",
    },
    {
        "id": "ghost-whispers",
        "kind": "original",
        "title": "Ghost Whispers",
        "alt": "Ghost Whispers, original painting by William Bowers — a mechanical being with flanking spirit faces",
        "source": "/workspace/organic-mechanic/scrape/images/products/ghostwhispers__01__11461.jpg",
        "source_note": "Big Cartel original-painting photo, 2034×2846",
        "object_position": "center 28%",
        "shop_path": "/product/ghostwhispers/",
    },
    {
        "id": "tree-house",
        "kind": "original",
        "title": "Tree House",
        "alt": "Tree House, original painting by William Bowers — a cabin perched in twisted golden roots",
        "source": "/workspace/prints2/masters/Tree_house_300dpi.jpg",
        "source_note": "Print master 300 DPI, 8007×10569",
        "object_position": "center 40%",
    },
]

# Requested titles we could not include as high-quality original photos.
MISSING = [
    {
        "title": "Bob Crosses DMT Dream",
        "reason": "No file, listing, or Drive match under this title (or close variants such as DMT, Bob Crosses, or Dream). Not in the Print Masters 300 DPI set, Big Cartel catalog, or local scrape.",
    },
    {
        "title": "Mandala Unraveled",
        "reason": "Only the Unraveled & Restored backpack merch mockups were found (2000×2000 product photos). No high-resolution photograph of the original mandala painting.",
    },
    {
        "title": "Mandala Restored",
        "reason": "Same as Mandala Unraveled — the backpack describes two contrasting mandalas, but the original paintings themselves are not in the catalog or Drive under these names.",
    },
    {
        "title": "Cephla-Creator (if this was meant instead of Cepla-Producer)",
        "reason": "The shop original “Cephla-Creator” (octopus with paintbrushes) exists, but every Big Cartel photo is ≤771px wide. Skipped as below the 1600px quality bar. The high-res “Octopus on Keys” painting is used for Cepla-Producer.",
    },
]

# Sacred Samauri tee/hoodie was not paired: the merch graphic is a symmetrical
# two-samurai lotus design, not a print of the Sacred Samurai / Symphony Samurai
# silhouette painting.
