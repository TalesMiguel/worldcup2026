"""
FIFA WC 2026 data pipeline.
Fetches match data from FIFA public APIs and writes JSON files to data/.

Sources:
  - api.fifa.com/api/v3/calendar/matches  → all 104 matches + scores
  - api.fifa.com/api/v3/live/football/{IdMatch} → goals, lineups, player names
  - fdh-api.fifa.com/v1/stats/match/{IdIFES}/players.json → per-player stats
  - fdh-api.fifa.com/v1/stats/match/{IdIFES}/teams.json   → per-team stats
"""

import json
import time
import sys
from pathlib import Path
from typing import Any

import requests

ROOT = Path(__file__).parent.parent
DATA = ROOT / "data"
STATS = DATA / "stats"
DATA.mkdir(exist_ok=True)
STATS.mkdir(exist_ok=True)

SESSION = requests.Session()
SESSION.headers.update({"Accept": "application/json", "User-Agent": "wc2026-tracker/1.0"})

FIFA_CALENDAR = (
    "https://api.fifa.com/api/v3/calendar/matches"
    "?idCompetition=17&idSeason=285023&language=en&count=200&from=2026-06-11"
)
FIFA_LIVE = "https://api.fifa.com/api/v3/live/football/{id_match}"
FDH_PLAYERS = "https://fdh-api.fifa.com/v1/stats/match/{id_ifes}/players.json"
FDH_TEAMS = "https://fdh-api.fifa.com/v1/stats/match/{id_ifes}/teams.json"

CARD_LABEL = {1: "yellow", 2: "red", 3: "yellow_red"}
POSITION_MAP = {0: "Goalkeeper", 1: "Defender", 2: "Midfielder", 3: "Forward"}


def get(url: str, retries: int = 3) -> Any:
    for attempt in range(retries):
        try:
            r = SESSION.get(url, timeout=15)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            if attempt == retries - 1:
                print(f"  ✗ Failed {url}: {e}", file=sys.stderr)
                return None
            time.sleep(2)
    return None


def player_name(names: list) -> str:
    if not names:
        return ""
    return names[0].get("Description", "")


def locale_str(value) -> str:
    """Handle fields that can be a plain string or a list of locale objects."""
    if not value:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return player_name(value)
    return str(value)


def fetch_calendar() -> list[dict]:
    data = get(FIFA_CALENDAR)
    if not data:
        return []
    return data.get("Results", [])


def fetch_live(id_match: str) -> dict | None:
    return get(FIFA_LIVE.format(id_match=id_match))


def fetch_fdh_players(id_ifes: str) -> dict | None:
    time.sleep(1)
    return get(FDH_PLAYERS.format(id_ifes=id_ifes))


def fetch_fdh_teams(id_ifes: str) -> dict | None:
    time.sleep(1)
    return get(FDH_TEAMS.format(id_ifes=id_ifes))


def parse_match(r: dict) -> dict:
    """Parse calendar API result into our Match shape."""
    home = r.get("Home") or {}
    away = r.get("Away") or {}

    def team(t: dict) -> dict:
        if not t:
            return {"id": "", "name": "TBD", "abbreviation": "TBD"}
        names = t.get("TeamName") or [{}]
        abbr = t.get("Abbreviation") or ""
        if isinstance(abbr, list):
            abbr = player_name(abbr)
        return {
            "id": str(t.get("IdTeam") or ""),
            "name": player_name(names),
            "abbreviation": abbr or player_name(names)[:3].upper() or "TBD",
        }

    return {
        "idMatch": str(r.get("IdMatch", "")),
        "idIFES": str(r.get("Properties", {}).get("IdIFES", "")),
        "idGroup": str(r.get("IdGroup", "")) if r.get("IdGroup") else None,
        "groupName": locale_str(r.get("GroupName")) or None,
        "stageName": locale_str(r.get("StageName")) or "",
        "date": r.get("Date", ""),
        "homeTeam": team(home),
        "awayTeam": team(away),
        "homeScore": r.get("HomeTeamScore"),
        "awayScore": r.get("AwayTeamScore"),
        "status": r.get("MatchStatus", 0),
        "goals": [],
        "bookings": [],
    }


def enrich_with_live(match: dict, live: dict) -> dict:
    """Add goals, bookings, and player registry data from the live endpoint."""
    goals = []
    bookings = []
    players_seen = {}  # player_id → {name, teamId, shirtNumber, position}

    for side_key, team in [("HomeTeam", match["homeTeam"]), ("AwayTeam", match["awayTeam"])]:
        side = live.get(side_key, {})

        for p in side.get("Players", []):
            pid = str(p.get("IdPlayer", ""))
            if pid:
                players_seen[pid] = {
                    "playerId": pid,
                    "teamId": team["id"],
                    "teamName": team["name"],
                    "playerName": player_name(p.get("PlayerName", [])),
                    "shirtNumber": p.get("ShirtNumber", 0),
                    "position": POSITION_MAP.get(p.get("Position", -1), "Unknown"),
                    "fieldStatus": p.get("FieldStatus", -1),  # 0=starter, 1=sub, 2=unused
                }

        for g in side.get("Goals", []):
            pid = str(g.get("IdPlayer", ""))
            goals.append({
                "playerId": pid,
                "playerName": players_seen.get(pid, {}).get("playerName", ""),
                "minute": g.get("Minute", ""),
                "type": g.get("Type", 1),
                "teamId": team["id"],
            })

        for b in side.get("Bookings", []):
            pid = str(b.get("IdPlayer", ""))
            bookings.append({
                "playerId": pid,
                "playerName": players_seen.get(pid, {}).get("playerName", ""),
                "minute": b.get("Minute", ""),
                "card": b.get("Card", 1),
                "teamId": team["id"],
            })

    match["goals"] = goals
    match["bookings"] = bookings
    return match, players_seen


def parse_fdh_players(raw: dict, registry: dict) -> list[dict]:
    """Convert FDH player stats into our PlayerStat shape."""

    def val(metrics: list, name: str) -> float | None:
        for m in metrics:
            if m[0] == name:
                v = m[1]
                return float(v) if v is not None else None
        return None

    result = []
    for pid, metrics in raw.items():
        info = registry.get(str(pid), {})
        result.append({
            "playerId": str(pid),
            "playerName": info.get("playerName", ""),
            "teamId": info.get("teamId", ""),
            "teamName": info.get("teamName", ""),
            "position": info.get("position", ""),
            "shirtNumber": info.get("shirtNumber", 0),
            "timePlayed": val(metrics, "TimePlayed") or 0,
            "goals": val(metrics, "Goals") or 0,
            "assists": val(metrics, "Assists") or 0,
            "passes": val(metrics, "Passes") or 0,
            "passesCompleted": val(metrics, "PassesCompleted") or 0,
            "attemptAtGoal": val(metrics, "AttemptAtGoal") or 0,
            "attemptAtGoalOnTarget": val(metrics, "AttemptAtGoalOnTarget") or 0,
            "yellowCards": val(metrics, "YellowCards") or 0,
            "redCards": val(metrics, "DirectRedCards") or 0,
            "totalDistance": val(metrics, "TotalDistance") or 0,
            "topSpeed": val(metrics, "TopSpeed") or 0,
            "xg": val(metrics, "Xg") or 0,
        })
    return result


def parse_fdh_teams(raw: dict) -> dict:
    """Convert FDH team stats into {teamId: TeamStat} dict."""

    def val(metrics: list, name: str) -> float | None:
        for m in metrics:
            if m[0] == name:
                v = m[1]
                return float(v) if v is not None else None
        return None

    result = {}
    for team_id, metrics in raw.items():
        result[str(team_id)] = {
            "teamId": str(team_id),
            "goals": val(metrics, "Goals") or 0,
            "attemptAtGoal": val(metrics, "AttemptAtGoal") or 0,
            "passes": val(metrics, "Passes") or 0,
            "passesCompleted": val(metrics, "PassesCompleted") or 0,
            "corners": val(metrics, "Corners") or 0,
            "yellowCards": val(metrics, "YellowCards") or 0,
            "redCards": val(metrics, "DirectRedCards") or 0,
        }
    return result


def compute_standings(matches: list[dict]) -> list[dict]:
    """Compute group standings from completed group stage matches."""
    groups: dict[str, dict] = {}  # groupId → {groupName, teams: {teamId → row}}

    for m in matches:
        if m["status"] != 1 or not m["idGroup"] or m["homeScore"] is None:
            continue

        gid = m["idGroup"]
        gname = m.get("groupName") or gid
        if gid not in groups:
            groups[gid] = {"groupId": gid, "groupName": gname, "teams": {}}

        def get_or_create(team):
            tid = team["id"]
            if tid not in groups[gid]["teams"]:
                groups[gid]["teams"][tid] = {
                    "teamId": tid,
                    "teamName": team["name"],
                    "played": 0, "won": 0, "drawn": 0, "lost": 0,
                    "goalsFor": 0, "goalsAgainst": 0, "goalDiff": 0, "points": 0,
                }
            return groups[gid]["teams"][tid]

        h = get_or_create(m["homeTeam"])
        a = get_or_create(m["awayTeam"])
        hs, as_ = int(m["homeScore"]), int(m["awayScore"])

        h["played"] += 1; a["played"] += 1
        h["goalsFor"] += hs; h["goalsAgainst"] += as_
        a["goalsFor"] += as_; a["goalsAgainst"] += hs

        if hs > as_:
            h["won"] += 1; h["points"] += 3
            a["lost"] += 1
        elif hs < as_:
            a["won"] += 1; a["points"] += 3
            h["lost"] += 1
        else:
            h["drawn"] += 1; h["points"] += 1
            a["drawn"] += 1; a["points"] += 1

    result = []
    for gdata in sorted(groups.values(), key=lambda g: g["groupName"]):
        rows = sorted(
            gdata["teams"].values(),
            key=lambda r: (-r["points"], -(r["goalsFor"] - r["goalsAgainst"]), -r["goalsFor"]),
        )
        for r in rows:
            r["goalDiff"] = r["goalsFor"] - r["goalsAgainst"]
        result.append({"groupId": gdata["groupId"], "groupName": gdata["groupName"], "rows": rows})

    return result


def main():
    print("→ Fetching calendar…")
    calendar = fetch_calendar()
    if not calendar:
        print("✗ No calendar data. Aborting.", file=sys.stderr)
        sys.exit(1)
    print(f"  {len(calendar)} matches found")

    matches = [parse_match(r) for r in calendar]
    completed = [m for m in matches if m["homeScore"] is not None and m["idIFES"]]
    print(f"  {len(completed)} completed matches")

    # Load existing player registry to merge into
    registry_file = DATA / "players.json"
    registry: dict = {}
    if registry_file.exists():
        registry = json.loads(registry_file.read_text())

    new_count = 0
    for m in completed:
        id_ifes = m["idIFES"]
        players_file = STATS / f"{id_ifes}_players.json"

        if players_file.exists():
            # Still need to load the registry from the live file if it exists
            live_file = STATS / f"{id_ifes}_live.json"
            if live_file.exists():
                for pid, info in json.loads(live_file.read_text()).items():
                    registry[pid] = info
            continue

        print(f"  → Match {id_ifes}: {m['homeTeam']['abbreviation']} vs {m['awayTeam']['abbreviation']}")

        # Fetch live data for goals/bookings/player names
        live = fetch_live(m["idMatch"])
        if live:
            m, players_seen = enrich_with_live(m, live)
            registry.update(players_seen)
            # Persist the per-match player registry slice
            live_file = STATS / f"{id_ifes}_live.json"
            live_file.write_text(json.dumps(players_seen, ensure_ascii=False, indent=2))
        else:
            print(f"    ⚠ No live data", file=sys.stderr)

        # Fetch FDH player stats
        fdh_p = fetch_fdh_players(id_ifes)
        if fdh_p:
            parsed_players = parse_fdh_players(fdh_p, registry)
            players_file.write_text(json.dumps(parsed_players, ensure_ascii=False, indent=2))
            print(f"    ✓ {len(parsed_players)} player stats")
        else:
            print(f"    ⚠ No FDH player data", file=sys.stderr)

        # Fetch FDH team stats
        fdh_t = fetch_fdh_teams(id_ifes)
        if fdh_t:
            teams_file = STATS / f"{id_ifes}_teams.json"
            parsed_teams = parse_fdh_teams(fdh_t)
            teams_file.write_text(json.dumps(parsed_teams, ensure_ascii=False, indent=2))

        new_count += 1

    # For completed matches already cached, enrich goals/bookings from live files
    for m in completed:
        id_ifes = m["idIFES"]
        live_file = STATS / f"{id_ifes}_live.json"
        if live_file.exists():
            live_registry = json.loads(live_file.read_text())
            live_data_path = STATS / f"{id_ifes}_live_raw.json"
            # Re-fetch goals/bookings from the raw live data if available
            # (we need to re-hydrate the match objects)

    # Re-enrich all completed matches with goals from stored live data
    live_cache: dict[str, dict] = {}
    for m in completed:
        id_ifes = m["idIFES"]
        # Try to load from cached live data
        live_file = STATS / f"{id_ifes}_live.json"
        # The live.json contains player registry, not raw live data
        # Reload goals from a goals cache or re-fetch goals
        # For now, re-hydrate goals from live endpoint only if we didn't just fetch
        goals_file = STATS / f"{id_ifes}_goals.json"
        if goals_file.exists():
            cached = json.loads(goals_file.read_text())
            m["goals"] = cached.get("goals", [])
            m["bookings"] = cached.get("bookings", [])
        elif m["goals"]:
            # Just fetched — persist goals
            goals_file.write_text(json.dumps({"goals": m["goals"], "bookings": m["bookings"]}, ensure_ascii=False))

    print(f"\n→ Writing data files…")

    # matches.json
    (DATA / "matches.json").write_text(json.dumps(matches, ensure_ascii=False, indent=2))
    print(f"  ✓ matches.json ({len(matches)} entries)")

    # standings.json
    standings = compute_standings(matches)
    (DATA / "standings.json").write_text(json.dumps(standings, ensure_ascii=False, indent=2))
    print(f"  ✓ standings.json ({len(standings)} groups)")

    # players.json
    registry_file.write_text(json.dumps(registry, ensure_ascii=False, indent=2))
    print(f"  ✓ players.json ({len(registry)} players)")

    print(f"\n✓ Done. {new_count} new matches processed.")


if __name__ == "__main__":
    main()
