(() => {
  const container = document.getElementById("impact-graph");
  const payloadNode = document.getElementById("impact-graph-data");
  if (!container || !payloadNode || !window.cytoscape) return;

  const getThemeColors = () => {
    const dark =
      document.documentElement.getAttribute("data-bs-theme") === "dark";

    return dark
      ? {
          text: "#f8f9fa",
          edgeLabelBackground: "#1e293b",
        }
      : {
          text: "#212529",
          edgeLabelBackground: "#ffffff",
        };
  };

  const payload = JSON.parse(payloadNode.textContent || "{}");
  const themeColors = getThemeColors();

  const cy = window.cytoscape({
    container,
    elements: [...(payload.nodes || []), ...(payload.edges || [])],
    layout: {
      name: "breadthfirst",
      directed: true,
      roots:
        payload.nodes
          ?.filter((n) => n.data.root)
          .map((n) => n.data.id) || [],
      padding: 30,
      spacingFactor: 1.4,
    },
    style: [
      {
        selector: "node",
        style: {
          label: "data(label)",
          "font-size": 11,
          "text-wrap": "wrap",
          "text-max-width": 110,
          "background-color": "#6c757d",
          color: themeColors.text,
          "text-valign": "bottom",
          "text-margin-y": 8,
          width: 34,
          height: 34,
        },
      },
      {
        selector: "node[root]",
        style: {
          "background-color": "#0d6efd",
          width: 46,
          height: 46,
          "font-weight": 700,
        },
      },
      {
        selector: "edge",
        style: {
          "curve-style": "bezier",
          "target-arrow-shape": "triangle",
          width: 1.5,
          "line-color": "#adb5bd",
          "target-arrow-color": "#adb5bd",
          label: "data(label)",
          "font-size": 9,
          color: themeColors.text,
          "text-background-color": themeColors.edgeLabelBackground,
          "text-background-opacity": 0.85,
          "text-background-padding": 2,
        },
      },
    ],
  });

  const applyTheme = () => {
    const colors = getThemeColors();

    cy.nodes().style("color", colors.text);

    cy.edges().style({
      color: colors.text,
      "text-background-color": colors.edgeLabelBackground,
    });
  };

  const themeObserver = new MutationObserver((mutations) => {
    if (
      mutations.some(
        (mutation) =>
          mutation.type === "attributes" &&
          mutation.attributeName === "data-bs-theme"
      )
    ) {
      applyTheme();
    }
  });

  themeObserver.observe(document.documentElement, {
    attributes: true,
    attributeFilter: ["data-bs-theme"],
  });

  cy.on("tap", "node", (event) => {
    const url = event.target.data("url");
    if (url) window.location.assign(url);
  });
})();