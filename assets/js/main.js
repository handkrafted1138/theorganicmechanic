(() => {
  const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const fine = window.matchMedia("(pointer: fine)").matches;

  const header = document.querySelector(".site-header");
  const onScrollHeader = () => {
    if (!header) return;
    header.classList.toggle("is-scrolled", window.scrollY > 12);
  };
  onScrollHeader();
  window.addEventListener("scroll", onScrollHeader, { passive: true });

  const toggle = document.querySelector(".menu-toggle");
  const nav = document.querySelector(".nav");
  if (toggle && nav) {
    toggle.addEventListener("click", () => {
      const open = document.body.classList.toggle("nav-open");
      toggle.setAttribute("aria-expanded", String(open));
    });
    nav.querySelectorAll("a").forEach((a) =>
      a.addEventListener("click", () => {
        document.body.classList.remove("nav-open");
        toggle.setAttribute("aria-expanded", "false");
      })
    );
  }

  if (!reduce && fine) {
    const glow = document.createElement("div");
    glow.className = "cursor-glow";
    glow.setAttribute("aria-hidden", "true");
    document.body.appendChild(glow);
    let x = 0, y = 0, cx = 0, cy = 0, on = false;
    window.addEventListener("pointermove", (e) => {
      x = e.clientX; y = e.clientY;
      if (!on) { on = true; glow.classList.add("is-on"); }
    }, { passive: true });
    window.addEventListener("pointerleave", () => { on = false; glow.classList.remove("is-on"); });
    const tick = () => {
      cx += (x - cx) * 0.16;
      cy += (y - cy) * 0.16;
      glow.style.transform = `translate(calc(${cx}px - 50%), calc(${cy}px - 50%))`;
      requestAnimationFrame(tick);
    };
    requestAnimationFrame(tick);
  }

  /* Hero parallax + slideshow */
  const hero = document.querySelector(".hero");
  // Hero slideshow is owned by /assets/js/hero.js when data-hero-slideshow is present.
  if (hero && !hero.hasAttribute("data-hero-slideshow")) {
    const hydrate = () => {
      hero.querySelectorAll(".hero-slide template").forEach((tpl) => {
        tpl.parentNode.appendChild(tpl.content.cloneNode(true));
        tpl.remove();
      });
    };
    if (document.readyState === "complete") hydrate();
    else window.addEventListener("load", hydrate);

    const slides = [...hero.querySelectorAll(".hero-slide")];
    const dots = [...hero.querySelectorAll(".hero-dots button")];
    let i = 0, timer;
    const show = (n) => {
      i = (n + slides.length) % slides.length;
      slides.forEach((s, idx) => s.classList.toggle("is-active", idx === i));
      dots.forEach((d, idx) => d.setAttribute("aria-current", idx === i ? "true" : "false"));
    };
    const start = () => {
      if (reduce || slides.length < 2) return;
      stop();
      timer = setInterval(() => show(i + 1), 6500);
    };
    const stop = () => { if (timer) clearInterval(timer); };
    dots.forEach((d, idx) => d.addEventListener("click", () => { show(idx); start(); }));
    hero.addEventListener("mouseenter", stop);
    hero.addEventListener("mouseleave", start);
    start();

    if (!reduce) {
      const imgs = hero.querySelectorAll(".hero-slide img");
      const onScroll = () => {
        const rect = hero.getBoundingClientRect();
        const p = Math.min(1, Math.max(0, -rect.top / Math.max(rect.height, 1)));
        imgs.forEach((img) => { img.style.transform = `scale(1.08) translateY(${p * 8}%)`; });
      };
      window.addEventListener("scroll", onScroll, { passive: true });
      onScroll();
    }
  }

  /* Gallery + lightbox */
  const gallery = document.querySelector("[data-gallery]");
  if (gallery) {
    const mainImg = gallery.querySelector("[data-gallery-main] img");
    const mainPic = gallery.querySelector("[data-gallery-main] picture");
    const thumbs = [...gallery.querySelectorAll("[data-thumb]")];
    const sources = thumbs.map((t) => ({
      full: t.getAttribute("data-full"),
      alt: t.getAttribute("data-alt") || "",
      webp: t.getAttribute("data-webp") || "",
      avif: t.getAttribute("data-avif") || "",
      src: t.querySelector("img")?.getAttribute("src") || "",
    }));
    let idx = 0;

    const applyMain = (n) => {
      idx = n;
      const s = sources[n];
      if (!s || !mainImg) return;
      mainImg.src = s.src;
      mainImg.alt = s.alt;
      thumbs.forEach((t, i) => t.setAttribute("aria-current", i === n ? "true" : "false"));
      if (mainPic) {
        const av = mainPic.querySelector('source[type="image/avif"]');
        const wp = mainPic.querySelector('source[type="image/webp"]');
        if (av && s.avif) av.srcset = s.avif;
        if (wp && s.webp) wp.srcset = s.webp;
      }
    };
    thumbs.forEach((t, n) => t.addEventListener("click", () => applyMain(n)));

    const lb = document.querySelector(".lightbox");
    const lbImg = lb?.querySelector("img");
    const open = (n) => {
      if (!lb || !lbImg) return;
      idx = n;
      lbImg.src = sources[n].full || sources[n].src;
      lbImg.alt = sources[n].alt;
      lb.classList.add("is-open");
      lb.setAttribute("aria-hidden", "false");
      document.body.style.overflow = "hidden";
      lb.querySelector(".lightbox-close")?.focus();
    };
    const close = () => {
      lb?.classList.remove("is-open");
      lb?.setAttribute("aria-hidden", "true");
      document.body.style.overflow = "";
    };
    gallery.querySelector("[data-gallery-main]")?.addEventListener("click", () => open(idx));
    lb?.querySelector(".lightbox-close")?.addEventListener("click", close);
    lb?.querySelector(".prev")?.addEventListener("click", () => open((idx - 1 + sources.length) % sources.length));
    lb?.querySelector(".next")?.addEventListener("click", () => open((idx + 1) % sources.length));
    lb?.addEventListener("click", (e) => { if (e.target === lb) close(); });
    window.addEventListener("keydown", (e) => {
      if (!lb?.classList.contains("is-open")) return;
      if (e.key === "Escape") close();
      if (e.key === "ArrowLeft") open((idx - 1 + sources.length) % sources.length);
      if (e.key === "ArrowRight") open((idx + 1) % sources.length);
    });
  }

  /* Contact form → mailto */
  const form = document.querySelector("[data-mailto-form]");
  if (form) {
    form.addEventListener("submit", (e) => {
      e.preventDefault();
      const data = new FormData(form);
      const name = (data.get("name") || "").toString().trim();
      const email = (data.get("email") || "").toString().trim();
      const topic = (data.get("topic") || "Inquiry").toString();
      const message = (data.get("message") || "").toString().trim();
      const subject = encodeURIComponent(`${topic} — ${name || "website inquiry"}`);
      const body = encodeURIComponent(`Name: ${name}\nEmail: ${email}\n\n${message}`);
      window.location.href = `mailto:theorganicmechanicshop@gmail.com?subject=${subject}&body=${body}`;
    });
  }
})();
