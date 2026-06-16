# WC 2026 Tracker

Site estático para acompanhar a Copa do Mundo FIFA 2026 em tempo real — resultados, tabelas de grupos, artilheiros e estatísticas por partida.

## Stack

- **Astro** — geração de páginas estáticas
- **Tailwind CSS** — estilos
- **Python** — pipeline de dados (`scripts/fetch_data.py`)

## Fontes de dados

Todos os dados vêm de APIs públicas da FIFA, sem autenticação:

| Endpoint | Dados |
|---|---|
| `api.fifa.com/api/v3/calendar/matches` | Lista das 104 partidas, placares e metadados |
| `api.fifa.com/api/v3/live/football/{IdMatch}` | Gols, cartões, escalações e nomes dos jogadores |
| `fdh-api.fifa.com/v1/stats/match/{IdIFES}/players.json` | Estatísticas por jogador (passes, chutes, distância, xG, etc.) |
| `fdh-api.fifa.com/v1/stats/match/{IdIFES}/teams.json` | Estatísticas por time (posse, escanteios, cartões, etc.) |

O script `scripts/fetch_data.py` busca essas APIs, processa os dados e grava os arquivos em `data/`:

- `data/matches.json` — todas as partidas com gols e cartões
- `data/standings.json` — tabela de grupos calculada localmente
- `data/players.json` — registro de jogadores encontrados nas partidas

Resultados de cada partida são cacheados em `data/stats/` para evitar re-fetches desnecessários.

## Rodar localmente

```bash
# instalar dependências do site
npm install

# atualizar os dados
pip install -r scripts/requirements.txt
python scripts/fetch_data.py

# subir o servidor de desenvolvimento
npm run dev
```

## Páginas

- `/` — partidas recentes e próximas
- `/groups` — tabela de todos os grupos
- `/matches` — calendário completo (resultados e agenda)
- `/match/[id]` — detalhe de uma partida com estatísticas individuais
