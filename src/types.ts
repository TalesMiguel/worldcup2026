export interface Team {
  id: string;
  name: string;
  abbreviation: string;
  flagUrl?: string;
}

export interface Goal {
  playerId: string;
  playerName: string;
  minute: string;
  type: number; // 1=normal, 2=penalty, 3=own goal
  teamId: string;
}

export interface Booking {
  playerId: string;
  playerName: string;
  minute: string;
  card: number; // 1=yellow, 2=red, 3=yellow+red
  teamId: string;
}

export interface Match {
  idMatch: string;
  idIFES: string;
  idGroup: string | null;
  groupName: string | null;
  stageName: string;
  date: string;
  homeTeam: Team;
  awayTeam: Team;
  homeScore: number | null;
  awayScore: number | null;
  status: number; // 0=scheduled, 1=finished, 3=live
  goals: Goal[];
  bookings: Booking[];
}

export interface StandingRow {
  teamId: string;
  teamName: string;
  played: number;
  won: number;
  drawn: number;
  lost: number;
  goalsFor: number;
  goalsAgainst: number;
  goalDiff: number;
  points: number;
}

export interface GroupStanding {
  groupId: string;
  groupName: string;
  rows: StandingRow[];
}

export interface PlayerStat {
  playerId: string;
  playerName: string;
  teamId: string;
  teamName: string;
  position: string;
  shirtNumber: number;
  timePlayed: number;
  goals: number;
  assists: number;
  passes: number;
  passesCompleted: number;
  attemptAtGoal: number;
  attemptAtGoalOnTarget: number;
  yellowCards: number;
  redCards: number;
  totalDistance: number;
  topSpeed: number;
  xg: number;
}

export interface TeamStat {
  teamId: string;
  goals: number;
  attemptAtGoal: number;
  passes: number;
  passesCompleted: number;
  corners: number;
  yellowCards: number;
  redCards: number;
}

export interface MatchDetail extends Match {
  homeTeamStat: TeamStat | null;
  awayTeamStat: TeamStat | null;
  playerStats: PlayerStat[];
}
