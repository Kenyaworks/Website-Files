/* Kenya Works site search.
   Fuse.js over a Hugo-generated /index.json. The index is fetched lazily on
   first use, so it costs nothing until someone actually searches. */
(function () {
  "use strict";

  var GROUP_ORDER = ["Our Work", "Challenges", "Stories", "Pages"];
  var MAX_PER_GROUP = 5;
  var MAX_TOTAL = 20;

  var fuse = null;
  var loading = null;

  function loadIndex() {
    if (loading) return loading;
    loading = fetch(window.KW_SEARCH_INDEX || "/index.json")
      .then(function (r) {
        if (!r.ok) throw new Error("index " + r.status);
        return r.json();
      })
      .then(function (data) {
        fuse = new Fuse(data, {
          includeScore: true,
          ignoreLocation: true,
          threshold: 0.38,
          minMatchCharLength: 2,
          keys: [
            { name: "t", weight: 0.5 },
            { name: "s", weight: 0.25 },
            { name: "k", weight: 0.15 },
            { name: "b", weight: 0.1 },
          ],
        });
        return fuse;
      });
    return loading;
  }

  function esc(s) {
    return String(s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }

  /* Bold the query terms inside a snippet, on escaped text only. */
  function highlight(text, query) {
    var out = esc(text);
    var terms = query.split(/\s+/).filter(function (t) {
      return t.length > 1;
    });
    terms.forEach(function (t) {
      var re = new RegExp("(" + t.replace(/[.*+?^${}()|[\]\\]/g, "\\$&") + ")", "gi");
      out = out.replace(re, "<mark>$1</mark>");
    });
    return out;
  }

  /* Prefer a snippet from the body that actually contains the query. */
  function snippet(item, query) {
    var first = query.split(/\s+/)[0] || "";
    var body = item.b || "";
    var at = first.length > 1 ? body.toLowerCase().indexOf(first.toLowerCase()) : -1;
    if (at > -1) {
      var start = Math.max(0, at - 60);
      var text = body.slice(start, start + 180);
      return (start > 0 ? "…" : "") + text + (start + 180 < body.length ? "…" : "");
    }
    return item.s || body.slice(0, 160) + (body.length > 160 ? "…" : "");
  }

  function groupResults(results) {
    var counts = {};
    var buckets = {};
    var total = 0;
    results.forEach(function (r) {
      var g = r.item.g || "Pages";
      counts[g] = counts[g] || 0;
      if (counts[g] >= MAX_PER_GROUP || total >= MAX_TOTAL) return;
      counts[g]++;
      total++;
      (buckets[g] = buckets[g] || []).push(r.item);
    });
    return buckets;
  }

  function render(container, query) {
    if (!query || query.trim().length < 2) {
      container.innerHTML =
        '<p class="kw-search-hint">Type at least two characters to search ' +
        "our programs, challenges, and stories.</p>";
      return;
    }
    if (!fuse) {
      container.innerHTML = '<p class="kw-search-hint">Loading…</p>';
      return;
    }

    var q = query.trim();
    var buckets = groupResults(fuse.search(q));
    var groups = GROUP_ORDER.filter(function (g) {
      return buckets[g] && buckets[g].length;
    });

    if (!groups.length) {
      container.innerHTML =
        '<p class="kw-search-hint">No results for <strong>' +
        esc(q) +
        "</strong>. Try a broader term like “school”, “shelter”, or “pads”.</p>";
      return;
    }

    var html = "";
    groups.forEach(function (g) {
      html += '<div class="kw-search-group"><h3>' + esc(g) + "</h3><ul>";
      buckets[g].forEach(function (item) {
        html +=
          '<li><a href="' +
          esc(item.u) +
          '" class="kw-result">' +
          '<span class="kw-result-title">' +
          highlight(item.t, q) +
          (item.d ? ' <span class="kw-result-year">' + esc(item.d) + "</span>" : "") +
          "</span>" +
          '<span class="kw-result-snip">' +
          highlight(snippet(item, q), q) +
          "</span></a></li>";
      });
      html += "</ul></div>";
    });
    container.innerHTML = html;
  }

  function debounce(fn, ms) {
    var t;
    return function () {
      var args = arguments;
      clearTimeout(t);
      t = setTimeout(function () {
        fn.apply(null, args);
      }, ms);
    };
  }

  /* Roving selection across whatever result links are currently rendered. */
  function wireKeyboardNav(input, container) {
    input.addEventListener("keydown", function (e) {
      var links = Array.prototype.slice.call(container.querySelectorAll("a.kw-result"));
      if (!links.length) return;
      var cur = links.indexOf(container.querySelector("a.kw-result.is-active"));
      var next = null;
      if (e.key === "ArrowDown") next = cur < links.length - 1 ? cur + 1 : 0;
      else if (e.key === "ArrowUp") next = cur > 0 ? cur - 1 : links.length - 1;
      else if (e.key === "Enter" && cur > -1) {
        e.preventDefault();
        links[cur].click();
        return;
      } else return;

      e.preventDefault();
      links.forEach(function (l) {
        l.classList.remove("is-active");
      });
      links[next].classList.add("is-active");
      links[next].scrollIntoView({ block: "nearest" });
    });
  }

  /* ── Modal (site-wide, opened from the header) ──────────────── */
  function initModal() {
    var modal = document.getElementById("kw-search-modal");
    if (!modal) return;
    var input = modal.querySelector("input");
    var results = modal.querySelector(".kw-search-results");
    var lastFocus = null;

    var update = debounce(function () {
      render(results, input.value);
    }, 120);

    function open() {
      lastFocus = document.activeElement;
      modal.classList.add("open");
      document.body.style.overflow = "hidden";
      input.focus();
      input.select();
      loadIndex().then(function () {
        render(results, input.value);
      });
    }

    function close() {
      modal.classList.remove("open");
      document.body.style.overflow = "";
      if (lastFocus) lastFocus.focus();
    }

    document.querySelectorAll("[data-kw-search-open]").forEach(function (b) {
      b.addEventListener("click", function (e) {
        e.preventDefault();
        open();
      });
    });

    modal.querySelector("[data-kw-search-close]").addEventListener("click", close);
    modal.addEventListener("mousedown", function (e) {
      if (e.target === modal) close();
    });

    input.addEventListener("input", update);
    wireKeyboardNav(input, results);

    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && modal.classList.contains("open")) {
        close();
        return;
      }
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        modal.classList.contains("open") ? close() : open();
        return;
      }
      /* "/" opens search, but not while the user is typing in a field. */
      if (e.key === "/" && !modal.classList.contains("open")) {
        var tag = (e.target.tagName || "").toLowerCase();
        if (tag === "input" || tag === "textarea" || e.target.isContentEditable) return;
        e.preventDefault();
        open();
      }
    });
  }

  /* ── Standalone /search/ page ───────────────────────────────── */
  function initPage() {
    var root = document.getElementById("kw-search-page");
    if (!root) return;
    var input = root.querySelector("input");
    var results = root.querySelector(".kw-search-results");

    var update = debounce(function () {
      render(results, input.value);
      var u = new URL(window.location);
      if (input.value) u.searchParams.set("q", input.value);
      else u.searchParams.delete("q");
      window.history.replaceState({}, "", u);
    }, 150);

    input.addEventListener("input", update);
    wireKeyboardNav(input, results);

    var q = new URLSearchParams(window.location.search).get("q");
    if (q) input.value = q;
    input.focus();
    loadIndex().then(function () {
      render(results, input.value);
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", function () {
      initModal();
      initPage();
    });
  } else {
    initModal();
    initPage();
  }
})();
