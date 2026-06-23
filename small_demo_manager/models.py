from dataclasses import dataclass


@dataclass
class PlayerSnapshot:
    steam_id: int
    player_name: str
    team_number: int
    team_name: str
    kills: int
    deaths: int
    assists: int
    headshot_kills: int
    headshot_percent: float
    kd: float
    damage: int
    mvp: int
    three_k: int
    four_k: int
    five_k: int
    end_score: int
    spec_id: int = 0


@dataclass
class MatchResult:
    team_a_score: int
    team_b_score: int
    team_a_name: str
    team_b_name: str


@dataclass
class AudioEntry:
    round: int
    time: float
    duration: float
    file_path: str
