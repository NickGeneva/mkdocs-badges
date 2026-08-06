(() => {
  "use strict";

  const pageData = () => window.MKDOCS_BADGES_DATA || {};

  function normalisePath(value) {
    return value.replace(/[?#].*$/, "").replace(/^\.\//, "").replace(/^\//, "")
      .replace(/index\.html$/, "").replace(/\.html$/, "/");
  }

  function badgesForLink(link) {
    const raw = link.getAttribute("href");
    if (!raw || /^(?:[a-z]+:|#)/i.test(raw)) return [];
    const data = pageData();
    const relative = normalisePath(raw);
    if (data[relative]) return data[relative];
    let path;
    try { path = normalisePath(new URL(raw, document.baseURI).pathname); }
    catch (_) { return []; }
    const keys = Object.keys(data).sort((a, b) => b.length - a.length);
    const key = keys.find((candidate) => {
      const clean = normalisePath(candidate);
      return clean && (path === clean || path.endsWith(`/${clean}`));
    });
    return key ? data[key] : [];
  }

  function directBadges(target) {
    const own = [];
    target.querySelectorAll(".mkdocs-badge[data-badge-id]").forEach((badge) => {
      if (!badge.closest(".mkdocs-badge-filter__controls")) own.push(badge.dataset.badgeId);
    });
    return [...new Set(own)];
  }

  function annotateTarget(target) {
    const direct = directBadges(target);
    if (direct.length) return direct;
    const link = target.querySelector("a[href]");
    if (!link) return [];
    const ids = badgesForLink(link);
    if (!ids.length) return [];
    const templates = document.querySelectorAll(
      ".mkdocs-badge-filter__controls .mkdocs-badge-filter__button"
    );
    const list = document.createElement("span");
    list.className = "mkdocs-badge-list";
    ids.forEach((id) => {
      const button = [...templates].find((item) => item.dataset.badgeId === id);
      const badge = button && button.querySelector(".mkdocs-badge");
      if (badge) list.appendChild(badge.cloneNode(true));
    });
    if (list.children.length) link.insertAdjacentElement("afterend", list);
    return ids;
  }

  function targetsFor(filter) {
    const content = filter.querySelector(":scope > .mkdocs-badge-filter__content");
    if (!content) return [];
    const docs = [...content.querySelectorAll(".doc-object")]
      .filter((item) => !item.parentElement.closest(".doc-object"));
    if (docs.length) return docs;
    const rows = [...content.querySelectorAll("tbody > tr")];
    if (rows.length) return rows;
    return [...content.querySelectorAll("li")]
      .filter((item) => !item.parentElement.closest("li"));
  }

  function selected(filter) {
    return [...filter.querySelectorAll(
      ".mkdocs-badge-filter__button[aria-pressed='true']"
    )].map((button) => button.dataset.badgeId);
  }

  function matches(ids, active, grouped, mode) {
    if (!active.length) return true;
    if (!grouped) {
      return mode === "or"
        ? active.some((id) => ids.includes(id))
        : active.every((id) => ids.includes(id));
    }
    const groups = new Map();
    active.forEach((id) => {
      const group = id.includes(":") ? id.split(":", 1)[0] : "";
      if (!groups.has(group)) groups.set(group, []);
      groups.get(group).push(id);
    });
    return [...groups.values()].every((members) =>
      members.some((id) => ids.includes(id))
    );
  }

  function apply(filter) {
    const active = selected(filter);
    const grouped = filter.dataset.grouped === "true";
    const mode = filter.dataset.filterMode || "and";
    filter._badgeTargets.forEach(({ element, ids }) => {
      if (matches(ids, active, grouped, mode)) {
        element.removeAttribute("data-mkdocs-badges-hidden");
      } else {
        element.setAttribute("data-mkdocs-badges-hidden", "");
      }
    });
    const clear = filter.querySelector(".mkdocs-badge-filter__clear");
    if (clear) clear.hidden = active.length === 0;
  }

  function applyOrder(filter) {
    const order = (filter.dataset.badgeOrder || "").split(",").filter(Boolean);
    if (!order.length) return;
    filter.querySelectorAll(".mkdocs-badge-filter__content .mkdocs-badge-list")
      .forEach((list) => {
        [...list.children].sort((left, right) => {
          const a = order.indexOf(left.dataset.badgeId);
          const b = order.indexOf(right.dataset.badgeId);
          return (a < 0 ? order.length : a) - (b < 0 ? order.length : b);
        }).forEach((badge) => list.appendChild(badge));
      });
  }

  function setGroupVisibility(filter, group, hidden) {
    filter.querySelectorAll(
      `.mkdocs-badge-filter__content .mkdocs-badge[data-badge-group="${CSS.escape(group)}"]`
    ).forEach((badge) => { badge.hidden = hidden; });
    const toggle = filter.querySelector(
      `.mkdocs-badge-filter__toggle[data-badge-group="${CSS.escape(group)}"]`
    );
    if (toggle) toggle.setAttribute("aria-pressed", String(hidden));
  }

  function initialise(filter) {
    if (filter.dataset.badgesReady) return;
    filter.dataset.badgesReady = "true";
    filter._badgeTargets = targetsFor(filter).map((element) => ({
      element,
      ids: annotateTarget(element),
    }));
    applyOrder(filter);
    (filter.dataset.groupsHidden || "").split(",").filter(Boolean)
      .forEach((group) => setGroupVisibility(filter, group, true));
    filter.addEventListener("click", (event) => {
      const button = event.target.closest("button");
      if (!button) return;
      if (button.classList.contains("mkdocs-badge-filter__button")) {
        button.setAttribute("aria-pressed", String(button.getAttribute("aria-pressed") !== "true"));
        apply(filter);
      } else if (button.classList.contains("mkdocs-badge-filter__clear")) {
        filter.querySelectorAll(".mkdocs-badge-filter__button")
          .forEach((item) => item.setAttribute("aria-pressed", "false"));
        apply(filter);
      } else if (button.classList.contains("mkdocs-badge-filter__toggle")) {
        setGroupVisibility(filter, button.dataset.badgeGroup, button.getAttribute("aria-pressed") !== "true");
      }
    });
  }

  function initialiseAll() {
    document.querySelectorAll(".mkdocs-badge-filter").forEach(initialise);
  }

  if (typeof document$ !== "undefined") document$.subscribe(initialiseAll);
  else if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", initialiseAll);
  else initialiseAll();
})();
