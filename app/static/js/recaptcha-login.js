(() => {
  const containerId = "openea-recaptcha";
  const errorId = "openea-recaptcha-error";

  const showError = () => {
    const error = document.getElementById(errorId);
    if (error) error.classList.remove("d-none");
  };

  window.openeaRecaptchaOnError = showError;
  window.openeaRecaptchaOnload = () => {
    const container = document.getElementById(containerId);
    if (!container || !window.grecaptcha) return;

    const sitekey = container.dataset.sitekey;
    if (!sitekey) {
      showError();
      return;
    }

    const theme =
      document.documentElement.getAttribute("data-bs-theme") === "dark" ? "dark" : "light";

    window.grecaptcha.render(container, {
      sitekey,
      theme,
      "error-callback": window.openeaRecaptchaOnError,
    });
  };
})();
