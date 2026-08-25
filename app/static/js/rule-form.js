(function () {
  "use strict";
  const select = document.getElementById("ruleType");
  if (!select) return;
  function update() {
    const value = select.value;
    document.querySelectorAll(".rule-fields").forEach(function (node) {
      const allowed = (node.dataset.types || "").split(" ");
      node.style.display = allowed.includes(value) ? "" : "none";
    });
  }
  select.addEventListener("change", update);
  update();
})();
