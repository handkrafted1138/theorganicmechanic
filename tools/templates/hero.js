/* Homepage original-art slideshow — written by build/build.py. */
(() => {
  const hero = document.querySelector("[data-hero-slideshow]");
  if (!hero) return;

  const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const params = new URLSearchParams(location.search);
  const requestedVariant = params.get("hero") === "sequential" ? "sequential" : (hero.getAttribute("data-hero-variant") || "hybrid");
  const SLIDE_MS = Number(hero.getAttribute("data-slide-ms")) || 6000;
  const PAIR_REVEAL_MS = Number(hero.getAttribute("data-pair-reveal-ms")) || 2800;
  const wideQuery = window.matchMedia("(min-width: 861px)");

  const hydrate = (root) => {
    root.querySelectorAll(":scope .hero-slide template").forEach((tpl) => {
      tpl.parentNode.appendChild(tpl.content.cloneNode(true));
      tpl.remove();
    });
  };

  const preload = (slide) => {
    if (!slide) return;
    slide.querySelectorAll("template").forEach((tpl) => {
      tpl.parentNode.appendChild(tpl.content.cloneNode(true));
      tpl.remove();
    });
    slide.querySelectorAll("img").forEach((img) => {
      if (img.dataset.hydrated) return;
      img.dataset.hydrated = "1";
      // Nudge the browser to fetch now (including srcset candidates).
      if (typeof img.decode === "function") img.decode().catch(() => {});
    });
  };

  const originalSlides = [...hero.querySelectorAll(".hero-slide")];
  const originalDots = hero.querySelector(".hero-dots");

  const expandSequential = () => {
    if (requestedVariant !== "sequential") return;
    hero.setAttribute("data-hero-variant", "sequential");
    const media = hero.querySelector(".hero-media");
    const dots = hero.querySelector(".hero-dots");
    if (!media || !dots) return;

    const next = [];
    const nextDots = [];
    originalSlides.forEach((slide) => {
      if (slide.classList.contains("hero-slide--pair")) {
        const product = slide.querySelector(".hero-pair-product");
        const art = slide.querySelector(".hero-pair-art");
        const title = slide.getAttribute("data-title") || "Original painting";
        const productName = slide.getAttribute("data-product-name") || "Wearable";
        const url = slide.getAttribute("data-product-url") || "";
        const cta = slide.getAttribute("data-cta") || "Shop this piece";

        const make = (kind, sourceEl, captionTitle, link) => {
          const div = document.createElement("div");
          div.className = `hero-slide hero-slide--${kind}`;
          div.setAttribute("data-title", captionTitle);
          const clone = sourceEl.cloneNode(true);
          clone.querySelectorAll("img").forEach((img) => {
            img.style.objectPosition = kind === "art" ? (sourceEl.getAttribute("data-object-position") || "center") : "center";
          });
          div.appendChild(clone);
          const cap = document.createElement("div");
          cap.className = "hero-caption";
          cap.innerHTML = kind === "product"
            ? `<span class="eyebrow">From canvas to wearable</span><p class="hero-art-title"></p>${link ? `<a href="${link}">${cta}</a>` : ""}`
            : `<span class="eyebrow">Original painting</span><p class="hero-art-title"></p>`;
          cap.querySelector(".hero-art-title").textContent = captionTitle;
          div.appendChild(cap);
          return div;
        };

        next.push(make("product", product, productName, url));
        next.push(make("art", art, title, ""));
        nextDots.push(`Show ${productName}`);
        nextDots.push(`Show ${title}`);
      } else {
        next.push(slide);
        const title = slide.getAttribute("data-title") || "Featured painting";
        nextDots.push(`Show ${title}`);
      }
    });

    media.innerHTML = "";
    next.forEach((s) => media.appendChild(s));
    dots.innerHTML = "";
    nextDots.forEach((label, i) => {
      const b = document.createElement("button");
      b.type = "button";
      b.setAttribute("aria-label", label);
      if (i === 0) b.setAttribute("aria-current", "true");
      dots.appendChild(b);
    });
    next[0]?.classList.add("is-active");
  };

  if (requestedVariant === "sequential") {
    hydrate(hero); // sequential screenshots should have every still ready
    expandSequential();
  } else {
    expandSequential();
    hydrate(hero);
  }

  const slides = () => [...hero.querySelectorAll(".hero-slide")];
  const dots = () => [...hero.querySelectorAll(".hero-dots button")];

  let i = 0;
  let timer = null;
  let pairTimer = null;

  const clearPairReveal = () => {
    if (pairTimer) {
      clearTimeout(pairTimer);
      pairTimer = null;
    }
    slides().forEach((s) => s.classList.remove("is-pair-reveal"));
  };

  const schedulePairReveal = (slide) => {
    clearPairReveal();
    if (reduce) return;
    if (requestedVariant === "sequential") return;
    if (!slide.classList.contains("hero-slide--pair")) return;
    if (wideQuery.matches) return; // side-by-side already shows both
    pairTimer = setTimeout(() => slide.classList.add("is-pair-reveal"), PAIR_REVEAL_MS);
  };

  const measureArt = (slide) => {
    if (!slide || wideQuery.matches) return;
    const img = slide.querySelector(".hero-art-frame img") || slide.querySelector(".hero-pair-art picture img");
    const apply = () => {
      if (!img) return;
      const h = img.getBoundingClientRect().height;
      if (h > 0) hero.style.setProperty("--active-art-h", `${Math.round(h)}px`);
    };
    if (!img) return;
    if (img.complete) apply();
    else img.addEventListener("load", apply, { once: true });
    if (typeof img.decode === "function") img.decode().then(apply).catch(() => {});
  };

  const show = (n) => {
    const list = slides();
    if (!list.length) return;
    i = (n + list.length) % list.length;
    preload(list[i]);
    list.forEach((s, idx) => s.classList.toggle("is-active", idx === i));
    dots().forEach((d, idx) => d.setAttribute("aria-current", idx === i ? "true" : "false"));
    // Preload the upcoming slide so the next fade is instant.
    preload(list[(i + 1) % list.length]);
    schedulePairReveal(list[i]);
    measureArt(list[i]);
  };

  const stop = () => {
    if (timer) {
      clearInterval(timer);
      timer = null;
    }
  };

  const start = () => {
    if (reduce || slides().length < 2) return;
    stop();
    timer = setInterval(() => show(i + 1), SLIDE_MS);
  };

  dots().forEach((d, idx) => d.addEventListener("click", () => { show(idx); start(); }));
  hero.addEventListener("mouseenter", stop);
  hero.addEventListener("mouseleave", start);
  hero.addEventListener("focusin", stop);
  hero.addEventListener("focusout", start);

  // First slide is already in the document (LCP). Preload slide 2 after first paint.
  const list = slides();
  if (list[1]) {
    if (document.readyState === "complete") preload(list[1]);
    else window.addEventListener("load", () => preload(list[1]), { once: true });
  }

  show(0);
  start();
  wideQuery.addEventListener?.("change", () => measureArt(slides()[i]));
  window.addEventListener("resize", () => measureArt(slides()[i]), { passive: true });

  if (!reduce) {
    const onScroll = () => {
      const rect = hero.getBoundingClientRect();
      const p = Math.min(1, Math.max(0, -rect.top / Math.max(rect.height, 1)));
      hero.querySelectorAll(".hero-art-bg img").forEach((img) => {
        img.style.transform = `scale(1.12) translateY(${p * 4}%)`;
      });
    };
    window.addEventListener("scroll", onScroll, { passive: true });
    onScroll();
  }
})();
