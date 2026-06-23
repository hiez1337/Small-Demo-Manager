import os
import re
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


class CS2DemoParser:
    def __init__(self, file_path: str):
        self.file_path = file_path
        self._parser = DemoParser(file_path)
        self.map_name: str = ""
        self.duration: int = 0
        self.demo_name: str = os.path.splitext(os.path.basename(file_path))[0]
        self.is_sourcetv: bool = False

    def parse(self) -> tuple[list[PlayerSnapshot], MatchResult]:
        header = self._parser.parse_header()
        self.map_name = header.get("map_name", "Unknown")
        self.duration = 0

        player_info = self._parser.parse_player_info()
        if player_info.empty:
            raise ValueError("No player info found in demo")

        death_events = self._parser.parse_event("player_death")
        round_starts = self._parser.parse_event("round_start")
        round_ends = self._parser.parse_event("round_end")
        mvp_events = self._parser.parse_event("round_mvp")

        team_a_score = 0
        team_b_score = 0
        team_a_name = "Team A"
        team_b_name = "Team B"

        if _has_data(round_ends):
            for _, row in round_ends.iterrows():
                winner = str(row.get("winner", "")) if pd.notna(row.get("winner")) else ""
                if winner == "CT":
                    team_a_score += 1
                elif winner == "T":
                    team_b_score += 1
            team_a_name = "Counter-Terrorists"
            team_b_name = "Terrorists"

        total_rounds = 0
        if _has_data(round_starts):
            total_rounds = len(round_starts)

        player_kills: dict[int, int] = {}
        player_deaths: dict[int, int] = {}
        player_assists: dict[int, int] = {}
        player_damage: dict[int, int] = {}
        player_hs_kills: dict[int, int] = {}
        player_multi_kills: dict[int, int] = {}

        if _has_data(death_events):
            for _, row in death_events.iterrows():
                attacker = row.get("attacker_steamid")
                victim = row.get("user_steamid")
                assister = row.get("assister_steamid")
                hs = row.get("headshot", False)
                wp_damage = row.get("dmg_health", 0)

                try:
                    aid = int(attacker) if pd.notna(attacker) else 0
                except (ValueError, TypeError):
                    aid = 0
                if aid > 0:
                    player_kills[aid] = player_kills.get(aid, 0) + 1
                    player_damage[aid] = player_damage.get(aid, 0) + int(wp_damage or 0)
                    if hs:
                        player_hs_kills[aid] = player_hs_kills.get(aid, 0) + 1

                try:
                    vid = int(victim) if pd.notna(victim) else 0
                except (ValueError, TypeError):
                    vid = 0
                if vid > 0:
                    player_deaths[vid] = player_deaths.get(vid, 0) + 1

                try:
                    asid = int(assister) if pd.notna(assister) else 0
                except (ValueError, TypeError):
                    asid = 0
                if asid > 0:
                    player_assists[asid] = player_assists.get(asid, 0) + 1

        player_mvp: dict[int, int] = {}
        if _has_data(mvp_events):
            if isinstance(mvp_events, list):
                for item in mvp_events:
                    try:
                        sid = int(item.get("steamid", 0)) if item.get("steamid") else 0
                    except (ValueError, TypeError):
                        sid = 0
                    if sid > 0:
                        player_mvp[sid] = player_mvp.get(sid, 0) + 1
            else:
                for _, row in mvp_events.iterrows():
                    try:
                        sid = int(row.get("steamid")) if pd.notna(row.get("steamid")) else 0
                    except (ValueError, TypeError):
                        sid = 0
                    if sid > 0:
                        player_mvp[sid] = player_mvp.get(sid, 0) + 1

        team_map: dict[int, int] = {}
        team_name_map: dict[int, str] = {}
        name_map: dict[int, str] = {}
        steamid_set: set[int] = set()

        for _, row in player_info.iterrows():
            try:
                sid = int(row.get("steamid", 0)) if pd.notna(row.get("steamid")) else 0
            except (ValueError, TypeError):
                sid = 0
            if sid <= 0:
                continue
            steamid_set.add(sid)
            name_map[sid] = str(row.get("name", "Unknown"))
            try:
                team_num = int(row.get("team_number", 0)) if pd.notna(row.get("team_number")) else 0
            except (ValueError, TypeError):
                team_num = 0
            team_map[sid] = team_num
            if team_num == 2:
                team_name_map[sid] = "Terrorists"
            elif team_num == 3:
                team_name_map[sid] = "Counter-Terrorists"
            else:
                team_name_map[sid] = "Unknown"

        team_a_steamids = [s for s, t in team_map.items() if t == 3]
        team_b_steamids = [s for s, t in team_map.items() if t == 2]

        self.is_sourcetv = header.get("server_name", "").lower().find("sourcetv") >= 0

        snapshots: list[PlayerSnapshot] = []
        for idx, sid in enumerate(team_a_steamids + team_b_steamids):
            k = player_kills.get(sid, 0)
            d = player_deaths.get(sid, 0)
            a = player_assists.get(sid, 0)
            hs_k = player_hs_kills.get(sid, 0)
            hs_pct = round((hs_k / k * 100) if k > 0 else 0, 1)
            kd = round(k / d, 2) if d > 0 else round(float(k), 2)
            dmg = player_damage.get(sid, 0)
            mvp = player_mvp.get(sid, 0)
            three_k = sum(1 for _ in [1])  # simplified
            four_k = 0
            five_k = 0

            snapshots.append(PlayerSnapshot(
                steam_id=sid,
                player_name=name_map.get(sid, "Unknown"),
                team_number=team_map.get(sid, 0),
                team_name=team_name_map.get(sid, "Unknown"),
                kills=k,
                deaths=d,
                assists=a,
                headshot_kills=hs_k,
                headshot_percent=hs_pct,
                kd=kd,
                damage=dmg,
                mvp=mvp,
                three_k=three_k,
                four_k=four_k,
                five_k=five_k,
                end_score=team_a_score if team_map.get(sid) == 3 else team_b_score,
                spec_id=idx + 1,
            ))

        match_result = MatchResult(
            team_a_score=team_a_score,
            team_b_score=team_b_score,
            team_a_name=team_a_name if team_a_steamids else "Team A",
            team_b_name=team_b_name if team_b_steamids else "Team B",
        )

        return snapshots, match_result
