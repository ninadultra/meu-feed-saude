/* ============================================================
   app.js  –  Feed de Artigos Personalizados
   ============================================================ */

"use strict";

// ── Estado global ────────────────────────────────────────────
const state = {
  articles:     [],   // todos os artigos carregados
  topics:       [],   // temas (do config, inferidos do JSON)
  topicMeta:    {},   // { nome: { color, icon } }
  activeTopic:  "all",
  searchQuery:  "",
};

// ── Elementos do DOM ─────────────────────────────────────────
const $ = (id) => document.getElementById(id);
const el = {
  loading:      $("state-loading"),
  error:        $("state-error"),
  empty:        $("state-empty"),
  grid:         $("articles-grid"),
  filters:      $("topic-filters"),
  search:       $("search-input"),
  themeToggle:  $("theme-toggle"),
  statTotal:    $("stat-total"),
  statUpdated:  $("stat-updated"),
  statNew:      $("stat-new"),
  modal:        $("article-modal"),
  modalContent: $("modal-content"),
  modalClose:   $("modal-close"),
};

// ── Formatação de datas ──────────────────────────────────────
const rtf = new Intl.RelativeTimeFormat("pt-BR", { numeric: "auto" });

function relativeDate(isoStr) {
  const now  = Date.now();
  const then = new Date(isoStr).getTime();
  const diff = (then - now) / 1000; // em segundos

  const abs = Math.abs(diff);
  if (abs < 3600)   return rtf.format(Math.round(diff / 60),   "minute");
  if (abs < 86400)  return rtf.format(Math.round(diff / 3600), "hour");
  if (abs < 604800) return rtf.format(Math.round(diff / 86400),"day");

  return new Date(isoStr).toLocaleDateString("pt-BR", {
    day: "2-digit", month: "short", year: "numeric",
  });
}

function isNew(isoStr) {
  return (Date.now() - new Date(isoStr).getTime()) < 24 * 3600 * 1000;
}

// ── Tema claro / escuro ──────────────────────────────────────
function applyTheme(dark) {
  document.documentElement.setAttribute("data-theme", dark ? "dark" : "light");
  el.themeToggle.textContent = dark ? "☀️" : "🌙";
  localStorage.setItem("theme", dark ? "dark" : "light");
}

function initTheme() {
  const saved = localStorage.getItem("theme");
  const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
  applyTheme(saved ? saved === "dark" : prefersDark);
}

el.themeToggle.addEventListener("click", () => {
  applyTheme(document.documentElement.getAttribute("data-theme") !== "dark");
});

// ── Carregar artigos ─────────────────────────────────────────
async function loadArticles() {
  try {
    const resp = await fetch("articles.json?t=" + Date.now());
    if (!resp.ok) throw new Error("HTTP " + resp.status);
    const data = await resp.json();
    return data;
  } catch (e) {
    return null;
  }
}

// ── Construir mapa de temas a partir do config embutido em articles.json
//    (ou inferir pelas propriedades dos artigos)
function buildTopicMeta(articles) {
  const meta = {};
  // Cores cíclicas se não tivermos config
  const fallbackColors = [
    "#e91e8c","#9c27b0","#5e35b1","#1e88e5","#00897b",
    "#d81b60","#f4511e","#6d4c41","#43a047","#e91e63",
    "#7b1fa2","#455a64","#0288d1","#3949ab",
  ];
  const fallbackIcons = ["🔴","🟣","💜","🔵","🩵","🌸","🟠","🟤","🟢","🌺","🫧","🧠","💡","🌙"];

  const topicSet = new Set();
  articles.forEach(a => a.topics.forEach(t => topicSet.add(t)));

  let i = 0;
  topicSet.forEach(name => {
    meta[name] = {
      color: fallbackColors[i % fallbackColors.length],
      icon:  fallbackIcons[i % fallbackIcons.length],
    };
    i++;
  });
  return meta;
}

// ── Renderizar sidebar de temas ──────────────────────────────
function buildTopicFilters() {
  // Contar artigos por tema no conjunto filtrado por busca
  const counts = {};
  state.articles.forEach(a => {
    a.topics.forEach(t => {
      counts[t] = (counts[t] || 0) + 1;
    });
  });

  // Botão "Todos"
  const allBtn = el.filters.children[0]; // já existe no HTML
  const total  = state.articles.length;
  allBtn.innerHTML = `<span>✨</span> Todos <span class="topic-count">${total}</span>`;
  allBtn.classList.toggle("active", state.activeTopic === "all");

  // Remover botões dinâmicos anteriores
  while (el.filters.children.length > 1) {
    el.filters.removeChild(el.filters.lastChild);
  }

  // Ordenar temas por contagem desc
  const sortedTopics = Object.entries(counts).sort((a, b) => b[1] - a[1]);

  sortedTopics.forEach(([name, count]) => {
    const m   = state.topicMeta[name] || { color: "#888", icon: "🏷" };
    const btn = document.createElement("button");
    btn.className = "topic-btn" + (state.activeTopic === name ? " active" : "");
    btn.dataset.topic = name;
    btn.innerHTML = `
      <span class="topic-dot" style="background:${m.color}"></span>
      ${name}
      <span class="topic-count">${count}</span>
    `;
    btn.addEventListener("click", () => setActiveTopic(name));
    el.filters.appendChild(btn);
  });

  allBtn.addEventListener("click", () => setActiveTopic("all"));
}

// ── Filtrar artigos ──────────────────────────────────────────
function getFilteredArticles() {
  const q = state.searchQuery.toLowerCase().trim();
  return state.articles.filter(a => {
    const topicMatch =
      state.activeTopic === "all" || a.topics.includes(state.activeTopic);
    const searchMatch =
      !q ||
      a.title.toLowerCase().includes(q) ||
      (a.summary || "").toLowerCase().includes(q) ||
      a.source.toLowerCase().includes(q);
    return topicMatch && searchMatch;
  });
}

// ── Criar card HTML ──────────────────────────────────────────
function createCard(article) {
  const novel     = isNew(article.published);
  const topicTags = article.topics.map(t => {
    const m = state.topicMeta[t] || { color: "#888" };
    return `<span class="topic-tag" style="background:${m.color}">${t}</span>`;
  }).join("");

  const imageHtml = article.image
    ? `<img class="card-image" src="${escHtml(article.image)}" alt="" loading="lazy" onerror="this.style.display='none'">`
    : `<div class="card-image-placeholder">${article.topics[0] ? (state.topicMeta[article.topics[0]]?.icon || "📄") : "📄"}</div>`;

  const card = document.createElement("article");
  card.className = "card";
  card.innerHTML = `
    ${novel ? '<span class="card-new-badge">🆕 Novo</span>' : ""}
    ${imageHtml}
    <div class="card-body">
      <div class="card-topics">${topicTags}</div>
      <h3 class="card-title">${escHtml(article.title)}</h3>
      ${article.summary ? `<p class="card-summary">${escHtml(article.summary)}</p>` : ""}
      <div class="card-meta">
        <span class="card-source">📰 ${escHtml(article.source)}</span>
        <span class="card-date">${relativeDate(article.published)}</span>
      </div>
    </div>
  `;

  card.addEventListener("click", () => openModal(article));
  return card;
}

// ── Renderizar grid ──────────────────────────────────────────
function renderGrid() {
  const filtered = getFilteredArticles();

  // Atualizar visibilidade dos estados
  el.loading.hidden = true;
  el.error.hidden   = true;
  el.empty.hidden   = filtered.length > 0;
  el.grid.hidden    = filtered.length === 0;

  // Limpar e preencher grid
  el.grid.innerHTML = "";
  filtered.forEach(article => {
    el.grid.appendChild(createCard(article));
  });
}

// ── Estatísticas da sidebar ──────────────────────────────────
function updateStats(updatedAt) {
  const newCount = state.articles.filter(a => isNew(a.published)).length;
  el.statTotal.textContent   = `${state.articles.length} artigos`;
  el.statNew.textContent     = `${newCount} novo${newCount !== 1 ? "s" : ""} hoje`;
  el.statUpdated.textContent = updatedAt
    ? "Atualizado " + relativeDate(updatedAt)
    : "Nunca atualizado";
}

// ── Filtro de tema ───────────────────────────────────────────
function setActiveTopic(topic) {
  state.activeTopic = topic;
  buildTopicFilters();
  renderGrid();
}

// ── Busca ────────────────────────────────────────────────────
let searchTimer;
el.search.addEventListener("input", () => {
  clearTimeout(searchTimer);
  searchTimer = setTimeout(() => {
    state.searchQuery = el.search.value;
    renderGrid();
  }, 250);
});

// ── Modal ────────────────────────────────────────────────────
function openModal(article) {
  const topicTags = article.topics.map(t => {
    const m = state.topicMeta[t] || { color: "#888" };
    return `<span class="topic-tag" style="background:${m.color}">${t}</span>`;
  }).join("");

  el.modalContent.innerHTML = `
    <div class="modal-topics">${topicTags}</div>
    <h2 class="modal-title">${escHtml(article.title)}</h2>
    <div class="modal-meta">
      <span>📰 ${escHtml(article.source)}</span>
      <span>📅 ${new Date(article.published).toLocaleDateString("pt-BR", { dateStyle: "long" })}</span>
    </div>
    ${article.image ? `<img class="modal-image" src="${escHtml(article.image)}" alt="" onerror="this.style.display='none'">` : ""}
    ${article.summary ? `<p class="modal-summary">${escHtml(article.summary)}</p>` : ""}
    <a class="modal-link" href="${escHtml(article.url)}" target="_blank" rel="noopener noreferrer">
      Ler artigo completo ↗
    </a>
  `;

  el.modal.hidden = false;
  document.body.style.overflow = "hidden";
}

function closeModal() {
  el.modal.hidden = true;
  document.body.style.overflow = "";
}

el.modalClose.addEventListener("click", closeModal);
el.modal.addEventListener("click", e => { if (e.target === el.modal) closeModal(); });
document.addEventListener("keydown", e => { if (e.key === "Escape") closeModal(); });

// ── Utilitário: escapar HTML ─────────────────────────────────
function escHtml(str) {
  return String(str ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

// ── Copiar comando ───────────────────────────────────────────
function copyCmd(btn) {
  const code = btn.previousElementSibling?.textContent || "";
  navigator.clipboard.writeText(code).then(() => {
    btn.textContent = "✓ Copiado!";
    setTimeout(() => (btn.textContent = "Copiar"), 2000);
  });
}
window.copyCmd = copyCmd;

// ── Bootstrap ────────────────────────────────────────────────
async function init() {
  initTheme();

  const data = await loadArticles();

  if (!data || !Array.isArray(data.articles) || data.articles.length === 0) {
    el.loading.hidden = true;
    el.error.hidden   = false;
    return;
  }

  state.articles  = data.articles;
  state.topicMeta = buildTopicMeta(data.articles);

  buildTopicFilters();
  renderGrid();
  updateStats(data.updated_at);
}

init();
