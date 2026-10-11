(() => {
  const reduce = matchMedia("(prefers-reduced-motion: reduce)").matches;
  // Variable message sign: real upgrades actnode found on public workflows
  const msgs = [
    ["actions/checkout@v4", "→ @v5 · node24"],
    ["actions/setup-node@v4", "→ @v5 · node24"],
    ["actions/cache@v4", "→ @v5 · node24"],
    ["actions/upload-artifact@v4", "→ @v6 · node24"],
    ["actions/setup-python@v5", "→ @v6 · node24"],
  ];
  const face = document.querySelector(".vms-face");
  if (face && !reduce) {
    let i = 0;
    setInterval(() => {
      i = (i + 1) % msgs.length;
      face.classList.remove("flip"); void face.offsetWidth; face.classList.add("flip");
      setTimeout(() => {
        face.querySelector(".vms-from").textContent = msgs[i][0];
        face.querySelector(".vms-to").textContent = msgs[i][1];
      }, 250);
    }, 2600);
  }
  if (reduce) return;
  // Driving: the center line moves with scroll, roadside signs come toward you
  const hw = document.querySelector(".highway");
  let ticking = false;
  addEventListener("scroll", () => {
    if (ticking) return; ticking = true;
    requestAnimationFrame(() => { hw.style.setProperty("--drive", (scrollY * 1.6) + "px"); ticking = false; });
  }, { passive: true });
  const signs = document.querySelectorAll(".roadside,.distance");
  signs.forEach(s => s.classList.add("reveal"));
  const io = new IntersectionObserver(es => es.forEach(e => { if (e.isIntersecting) { e.target.classList.add("in"); io.unobserve(e.target); } }), { threshold: .2 });
  signs.forEach(s => io.observe(s));
})();
