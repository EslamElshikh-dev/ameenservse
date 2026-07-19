(() => {
  "use strict";

  const header = document.querySelector(".site-header");
  const menuButton = document.querySelector(".menu-toggle");
  const navigation = document.querySelector(".primary-nav");
  const navigationLinks = [...document.querySelectorAll('.primary-nav a[href^="#"]')];
  const sectionLinks = navigationLinks
    .map((link) => ({ link, section: document.querySelector(link.getAttribute("href")) }))
    .filter(({ section }) => section);

  const setMenuState = (isOpen) => {
    if (!menuButton || !navigation) return;

    menuButton.setAttribute("aria-expanded", String(isOpen));
    menuButton.setAttribute("aria-label", isOpen ? "إغلاق القائمة" : "فتح القائمة");
    navigation.classList.toggle("is-open", isOpen);
    document.body.classList.toggle("menu-open", isOpen);
  };

  menuButton?.addEventListener("click", () => {
    setMenuState(menuButton.getAttribute("aria-expanded") !== "true");
  });

  navigationLinks.forEach((link) => {
    link.addEventListener("click", () => setMenuState(false));
  });

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") setMenuState(false);
  });

  document.addEventListener("click", (event) => {
    if (!navigation?.classList.contains("is-open")) return;
    if (navigation.contains(event.target) || menuButton?.contains(event.target)) return;
    setMenuState(false);
  });

  const updateHeader = () => {
    header?.classList.toggle("is-scrolled", window.scrollY > 10);
  };

  updateHeader();
  window.addEventListener("scroll", updateHeader, { passive: true });

  if ("IntersectionObserver" in window && sectionLinks.length) {
    const observer = new IntersectionObserver(
      (entries) => {
        const visible = entries
          .filter((entry) => entry.isIntersecting)
          .sort((a, b) => b.intersectionRatio - a.intersectionRatio)[0];

        if (!visible) return;

        sectionLinks.forEach(({ link, section }) => {
          const active = section === visible.target;
          link.classList.toggle("is-active", active);
          if (active) link.setAttribute("aria-current", "location");
          else link.removeAttribute("aria-current");
        });
      },
      {
        rootMargin: "-28% 0px -58% 0px",
        threshold: [0, 0.08, 0.2]
      }
    );

    sectionLinks.forEach(({ section }) => observer.observe(section));
  }

  const detailsItems = [...document.querySelectorAll(".accordion details")];
  detailsItems.forEach((item) => {
    item.addEventListener("toggle", () => {
      if (!item.open) return;
      detailsItems.forEach((otherItem) => {
        if (otherItem !== item) otherItem.open = false;
      });
    });
  });

  const year = document.querySelector("#current-year");
  if (year) year.textContent = String(new Date().getFullYear());

  const desktopMedia = window.matchMedia("(min-width: 921px)");
  const closeMenuOnDesktop = (event) => {
    if (event.matches) setMenuState(false);
  };

  desktopMedia.addEventListener?.("change", closeMenuOnDesktop);
})();
