# WC 2026 Tracker

**https://wc26.talesmiguel.dev**

A site for following the FIFA World Cup 2026: live results, full schedule, group standings, and detailed match stats (team and player), in English and Portuguese.

## What it has

- Scores and schedule for all 104 matches, with a results/upcoming filter
- Group standings, computed automatically
- Match detail: goals, bookings, lineups
- Team stats: possession, shots, passes, corners
- Tactical team stats: ball progressions, switches of play, crosses, line breaks by third (attacking/midfield/defensive), defensive pressures, forced turnovers
- Player stats: minutes played, goals, assists, passes, shots, distance covered, top speed, xG

## Data sources

All data comes from FIFA's public APIs, no authentication required:

| Endpoint | Data |
|---|---|
| `api.fifa.com/api/v3/calendar/matches` | List of all 104 matches, scores, and metadata |
| `api.fifa.com/api/v3/live/football/{IdMatch}` | Goals, bookings, lineups, and player names |
| `fdh-api.fifa.com/v1/stats/match/{IdIFES}/players.json` | Per-player stats |
| `fdh-api.fifa.com/v1/stats/match/{IdIFES}/teams.json` | Per-team stats, including the tactical metrics |

`scripts/fetch_data.py` fetches these APIs, processes the data, and writes the files in `data/`:

- `data/matches.json` — every match with its goals and bookings
- `data/standings.json` — group standings, computed locally
- `data/players.json` — registry of players found across matches
- `data/stats/` — per-match team and player stats, cached to avoid unnecessary re-fetches

## Stack

- Astro (static site generation)
- Tailwind CSS
- Python (data pipeline)

## Run locally

```bash
npm install

pip install -r scripts/requirements.txt
python scripts/fetch_data.py

npm run dev
```

## Pages

- `/` — recent and upcoming matches
- `/groups` — all group standings
- `/matches` — full schedule (results and upcoming)
- `/match/[id]` — match detail with team and player stats
