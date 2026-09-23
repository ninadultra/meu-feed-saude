#!/usr/bin/env python3
"""
Buscador de Artigos - Atualização Diária
Lê config.json, busca artigos via RSS/APIs e salva em articles.json
"""

import json
import re
import hashlib
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
    text = re.sub(r"<[^>]+>", " ", text)
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


def matched_topics(text: str, topics: list) -> list[str]:
    """Retorna lista de nomes de temas que aparecem no texto."""
    text_lower = text.lower()
    hits = []
    for topic in topics:
        for kw in topic["keywords"]:
            if kw.lower() in text_lower:
                hits.append(topic["name"])
                break
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


# ── Principal ──────────────────────────────────────────────────────────────────

def main():
    log.info("=" * 60)
    log.info("Iniciando busca de artigos...")

    config     = load_config()
    topics     = config["topics"]
    days_back  = config.get("days_back", 30)
    max_arts   = config.get("max_articles", 300)
    feeds      = config.get("rss_feeds", [])

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

    for feed_url in feeds:
        new_articles = fetch_feed(feed_url, topics, days_back)
        for art in new_articles:
            all_articles[art["id"]] = art
        time.sleep(1.5)   # Respeita servidores

    # Ordena por data e limita quantidade
    sorted_articles = sorted(
        all_articles.values(),
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
