(() => {
  const relationship = document.getElementById("relationship_choice");
  const target = document.getElementById("target_object_id");
  const targetUrl = target?.dataset.targetUrl;
  let requestController = null;

  if (!relationship || !target || !targetUrl) return;

  const syncPropertyGroups = () => {
    const relationshipKey = (relationship.value || "").split("|", 1)[0];

    document.querySelectorAll(".relationship-properties").forEach((group) => {
      const active = group.dataset.relKey === relationshipKey;
      group.hidden = !active;
      group.querySelectorAll("input, select, textarea").forEach((field) => {
        field.disabled = !active;
      });
    });
  };

  const setTargetPlaceholder = (label, disabled = true) => {
    target.replaceChildren(new Option(label, ""));
    target.disabled = disabled;
  };

  const loadTargets = async () => {
    const choice = relationship.value;
    syncPropertyGroups();

    if (!choice) {
      requestController?.abort();
      setTargetPlaceholder("Choose a relationship type first…");
      return;
    }

    requestController?.abort();
    requestController = new AbortController();
    setTargetPlaceholder("Loading targets…");

    try {
      const url = new URL(targetUrl, window.location.origin);
      url.searchParams.set("relationship_choice", choice);
      const response = await fetch(url, {
        headers: { Accept: "application/json" },
        signal: requestController.signal,
      });

      if (!response.ok) throw new Error(`HTTP ${response.status}`);

      const payload = await response.json();
      target.replaceChildren(new Option("Choose target…", ""));

      for (const item of payload.items || []) {
        target.add(new Option(item.name, item.id));
      }

      target.disabled = false;
    } catch (error) {
      if (error.name === "AbortError") return;
      console.error("Unable to load relationship targets", error);
      setTargetPlaceholder("Unable to load valid targets");
    }
  };

  relationship.addEventListener("change", loadTargets);
  syncPropertyGroups();
})();
