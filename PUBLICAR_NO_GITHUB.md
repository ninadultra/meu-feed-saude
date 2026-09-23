# 🚀 Guia de Publicação no GitHub Pages

Este guia mostra como publicar o seu Feed de Artigos na internet, **gratuitamente**, para acessar de qualquer dispositivo.

---

## O que você vai precisar

- ✅ Conta no GitHub (já criada)
- ✅ Git instalado no Mac (já vem instalado)
- ✅ Os arquivos do projeto (já criados)

---

## Passo 1 — Crie o repositório no GitHub

1. Acesse [github.com](https://github.com) e faça login
2. Clique no botão **"+"** no canto superior direito → **"New repository"**
3. Preencha:
   - **Repository name:** `meu-feed-saude` (ou qualquer nome sem espaços)
   - **Description:** Feed de artigos sobre saúde feminina
   - **Visibility:** ✅ **Public** (necessário para GitHub Pages grátis)
   - **NÃO** marque "Add a README file"
4. Clique em **"Create repository"**

> [!IMPORTANT]
> Anote o endereço do repositório que aparece na tela seguinte. Será algo como:
> `https://github.com/SEU-USUARIO/meu-feed-saude.git`

---

## Passo 2 — Envie os arquivos pelo Terminal

Abra o **Terminal** no Mac e execute os comandos abaixo **um de cada vez**:

### 2.1 Entre na pasta do projeto
```bash
cd /Users/ninapatrocinio/.gemini/antigravity/scratch/article-feed
```

### 2.2 Inicialize o Git
```bash
git init
git add .
git commit -m "🌸 Primeiro commit — Feed de Saúde"
```

### 2.3 Conecte ao GitHub
> ⚠️ Substitua `SEU-USUARIO` e `meu-feed-saude` pelo seu usuário e nome do repositório real:
```bash
git remote add origin https://github.com/SEU-USUARIO/meu-feed-saude.git
git branch -M main
git push -u origin main
```

> Se pedir senha: o GitHub não aceita mais senha, use um **token de acesso pessoal**.
> Veja como criar um token: [github.com/settings/tokens](https://github.com/settings/tokens)
> (Tipo: Classic → marque `repo` → Generate → copie e use como senha)

---

## Passo 3 — Ative o GitHub Pages

1. No GitHub, abra o seu repositório
2. Clique na aba **"Settings"** (⚙️)
3. No menu lateral, clique em **"Pages"**
4. Em **"Source"**, selecione:
   - Branch: **main**
   - Folder: **/ (root)**
5. Clique em **"Save"**

Após alguns minutos, sua página estará disponível em:
```
https://SEU-USUARIO.github.io/meu-feed-saude
```

> [!TIP]
> O endereço aparecerá na própria seção Pages após salvar. Pode demorar 2–5 minutos para ficar online.

---

## Passo 4 — Ative as atualizações automáticas

O GitHub Actions já está configurado para buscar artigos **todo dia às 7h da manhã** (horário de Brasília). Para que funcione:

1. Vá ao seu repositório no GitHub
2. Clique na aba **"Actions"**
3. Se aparecer um aviso perguntando se deseja ativar workflows, clique em **"I understand my workflows, go ahead and enable them"**

### Testando agora (sem esperar amanhã)
1. Vá em **Actions** → **"🌸 Atualizar Artigos Diariamente"**
2. Clique em **"Run workflow"** → **"Run workflow"** (botão verde)
3. Aguarde ~2 minutos
4. Recarregue sua página — os artigos aparecerão!

---

## ✅ Pronto! Seu feed está na internet

| O que acontece | Quando |
|---|---|
| GitHub Actions executa `fetch_articles.py` | Todo dia às 7h (Brasília) |
| `articles.json` é atualizado e salvo | Automaticamente |
| Sua página exibe os novos artigos | Imediatamente após |

---

## 📱 Adicionando ao celular como app (opcional)

### iPhone / iPad
1. Abra Safari e acesse a URL da sua página
2. Toque no ícone de compartilhar (quadrado com seta)
3. Selecione **"Adicionar à Tela de Início"**
4. Dê o nome "Feed Saúde" e toque em **"Adicionar"**

### Android
1. Abra Chrome e acesse a URL
2. Menu (⋮) → **"Adicionar à tela inicial"**

---

## 🔧 Ajustes futuros

Para atualizar qualquer coisa (temas, cores, fontes RSS):

1. Edite os arquivos localmente
2. No Terminal, execute:
```bash
cd /Users/ninapatrocinio/.gemini/antigravity/scratch/article-feed
git add .
git commit -m "Atualização"
git push
```
3. Em 1–2 minutos a página online atualiza automaticamente.

---

## 🆘 Problemas comuns

| Problema | Solução |
|---|---|
| `git push` pede senha e não aceita | Use token de acesso ([instruções](https://github.com/settings/tokens)) |
| Página mostra "404" | Aguarde 5 min após ativar o Pages |
| Actions não aparece | Clique em "Actions" e habilite |
| Artigos não atualizam | Vá em Actions → Run workflow manualmente |
