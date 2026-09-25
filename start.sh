#!/bin/bash
# ─────────────────────────────────────────────────────────────
# start.sh  –  Busca artigos e abre o feed no navegador
# ─────────────────────────────────────────────────────────────

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "🌸  Feed de Artigos de Saúde"
echo "────────────────────────────────────────"

# 1. Buscar artigos (opcional: pula se quiser só abrir a página)
if [[ "$1" != "--no-fetch" ]]; then
  echo "📡  Buscando artigos…"
  python3 fetch_articles.py
  echo ""
fi

# 2. Iniciar servidor local
PORT=8787
echo "🌐  Iniciando servidor em http://localhost:$PORT"
echo "     (pressione Ctrl+C para encerrar)"
echo ""

# Abre o navegador após 1 segundo
(sleep 1 && open "http://localhost:$PORT") &

# Inicia servidor Python
python3 -m http.server $PORT
