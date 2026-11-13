/* অতঃকিম site script: sketchy frames (rough.js), search, share, zoom.
   Everything degrades gracefully: without JS the page still reads fine. */
(function () {
  "use strict";
  var doc = document.documentElement;
  doc.classList.remove("no-js");
  var ROOT = doc.getAttribute("data-root") || "";
  var COLORS = { ink: "#22303A", teal: "#2FB3A3", coral: "#E8705F", yellow: "#F4B740" };
  var BN = "০১২৩৪৫৬৭৮৯";
  function bn(n) { return String(n).replace(/[0-9]/g, function (d) { return BN[+d]; }); }

  /* ---------------- rough.js frames around HTML boxes ---------------- */
  var NS = "http://www.w3.org/2000/svg";
  function hashSeed(s) { var h = 7; for (var i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) % 2147483; return h + 1; }

  function frame(el, i) {
    if (!window.rough) return;
    var old = el.querySelector(":scope > .rough-layer");
    if (old) old.remove();
    var w = el.offsetWidth, h = el.offsetHeight;
    if (!w || !h) return;
    var spec = (el.getAttribute("data-rough") || "ink").split(" ");
    var color = COLORS[spec[0]] || spec[0] || COLORS.ink;
    var svg = document.createElementNS(NS, "svg");
    svg.setAttribute("class", "rough-layer");
    svg.setAttribute("aria-hidden", "true");
    svg.setAttribute("viewBox", "0 0 " + (w + 12) + " " + (h + 12));
    var rc = rough.svg(svg);
    var opts = { stroke: color, strokeWidth: spec.indexOf("thin") >= 0 ? 1.3 : 1.9, roughness: 1.4, bowing: 1.2, seed: hashSeed((el.id || "") + i + w) };
    if (spec.indexOf("hatch") >= 0) { opts.fill = color; opts.fillStyle = "hachure"; opts.hachureGap = 9; opts.fillWeight = .6; opts.hachureAngle = -41; }
    if (spec.indexOf("underline") >= 0) {
      svg.appendChild(rc.line(4, h + 4, w + 8, h + 2, opts));
    } else {
      var node = rc.rectangle(6, 6, w, h, opts);
      if (opts.fill) { var f = node.querySelector("path"); if (f) f.setAttribute("opacity", ".16"); }
      svg.appendChild(node);
    }
    el.insertBefore(svg, el.firstChild);
  }
  function drawFrames() {
    var els = document.querySelectorAll("[data-rough]");
    for (var i = 0; i < els.length; i++) frame(els[i], i);
  }

  /* ---------------- rough.js inside SVG graphics ----------------
     Any SVG shape with data-r gets redrawn sketchily; the crisp original is
     hidden only after the sketch is in place. Text is never sketched. */
  function roughenSvg(svg, k) {
    if (!window.rough) return;
    var rc = rough.svg(svg);
    var shapes = svg.querySelectorAll("[data-r]");
    for (var i = 0; i < shapes.length; i++) {
      var s = shapes[i], tag = s.tagName.toLowerCase(), node;
      var g = function (a, d) { var v = s.getAttribute(a); return v === null ? d : v; };
      var o = {
        stroke: g("stroke", "none"), strokeWidth: +g("stroke-width", 1.8),
        roughness: +(s.getAttribute("data-r") || 1.3), bowing: 1, seed: (k + 1) * 100 + i + 1,
        fill: g("fill", "none") === "none" ? undefined : g("fill"),
        fillStyle: g("data-fill", "hachure"), hachureGap: +g("data-gap", 7), fillWeight: +g("data-weight", 1),
        hachureAngle: +g("data-angle", -41)
      };
      if (tag === "rect") node = rc.rectangle(+g("x", 0), +g("y", 0), +g("width"), +g("height"), o);
      else if (tag === "line") node = rc.line(+g("x1"), +g("y1"), +g("x2"), +g("y2"), o);
      else if (tag === "circle") node = rc.circle(+g("cx"), +g("cy"), 2 * g("r"), o);
      else if (tag === "ellipse") node = rc.ellipse(+g("cx"), +g("cy"), 2 * g("rx"), 2 * g("ry"), o);
      else if (tag === "path") node = rc.path(g("d"), o);
      else continue;
      if (s.getAttribute("class")) node.setAttribute("class", s.getAttribute("class"));
      s.parentNode.insertBefore(node, s);
      s.style.display = "none";
    }
  }

  function start() {
    var svgs = document.querySelectorAll("svg.gfx");
    for (var i = 0; i < svgs.length; i++) roughenSvg(svgs[i], i);
    drawFrames();
    var t;
    window.addEventListener("resize", function () { clearTimeout(t); t = setTimeout(drawFrames, 150); });
    if (document.fonts && document.fonts.ready) document.fonts.ready.then(drawFrames);
  }

  /* ---------------- search ----------------
     A small client-side index (search-index.json) built with the site.
     Matching is forgiving for Bengali spelling (ী/ি, ূ/ু, শ/ষ/স, ণ/ন) and for
     Banglish typed in English letters (hotey/hote, chai/chay, ee/i ...). */
  var INDEX = null, loading = null;
  function loadIndex() {
    if (INDEX) return Promise.resolve(INDEX);
    if (!loading) loading = fetch(ROOT + "search-index.json").then(function (r) { return r.json(); }).then(function (d) {
      d.forEach(function (p) {
        p._t = fold(p.t); p._k = fold(p.k + " " + p.tags.join(" "));
        p._s = fold(p.s); p._b = fold(p.b);
      });
      INDEX = d; return d;
    });
    return loading;
  }
  function fold(s) {
    s = (s || "").normalize("NFC").toLowerCase();
    s = s.replace(/[০-৯]/g, function (d) { return String(d.charCodeAt(0) - 0x09E6); });
    s = s.replace(/ী/g, "ি").replace(/ূ/g, "ু").replace(/[শষ]/g, "স").replace(/ণ/g, "ন")
         .replace(/ৎ/g, "ত").replace(/ঁ/g, "").replace(/য়/g, "য").replace(/ড়/g, "ড").replace(/ঢ়/g, "ঢ");
    s = s.replace(/[a-z]+/g, function (w) {
      return w.replace(/ee/g, "i").replace(/oo/g, "u").replace(/ph/g, "f").replace(/([kgcjtdpbs])h/g, "$1")
              .replace(/y/g, "i").replace(/w/g, "o").replace(/z/g, "j").replace(/(.)\1+/g, "$1");
    });
    return s.replace(/[^\p{L}\p{M}\p{N}%]+/gu, " ").trim();
  }
  function has(hay, term) {
    if (hay.indexOf(term) >= 0) return true;
    if (term.length >= 4 && /^[a-z]+$/.test(term)) return hay.indexOf(term.slice(0, -1)) >= 0;
    return false;
  }
  function search(q) {
    var terms = fold(q).split(" ").filter(function (t) { return t.length > 0; });
    if (!terms.length) return [];
    var out = [];
    INDEX.forEach(function (p) {
      var score = 0, hit = 0;
      terms.forEach(function (t) {
        var s = 0;
        if (has(p._t, t)) s = 10; else if (has(p._k, t)) s = 6; else if (has(p._s, t)) s = 4; else if (has(p._b, t)) s = 1;
        if (s) { hit++; score += s; }
      });
      if (hit) out.push({ p: p, score: score + hit * 5, full: hit === terms.length || (terms.length > 2 && hit >= terms.length - 1) });
    });
    /* pages matching every word come first; if none do (a question like
       "ctet kobe dibo"), show the pages that match some of the words */
    var full = out.filter(function (r) { return r.full; });
    if (full.length) out = full;
    out.sort(function (a, b) { return b.score - a.score || (b.p.d > a.p.d ? 1 : -1); });
    return out;
  }
  function esc(s) { return s.replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); }
  function itemHtml(r) {
    return '<a href="' + ROOT + r.p.u + '"><span class="result-t">' + esc(r.p.t) + '</span><span class="result-s">' + esc(r.p.s) + "</span></a>";
  }
  function wireSearch(box) {
    var input = box.querySelector("input"), panel = box.querySelector(".search-results"), timer, active = -1;
    if (!input || !panel) return;
    function close() { panel.classList.remove("open"); active = -1; }
    function render() {
      var q = input.value.trim();
      if (!q) { close(); return; }
      loadIndex().then(function () {
        var res = search(q).slice(0, 8);
        panel.innerHTML = res.length ? res.map(itemHtml).join("")
          : '<div class="search-empty">"' + esc(q) + '" দিয়ে কিছু পেলাম না। অন্য শব্দে খোঁজো, বা ভিডিওর কমেন্টে প্রশ্নটা লেখো।</div>';
        panel.classList.add("open"); active = -1;
      });
    }
    input.addEventListener("focus", loadIndex);
    input.addEventListener("input", function () { clearTimeout(timer); timer = setTimeout(render, 120); });
    input.addEventListener("keydown", function (e) {
      var links = panel.querySelectorAll("a");
      if (e.key === "ArrowDown" || e.key === "ArrowUp") {
        if (!links.length) return;
        e.preventDefault();
        active = (active + (e.key === "ArrowDown" ? 1 : -1) + links.length) % links.length;
        links.forEach(function (a, i) { a.classList.toggle("active", i === active); });
      } else if (e.key === "Enter") {
        e.preventDefault();
        if (active >= 0 && links[active]) location.href = links[active].href;
        else if (input.value.trim()) location.href = ROOT + "search/?q=" + encodeURIComponent(input.value.trim());
      } else if (e.key === "Escape") { close(); input.blur(); }
    });
    document.addEventListener("click", function (e) { if (!box.contains(e.target)) close(); });
  }
  function searchPage() {
    var out = document.getElementById("search-page-results");
    if (!out) return;
    var q = new URLSearchParams(location.search).get("q") || "";
    var input = document.querySelector(".search input");
    if (input) input.value = q;
    var title = document.getElementById("search-q");
    if (title) title.textContent = q;
    if (!q) { out.innerHTML = ""; return; }
    loadIndex().then(function () {
      var res = search(q);
      out.innerHTML = res.length
        ? '<p class="change-note">' + bn(res.length) + "টা পাতা পাওয়া গেছে</p>" + res.map(function (r) { return '<div class="result">' + itemHtml(r) + "</div>"; }).join("")
        : '<p>কিছু পাওয়া গেল না। অন্য বানানে বা ইংরেজিতে খুঁজে দেখো। প্রশ্নটা ভিডিওর কমেন্টেও লিখতে পারো।</p>';
    });
  }

  /* ---------------- share + zoom ---------------- */
  function wireShare() {
    document.querySelectorAll("[data-copy]").forEach(function (b) {
      b.addEventListener("click", function () {
        var url = b.getAttribute("data-copy");
        var done = function () { var t = b.querySelector("span"); var old = t.textContent; t.textContent = "কপি হয়েছে ✓"; setTimeout(function () { t.textContent = old; }, 1800); };
        if (navigator.clipboard) navigator.clipboard.writeText(url).then(done, function () { prompt("লিংকটা কপি করো:", url); });
        else prompt("লিংকটা কপি করো:", url);
      });
    });
    var lb = document.createElement("div");
    lb.className = "lightbox"; lb.setAttribute("role", "dialog");
    lb.addEventListener("click", function () { lb.classList.remove("open"); lb.innerHTML = ""; });
    document.body.appendChild(lb);
    document.querySelectorAll("img.zoom").forEach(function (img) {
      img.addEventListener("click", function () {
        lb.innerHTML = '<button class="close" type="button">✕ বন্ধ</button>' +
          (window.innerWidth < 900 ? '<span class="hint">পাশে টেনে দেখো</span>' : "") +
          '<img alt="" src="' + (img.getAttribute("data-full") || img.src) + '">';
        lb.classList.add("open");
        lb.scrollLeft = 0; lb.scrollTop = 0;
      });
    });
  }

  function ready(f) { if (document.readyState !== "loading") f(); else document.addEventListener("DOMContentLoaded", f); }
  ready(function () {
    start();
    document.querySelectorAll(".search").forEach(wireSearch);
    searchPage();
    wireShare();
    /* the whole card opens its page; links inside it (tags, button) work as usual */
    document.querySelectorAll(".card[data-href]").forEach(function (c) {
      c.addEventListener("click", function (e) {
        if (e.target.closest("a, button")) return;
        location.href = c.getAttribute("data-href");
      });
    });
  });
})();
