(() => {
  const themeKey = "openea-theme";

  const renderIcons = () => {
    if (window.lucide) window.lucide.createIcons();
  };

  const updateThemeButtons = () => {
    const dark = document.documentElement.getAttribute("data-bs-theme") === "dark";
    document.querySelectorAll(".js-theme-toggle").forEach((button) => {
      button.setAttribute("aria-label", dark ? "Switch to light theme" : "Switch to dark theme");
      button.setAttribute("title", dark ? "Switch to light theme" : "Switch to dark theme");
      const icon = button.querySelector("[data-lucide]");
      if (icon) icon.setAttribute("data-lucide", dark ? "sun" : "moon");
    });
    renderIcons();
  };

  document.querySelectorAll(".js-theme-toggle").forEach((button) => {
    button.addEventListener("click", () => {
      const current = document.documentElement.getAttribute("data-bs-theme") || "light";
      const next = current === "dark" ? "light" : "dark";
      document.documentElement.setAttribute("data-bs-theme", next);
      localStorage.setItem(themeKey, next);
      updateThemeButtons();
    });
  });

  updateThemeButtons();
})();
