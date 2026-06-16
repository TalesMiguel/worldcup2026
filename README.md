# WC 2026 Tracker

**https://wc26.talesmiguel.dev**

Site para acompanhar a Copa do Mundo FIFA 2026: resultados em tempo real, calendário completo, tabelas de grupos e estatísticas detalhadas de cada partida (time e jogador), em português e inglês.

## O que tem

- Placares e calendário das 104 partidas, com filtro por resultados/agenda
- Tabelas de grupos calculadas automaticamente
- Detalhe de cada partida: gols, cartões, escalações
- Estatísticas de time: posse de bola, chutes, passes, escanteios
- Estatísticas táticas de time: progressões de bola, mudanças de lado, cruzamentos, quebras de linha por terço (ataque/meio/defesa), pressões defensivas, posses forçadas
- Estatísticas por jogador: minutos, gols, assistências, passes, chutes, distância percorrida, velocidade máxima, xG

## Fontes de dados

Todos os dados vêm de APIs públicas da FIFA, sem autenticação:

| Endpoint | Dados |
|---|---|
| `api.fifa.com/api/v3/calendar/matches` | Lista das 104 partidas, placares e metadados |
| `api.fifa.com/api/v3/live/football/{IdMatch}` | Gols, cartões, escalações e nomes dos jogadores |
| `fdh-api.fifa.com/v1/stats/match/{IdIFES}/players.json` | Estatísticas por jogador |
| `fdh-api.fifa.com/v1/stats/match/{IdIFES}/teams.json` | Estatísticas por time, incluindo as métricas táticas |

O script `scripts/fetch_data.py` busca essas APIs, processa os dados e grava os arquivos em `data/`:

- `data/matches.json` — todas as partidas com gols e cartões
- `data/standings.json` — tabela de grupos calculada localmente
- `data/players.json` — registro de jogadores encontrados nas partidas
- `data/stats/` — estatísticas de time e jogador por partida, cacheadas para evitar re-fetches

## Stack

- Astro (geração de páginas estáticas)
- Tailwind CSS
- Python (pipeline de dados)

## Rodar localmente

```bash
npm install

pip install -r scripts/requirements.txt
python scripts/fetch_data.py

npm run dev
```

## Páginas

- `/` — partidas recentes e próximas
- `/groups` — tabela de todos os grupos
- `/matches` — calendário completo (resultados e agenda)
- `/match/[id]` — detalhe de uma partida com estatísticas de time e jogador
