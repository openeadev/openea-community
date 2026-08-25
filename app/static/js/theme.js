(() => {
  const key = "openea-theme";
  const stored = localStorage.getItem(key);
  const systemDark = window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches;
  const theme = stored === "dark" || stored === "light" ? stored : (systemDark ? "dark" : "light");
  document.documentElement.setAttribute("data-bs-theme", theme);
})();
