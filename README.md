# 🌸 Meu Feed de Saúde — Guia de Uso

Feed de artigos personalizados sobre saúde feminina com atualização diária automática.

---

## ✅ Instalação (primeira vez)

Abra o **Terminal** e siga os passos:

### 1. Entre na pasta do projeto
```bash
cd /Users/ninapatrocinio/.gemini/antigravity/scratch/article-feed
```

### 2. Instale as dependências Python
```bash
pip3 install -r requirements.txt
```

### 3. Busque os primeiros artigos
```bash
python3 fetch_articles.py
```
> Aguarde ~30–60 segundos. Vai aparecer no terminal quantos artigos foram encontrados.

### 4. Abra a página
```bash
bash start.sh --no-fetch
```
O navegador abrirá automaticamente em `http://localhost:8787`.

---

## 🚀 Uso diário (versão rápida)

Para buscar artigos novos **e** abrir a página de uma vez:

```bash
bash /Users/ninapatrocinio/.gemini/antigravity/scratch/article-feed/start.sh
```

Ou, só para abrir sem buscar (mais rápido):
```bash
bash /Users/ninapatrocinio/.gemini/antigravity/scratch/article-feed/start.sh --no-fetch
```

---

## ⏰ Atualização automática diária (cron no Mac)

Configure o Mac para buscar artigos todo dia de manhã automaticamente:

### 1. Descubra o caminho do Python3
```bash
which python3
```
Anote o resultado (geralmente `/usr/local/bin/python3` ou `/opt/homebrew/bin/python3`).

### 2. Abra o editor de cron
```bash
crontab -e
```
> Se perguntar sobre o editor, escolha `nano` (opção mais fácil).

### 3. Adicione esta linha (substitua o caminho do Python3 se necessário)
```
0 7 * * * /usr/local/bin/python3 /Users/ninapatrocinio/.gemini/antigravity/scratch/article-feed/fetch_articles.py >> /Users/ninapatrocinio/.gemini/antigravity/scratch/article-feed/fetch.log 2>&1
```
> Isso roda todo dia às **7h da manhã**.  
> Para mudar o horário: `0 7` = 7h00, `0 8` = 8h00, `30 6` = 6h30.

### 4. Salve e saia
- No nano: `Ctrl+O` → Enter → `Ctrl+X`

### ⚠️ Permissão de acesso total ao disco (macOS Ventura / Sonoma)
Se o cron não funcionar, você precisa dar permissão ao Terminal:
1. **Preferências do Sistema** → **Privacidade e Segurança** → **Acesso Total ao Disco**
2. Adicione o app **Terminal**

---

## 🔧 Personalizar temas e fontes

Edite o arquivo [`config.json`](./config.json):

- **`topics`** — lista de temas com palavras-chave em português e inglês
- **`rss_feeds`** — URLs de feeds RSS para buscar artigos
- **`days_back`** — quantos dias para trás buscar (padrão: 30)
- **`max_articles`** — máximo de artigos a guardar (padrão: 300)

### Adicionar um novo tema
```json
{
  "name": "Meu Tema",
  "keywords": ["palavra-chave pt", "english keyword"],
  "color": "#FF5722",
  "icon": "🔥"
}
```

### Adicionar um feed RSS
Encontre o feed RSS do site que você gosta e adicione na lista `rss_feeds`.  
Exemplo: `"https://www.sitedaudo.com/feed"`

---

## 📁 Estrutura de arquivos

```
article-feed/
├── index.html          ← Página web principal
├── style.css           ← Estilo visual
├── app.js              ← Lógica da página
├── config.json         ← Temas e fontes (EDITE AQUI)
├── articles.json       ← Artigos gerados pelo script (não edite)
├── fetch_articles.py   ← Script de atualização diária
├── fetch.log           ← Log das buscas (para diagnosticar erros)
├── requirements.txt    ← Dependências Python
├── start.sh            ← Script para abrir o feed
└── README.md           ← Este arquivo
```

---

## 🆘 Problemas comuns

| Problema | Solução |
|---|---|
| "No module named feedparser" | Execute `pip3 install feedparser requests` |
| Página em branco | Execute `python3 fetch_articles.py` primeiro |
| Poucos artigos | Aumente `days_back` no `config.json` |
| Cron não funciona | Veja a seção "Permissão de acesso total ao disco" acima |
| Erro de rede | Verifique a conexão com a internet |

Verifique o arquivo `fetch.log` para detalhes sobre erros de busca.
