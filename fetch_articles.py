#!/usr/bin/env python3
"""
Buscador de Artigos - Atualização Diária
Lê config.json, busca artigos via RSS/APIs e salva em articles.json
"""

from __future__ import annotations

import json
import re
import hashlib
import html
import os
import logging
import time
from datetime import datetime, timedelta, timezone

try:
    import feedparser
except ImportError:
    print("Erro: feedparser não instalado. Execute: pip3 install feedparser requests")
    exit(1)

try:
    import requests
except ImportError:
    print("Erro: requests não instalado. Execute: pip3 install feedparser requests")
    exit(1)

# ── Configuração de log ────────────────────────────────────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE   = os.path.join(SCRIPT_DIR, "fetch.log")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger(__name__)

CONFIG_FILE = os.path.join(SCRIPT_DIR, "config.json")
OUTPUT_FILE = os.path.join(SCRIPT_DIR, "articles.json")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

# ── Helpers ────────────────────────────────────────────────────────────────────

def load_config() -> dict:
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    # Filtra entradas de comentário (strings que começam com "//") da lista de feeds
    data["rss_feeds"] = [
        url for url in data.get("rss_feeds", [])
        if isinstance(url, str) and url.startswith("http")
    ]
    return data


def article_id(url: str) -> str:
    return hashlib.md5(url.encode()).hexdigest()


def parse_date(entry) -> datetime:
    """Tenta extrair a data de publicação de um entry feedparser."""
    for attr in ("published_parsed", "updated_parsed", "created_parsed"):
        parsed = getattr(entry, attr, None)
        if parsed:
            try:
                return datetime(*parsed[:6], tzinfo=timezone.utc)
            except Exception:
                pass
    return datetime.now(timezone.utc)


def strip_html(text: str) -> str:
    # duas passagens: o PubMed às vezes entrega as tags escapadas (&lt;i&gt;)
    text = re.sub(r"<[^>]+>", "", text)
    text = html.unescape(text)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def is_within_days(dt: datetime, days: int) -> bool:
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    return dt >= cutoff


def find_image(entry) -> str | None:
    """Extrai a URL da primeira imagem encontrada no entry."""
    # 1. media_content
    for media in entry.get("media_content", []):
        url = media.get("url", "")
        mime = media.get("type", "")
        if mime.startswith("image") or url.lower().endswith((".jpg", ".png", ".webp", ".jpeg")):
            return url
    # 2. enclosures
    for enc in entry.get("enclosures", []):
        if enc.get("type", "").startswith("image"):
            return enc.get("href") or enc.get("url")
    # 3. media_thumbnail
    for thumb in entry.get("media_thumbnail", []):
        if thumb.get("url"):
            return thumb["url"]
    # 4. primeira <img> no summary
    if hasattr(entry, "summary"):
        m = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', entry.summary)
        if m:
            return m.group(1)
    return None


def keyword_in_text(kw: str, text_lower: str, words: set) -> bool:
    kw = kw.lower()
    if kw in text_lower:
        # siglas curtas (TRH, HRT) só valem como palavra inteira
        if len(kw) <= 4:
            return re.search(rf"\b{re.escape(kw)}\b", text_lower) is not None
        return True
    # termos com várias palavras ("sleep women"): basta todas aparecerem no texto
    parts = kw.split()
    return len(parts) > 1 and all(p in words for p in parts)


AUDIENCE_RE = None   # definido em main() a partir de "audience_terms" do config


def is_female_focused(text: str) -> bool:
    return AUDIENCE_RE is None or AUDIENCE_RE.search(text) is not None


def matched_topics(text: str, topics: list) -> list[str]:
    """Retorna lista de nomes de temas que aparecem no texto (só se o foco for feminino)."""
    if not is_female_focused(text):
        return []
    text_lower = text.lower()
    words = set(re.findall(r"[\w'-]+", text_lower))
    hits = []
    for topic in topics:
        if any(keyword_in_text(kw, text_lower, words) for kw in topic["keywords"]):
            hits.append(topic["name"])
    return hits


# ── Busca RSS ──────────────────────────────────────────────────────────────────

def fetch_feed(url: str, topics: list, days_back: int) -> list[dict]:
    articles = []
    try:
        log.info(f"Buscando: {url}")
        # feedparser aceita URL ou texto já baixado; passamos headers via requests
        resp = requests.get(url, headers=HEADERS, timeout=20)
        resp.raise_for_status()
        feed = feedparser.parse(resp.content)

        feed_title = feed.feed.get("title") or url.split("/")[2]
        if "medrxiv" in url:
            feed_title = "medRxiv (preprint)"

        for entry in feed.entries:
            title   = entry.get("title", "").strip()
            link    = entry.get("link", "").strip()
            summary = entry.get("summary", entry.get("description", ""))

            if not link or not title:
                continue

            pub_date = parse_date(entry)
            if not is_within_days(pub_date, days_back):
                continue

            full_text = f"{title} {summary}"
            topics_hit = matched_topics(full_text, topics)
            if not topics_hit:
                continue

            clean_summary = strip_html(summary)[:400]
            image_url     = find_image(entry)

            articles.append({
                "id":         article_id(link),
                "title":      title,
                "url":        link,
                "source":     feed_title,
                "summary":    clean_summary,
                "image":      image_url,
                "published":  pub_date.isoformat(),
                "topics":     topics_hit,
                "fetched_at": datetime.now(timezone.utc).isoformat(),
            })

    except requests.exceptions.RequestException as e:
        log.warning(f"Erro de rede em {url}: {e}")
    except Exception as e:
        log.error(f"Erro inesperado em {url}: {e}")

    return articles


# ── Busca PubMed (E-utilities) ─────────────────────────────────────────────────

EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"


def fetch_pubmed(term: str, topics: list, days_back: int, retmax: int) -> list[dict]:
    """Busca artigos recentes no PubMed via esearch + esummary (sem abstract)."""
    articles = []
    try:
        log.info(f"Buscando PubMed: {term}")
        search = requests.get(
            EUTILS + "esearch.fcgi",
            params={
                "db": "pubmed", "term": term, "retmode": "json",
                "sort": "date", "datetype": "pdat", "reldate": days_back,
                "retmax": retmax,
            },
            headers=HEADERS, timeout=20,
        )
        search.raise_for_status()
        ids = search.json()["esearchresult"]["idlist"]
        if not ids:
            return articles

        summ = requests.get(
            EUTILS + "esummary.fcgi",
            params={"db": "pubmed", "id": ",".join(ids), "retmode": "json"},
            headers=HEADERS, timeout=20,
        )
        summ.raise_for_status()
        result = summ.json()["result"]

        for pmid in ids:
            item  = result.get(pmid)
            if not item:
                continue
            title = strip_html(item.get("title", "")).rstrip(".")
            if not title:
                continue

            try:
                pub_date = datetime.strptime(
                    item["sortpubdate"].split()[0], "%Y/%m/%d"
                ).replace(tzinfo=timezone.utc)
            except (KeyError, ValueError):
                pub_date = datetime.now(timezone.utc)
            pub_date = min(pub_date, datetime.now(timezone.utc))

            topics_hit = matched_topics(title, topics)
            if not topics_hit:
                continue

            journal = item.get("fulljournalname") or item.get("source", "")
            authors = [a["name"] for a in item.get("authors", [])[:3]]
            summary = journal
            if authors:
                summary += " · " + ", ".join(authors) + (" et al." if len(item.get("authors", [])) > 3 else "")

            url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
            articles.append({
                "id":         article_id(url),
                "title":      title,
                "url":        url,
                "source":     "PubMed",
                "summary":    summary,
                "image":      None,
                "published":  pub_date.isoformat(),
                "topics":     topics_hit,
                "fetched_at": datetime.now(timezone.utc).isoformat(),
            })

    except requests.exceptions.RequestException as e:
        log.warning(f"Erro de rede no PubMed ({term}): {e}")
    except Exception as e:
        log.error(f"Erro inesperado no PubMed ({term}): {e}")

    return articles


# ── Busca Europe PMC (com abstract) ────────────────────────────────────────────

EUROPEPMC = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"


def fetch_europepmc(term: str, topics: list, days_back: int, page_size: int) -> list[dict]:
    """Busca no Europe PMC (índice do PubMed) — devolve abstract, ao contrário do esummary."""
    articles = []
    try:
        log.info(f"Buscando Europe PMC: {term}")
        today = datetime.now(timezone.utc).date()
        start = today - timedelta(days=days_back)
        resp = requests.get(
            EUROPEPMC,
            params={
                "query": f"({term}) AND SRC:MED AND FIRST_PDATE:[{start} TO {today}]",
                "format": "json", "resultType": "core",
                "pageSize": page_size, "sort": "P_PDATE_D desc",
            },
            headers=HEADERS, timeout=30,
        )
        resp.raise_for_status()

        for item in resp.json()["resultList"]["result"]:
            pmid  = item.get("pmid")
            title = strip_html(item.get("title", "")).rstrip(".")
            if not pmid or not title:
                continue
            abstract = strip_html(item.get("abstractText", ""))

            topics_hit = matched_topics(f"{title} {abstract}", topics)
            if not topics_hit:
                continue

            try:
                pub_date = datetime.strptime(
                    item["firstPublicationDate"], "%Y-%m-%d"
                ).replace(tzinfo=timezone.utc)
            except (KeyError, ValueError):
                pub_date = datetime.now(timezone.utc)

            journal = item.get("journalTitle", "")
            summary = abstract[:400] or (f"{journal} · {item.get('authorString', '')}".strip(" ·"))

            url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
            articles.append({
                "id":         article_id(url),
                "title":      title,
                "url":        url,
                "source":     journal or "PubMed",
                "summary":    summary,
                "image":      None,
                "published":  pub_date.isoformat(),
                "topics":     topics_hit,
                "fetched_at": datetime.now(timezone.utc).isoformat(),
            })

    except requests.exceptions.RequestException as e:
        log.warning(f"Erro de rede no Europe PMC ({term}): {e}")
    except Exception as e:
        log.error(f"Erro inesperado no Europe PMC ({term}): {e}")

    return articles


# ── Busca Crossref (revistas com RSS bloqueado) ────────────────────────────────

def fetch_crossref(name: str, issn: str, topics: list, days_back: int, rows: int) -> list[dict]:
    """Últimos artigos de uma revista (por ISSN) via Crossref, filtrados por tema."""
    articles = []
    try:
        log.info(f"Buscando Crossref: {name}")
        start = (datetime.now(timezone.utc) - timedelta(days=days_back)).date()
        resp = requests.get(
            f"https://api.crossref.org/journals/{issn}/works",
            params={
                "filter": f"from-pub-date:{start},type:journal-article",
                "rows": rows, "sort": "published", "order": "desc",
                "select": "title,abstract,URL,published",
            },
            headers=HEADERS, timeout=30,
        )
        resp.raise_for_status()

        now = datetime.now(timezone.utc)
        for item in resp.json()["message"]["items"]:
            title = strip_html((item.get("title") or [""])[0])
            url   = item.get("URL", "")
            if not title or not url:
                continue
            abstract = strip_html(item.get("abstract", ""))
            abstract = re.sub(r"^Abstract\s*", "", abstract)

            topics_hit = matched_topics(f"{title} {abstract}", topics)
            if not topics_hit:
                continue

            try:
                y, m, d = (item["published"]["date-parts"][0] + [1, 1])[:3]
                pub_date = min(datetime(y, m, d, tzinfo=timezone.utc), now)
            except (KeyError, IndexError, TypeError, ValueError):
                pub_date = now

            articles.append({
                "id":         article_id(url),
                "title":      title,
                "url":        url,
                "source":     name,
                "summary":    abstract[:400],
                "image":      None,
                "published":  pub_date.isoformat(),
                "topics":     topics_hit,
                "fetched_at": now.isoformat(),
            })

    except requests.exceptions.RequestException as e:
        log.warning(f"Erro de rede no Crossref ({name}): {e}")
    except Exception as e:
        log.error(f"Erro inesperado no Crossref ({name}): {e}")

    return articles


def dedupe_by_title(articles: list[dict]) -> list[dict]:
    """Remove o mesmo artigo vindo de fontes diferentes, mantendo a versão com mais texto."""
    best: dict = {}
    for a in articles:
        key = re.sub(r"[^a-z0-9]", "", a["title"].lower())
        if key not in best or len(a["summary"]) > len(best[key]["summary"]):
            best[key] = a
    return list(best.values())


# ── Principal ──────────────────────────────────────────────────────────────────

def main():
    log.info("=" * 60)
    log.info("Iniciando busca de artigos...")

    config     = load_config()
    global AUDIENCE_RE
    terms = config.get("audience_terms", [])
    if terms:
        AUDIENCE_RE = re.compile(
            r"\b(?:" + "|".join(re.escape(t) for t in terms) + r")", re.IGNORECASE
        )
    topics     = config["topics"]
    days_back  = config.get("days_back", 30)
    max_arts   = config.get("max_articles", 300)
    feeds      = config.get("rss_feeds", [])
    pubmed_qs  = config.get("pubmed_queries", [])
    pubmed_max = config.get("pubmed_max_per_query", 20)
    journals   = config.get("crossref_journals", [])
    crossref_n = config.get("crossref_max_per_journal", 100)

    # Carrega artigos anteriores para manter histórico
    previous: dict = {}
    if os.path.exists(OUTPUT_FILE):
        try:
            with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
                old = json.load(f)
            for a in old.get("articles", []):
                previous[a["id"]] = a
            log.info(f"{len(previous)} artigos anteriores carregados.")
        except Exception as e:
            log.warning(f"Não foi possível ler artigos anteriores: {e}")

    all_articles: dict = dict(previous)

    for term in pubmed_qs:
        for art in fetch_pubmed(term, topics, days_back, pubmed_max):
            all_articles[art["id"]] = art
        time.sleep(0.5)   # limite do NCBI sem chave: 3 req/s
        for art in fetch_europepmc(term, topics, days_back, pubmed_max):
            all_articles[art["id"]] = art   # mesmo PMID: substitui pela versão com abstract
        time.sleep(0.5)

    for j in journals:
        for art in fetch_crossref(j["name"], j["issn"], topics, days_back, crossref_n):
            all_articles[art["id"]] = art
        time.sleep(0.5)

    for feed_url in feeds:
        new_articles = fetch_feed(feed_url, topics, days_back)
        for art in new_articles:
            all_articles[art["id"]] = art
        time.sleep(1.5)   # Respeita servidores

    # Ordena por data e limita quantidade
    sorted_articles = sorted(
        dedupe_by_title(list(all_articles.values())),
        key=lambda x: x["published"],
        reverse=True,
    )[:max_arts]

    # Remove artigos mais antigos que days_back + 7 dias de margem
    cutoff = datetime.now(timezone.utc) - timedelta(days=days_back + 7)
    sorted_articles = [
        a for a in sorted_articles
        if datetime.fromisoformat(a["published"]) >= cutoff
    ]

    output = {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "total":      len(sorted_articles),
        "articles":   sorted_articles,
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    log.info(f"✅  {len(sorted_articles)} artigos salvos em articles.json")
    log.info("=" * 60)


if __name__ == "__main__":
    main()
