const state = {
  index: [],
  byHeadword: new Map(),
  byNormalizedHeadword: new Map(),
  bucketCache: new Map(),
  ready: false,
};

const searchForm = document.querySelector("#search-form");
const searchInput = document.querySelector("#search-input");
const searchResults = document.querySelector("#search-results");
const searchHint = document.querySelector("#search-hint");
const statusText = document.querySelector("#status-text");
const cardView = document.querySelector("#card-view");
const emptyState = document.querySelector("#empty-state");

const MAX_RESULTS = 12;

function normalizeLookup(text) {
  return text.trim().toLowerCase().replace(/\s+/g, " ");
}

function escapeHtml(text) {
  return text
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");
}

function setStatus(message) {
  statusText.textContent = message;
}

function uniqueByHeadword(records) {
  const seen = new Set();
  return records.filter((record) => {
    if (seen.has(record.headword)) {
      return false;
    }
    seen.add(record.headword);
    return true;
  });
}

function findMatches(rawQuery) {
  const query = normalizeLookup(rawQuery);
  if (!query) {
    return [];
  }

  const exactHeadword = [];
  const exactAlias = [];
  const prefixHeadword = [];
  const prefixAlias = [];
  const contains = [];

  for (const record of state.index) {
    const headwordKey = normalizeLookup(record.headword);
    const termSet = record.terms || [];

    if (headwordKey === query) {
      exactHeadword.push(record);
      continue;
    }

    if (termSet.includes(query)) {
      exactAlias.push(record);
      continue;
    }

    if (headwordKey.startsWith(query)) {
      prefixHeadword.push(record);
      continue;
    }

    if (termSet.some((term) => term.startsWith(query))) {
      prefixAlias.push(record);
      continue;
    }

    if (headwordKey.includes(query)) {
      contains.push(record);
    }
  }

  return uniqueByHeadword([
    ...exactHeadword,
    ...exactAlias,
    ...prefixHeadword,
    ...prefixAlias,
    ...contains,
  ]).slice(0, MAX_RESULTS);
}

function bestMatchFor(query, matches) {
  const normalized = normalizeLookup(query);
  return (
    matches.find((record) => normalizeLookup(record.headword) === normalized) ||
    matches.find((record) => (record.terms || []).includes(normalized)) ||
    matches[0] ||
    null
  );
}

function renderSuggestions(matches) {
  if (!matches.length) {
    searchResults.hidden = true;
    searchResults.innerHTML = "";
    return;
  }

  searchResults.innerHTML = matches
    .map((record) => {
      return `
        <li>
          <button type="button" data-headword="${escapeHtml(record.headword)}">
            <strong>${escapeHtml(record.headword)}</strong>
          </button>
        </li>
      `;
    })
    .join("");
  searchResults.hidden = false;
}

async function loadBucket(bucket) {
  if (state.bucketCache.has(bucket)) {
    return state.bucketCache.get(bucket);
  }

  const response = await fetch(`./data/entries/${bucket}.json`);
  if (!response.ok) {
    throw new Error(`Failed to load bucket ${bucket}`);
  }

  const payload = await response.json();
  const entries = payload.entries || {};
  state.bucketCache.set(bucket, entries);
  return entries;
}

function resolveRecord(query) {
  const direct = state.byHeadword.get(query);
  if (direct) {
    return direct;
  }

  const normalized = normalizeLookup(query);
  return (
    state.byNormalizedHeadword.get(normalized) ||
    state.index.find((record) => (record.terms || []).includes(normalized)) ||
    null
  );
}

function showEmptyState() {
  cardView.hidden = true;
  cardView.innerHTML = "";
  emptyState.hidden = false;
}

async function showEntry(query, options = {}) {
  const { updateHash = true } = options;
  const record = resolveRecord(query);

  if (!record) {
    showEmptyState();
    setStatus(`No entry found for “${query}”.`);
    return;
  }

  const entries = await loadBucket(record.bucket);
  const entry = entries[record.headword];
  if (!entry) {
    throw new Error(`Entry ${record.headword} missing from bucket ${record.bucket}`);
  }

  emptyState.hidden = true;
  cardView.hidden = false;
  cardView.innerHTML = entry.html;
  setStatus(`Showing “${record.headword}”.`);
  searchInput.value = record.headword;
  renderSuggestions([]);
  document.title = `${record.headword} — Yudakhin Dictionary`;

  if (updateHash) {
    const nextHash = `#${encodeURIComponent(record.headword)}`;
    if (window.location.hash !== nextHash) {
      history.replaceState(null, "", nextHash);
    }
  }
}

async function loadIndex() {
  const response = await fetch("./data/index.json");
  if (!response.ok) {
    throw new Error("Failed to load dictionary index");
  }

  const payload = await response.json();
  state.index = payload.entries || [];
  for (const record of state.index) {
    state.byHeadword.set(record.headword, record);
    state.byNormalizedHeadword.set(normalizeLookup(record.headword), record);
  }
  state.ready = true;

  setStatus(`${payload.count || state.index.length} entries ready.`);
  if (searchHint) {
    searchHint.textContent =
      "Type a headword, synonym, or alternative form. Matching cards are loaded on demand.";
  }
}

function syncFromHash() {
  const hash = window.location.hash.slice(1);
  if (!hash) {
    return;
  }

  const decoded = decodeURIComponent(hash);
  showEntry(decoded, { updateHash: false }).catch((error) => {
    console.error(error);
    setStatus("Failed to load the requested entry.");
  });
}

searchForm.addEventListener("submit", (event) => {
  event.preventDefault();
  if (!state.ready) {
    return;
  }

  const query = searchInput.value;
  const matches = findMatches(query);
  const record = bestMatchFor(query, matches);
  if (!record) {
    showEmptyState();
    setStatus(`No entry found for “${query}”.`);
    renderSuggestions([]);
    return;
  }

  showEntry(record.headword).catch((error) => {
    console.error(error);
    setStatus("Failed to load the selected entry.");
  });
});

searchInput.addEventListener("input", () => {
  if (!state.ready) {
    return;
  }
  renderSuggestions(findMatches(searchInput.value));
});

searchResults.addEventListener("click", (event) => {
  const button = event.target.closest("button[data-headword]");
  if (!button) {
    return;
  }

  showEntry(button.dataset.headword).catch((error) => {
    console.error(error);
    setStatus("Failed to load the selected entry.");
  });
});

cardView.addEventListener("click", (event) => {
  const link = event.target.closest("a.wordLink[data-headword]");
  if (!link) {
    return;
  }

  event.preventDefault();
  const target = link.dataset.headword;
  if (!target) {
    return;
  }

  showEntry(target).catch((error) => {
    console.error(error);
    setStatus("Failed to follow the cross-reference.");
  });
});

window.addEventListener("hashchange", syncFromHash);

loadIndex()
  .then(() => {
    syncFromHash();
  })
  .catch((error) => {
    console.error(error);
    setStatus("Failed to load the dictionary index.");
  });
