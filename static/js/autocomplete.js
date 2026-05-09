// OnePass — lightweight, fuzzy city autocomplete (no external APIs).
// Usage: add `data-autocomplete="cities"` (or "metro") to any <input>.
// Lists are exposed by templates as window.OP_CITIES and window.OP_METRO.
(function () {
  function fuzzyScore(query, candidate) {
    // Higher score = better match. 0 = no match.
    const q = query.trim().toLowerCase();
    const c = candidate.toLowerCase();
    if (!q) return 0;
    if (c === q) return 1000;                 // exact
    if (c.startsWith(q)) return 800 - c.length;  // prefix wins
    const idx = c.indexOf(q);
    if (idx >= 0) return 500 - idx - c.length;  // contains
    // tolerant: every char in query exists in candidate in order
    let i = 0;
    for (const ch of c) { if (ch === q[i]) i++; if (i === q.length) break; }
    if (i === q.length) return 100 - c.length;
    return 0;
  }

  function rank(query, list, max = 8) {
    return list
      .map(s => ({ s, score: fuzzyScore(query, s) }))
      .filter(x => x.score > 0)
      .sort((a, b) => b.score - a.score)
      .slice(0, max)
      .map(x => x.s);
  }

  function build(input) {
    const listName = input.dataset.autocomplete;
    const source = (listName === "metro" ? (window.OP_METRO || []) : (window.OP_CITIES || []));

    // Anchor the dropdown to the nearest .input-group / .col / parent so the
    // input's own layout (e.g. inside a Bootstrap input-group) stays intact.
    const anchor = input.closest(".input-group") || input.parentNode;
    if (getComputedStyle(anchor).position === "static") {
      anchor.style.position = "relative";
    }

    const dropdown = document.createElement("ul");
    dropdown.className = "op-ac-dropdown";
    anchor.appendChild(dropdown);

    let activeIdx = -1;
    let lastShown = [];

    function close() {
      dropdown.style.display = "none";
      activeIdx = -1;
    }

    function open(items) {
      lastShown = items;
      if (!items.length) { close(); return; }
      dropdown.innerHTML = items
        .map((s, i) => `<li class="op-ac-item${i === activeIdx ? ' active' : ''}" data-i="${i}">${s}</li>`)
        .join("");
      dropdown.style.display = "block";
    }

    function pick(value) {
      input.value = value;
      close();
      input.dispatchEvent(new Event("change", { bubbles: true }));
    }

    input.setAttribute("autocomplete", "off");
    input.removeAttribute("list");

    input.addEventListener("input", () => {
      const items = input.value.trim()
        ? rank(input.value, source)
        : source.slice(0, 8);  // empty input: show top 8
      activeIdx = -1;
      open(items);
    });

    input.addEventListener("focus", () => {
      const items = input.value.trim() ? rank(input.value, source) : source.slice(0, 8);
      open(items);
    });

    input.addEventListener("keydown", (e) => {
      if (dropdown.style.display === "none") return;
      if (e.key === "ArrowDown") { e.preventDefault(); activeIdx = Math.min(lastShown.length - 1, activeIdx + 1); open(lastShown); }
      else if (e.key === "ArrowUp") { e.preventDefault(); activeIdx = Math.max(0, activeIdx - 1); open(lastShown); }
      else if (e.key === "Enter") {
        if (activeIdx >= 0) { e.preventDefault(); pick(lastShown[activeIdx]); }
      } else if (e.key === "Escape") { close(); }
    });

    dropdown.addEventListener("mousedown", (e) => {
      const li = e.target.closest(".op-ac-item");
      if (!li) return;
      e.preventDefault(); // keep focus on input
      pick(lastShown[+li.dataset.i]);
    });

    document.addEventListener("click", (e) => {
      if (e.target !== input && !dropdown.contains(e.target)) close();
    });
  }

  document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll("input[data-autocomplete]").forEach(build);
  });
})();
