import os
from typing import Optional

from demoparser2 import DemoParser
import pandas as pd

from models import PlayerSnapshot, MatchResult


def _has_data(result) -> bool:
    if result is None:
        return False
    if isinstance(result, pd.DataFrame):
        return not result.empty
    if isinstance(result, list):
        return len(result) > 0
    return bool(result)


PLAYER_STATS = [
    "CCSPlayerController.CCSPlayerController_ActionTrackingServices.m_iKills",
    "CCSPlayerController.CCSPlayerController_ActionTrackingServices.m_iDeaths",
    "CCSPlayerController.CCSPlayerController_ActionTrackingServices.m_iAssists",
    "CCSPlayerController.CCSPlayerController_ActionTrackingServices.m_iHeadShotKills",
    "CCSPlayerController.CCSPlayerController_ActionTrackingServices.m_iDamage",
    "CCSPlayerController.m_iTeamNum",
    "CCSPlayerController.m_iScore",
    "CCSPlayerController.m_iMVPs",
]

TEAM_STATS = [
    "CCSTeam.m_iScore",
    "CCSTeam.m_szClanTeamname",
    "CCSTeam.m_iTeamNum",
]


class CS2DemoParser:
    def __init__(self, file_path: str):
        self.file_path = file_path
        self._parser = DemoParser(file_path)
        self.map_name: str = ""
        self.demo_name: str = os.path.splitext(os.path.basename(file_path))[0]
        self.is_sourcetv: bool = False

    def _get_last_tick(self) -> int:
        re = self._parser.parse_event("round_end")
        if _has_data(re):
            re = re[re["winner"].notna()]
            if not re.empty:
                return int(re["tick"].max())
        return 0

    def parse(self) -> tuple[list[PlayerSnapshot], MatchResult]:
        header = self._parser.parse_header()
        self.map_name = header.get("map_name", "Unknown")
        self.is_sourcetv = "sourcetv" in header.get("client_name", "").lower()

        player_info = self._parser.parse_player_info()
        if player_info.empty:
            raise ValueError("No player info found in demo")

        last_tick = self._get_last_tick()
        if last_tick == 0:
            raise ValueError("No round_end events found in demo")

        stats_df = self._parser.parse_ticks(PLAYER_STATS, ticks=[last_tick])
        team_df = self._parser.parse_ticks(TEAM_STATS, ticks=[last_tick])

        team_data: dict[int, tuple[int, str]] = {}
        if team_df is not None and not team_df.empty:
            for _, row in team_df.iterrows():
                tn = row.get("CCSTeam.m_iTeamNum")
                score = row.get("CCSTeam.m_iScore")
                clan = row.get("CCSTeam.m_szClanTeamname")
                if pd.notna(tn):
                    tn_int = int(tn)
                    if tn_int not in team_data:
                        team_data[tn_int] = (
                            int(score) if pd.notna(score) else 0,
                            str(clan) if pd.notna(clan) else "",
                        )

        team_scores: dict[int, int] = {}
        team_names: dict[int, str] = {}
        for tn, (sc, nm) in team_data.items():
            team_scores[tn] = sc
            team_names[tn] = nm

        default_team_names = {2: "Terrorists", 3: "Counter-Terrorists"}

        pi_map: dict[int, tuple[str, int]] = {}
        for _, row in player_info.iterrows():
            try:
                sid = int(row.get("steamid", 0)) if pd.notna(row.get("steamid")) else 0
            except (ValueError, TypeError):
                sid = 0
            if sid <= 0:
                continue
            name = str(row.get("name", "Unknown"))
            try:
                tn = int(row.get("team_number", 0)) if pd.notna(row.get("team_number")) else 0
            except (ValueError, TypeError):
                tn = 0
            pi_map[sid] = (name, tn)

        snapshots: list[PlayerSnapshot] = []
        for _, row in stats_df.iterrows():
            sid = int(row["steamid"])
            if sid == 0:
                continue
            if sid not in pi_map:
                continue

            player_name, team_num = pi_map[sid]

            kills = int(row.get(PLAYER_STATS[0], 0))
            deaths = int(row.get(PLAYER_STATS[1], 0))
            assists = int(row.get(PLAYER_STATS[2], 0))
            hs_kills = int(row.get(PLAYER_STATS[3], 0))
            damage = int(row.get(PLAYER_STATS[4], 0))
            mvp = int(row.get(PLAYER_STATS[7], 0))
            score_val = int(row.get(PLAYER_STATS[6], 0))

            hs_pct = round((hs_kills / kills * 100) if kills > 0 else 0, 1)
            kd = round(kills / deaths, 2) if deaths > 0 else round(float(kills), 2)

            team_name = team_names.get(team_num, default_team_names.get(team_num, "Unknown"))
            end_score = team_scores.get(team_num, 0)

            snapshots.append(PlayerSnapshot(
                steam_id=sid,
                player_name=player_name,
                team_number=team_num,
                team_name=team_name,
                kills=kills,
                deaths=deaths,
                assists=assists,
                headshot_kills=hs_kills,
                headshot_percent=hs_pct,
                kd=kd,
                damage=damage,
                mvp=mvp,
                three_k=0,
                four_k=0,
                five_k=0,
                end_score=end_score,
                spec_id=0,
            ))

        pi_order = list(pi_map.keys())
        for snap in snapshots:
            snap.spec_id = pi_order.index(snap.steam_id) + 1

        match_result = MatchResult(
            team_a_score=team_scores.get(3, 0),
            team_b_score=team_scores.get(2, 0),
            team_a_name=team_names.get(3, "Counter-Terrorists"),
            team_b_name=team_names.get(2, "Terrorists"),
        )

        return snapshots, match_result
