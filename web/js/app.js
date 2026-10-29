/* ShowFinder front end: talks to the Python web layer (/api/*). */
(() => {
  "use strict";

  const elements = {
    form: document.getElementById("searchForm"),
    input: document.getElementById("searchInput"),
    searchError: document.getElementById("searchError"),
    range: document.getElementById("ratingRange"),
    rangeValue: document.getElementById("ratingValue"),
    button: document.getElementById("searchButton"),
    stats: document.getElementById("statsSection"),
    statTerm: document.getElementById("statTerm"),
    statFound: document.getElementById("statFound"),
    statMatching: document.getElementById("statMatching"),
    statAverage: document.getElementById("statAverage"),
    toolbar: document.getElementById("toolbar"),
    genreFilters: document.getElementById("genreFilters"),
    showAll: document.getElementById("showAllSwitch"),
    sort: document.getElementById("sortSelect"),
    results: document.getElementById("results"),
    empty: document.getElementById("emptyState"),
    themeToggle: document.getElementById("themeToggle"),
    toast: document.getElementById("errorToast"),
    toastMessage: document.getElementById("errorToastMessage"),
  };

  const modal = {
    instance: new bootstrap.Modal(document.getElementById("showModal")),
    title: document.getElementById("showModalTitle"),
    poster: document.getElementById("modalPoster"),
    meta: document.getElementById("modalMeta"),
    genres: document.getElementById("modalGenres"),
    summary: document.getElementById("modalSummary"),
    link: document.getElementById("modalLink"),
  };

  const errorToast = new bootstrap.Toast(elements.toast, { delay: 6000 });

  const state = {
    searchTerm: "",
    shows: [],        // every show returned by the API
    genre: null,      // active genre filter
    loaded: false,
  };

  /* ---------- Helpers ---------- */

  const escapeHtml = (value) =>
    String(value ?? "").replace(/[&<>"']/g, (ch) => ({
      "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
    })[ch]);

  const storage = {
    get(key) { try { return localStorage.getItem(key); } catch { return null; } },
    set(key, value) { try { localStorage.setItem(key, value); } catch { /* ignore */ } },
  };

  const minimumRating = () => parseFloat(elements.range.value);
  const meetsThreshold = (show) => show.rating !== null && show.rating >= minimumRating();
  const year = (show) => (show.premiered ? show.premiered.slice(0, 4) : null);

  function showError(message) {
    elements.toastMessage.textContent = message;
    errorToast.show();
  }

  /* ---------- Theme ---------- */

  function applyTheme(theme) {
    document.documentElement.setAttribute("data-bs-theme", theme);
    elements.themeToggle.innerHTML = theme === "dark"
      ? '<i class="bi bi-sun"></i>'
      : '<i class="bi bi-moon-stars"></i>';
  }

  function initTheme() {
    const saved = storage.get("sf-theme");
    const prefersLight = window.matchMedia("(prefers-color-scheme: light)").matches;
    applyTheme(saved || (prefersLight ? "light" : "dark"));
    elements.themeToggle.addEventListener("click", () => {
      const next = document.documentElement.getAttribute("data-bs-theme") === "dark" ? "light" : "dark";
      applyTheme(next);
      storage.set("sf-theme", next);
    });
  }

  /* ---------- Rendering ---------- */

  function renderSkeletons(count = 8) {
    elements.empty.hidden = true;
    elements.results.innerHTML = Array.from({ length: count }, () => `
      <div class="col-6 col-md-4 col-lg-3">
        <div class="skeleton">
          <div class="sk-poster"></div>
          <div class="sk-line"></div>
          <div class="sk-line short"></div>
        </div>
      </div>`).join("");
  }

  function renderEmpty(icon, title, text) {
    elements.results.innerHTML = "";
    elements.empty.innerHTML = `
      <div class="empty-icon"><i class="bi ${icon}"></i></div>
      <h2 class="h5 fw-bold">${escapeHtml(title)}</h2>
      <p class="text-body-secondary mb-0">${escapeHtml(text)}</p>`;
    elements.empty.hidden = false;
  }

  function renderStats() {
    const matching = state.shows.filter(meetsThreshold);
    const average = matching.length
      ? (matching.reduce((sum, show) => sum + show.rating, 0) / matching.length).toFixed(1)
      : "-";
    elements.statTerm.textContent = state.searchTerm;
    elements.statTerm.title = state.searchTerm;
    elements.statFound.textContent = state.shows.length;
    elements.statMatching.textContent = matching.length;
    elements.statAverage.textContent = average;
    elements.stats.hidden = false;
  }

  function baseShows() {
    return elements.showAll.checked ? state.shows : state.shows.filter(meetsThreshold);
  }

  function renderGenreFilters(shows) {
    const genres = [...new Set(shows.flatMap((show) => show.genres))].sort();
    if (state.genre && !genres.includes(state.genre)) state.genre = null;
    if (!genres.length) {
      elements.genreFilters.innerHTML = "";
      return;
    }
    elements.genreFilters.innerHTML = [
      `<button type="button" class="btn btn-sm chip ${state.genre ? "" : "active"}" data-genre="">All genres</button>`,
      ...genres.map((genre) =>
        `<button type="button" class="btn btn-sm chip ${state.genre === genre ? "active" : ""}" data-genre="${escapeHtml(genre)}">${escapeHtml(genre)}</button>`),
    ].join("");
  }

  function sortShows(shows) {
    const sorted = [...shows];
    switch (elements.sort.value) {
      case "rating": return sorted.sort((a, b) => (b.rating ?? -1) - (a.rating ?? -1));
      case "name": return sorted.sort((a, b) => a.name.localeCompare(b.name));
      case "newest": return sorted.sort((a, b) => (b.premiered ?? "").localeCompare(a.premiered ?? ""));
      default: return sorted; // relevance = API order
    }
  }

  function cardHtml(show, index) {
    const meets = meetsThreshold(show);
    const poster = show.image
      ? `<img src="${escapeHtml(show.image)}" alt="${escapeHtml(show.name)} poster" loading="lazy">`
      : '<div class="poster-fallback"><i class="bi bi-film"></i></div>';
    const rating = show.rating !== null
      ? `<span class="rating-badge"><i class="bi bi-star-fill"></i>${show.rating.toFixed(1)}</span>`
      : '<span class="rating-badge unrated">Unrated</span>';
    const status = show.status
      ? `<span class="status-badge ${show.status === "Running" ? "running" : ""}">${escapeHtml(show.status)}</span>`
      : "";
    const meta = [year(show), show.network].filter(Boolean).map(escapeHtml).join(" · ") || "&nbsp;";
    const genres = show.genres.slice(0, 3).map((g) => `<span class="genre-pill">${escapeHtml(g)}</span>`).join("");

    return `
      <div class="col-6 col-md-4 col-lg-3">
        <article class="show-card ${meets ? "" : "below-threshold"}" tabindex="0" role="button"
                 data-index="${state.shows.indexOf(show)}" style="animation-delay:${Math.min(index * 40, 400)}ms"
                 aria-label="${escapeHtml(show.name)} details">
          <div class="poster-wrap">${poster}${rating}${status}</div>
          <div class="show-body">
            <h3 class="show-title">${escapeHtml(show.name)}</h3>
            <div class="show-meta mb-2">${meta}</div>
            <div class="d-flex flex-wrap gap-1">${genres}</div>
          </div>
        </article>
      </div>`;
  }

  function renderResults() {
    if (!state.loaded) return;
    renderStats();
    elements.toolbar.hidden = state.shows.length === 0;

    if (state.shows.length === 0) {
      renderEmpty("bi-search", "No results were returned",
        `TVMaze has no shows matching “${state.searchTerm}”. Try a different search term.`);
      return;
    }

    const base = baseShows();
    renderGenreFilters(base);
    const visible = sortShows(state.genre ? base.filter((s) => s.genres.includes(state.genre)) : base);

    if (visible.length === 0) {
      renderEmpty("bi-star", "No shows met the minimum rating",
        `Lower the rating below ${minimumRating().toFixed(1)} or switch on “Show all results”.`);
      return;
    }

    elements.empty.hidden = true;
    elements.results.innerHTML = visible.map(cardHtml).join("");
  }

  function openModal(show) {
    modal.title.textContent = show.name;
    if (show.image) {
      modal.poster.src = show.image.replace("medium_portrait", "original_untouched");
      modal.poster.alt = `${show.name} poster`;
      modal.poster.hidden = false;
    } else {
      modal.poster.hidden = true;
    }
    const metaItems = [
      show.rating !== null ? `<i class="bi bi-star-fill"></i>${show.rating.toFixed(1)}` : "Unrated",
      year(show) && `<i class="bi bi-calendar3"></i>${escapeHtml(year(show))}`,
      show.network && `<i class="bi bi-broadcast"></i>${escapeHtml(show.network)}`,
      show.status && `<i class="bi bi-info-circle"></i>${escapeHtml(show.status)}`,
    ].filter(Boolean);
    modal.meta.innerHTML = metaItems.map((item) => `<span class="meta-pill">${item}</span>`).join("");
    modal.genres.innerHTML = show.genres.map((g) => `<span class="genre-pill">${escapeHtml(g)}</span>`).join("");
    modal.summary.textContent = show.summary || "No summary available.";
    modal.link.hidden = !show.url;
    if (show.url) modal.link.href = show.url;
    modal.instance.show();
  }

  /* ---------- Data ---------- */

  function setLoading(isLoading) {
    elements.button.disabled = isLoading;
    elements.button.querySelector(".spinner-border").classList.toggle("d-none", !isLoading);
    elements.button.querySelector(".btn-label").classList.toggle("d-none", isLoading);
  }

  async function search(term) {
    const searchTerm = term.trim();
    if (!searchTerm) {
      elements.searchError.hidden = false;
      elements.input.classList.add("is-invalid");
      elements.input.focus();
      return;
    }
    elements.searchError.hidden = true;
    elements.input.classList.remove("is-invalid");

    setLoading(true);
    renderSkeletons();
    const params = new URLSearchParams({ q: searchTerm, min_rating: minimumRating() });
    history.replaceState(null, "", `?${params}`);

    try {
      const response = await fetch(`/api/search?${params}`);
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || "Search failed.");
      state.searchTerm = data.search_term;
      state.shows = data.shows;
      state.genre = null;
      state.loaded = true;
      renderResults();
    } catch (error) {
      state.loaded = false;
      elements.stats.hidden = true;
      elements.toolbar.hidden = true;
      renderEmpty("bi-wifi-off", "Something went wrong", error.message);
      showError(error.message);
    } finally {
      setLoading(false);
    }
  }

  async function loadDefaults() {
    const params = new URLSearchParams(location.search);
    if (params.has("q")) {
      elements.input.value = params.get("q");
      if (params.has("min_rating")) elements.range.value = params.get("min_rating");
      updateRangeLabel();
      search(elements.input.value);
      return;
    }
    try {
      const response = await fetch("/api/config");
      const config = await response.json();
      elements.input.value = config.search_term || "";
      elements.range.value = config.minimum_rating ?? 8;
    } catch {
      /* keep the built-in defaults */
    }
    updateRangeLabel();
  }

  /* ---------- Events ---------- */

  function updateRangeLabel() {
    elements.rangeValue.textContent = minimumRating().toFixed(1);
  }

  elements.form.addEventListener("submit", (event) => {
    event.preventDefault();
    search(elements.input.value);
  });

  elements.input.addEventListener("input", () => {
    elements.searchError.hidden = true;
    elements.input.classList.remove("is-invalid");
  });

  // The rating filter is applied instantly in the browser, so no new API call is needed.
  elements.range.addEventListener("input", () => {
    updateRangeLabel();
    renderResults();
  });

  document.querySelectorAll(".quick-search").forEach((button) =>
    button.addEventListener("click", () => {
      elements.input.value = button.textContent.trim();
      search(elements.input.value);
    }));

  elements.genreFilters.addEventListener("click", (event) => {
    const chip = event.target.closest("[data-genre]");
    if (!chip) return;
    state.genre = chip.dataset.genre || null;
    renderResults();
  });

  elements.showAll.addEventListener("change", renderResults);
  elements.sort.addEventListener("change", renderResults);

  elements.results.addEventListener("click", (event) => {
    const card = event.target.closest(".show-card");
    if (card) openModal(state.shows[Number(card.dataset.index)]);
  });
  elements.results.addEventListener("keydown", (event) => {
    const card = event.target.closest(".show-card");
    if (card && (event.key === "Enter" || event.key === " ")) {
      event.preventDefault();
      openModal(state.shows[Number(card.dataset.index)]);
    }
  });

  // Press "/" anywhere to jump to the search box.
  document.addEventListener("keydown", (event) => {
    if (event.key === "/" && document.activeElement.tagName !== "INPUT") {
      event.preventDefault();
      elements.input.focus();
      elements.input.select();
    }
  });

  initTheme();
  loadDefaults();
})();
