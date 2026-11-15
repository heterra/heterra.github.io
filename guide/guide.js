// Heterra guide: the contents bar, the previous and next links and the full-size view of a picture.
// One list holds the whole guide, so every page shows the same contents. A page says where it is with
// <body data-page="opgd" data-base="../"> (data-base: the way from the page to the site's root).
(function () {
  var parts = [
    { name: "Part 1", title: "Heterra", cls: "data", pages: [
      { id: "start", file: "guide.html", title: "Getting started with Heterra" } ] },
    { name: "Part 2", title: "Spatial heterogeneity", cls: "heterogeneity", pages: [
      { id: "opgd", abbr: "OPGD", title: "Optimal parameters-based geographical detector" },
      { id: "lisp", abbr: "LISP", title: "Local indicator of stratified power" } ] },
    { name: "Part 3", title: "Spatial pattern", cls: "pattern", pages: [
      { id: "gc", abbr: "GC", title: "Geocomplexity" },
      { id: "sda", abbr: "SDA", title: "Second dimension of spatial association" },
      { id: "sdo", abbr: "SDO", title: "Second-dimension outliers" } ] },
    { name: "Part 4", title: "Spatial prediction", cls: "prediction", pages: [
      { id: "gcf", abbr: "GCF", title: "Generalized covariate field" },
      { id: "gos", abbr: "GOS", title: "Geographically optimal similarity" } ] },
    { name: "Part 5", title: "Model evaluation", cls: "evaluation", pages: [
      { id: "dsi", abbr: "DSI", title: "Degree of spatial interpretability" },
      { id: "sie", abbr: "SIE", title: "Spatial information explained" } ] }
  ];
  var body = document.body, base = body.getAttribute("data-base") || "", here = body.getAttribute("data-page");
  function href(p) { return base + (p.file || "guide/" + p.id + ".html"); }
  function esc(s) { return s.replace(/&/g, "&amp;").replace(/</g, "&lt;"); }

  var flat = [], chapter = 0;
  parts.forEach(function (part) {
    part.pages.forEach(function (p) { p.part = part; if (p.abbr) p.chapter = ++chapter; flat.push(p); });
  });

  // the contents bar; the page shown lists its own sections (its h2 with an id)
  var side = document.querySelector(".side");
  if (side) {
    var html = '<button type="button" class="side-toggle">Contents</button><div class="side-body">';
    parts.forEach(function (part) {
      html += '<p class="part">' + part.name + " · " + esc(part.title) + "</p><ul>";
      part.pages.forEach(function (p) {
        var label = p.abbr ? "<abbr>" + p.abbr + "</abbr> " + esc(p.title) : esc(p.title);
        html += '<li><a href="' + href(p) + '"' + (p.id === here ? ' class="current"' : "") + ">" + label + "</a>";
        if (p.id === here) {
          var heads = document.querySelectorAll(".page h2[id]");
          if (heads.length) {
            html += "<ul>";
            Array.prototype.forEach.call(heads, function (h) {
              html += '<li><a href="#' + h.id + '">' + esc(h.getAttribute("data-nav") || h.textContent) + "</a></li>";
            });
            html += "</ul>";
          }
        }
        html += "</li>";
      });
      html += "</ul>";
    });
    side.innerHTML = html + "</div>";
    side.querySelector(".side-toggle").addEventListener("click", function () { side.classList.toggle("open"); });
    var cur = side.querySelector("a.current");
    if (cur && cur.scrollIntoView && side.scrollHeight > side.clientHeight) cur.scrollIntoView({ block: "center" });

    // the section being read
    var links = side.querySelectorAll("ul ul a");
    if (links.length && "IntersectionObserver" in window) {
      var seen = new IntersectionObserver(function (entries) {
        entries.forEach(function (e) {
          if (!e.isIntersecting) return;
          Array.prototype.forEach.call(links, function (a) { a.classList.toggle("on", a.getAttribute("href") === "#" + e.target.id); });
        });
      }, { rootMargin: "-80px 0px -70% 0px" });
      Array.prototype.forEach.call(document.querySelectorAll(".page h2[id]"), function (h) { seen.observe(h); });
    }
  }

  // previous and next
  var pager = document.querySelector(".pager");
  if (pager) {
    var i = flat.findIndex(function (p) { return p.id === here; });
    function link(p, word) {
      if (!p) return "<span></span>";
      return '<a href="' + href(p) + '"><small>' + word + "</small>" + (p.abbr ? "Chapter " + p.chapter + " · " + p.abbr : esc(p.title)) + "</a>";
    }
    pager.innerHTML = link(flat[i - 1], "Previous") + link(flat[i + 1], "Next");
  }

  // a click on a picture shows it at full size
  var viewer = document.querySelector("dialog.viewer");
  if (viewer && viewer.showModal) {
    var big = viewer.querySelector("img");
    document.addEventListener("click", function (e) {
      var t = e.target;
      if (t.tagName === "IMG" && t.closest(".page figure, .steps")) { big.src = t.src; big.alt = t.alt; viewer.showModal(); }
      else if (t === viewer || t === big) viewer.close();
    });
  }
})();
